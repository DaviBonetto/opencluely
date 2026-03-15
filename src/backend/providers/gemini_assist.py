"""Gemini text/multimodal assist adapter."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import GEMINI_ASSIST_API_KEY, GEMINI_ASSIST_MODEL


logger = logging.getLogger("backend.providers.gemini_assist")

try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class _GeminiAssistSignals(QObject):
    started = Signal()
    finished = Signal(str)
    error = Signal(str)


class _GeminiAssistTask(QRunnable):
    def __init__(self, client, model: str, prompt: str, system_instruction: str):
        super().__init__()
        self._client = client
        self._model = model
        self._prompt = prompt
        self._system_instruction = system_instruction
        self.signals = _GeminiAssistSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            response = self._client.models.generate_content(
                model=self._model,
                contents=self._prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self._system_instruction,
                    temperature=0.3,
                    max_output_tokens=400,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            self.signals.finished.emit((response.text or "").strip())
        except Exception as exc:
            logger.error("Gemini assist failed", exc_info=True)
            self.signals.error.emit(f"Gemini assist failed: {exc}")


class GeminiAssistService(QObject):
    answer_ready = Signal(str)
    answer_started = Signal()
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, model: str | None = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key or GEMINI_ASSIST_API_KEY
        self._model = model or GEMINI_ASSIST_MODEL
        self._client = None
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return GEMINI_AVAILABLE and bool(self._api_key)

    def initialize(self) -> bool:
        if not self.is_available:
            self.error_occurred.emit("Gemini is unavailable.")
            return False
        self._client = genai.Client(api_key=self._api_key)
        return True

    def generate_answer(self, prompt: str, system_instruction: str) -> None:
        if not self._client and not self.initialize():
            return
        task = _GeminiAssistTask(self._client, self._model, prompt, system_instruction)
        self._track_task(task)
        task.signals.started.connect(self.answer_started.emit)
        task.signals.finished.connect(self.answer_ready.emit)
        task.signals.error.connect(self.error_occurred.emit)
        self._thread_pool.start(task)

    def set_model(self, model: str) -> None:
        self._model = model.strip()

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _answer, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))
