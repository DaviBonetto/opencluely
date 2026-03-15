"""Local faster-whisper adapter used as degraded fallback."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
import re
import traceback
import uuid

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Signal, Slot

from ..contracts import AudioSource, SttProviderKind, TranscriptSegment
from ..settings import LOCAL_WHISPER_MODEL_SIZE


logger = logging.getLogger("backend.providers.local_stt")

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


class _LoaderThread(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, model_size: str):
        super().__init__()
        self._model_size = model_size

    def run(self) -> None:
        if not WHISPER_AVAILABLE:
            self.error.emit("faster-whisper is unavailable.")
            return
        if not NUMPY_AVAILABLE:
            self.error.emit("numpy is unavailable.")
            return

        try:
            model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
            self.finished.emit(model)
        except Exception as exc:
            logger.error("Local whisper model load failed", exc_info=True)
            self.error.emit(f"Local whisper load failed: {exc}")


class _LocalSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)


class _LocalChunkTask(QRunnable):
    def __init__(
        self,
        model,
        audio_bytes: bytes,
        start_ms: int,
        end_ms: int,
        source: AudioSource,
    ):
        super().__init__()
        self._model = model
        self._audio_bytes = audio_bytes
        self._start_ms = start_ms
        self._end_ms = end_ms
        self._source = source
        self.signals = _LocalSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            audio_array = np.frombuffer(self._audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _info = self._model.transcribe(
                audio_array,
                language=None,
                beam_size=1,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500, "speech_pad_ms": 200},
            )
            text = _clean_text(" ".join(segment.text for segment in segments))
            segment = TranscriptSegment(
                id=f"local-{uuid.uuid4().hex[:12]}",
                text=text,
                start_ms=self._start_ms,
                end_ms=self._end_ms,
                created_at=datetime.now(UTC),
                is_partial=False,
                source=self._source,
                provider=SttProviderKind.LOCAL,
            )
            self.signals.finished.emit(segment)
        except Exception as exc:
            logger.error("Local transcription failed", exc_info=True)
            self.signals.error.emit(f"Local transcription failed: {exc}")


class LocalChunkTranscriber(QObject):
    segment_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model_size: str | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._model_size = model_size or LOCAL_WHISPER_MODEL_SIZE
        self._model = None
        self._loader_thread: _LoaderThread | None = None
        self._thread_pool = QThreadPool.globalInstance()
        self._pending: list[tuple[bytes, int, int, AudioSource]] = []
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return WHISPER_AVAILABLE and NUMPY_AVAILABLE

    def start(self) -> bool:
        if self._model is not None:
            self.status_changed.emit("ready")
            return True
        if not self.is_available:
            self.error_occurred.emit("Local STT dependencies are unavailable.")
            return False
        if self._loader_thread and self._loader_thread.isRunning():
            return True

        self.status_changed.emit("loading")
        self._loader_thread = _LoaderThread(self._model_size)
        self._loader_thread.finished.connect(self._on_model_loaded)
        self._loader_thread.error.connect(self.error_occurred.emit)
        self._loader_thread.start()
        return True

    def stop(self) -> None:
        if self._loader_thread and self._loader_thread.isRunning():
            self._loader_thread.quit()
            self._loader_thread.wait(2000)
        self._model = None
        self._pending.clear()
        self.status_changed.emit("stopped")

    def submit_chunk(
        self,
        audio_bytes: bytes,
        start_ms: int,
        end_ms: int,
        source: AudioSource,
    ) -> None:
        if not audio_bytes:
            return
        if self._model is None:
            self._pending.append((audio_bytes, start_ms, end_ms, source))
            self.start()
            return

        task = _LocalChunkTask(self._model, audio_bytes, start_ms, end_ms, source)
        self._track_task(task)
        task.signals.started.connect(lambda: self.status_changed.emit("transcribing"))
        task.signals.finished.connect(self.segment_ready.emit)
        task.signals.finished.connect(lambda _segment: self.status_changed.emit("ready"))
        task.signals.error.connect(self.error_occurred.emit)
        task.signals.error.connect(lambda _error: self.status_changed.emit("error"))
        self._thread_pool.start(task)

    def _on_model_loaded(self, model) -> None:
        self._model = model
        self.status_changed.emit("ready")
        pending = list(self._pending)
        self._pending.clear()
        for audio_bytes, start_ms, end_ms, source in pending:
            self.submit_chunk(audio_bytes, start_ms, end_ms, source)

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _segment, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if text and not text[0].isupper():
        text = text[0].upper() + text[1:]
    return text
