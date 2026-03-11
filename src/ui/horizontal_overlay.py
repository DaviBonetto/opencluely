# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - UI Horizontal (Sprint E2)
Refinamento Visual e Interativo - Capsule Style

Características:
- Janela transparente com widgets flutuantes arredondados
- Top Bar estilo "Cápsula"
- Drag & Drop na Top Bar
- Resize na borda inferior
- Chat Cards estilizados
- Botões "Pill" (arredondados)
"""

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QFrame, QSystemTrayIcon,
    QMenu, QAction, QApplication, QSizePolicy, QFileDialog, QGraphicsDropShadowEffect,
    QLineEdit, QComboBox  # Para input de chat e notas
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt5.QtGui import QFont, QCursor, QIcon, QColor, QMouseEvent
import markdown # Para renderizar MD em HTML

# Adicionar src ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NotesManager
try:
    from notes_manager import NotesManager
except ImportError:
    from src.notes_manager import NotesManager

# Import LALA components
try:
    from lala_manager import LALAManager
    from ui.lala_panel import LALAPanel
except ImportError:
    from src.lala_manager import LALAManager
    from src.ui.lala_panel import LALAPanel

logger = logging.getLogger('horizontal_overlay')

# ============================================================================
# ESTILOS (CSS)
# ============================================================================

STYLESHEET = """
/* Janela Transparente */
QMainWindow, QWidget#central {
    background: transparent;
}

/* Container Principal (Top Bar) */
QFrame#top_bar {
    background-color: #1E1E1E;
    border-radius: 20px;
    border: 1px solid #333333;
}

/* Container de Conteúdo (Transcrição/Chat) */
QFrame#content_container {
    background-color: #121212;
    border-radius: 15px;
    border: 1px solid #2A2A2A;
}

/* Labels */
QLabel {
    color: #FFFFFF;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

QLabel#logo_text {
    font-weight: bold;
    font-size: 14px;
}

QLabel#timer_label {
    font-family: 'Consolas', monospace;
    font-weight: bold;
    color: #FFFFFF;
    background-color: #000000;
    border-radius: 5px;
    padding: 4px 8px;
}

/* Botões Genéricos */
QPushButton {
    background: transparent;
    border: none;
    color: #E0E0E0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    padding: 5px;
}

QPushButton:hover {
    color: #FFFFFF;
}

/* Botões "Pill" (Cápsula) */
QPushButton.pill-btn {
    background-color: #2D2D2D;
    border-radius: 15px;
    padding: 6px 16px;
    font-weight: 500;
}

QPushButton.pill-btn:hover {
    background-color: #404040;
}

QPushButton.pill-btn:pressed {
    background-color: #505050;
}

/* Botão AI Help (Destaque) */
QPushButton#btn_ai {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
}

QPushButton#btn_ai:hover {
    border-color: #555555;
    background-color: #333333;
}

/* Botão Screen */
QPushButton#btn_screen {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
}

/* Ícones de Controle (Direita) */
QPushButton.icon-btn {
    background-color: #252525;
    border-radius: 8px;
    padding: 6px;
    width: 32px;
    height: 32px;
}

QPushButton.icon-btn:hover {
    background-color: #353535;
}

QPushButton#btn_close:hover {
    background-color: #CC2222;
}

/* Transcrição */
QTextEdit#transcription_box {
    background-color: #121212;
    border: none;
    color: #E0E0E0;
    font-size: 13px;
    selection-background-color: #404040;
}

/* ScrollArea */
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #1A1A1A;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #404040;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Cards de Resposta - MELHORADOS */
QFrame.response-card {
    background-color: #1E1E1E;
    border-radius: 12px;
    border: 2px solid #333333;
    margin: 8px 0;
}

/* ScrollBar mais fina */
QScrollBar:vertical {
    background: #1A1A1A;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QLabel.q-label {
    color: #AAAAAA;
    font-size: 12px;
    font-style: italic;
}

QLabel.a-label {
    color: #FFFFFF;
    font-size: 13px;
    line-height: 1.4;
}

