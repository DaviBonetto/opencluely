"""Groq-based audio transcription backend."""

from __future__ import annotations

import io
import logging
import traceback
import wave

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import GROQ_API_KEY, GROQ_AUDIO_MODEL


logger = logging.getLogger("backend.audio_capture.groq_transcriber")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
    logger.info("Groq SDK imported successfully")
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None
    logger.warning("Groq SDK is unavailable. Install: pip install groq")


SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


class TranscriptionTaskGroq(QRunnable):
    """Processes a single audio chunk through the Groq Whisper API."""

    class Signals(QObject):
        started = Signal()
        finished = Signal(str)
        error = Signal(str)

    def __init__(self, client, audio_bytes: bytes):
        super().__init__()
        self.client = client
        self.audio_bytes = audio_bytes
        self.signals = self.Signals()

    @Slot()
    def run(self):
        try:
            self.signals.started.emit()
            wav_buffer = self._create_wav_buffer(self.audio_bytes)
            transcription = self.client.audio.transcriptions.create(
                file=("audio.wav", wav_buffer, "audio/wav"),
                model=GROQ_AUDIO_MODEL,
                language=None,
                response_format="text",
            )

            text = transcription.strip() if transcription else ""
            self.signals.finished.emit(text)
        except Exception as exc:
            error_msg = f"Erro na transcrição Groq: {exc}"
            logger.error("[TranscriptionTaskGroq] %s", error_msg)
            logger.error(traceback.format_exc())
            self.signals.error.emit(error_msg)

    def _create_wav_buffer(self, audio_bytes: bytes) -> io.BytesIO:
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_bytes)

        wav_buffer.seek(0)
        return wav_buffer


class TranscriberGroq(QObject):
    """Coordinates Groq audio transcription with a thread pool."""

    transcription_ready = Signal(str)
    transcription_started = Signal()
    error_occurred = Signal(str)
    model_loading = Signal()
    model_loaded = Signal()

    def __init__(self, api_key: str | None = None, parent=None):
        super().__init__(parent)
        self._client = None
        self._is_ready = False
        self._api_key = api_key or GROQ_API_KEY
        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(2)
        logger.info("[TranscriberGroq] Initialized")

    def load_model(self):
        logger.info("[TranscriberGroq] Configuring Groq client")
        self.model_loading.emit()

        if not GROQ_AVAILABLE:
            error_msg = "Groq SDK não disponível. Instale: pip install groq"
            logger.error("[TranscriberGroq] %s", error_msg)
            self.error_occurred.emit(error_msg)
            return

        if not self._api_key:
            error_msg = "API key Groq não configurada"
            logger.error("[TranscriberGroq] %s", error_msg)
            self.error_occurred.emit(error_msg)
            return

        try:
            self._client = Groq(api_key=self._api_key)
            self._is_ready = True
            logger.info("[TranscriberGroq] Groq client configured")
            self.model_loaded.emit()
        except Exception as exc:
            error_msg = f"Erro ao configurar Groq: {exc}"
            logger.error("[TranscriberGroq] %s", error_msg)
            logger.error(traceback.format_exc())
            self.error_occurred.emit(error_msg)

    def set_api_key(self, api_key: str):
        self._api_key = api_key

    def transcribe_chunk(self, audio_bytes: bytes):
        if not self._is_ready:
            self.error_occurred.emit("Cliente Groq não configurado.")
            return

        if not audio_bytes:
            return

        task = TranscriptionTaskGroq(self._client, audio_bytes)
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
        return self._is_ready

    def cleanup(self):
        self._client = None
        self._is_ready = False
