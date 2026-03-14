"""Live Bar UI for Opencluely."""

from __future__ import annotations

import logging
import os

from PyQt5.QtCore import QEvent, QPoint, QSize, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon, QKeySequence, QMouseEvent
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
    QShortcut,
    QStackedWidget,
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

# ── Styles & icons are in src.ui.styles ──────────────────────
try:
    from ui.styles import LIVE_BAR_STYLESHEET, RESPONSE_ANSWER_STYLE, render_svg_icon
except ImportError:
    from src.ui.styles import LIVE_BAR_STYLESHEET, RESPONSE_ANSWER_STYLE, render_svg_icon





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
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)
        question_label = QLabel(self.question)
        question_label.setObjectName("response_title")
        question_label.setWordWrap(True)
        header.addWidget(question_label, 1)

        copy_button = QPushButton("Copy")
        copy_button.setObjectName("card_button")
        copy_button.clicked.connect(lambda: self.copy_requested.emit(self.answer))
        header.addWidget(copy_button)

        delete_button = QPushButton("Remove")
        delete_button.setObjectName("card_button")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self))
        header.addWidget(delete_button)

        layout.addLayout(header)

        answer_box = QTextEdit()
        answer_box.setReadOnly(True)
        answer_box.setMinimumHeight(132)
        answer_box.setStyleSheet(RESPONSE_ANSWER_STYLE)
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
        self.current_profile_name = "Blank Brief"
        self.is_recording = False
        self.is_expanded = False
        self.is_dragging = False
        self.drag_position = QPoint()
        self.drag_hot_zone = None
        self.active_surface = "ask"
        self.vision_mode = "visible"
        self.smart_mode = False
        self.min_height = 92
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
        self.escape_shortcut = None
        self.suggestion_buttons = []
        self.visual_only = True
        self.setup_window()
        self.setup_ui()
        self.setStyleSheet(LIVE_BAR_STYLESHEET)
        if not self.visual_only:
            self.setup_backend()
            self.setup_tray()
            self.setup_hotkey()
        self.set_session_data(self.session_context)

    def setup_window(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().availableGeometry()
        width = 744
        height = 228
        x_pos = screen.x() + (screen.width() - width) // 2
        y_pos = screen.y() + 24
        self.min_height = height
        self.max_height = height
        self.setGeometry(x_pos, y_pos, width, height)

    def setup_ui(self) -> None:
        self.central = QWidget()
        self.central.setObjectName("central")
        self.setCentralWidget(self.central)

        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(22, 12, 22, 12)
        self.main_layout.setSpacing(8)

        self.top_row = QWidget()
        self.top_row.setObjectName("top_row")
        self.main_layout.addWidget(self.top_row, 0, Qt.AlignHCenter)

        top_row_layout = QHBoxLayout(self.top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(8)
        top_row_layout.addStretch()

        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setAccessibleName("Opencluely controls")
        self.top_bar.setFixedHeight(38)
        top_row_layout.addWidget(self.top_bar)
        self._apply_panel_shadow(self.top_bar, blur=16, y_offset=4)

        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(10, 4, 10, 4)
        top_layout.setSpacing(9)

        vision_group = self._make_segment("top_inner_group")
        vision_layout = QHBoxLayout(vision_group)
        vision_layout.setContentsMargins(2, 2, 2, 2)
        vision_layout.setSpacing(2)

        self.btn_eye_mode = self._make_icon_button(
            "glass_icon_button",
            "eye",
            "Visible screen mode",
            tooltip="Use visible screen mode",
        )
        self.btn_eye_mode.clicked.connect(self._noop)
        vision_layout.addWidget(self.btn_eye_mode)

        self.btn_privacy_mode = self._make_icon_button(
            "glass_icon_button",
            "anonymous",
            "Anonymous mode",
            tooltip="Use anonymous mode",
        )
        self.btn_privacy_mode.clicked.connect(self._noop)
        vision_layout.addWidget(self.btn_privacy_mode)
        top_layout.addWidget(vision_group)

        top_layout.addWidget(self._make_divider())

        media_group = self._make_segment("top_inner_group")
        media_layout = QHBoxLayout(media_group)
        media_layout.setContentsMargins(2, 2, 2, 2)
        media_layout.setSpacing(2)

        self.btn_pause = self._make_icon_button(
            "glass_icon_button",
            "pause",
            "Toggle live listening",
            tooltip="Start or stop live listening",
        )
        self.btn_pause.clicked.connect(self._noop)
        media_layout.addWidget(self.btn_pause)

        self.btn_stop_transport = self._make_icon_button(
            "glass_icon_button",
            "stop",
            "Stop listening",
            tooltip="Stop listening and clear active capture",
        )
        self.btn_stop_transport.clicked.connect(self._noop)
        media_layout.addWidget(self.btn_stop_transport)
        
        self.record_indicator = QLabel("LIVE")
        self.record_indicator.setObjectName("record_indicator")
        self.record_indicator.hide()
        media_layout.addWidget(self.record_indicator)
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timer_label")
        self.timer_label.hide()
        media_layout.addWidget(self.timer_label)

        top_layout.addWidget(media_group)

        top_layout.addWidget(self._make_divider())

        control_group = QWidget()
        control_layout = QHBoxLayout(control_group)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(2)

        self.btn_collapse = self._make_icon_button(
            "glass_icon_button",
            "chevron_up",
            "Expand or collapse the assistant",
            tooltip="Expand or collapse the assistant",
        )
        self.btn_collapse.clicked.connect(self._noop)
        control_layout.addWidget(self.btn_collapse)

        self.btn_grip = self._make_icon_button(
            "glass_icon_button",
            "grip",
            "Drag live bar",
            tooltip="Drag live bar",
        )
        self.btn_grip.setCursor(QCursor(Qt.OpenHandCursor))
        self.btn_grip.clicked.connect(self._noop)
        control_layout.addWidget(self.btn_grip)
        top_layout.addWidget(control_group)

        self.btn_close = self._make_icon_button(
            "top_close_button",
            "close",
            "Close live bar",
            tooltip="Close live bar",
            button_size=QSize(38, 38),
            icon_size=QSize(16, 16),
        )
        self.btn_close.clicked.connect(self.close)
        top_row_layout.addWidget(self.btn_close)
        self._apply_panel_shadow(self.btn_close, blur=14, y_offset=4)
        top_row_layout.addStretch()

        self.profile_chip = None
        self.brand_label = None

        self.content_container = QFrame()
        self.content_container.setObjectName("glass_sheet")
        self.content_container.setFixedWidth(700)
        self.content_container.setVisible(True)
        self.main_layout.addWidget(self.content_container, 0, Qt.AlignHCenter)
        self._apply_panel_shadow(self.content_container, blur=40, y_offset=18)

        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(16, 12, 16, 13)
        content_layout.setSpacing(10)

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        self.btn_context = self._make_icon_button(
            "header_home_button",
            "home",
            "Toggle session notes",
            tooltip="Toggle session notes",
            button_size=QSize(30, 30),
            icon_size=QSize(15, 15),
            active_color="#F4F5F8",
            inactive_color="#E7E9EE",
        )
        self.btn_context.clicked.connect(self._noop)
        header_layout.addWidget(self.btn_context)

        self.btn_tab_ask = QPushButton("Chat")
        self.btn_tab_ask.setObjectName("surface_tab")
        self.btn_tab_ask.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_tab_ask.setAccessibleName("Show chat surface")
        self.btn_tab_ask.clicked.connect(self._noop)
        header_layout.addWidget(self.btn_tab_ask)

        self.btn_tab_transcript = QPushButton("Transcript")
        self.btn_tab_transcript.setObjectName("surface_tab")
        self.btn_tab_transcript.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_tab_transcript.setAccessibleName("Show transcript surface")
        self.btn_tab_transcript.clicked.connect(self._noop)
        header_layout.addWidget(self.btn_tab_transcript)

        header_layout.addStretch()

        self.btn_menu = self._make_icon_button(
            "header_expand_button",
            "expand",
            "Open assistant actions",
            tooltip="Open assistant actions",
            icon_size=QSize(14, 14),
        )
        self.btn_menu.clicked.connect(self._noop)
        header_layout.addWidget(self.btn_menu)
        content_layout.addWidget(header_row)

        self.quick_actions_row = QFrame()
        self.quick_actions_row.setObjectName("quick_actions_row")
        quick_actions_layout = QHBoxLayout(self.quick_actions_row)
        quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        quick_actions_layout.setSpacing(7)

        self.btn_assist = self._make_quick_action_button("Assist", self._noop, "sparkles")
        quick_actions_layout.addWidget(self.btn_assist)
        quick_actions_layout.addWidget(self._make_dot_label())

        self.btn_suggest_next = self._make_quick_action_button(
            "What should I say?",
            self._noop,
            "wand",
        )
        quick_actions_layout.addWidget(self.btn_suggest_next)
        quick_actions_layout.addWidget(self._make_dot_label())

        self.btn_suggest_followup = self._make_quick_action_button(
            "Follow-up questions",
            self._noop,
            "message_plus",
        )
        quick_actions_layout.addWidget(self.btn_suggest_followup)
        quick_actions_layout.addWidget(self._make_dot_label())

        self.btn_suggest_recap = self._make_quick_action_button(
            "Recap",
            self._noop,
            "rotate",
        )
        quick_actions_layout.addWidget(self.btn_suggest_recap)
        quick_actions_layout.addStretch()
        content_layout.addWidget(self.quick_actions_row)

        self.suggestion_buttons = [
            self.btn_assist,
            self.btn_suggest_next,
            self.btn_suggest_followup,
            self.btn_suggest_recap,
        ]

        self.content_stack = QStackedWidget()
        ask_page = QWidget()
        ask_page.setObjectName("ask_page")
        ask_layout = QVBoxLayout(ask_page)
        ask_layout.setContentsMargins(0, 0, 0, 0)
        ask_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("response_scroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        ask_layout.addWidget(self.scroll_area, 1)

        self.response_pool = QWidget()
        self.response_pool.setObjectName("response_pool")
        self.response_pool.setStyleSheet("background: transparent;")
        self.response_layout = QVBoxLayout(self.response_pool)
        self.response_layout.setContentsMargins(0, 0, 0, 0)
        self.response_layout.setSpacing(10)
        self.empty_state = QLabel(
            "Assist responses will appear here. Start with a suggestion above or ask a direct question."
        )
        self.empty_state.setObjectName("empty_state")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.response_layout.addWidget(self.empty_state)
        self.response_layout.addStretch()
        self.scroll_area.setWidget(self.response_pool)

        transcript_page = QWidget()
        transcript_page.setObjectName("transcript_page")
        transcript_layout = QVBoxLayout(transcript_page)
        transcript_layout.setContentsMargins(0, 0, 0, 0)
        transcript_layout.setSpacing(0)

        self.txt_transcription = QTextEdit()
        self.txt_transcription.setObjectName("transcript_box")
        self.txt_transcription.setReadOnly(True)
        self.txt_transcription.setPlaceholderText("Live transcript will appear here.")
        transcript_layout.addWidget(self.txt_transcription)

        self.content_stack.addWidget(ask_page)
        self.content_stack.addWidget(transcript_page)
        self.content_stack.hide()

        composer_shell = QFrame()
        composer_shell.setObjectName("composer_shell")
        content_layout.addWidget(composer_shell)

        composer_layout = QVBoxLayout(composer_shell)
        composer_layout.setContentsMargins(12, 8, 10, 8)
        composer_layout.setSpacing(7)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(4, 0, 4, 0)
        input_row.setSpacing(6)

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("chat_input")
        self.chat_input.setPlaceholderText("Ask about your screen or conversation, or")
        input_row.addWidget(self.chat_input, 1)

        shortcut_layout = QHBoxLayout()
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setSpacing(3)
        shortcut_layout.addWidget(self._make_shortcut_chip("Ctrl"))
        shortcut_layout.addWidget(self._make_shortcut_chip("Enter"))

        shortcut_hint = QLabel("for Assist")
        shortcut_hint.setObjectName("shortcut_hint")
        shortcut_layout.addWidget(shortcut_hint)
        input_row.addLayout(shortcut_layout)
        composer_layout.addLayout(input_row)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.setSpacing(6)

        toolbar_left = QHBoxLayout()
        toolbar_left.setContentsMargins(0, 0, 0, 0)
        toolbar_left.setSpacing(7)

        self.btn_screen_analysis = QPushButton("Use Screen")
        self.btn_screen_analysis.setObjectName("toolbar_button_primary")
        self.btn_screen_analysis.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_screen_analysis.setToolTip("Capture and analyze the current screen")
        self.btn_screen_analysis.setAccessibleName("Use screen")
        self.btn_screen_analysis.clicked.connect(self._noop)
        self._set_text_button_icon(self.btn_screen_analysis, "image", QSize(14, 14), "#8AB4F8")
        toolbar_left.addWidget(self.btn_screen_analysis)

        self.btn_smart = QPushButton("Smart")
        self.btn_smart.setObjectName("toolbar_button_warm")
        self.btn_smart.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_smart.setToolTip("Toggle smart mode")
        self.btn_smart.setAccessibleName("Toggle smart mode")
        self.btn_smart.clicked.connect(self._noop)
        self._set_text_button_icon(self.btn_smart, "zap", QSize(14, 14), "#E7E8EC")
        toolbar_left.addWidget(self.btn_smart)

        self.btn_context_vault = QPushButton("General")
        self.btn_context_vault.setObjectName("toolbar_button_dropdown")
        self.btn_context_vault.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_context_vault.setToolTip("General actions")
        self.btn_context_vault.setAccessibleName("Open general actions")
        self.btn_context_vault.clicked.connect(self._noop)
        self.btn_context_vault.setLayoutDirection(Qt.RightToLeft)
        self._set_text_button_icon(self.btn_context_vault, "chevron_down", QSize(13, 13), "#A3A7B2")
        toolbar_left.addWidget(self.btn_context_vault)
        toolbar_left.addStretch()

        toolbar_row.addLayout(toolbar_left, 1)

        self.btn_send = QPushButton()
        self.btn_send.setObjectName("send_button")
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.setToolTip("Send prompt")
        self.btn_send.setAccessibleName("Send prompt")
        self.btn_send.clicked.connect(self._noop)
        self.btn_send.setIcon(render_svg_icon("send", "#FFFFFF", QSize(15, 15)))
        self.btn_send.setIconSize(QSize(15, 15))
        toolbar_row.addWidget(self.btn_send)
        composer_layout.addLayout(toolbar_row)

        self.context_container = QFrame()
        self.context_container.setObjectName("context_container")
        self.context_container.setVisible(False)
        self.context_container.setMinimumHeight(220)
        self.main_layout.addWidget(self.context_container, 0, Qt.AlignHCenter)

        context_layout = QVBoxLayout(self.context_container)
        context_layout.setContentsMargins(14, 14, 14, 14)
        context_layout.setSpacing(10)

        context_header = QHBoxLayout()
        context_title = QLabel("Session Notes")
        context_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F8F8FF;")
        context_header.addWidget(context_title)

        self.combo_context_notes = QComboBox()
        self.combo_context_notes.setMinimumHeight(38)
        self.combo_context_notes.currentIndexChanged.connect(self.on_note_selected)
        context_header.addWidget(self.combo_context_notes, 1)

        self.btn_add_context_note = QPushButton("Add")
        self.btn_add_context_note.setObjectName("notes_action_button")
        self.btn_add_context_note.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_add_context_note.setToolTip("Create a new session note")
        self.btn_add_context_note.setAccessibleName("Create a new session note")
        self.btn_add_context_note.clicked.connect(self.add_note)
        context_header.addWidget(self.btn_add_context_note)

        self.btn_rename_context_note = QPushButton("Rename")
        self.btn_rename_context_note.setObjectName("notes_action_button")
        self.btn_rename_context_note.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_rename_context_note.setToolTip("Rename the selected session note")
        self.btn_rename_context_note.setAccessibleName("Rename the selected session note")
        self.btn_rename_context_note.clicked.connect(self.rename_note)
        context_header.addWidget(self.btn_rename_context_note)

        self.btn_delete_context_note = QPushButton("Delete")
        self.btn_delete_context_note.setObjectName("notes_action_button")
        self.btn_delete_context_note.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_delete_context_note.setToolTip("Delete the selected session note")
        self.btn_delete_context_note.setAccessibleName("Delete the selected session note")
        self.btn_delete_context_note.clicked.connect(self.delete_note)
        context_header.addWidget(self.btn_delete_context_note)

        self.btn_close_context = QPushButton("Hide")
        self.btn_close_context.setObjectName("notes_action_button")
        self.btn_close_context.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close_context.setToolTip("Hide session notes")
        self.btn_close_context.setAccessibleName("Hide session notes")
        self.btn_close_context.clicked.connect(self._noop)
        context_header.addWidget(self.btn_close_context)
        context_layout.addLayout(context_header)

        self.txt_context = QTextEdit()
        self.txt_context.setObjectName("notes_editor")
        self.txt_context.setPlaceholderText("Capture proof points, risks, and follow-ups here.")
        context_layout.addWidget(self.txt_context, 1)

        self.btn_load_context = None
        self.btn_clear = None
        self.transcript_kicker = None
        self.sheet_kicker = QLabel("")
        self.sheet_kicker.hide()

        self.btn_mic = self.btn_pause
        self.is_expanded = True
        self._set_icon_button_state(self.btn_eye_mode, True)
        self._set_icon_button_state(self.btn_privacy_mode, False)
        self._set_icon_button_state(self.btn_pause, False)
        self._set_icon_button_state(self.btn_stop_transport, False)
        self._set_icon_button_state(self.btn_collapse, False)
        self._set_icon_button_state(self.btn_grip, False)
        self._set_icon_button_state(self.btn_context, False)
        self._set_tab_active(self.btn_tab_ask, True)
        self._set_tab_active(self.btn_tab_transcript, False)
        self._set_button_active(self.btn_smart, False)
        self._apply_ui_typography()
        self._switch_surface("ask")

    def _apply_wordmark_font(self) -> None:
        if self.brand_label is None:
            return
        brand_family = QApplication.instance().property("opencluely_wordmark_family") or "Inter"
        wordmark_font = QFont(str(brand_family), 15)
        wordmark_font.setWeight(QFont.DemiBold)
        wordmark_font.setLetterSpacing(QFont.AbsoluteSpacing, -0.7)
        self.brand_label.setFont(wordmark_font)

    @staticmethod
    def _apply_panel_shadow(widget: QWidget, *, blur: int, y_offset: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, 76))
        shadow.setOffset(0, y_offset)
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def _make_ui_font(point_size: int, *, weight: int, tracking: float) -> QFont:
        family = QApplication.instance().property("opencluely_ui_family") or "Inter"
        font = QFont(str(family), point_size)
        font.setWeight(weight)
        font.setLetterSpacing(QFont.AbsoluteSpacing, tracking)
        return font

    def _apply_ui_typography(self) -> None:
        label_font = self._make_ui_font(10, weight=QFont.DemiBold, tracking=-0.7)
        micro_font = self._make_ui_font(8, weight=QFont.DemiBold, tracking=-0.45)
        input_font = self._make_ui_font(10, weight=QFont.Medium, tracking=-0.35)

        for button in (
            self.btn_tab_ask,
            self.btn_tab_transcript,
            self.btn_assist,
            self.btn_suggest_next,
            self.btn_suggest_followup,
            self.btn_suggest_recap,
            self.btn_screen_analysis,
            self.btn_smart,
            self.btn_context_vault,
        ):
            button.setFont(label_font)

        self.chat_input.setFont(input_font)
        self.record_indicator.setFont(micro_font)
        self.timer_label.setFont(micro_font)

    @staticmethod
    def _noop() -> None:
        return None

    @staticmethod
    def _make_segment(object_name: str = "top_segment") -> QFrame:
        segment = QFrame()
        segment.setObjectName(object_name)
        return segment

    @staticmethod
    def _make_divider() -> QFrame:
        divider = QFrame()
        divider.setObjectName("line_divider")
        return divider

    def _make_icon_button(
        self,
        object_name: str,
        icon_key: str,
        accessible_name: str,
        *,
        tooltip: str,
        button_size: QSize | None = None,
        icon_size: QSize | None = None,
        active_color: str = "#FFFFFF",
        inactive_color: str = "#9CA3AF",
    ) -> QPushButton:
        button = QPushButton()
        button.setObjectName(object_name)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setToolTip(tooltip)
        button.setAccessibleName(accessible_name)
        target_size = button_size or QSize(26, 26)
        target_icon_size = icon_size or QSize(16, 16)
        button.setFixedSize(target_size)
        button.setIconSize(target_icon_size)
        button._icon_key = icon_key
        button._active_color = active_color
        button._inactive_color = inactive_color
        self._set_icon_button_state(button, False)
        return button

    @staticmethod
    def _set_text_button_icon(button: QPushButton, icon_key: str, size: QSize, color: str) -> None:
        button.setIcon(render_svg_icon(icon_key, color, size))
        button.setIconSize(size)

    def _make_quick_action_button(self, label: str, callback, icon_key: str | None = None) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("quick_action_button")
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setToolTip(label)
        button.setAccessibleName(label)
        if icon_key is not None:
            self._set_text_button_icon(button, icon_key, QSize(13, 13), "#D8D8DC")
        button.clicked.connect(callback)
        return button

    @staticmethod
    def _make_shortcut_chip(label: str) -> QLabel:
        chip = QLabel(label)
        chip.setObjectName("shortcut_chip")
        chip.setAlignment(Qt.AlignCenter)
        return chip

    @staticmethod
    def _make_dot_label() -> QLabel:
        dot = QLabel("●")
        dot.setObjectName("quick_action_dot")
        return dot

    @staticmethod
    def _set_tab_active(button: QPushButton, is_active: bool) -> None:
        button.setProperty("active", "true" if is_active else "false")
        button.style().unpolish(button)
        button.style().polish(button)

    def _set_icon_button_state(self, button: QPushButton, is_active: bool) -> None:
        button.setProperty("active", "true" if is_active else "false")
        color = button._active_color if is_active else button._inactive_color
        button.setIcon(render_svg_icon(button._icon_key, color, button.iconSize()))
        button.style().unpolish(button)
        button.style().polish(button)

    def set_vision_mode(self, mode: str) -> None:
        self.vision_mode = mode
        self._set_icon_button_state(self.btn_eye_mode, mode == "visible")
        self._set_icon_button_state(self.btn_privacy_mode, mode == "anonymous")
        self._update_general_button_text()

    def toggle_smart_mode(self) -> None:
        self.smart_mode = not getattr(self, "smart_mode", False)
        self._sync_smart_button()

    def _sync_smart_button(self) -> None:
        self._set_button_active(self.btn_smart, getattr(self, "smart_mode", False))

    def _sync_recording_transport(self) -> None:
        self._set_icon_button_state(self.btn_pause, self.is_recording)
        self._set_icon_button_state(self.btn_stop_transport, False)
        self._set_icon_button_state(self.btn_collapse, False)
        self.btn_grip.setCursor(QCursor(Qt.OpenHandCursor))

    def _update_general_button_text(self) -> None:
        privacy_label = "Private" if getattr(self, "vision_mode", "visible") == "anonymous" else "General"
        self.btn_context_vault.setText(privacy_label)
        self._set_text_button_icon(self.btn_context_vault, "chevron_down", QSize(13, 13), "#A3A7B2")

    def _switch_surface(self, surface: str) -> None:
        self.active_surface = surface
        if self.content_stack is not None:
            self.content_stack.setCurrentIndex(0 if surface == "ask" else 1)
        self._set_tab_active(self.btn_tab_ask, surface == "ask")
        self._set_tab_active(self.btn_tab_transcript, surface == "transcript")
        self.quick_actions_row.setVisible(surface == "ask")

    def _request_assist_prompt(self, prompt: str) -> None:
        self._switch_surface("ask")
        self.chat_input.setText(prompt)
        self.send_chat_message()

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
        profile_name = (
            self.session_context.get("brief_name")
            or self.session_context.get("profile_name")
            or "Blank Brief"
        )
        self.current_profile_name = self._trim_text(profile_name, 48)
        self.setWindowTitle(f"Opencluely - {self.current_profile_name}")
        self.top_bar.setToolTip(f"Opencluely controls for {self.current_profile_name}")
        self.content_container.setToolTip(f"Active brief: {self.current_profile_name}")
        self.btn_context_vault.setToolTip(f"General actions for {self.current_profile_name}")
        self.chat_input.setAccessibleName(f"Ask Opencluely about {self.current_profile_name}")
        self._update_general_button_text()

    def _install_drag_handles(self) -> None:
        for label in (self.brand_label, self.record_indicator, self.timer_label):
            if label is not None:
                label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.top_bar.installEventFilter(self)
        self.btn_grip.installEventFilter(self)

    def _begin_drag(self, global_pos: QPoint) -> None:
        self.is_dragging = True
        self.drag_position = global_pos - self.frameGeometry().topLeft()
        self._sync_recording_transport()

    def _end_drag(self) -> None:
        self.is_dragging = False
        self.setCursor(QCursor(Qt.ArrowCursor))
        self._sync_recording_transport()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if self.top_bar.geometry().contains(event.pos()):
            target = self.childAt(event.pos())
            interactive_types = (QPushButton, QLineEdit, QTextEdit, QComboBox)
            if target is None or not isinstance(target, interactive_types):
                self._begin_drag(event.globalPos())
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._end_drag()
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):
        if watched in (self.top_bar, self.btn_grip):
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._begin_drag(event.globalPos())
                event.accept()
                return True

            if event.type() == QEvent.MouseMove and self.is_dragging:
                self.move(event.globalPos() - self.drag_position)
                event.accept()
                return True

            if event.type() == QEvent.MouseButtonRelease and self.is_dragging:
                self._end_drag()
                event.accept()
                return True

        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.handle_escape()
            event.accept()
            return

        super().keyPressEvent(event)

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
        show_ask = menu.addAction("Show Chat")
        show_ask.setCheckable(True)
        show_ask.setChecked(self.active_surface == "ask")
        show_ask.triggered.connect(lambda: [self.ensure_content_visible(), self._switch_surface("ask")])

        show_transcript = menu.addAction("Show Transcript")
        show_transcript.setCheckable(True)
        show_transcript.setChecked(self.active_surface == "transcript")
        show_transcript.triggered.connect(
            lambda: [self.ensure_content_visible(), self._switch_surface("transcript")]
        )

        menu.addSeparator()

        smart_action = menu.addAction("Smart Mode")
        smart_action.setCheckable(True)
        smart_action.setChecked(self.smart_mode)
        smart_action.triggered.connect(self.toggle_smart_mode)

        visible_action = menu.addAction("Visible Mode")
        visible_action.setCheckable(True)
        visible_action.setChecked(self.vision_mode == "visible")
        visible_action.triggered.connect(lambda: self.set_vision_mode("visible"))

        privacy_action = menu.addAction("Anonymous Mode")
        privacy_action.setCheckable(True)
        privacy_action.setChecked(self.vision_mode == "anonymous")
        privacy_action.triggered.connect(lambda: self.set_vision_mode("anonymous"))

        menu.addSeparator()

        notes_action = menu.addAction("Session Notes")
        notes_action.setCheckable(True)
        notes_action.setChecked(self.context_container.isVisible())
        notes_action.triggered.connect(self.toggle_notes)

        prep_action = menu.addAction("Prep Deck")
        prep_action.setCheckable(True)
        prep_action.setChecked(
            self.context_vault_panel is not None and self.context_vault_panel.isVisible()
        )
        prep_action.triggered.connect(self.toggle_context_vault_panel)

        menu.addAction("Load Context File", self.load_context)
        menu.addAction("Clear Transcript", self.clear_all)
        menu.addAction("Hide Sheet", lambda: self.set_content_visibility(False))
        menu.addSeparator()
        menu.addAction("Hide Live Bar", self.toggle_visibility)
        menu.addAction("Quit", self.close)

        sender = self.sender()
        if isinstance(sender, QPushButton):
            anchor = sender.mapToGlobal(sender.rect().bottomLeft())
        else:
            anchor = QCursor.pos()
        menu.exec_(anchor)

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
        self.record_indicator.setVisible(True)
        self.timer_label.setVisible(True)
        self.txt_transcription.setPlaceholderText("Listening...")
        self._sync_recording_transport()
        self.start_timer()

        if not hasattr(self, "pulse_timer"):
            self.pulse_timer = QTimer(self)
            self.pulse_timer.timeout.connect(self._toggle_pulse)
        self.pulse_timer.start(800)

    def stop_recording(self) -> None:
        if self.audio is not None:
            try:
                self.audio.stop_recording()
                self.audio.wait()
            except Exception:
                logger.debug("Audio thread stop failed", exc_info=True)
        self.on_recording_stopped()

    def handle_transport_stop(self) -> None:
        if self.is_recording or self.audio is not None:
            self.stop_recording()
            return

        self.txt_transcription.setPlaceholderText("Live transcript will appear here.")

    def on_recording_stopped(self) -> None:
        self.is_recording = False
        self.audio = None
        self.record_indicator.setVisible(False)
        self.timer_label.setVisible(False)
        self.txt_transcription.setPlaceholderText("Live transcript will appear here.")
        self._sync_recording_transport()

        if self.timer_rec is not None:
            self.timer_rec.stop()
            
        if hasattr(self, "pulse_timer"):
            self.pulse_timer.stop()
            self.record_indicator.setProperty("pulse", "false")
            self.record_indicator.style().unpolish(self.record_indicator)
            self.record_indicator.style().polish(self.record_indicator)

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

    def _toggle_pulse(self) -> None:
        is_pulse_active = self.record_indicator.property("pulse") == "true"
        self.record_indicator.setProperty("pulse", "false" if is_pulse_active else "true")
        self.record_indicator.style().unpolish(self.record_indicator)
        self.record_indicator.style().polish(self.record_indicator)

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
        self._switch_surface("ask")
        self.assist_service.generate_answer(question, reference_context, self.session_context)

    def on_assist_started(self) -> None:
        self.btn_assist.setEnabled(False)
        self.btn_assist.setText("Working...")
        self.btn_send.setEnabled(False)
        self._set_suggestion_buttons_enabled(False)
        self.chat_input.setPlaceholderText("Assist is generating a grounded response...")

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
        self._set_suggestion_buttons_enabled(True)
        self.chat_input.setPlaceholderText("Ask about your conversation, next move, or screen.")

    def _set_suggestion_buttons_enabled(self, enabled: bool) -> None:
        for button in self.suggestion_buttons:
            if button is self.btn_assist:
                continue
            button.setEnabled(enabled)

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
        self.btn_screen_analysis.setText("Scanning...")
        self.ensure_content_visible()
        self._switch_surface("ask")
        self.screen_analysis.capture_and_analyze()

    def on_screen_analysis_started(self) -> None:
        self.txt_transcription.setPlaceholderText("Running screen capture...")

    def on_screen_result(self, text: str) -> None:
        self.btn_screen_analysis.setEnabled(True)
        self.btn_screen_analysis.setText("Use Screen")
        self.txt_transcription.setPlaceholderText("Live transcript will appear here.")
        self.add_response("Screen Analysis", text)

    def on_screen_error(self, message: str) -> None:
        self.btn_screen_analysis.setEnabled(True)
        self.btn_screen_analysis.setText("Use Screen")
        self.txt_transcription.setPlaceholderText("Live transcript will appear here.")
        self.add_response("Screen Analysis", message)

    def clear_all(self) -> None:
        self.txt_transcription.clear()
        self.last_question = ""
        self.txt_transcription.setPlaceholderText("Transcript cleared. Live transcript will appear here.")

        for index in reversed(range(self.response_layout.count())):
            widget = self.response_layout.itemAt(index).widget()
            if isinstance(widget, ResponseCard):
                self.response_layout.takeAt(index)
                widget.deleteLater()

        self._refresh_response_empty_state()

        if self.context is not None and self.context.has_context():
            self.context.clear_context()

    def add_response(self, question: str, answer: str) -> None:
        label = self._trim_text(question or "Assist", 140)
        card = ResponseCard(label, answer or "")
        card.copy_requested.connect(self.copy_to_clipboard)
        card.delete_requested.connect(self.remove_card)
        self.empty_state.hide()

        self.ensure_content_visible()
        self._switch_surface("ask")
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
        QTimer.singleShot(0, self._refresh_response_empty_state)

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
        self._switch_surface("ask")
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
            self.resize(self.width(), max(self.height(), 520))
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
        self._set_button_active(self.btn_context_vault, True)

    def on_context_vault_closed(self) -> None:
        self._set_button_active(self.btn_context_vault, False)

    def toggle_content_area(self) -> None:
        self.set_content_visibility(not self.is_expanded)

    def set_content_visibility(self, visible: bool) -> None:
        self.is_expanded = visible
        self.content_container.setVisible(visible)
        self.btn_collapse.setAccessibleName("Collapse live sheet" if visible else "Expand live sheet")
        self._sync_recording_transport()

        if visible:
            if self.height() < 500:
                self.resize(self.width(), 500)
            return

        if not self.context_container.isVisible():
            self.resize(self.width(), self.min_height)
        else:
            self.resize(self.width(), 318)

    def ensure_content_visible(self, min_height: int = 460) -> None:
        if not self.is_expanded:
            self.set_content_visibility(True)
        if self.height() < min_height:
            self.resize(self.width(), min_height)

    def handle_escape(self) -> None:
        if self.context_vault_panel is not None and self.context_vault_panel.isVisible():
            self.context_vault_panel.hide()
            self.on_context_vault_closed()
            return

        if self.context_container.isVisible():
            self.toggle_notes()
            return

        if self.is_expanded:
            self.set_content_visibility(False)

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

        if self.current_profile_name:
            parts.append(f"ACTIVE PROFILE\n{self.current_profile_name}")

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

        if self.smart_mode:
            parts.append(
                "WORKING MODE\n"
                "Smart mode is enabled. Be more proactive, concise, and prescriptive. "
                "Prefer specific next steps, cleaner wording, and grounded recommendations."
            )

        if self.vision_mode == "anonymous":
            parts.append(
                "PRIVACY MODE\n"
                "The user enabled anonymous mode. Avoid identifying people or exposing sensitive details "
                "unless the user explicitly asks for that level of specificity."
            )

        return "\n\n".join(parts)

    @staticmethod
    def _trim_text(text: str, limit: int) -> str:
        clean_text = (text or "").strip()
        if len(clean_text) <= limit:
            return clean_text
        return f"{clean_text[:limit].rstrip()}\n\n[truncated]"

    def _set_context_button_active(self, is_active: bool) -> None:
        self._set_button_active(self.btn_context, is_active)

    def _refresh_response_empty_state(self) -> None:
        has_cards = any(
            isinstance(self.response_layout.itemAt(index).widget(), ResponseCard)
            for index in range(self.response_layout.count())
        )
        self.empty_state.setVisible(not has_cards)

    @staticmethod
    def _set_button_active(button: QPushButton, is_active: bool) -> None:
        button.setProperty("active", "true" if is_active else "false")
        button.style().unpolish(button)
        button.style().polish(button)


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
