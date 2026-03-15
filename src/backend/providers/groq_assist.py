"""Groq text assist adapter."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import (
    GROQ_API_KEY,
    GROQ_ASSIST_MAX_TOKENS,
    GROQ_ASSIST_MODEL,
    GROQ_ASSIST_TEMPERATURE,
    GROQ_REQUEST_TIMEOUT,
)


logger = logging.getLogger("backend.providers.groq_assist")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None


class _GroqAssistSignals(QObject):
    started = Signal()
    finished = Signal(str)
    error = Signal(str)


class _GroqAssistTask(QRunnable):
    def __init__(self, client, prompt: str, system_instruction: str):
        super().__init__()
        self._client = client
        self._prompt = prompt
        self._system_instruction = system_instruction
        self.signals = _GroqAssistSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            response = self._client.chat.completions.create(
                model=GROQ_ASSIST_MODEL,
                messages=[
                    {"role": "system", "content": self._system_instruction},
                    {"role": "user", "content": self._prompt},
                ],
                max_tokens=GROQ_ASSIST_MAX_TOKENS,
                temperature=GROQ_ASSIST_TEMPERATURE,
                timeout=GROQ_REQUEST_TIMEOUT,
            )
            answer = response.choices[0].message.content.strip()
            self.signals.finished.emit(answer)
        except Exception as exc:
            logger.error("Groq assist failed", exc_info=True)
            self.signals.error.emit(f"Groq assist failed: {exc}")


class GroqAssistService(QObject):
    answer_ready = Signal(str)
    answer_started = Signal()
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key or GROQ_API_KEY
        self._client = None
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return GROQ_AVAILABLE and bool(self._api_key)

    def initialize(self) -> bool:
        if not self.is_available:
            self.error_occurred.emit("Groq is unavailable.")
            return False
        self._client = Groq(api_key=self._api_key)
        return True

    def generate_answer(self, prompt: str, system_instruction: str) -> None:
        if not self._client and not self.initialize():
            return
        task = _GroqAssistTask(self._client, prompt, system_instruction)
        self._track_task(task)
        task.signals.started.connect(self.answer_started.emit)
        task.signals.finished.connect(self.answer_ready.emit)
        task.signals.error.connect(self.error_occurred.emit)
        self._thread_pool.start(task)

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _answer, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))
