"""Gemini Live API transcription adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import asyncio
import contextlib
import logging
from queue import Queue
import threading
import uuid

from PySide6.QtCore import QObject, Signal

from ..audio_capture.signal_gate import has_spoken_audio
from ..contracts import AudioSource, SttProviderKind, TranscriptSegment
from ..settings import GEMINI_API_KEY, GEMINI_LIVE_MODEL


logger = logging.getLogger("backend.providers.gemini_live_stt")

try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


def _merge_transcription_text(current: str, incoming: str) -> str:
    clean_incoming = " ".join((incoming or "").split()).strip()
    if not clean_incoming:
        return current
    if not current:
        return clean_incoming
    if clean_incoming.startswith(current):
        return clean_incoming
    if current.startswith(clean_incoming):
        return current
    if " " in clean_incoming or clean_incoming.startswith((".", ",", "!", "?", ";", ":")):
        separator = "" if current.endswith((" ", "\n")) or clean_incoming.startswith((".", ",", "!", "?", ";", ":")) else " "
        return f"{current}{separator}{clean_incoming}".strip()
    if current[-1].isalnum() and clean_incoming[0].isalnum():
        return f"{current}{clean_incoming}"
    return f"{current} {clean_incoming}".strip()


@dataclass(slots=True)
class _AudioFrame:
    payload: bytes | None = None
    source: AudioSource = AudioSource.MIXED
    start_ms: int = 0
    end_ms: int = 0
    audio_stream_end: bool = False


class GeminiLiveTranscriber(QObject):
    partial_text = Signal(str)
    segment_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, model: str | None = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key or GEMINI_API_KEY
        self._model = model or GEMINI_LIVE_MODEL
        self._thread: threading.Thread | None = None
        self._queue: Queue[_AudioFrame | None] = Queue()
        self._stop_requested = threading.Event()
        self._latest_frame = _AudioFrame()
        self._buffered_input_text = ""
        self._turn_complete_seen = False
        self._last_voiced_end_ms = 0
        self._idle_flush_sent = False

    @property
    def is_available(self) -> bool:
        return GEMINI_AVAILABLE and bool(self._api_key)

    def start(self) -> bool:
        if not self.is_available:
            self.error_occurred.emit("Gemini Live is unavailable.")
            return False
        if self._thread and self._thread.is_alive():
            return True

        self._stop_requested.clear()
        self._thread = threading.Thread(target=self._run, name="GeminiLiveStt", daemon=True)
        self._thread.start()
        self.status_changed.emit("connecting")
        return True

    def submit_frame(
        self,
        audio_bytes: bytes,
        start_ms: int,
        end_ms: int,
        source: AudioSource,
    ) -> None:
        if not audio_bytes:
            return
        if not has_spoken_audio(audio_bytes):
            if self._last_voiced_end_ms and not self._idle_flush_sent and end_ms - self._last_voiced_end_ms >= 900:
                self._queue.put(_AudioFrame(audio_stream_end=True))
                self._idle_flush_sent = True
            return
        frame = _AudioFrame(payload=audio_bytes, source=source, start_ms=start_ms, end_ms=end_ms)
        self._latest_frame = frame
        self._last_voiced_end_ms = end_ms
        self._idle_flush_sent = False
        self._queue.put(frame)

    def flush_stream(self) -> None:
        self._queue.put(_AudioFrame(audio_stream_end=True))

    def stop(self) -> None:
        self._stop_requested.set()
        self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None
        self._reset_turn_buffer()
        self.status_changed.emit("stopped")

    def set_model(self, model: str) -> None:
        self._model = model.strip()

    def _run(self) -> None:
        try:
            asyncio.run(self._run_forever())
        except Exception as exc:
            logger.error("Gemini Live loop failed", exc_info=True)
            self.error_occurred.emit(f"Gemini Live failed: {exc}")
            self.status_changed.emit("error")

    async def _run_forever(self) -> None:
        retry_delay = 1.0
        while not self._stop_requested.is_set():
            try:
                await self._live_loop()
                return
            except Exception:
                if self._stop_requested.is_set():
                    return
                logger.warning("Gemini Live session dropped; reconnecting", exc_info=True)
                self.status_changed.emit("reconnecting")
                await asyncio.sleep(retry_delay)
                retry_delay = min(4.0, retry_delay * 2)

    async def _live_loop(self) -> None:
        client = genai.Client(api_key=self._api_key)
        config = {
            "response_modalities": ["AUDIO"],
            "input_audio_transcription": {},
            "output_audio_transcription": {},
            "system_instruction": (
                "You are a live transcription engine. "
                "Transcribe the user's speech faithfully. "
                "Do not answer questions or add commentary."
            ),
        }

        async with client.aio.live.connect(model=self._model, config=config) as session:
            self.status_changed.emit("ready")
            receiver = asyncio.create_task(self._receive_loop(session))
            try:
                while not self._stop_requested.is_set():
                    frame = await asyncio.to_thread(self._queue.get)
                    if frame is None:
                        break
                    if frame.audio_stream_end:
                        await session.send_realtime_input(audio_stream_end=True)
                        continue
                    await session.send_realtime_input(
                        audio=types.Blob(data=frame.payload, mime_type="audio/pcm;rate=16000")
                    )
            finally:
                receiver.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await receiver

    async def _receive_loop(self, session) -> None:
        async for message in session.receive():
            server_content = getattr(message, "server_content", None)
            if server_content is None:
                continue

            if bool(getattr(server_content, "turn_complete", False)):
                self._turn_complete_seen = True
                self._emit_buffered_segment_if_ready()

            input_transcription = getattr(server_content, "input_transcription", None)
            if input_transcription is None:
                continue

            text = getattr(input_transcription, "text", "") or ""
            parts = getattr(input_transcription, "parts", None) or []
            if not text and parts:
                text = getattr(parts[0], "text", "") or ""
            if not text:
                continue

            self._buffered_input_text = _merge_transcription_text(self._buffered_input_text, text)
            finished = bool(getattr(input_transcription, "finished", False))
            if not finished:
                self.partial_text.emit(self._buffered_input_text)
                self._emit_buffered_segment_if_ready()
                continue

            self._emit_buffered_segment()

    def _emit_buffered_segment_if_ready(self) -> None:
        if self._turn_complete_seen and self._buffered_input_text:
            self._emit_buffered_segment()

    def _emit_buffered_segment(self) -> None:
        text = " ".join(self._buffered_input_text.split()).strip()
        if not text:
            return
        frame = self._latest_frame
        segment = TranscriptSegment(
            id=f"gemini-{uuid.uuid4().hex[:12]}",
            text=text,
            start_ms=max(0, frame.start_ms),
            end_ms=max(frame.end_ms, frame.start_ms),
            created_at=datetime.now(UTC),
            is_partial=False,
            source=frame.source,
            provider=SttProviderKind.GEMINI,
        )
        self.segment_ready.emit(segment)
        self.partial_text.emit("")
        self._reset_turn_buffer()

    def _reset_turn_buffer(self) -> None:
        self._buffered_input_text = ""
        self._turn_complete_seen = False
