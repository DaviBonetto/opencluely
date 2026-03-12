"""Live Bar UI for Opencluely."""

from __future__ import annotations

import logging
import os

from PyQt5.QtCore import QPoint, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QMouseEvent
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from assist_service import AssistService

    ASSIST_AVAILABLE = True
except ImportError:
    ASSIST_AVAILABLE = False
    AssistService = None

try:
    from audio_capture import AudioCapture

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    AudioCapture = None

try:
    from context_manager import ContextManager

    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False
    ContextManager = None

try:
    from context_notes_manager import ContextNotesManager
except ImportError:
    from src.context_notes_manager import ContextNotesManager

try:
    from context_vault_manager import ContextVaultManager
except ImportError:
    from src.context_vault_manager import ContextVaultManager

try:
    from screen_analysis import ScreenAnalysis

    SCREEN_ANALYSIS_AVAILABLE = True
except ImportError:
    SCREEN_ANALYSIS_AVAILABLE = False
    ScreenAnalysis = None

try:
    from transcription_groq import TranscriberGroq

    TRANSCRIBER_AVAILABLE = True
except ImportError:
    TRANSCRIBER_AVAILABLE = False
    TranscriberGroq = None

try:
    from ui.context_vault_panel import ContextVaultPanel
except ImportError:
    from src.ui.context_vault_panel import ContextVaultPanel

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None


logger = logging.getLogger("live_bar")


LIVE_BAR_STYLESHEET = """
QMainWindow, QWidget#central {
    background: transparent;
}

QFrame#top_bar {
    background-color: #171717;
    border: 1px solid #2F2F2F;
    border-radius: 22px;
}

QFrame#content_container, QFrame#context_container {
    background-color: #101010;
    border: 1px solid #242424;
    border-radius: 16px;
}

QLabel {
    color: #FFFFFF;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

QLabel#title_label {
    font-size: 14px;
    font-weight: 700;
}

QLabel#status_label {
    color: #8F8F8F;
    font-size: 12px;
}

QLabel#timer_label {
    background-color: #000000;
    border-radius: 8px;
    color: #FFFFFF;
    font-family: Consolas, monospace;
    font-weight: 700;
    padding: 4px 10px;
}

QPushButton {
    background-color: #242424;
    border: 1px solid #343434;
    border-radius: 10px;
    color: #E4E4E4;
    font-size: 12px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #2D2D2D;
    border-color: #444444;
    color: #FFFFFF;
}

QPushButton#btn_primary {
    background-color: #0A84FF;
    border: none;
    color: #FFFFFF;
    font-weight: 700;
}

QPushButton#btn_recording {
    background-color: #4A1717;
    border: 1px solid #A43A3A;
}

QPushButton#btn_active {
    background-color: #18311E;
    border: 1px solid #2E8B57;
}

QTextEdit, QLineEdit, QComboBox {
    background-color: #1B1B1B;
    border: 1px solid #2E2E2E;
    border-radius: 10px;
    color: #F1F1F1;
    font-size: 13px;
    padding: 8px 10px;
}

QTextEdit#transcript_box {
    background-color: #121212;
    border: none;
    padding: 12px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QFrame#response_card {
    background-color: #191919;
    border: 1px solid #2E2E2E;
    border-radius: 14px;
}
"""


class ResponseCard(QFrame):
    """A compact response card for Assist and Screen Analysis results."""

    copy_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(object)

    def __init__(self, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setObjectName("response_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        question_label = QLabel(self.question)
        question_label.setWordWrap(True)
        question_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        header.addWidget(question_label, 1)

        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(lambda: self.copy_requested.emit(self.answer))
        header.addWidget(copy_button)

        delete_button = QPushButton("Remove")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self))
        header.addWidget(delete_button)

        layout.addLayout(header)

        answer_box = QTextEdit()
        answer_box.setReadOnly(True)
        answer_box.setMinimumHeight(120)
        answer_box.setStyleSheet(
            "QTextEdit { background-color: #121212; border: 1px solid #252525; "
            "border-radius: 10px; padding: 10px; color: #E7E7E7; }"
        )
        if hasattr(answer_box, "setMarkdown"):
            answer_box.setMarkdown(self.answer)
        else:
            answer_box.setPlainText(self.answer)
        layout.addWidget(answer_box)


