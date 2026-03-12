"""Opencluely assist service."""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, timedelta

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


logger = logging.getLogger("assist_service")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
    logger.info("Groq SDK imported successfully for Assist")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK is unavailable for Assist")


ASSIST_MODEL = "llama-3.3-70b-versatile"
ASSIST_MAX_TOKENS = 500
ASSIST_TEMPERATURE = 0.7
ASSIST_TIMEOUT = 15.0
RATE_LIMIT = 30

SYSTEM_PROMPT = """You are Opencluely Assist, a live session copilot.

Help the user respond clearly in meetings, demos, support calls, and problem-solving sessions.

Rules:
- Answer in the same language as the request when possible.
- Prefer spoken-ready responses that are brief, concrete, and easy to deliver.
- Use the supplied session brief and reference material when they are available.
- When code is needed, provide the smallest correct solution plus a short explanation.
- If context is missing, make the safest reasonable assumption and state it plainly.
- Avoid filler, hype, and generic prefaces.
"""


class AssistTask(QRunnable):
    """Runs a single Assist request off the UI thread."""

    class Signals(QObject):
        started = pyqtSignal()
        finished = pyqtSignal(str)
        error = pyqtSignal(str)

    def __init__(
        self,
        client,
        question: str,
        reference_context: str = "",
        session_context: dict = None,
    ):
        super().__init__()
        self.client = client
        self.question = question
        self.reference_context = reference_context
        self.session_context = session_context or {}
        self.signals = self.Signals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.started.emit()
            logger.info("[AssistTask] Generating response for '%s...'", self.question[:50])

            user_prompt = (
                f'Session prompt: "{self.question}"\n\n'
                "Generate the clearest useful response for what the user should say, type, or do next."
            )

            if self.session_context.get("system_instructions"):
                system_prompt = self.session_context["system_instructions"]
                logger.info("[AssistTask] Using profile system instructions")
            else:
                system_prompt = SYSTEM_PROMPT

            if self.session_context.get("profile_name"):
                system_prompt += f"\n\nACTIVE PROFILE:\n{self.session_context['profile_name']}"

            if self.session_context.get("user_context"):
                system_prompt += f"\n\nSESSION BRIEF:\n{self.session_context['user_context']}"

            if self.reference_context:
                system_prompt += f"\n\nREFERENCE MATERIAL:\n{self.reference_context}"

            response = self.client.chat.completions.create(
                model=ASSIST_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=ASSIST_MAX_TOKENS,
                temperature=ASSIST_TEMPERATURE,
                timeout=ASSIST_TIMEOUT,
            )

            answer = response.choices[0].message.content.strip()
            logger.info("[AssistTask] Generated %s characters", len(answer))
            self.signals.finished.emit(answer)
        except Exception as exc:
            error_msg = f"Error generating Assist response: {exc}"
            logger.error("[AssistTask] %s", error_msg)
            logger.error(traceback.format_exc())
            self.signals.error.emit(error_msg)


class AssistService(QObject):
    """Coordinates Groq-backed Assist responses with rate limiting."""

    answer_ready = pyqtSignal(str)
    answer_started = pyqtSignal()
    error_occurred = pyqtSignal(str)
    rate_limit_hit = pyqtSignal()

    def __init__(self, api_key: str = None, parent=None):
        super().__init__(parent)
        self._client = None
        self._api_key = api_key
        self._is_ready = False
        self._is_processing = False
        self._request_count = 0
        self._last_reset = datetime.now()
        self._thread_pool = QThreadPool.globalInstance()
        logger.info("[AssistService] Initialized")

    def initialize(self):
        """Create the Groq client when the API key is available."""
        logger.info("[AssistService] Initializing Groq client")

        if not GROQ_AVAILABLE:
            error_msg = "Groq SDK is unavailable. Install it with: pip install groq"
            logger.error("[AssistService] %s", error_msg)
            self.error_occurred.emit(error_msg)
            return False

        if not self._api_key:
            error_msg = "API key is not configured"
            logger.error("[AssistService] %s", error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            self._client = Groq(api_key=self._api_key)
            self._is_ready = True
            logger.info("[AssistService] Groq client configured")
            return True
        except Exception as exc:
            error_msg = f"Error configuring Groq: {exc}"
            logger.error("[AssistService] %s", error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def generate_answer(
        self,
        question: str,
        reference_context: str = "",
        session_context: dict = None,
    ):
        """Generate a response without blocking the UI thread."""
        if not self._is_ready:
            self.error_occurred.emit("Assist service is not initialized")
            return

        if self._is_processing:
            logger.warning("[AssistService] A request is already in progress")
            return

        if not question or not question.strip():
            self.error_occurred.emit("The request is empty")
            return

        if not self._check_rate_limit():
            logger.warning("[AssistService] Rate limit reached")
            self.rate_limit_hit.emit()
            return

        self._is_processing = True
        task = AssistTask(self._client, question.strip(), reference_context, session_context)
        task.signals.started.connect(self._on_task_started)
        task.signals.finished.connect(self._on_task_finished)
        task.signals.error.connect(self._on_task_error)
        self._thread_pool.start(task)

    def _check_rate_limit(self) -> bool:
        self._reset_counter_if_needed()
        return self._request_count < RATE_LIMIT

    def _reset_counter_if_needed(self):
        now = datetime.now()
        if (now - self._last_reset) >= timedelta(minutes=1):
            self._request_count = 0
            self._last_reset = now
            logger.info("[AssistService] Rate limit counter reset")

    def _on_task_started(self):
        self._request_count += 1
        logger.info("[AssistService] Requests this minute: %s/%s", self._request_count, RATE_LIMIT)
        self.answer_started.emit()

    def _on_task_finished(self, answer: str):
        self._is_processing = False
        self.answer_ready.emit(answer)

    def _on_task_error(self, error_msg: str):
        self._is_processing = False
        self.error_occurred.emit(error_msg)

    def is_ready(self) -> bool:
        return self._is_ready

    def is_processing(self) -> bool:
        return self._is_processing

    def get_request_count(self) -> tuple:
        self._reset_counter_if_needed()
        return (self._request_count, RATE_LIMIT)


if __name__ == "__main__":
    import os
    import sys

    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Configure GROQ_API_KEY before running this test")
        sys.exit(1)

    def on_started():
        print("Generating Assist response...")

    def on_ready(answer):
        print(f"\nResponse:\n{answer}\n")
        app.quit()

    def on_error(message):
        print(f"Error: {message}")
        app.quit()

    app = QApplication(sys.argv)

    assist = AssistService(api_key=api_key)
    assist.initialize()
    assist.answer_started.connect(on_started)
    assist.answer_ready.connect(on_ready)
    assist.error_occurred.connect(on_error)
    assist.generate_answer("How should I frame a risky API change for a stakeholder update?")

    QTimer.singleShot(30000, app.quit)
    sys.exit(app.exec_())
