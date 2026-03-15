"""Local transcription backend using faster-whisper."""

from __future__ import annotations

import logging
import re
import traceback

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Signal, Slot


logger = logging.getLogger("backend.audio_capture.local_transcriber")

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None
    logger.warning("numpy is unavailable for local transcription")

try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
    logger.info("faster-whisper imported successfully")
except ImportError as exc:
    WHISPER_AVAILABLE = False
    WhisperModel = None
    logger.warning("faster-whisper is unavailable: %s", exc)


MODEL_SIZE = "tiny"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


class ModelLoaderThread(QThread):
    """Loads the Whisper model off the UI thread."""

    finished = Signal(object)
    error = Signal(str)

    def run(self):
        if not WHISPER_AVAILABLE:
            self.error.emit("faster-whisper não disponível")
            return

        if not NUMPY_AVAILABLE:
            self.error.emit("numpy não disponível")
            return

        try:
            model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            self.finished.emit(model)
        except Exception as exc:
            error_msg = f"Erro ao carregar modelo: {exc}"
            logger.error("[ModelLoaderThread] %s", error_msg)
            logger.error(traceback.format_exc())
            self.error.emit(error_msg)


class TranscriptionTask(QRunnable):
    """Processes a single audio chunk with the loaded model."""

    class Signals(QObject):
        started = Signal()
        finished = Signal(str)
        error = Signal(str)

    def __init__(self, model, audio_bytes: bytes):
        super().__init__()
        self.model = model
        self.audio_bytes = audio_bytes
        self.signals = self.Signals()

    @Slot()
    def run(self):
        try:
            if not NUMPY_AVAILABLE:
                self.signals.error.emit("numpy não disponível")
                return

            self.signals.started.emit()
            audio_array = self._convert_bytes_to_array(self.audio_bytes)
            segments, info = self.model.transcribe(
                audio_array,
                language=None,
                beam_size=1,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500, "speech_pad_ms": 200},
            )

            text_parts = [segment.text for segment in segments]
            full_text = " ".join(text_parts).strip()
            clean_text = self._clean_transcription(full_text)
            self.signals.finished.emit(clean_text if clean_text else "")
        except Exception as exc:
            self.signals.error.emit(f"Erro na transcrição: {exc}")

    def _convert_bytes_to_array(self, audio_bytes: bytes):
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0

    def _clean_transcription(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([.,!?])", r"\1", text)
        text = re.sub(r"([.,!?])\1+", r"\1", text)
        text = text.strip()

        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]

        return text


class Transcriber(QObject):
    """Coordinates local faster-whisper transcription."""

    transcription_ready = Signal(str)
    transcription_started = Signal()
    error_occurred = Signal(str)
    model_loading = Signal()
    model_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
        self._is_model_loaded = False
        self._loader_thread = None
        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(2)

    def load_model(self):
        if not WHISPER_AVAILABLE:
            self.error_occurred.emit("faster-whisper não disponível.\nInstale via: pip install faster-whisper")
            return

        if not NUMPY_AVAILABLE:
            self.error_occurred.emit("numpy não disponível.\nInstale via: pip install numpy")
            return

        if self._is_model_loaded:
            self.model_loaded.emit()
            return

        if self._loader_thread is not None and self._loader_thread.isRunning():
            return

        self.model_loading.emit()
        self._loader_thread = ModelLoaderThread()
        self._loader_thread.finished.connect(self._on_model_loaded)
        self._loader_thread.error.connect(self._on_model_error)
        self._loader_thread.start()

    def _on_model_loaded(self, model):
        self._model = model
        self._is_model_loaded = True
        self.model_loaded.emit()

    def _on_model_error(self, error_msg: str):
        self._is_model_loaded = False
        self.error_occurred.emit(error_msg)

    def transcribe_chunk(self, audio_bytes: bytes):
        if not self._is_model_loaded:
            self.error_occurred.emit("Modelo ainda não carregado.")
            return

        if not audio_bytes:
            return

        task = TranscriptionTask(self._model, audio_bytes)
        task.signals.started.connect(self._on_transcription_started)
        task.signals.finished.connect(self._on_transcription_finished)
        task.signals.error.connect(self._on_transcription_error)
        self._thread_pool.start(task)

    def _on_transcription_started(self):
        self.transcription_started.emit()

    def _on_transcription_finished(self, text: str):
        self.transcription_ready.emit(text)

    def _on_transcription_error(self, error_msg: str):
        self.error_occurred.emit(error_msg)

    def is_model_loaded(self) -> bool:
        return self._is_model_loaded

    def cleanup(self):
        if self._loader_thread is not None:
            self._loader_thread.quit()
            self._loader_thread.wait(2000)
        self._model = None