class LiveBar(QMainWindow):
    """Floating session UI for transcription, Assist, and Context tooling."""

    def __init__(self, session_context: dict | None = None):
        super().__init__()
        self.session_context = session_context or {}
        self.is_recording = False
        self.is_expanded = False
        self.is_dragging = False
        self.is_resizing = False
        self.drag_position = QPoint()
        self.resize_start_height = 0
        self.min_height = 72
        self.max_height = 860
        self.seconds = 0
        self.timer_rec = None
        self.last_question = ""
        self.current_note_id = None
        self.hotkey_handle = None
        self.audio = None
        self.transcriber = None
        self.assist_service = None
        self.screen_analysis = None
        self.context = None
        self.context_notes_manager = None
        self.context_vault_manager = None
        self.context_vault_panel = None
        self.tray = None
        self.setup_window()
        self.setup_ui()
        self.setStyleSheet(LIVE_BAR_STYLESHEET)
        self.setup_backend()
        self.setup_tray()
        self.setup_hotkey()
        self.set_session_data(self.session_context)

    def setup_window(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.7)
        x_pos = int((screen.width() - width) / 2)
        self.setGeometry(x_pos, screen.y() + 20, width, self.min_height)

    def setup_ui(self) -> None:
        self.central = QWidget()
        self.central.setObjectName("central")
        self.setCentralWidget(self.central)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 170))
        shadow.setOffset(0, 6)
        self.central.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setFixedHeight(52)
        self.main_layout.addWidget(self.top_bar)

        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(14, 8, 14, 8)
        top_layout.setSpacing(8)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(1)
        self.title_label = QLabel("Opencluely Live Bar")
        self.title_label.setObjectName("title_label")
        title_stack.addWidget(self.title_label)
        self.status_label = QLabel("Profile: General Copilot")
        self.status_label.setObjectName("status_label")
        title_stack.addWidget(self.status_label)
        top_layout.addLayout(title_stack)

        self.record_indicator = QLabel("REC")
        self.record_indicator.setVisible(False)
        self.record_indicator.setStyleSheet(
            "color: #FF6B6B; font-size: 11px; font-weight: 700; "
            "background: #2B1212; border-radius: 8px; padding: 3px 8px;"
        )
        top_layout.addWidget(self.record_indicator)

        self.btn_mic = QPushButton("Mic")
        self.btn_mic.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_mic.clicked.connect(self.toggle_recording)
        top_layout.addWidget(self.btn_mic)

        self.btn_assist = QPushButton("Assist")
        self.btn_assist.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_assist.clicked.connect(self.on_assist)
        top_layout.addWidget(self.btn_assist)

        self.btn_screen_analysis = QPushButton("Screen Analysis")
        self.btn_screen_analysis.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_screen_analysis.clicked.connect(self.on_screen_analysis)
        top_layout.addWidget(self.btn_screen_analysis)

        self.btn_chat = QPushButton("Chat")
        self.btn_chat.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_chat.clicked.connect(self.toggle_content_area)
        top_layout.addWidget(self.btn_chat)

        self.btn_context = QPushButton("Context")
        self.btn_context.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_context.setToolTip("Show or hide Context")
        self.btn_context.clicked.connect(self.toggle_notes)
        top_layout.addWidget(self.btn_context)

        self.btn_context_vault = QPushButton("Vault")
        self.btn_context_vault.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_context_vault.setToolTip("Context Vault")
        self.btn_context_vault.clicked.connect(self.toggle_context_vault_panel)
        top_layout.addWidget(self.btn_context_vault)

        top_layout.addStretch()

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clear.clicked.connect(self.clear_all)
        top_layout.addWidget(self.btn_clear)

        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setVisible(False)
        top_layout.addWidget(self.timer_label)

        self.btn_menu = QPushButton("Menu")
        self.btn_menu.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_menu.clicked.connect(self.show_menu)
        top_layout.addWidget(self.btn_menu)

        self.btn_collapse = QPushButton("Open")
        self.btn_collapse.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_collapse.clicked.connect(self.toggle_content_area)
        top_layout.addWidget(self.btn_collapse)

        self.btn_close = QPushButton("Close")
        self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close.clicked.connect(self.close)
        top_layout.addWidget(self.btn_close)

        self.content_container = QFrame()
        self.content_container.setObjectName("content_container")
        self.content_container.setVisible(False)
        self.main_layout.addWidget(self.content_container, 1)

        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        self.txt_transcription = QTextEdit()
        self.txt_transcription.setObjectName("transcript_box")
        self.txt_transcription.setReadOnly(True)
        self.txt_transcription.setFixedHeight(100)
        self.txt_transcription.setPlaceholderText("Transcript will appear here.")
        content_layout.addWidget(self.txt_transcription)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        content_layout.addWidget(self.scroll_area, 1)

        self.response_pool = QWidget()
        self.response_layout = QVBoxLayout(self.response_pool)
        self.response_layout.setContentsMargins(2, 2, 2, 2)
        self.response_layout.setSpacing(10)
        self.response_layout.addStretch()
        self.scroll_area.setWidget(self.response_pool)

        chat_row = QHBoxLayout()
        chat_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Assist a follow-up or paste a prompt here.")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        chat_row.addWidget(self.chat_input, 1)

        self.btn_send = QPushButton("Send")
        self.btn_send.setObjectName("btn_primary")
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.clicked.connect(self.send_chat_message)
        chat_row.addWidget(self.btn_send)
        content_layout.addLayout(chat_row)

        self.context_container = QFrame()
        self.context_container.setObjectName("context_container")
        self.context_container.setVisible(False)
        self.context_container.setMinimumHeight(190)
        self.main_layout.addWidget(self.context_container)

        context_layout = QVBoxLayout(self.context_container)
        context_layout.setContentsMargins(12, 12, 12, 12)
        context_layout.setSpacing(8)

        context_header = QHBoxLayout()
        context_title = QLabel("Context")
        context_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        context_header.addWidget(context_title)

        self.combo_context_notes = QComboBox()
        self.combo_context_notes.currentIndexChanged.connect(self.on_note_selected)
        context_header.addWidget(self.combo_context_notes, 1)

        self.btn_add_context_note = QPushButton("Add")
        self.btn_add_context_note.clicked.connect(self.add_note)
        context_header.addWidget(self.btn_add_context_note)

        self.btn_rename_context_note = QPushButton("Rename")
        self.btn_rename_context_note.clicked.connect(self.rename_note)
        context_header.addWidget(self.btn_rename_context_note)

        self.btn_delete_context_note = QPushButton("Delete")
        self.btn_delete_context_note.clicked.connect(self.delete_note)
        context_header.addWidget(self.btn_delete_context_note)

        self.btn_close_context = QPushButton("Hide")
        self.btn_close_context.clicked.connect(self.toggle_notes)
        context_header.addWidget(self.btn_close_context)
        context_layout.addLayout(context_header)

        self.txt_context = QTextEdit()
        self.txt_context.setPlaceholderText("Capture notes, proof points, and follow-ups here.")
        self.txt_context.textChanged.connect(self.auto_save_note)
        context_layout.addWidget(self.txt_context, 1)

        self.resize_handle = QWidget()
        self.resize_handle.setObjectName("resize_handle")
        self.resize_handle.setFixedHeight(8)
        self.resize_handle.setCursor(QCursor(Qt.SizeVerCursor))
        self.main_layout.addWidget(self.resize_handle)

    def setup_backend(self) -> None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()

        if TRANSCRIBER_AVAILABLE and api_key:
            self.transcriber = TranscriberGroq(api_key)
            self.transcriber.transcription_ready.connect(self.on_transcription)
            self.transcriber.error_occurred.connect(
                lambda message: logger.warning("Transcription error: %s", message)
            )
            QTimer.singleShot(50, self.transcriber.load_model)

        if ASSIST_AVAILABLE and api_key:
            self.assist_service = AssistService(api_key, parent=self)
            self.assist_service.answer_started.connect(self.on_assist_started)
            self.assist_service.answer_ready.connect(self.on_assist_response)
            self.assist_service.error_occurred.connect(self.on_assist_error)
            self.assist_service.rate_limit_hit.connect(
                lambda: self.add_response("Assist", "Rate limit reached. Try again in a minute.")
            )
            QTimer.singleShot(100, self.assist_service.initialize)

        if SCREEN_ANALYSIS_AVAILABLE:
            self.screen_analysis = ScreenAnalysis(parent=self)
            self.screen_analysis.analysis_started.connect(self.on_screen_analysis_started)
            self.screen_analysis.analysis_completed.connect(self.on_screen_result)
            self.screen_analysis.analysis_method.connect(
                lambda method: logger.info("Screen analysis method: %s", method)
            )
            self.screen_analysis.error_occurred.connect(self.on_screen_error)

        if CONTEXT_AVAILABLE:
            self.context = ContextManager(parent=self)
            self.context.context_loaded.connect(self.on_context_loaded)
            self.context.context_cleared.connect(lambda: self.add_log("Loaded context cleared."))
            self.context.error_occurred.connect(lambda message: self.add_log(message))

        self.init_context_notes()
        self.init_context_vault()

    def setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Opencluely")

        menu = QMenu()
        toggle_action = QAction("Show or hide Live Bar", self)
        toggle_action.triggered.connect(self.toggle_visibility)
        menu.addAction(toggle_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def setup_hotkey(self) -> None:
        if not KEYBOARD_AVAILABLE:
            return

        try:
            self.hotkey_handle = keyboard.add_hotkey(
                "ctrl+shift+o",
                lambda: QTimer.singleShot(0, self.toggle_visibility),
            )
            logger.info("Registered Live Bar hotkey: Ctrl+Shift+O")
        except Exception as exc:
            logger.warning("Failed to register hotkey: %s", exc)
            self.hotkey_handle = None

    def set_session_data(self, session_context: dict | None) -> None:
        self.session_context = session_context or {}
        profile_name = self.session_context.get("profile_name") or "General Copilot"
        self.status_label.setText(f"Profile: {profile_name}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        resize_zone = 14
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if event.y() >= self.height() - resize_zone:
            self.is_resizing = True
            self.is_dragging = False
            self.drag_position = event.globalPos()
            self.resize_start_height = self.height()
            self.setCursor(QCursor(Qt.SizeVerCursor))
            event.accept()
            return

        self.is_dragging = True
        self.is_resizing = False
        self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        resize_zone = 14

        if not self.is_dragging and not self.is_resizing:
            if event.y() >= self.height() - resize_zone:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

        if self.is_resizing:
            delta_y = event.globalPos().y() - self.drag_position.y()
            new_height = self.resize_start_height + delta_y
            new_height = max(self.min_height, min(self.max_height, new_height))
            self.resize(self.width(), new_height)

            if new_height > 160 and not self.is_expanded:
                self.set_content_visibility(True)

            event.accept()
            return

        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.is_dragging = False
        self.is_resizing = False
        self.setCursor(QCursor(Qt.ArrowCursor))
        super().mouseReleaseEvent(event)

    def closeEvent(self, event) -> None:
        self.stop_recording()

        if self.transcriber and hasattr(self.transcriber, "cleanup"):
            self.transcriber.cleanup()

        if KEYBOARD_AVAILABLE and self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                logger.debug("Hotkey removal failed", exc_info=True)

        if self.context_vault_panel is not None:
            self.context_vault_panel.close()

        if self.tray is not None:
            self.tray.hide()

        super().closeEvent(event)

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
            return

        self.show()
        self.raise_()
        self.activateWindow()

    def show_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Load Context File", self.load_context)
        menu.addAction("Toggle Context", self.toggle_notes)
        menu.addAction("Toggle Context Vault", self.toggle_context_vault_panel)
        menu.addAction("Toggle Chat Area", self.toggle_content_area)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        menu.exec_(QCursor.pos())

    def toggle_recording(self) -> None:
        if self.is_recording:
            self.stop_recording()
            return

        if not AUDIO_AVAILABLE:
            self.add_response("Recording", "Audio capture is unavailable in this environment.")
            return

        if self.audio is not None:
            try:
                self.audio.stop_recording()
                self.audio.wait()
            except Exception:
                logger.debug("Previous audio thread cleanup failed", exc_info=True)

        self.audio = AudioCapture()
        self.audio.audio_chunk_ready.connect(self.on_audio_data)
        self.audio.error_occurred.connect(lambda message: self.add_log(message))
        self.audio.recording_stopped.connect(self.on_recording_stopped)
        self.audio.start()

        self.is_recording = True
        self.btn_mic.setText("Stop")
        self.btn_mic.setObjectName("btn_recording")
        self.btn_mic.style().unpolish(self.btn_mic)
        self.btn_mic.style().polish(self.btn_mic)
        self.record_indicator.setVisible(True)
        self.timer_label.setVisible(True)
        self.txt_transcription.setPlaceholderText("Listening...")
        self.start_timer()
        self.ensure_content_visible()

    def stop_recording(self) -> None:
        if self.audio is not None:
            try:
                self.audio.stop_recording()
                self.audio.wait()
            except Exception:
                logger.debug("Audio thread stop failed", exc_info=True)
        self.on_recording_stopped()

    def on_recording_stopped(self) -> None:
        self.is_recording = False
        self.audio = None
        self.btn_mic.setText("Mic")
        self.btn_mic.setObjectName("")
        self.btn_mic.style().unpolish(self.btn_mic)
        self.btn_mic.style().polish(self.btn_mic)
        self.record_indicator.setVisible(False)
        self.timer_label.setVisible(False)
        self.txt_transcription.setPlaceholderText("Transcript will appear here.")

        if self.timer_rec is not None:
            self.timer_rec.stop()

    def start_timer(self) -> None:
        self.seconds = 0
        self.timer_label.setText("00:00")

        if self.timer_rec is None:
            self.timer_rec = QTimer(self)
            self.timer_rec.timeout.connect(self.update_timer)

        self.timer_rec.start(1000)

    def update_timer(self) -> None:
        if not self.is_recording:
            if self.timer_rec is not None:
                self.timer_rec.stop()
            return

        self.seconds += 1
        minutes, seconds = divmod(self.seconds, 60)
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def on_audio_data(self, chunk: bytes) -> None:
        if self.transcriber is None:
            return
        self.transcriber.transcribe_chunk(chunk)

    def on_transcription(self, text: str) -> None:
        clean_text = (text or "").strip()
        if not clean_text:
            return

        self.txt_transcription.append(clean_text)
        self.last_question = clean_text
        self.ensure_content_visible()

    def add_log(self, text: str) -> None:
        clean_text = (text or "").strip()
        if not clean_text:
            return
        self.txt_transcription.append(f"[info] {clean_text}")

    def on_assist(self) -> None:
        if self.assist_service is None:
            self.add_response("Assist", "Assist is unavailable. Configure GROQ_API_KEY to enable it.")
            return

        transcript = self.txt_transcription.toPlainText().strip()
        question = transcript or self.last_question.strip()
        if not question:
            self.add_response("Assist", "Record audio, type a prompt, or capture a screen first.")
            return

        self.last_question = question
        reference_context = self.build_reference_context(include_transcript=False)
        self.ensure_content_visible()
        self.assist_service.generate_answer(question, reference_context, self.session_context)

    def on_assist_started(self) -> None:
        self.btn_assist.setEnabled(False)
        self.btn_assist.setText("Working...")
        self.btn_send.setEnabled(False)
        self.chat_input.setPlaceholderText("Assist is generating a response...")

    def on_assist_response(self, answer: str) -> None:
        self.reset_assist_controls()
        self.add_response(self.last_question or "Assist", answer)

    def on_assist_error(self, message: str) -> None:
        self.reset_assist_controls()
        self.add_response("Assist", message)

    def reset_assist_controls(self) -> None:
        self.btn_assist.setEnabled(True)
        self.btn_assist.setText("Assist")
        self.btn_send.setEnabled(True)
        self.chat_input.setPlaceholderText("Ask Assist a follow-up or paste a prompt here.")

    def on_screen_analysis(self) -> None:
        if self.screen_analysis is None:
            self.add_response("Screen Analysis", "Screen Analysis is unavailable in this environment.")
            return

        self.hide()
        QTimer.singleShot(350, self._run_screen_analysis)

    def _run_screen_analysis(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.btn_screen_analysis.setEnabled(False)
        self.btn_screen_analysis.setText("Working...")
        self.ensure_content_visible()
        self.screen_analysis.capture_and_analyze()

    def on_screen_analysis_started(self) -> None:
        self.txt_transcription.setPlaceholderText("Running Screen Analysis...")

    def on_screen_result(self, text: str) -> None:
        self.btn_screen_analysis.setEnabled(True)
        self.btn_screen_analysis.setText("Screen Analysis")
        self.txt_transcription.setPlaceholderText("Transcript will appear here.")
        self.add_response("Screen Analysis", text)

    def on_screen_error(self, message: str) -> None:
        self.btn_screen_analysis.setEnabled(True)
        self.btn_screen_analysis.setText("Screen Analysis")
        self.txt_transcription.setPlaceholderText("Transcript will appear here.")
        self.add_response("Screen Analysis", message)

    def clear_all(self) -> None:
        self.txt_transcription.clear()
        self.last_question = ""
        self.txt_transcription.setPlaceholderText("Transcript cleared.")

        while self.response_layout.count() > 1:
            item = self.response_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self.context is not None and self.context.has_context():
            self.context.clear_context()

    def add_response(self, question: str, answer: str) -> None:
        label = self._trim_text(question or "Assist", 140)
        card = ResponseCard(label, answer or "")
        card.copy_requested.connect(self.copy_to_clipboard)
        card.delete_requested.connect(self.remove_card)

        insert_index = self.response_layout.count() - 1
        self.response_layout.insertWidget(insert_index, card)
        QTimer.singleShot(
            50,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

    def copy_to_clipboard(self, text: str) -> None:
        QApplication.clipboard().setText(text)

    def remove_card(self, card: ResponseCard) -> None:
        card.deleteLater()

    def send_chat_message(self) -> None:
        message = self.chat_input.text().strip()
        if not message:
            return

        self.chat_input.clear()
        self.last_question = message

        if self.assist_service is None:
            self.add_response("Assist", "Assist is unavailable. Configure GROQ_API_KEY to enable it.")
            return

        reference_context = self.build_reference_context(include_transcript=True)
        self.ensure_content_visible()
        self.assist_service.generate_answer(message, reference_context, self.session_context)

    def init_context_notes(self) -> None:
        self.context_notes_manager = ContextNotesManager()
        self.current_note_id = None
        self.refresh_notes_list()

    def refresh_notes_list(self) -> None:
        self.combo_context_notes.blockSignals(True)
        self.combo_context_notes.clear()

        for note_id, title in self.context_notes_manager.get_titles():
            self.combo_context_notes.addItem(title, note_id)

        self.combo_context_notes.blockSignals(False)

        if self.combo_context_notes.count() == 0:
            self.current_note_id = None
            self.txt_context.clear()
            return

        if self.current_note_id is not None:
            index = self.combo_context_notes.findData(self.current_note_id)
            if index >= 0:
                self.combo_context_notes.setCurrentIndex(index)
            else:
                self.combo_context_notes.setCurrentIndex(0)
        else:
            self.combo_context_notes.setCurrentIndex(0)

        self.on_note_selected(self.combo_context_notes.currentIndex())

    def on_note_selected(self, index: int) -> None:
        if index < 0:
            return

        note_id = self.combo_context_notes.currentData()
        note = self.context_notes_manager.get_by_id(note_id)
        if note is None:
            return

        self.current_note_id = note_id
        self.txt_context.blockSignals(True)
        self.txt_context.setPlainText(note.content)
        self.txt_context.blockSignals(False)

    def auto_save_note(self) -> None:
        if self.current_note_id is None:
            return

        self.context_notes_manager.update(
            self.current_note_id,
            content=self.txt_context.toPlainText(),
        )

    def add_note(self) -> None:
        title, ok = QInputDialog.getText(self, "New Context Note", "Title:")
        if not ok or not title.strip():
            return

        note = self.context_notes_manager.add(title.strip(), "")
        self.current_note_id = note.id
        self.refresh_notes_list()

    def rename_note(self) -> None:
        if self.current_note_id is None:
            return

        note = self.context_notes_manager.get_by_id(self.current_note_id)
        if note is None:
            return

        title, ok = QInputDialog.getText(self, "Rename Context Note", "Title:", text=note.title)
        if not ok or not title.strip():
            return

        self.context_notes_manager.update(self.current_note_id, title=title.strip())
        self.refresh_notes_list()

    def delete_note(self) -> None:
        if self.current_note_id is None:
            self.add_response("Context", "No context note is selected.")
            return

        answer = QMessageBox.question(
            self,
            "Delete Context Note",
            "Delete the selected context note?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.context_notes_manager.delete(self.current_note_id)
        self.current_note_id = None
        self.refresh_notes_list()

    def toggle_notes(self) -> None:
        is_visible = self.context_container.isVisible()
        next_visible = not is_visible
        self.context_container.setVisible(next_visible)
        self._set_context_button_active(next_visible)

        if next_visible:
            self.ensure_content_visible(min_height=620)
        elif not self.is_expanded:
            self.resize(self.width(), self.min_height)

    def init_context_vault(self) -> None:
        self.context_vault_manager = ContextVaultManager()
        self.context_vault_panel = ContextVaultPanel(self.context_vault_manager, None)
        self.context_vault_panel.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.context_vault_panel.closed.connect(self.on_context_vault_closed)
        self.context_vault_panel.resize(560, 660)
        self.context_vault_panel.hide()

    def toggle_context_vault_panel(self) -> None:
        if self.context_vault_panel is None:
            return

        if self.context_vault_panel.isVisible():
            self.context_vault_panel.hide()
            self.on_context_vault_closed()
            return

        screen = QApplication.primaryScreen().availableGeometry()
        panel_width = self.context_vault_panel.width()
        panel_height = self.context_vault_panel.height()
        center_x = screen.x() + (screen.width() - panel_width) // 2
        center_y = screen.y() + (screen.height() - panel_height) // 2

        self.context_vault_panel.move(center_x, center_y)
        self.context_vault_panel.show()
        self.context_vault_panel.raise_()
        self.context_vault_panel.activateWindow()
        self.btn_context_vault.setObjectName("btn_active")
        self.btn_context_vault.style().unpolish(self.btn_context_vault)
        self.btn_context_vault.style().polish(self.btn_context_vault)

    def on_context_vault_closed(self) -> None:
        self.btn_context_vault.setObjectName("")
        self.btn_context_vault.style().unpolish(self.btn_context_vault)
        self.btn_context_vault.style().polish(self.btn_context_vault)

    def toggle_content_area(self) -> None:
        self.set_content_visibility(not self.is_expanded)

    def set_content_visibility(self, visible: bool) -> None:
        self.is_expanded = visible
        self.content_container.setVisible(visible)
        self.btn_collapse.setText("Hide" if visible else "Open")

        if visible:
            if self.height() < 460:
                self.resize(self.width(), 460)
            return

        if not self.context_container.isVisible():
            self.resize(self.width(), self.min_height)

    def ensure_content_visible(self, min_height: int = 460) -> None:
        if not self.is_expanded:
            self.set_content_visibility(True)
        if self.height() < min_height:
            self.resize(self.width(), min_height)

    def load_context(self) -> None:
        if self.context is None:
            self.add_response("Context", "Document context loading is unavailable in this environment.")
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Context",
            "",
            "Documents (*.pdf *.docx *.txt *.md);;All Files (*.*)",
        )
        if path:
            self.context.load_file(path)

    def on_context_loaded(self, filename: str, char_count: int) -> None:
        self.add_log(f"Loaded context: {filename} ({char_count} chars)")

    def build_reference_context(self, include_transcript: bool = True) -> str:
        parts = []

        session_brief = self.session_context.get("user_context", "").strip()
        if session_brief:
            parts.append(f"SESSION BRIEF\n{self._trim_text(session_brief, 2500)}")

        if self.context is not None and self.context.has_context():
            parts.append(f"LOADED CONTEXT\n{self._trim_text(self.context.get_context(), 5000)}")

        notes = self.txt_context.toPlainText().strip()
        if notes:
            parts.append(f"CONTEXT NOTES\n{self._trim_text(notes, 2500)}")

        if include_transcript:
            transcript = self.txt_transcription.toPlainText().strip()
            if transcript:
                parts.append(f"TRANSCRIPT\n{self._trim_text(transcript, 3500)}")

        return "\n\n".join(parts)

    @staticmethod
    def _trim_text(text: str, limit: int) -> str:
        clean_text = (text or "").strip()
        if len(clean_text) <= limit:
            return clean_text
        return f"{clean_text[:limit].rstrip()}\n\n[truncated]"

    def _set_context_button_active(self, is_active: bool) -> None:
        self.btn_context.setObjectName("btn_active" if is_active else "")
        self.btn_context.style().unpolish(self.btn_context)
        self.btn_context.style().polish(self.btn_context)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    window = LiveBar(
        {
            "profile_name": "General Copilot",
            "system_instructions": "",
            "user_context": "",
            "language": "english (us)",
        }
    )
    window.show()
    sys.exit(app.exec_())