/* Barra de Resize */
QWidget#resize_handle {
    background-color: transparent;
}
QWidget#resize_handle:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
"""

# ============================================================================
# IMPORTAR COMPONENTES (Mockável)
# ============================================================================

try:
    from audio_capture import AudioCapture
    AUDIO_AVAILABLE = True
except:
    AUDIO_AVAILABLE = False
    AudioCapture = None

try:
    from transcription_groq import TranscriberGroq
    TRANSCRIBER_AVAILABLE = True
except:
    TRANSCRIBER_AVAILABLE = False
    TranscriberGroq = None

try:
    from ai_helper import AIHelper
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False
    AIHelper = None

try:
    from context_manager import ContextManager
    CONTEXT_AVAILABLE = True
except:
    CONTEXT_AVAILABLE = False
    ContextManager = None

try:
    from screen_analyzer import ScreenAnalyzer
    SCREEN_AVAILABLE = True
except:
    SCREEN_AVAILABLE = False
    ScreenAnalyzer = None

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except:
    KEYBOARD_AVAILABLE = False


# ============================================================================
# UTILS
# ============================================================================

class ResponseCard(QFrame):
    """Card de resposta estilizado - GRANDE como bloco de notas."""
    
    copy_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(object)
    
    def __init__(self, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        
        self.setProperty("class", "response-card")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 18, 18)  # Margens maiores
        layout.setSpacing(12)
        
        # Header (Pergunta + Botões) - MAIOR
        header = QHBoxLayout()
        header.setSpacing(15)
        
        # Pergunta - TEXTO GRANDE
        q_label = QLabel(f"💬 {self.question}")
        q_label.setStyleSheet("""
            color: #ffffff; 
            font-size: 16px; 
            font-weight: 600;
            padding: 8px 0;
        """)
        q_label.setWordWrap(True)
        header.addWidget(q_label, 1) # Stretch
        
        # Botões (Copy/Delete) - MAIORES e mais visíveis
        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setFixedSize(90, 36)
        btn_copy.setToolTip("Copiar Resposta")
        btn_copy.setCursor(QCursor(Qt.PointingHandCursor))
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #2a5a2a;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #3a6a3a; }
        """)
        btn_copy.clicked.connect(lambda: self.copy_clicked.emit(self.answer))
        
        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(36, 36)
        btn_del.setToolTip("Remover Card")
        btn_del.setCursor(QCursor(Qt.PointingHandCursor))
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: #5a2a2a;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #6a3a3a; }
        """)
        btn_del.clicked.connect(lambda: self.delete_clicked.emit(self))
        
        header.addWidget(btn_copy)
        header.addWidget(btn_del)
        layout.addLayout(header)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; height: 1px; margin: 5px 0;")
        layout.addWidget(line)
        
        # Resposta - TEXTO GRANDE como bloco de notas
        a_label = QLabel()
        a_label.setStyleSheet("""
            color: #e0e0e0; 
            font-size: 15px; 
            line-height: 1.6;
            padding: 16px;
            background-color: #1a1a1a;
            border-radius: 10px;
            border-left: 4px solid #4a90d9;
        """)
        a_label.setWordWrap(True)
        a_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        a_label.setOpenExternalLinks(True)
        a_label.setMinimumHeight(120)  # Altura mínima maior
        
        # Converter Markdown para HTML
        html_content = markdown.markdown(self.answer, extensions=['fenced_code', 'codehilite'])
        
        # Estilo CSS inline para código (Dark Mode) - MELHORADO
        style = """
        <style>
        body { 
            background-color: transparent; 
            color: #e0e0e0; 
            font-family: 'Segoe UI', sans-serif;
            font-size: 15px;
            line-height: 1.6;
        }
        code { 
            background-color: #2b2b2b; 
            color: #a9b7c6; 
            font-family: 'Consolas', monospace; 
            padding: 3px 6px; 
            border-radius: 4px; 
            font-size: 14px;
        }
        pre { 
            background-color: #252525; 
            color: #e0e0e0; 
            padding: 15px; 
            border-radius: 8px; 
            overflow-x: auto; 
            margin: 12px 0; 
            border: 1px solid #333;
            font-size: 14px;
        }
        p { margin-bottom: 12px; }
        ul, ol { margin-bottom: 12px; padding-left: 25px; }
        li { margin-bottom: 6px; }
        strong { color: #ffffff; font-weight: 600; }
        h1, h2, h3 { color: #ffffff; margin-top: 16px; margin-bottom: 8px; }
        h1 { font-size: 20px; }
        h2 { font-size: 18px; }
        h3 { font-size: 16px; }
        </style>
        """
        a_label.setText(style + html_content)
        
        layout.addWidget(a_label)


# ============================================================================
# MAIN WINDOW
# ============================================================================

class HorizontalOverlay(QMainWindow):
    """Overlay Horizontal (Sprint E2)."""
    
    def __init__(self, session_context: dict = None):
        super().__init__()
        
        # Session Context (do SessionSetup)
        self.session_context = session_context or {}
        
        # Estado
        self.is_recording = False
        self.is_expanded = False # Conteúdo visível?
        self.is_dragging = False
        self.is_resizing = False
        self.drag_position = QPoint()
        self.resize_start_height = 0
        
        self.last_question = ""
        
        # Backend (inicializado em setup_backend)
        self.audio = None
        self.transcriber = None
        self.ai = None
        self.screen = None
        self.context = None
        self.timer_rec = None
        self.seconds = 0
        
        # Configurar Janela
        self.setup_window()
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)  # Aplicar estilos diretamente
        self.setup_backend()
        self.setup_tray()
        self.setup_hotkey()

    def setup_window(self):
        """Configura flags e geometria da janela."""
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Geometria Inicial
        screen = QApplication.primaryScreen().geometry()
        # Mais compacto: 70% da largura, centralizado
        w = int(screen.width() * 0.70)
        x = int((screen.width() - w) / 2)
        y = 20 # Bem próximo ao topo
        h = 55 # Altura inicial mais compacta
        self.setGeometry(x, y, w, h)
        
        self.min_height = 55
        self.max_height = 700

    def set_session_data(self, session_context: dict):
        """Define o contexto da sessão vindo do SessionSetup."""
        self.session_context = session_context or {}
        logger.info(f"Dados da sessão definidos: {self.session_context.get('template_name')}")

    def setup_ui(self):
        """Monta a interface."""
        self.central = QWidget()
        self.central.setObjectName("central")
        self.setCentralWidget(self.central)
        
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Margem para sombra
        self.main_layout.setSpacing(5)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.central.setGraphicsEffect(shadow)
        
        # 1. TOP BAR (Capsule)
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setFixedHeight(48) # Mais compacto (era 50)
        
        bar_layout = QHBoxLayout(self.top_bar)
        bar_layout.setContentsMargins(10, 4, 10, 4) # Menos margem
        bar_layout.setSpacing(8)
        
        # -- Logo --
        # img_logo = QLabel("🦜") # Placeholder para imagem
        # img_logo.setStyleSheet("font-size: 20px;")
        # bar_layout.addWidget(img_logo)
        
        lbl_logo = QLabel("🦜 ParakeetAI")
        lbl_logo.setObjectName("logo_text")
        bar_layout.addWidget(lbl_logo)
        
        # -- Status Icon (Rec) --
        self.icon_rec = QLabel("🔴")
        self.icon_rec.setVisible(False)
        bar_layout.addWidget(self.icon_rec)
        
        # -- Mic Button --
        self.btn_mic = QPushButton()
        self.btn_mic.setIcon(QIcon("resources/mic.png")) # Fallback text
        self.btn_mic.setText("🎤")
        self.btn_mic.setFixedSize(30, 30)
        self.btn_mic.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_mic.clicked.connect(self.toggle_recording)
        self.btn_mic.setToolTip("Start/Stop Recording")
        bar_layout.addWidget(self.btn_mic)
        
        # Separator V
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #444; width: 1px;")
        bar_layout.addWidget(sep1)
        
        # -- Pills --
        self.btn_ai = QPushButton("AI Help ✨")
        self.btn_ai.setObjectName("btn_ai")
        self.btn_ai.setProperty("class", "pill-btn")
        self.btn_ai.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_ai.clicked.connect(self.on_ai_help)
        bar_layout.addWidget(self.btn_ai)
        
        self.btn_screen = QPushButton("Analyze Screen 📺")
        self.btn_screen.setObjectName("btn_screen")
        self.btn_screen.setProperty("class", "pill-btn")
        self.btn_screen.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_screen.clicked.connect(self.on_screen_capture)
        bar_layout.addWidget(self.btn_screen)
        
        # Botão Chat (Toggle Visibilidade)
        self.btn_chat = QPushButton("Chat 💬")
        self.btn_chat.setProperty("class", "pill-btn")
        self.btn_chat.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_chat.clicked.connect(self.toggle_content_area)
        bar_layout.addWidget(self.btn_chat)
        
        bar_layout.addStretch()
        
        # -- Trash Button (Clear) --
        self.btn_clear = QPushButton("🗑️")
        self.btn_clear.setFixedSize(30, 30)
        self.btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clear.setToolTip("Limpar Transcrição e Contexto")
        self.btn_clear.clicked.connect(self.clear_all)
        bar_layout.addWidget(self.btn_clear)
        
        # -- Notes Button --
        self.btn_notes = QPushButton("📝")
        self.btn_notes.setFixedSize(30, 30)
        self.btn_notes.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_notes.setToolTip("Mostrar/Ocultar Notas")
        self.btn_notes.clicked.connect(self.toggle_notes)
        bar_layout.addWidget(self.btn_notes)
        
        # -- LALA Prep Button --
        self.btn_lala = QPushButton("🎓")
        self.btn_lala.setFixedSize(30, 30)
        self.btn_lala.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_lala.setToolTip("LALA Interview Prep")
        self.btn_lala.clicked.connect(self.toggle_lala_panel)
        bar_layout.addWidget(self.btn_lala)
        
        # -- Timer --
        self.lbl_timer = QLabel("00:00")
        self.lbl_timer.setObjectName("timer_label")
        self.lbl_timer.setVisible(False) # Só mostra gravando
        bar_layout.addWidget(self.lbl_timer)
        
        # -- Window Controls --
        
        # Menu (3 dots)
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setProperty("class", "icon-btn")
        self.btn_menu.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_menu.clicked.connect(self.show_menu)
        bar_layout.addWidget(self.btn_menu)
        
        # Drag Handle (Move)
        self.btn_move = QPushButton("✥")
        self.btn_move.setProperty("class", "icon-btn")
        self.btn_move.setCursor(QCursor(Qt.SizeAllCursor))
        # O drag vai ser tratado no evento do mouse do parent, mas indicamos visualmente
        bar_layout.addWidget(self.btn_move)
        
        # Expand/Collapse (Chevron)
        self.btn_collapse = QPushButton("▼") # Muda para ▲ quando expandido
        self.btn_collapse.setProperty("class", "icon-btn")
        self.btn_collapse.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_collapse.clicked.connect(self.toggle_content_area)
        bar_layout.addWidget(self.btn_collapse)
        
        self.main_layout.addWidget(self.top_bar)
        
        # 2. CONTENT AREA (Hidden initially)
        self.content_container = QFrame()
        self.content_container.setObjectName("content_container")
        self.content_container.setVisible(False) # Start collapsed
        
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(1, 1, 1, 1)
        content_layout.setSpacing(0)
        
        # Transcrição (Simples 3 linhas)
        self.txt_transcription = QTextEdit()
        self.txt_transcription.setObjectName("transcription_box")
        self.txt_transcription.setFixedHeight(60) # Padrão pequeno
        self.txt_transcription.setReadOnly(True)
        self.txt_transcription.setPlaceholderText("Transcrição em tempo real...")
        content_layout.addWidget(self.txt_transcription)
        
        # Scroll de Respostas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.response_pool = QWidget()
        self.response_layout = QVBoxLayout(self.response_pool)
        self.response_layout.setContentsMargins(15, 15, 15, 15)
        self.response_layout.setSpacing(15)  # Aumentado para evitar sobreposição
        self.response_layout.addStretch()
        
        self.scroll_area.setWidget(self.response_pool)
        content_layout.addWidget(self.scroll_area)
        
        # -- Chat Input Area --
        chat_input_layout = QHBoxLayout()
        chat_input_layout.setSpacing(8)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Digite sua mensagem para a IA...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 15px;
                padding: 8px 15px;
                color: #fff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #666;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        chat_input_layout.addWidget(self.chat_input)
        
        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(35, 35)
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                border-radius: 17px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #5aa0e9;
            }
        """)
        self.btn_send.clicked.connect(self.send_chat_message)
        chat_input_layout.addWidget(self.btn_send)
        
        content_layout.addLayout(chat_input_layout)
        
        self.main_layout.addWidget(self.content_container, 1) # 1 = Stretch vertical
        
# 3. NOTES PANEL (Enhanced with CRUD and resize - FIXED OVERLAY)
        self.notes_container = QFrame()
        self.notes_container.setObjectName("notes_container")
        self.notes_container.setVisible(False)
        self.notes_min_height = 150
        self.notes_max_height = 500
        self.notes_container.setMinimumHeight(self.notes_min_height)
        self.notes_container.setMaximumHeight(self.notes_max_height)
        self.notes_container.setStyleSheet("""
            QFrame#notes_container {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 2px solid #333;
                margin: 5px 0;
            }
        """)
        
        notes_layout = QVBoxLayout(self.notes_container)
        notes_layout.setContentsMargins(10, 8, 10, 5)
        notes_layout.setSpacing(6)
        
        # Header com seletor e botões CRUD
        notes_header = QHBoxLayout()
        notes_header.setSpacing(8)
        
        # Seletor de nota
        self.combo_notes = QComboBox()
        self.combo_notes.setMinimumWidth(150)
        self.combo_notes.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px 10px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self.combo_notes.currentIndexChanged.connect(self.on_note_selected)
        notes_header.addWidget(self.combo_notes)
        
        # Botões CRUD
        btn_style = "background: #333; border-radius: 4px; color: #aaa; font-size: 11px; padding: 4px 8px;"
        
        self.btn_note_add = QPushButton("+ Nova")
        self.btn_note_add.setStyleSheet(btn_style + "background: #2a5a2a;")
        self.btn_note_add.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_note_add.clicked.connect(self.add_note)
        notes_header.addWidget(self.btn_note_add)
        
        self.btn_note_rename = QPushButton("✏️")
        self.btn_note_rename.setFixedWidth(30)
        self.btn_note_rename.setStyleSheet(btn_style)
        self.btn_note_rename.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_note_rename.setToolTip("Renomear nota")
        self.btn_note_rename.clicked.connect(self.rename_note)
        notes_header.addWidget(self.btn_note_rename)
        
        self.btn_note_delete = QPushButton("🗑️")
        self.btn_note_delete.setFixedWidth(30)
        self.btn_note_delete.setStyleSheet(btn_style + "background: #4a2a2a;")
        self.btn_note_delete.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_note_delete.setToolTip("Excluir nota")
        self.btn_note_delete.clicked.connect(self.delete_note)
        notes_header.addWidget(self.btn_note_delete)
        
        notes_header.addStretch()
        
        self.btn_notes_close = QPushButton("✕")
        self.btn_notes_close.setFixedSize(20, 20)
        self.btn_notes_close.setStyleSheet("background: transparent; color: #666; font-size: 14px;")
        self.btn_notes_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_notes_close.clicked.connect(self.toggle_notes)
        notes_header.addWidget(self.btn_notes_close)
        
        notes_layout.addLayout(notes_header)
        
        # Área de texto da nota
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Escreva suas notas para ler durante a entrevista...")
        self.txt_notes.setStyleSheet("""
            QTextEdit {
                background-color: #222;
                border: none;
                border-radius: 5px;
                color: #e0e0e0;
                font-size: 14px;
                padding: 8px;
                line-height: 1.5;
            }
        """)
        self.txt_notes.textChanged.connect(self.auto_save_note)
        notes_layout.addWidget(self.txt_notes, 1)  # Stretch
        
        self.main_layout.addWidget(self.notes_container)
        
        # 3. RESIZE HANDLE (Invisible but interactive)
        self.resize_handle = QWidget()
        self.resize_handle.setObjectName("resize_handle")
        self.resize_handle.setFixedHeight(8)
        self.resize_handle.setCursor(QCursor(Qt.SizeVerCursor))
        self.main_layout.addWidget(self.resize_handle)

    def apply_styles(self):
        self.setStyleSheet(STYLESHEET)
        
    def setup_backend(self):
        """Inicializa backend."""
        api_key = os.environ.get("GROQ_API_KEY", "")
        
        # Audio
        # Audio (Instanciado sob demanda)
        # self.audio = AudioCapture() 
        # self.audio.audio_chunk_ready.connect(self.on_audio_data)
        pass
        
        # Transcriber
        if TRANSCRIBER_AVAILABLE and api_key:
            self.transcriber = TranscriberGroq(api_key)
            self.transcriber.transcription_ready.connect(self.on_transcription)
            self.transcriber.error_occurred.connect(lambda e: self.add_log(f"Erro Transcrição: {e}"))
            # Inicialização sem bloquear
            QTimer.singleShot(100, self.transcriber.load_model)
            
        # AI Helper
        if AI_AVAILABLE and api_key:
            self.ai = AIHelper(api_key, parent=self)
            self.ai.answer_ready.connect(self.on_ai_answer)
            self.ai.error_occurred.connect(lambda e: self.add_response("Erro AI", e))
            QTimer.singleShot(200, self.ai.initialize)
            
        # Screen
        if SCREEN_AVAILABLE:
            self.screen = ScreenAnalyzer(parent=self)
            self.screen.ocr_completed.connect(self.on_ocr_result)
            self.screen.error_occurred.connect(lambda e: self.add_log(f"Erro OCR: {e}"))
            
        # Context
        if CONTEXT_AVAILABLE:
            self.context = ContextManager(parent=self)
        
        # Notes Manager
        self.init_notes_manager()
        
        # LALA Manager
        self.init_lala_manager()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        menu = QMenu()
        menu.addAction("Mostrar", self.show)
        menu.addAction("Sair", self.close)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def setup_hotkey(self):
        if KEYBOARD_AVAILABLE:
            keyboard.add_hotkey('ctrl+shift+p', self.toggle_visibility)

    # ========================================================================
    # LOGIC: INTERACTIONS
    # ========================================================================

    def mousePressEvent(self, event: QMouseEvent):
        # Região de resize = últimos 15 pixels da janela
        resize_zone = 15
        
        # 1. Resize Handle? (usa Y position, não underMouse)
        if event.y() >= self.height() - resize_zone:
            self.is_resizing = True
            self.is_dragging = False
            self.drag_position = event.globalPos()
            self.resize_start_height = self.height()
            self.setCursor(QCursor(Qt.SizeVerCursor))
            event.accept()
            return
            
        # 2. Drag Window?
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.is_resizing = False
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        resize_zone = 15
        
        # Cursor visual
        if not self.is_dragging and not self.is_resizing:
            if event.y() >= self.height() - resize_zone:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
        
        if self.is_resizing:
            # Calcular novo tamanho
            delta_y = event.globalPos().y() - self.drag_position.y()
            new_height = self.resize_start_height + delta_y
            
            # Limitar
            new_height = max(self.min_height, min(self.max_height, new_height))
            
            self.resize(self.width(), new_height)
            
            # Se expandiu, mostrar conteúdo
            if new_height > 100 and not self.is_expanded:
                self.content_container.setVisible(True)
                self.is_expanded = True
                self.btn_collapse.setText("▲")
            
            event.accept()
            
        elif self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
        self.is_resizing = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def show_menu(self):
        menu = QMenu(self)
        menu.addAction("📁 Carregar Contexto", self.load_context)
        menu.addAction("⚙️ Configurações (N/A)")
        menu.addSeparator()
        menu.addAction("❌ Sair", self.close)
        menu.exec_(QCursor.pos())

    # ========================================================================
    # LOGIC: RECORDING & TRANSCRIPTION
    # ========================================================================

    def toggle_recording(self):
        try:
            if not self.is_recording:
                # Sempre criar nova instância para garantir integridade da thread
                if AUDIO_AVAILABLE:
                    # Limpar anterior se existir
                    if self.audio:
                        try:
                            self.audio.stop_recording()
                            self.audio.wait()
                        except: pass
                    
                    self.audio = AudioCapture()
                    self.audio.audio_chunk_ready.connect(self.on_audio_data)
                    self.audio.start() # Inicia QThread
                    
                    self.is_recording = True
                    self.btn_mic.setText("⏹️")
                    self.btn_mic.setStyleSheet("background-color: #4A1A1A; border: 1px solid #FF0000; border-radius: 15px;")
                    self.icon_rec.setVisible(True)
                    self.lbl_timer.setVisible(True)
                    self.start_timer()
                    
                    # Auto-expandir e focar
                    if not self.is_expanded:
                        self.toggle_content_area()
                    
                    self.txt_transcription.setPlaceholderText("Escutando...")
                else:
                    self.add_log("Erro: Módulo de áudio não disponível")
            else:
                if self.audio:
                    self.audio.stop_recording()
                    self.audio.wait()
                
                self.is_recording = False
                self.btn_mic.setText("🎤")
                self.btn_mic.setStyleSheet("")
                self.icon_rec.setVisible(False)
                self.lbl_timer.setVisible(False)
                if self.timer_rec:
                    self.timer_rec.stop()
                
                self.txt_transcription.setPlaceholderText("Clique no microfone para iniciar transcrição...")
        except Exception as e:
            print(f"Erro toggle_recording: {e}")
            self.add_log(f"Erro: {e}")

    def start_timer(self):
        self.seconds = 0
        self.timer_rec = QTimer(self)
        self.timer_rec.timeout.connect(self.update_timer)
        self.timer_rec.start(1000)
        
    def update_timer(self):
        if not self.is_recording:
            self.timer_rec.stop()
            return
        self.seconds += 1
        mins, secs = divmod(self.seconds, 60)
        self.lbl_timer.setText(f"{mins:02}:{secs:02}")

    def on_audio_data(self, chunk):
        if self.transcriber:
            self.transcriber.transcribe_chunk(chunk)

    def on_transcription(self, text):
        if not text.strip(): return
        
        # Logica para não scrollar se usuário estiver lendo? (Opcional)
        self.txt_transcription.append(text)
        self.txt_transcription.verticalScrollBar().setValue(
            self.txt_transcription.verticalScrollBar().maximum()
        )
        self.last_question = text
        
        # Auto-expandir se estiver colapsado e usuário começar a falar?
        # Melhor não, pode ser intrusivo. Mantemos manual.

    def add_log(self, text):
        """Adiciona log visual."""
        print(text) # Console
        self.txt_transcription.append(f"ℹ️ {text}")

    # ========================================================================
    # LOGIC: AI & SCREEN
    # ========================================================================

    def on_ai_help(self):
        if not self.ai: return
        
        # Pegar transcrição COMPLETA para contexto
        full_transcript = self.txt_transcription.toPlainText().strip()
        
        # A pergunta é o transcript completo (ou última pergunta detectada)
        q = full_transcript if full_transcript else self.last_question.strip()
        
        if not q:
            self.add_response("Sistema", "Fale algo ou capture a tela primeiro!")
            return
        
        # Log debug
        print(f"[DEBUG] on_ai_help - Transcript length: {len(q)} chars")
        print(f"[DEBUG] on_ai_help - session_context: {self.session_context}")
            
        self.btn_ai.setEnabled(False)
        self.btn_ai.setText("🤖 ...")
        
        resume_context = ""
        if self.context:
            resume_context = self.context.get_context()
        
        # Passar session_context (do SessionSetup)
        self.ai.generate_answer(q, resume_context, self.session_context)
        
        # Garantir visibilidade
        if not self.is_expanded:
            self.toggle_content_area()

    def on_ai_answer(self, answer):
        self.btn_ai.setEnabled(True)
        self.btn_ai.setText("AI Help ✨")
        self.btn_send.setEnabled(True)
        self.chat_input.setPlaceholderText("Digite sua mensagem para a IA...")
        self.add_response(self.last_question, answer)

    def on_screen_capture(self):
        if not self.screen: return
        self.hide()
        QTimer.singleShot(500, self._do_capture)

    def _do_capture(self):
        self.show()
        self.btn_screen.setText("📺 ...")
        self.btn_screen.setEnabled(False)
        self.txt_transcription.setPlaceholderText("Analisando tela...")
        
        if self.screen:
            self.screen.capture_and_ocr()

    def on_ocr_result(self, text):
        self.btn_screen.setText("Analyze Screen 📺")
        self.btn_screen.setEnabled(True)
        
        # Adicionar Card de Resposta (Markdown Renderizado)
        self.add_response("📸 Análise de Tela", text)
        
        # Opcional: Colocar no transcript (ou deixar limpo para não poluir?)
        # O usuário pediu para "não atrapalhar a transcrição". 
        # Vamos deixar o transcript QUIETO ou apenas um aviso.
        self.txt_transcription.setPlaceholderText("Análise completa. Veja o card abaixo.")
        # self.txt_transcription.setPlainText(f"--- ANÁLISE DE TELA ---\n\n{text}") # REMOVIDO para limpeza
        
    def clear_all(self):
        """Limpa transcrição, resetou contexto e last_question."""
        self.txt_transcription.clear()
        self.last_question = ""
        self.txt_transcription.setPlaceholderText("Transcrição limpa...")
        
        # Limpar cards antigos?
        while self.response_layout.count() > 1: # Mantém o stretch no final
            item = self.response_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.add_log("Contexto limpo.")
        
    def add_response(self, question, answer):
        card = ResponseCard(question, answer)
        card.copy_clicked.connect(self.copy_to_clipboard)
        card.delete_clicked.connect(self.remove_card)
        
        # Inserir no início ou final? Final.
        idx = self.response_layout.count() - 1 # Antes do stretch
        self.response_layout.insertWidget(idx, card)
        
        # Auto scroll
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def copy_to_clipboard(self, text):
        cb = QApplication.clipboard()
        cb.setText(text)

    def remove_card(self, card):
        card.deleteLater()

    def send_chat_message(self):
        """Envia mensagem do chat para a IA."""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Limpar input
        self.chat_input.clear()
        self.chat_input.setPlaceholderText("Enviando...")
        
        # Guardar como última pergunta
        self.last_question = message
        
        # Usar AI Helper se disponível
        if self.ai:
            self.btn_send.setEnabled(False)
            
            # Pegar contexto do ContextManager (arquivos carregados)
            resume_context = ""
            if self.context:
                resume_context = self.context.get_context()
            
            # Incluir notas no contexto se existirem
            notes = self.txt_notes.toPlainText().strip()
            if notes:
                resume_context += f"\n\n--- NOTAS DO USUÁRIO ---\n{notes}"
            
            # Pegar user_context da sessão
            user_context = self.session_context.get("user_context", "")
            
            # Mostrar INFO de contexto no log (debug)
            context_info = []
            if user_context:
                context_info.append(f"Session: {len(user_context)} chars")
            if resume_context:
                context_info.append(f"Files/Notes: {len(resume_context)} chars")
            
            if context_info:
                self.add_log(f"Contexto: {', '.join(context_info)}")
            else:
                self.add_log("⚠️ Sem contexto definido!")
            
            # Enviar para IA
            self.ai.generate_answer(message, resume_context, self.session_context)
            
            # Garantir visibilidade do conteúdo
            if not self.is_expanded:
                self.toggle_content_area()
        else:
            self.add_response("Sistema", "AI Helper não disponível. Verifique a API Key.")

    def toggle_notes(self):
        """Mostra/Oculta painel de notas - FIXED UI BREAK."""
        is_visible = self.notes_container.isVisible()
        
        # Se estiver abrindo
        if not is_visible:
            self.notes_container.setVisible(True)
            self.refresh_notes_list()
            
            # Expandir main window se estiver pequena
            current_h = self.height()
            target_h = max(current_h, 650) # Altura mínima para notas confortável
            
            if not self.is_expanded:
                self.content_container.setVisible(True)
                self.is_expanded = True
                self.btn_collapse.setText("▲")
            
            if current_h < target_h:
                self.resize(self.width(), target_h)
                
            # Fechar LALA se estiver aberto (não é mais necessário pois é janela separada, mas bom pra foco)
            # Mas como agora é janela separada, podemos deixar aberto.
            # Apenas garantimos que o botão LALA atualize se precisarmos
        else:
            self.notes_container.setVisible(False)
            # Se quiser encolher de volta quando fecha notas?
            # Melhor não forçar encolhimento, usuário pode estar lendo chat.
    
    # ========================================================================
    # NOTES MANAGEMENT
    # ========================================================================
    
    def init_notes_manager(self):
        """Inicializa o gerenciador de notas."""
        self.notes_manager = NotesManager()
        self.current_note_id = None
        self.refresh_notes_list()
    
    def refresh_notes_list(self):
        """Atualiza lista de notas no ComboBox."""
        self.combo_notes.blockSignals(True)
        self.combo_notes.clear()
        
        for note_id, title in self.notes_manager.get_titles():
            self.combo_notes.addItem(title, note_id)
        
        # Selecionar primeira se existir
        if self.combo_notes.count() > 0:
            self.combo_notes.setCurrentIndex(0)
            self.on_note_selected(0)
        
        self.combo_notes.blockSignals(False)
    
    def on_note_selected(self, index):
        """Callback quando nota é selecionada."""
        if index < 0:
            return
        
        note_id = self.combo_notes.currentData()
        if note_id:
            note = self.notes_manager.get_by_id(note_id)
            if note:
                self.current_note_id = note_id
                self.txt_notes.blockSignals(True)
                self.txt_notes.setPlainText(note.content)
                self.txt_notes.blockSignals(False)
    
    def auto_save_note(self):
        """Salva nota automaticamente ao editar."""
        if self.current_note_id:
            content = self.txt_notes.toPlainText()
            self.notes_manager.update(self.current_note_id, content=content)
    
    def add_note(self):
        """Adiciona nova nota."""
        from PyQt5.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "Nova Nota", "Nome da nota:")
        if ok and title.strip():
            note = self.notes_manager.add(title.strip(), "")
            self.refresh_notes_list()
            # Selecionar a nova nota
            idx = self.combo_notes.findData(note.id)
            if idx >= 0:
                self.combo_notes.setCurrentIndex(idx)
    
    def rename_note(self):
        """Renomeia nota selecionada."""
        if not self.current_note_id:
            return
        
        from PyQt5.QtWidgets import QInputDialog
        note = self.notes_manager.get_by_id(self.current_note_id)
        if note:
            title, ok = QInputDialog.getText(self, "Renomear Nota", "Novo nome:", text=note.title)
            if ok and title.strip():
                self.notes_manager.update(self.current_note_id, title=title.strip())
                self.refresh_notes_list()
    
    def delete_note(self):
        """Remove nota selecionada."""
        if not self.current_note_id:
            self.add_log("⚠️ Nenhuma nota selecionada para excluir")
            return
        
        from PyQt5.QtWidgets import QMessageBox
        
        # Usar None como parent para evitar conflitos com overlay translúcido
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Excluir Nota")
        msg.setText("Tem certeza que deseja excluir esta nota?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        # Garantir que aparece na frente
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        
        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            note = self.notes_manager.get_by_id(self.current_note_id)
            title = note.title if note else "Desconhecida"
            self.notes_manager.delete(self.current_note_id)
            self.current_note_id = None
            self.txt_notes.clear()
            self.refresh_notes_list()
            self.add_log(f"🗑️ Nota '{title}' excluída")
    
    # ========================================================================
    # LALA MANAGEMENT
    # ========================================================================
    
    def init_lala_manager(self):
        """Inicializa o gerenciador LALA e o painel."""
        self.lala_manager = LALAManager()
        
        # Criar como janela TOP-LEVEL (sem parent) para evitar problemas de transparência
        self.lala_panel = LALAPanel(self.lala_manager, None)
        self.lala_panel.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.lala_panel.setVisible(False)
        self.lala_panel.closed.connect(lambda: self.btn_lala.setStyleSheet(""))
        
        # Tamanho padrão maior e melhor posicionado
        self.lala_panel.resize(550, 650)
        
        logger.info(f"[LALAManager] Inicializado com {len(self.lala_manager.get_all())} perguntas")
    
    def toggle_lala_panel(self):
        """Mostra/Oculta painel LALA Prep - Janela Independente Centralizada."""
        is_visible = self.lala_panel.isVisible()
        
        if not is_visible:
            # Centralizar na tela
            screen_geo = QApplication.primaryScreen().availableGeometry()
            panel_w = self.lala_panel.width()
            panel_h = self.lala_panel.height()
            
            center_x = screen_geo.x() + (screen_geo.width() - panel_w) // 2
            center_y = screen_geo.y() + (screen_geo.height() - panel_h) // 2
            
            self.lala_panel.move(center_x, center_y)
            self.lala_panel.show()
            self.lala_panel.raise_()
            self.lala_panel.activateWindow()
            self.btn_lala.setStyleSheet("background: #22c55e;")
        else:
            self.lala_panel.hide()
            self.btn_lala.setStyleSheet("")

    # ========================================================================
    # LOGIC: UI CONTROL
    # ========================================================================

    def toggle_content_area(self):
        self.is_expanded = not self.is_expanded
        self.content_container.setVisible(self.is_expanded)
        
        if self.is_expanded:
            self.btn_collapse.setText("▲")
            # Altura padrão expandida
            if self.height() < 300:
                self.resize(self.width(), 400)
        else:
            self.btn_collapse.setText("▼")
            self.resize(self.width(), 80) # Volta para só TopBar

    def load_context(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Contexto")
        if path and self.context:
            self.context.load_file(path)
            self.add_log(f"Contexto carregado: {os.path.basename(path)}")
