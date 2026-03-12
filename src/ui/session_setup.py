import sys
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QFrame, QApplication, QScrollArea,
    QDialog, QLineEdit, QSpinBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor

from templates.template_manager import get_template_manager, Template
try:
    from brand import (
        APP_NAME,
        APP_TAGLINE,
        PRIMARY_BLUE,
        SETUP_SURFACE_NAME,
        SOFT_WHITE,
        TEXT_MUTED,
        WORDMARK_FAMILY,
        WORDMARK_POINT_SIZE,
        WORDMARK_TRACKING_PERCENT,
    )
except ImportError:
    from src.brand import (
        APP_NAME,
        APP_TAGLINE,
        PRIMARY_BLUE,
        SETUP_SURFACE_NAME,
        SOFT_WHITE,
        TEXT_MUTED,
        WORDMARK_FAMILY,
        WORDMARK_POINT_SIZE,
        WORDMARK_TRACKING_PERCENT,
    )

logger = logging.getLogger(__name__)

# ============================================================================
# STYLESHEET
# ============================================================================

SETUP_STYLESHEET = """
QWidget {
    background-color: #08111F;
    color: #F8F8FF;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Headers */
QLabel#header_title {
    font-size: 24px;
    font-weight: 600;
    color: #F8F8FF;
    margin-bottom: 5px;
}

QLabel#header_subtitle {
    font-size: 14px;
    color: #9FB0CC;
    margin-bottom: 20px;
}

/* Section Cards */
QFrame.section_card {
    background-color: rgba(9, 17, 31, 0.96);
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 16px;
}

QLabel.section_title {
    font-size: 13px;
    font-weight: 600;
    color: #9FB0CC;
    margin-bottom: 8px;
}

/* Inputs */
QLineEdit, QTextEdit {
    background-color: #0D1527;
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 12px;
    padding: 12px;
    font-size: 13px;
    color: #F8F8FF;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #4F86F7;
    background-color: #101B31;
}

QLineEdit:hover, QTextEdit:hover {
    border: 1px solid rgba(79, 134, 247, 0.30);
}

/* ComboBox */
QComboBox {
    background-color: #0D1527;
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 12px;
    padding: 10px 15px;
    font-size: 14px;
    color: #F8F8FF;
}

QComboBox:hover {
    border: 1px solid rgba(79, 134, 247, 0.30);
    background-color: #101B31;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
    width: 0; 
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #9FB0CC;
    margin-right: 15px;
}

QComboBox QAbstractItemView {
    background-color: #0D1527;
    border: 1px solid rgba(130, 166, 249, 0.16);
    selection-background-color: #4F86F7;
    selection-color: #F8F8FF;
    outline: none;
    padding: 5px;
}

/* Buttons */
QPushButton {
    background-color: #101B31;
    border: 1px solid rgba(130, 166, 249, 0.16);
    border-radius: 10px;
    color: #D8E2F3;
    font-weight: 600;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #162544;
    border-color: rgba(79, 134, 247, 0.34);
    color: #F8F8FF;
}

QPushButton:pressed {
    background-color: #0D1527;
}

QPushButton#btn_primary {
    background-color: #4F86F7;
    border: none;
    border-radius: 12px;
    color: #F8F8FF;
    font-size: 16px;
    font-weight: 700;
    padding: 15px;
    margin-top: 10px;
}

QPushButton#btn_primary:hover {
    background-color: #6696F8;
}

QPushButton#btn_primary:pressed {
    background-color: #3E74DF;
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

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #0D1527;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: rgba(130, 166, 249, 0.26);
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


# ============================================================================
# TEMPLATE EDITOR DIALOG
# ============================================================================

class TemplateEditorDialog(QDialog):
    """Modal for creating and editing reusable briefs."""
    
    template_saved = pyqtSignal(object)
    
    def __init__(self, template: Template = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.is_edit_mode = template is not None and not template.is_builtin
        
        self.setWindowTitle("Brief Editor")
        self.setFixedSize(550, 650)
        self.setStyleSheet(SETUP_STYLESHEET)
        # Usar janela modal padrão mas com style dark
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        if template:
            self.load_template(template)
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Edit Brief" if self.is_edit_mode else "New Brief")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.btn_save = QPushButton("Save Brief")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setStyleSheet("font-size: 14px; padding: 0;")
        self.btn_save.clicked.connect(self.save_template)
        header.addWidget(self.btn_save)
        
        main_layout.addLayout(header)
        
        # Content Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        form_layout = QVBoxLayout(content)
        form_layout.setSpacing(15)
        
        # Name
        form_layout.addWidget(QLabel("Brief Name", objectName="section_title"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g., Hiring Loop, Sales Call, Design Review...")
        form_layout.addWidget(self.input_name)
        
        # Description
        form_layout.addWidget(QLabel("Description", objectName="section_title"))
        self.input_description = QLineEdit()
        self.input_description.setPlaceholderText("Short description of what this brief is optimized for")
        form_layout.addWidget(self.input_description)
        
        # Icon & Version
        row_stats = QHBoxLayout()
        
        # Icon
        icon_container = QVBoxLayout()
        icon_container.addWidget(QLabel("Icon", objectName="section_title"))
        self.combo_icon = QComboBox()
        self.combo_icon.addItems(["💼", "🧩", "📈", "📄", "🎯", "💡", "🔧", "📝", "✨", "🤖", "🎓", "🏥", "⚖️"])
        self.combo_icon.setMinimumWidth(100)
        icon_container.addWidget(self.combo_icon)
        row_stats.addLayout(icon_container)
        
        row_stats.addStretch()
        
        # Version
        ver_container = QVBoxLayout()
        ver_container.addWidget(QLabel("Version", objectName="section_title"))
        self.spin_version = QSpinBox()
        self.spin_version.setRange(1, 100)
        self.spin_version.setFixedWidth(80)
        self.spin_version.setStyleSheet("""
            QSpinBox { background: #252525; border: 1px solid #333; border-radius: 8px; padding: 10px; color: white; }
        """)
        ver_container.addWidget(self.spin_version)
        row_stats.addLayout(ver_container)
        
        form_layout.addLayout(row_stats)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; max-height: 1px;")
        form_layout.addWidget(line)
        
        # System Instructions
        form_layout.addWidget(QLabel("System Instructions (The 'Prompt')", objectName="section_title"))
        self.input_instructions = QTextEdit()
        self.input_instructions.setPlaceholderText("You are an expert assistant... (Define how the AI should behave)")
        self.input_instructions.setMinimumHeight(150)
        form_layout.addWidget(self.input_instructions)
        
        # User Context Example
        form_layout.addWidget(QLabel("Suggested Context", objectName="section_title"))
        self.input_context = QTextEdit()
        self.input_context.setPlaceholderText("Suggested structure to guide the operator before a session...")
        self.input_context.setMinimumHeight(100)
        form_layout.addWidget(self.input_context)
        
        form_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_template(self, template: Template):
        self.input_name.setText(template.name)
        self.input_description.setText(template.description)
        self.spin_version.setValue(template.version)
        idx = self.combo_icon.findText(template.icon)
        if idx >= 0: self.combo_icon.setCurrentIndex(idx)
        self.input_instructions.setText(template.system_instructions)
        self.input_context.setText(template.user_context_example)
    
    def save_template(self):
        name = self.input_name.text().strip()
        if not name:
            self.input_name.setStyleSheet("border: 1px solid #FF4444;")
            return
            
        manager = get_template_manager()
        
        if self.is_edit_mode and self.template:
            manager.update(
                self.template.id,
                name=name,
                description=self.input_description.text().strip(),
                icon=self.combo_icon.currentText(),
                system_instructions=self.input_instructions.toPlainText(),
                user_context_example=self.input_context.toPlainText()
            )
            template = self.template
        else:
            template = manager.create(
                name=name,
                description=self.input_description.text().strip(),
                icon=self.combo_icon.currentText(),
                system_instructions=self.input_instructions.toPlainText(),
                user_context_example=self.input_context.toPlainText()
            )
        
        self.template_saved.emit(template)
        self.accept()


# ============================================================================
# SESSION SETUP WINDOW
# ============================================================================

class SessionSetupWindow(QWidget):
    """
    Janela de configuração de sessão.
    Estilo limpo e moderno.
    """
    
    session_started = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.template_manager = get_template_manager()
        self.selected_template: Template = None
        
        self.setWindowTitle(f"{APP_NAME} - {SETUP_SURFACE_NAME}")
        self.setFixedSize(500, 750) 
        self.setObjectName("session_setup")
        self.setStyleSheet(SETUP_STYLESHEET)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.setup_ui()
        self.load_last_template()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area for the whole window behavior
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content.setObjectName("session_setup")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(35, 40, 35, 40)
        self.content_layout.setSpacing(25)
        
        # ================== HEADER ==================
        header = QVBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        header.setSpacing(5)
        
        wordmark = QLabel(APP_NAME)
        wordmark_font = QFont(WORDMARK_FAMILY, WORDMARK_POINT_SIZE + 8)
        wordmark_font.setWeight(QFont.DemiBold)
        wordmark_font.setLetterSpacing(QFont.PercentageSpacing, WORDMARK_TRACKING_PERCENT)
        wordmark.setFont(wordmark_font)
        wordmark.setStyleSheet("color: #F8F8FF; margin-bottom: 10px;")
        wordmark.setAlignment(Qt.AlignCenter)
        header.addWidget(wordmark)
        
        title = QLabel(SETUP_SURFACE_NAME)
        title.setObjectName("header_title")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        
        sub = QLabel(APP_TAGLINE)
        sub.setObjectName("header_subtitle")
        sub.setAlignment(Qt.AlignCenter)
        header.addWidget(sub)
        
        self.content_layout.addLayout(header)
        
        # ================== AI PROVIDER ==================
        card_provider = QFrame()
        card_provider.setProperty("class", "section_card")
        layout_prov = QVBoxLayout(card_provider)
        layout_prov.setContentsMargins(20, 20, 20, 20)
        
        row_prov = QHBoxLayout()
        
        # Icon + Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        lbl_prov_title = QLabel("Live Provider")
        lbl_prov_title.setStyleSheet("color: #9FB0CC; font-size: 12px; font-weight: 600; text-transform: uppercase;")
        lbl_prov_val = QLabel("Groq Whisper Turbo")
        lbl_prov_val.setStyleSheet("color: #F8F8FF; font-size: 15px; font-weight: 700;")
        info_layout.addWidget(lbl_prov_title)
        info_layout.addWidget(lbl_prov_val)
        row_prov.addLayout(info_layout)
        
        row_prov.addStretch()
        
        # Status
        status = QLabel("●  Active")
        status.setStyleSheet("color: #4ADE80; font-weight: 600; background: rgba(74, 222, 128, 0.10); padding: 5px 10px; border-radius: 15px; font-size: 12px;")
        row_prov.addWidget(status)
        
        layout_prov.addLayout(row_prov)
        self.content_layout.addWidget(card_provider)
        
        # ================== TEMPLATE SELECTION ==================
        wrapper_tmpl = QVBoxLayout()
        wrapper_tmpl.setSpacing(10)
        
        # Header Row
        row_tmpl_header = QHBoxLayout()
        lbl_tmpl_sec = QLabel("Brief")
        lbl_tmpl_sec.setProperty("class", "section_title")
        row_tmpl_header.addWidget(lbl_tmpl_sec)
        row_tmpl_header.addStretch()
        
        # Actions
        btn_new = QPushButton("+ New")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.new_template)
        btn_new.setStyleSheet(
            "background: #101B31; border: 1px solid rgba(130, 166, 249, 0.16); "
            "border-radius: 8px; padding: 6px 10px; font-size: 12px; color: #D8E2F3;"
        )
        
        btn_edit = QPushButton("Edit")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.edit_template)
        btn_edit.setStyleSheet(
            "background: #101B31; border: 1px solid rgba(130, 166, 249, 0.16); "
            "border-radius: 8px; padding: 6px 10px; font-size: 12px; color: #D8E2F3;"
        )
        
        row_tmpl_header.addWidget(btn_new)
        row_tmpl_header.addWidget(btn_edit)
        
        wrapper_tmpl.addLayout(row_tmpl_header)
        
        # ComboBox
        self.combo_template = QComboBox()
        self.combo_template.setMinimumHeight(50)
        self.combo_template.setIconSize(QSize(24, 24))
        self.combo_template.setCursor(Qt.PointingHandCursor)
        self.combo_template.currentIndexChanged.connect(self.on_template_changed)
        wrapper_tmpl.addWidget(self.combo_template)
        
        self.content_layout.addLayout(wrapper_tmpl)
        
        # ================== LANGUAGE ==================
        wrapper_lang = QVBoxLayout()
        wrapper_lang.setSpacing(10)
        lbl_lang = QLabel("Transcript Language")
        lbl_lang.setProperty("class", "section_title")
        wrapper_lang.addWidget(lbl_lang)
        
        self.combo_language = QComboBox()
        self.combo_language.setMinimumHeight(45)
        self.combo_language.addItems(["English (US)", "Portuguese (BR)", "Spanish", "French", "German", "Japanese"])
        wrapper_lang.addWidget(self.combo_language)
        
        self.content_layout.addLayout(wrapper_lang)
        
        # ================== CONTEXT INPUT ==================
        wrapper_ctx = QVBoxLayout()
        wrapper_ctx.setSpacing(10)
        
        lbl_ctx = QLabel("Context Brief")
        lbl_ctx.setProperty("class", "section_title")
        wrapper_ctx.addWidget(lbl_ctx)
        
        self.input_details = QTextEdit()
        self.input_details.setPlaceholderText("Paste goals, stakeholders, risks, references, or the agenda for this session...")
        self.input_details.setMinimumHeight(120)
        wrapper_ctx.addWidget(self.input_details)
        
        self.content_layout.addLayout(wrapper_ctx)
        
        self.content_layout.addStretch()
        
        # ================== FOOTER ACTIONS ==================
        footer = QVBoxLayout()
        footer.setSpacing(15)
        
        self.btn_start = QPushButton("Launch Session")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setMinimumHeight(55)
        self.btn_start.clicked.connect(self.start_session)
        footer.addWidget(self.btn_start)
        
        btn_skip = QPushButton("Quick Session")
        btn_skip.setObjectName("btn_ghost")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self.skip_setup)
        footer.addWidget(btn_skip, alignment=Qt.AlignCenter)
        
        self.content_layout.addLayout(footer)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Call refresh templates AFTER UI is built
        self.refresh_templates()

    def refresh_templates(self):
        """Atualiza lista de templates no combo."""
        self.combo_template.blockSignals(True)
        self.combo_template.clear()
        templates = self.template_manager.get_all()
        for t in templates:
            self.combo_template.addItem(f"{t.icon}  {t.name}", t.id)
        self.combo_template.blockSignals(False)
        
        # Trigger change manually if needed, or rely on selection
        # No, selection hasn't changed unless index 0 is selected.
        if self.combo_template.count() > 0:
            self.on_template_changed(self.combo_template.currentIndex())


    def load_last_template(self):
        """Carrega último template usado."""
        last = self.template_manager.get_last_used()
        if last:
            idx = self.combo_template.findData(last.id)
            if idx >= 0:
                self.combo_template.setCurrentIndex(idx)
                # selected_template is updated in on_template_changed connection
    
    def on_template_changed(self, index):
        """Callback quando template muda."""
        template_id = self.combo_template.currentData()
        if template_id:
            self.selected_template = self.template_manager.get_by_id(template_id)
            
            # Preencher user context exemplo se vazio (e widget existe)
            if hasattr(self, 'input_details') and self.selected_template:
                if not self.input_details.toPlainText().strip():
                    self.input_details.setPlaceholderText(
                        self.selected_template.user_context_example or "Add session details..."
                    )
    
    def edit_template(self):
        """Abre editor para template selecionado."""
        if self.selected_template:
            dialog = TemplateEditorDialog(self.selected_template, self)
            dialog.template_saved.connect(lambda t: self.refresh_templates())
            dialog.exec_()
    
    def new_template(self):
        """Abre editor para novo template."""
        dialog = TemplateEditorDialog(None, self)
        dialog.template_saved.connect(lambda t: self.on_template_created(t))
        dialog.exec_()
    
    def on_template_created(self, template: Template):
        """Callback quando template é criado."""
        self.refresh_templates()
        # Selecionar novo template
        idx = self.combo_template.findData(template.id)
        if idx >= 0:
            self.combo_template.setCurrentIndex(idx)
    
    def start_session(self):
        """Inicia sessão com contexto configurado."""
        # Salvar último usado
        if self.selected_template:
            self.template_manager.set_last_used(self.selected_template.id)
        
        # Construir session context
        session_context = {
            "system_instructions": self.selected_template.system_instructions if self.selected_template else "",
            "user_context": self.input_details.toPlainText().strip(),
            "brief_name": self.selected_template.name if self.selected_template else "Blank Brief",
            "template_name": self.selected_template.name if self.selected_template else "Blank Brief",
            "language": self.combo_language.currentText().lower()
        }

        logger.info("[SessionSetup] Starting session with brief: %s", session_context["brief_name"])
        
        self.session_started.emit(session_context)
        self.hide()
    
    def skip_setup(self):
        """Pula setup e inicia com config padrão."""
        session_context = {
            "system_instructions": "",
            "user_context": "",
            "brief_name": "Blank Brief",
            "template_name": "Blank Brief",
            "language": "en"
        }
        self.session_started.emit(session_context)
        self.hide()


SessionSetup = SessionSetupWindow


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    def on_start(ctx):
        print("Session started with context:")
        print(ctx)
        app.quit()
    
    setup = SessionSetupWindow()
    setup.session_started.connect(on_start)
    setup.show()
    
    sys.exit(app.exec_())
