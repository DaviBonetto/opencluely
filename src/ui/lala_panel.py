# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - LALA Prep Panel (Enhanced)
Painel de preparação para entrevista LALA - Otimizado para leitura rápida
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QCursor, QMouseEvent

logger = logging.getLogger('lala_panel')


class QuestionItem(QFrame):
    """Widget de pergunta com acordeão."""
    
    question_updated = pyqtSignal(str, str, str)  # id, title, content
    question_deleted = pyqtSignal(str)  # id
    starred_toggled = pyqtSignal(str, bool)  # id, starred
    completed_toggled = pyqtSignal(str, bool)  # id, completed
    move_up_requested = pyqtSignal(str)  # id
    move_down_requested = pyqtSignal(str)  # id
    
    def __init__(self, question_id: str, title: str, content: str, number: int, 
                 starred: bool = False, completed: bool = False, parent=None):
        super().__init__(parent)
        self.question_id = question_id
        self.number = number
        self.is_expanded = False
        self.is_editing = False
        self.is_starred = starred
        self.is_completed = completed
        self.setup_ui(title, content)
    
    def setup_ui(self, title: str, content: str):
        self.setObjectName("question_item")
        self.update_card_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # Header (título clicável)
        header = QHBoxLayout()
        header.setSpacing(12)
        
        # Número
        self.num_label = QLabel(f"{self.number:02d}")
        self.num_label.setStyleSheet("""
            color: #0a84ff; font-size: 18px; font-weight: bold;
            background: #1a2a3a; padding: 4px 10px; border-radius: 6px;
        """)
        self.num_label.setFixedWidth(45)
        self.num_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.num_label)
        
        # Ícone expandir
        self.expand_icon = QLabel("▶")
        self.expand_icon.setStyleSheet("color: #666; font-size: 14px;")
        self.expand_icon.setFixedWidth(18)
        header.addWidget(self.expand_icon)
        
        # Título
        clean_title = title.replace(f"{self.number}. ", "").replace(f"{self.number}.", "")
        self.title_label = QLabel(clean_title)
        self.title_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 500;")
        self.title_label.setWordWrap(True)
        self.title_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.title_label.mousePressEvent = lambda e: self.toggle_expand()
        header.addWidget(self.title_label, 1)
        
        # Botão Estrela (importante)
        self.btn_star = QPushButton("★" if self.is_starred else "☆")
        self.btn_star.setFixedSize(28, 28)
        self.btn_star.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_star.setToolTip("Marcar como importante")
        self.update_star_style()
        self.btn_star.clicked.connect(self.toggle_star)
        header.addWidget(self.btn_star)
        
        # Botão Concluído (check)
        self.btn_check = QPushButton("✓")
        self.btn_check.setFixedSize(28, 28)
        self.btn_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_check.setToolTip("Marcar como concluído")
        self.update_check_style()
        self.btn_check.clicked.connect(self.toggle_completed)
        header.addWidget(self.btn_check)
        
        # Botão Mover para cima
        self.btn_up = QPushButton("↑")
        self.btn_up.setFixedSize(24, 24)
        self.btn_up.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_up.setToolTip("Mover para cima")
        self.btn_up.setStyleSheet("background: #333; color: #aaa; border-radius: 4px; font-size: 14px; font-weight: bold;")
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self.question_id))
        header.addWidget(self.btn_up)
        
        # Botão Mover para baixo
        self.btn_down = QPushButton("↓")
        self.btn_down.setFixedSize(24, 24)
        self.btn_down.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_down.setToolTip("Mover para baixo")
        self.btn_down.setStyleSheet("background: #333; color: #aaa; border-radius: 4px; font-size: 14px; font-weight: bold;")
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self.question_id))
        header.addWidget(self.btn_down)
        
        # Indicador status
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {'#4ade80' if content else '#666'}; font-size: 10px;")
        header.addWidget(self.status_dot)
        
        layout.addLayout(header)
        
        # Área de Conteúdo (Hidden by default)
        self.content_frame = QFrame()
        self.content_frame.setVisible(False)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(60, 10, 10, 10)
        
        # Toolbar
        action_bar = QHBoxLayout()
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_edit.setStyleSheet("background: #333; border-radius: 6px; padding: 6px 12px; color: #ccc;")
        self.btn_edit.clicked.connect(self.toggle_edit)
        action_bar.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_delete.setStyleSheet("background: #3a2a2a; border-radius: 6px;")
        self.btn_delete.clicked.connect(lambda: self.question_deleted.emit(self.question_id))
        action_bar.addWidget(self.btn_delete)
        action_bar.addStretch()
        content_layout.addLayout(action_bar)
        
        # Leitor
        self.content_label = QTextEdit()
        self.content_label.setReadOnly(True)
        self.content_label.setPlaceholderText("Sem resposta definida.")
        if content: self.content_label.setPlainText(content)
        self.content_label.setStyleSheet("""
            QTextEdit { background: #222; color: #e0e0e0; font-size: 16px; padding: 15px; border: none; border-radius: 8px; border-left: 4px solid #0a84ff; }
        """)
        self.content_label.setMinimumHeight(120)
        content_layout.addWidget(self.content_label)
        
        # Editor
        self.content_editor = QTextEdit()
        self.content_editor.setPlainText(content)
        self.content_editor.setVisible(False)
        self.content_editor.setStyleSheet("QTextEdit { background: #1a1a1a; border: 2px solid #0a84ff; font-size: 15px; padding: 10px; color: white; }")
        self.content_editor.setMinimumHeight(120)
        content_layout.addWidget(self.content_editor)
        
        # Botão Salvar
        self.btn_save = QPushButton("💾 Salvar")
        self.btn_save.setVisible(False)
        self.btn_save.setStyleSheet("background: #22c55e; color: white; padding: 8px; border-radius: 6px; font-weight: bold;")
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.clicked.connect(self.save_content)
        content_layout.addWidget(self.btn_save)
        
        layout.addWidget(self.content_frame)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_frame.setVisible(self.is_expanded)
        self.expand_icon.setText("▼" if self.is_expanded else "▶")
        self.expand_icon.setStyleSheet(f"color: {'#0a84ff' if self.is_expanded else '#666'}; font-size: 14px;")

    def toggle_edit(self):
        self.is_editing = not self.is_editing
        self.content_label.setVisible(not self.is_editing)
        self.content_editor.setVisible(self.is_editing)
        self.btn_save.setVisible(self.is_editing)
        self.btn_edit.setText("❌ Cancelar" if self.is_editing else "✏️ Editar")

    def save_content(self):
        new_content = self.content_editor.toPlainText()
        self.content_label.setPlainText(new_content)
        self.status_dot.setStyleSheet(f"color: {'#4ade80' if new_content else '#666'}; font-size: 10px;")
        
        # Emitir sinal de update
        self.question_updated.emit(self.question_id, self.title_label.text(), new_content)
        self.toggle_edit()
    
    def update_card_style(self):
        """Atualiza o estilo do cartão baseado no estado (starred/completed)."""
        if self.is_starred:
            bg_color = "#2a2a1a"  # Amarelado para importante
            border_color = "#f59e0b"  # Laranja/ouro
            hover_bg = "#3a3a2a"
        elif self.is_completed:
            bg_color = "#1a2a1a"  # Esverdeado para concluído
            border_color = "#22c55e"  # Verde
            hover_bg = "#2a3a2a"
        else:
            bg_color = "#1a1a1a"
            border_color = "#2a2a2a"
            hover_bg = "#202020"
        
        self.setStyleSheet(f"""
            QFrame#question_item {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                margin: 3px 0;
            }}
            QFrame#question_item:hover {{
                border-color: #444;
                background-color: {hover_bg};
            }}
        """)
    
    def update_star_style(self):
        """Atualiza estilo do botão estrela."""
        if self.is_starred:
            self.btn_star.setStyleSheet("background: #f59e0b; color: #000; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("★")
        else:
            self.btn_star.setStyleSheet("background: #333; color: #888; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("☆")
    
    def update_check_style(self):
        """Atualiza estilo do botão check."""
        if self.is_completed:
            self.btn_check.setStyleSheet("background: #22c55e; color: #fff; border-radius: 6px; font-size: 14px; font-weight: bold;")
        else:
            self.btn_check.setStyleSheet("background: #333; color: #666; border-radius: 6px; font-size: 14px; font-weight: bold;")
    
    def toggle_star(self):
        """Alterna o estado de importante."""
        self.is_starred = not self.is_starred
        if self.is_starred:
            self.is_completed = False  # Se marcar como importante, desmarca concluído
            self.update_check_style()
        self.update_star_style()
        self.update_card_style()
        self.starred_toggled.emit(self.question_id, self.is_starred)
        if not self.is_starred and self.is_completed:
            self.completed_toggled.emit(self.question_id, False)
    
    def toggle_completed(self):
        """Alterna o estado de concluído."""
        self.is_completed = not self.is_completed
        if self.is_completed:
            self.is_starred = False  # Se marcar como concluído, desmarca importante
            self.update_star_style()
        self.update_check_style()
        self.update_card_style()
        self.completed_toggled.emit(self.question_id, self.is_completed)


class LALAPanel(QFrame):
    """Painel principal do LALA Prep."""
    
    closed = pyqtSignal()
    
    def __init__(self, lala_manager, parent=None):
        super().__init__(parent)
        self.manager = lala_manager
        self.question_widgets = []
        
        # Resize and Drag variables
        self.is_resizing = False
        self.is_dragging = False
        self.resize_edge = None
        self.drag_start_pos = None
        self.drag_start_geometry = None
        
        self.setup_ui()
        self.load_questions()
        
    def setup_ui(self):
        self.setObjectName("lala_panel")
        self.setMinimumSize(450, 400)
        self.setMouseTracking(True)  # Importante para resize
        self.setStyleSheet("""
            QFrame#lala_panel {
                background-color: #0d0d0d;
                border: 2px solid #333;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER
        header = QFrame()
        header.setStyleSheet("background: #1a1a1a; border-radius: 16px 16px 0 0;")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("🎓 LALA Interview Prep")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        h_layout.addWidget(title)
        
        h_layout.addStretch()
        
        self.counter_label = QLabel("0 perguntas")
        self.counter_label.setStyleSheet("color: #888; font-size: 12px; margin-right: 15px;")
        h_layout.addWidget(self.counter_label)
        
        btn_add = QPushButton("+ Nova")
        btn_add.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add.setStyleSheet("background: #22c55e; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold;")
        btn_add.clicked.connect(self.add_question)
        h_layout.addWidget(btn_add)
        
        btn_close = QPushButton("✕")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("background: #333; color: #aaa; border-radius: 15px; font-size: 14px; margin-left: 10px;")
        btn_close.clicked.connect(self.close_panel)
        h_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # LISTA SROLL
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar:vertical { background: #111; width: 10px; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        # RESIZE GRIP VISUAL
        grip = QLabel("⋮⋮")
        grip.setAlignment(Qt.AlignCenter)
        grip.setStyleSheet("color: #444; font-size: 12px; padding: 2px;")
        layout.addWidget(grip)

    def load_questions(self):
        # Limpar
        for w in self.question_widgets:
            w.deleteLater()
        self.question_widgets.clear()
        
        # Limpar layout (exceto stretch)
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Adicionar
        questions = self.manager.get_all()
        for i, q in enumerate(questions, 1):
            self.add_question_widget(q, i)
        
        self.update_counter()

    def add_question_widget(self, question, number):
        w = QuestionItem(question.id, question.title, question.content, number,
                         starred=question.starred, completed=question.completed)
        w.question_updated.connect(self.on_update)
        w.question_deleted.connect(self.on_delete)
        w.starred_toggled.connect(self.on_star_toggled)
        w.completed_toggled.connect(self.on_completed_toggled)
        w.move_up_requested.connect(self.on_move_up)
        w.move_down_requested.connect(self.on_move_down)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, w)
        self.question_widgets.append(w)

    def add_question(self):
        title, ok = QInputDialog.getText(self, "Nova Pergunta", "Título:", flags=Qt.WindowStaysOnTopHint)
        if ok and title.strip():
            q = self.manager.add(title.strip())
            self.load_questions() # Reload simples pra reordenar números

    def on_update(self, q_id, title, content):
        self.manager.update(q_id, title=title, content=content)
    
    def on_delete(self, q_id):
        if self.manager.delete(q_id):
            self.load_questions()
    
    def on_star_toggled(self, q_id, starred):
        """Handler para quando o usuário marca/desmarca como importante."""
        self.manager.update(q_id, starred=starred)
        if starred:
            self.manager.update(q_id, completed=False)
    
    def on_completed_toggled(self, q_id, completed):
        """Handler para quando o usuário marca/desmarca como concluído."""
        self.manager.update(q_id, completed=completed)
        if completed:
            self.manager.update(q_id, starred=False)
    
    def on_move_up(self, q_id):
        """Move o cartão para cima."""
        if self.manager.move_up(q_id):
            self.load_questions()
    
    def on_move_down(self, q_id):
        """Move o cartão para baixo."""
        if self.manager.move_down(q_id):
            self.load_questions()

    def update_counter(self):
        count = len(self.manager.get_all())
        self.counter_label.setText(f"{count} perguntas")

    def close_panel(self):
        self.hide()
        self.closed.emit()

    # --- RESIZE AND DRAG LOGIC ---
    def get_resize_edge(self, pos: QPoint) -> str:
        margin = 10
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        
        edge = ""
        if y <= margin: edge += "top"
        elif y >= h - margin: edge += "bottom"
        
        if x <= margin: edge += ("-" if edge else "") + "left"
        elif x >= w - margin: edge += ("-" if edge else "") + "right"
        
        return edge if edge else None

    def is_in_header(self, pos: QPoint) -> bool:
        """Verifica se o clique foi no header (primeiros 60px)."""
        return pos.y() <= 60 and not self.get_resize_edge(pos)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            edge = self.get_resize_edge(event.pos())
            if edge:
                # Resize mode
                self.is_resizing = True
                self.is_dragging = False
                self.resize_edge = edge
                self.drag_start_pos = event.globalPos()
                self.drag_start_geometry = self.geometry()
            elif self.is_in_header(event.pos()):
                # Drag mode (move window)
                self.is_dragging = True
                self.is_resizing = False
                self.drag_start_pos = event.globalPos()
                self.drag_start_geometry = self.geometry()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_resizing:
            delta = event.globalPos() - self.drag_start_pos
            geo = self.drag_start_geometry
            new_geo = QRect(geo)
            
            dx, dy = delta.x(), delta.y()
            
            if "right" in self.resize_edge:
                new_geo.setWidth(max(400, geo.width() + dx))
            if "left" in self.resize_edge:
                w = max(400, geo.width() - dx)
                new_geo.setX(geo.right() - w)
            if "bottom" in self.resize_edge:
                new_geo.setHeight(max(300, geo.height() + dy))
            if "top" in self.resize_edge:
                h = max(300, geo.height() - dy)
                new_geo.setY(geo.bottom() - h)
            
            self.setGeometry(new_geo)
        elif self.is_dragging:
            # Move window
            delta = event.globalPos() - self.drag_start_pos
            new_pos = self.drag_start_geometry.topLeft() + delta
            self.move(new_pos)
        else:
            # Update cursor based on position
            edge = self.get_resize_edge(event.pos())
            if edge:
                if edge in ["top", "bottom"]: cursor = Qt.SizeVerCursor
                elif edge in ["left", "right"]: cursor = Qt.SizeHorCursor
                elif edge in ["top-left", "bottom-right"]: cursor = Qt.SizeFDiagCursor
                elif edge in ["top-right", "bottom-left"]: cursor = Qt.SizeBDiagCursor
                else: cursor = Qt.ArrowCursor
                self.setCursor(QCursor(cursor))
            elif self.is_in_header(event.pos()):
                self.setCursor(QCursor(Qt.SizeAllCursor))  # Move cursor
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_resizing = False
        self.is_dragging = False
        self.setCursor(QCursor(Qt.ArrowCursor))

