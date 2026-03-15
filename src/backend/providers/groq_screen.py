"""Groq multimodal screen analysis adapter."""

from __future__ import annotations

import base64
import io
import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import GROQ_API_KEY, GROQ_REQUEST_TIMEOUT, GROQ_VISION_MODEL


logger = logging.getLogger("backend.providers.groq_screen")

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None


class _GroqScreenSignals(QObject):
    started = Signal()
    finished = Signal(str)
    error = Signal(str)


class _GroqScreenTask(QRunnable):
    def __init__(self, client, image, prompt: str):
        super().__init__()
        self._client = client
        self._image = image
        self._prompt = prompt
        self.signals = _GroqScreenSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
            resized = self._image.copy()
            if resized.width > 1280 or resized.height > 720:
                ratio = min(1280 / resized.width, 720 / resized.height)
                resized = resized.resize(
                    (int(resized.width * ratio), int(resized.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            response = self._client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
                temperature=0.1,
                timeout=GROQ_REQUEST_TIMEOUT,
            )
            self.signals.finished.emit(response.choices[0].message.content.strip())
        except Exception as exc:
            logger.error("Groq screen analysis failed", exc_info=True)
            self.signals.error.emit(f"Groq screen analysis failed: {exc}")


class GroqScreenAnalyzer(QObject):
    analysis_ready = Signal(str)
    analysis_started = Signal()
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key or GROQ_API_KEY
        self._client = None
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[object] = set()

    @property
    def is_available(self) -> bool:
        return GROQ_AVAILABLE and Image is not None and bool(self._api_key)

    def initialize(self) -> bool:
        if not self.is_available:
            self.error_occurred.emit("Groq vision is unavailable.")
            return False
        self._client = Groq(api_key=self._api_key)
        return True

    def analyze_image(self, image, prompt: str) -> None:
        if not self._client and not self.initialize():
            return
        task = _GroqScreenTask(self._client, image, prompt)
        self._track_task(task)
        task.signals.started.connect(self.analysis_started.emit)
        task.signals.finished.connect(self.analysis_ready.emit)
        task.signals.error.connect(self.error_occurred.emit)
        self._thread_pool.start(task)

    def _track_task(self, task) -> None:
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _summary, current=task: self._active_tasks.discard(current))
        task.signals.error.connect(lambda _error, current=task: self._active_tasks.discard(current))
