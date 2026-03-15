"""Groq Whisper adapter for chunk-based speech-to-text."""

from __future__ import annotations

from datetime import UTC, datetime
import io
import logging
import traceback
import uuid
import wave

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..audio_capture.signal_gate import looks_like_silence
from ..contracts import AudioSource, SttProviderKind, TranscriptSegment
from ..settings import GROQ_API_KEY, GROQ_AUDIO_MODEL


logger = logging.getLogger("backend.providers.groq_stt")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None


SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


class _GroqSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)


class _GroqChunkTask(QRunnable):
    def __init__(
        self,
        client: Groq,
        model: str,
        audio_bytes: bytes,
        start_ms: int,
        end_ms: int,
        source: AudioSource,
    ):
        super().__init__()
        self._client = client
        self._model = model
        self._audio_bytes = audio_bytes
        self._start_ms = start_ms
        self._end_ms = end_ms
        self._source = source
        self.signals = _GroqSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(SAMPLE_WIDTH)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(self._audio_bytes)
            wav_buffer.seek(0)

            transcription = self._client.audio.transcriptions.create(
                file=("audio.wav", wav_buffer, "audio/wav"),
                model=self._model,
                language=None,
                response_format="text",
            )
            text = _normalize_text(transcription.strip() if transcription else "")
            segment = TranscriptSegment(
                id=f"groq-{uuid.uuid4().hex[:12]}",
                text=text,
                start_ms=self._start_ms,
                end_ms=self._end_ms,
                created_at=datetime.now(UTC),
                is_partial=False,
                source=self._source,
                provider=SttProviderKind.GROQ,
            )
            self.signals.finished.emit(segment)
        except Exception as exc:
            logger.error("Groq transcription failed", exc_info=True)
            self.signals.error.emit(f"Groq transcription failed: {exc}")


class GroqChunkTranscriber(QObject):
    segment_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._api_key = api_key or GROQ_API_KEY
        self._model = GROQ_AUDIO_MODEL
        self._client: Groq | None = None
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return GROQ_AVAILABLE and bool(self._api_key)

    def start(self) -> bool:
        if not GROQ_AVAILABLE:
            self.error_occurred.emit("Groq SDK is unavailable.")
            return False
        if not self._api_key:
            self.error_occurred.emit("Groq API key is not configured.")
            return False

        try:
            self._client = Groq(api_key=self._api_key)
            self.status_changed.emit("ready")
            return True
        except Exception as exc:
            self.error_occurred.emit(f"Groq client setup failed: {exc}")
            return False

    def stop(self) -> None:
        self._client = None
        self.status_changed.emit("stopped")

    def set_model(self, model: str) -> None:
        self._model = model.strip()

    def submit_chunk(
        self,
        audio_bytes: bytes,
        start_ms: int,
        end_ms: int,
        source: AudioSource,
    ) -> None:
        if not self._client:
            self.error_occurred.emit("Groq transcriber is not ready.")
            return
        if not audio_bytes:
            return
        if looks_like_silence(audio_bytes):
            self.status_changed.emit("ready")
            return

        task = _GroqChunkTask(self._client, self._model, audio_bytes, start_ms, end_ms, source)
        self._track_task(task)
        task.signals.started.connect(lambda: self.status_changed.emit("transcribing"))
        task.signals.finished.connect(self.segment_ready.emit)
        task.signals.finished.connect(lambda _segment: self.status_changed.emit("ready"))
        task.signals.error.connect(self.error_occurred.emit)
        task.signals.error.connect(lambda _error: self.status_changed.emit("error"))
        self._thread_pool.start(task)

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _segment, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()
