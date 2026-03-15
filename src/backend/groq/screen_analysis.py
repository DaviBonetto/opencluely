"""Opencluely screen analysis service powered by Groq vision."""

from __future__ import annotations

import base64
import io
import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ..settings import GROQ_API_KEY, GROQ_REQUEST_TIMEOUT, GROQ_VISION_MODEL


logger = logging.getLogger("backend.groq.screen_analysis")

try:
    from PIL import Image, ImageGrab

    PIL_AVAILABLE = True
    logger.info("Pillow imported successfully for Screen Analysis")
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageGrab = None
    logger.warning("Pillow is unavailable for Screen Analysis")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
    logger.info("Groq SDK imported successfully for Screen Analysis")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK is unavailable for Screen Analysis")


VISION_PROMPT = """You are Opencluely Assist.
Analyze this screenshot carefully.

If it shows code or a technical problem:
1. Identify the issue.
2. Provide the fix or the best answer.
3. Explain the reasoning briefly.

If it shows general text:
1. Summarize the important information.
2. Format the result clearly.

If it shows a UI:
1. Describe what is happening.
2. Suggest improvements if the UI appears broken or confusing.

Respond in the same language that best matches the content.
Be direct, precise, and use Markdown for code when useful.
"""


class ScreenAnalysisTask(QRunnable):
    """Captures the screen and sends it to the multimodal model."""

    class Signals(QObject):
        started = Signal()
        completed = Signal(str)
        error = Signal(str)
        method_used = Signal(str)

    def __init__(self, groq_client):
        super().__init__()
        self.client = groq_client
        self.signals = self.Signals()

    @Slot()
    def run(self):
        try:
            self.signals.started.emit()
            logger.info("=== Screen Analysis started ===")

            screenshot = ImageGrab.grab()
            logger.info("[ScreenAnalysisTask] Screenshot captured: %s", screenshot.size)

            text = self._analyze_with_groq(screenshot)
            logger.info("[ScreenAnalysisTask] Analysis complete")
            self.signals.method_used.emit("Opencluely Screen Analysis")
            self.signals.completed.emit(text)
        except Exception as exc:
            error_msg = f"Screen analysis failed: {exc}"
            logger.error("[ScreenAnalysisTask] %s", error_msg)
            self.signals.error.emit(error_msg)

    def _analyze_with_groq(self, screenshot: Image.Image) -> str:
        max_width = 1280
        max_height = 720

        if screenshot.width > max_width or screenshot.height > max_height:
            ratio = min(max_width / screenshot.width, max_height / screenshot.height)
            new_size = (int(screenshot.width * ratio), int(screenshot.height * ratio))
            screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug("[ScreenAnalysisTask] Resized screenshot to %s", screenshot.size)

        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=85)
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        response = self.client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            max_tokens=4000,
            temperature=0.1,
            timeout=GROQ_REQUEST_TIMEOUT,
        )

        text = response.choices[0].message.content.strip()
        logger.info("[ScreenAnalysisTask] Generated %s characters", len(text))
        return text


class ScreenAnalysis(QObject):
    """Coordinates screenshot analysis with the Groq multimodal model."""

    analysis_started = Signal()
    analysis_completed = Signal(str)
    analysis_method = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, api_key: str | None = None, parent=None):
        super().__init__(parent)
        self.client = None
        self.vision_available = False
        self._api_key = api_key or GROQ_API_KEY
        self._init_groq_client()
        logger.info("[ScreenAnalysis] Initialized")

    def _init_groq_client(self):
        if not PIL_AVAILABLE:
            logger.warning("[ScreenAnalysis] Pillow is unavailable")
            return

        if not GROQ_AVAILABLE:
            logger.warning("[ScreenAnalysis] Groq SDK is unavailable")
            return

        if not self._api_key or not self._api_key.startswith("gsk_"):
            logger.warning("[ScreenAnalysis] GROQ_API_KEY is not configured")
            return

        try:
            self.client = Groq(api_key=self._api_key)
            self.vision_available = True
            logger.info("[ScreenAnalysis] Groq vision is available")
        except Exception as exc:
            logger.error("[ScreenAnalysis] Failed to initialize Groq: %s", exc)

    def capture_and_analyze(self):
        """Start screenshot analysis on the global thread pool."""
        if not self.vision_available:
            self.error_occurred.emit(
                "Screen analysis is unavailable.\nConfigure GROQ_API_KEY to enable it."
            )
            return

        task = ScreenAnalysisTask(self.client)
        task.signals.started.connect(self._on_started)
        task.signals.completed.connect(self._on_completed)
        task.signals.error.connect(self._on_error)
        task.signals.method_used.connect(self._on_method)
        QThreadPool.globalInstance().start(task)

    def _on_started(self):
        self.analysis_started.emit()

    def _on_completed(self, text: str):
        self.analysis_completed.emit(text)

    def _on_error(self, error_msg: str):
        self.error_occurred.emit(error_msg)

    def _on_method(self, method: str):
        self.analysis_method.emit(method)
