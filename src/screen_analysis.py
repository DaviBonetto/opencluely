"""Opencluely screen analysis service."""

from __future__ import annotations

import base64
import io
import logging
import os
import time

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


logger = logging.getLogger("screen_analysis")

try:
    from PIL import Image, ImageGrab

    PIL_AVAILABLE = True
    logger.info("Pillow imported successfully for Screen Analysis")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow is unavailable for Screen Analysis")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
    logger.info("Groq SDK imported successfully for Screen Analysis")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK is unavailable for Screen Analysis")


VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
VISION_TIMEOUT = 30

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
        started = pyqtSignal()
        completed = pyqtSignal(str)
        error = pyqtSignal(str)
        method_used = pyqtSignal(str)

    def __init__(self, groq_client):
        super().__init__()
        self.client = groq_client
        self.signals = self.Signals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.started.emit()
            logger.info("=== Screen Analysis started ===")

            screenshot = ImageGrab.grab()
            logger.info("[ScreenAnalysisTask] Screenshot captured: %s", screenshot.size)

            start_time = time.time()
            try:
                text = self._analyze_with_groq(screenshot)
                elapsed = time.time() - start_time
                logger.info("[ScreenAnalysisTask] Success in %.2fs", elapsed)
                self.signals.method_used.emit("Opencluely Screen Analysis")
                self.signals.completed.emit(text)
            except Exception as exc:
                logger.error("[ScreenAnalysisTask] Vision request failed: %s", exc)
                self.signals.error.emit(f"Screen analysis failed: {exc}")
        except Exception as exc:
            error_msg = f"Screen capture failed: {exc}"
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
            model=VISION_MODEL,
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
            timeout=VISION_TIMEOUT,
        )

        text = response.choices[0].message.content.strip()
        logger.info("[ScreenAnalysisTask] Generated %s characters", len(text))
        return text


class ScreenAnalysis(QObject):
    """Coordinates screenshot analysis with the Groq multimodal model."""

    analysis_started = pyqtSignal()
    analysis_completed = pyqtSignal(str)
    analysis_method = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self.vision_available = False
        self._init_groq_client()
        logger.info("[ScreenAnalysis] Initialized")

    def _init_groq_client(self):
        if not GROQ_AVAILABLE:
            logger.warning("[ScreenAnalysis] Groq SDK is unavailable")
            return

        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key or not api_key.startswith("gsk_"):
            logger.warning("[ScreenAnalysis] GROQ_API_KEY is not configured")
            return

        try:
            self.client = Groq(api_key=api_key)
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

        from PyQt5.QtCore import QThreadPool

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


if __name__ == "__main__":
    import sys

    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    analyzer = ScreenAnalysis()

    def on_completed(text):
        print(f"Extracted {len(text)} characters:")
        print(text[:500] + "..." if len(text) > 500 else text)
        app.quit()

    def on_error(message):
        print(f"Error: {message}")
        app.quit()

    def on_method(method):
        print(f"Method: {method}")

    analyzer.analysis_completed.connect(on_completed)
    analyzer.error_occurred.connect(on_error)
    analyzer.analysis_method.connect(on_method)

    print("Screen Analysis Test")
    print(f"  Vision available: {analyzer.vision_available}")
    print("\nCapturing screen in 2s...")

    QTimer.singleShot(2000, analyzer.capture_and_analyze)
    sys.exit(app.exec_())
