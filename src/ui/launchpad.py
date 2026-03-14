"""Launchpad UI for Opencluely."""

from __future__ import annotations

import logging

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from profiles.profile_manager import CopilotProfile, get_profile_manager


logger = logging.getLogger(__name__)


LAUNCHPAD_STYLESHEET = """
QWidget {
    background-color: #08111F;
    color: #F8F8FF;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QLabel#header_title {
    font-size: 24px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 5px;
}

QLabel#header_subtitle {
    font-size: 14px;
    color: #888888;
    margin-bottom: 20px;
}

QFrame.section_card {
    background-color: #0D1527;
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 16px;
}

QLabel.section_title {
    font-size: 13px;
    font-weight: 600;
    color: #AAAAAA;
    margin-bottom: 8px;
}

QLineEdit, QTextEdit {
    background-color: #101B31;
    border: 1px solid rgba(130, 166, 249, 0.14);
    border-radius: 12px;
    padding: 12px;
    font-size: 13px;
    color: #F8F8FF;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid rgba(79, 134, 247, 0.4);
    background-color: #162544;
}

QComboBox {
    background-color: #101B31;
    border: 1px solid rgba(130, 166, 249, 0.14);
    border-radius: 12px;
    padding: 10px 15px;
    font-size: 14px;
    color: #F8F8FF;
}

QComboBox:hover {
    border: 1px solid rgba(79, 134, 247, 0.28);
    background-color: #162544;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #101B31;
    border: 1px solid rgba(130, 166, 249, 0.16);
    selection-background-color: #4F86F7;
    selection-color: #F8F8FF;
    outline: none;
    padding: 5px;
}

QPushButton {
    background-color: #101B31;
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 10px;
    color: #E9F0FF;
    font-weight: 500;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #162544;
    border-color: rgba(79, 134, 247, 0.28);
    color: #F8F8FF;
}

QPushButton#btn_primary {
    background-color: #4F86F7;
    border: none;
    border-radius: 14px;
    color: #F8F8FF;
    font-size: 16px;
    font-weight: bold;
    padding: 15px;
    margin-top: 10px;
}

QPushButton#btn_primary:hover {
    background-color: #6A98F8;
}

QPushButton#btn_ghost {
    background-color: transparent;
    border: none;
    color: #4F86F7;
    font-size: 13px;
}

QPushButton#btn_ghost:hover {
    text-decoration: underline;
}

QScrollBar:vertical {
    border: none;
    background: #0D1527;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: rgba(130, 166, 249, 0.28);
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


class ProfileEditorDialog(QDialog):
    """Create, duplicate, or edit a copilot profile."""

    profile_saved = pyqtSignal(object)

    def __init__(self, profile: CopilotProfile = None, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.is_edit_mode = profile is not None and not profile.is_builtin

        self.setWindowTitle("Profile Editor")
        self.setFixedSize(550, 650)
        self.setStyleSheet(LAUNCHPAD_STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.setup_ui()
        if profile:
            self.load_profile(profile)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header = QHBoxLayout()
        if self.is_edit_mode:
            title_text = "Edit Profile"
        elif self.profile:
            title_text = "Duplicate Profile"
        else:
            title_text = "New Profile"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()

        self.btn_save = QPushButton("Save Profile")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setStyleSheet("font-size: 14px; padding: 0;")
        self.btn_save.clicked.connect(self.save_profile)
        header.addWidget(self.btn_save)
        main_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        form_layout = QVBoxLayout(content)
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Profile Name", objectName="section_title"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g., Weekly Sync, Problem Solving, Customer Demo")
        form_layout.addWidget(self.input_name)

        form_layout.addWidget(QLabel("Description", objectName="section_title"))
        self.input_description = QLineEdit()
        self.input_description.setPlaceholderText("Brief description of when to use this profile")
        form_layout.addWidget(self.input_description)

        row_stats = QHBoxLayout()

        icon_container = QVBoxLayout()
        icon_container.addWidget(QLabel("Icon", objectName="section_title"))
        self.combo_icon = QComboBox()
        self.combo_icon.addItems(["💼", "🧩", "📈", "📄", "🎯", "💡", "🔧", "📝", "✨", "🤖", "📚", "🏥", "⚖️"])
        self.combo_icon.setMinimumWidth(100)
        icon_container.addWidget(self.combo_icon)
        row_stats.addLayout(icon_container)

        row_stats.addStretch()

        version_container = QVBoxLayout()
        version_container.addWidget(QLabel("Version", objectName="section_title"))
        self.spin_version = QSpinBox()
        self.spin_version.setRange(1, 100)
        self.spin_version.setFixedWidth(80)
        self.spin_version.setStyleSheet(
            "QSpinBox { background: #252525; border: 1px solid #333; border-radius: 8px; padding: 10px; color: white; }"
        )
        version_container.addWidget(self.spin_version)
        row_stats.addLayout(version_container)

        form_layout.addLayout(row_stats)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; max-height: 1px;")
        form_layout.addWidget(line)

        form_layout.addWidget(QLabel("System Instructions", objectName="section_title"))
        self.input_instructions = QTextEdit()
        self.input_instructions.setPlaceholderText("Define how this copilot profile should behave.")
        self.input_instructions.setMinimumHeight(150)
        form_layout.addWidget(self.input_instructions)

        form_layout.addWidget(QLabel("Session Brief Placeholder", objectName="section_title"))
        self.input_context = QTextEdit()
        self.input_context.setPlaceholderText("Default context structure to show in Launchpad.")
        self.input_context.setMinimumHeight(100)
        form_layout.addWidget(self.input_context)

        form_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_profile(self, profile: CopilotProfile):
        self.input_name.setText(profile.name)
        self.input_description.setText(profile.description)
        self.spin_version.setValue(profile.version)
        index = self.combo_icon.findText(profile.icon)
        if index >= 0:
            self.combo_icon.setCurrentIndex(index)
        self.input_instructions.setText(profile.system_instructions)
        self.input_context.setText(profile.user_context_example)

    def save_profile(self):
        name = self.input_name.text().strip()
        if not name:
            self.input_name.setStyleSheet("border: 1px solid #FF4444;")
            return

        manager = get_profile_manager()

        if self.is_edit_mode and self.profile:
            manager.update(
                self.profile.id,
                name=name,
                description=self.input_description.text().strip(),
                icon=self.combo_icon.currentText(),
                system_instructions=self.input_instructions.toPlainText(),
                user_context_example=self.input_context.toPlainText(),
            )
            profile = self.profile
        else:
            profile = manager.create(
                name=name,
                description=self.input_description.text().strip(),
                icon=self.combo_icon.currentText(),
                system_instructions=self.input_instructions.toPlainText(),
                user_context_example=self.input_context.toPlainText(),
            )

        self.profile_saved.emit(profile)
        self.accept()


class LaunchpadWindow(QWidget):
    """Pre-session launch surface for Opencluely."""

    session_started = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = get_profile_manager()
        self.selected_profile: CopilotProfile = None

        self.setWindowTitle("Opencluely - Launchpad")
        self.setFixedSize(500, 790)
        self.setObjectName("launchpad")
        self.setStyleSheet(LAUNCHPAD_STYLESHEET)

        screen = QApplication.primaryScreen().geometry()
        x_pos = (screen.width() - self.width()) // 2
        y_pos = (screen.height() - self.height()) // 2
        self.move(x_pos, y_pos)

        self.setup_ui()
        self.refresh_profiles()
        self.load_last_profile()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(35, 40, 35, 40)
        self.content_layout.setSpacing(25)

        header = QVBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        header.setSpacing(5)

        icon = QLabel("◎")
        icon.setStyleSheet("font-size: 54px; margin-bottom: 10px;")
        icon.setAlignment(Qt.AlignCenter)
        header.addWidget(icon)

        title = QLabel("Launchpad")
        title.setObjectName("header_title")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)

        subtitle = QLabel("Configure your copilot before opening Live Bar")
        subtitle.setObjectName("header_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header.addWidget(subtitle)

        self.content_layout.addLayout(header)

        provider_card = QFrame()
        provider_card.setProperty("class", "section_card")
        provider_layout = QVBoxLayout(provider_card)
        provider_layout.setContentsMargins(20, 20, 20, 20)

        provider_row = QHBoxLayout()
        provider_info = QVBoxLayout()
        provider_info.setSpacing(2)
        provider_title = QLabel("AI Provider")
        provider_title.setStyleSheet("color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase;")
        provider_value = QLabel("Groq (Llama 3 70B)")
        provider_value.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        provider_info.addWidget(provider_title)
        provider_info.addWidget(provider_value)
        provider_row.addLayout(provider_info)
        provider_row.addStretch()

        status = QLabel("●  Active")
        status.setStyleSheet(
            "color: #4CAF50; font-weight: 600; background: rgba(76, 175, 80, 0.1); "
            "padding: 5px 10px; border-radius: 15px; font-size: 12px;"
        )
        provider_row.addWidget(status)
        provider_layout.addLayout(provider_row)
        self.content_layout.addWidget(provider_card)

        profile_wrapper = QVBoxLayout()
        profile_wrapper.setSpacing(10)

        profile_header = QHBoxLayout()
        profile_label = QLabel("Copilot Profile")
        profile_label.setProperty("class", "section_title")
        profile_header.addWidget(profile_label)
        profile_header.addStretch()

        btn_new = QPushButton("+ New")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.new_profile)
        btn_new.setStyleSheet("background: #252525; border: 1px solid #333; border-radius: 4px; padding: 4px 10px; font-size: 12px;")

        btn_edit = QPushButton("Edit")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.edit_profile)
        btn_edit.setStyleSheet("background: #252525; border: 1px solid #333; border-radius: 4px; padding: 4px 10px; font-size: 12px;")

        profile_header.addWidget(btn_new)
        profile_header.addWidget(btn_edit)
        profile_wrapper.addLayout(profile_header)

        self.combo_profile = QComboBox()
        self.combo_profile.setMinimumHeight(50)
        self.combo_profile.setIconSize(QSize(24, 24))
        self.combo_profile.setCursor(Qt.PointingHandCursor)
        self.combo_profile.currentIndexChanged.connect(self.on_profile_changed)
        profile_wrapper.addWidget(self.combo_profile)
        self.content_layout.addLayout(profile_wrapper)

        language_wrapper = QVBoxLayout()
        language_wrapper.setSpacing(10)
        language_label = QLabel("Transcription Language")
        language_label.setProperty("class", "section_title")
        language_wrapper.addWidget(language_label)

        self.combo_language = QComboBox()
        self.combo_language.setMinimumHeight(45)
        self.combo_language.addItems(["English (US)", "Portuguese (BR)", "Spanish", "French", "German", "Japanese"])
        language_wrapper.addWidget(self.combo_language)
        self.content_layout.addLayout(language_wrapper)

        context_wrapper = QVBoxLayout()
        context_wrapper.setSpacing(10)
        context_label = QLabel("Session Brief")
        context_label.setProperty("class", "section_title")
        context_wrapper.addWidget(context_label)

        self.input_details = QTextEdit()
        self.input_details.setPlaceholderText("Paste agenda, goals, objections, code context, or notes here...")
        self.input_details.setMinimumHeight(130)
        context_wrapper.addWidget(self.input_details)
        self.content_layout.addLayout(context_wrapper)

        debrief_card = QFrame()
        debrief_card.setProperty("class", "section_card")
        debrief_layout = QVBoxLayout(debrief_card)
        debrief_layout.setContentsMargins(18, 16, 18, 16)
        debrief_title = QLabel("Debrief")
        debrief_title.setProperty("class", "section_title")
        debrief_copy = QLabel("After the session, Debrief is where summaries, follow-ups, and next steps land.")
        debrief_copy.setWordWrap(True)
        debrief_copy.setStyleSheet("color: #D0D0D0; font-size: 13px;")
        debrief_layout.addWidget(debrief_title)
        debrief_layout.addWidget(debrief_copy)
        self.content_layout.addWidget(debrief_card)

        self.content_layout.addStretch()

        footer = QVBoxLayout()
        footer.setSpacing(15)

        self.btn_start = QPushButton("Open Live Bar")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setMinimumHeight(55)
        self.btn_start.clicked.connect(self.start_session)
        footer.addWidget(self.btn_start)

        btn_skip = QPushButton("Start Without Brief")
        btn_skip.setObjectName("btn_ghost")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self.skip_setup)
        footer.addWidget(btn_skip, alignment=Qt.AlignCenter)

        self.content_layout.addLayout(footer)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def refresh_profiles(self):
        self.combo_profile.blockSignals(True)
        self.combo_profile.clear()
        for profile in self.profile_manager.get_all():
            self.combo_profile.addItem(f"{profile.icon}  {profile.name}", profile.id)
        self.combo_profile.blockSignals(False)
        if self.combo_profile.count() > 0:
            self.on_profile_changed(self.combo_profile.currentIndex())

    def load_last_profile(self):
        last = self.profile_manager.get_last_used()
        if last:
            index = self.combo_profile.findData(last.id)
            if index >= 0:
                self.combo_profile.setCurrentIndex(index)

    def on_profile_changed(self, index):
        profile_id = self.combo_profile.currentData()
        if not profile_id:
            return

        self.selected_profile = self.profile_manager.get_by_id(profile_id)
        if hasattr(self, "input_details") and self.selected_profile and not self.input_details.toPlainText().strip():
            self.input_details.setPlaceholderText(
                self.selected_profile.user_context_example or "Add context for the upcoming session..."
            )

    def edit_profile(self):
        if self.selected_profile:
            dialog = ProfileEditorDialog(self.selected_profile, self)
            dialog.profile_saved.connect(lambda _: self.refresh_profiles())
            dialog.exec_()

    def new_profile(self):
        dialog = ProfileEditorDialog(None, self)
        dialog.profile_saved.connect(self.on_profile_created)
        dialog.exec_()

    def on_profile_created(self, profile: CopilotProfile):
        self.refresh_profiles()
        index = self.combo_profile.findData(profile.id)
        if index >= 0:
            self.combo_profile.setCurrentIndex(index)

    def start_session(self):
        if self.selected_profile:
            self.profile_manager.set_last_used(self.selected_profile.id)

        session_context = {
            "system_instructions": self.selected_profile.system_instructions if self.selected_profile else "",
            "user_context": self.input_details.toPlainText().strip(),
            "profile_name": self.selected_profile.name if self.selected_profile else "General Copilot",
            "language": self.combo_language.currentText().lower(),
        }

        logger.info("[Launchpad] Starting session with profile: %s", session_context["profile_name"])
        self.session_started.emit(session_context)
        self.hide()

    def skip_setup(self):
        session_context = {
            "system_instructions": "",
            "user_context": "",
            "profile_name": "General Copilot",
            "language": "en",
        }
        self.session_started.emit(session_context)
        self.hide()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    def on_start(context):
        print("Session started with context:")
        print(context)
        app.quit()

    launchpad = LaunchpadWindow()
    launchpad.session_started.connect(on_start)
    launchpad.show()

    sys.exit(app.exec_())
