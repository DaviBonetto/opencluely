"""Opencluely Context Vault panel."""

from __future__ import annotations

import logging

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QMouseEvent
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
)


logger = logging.getLogger("context_vault_panel")


class ContextPromptItem(QFrame):
    """Accordion card for a single context prompt."""

    item_updated = pyqtSignal(str, str, str)
    item_deleted = pyqtSignal(str)
    starred_toggled = pyqtSignal(str, bool)
    completed_toggled = pyqtSignal(str, bool)
    move_up_requested = pyqtSignal(str)
    move_down_requested = pyqtSignal(str)

    def __init__(
        self,
        item_id: str,
        title: str,
        content: str,
        number: int,
        starred: bool = False,
        completed: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.item_id = item_id
        self.number = number
        self.is_expanded = False
        self.is_editing = False
        self.is_starred = starred
        self.is_completed = completed
        self.setup_ui(title, content)

    def setup_ui(self, title: str, content: str):
        self.setObjectName("context_prompt_item")
        self.update_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.num_label = QLabel(f"{self.number:02d}")
        self.num_label.setStyleSheet(
            "color: #0a84ff; font-size: 18px; font-weight: bold;"
            "background: #1a2a3a; padding: 4px 10px; border-radius: 6px;"
        )
        self.num_label.setFixedWidth(45)
        self.num_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.num_label)

        self.expand_icon = QLabel("▶")
        self.expand_icon.setStyleSheet("color: #666; font-size: 14px;")
        self.expand_icon.setFixedWidth(18)
        header.addWidget(self.expand_icon)

        clean_title = title.replace(f"{self.number}. ", "").replace(f"{self.number}.", "")
        self.title_label = QLabel(clean_title)
        self.title_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 500;")
        self.title_label.setWordWrap(True)
        self.title_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.title_label.mousePressEvent = lambda event: self.toggle_expand()
        header.addWidget(self.title_label, 1)

        self.btn_star = QPushButton("★" if self.is_starred else "☆")
        self.btn_star.setFixedSize(28, 28)
        self.btn_star.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_star.setToolTip("Mark as important")
        self.update_star_style()
        self.btn_star.clicked.connect(self.toggle_star)
        header.addWidget(self.btn_star)

        self.btn_check = QPushButton("✓")
        self.btn_check.setFixedSize(28, 28)
        self.btn_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_check.setToolTip("Mark as complete")
        self.update_check_style()
        self.btn_check.clicked.connect(self.toggle_completed)
        header.addWidget(self.btn_check)

        self.btn_up = QPushButton("↑")
        self.btn_up.setFixedSize(24, 24)
        self.btn_up.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_up.setToolTip("Move up")
        self.btn_up.setStyleSheet(
            "background: #333; color: #aaa; border-radius: 4px; font-size: 14px; font-weight: bold;"
        )
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self.item_id))
        header.addWidget(self.btn_up)

        self.btn_down = QPushButton("↓")
        self.btn_down.setFixedSize(24, 24)
        self.btn_down.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_down.setToolTip("Move down")
        self.btn_down.setStyleSheet(
            "background: #333; color: #aaa; border-radius: 4px; font-size: 14px; font-weight: bold;"
        )
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self.item_id))
        header.addWidget(self.btn_down)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {'#4ade80' if content else '#666'}; font-size: 10px;")
        header.addWidget(self.status_dot)

        layout.addLayout(header)

        self.content_frame = QFrame()
        self.content_frame.setVisible(False)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(60, 10, 10, 10)

        action_bar = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_edit.setStyleSheet("background: #333; border-radius: 6px; padding: 6px 12px; color: #ccc;")
        self.btn_edit.clicked.connect(self.toggle_edit)
        action_bar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_delete.setStyleSheet("background: #3a2a2a; border-radius: 6px;")
        self.btn_delete.clicked.connect(lambda: self.item_deleted.emit(self.item_id))
        action_bar.addWidget(self.btn_delete)
        action_bar.addStretch()
        content_layout.addLayout(action_bar)

        self.content_label = QTextEdit()
        self.content_label.setReadOnly(True)
        self.content_label.setPlaceholderText("No notes yet.")
        if content:
            self.content_label.setPlainText(content)
        self.content_label.setStyleSheet(
            "QTextEdit { background: #222; color: #e0e0e0; font-size: 16px; padding: 15px;"
            "border: none; border-radius: 8px; border-left: 4px solid #0a84ff; }"
        )
        self.content_label.setMinimumHeight(120)
        content_layout.addWidget(self.content_label)

        self.content_editor = QTextEdit()
        self.content_editor.setPlainText(content)
        self.content_editor.setVisible(False)
        self.content_editor.setStyleSheet(
            "QTextEdit { background: #1a1a1a; border: 2px solid #0a84ff; font-size: 15px; padding: 10px; color: white; }"
        )
        self.content_editor.setMinimumHeight(120)
        content_layout.addWidget(self.content_editor)

        self.btn_save = QPushButton("Save")
        self.btn_save.setVisible(False)
        self.btn_save.setStyleSheet(
            "background: #22c55e; color: white; padding: 8px; border-radius: 6px; font-weight: bold;"
        )
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.clicked.connect(self.save_content)
        content_layout.addWidget(self.btn_save)

        layout.addWidget(self.content_frame)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_frame.setVisible(self.is_expanded)
        self.expand_icon.setText("▼" if self.is_expanded else "▶")
        self.expand_icon.setStyleSheet(
            f"color: {'#0a84ff' if self.is_expanded else '#666'}; font-size: 14px;"
        )

    def toggle_edit(self):
        self.is_editing = not self.is_editing
        self.content_label.setVisible(not self.is_editing)
        self.content_editor.setVisible(self.is_editing)
        self.btn_save.setVisible(self.is_editing)
        self.btn_edit.setText("Cancel" if self.is_editing else "Edit")

    def save_content(self):
        new_content = self.content_editor.toPlainText()
        self.content_label.setPlainText(new_content)
        self.status_dot.setStyleSheet(f"color: {'#4ade80' if new_content else '#666'}; font-size: 10px;")
        self.item_updated.emit(self.item_id, self.title_label.text(), new_content)
        self.toggle_edit()

    def update_card_style(self):
        if self.is_starred:
            bg_color = "#2a2a1a"
            border_color = "#f59e0b"
            hover_bg = "#3a3a2a"
        elif self.is_completed:
            bg_color = "#1a2a1a"
            border_color = "#22c55e"
            hover_bg = "#2a3a2a"
        else:
            bg_color = "#1a1a1a"
            border_color = "#2a2a2a"
            hover_bg = "#202020"

        self.setStyleSheet(
            f"""
            QFrame#context_prompt_item {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                margin: 3px 0;
            }}
            QFrame#context_prompt_item:hover {{
                border-color: #444;
                background-color: {hover_bg};
            }}
            """
        )

    def update_star_style(self):
        if self.is_starred:
            self.btn_star.setStyleSheet("background: #f59e0b; color: #000; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("★")
        else:
            self.btn_star.setStyleSheet("background: #333; color: #888; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("☆")

    def update_check_style(self):
        if self.is_completed:
            self.btn_check.setStyleSheet(
                "background: #22c55e; color: #fff; border-radius: 6px; font-size: 14px; font-weight: bold;"
            )
        else:
            self.btn_check.setStyleSheet(
                "background: #333; color: #666; border-radius: 6px; font-size: 14px; font-weight: bold;"
            )

    def toggle_star(self):
        self.is_starred = not self.is_starred
        if self.is_starred:
            self.is_completed = False
            self.update_check_style()
        self.update_star_style()
        self.update_card_style()
        self.starred_toggled.emit(self.item_id, self.is_starred)
        if not self.is_starred and self.is_completed:
            self.completed_toggled.emit(self.item_id, False)

    def toggle_completed(self):
        self.is_completed = not self.is_completed
        if self.is_completed:
            self.is_starred = False
            self.update_star_style()
        self.update_check_style()
        self.update_card_style()
        self.completed_toggled.emit(self.item_id, self.is_completed)


class ContextVaultPanel(QFrame):
    """Standalone floating panel for the Context Vault."""

    closed = pyqtSignal()

    def __init__(self, context_vault_manager, parent=None):
        super().__init__(parent)
        self.manager = context_vault_manager
        self.prompt_widgets = []
        self.is_resizing = False
        self.is_dragging = False
        self.resize_edge = None
        self.drag_start_pos = None
        self.drag_start_geometry = None
        self.setup_ui()
        self.load_prompts()

    def setup_ui(self):
        self.setObjectName("context_vault_panel")
        self.setMinimumSize(450, 400)
        self.setMouseTracking(True)
        self.setStyleSheet(
            """
            QFrame#context_vault_panel {
                background-color: #0d0d0d;
                border: 2px solid #333;
                border-radius: 16px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #1a1a1a; border-radius: 16px 16px 0 0;")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("📚 Context Vault")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.counter_label = QLabel("0 prompts")
        self.counter_label.setStyleSheet("color: #888; font-size: 12px; margin-right: 15px;")
        header_layout.addWidget(self.counter_label)

        btn_add = QPushButton("+ New")
        btn_add.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add.setStyleSheet("background: #22c55e; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold;")
        btn_add.clicked.connect(self.add_prompt)
        header_layout.addWidget(btn_add)

        btn_close = QPushButton("✕")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("background: #333; color: #aaa; border-radius: 15px; font-size: 14px; margin-left: 10px;")
        btn_close.clicked.connect(self.close_panel)
        header_layout.addWidget(btn_close)

        layout.addWidget(header)

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

        grip = QLabel("⋮⋮")
        grip.setAlignment(Qt.AlignCenter)
        grip.setStyleSheet("color: #444; font-size: 12px; padding: 2px;")
        layout.addWidget(grip)

    def load_prompts(self):
        for widget in self.prompt_widgets:
            widget.deleteLater()
        self.prompt_widgets.clear()

        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        prompts = self.manager.get_all()
        for index, prompt in enumerate(prompts, 1):
            self.add_prompt_widget(prompt, index)

        self.update_counter()

    def add_prompt_widget(self, prompt, number):
        widget = ContextPromptItem(
            prompt.id,
            prompt.title,
            prompt.content,
            number,
            starred=prompt.starred,
            completed=prompt.completed,
        )
        widget.item_updated.connect(self.on_update)
        widget.item_deleted.connect(self.on_delete)
        widget.starred_toggled.connect(self.on_star_toggled)
        widget.completed_toggled.connect(self.on_completed_toggled)
        widget.move_up_requested.connect(self.on_move_up)
        widget.move_down_requested.connect(self.on_move_down)

        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
        self.prompt_widgets.append(widget)

    def add_prompt(self):
        title, ok = QInputDialog.getText(self, "New Context Prompt", "Title:", flags=Qt.WindowStaysOnTopHint)
        if ok and title.strip():
            self.manager.add(title.strip())
            self.load_prompts()

    def on_update(self, item_id, title, content):
        self.manager.update(item_id, title=title, content=content)

    def on_delete(self, item_id):
        if self.manager.delete(item_id):
            self.load_prompts()

    def on_star_toggled(self, item_id, starred):
        self.manager.update(item_id, starred=starred)
        if starred:
            self.manager.update(item_id, completed=False)

    def on_completed_toggled(self, item_id, completed):
        self.manager.update(item_id, completed=completed)
        if completed:
            self.manager.update(item_id, starred=False)

    def on_move_up(self, item_id):
        if self.manager.move_up(item_id):
            self.load_prompts()

    def on_move_down(self, item_id):
        if self.manager.move_down(item_id):
            self.load_prompts()

    def update_counter(self):
        self.counter_label.setText(f"{len(self.manager.get_all())} prompts")

    def close_panel(self):
        self.hide()
        self.closed.emit()

    def get_resize_edge(self, pos: QPoint) -> str:
        margin = 10
        width, height = self.width(), self.height()
        x_pos, y_pos = pos.x(), pos.y()

        edge = ""
        if y_pos <= margin:
            edge += "top"
        elif y_pos >= height - margin:
            edge += "bottom"

        if x_pos <= margin:
            edge += ("-" if edge else "") + "left"
        elif x_pos >= width - margin:
            edge += ("-" if edge else "") + "right"

        return edge if edge else None

    def is_in_header(self, pos: QPoint) -> bool:
        return pos.y() <= 60 and not self.get_resize_edge(pos)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            edge = self.get_resize_edge(event.pos())
            if edge:
                self.is_resizing = True
                self.is_dragging = False
                self.resize_edge = edge
                self.drag_start_pos = event.globalPos()
                self.drag_start_geometry = self.geometry()
            elif self.is_in_header(event.pos()):
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
            geometry = self.drag_start_geometry
            new_geometry = QRect(geometry)

            dx, dy = delta.x(), delta.y()

            if "right" in self.resize_edge:
                new_geometry.setWidth(max(400, geometry.width() + dx))
            if "left" in self.resize_edge:
                width = max(400, geometry.width() - dx)
                new_geometry.setX(geometry.right() - width)
            if "bottom" in self.resize_edge:
                new_geometry.setHeight(max(300, geometry.height() + dy))
            if "top" in self.resize_edge:
                height = max(300, geometry.height() - dy)
                new_geometry.setY(geometry.bottom() - height)

            self.setGeometry(new_geometry)
        elif self.is_dragging:
            delta = event.globalPos() - self.drag_start_pos
            self.move(self.drag_start_geometry.topLeft() + delta)
        else:
            edge = self.get_resize_edge(event.pos())
            if edge in ["top", "bottom"]:
                cursor = Qt.SizeVerCursor
            elif edge in ["left", "right"]:
                cursor = Qt.SizeHorCursor
            elif edge in ["top-left", "bottom-right"]:
                cursor = Qt.SizeFDiagCursor
            elif edge in ["top-right", "bottom-left"]:
                cursor = Qt.SizeBDiagCursor
            elif self.is_in_header(event.pos()):
                cursor = Qt.SizeAllCursor
            else:
                cursor = Qt.ArrowCursor
            self.setCursor(QCursor(cursor))

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_resizing = False
        self.is_dragging = False
        self.setCursor(QCursor(Qt.ArrowCursor))
