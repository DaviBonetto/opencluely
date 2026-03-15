"""Gemini multimodal screen analysis adapter."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import GEMINI_API_KEY, GEMINI_VISION_MODEL


logger = logging.getLogger("backend.providers.gemini_screen")

try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class _GeminiScreenSignals(QObject):
    started = Signal()
    finished = Signal(str)
    error = Signal(str)


class _GeminiScreenTask(QRunnable):
    def __init__(self, client, model: str, image, prompt: str):
        super().__init__()
        self._client = client
        self._model = model
        self._image = image
        self._prompt = prompt
        self.signals = _GeminiScreenSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            response = self._client.models.generate_content(
                model=self._model,
                contents=[self._prompt, self._image],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            self.signals.finished.emit((response.text or "").strip())
        except Exception as exc:
            logger.error("Gemini screen analysis failed", exc_info=True)
            self.signals.error.emit(f"Gemini screen analysis failed: {exc}")


class GeminiScreenAnalyzer(QObject):
    analysis_ready = Signal(str)
    analysis_started = Signal()
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, model: str | None = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key or GEMINI_API_KEY
        self._model = model or GEMINI_VISION_MODEL
        self._client = None
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return GEMINI_AVAILABLE and bool(self._api_key)

    def initialize(self) -> bool:
        if not self.is_available:
            self.error_occurred.emit("Gemini vision is unavailable.")
            return False
        self._client = genai.Client(api_key=self._api_key)
        return True

    def analyze_image(self, image, prompt: str) -> None:
        if not self._client and not self.initialize():
            return
        task = _GeminiScreenTask(self._client, self._model, image, prompt)
        self._track_task(task)
        task.signals.started.connect(self.analysis_started.emit)
        task.signals.finished.connect(self.analysis_ready.emit)
        task.signals.error.connect(self.error_occurred.emit)
        self._thread_pool.start(task)

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _summary, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))
