# -*- coding: utf-8 -*-
"""Opencluely Prep Deck panel."""

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
    QWidget,
)

try:
    from brand import PREP_DECK_NAME
except ImportError:
    from src.brand import PREP_DECK_NAME

logger = logging.getLogger("prep_deck_panel")


class PrepDeckItem(QFrame):
    """Accordion card for one prep prompt."""

    prompt_updated = pyqtSignal(str, str, str)
    prompt_deleted = pyqtSignal(str)
    starred_toggled = pyqtSignal(str, bool)
    completed_toggled = pyqtSignal(str, bool)
    move_up_requested = pyqtSignal(str)
    move_down_requested = pyqtSignal(str)

    def __init__(
        self,
        prompt_id: str,
        title: str,
        content: str,
        number: int,
        starred: bool = False,
        completed: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.prompt_id = prompt_id
        self.number = number
        self.is_expanded = False
        self.is_editing = False
        self.is_starred = starred
        self.is_completed = completed
        self._build_ui(title, content)

    def _build_ui(self, title: str, content: str) -> None:
        self.setObjectName("prep_deck_item")
        self._apply_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.num_label = QLabel(f"{self.number:02d}")
        self.num_label.setAlignment(Qt.AlignCenter)
        self.num_label.setFixedWidth(46)
        self.num_label.setStyleSheet(
            """
            color: #4F86F7;
            font-size: 18px;
            font-weight: 700;
            background: rgba(79, 134, 247, 0.14);
            padding: 4px 10px;
            border-radius: 6px;
            """
        )
        header.addWidget(self.num_label)

        self.expand_icon = QLabel(">")
        self.expand_icon.setFixedWidth(18)
        self.expand_icon.setStyleSheet("color: #6B7A98; font-size: 14px;")
        header.addWidget(self.expand_icon)

        clean_title = title.replace(f"{self.number}. ", "").replace(f"{self.number}.", "")
        self.title_label = QLabel(clean_title)
        self.title_label.setWordWrap(True)
        self.title_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.title_label.setStyleSheet("color: #F8F8FF; font-size: 16px; font-weight: 600;")
        self.title_label.mousePressEvent = lambda event: self.toggle_expand()
        header.addWidget(self.title_label, 1)

        self.btn_star = QPushButton()
        self.btn_star.setFixedSize(28, 28)
        self.btn_star.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_star.setToolTip("Mark as priority")
        self.btn_star.clicked.connect(self.toggle_star)
        header.addWidget(self.btn_star)

        self.btn_check = QPushButton("OK")
        self.btn_check.setFixedSize(34, 28)
        self.btn_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_check.setToolTip("Mark as ready")
        self.btn_check.clicked.connect(self.toggle_completed)
        header.addWidget(self.btn_check)

        self.btn_up = QPushButton("^")
        self.btn_up.setFixedSize(24, 24)
        self.btn_up.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_up.setToolTip("Move up")
        self.btn_up.setStyleSheet(
            "background: #14213a; color: #9FB0CC; border-radius: 4px; font-size: 13px; font-weight: 700;"
        )
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self.prompt_id))
        header.addWidget(self.btn_up)

        self.btn_down = QPushButton("v")
        self.btn_down.setFixedSize(24, 24)
        self.btn_down.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_down.setToolTip("Move down")
        self.btn_down.setStyleSheet(
            "background: #14213a; color: #9FB0CC; border-radius: 4px; font-size: 13px; font-weight: 700;"
        )
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self.prompt_id))
        header.addWidget(self.btn_down)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {'#4ADE80' if content else '#5C667A'}; font-size: 10px;")
        header.addWidget(self.status_dot)

        layout.addLayout(header)

        self.content_frame = QFrame()
        self.content_frame.setVisible(False)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(60, 10, 10, 10)

        action_bar = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_edit.setStyleSheet("background: #14213a; border-radius: 6px; padding: 6px 12px; color: #D5DDF0;")
        self.btn_edit.clicked.connect(self.toggle_edit)
        action_bar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(30)
        self.btn_delete.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_delete.setStyleSheet("background: #2B1720; color: #F8F8FF; border-radius: 6px; padding: 0 10px;")
        self.btn_delete.clicked.connect(lambda: self.prompt_deleted.emit(self.prompt_id))
        action_bar.addWidget(self.btn_delete)
        action_bar.addStretch()
        content_layout.addLayout(action_bar)

        self.content_label = QTextEdit()
        self.content_label.setReadOnly(True)
        self.content_label.setPlaceholderText("No notes yet.")
        if content:
            self.content_label.setPlainText(content)
        self.content_label.setMinimumHeight(120)
        self.content_label.setStyleSheet(
            """
            QTextEdit {
                background: rgba(12, 20, 36, 0.92);
                color: #E4EBF8;
                font-size: 15px;
                padding: 15px;
                border: none;
                border-radius: 8px;
                border-left: 4px solid #4F86F7;
            }
            """
        )
        content_layout.addWidget(self.content_label)

        self.content_editor = QTextEdit()
        self.content_editor.setPlainText(content)
        self.content_editor.setVisible(False)
        self.content_editor.setMinimumHeight(120)
        self.content_editor.setStyleSheet(
            "QTextEdit { background: #0D1527; border: 2px solid #4F86F7; font-size: 15px; padding: 10px; color: #F8F8FF; }"
        )
        content_layout.addWidget(self.content_editor)

        self.btn_save = QPushButton("Save")
        self.btn_save.setVisible(False)
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.setStyleSheet(
            "background: #4F86F7; color: white; padding: 8px; border-radius: 6px; font-weight: 700;"
        )
        self.btn_save.clicked.connect(self.save_content)
        content_layout.addWidget(self.btn_save)

        layout.addWidget(self.content_frame)

        self._apply_star_style()
        self._apply_check_style()

    def toggle_expand(self) -> None:
        self.is_expanded = not self.is_expanded
        self.content_frame.setVisible(self.is_expanded)
        self.expand_icon.setText("v" if self.is_expanded else ">")
        self.expand_icon.setStyleSheet(f"color: {'#4F86F7' if self.is_expanded else '#6B7A98'}; font-size: 14px;")

    def toggle_edit(self) -> None:
        self.is_editing = not self.is_editing
        self.content_label.setVisible(not self.is_editing)
        self.content_editor.setVisible(self.is_editing)
        self.btn_save.setVisible(self.is_editing)
        self.btn_edit.setText("Cancel" if self.is_editing else "Edit")

    def save_content(self) -> None:
        new_content = self.content_editor.toPlainText()
        self.content_label.setPlainText(new_content)
        self.status_dot.setStyleSheet(f"color: {'#4ADE80' if new_content else '#5C667A'}; font-size: 10px;")
        self.prompt_updated.emit(self.prompt_id, self.title_label.text(), new_content)
        self.toggle_edit()

    def _apply_card_style(self) -> None:
        if self.is_starred:
            bg_color = "rgba(58, 42, 15, 0.96)"
            border_color = "#FBBF24"
            hover_bg = "rgba(72, 50, 16, 0.98)"
        elif self.is_completed:
            bg_color = "rgba(15, 47, 31, 0.96)"
            border_color = "#4ADE80"
            hover_bg = "rgba(18, 58, 36, 0.98)"
        else:
            bg_color = "rgba(9, 17, 31, 0.96)"
            border_color = "rgba(130, 166, 249, 0.18)"
            hover_bg = "rgba(13, 24, 44, 0.98)"

        self.setStyleSheet(
            f"""
            QFrame#prep_deck_item {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                margin: 3px 0;
            }}
            QFrame#prep_deck_item:hover {{
                border-color: #4F86F7;
                background-color: {hover_bg};
            }}
            """
        )

    def _apply_star_style(self) -> None:
        if self.is_starred:
            self.btn_star.setStyleSheet("background: #FBBF24; color: #08111F; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("*")
        else:
            self.btn_star.setStyleSheet("background: #14213A; color: #6B7A98; border-radius: 6px; font-size: 16px;")
            self.btn_star.setText("o")

    def _apply_check_style(self) -> None:
        if self.is_completed:
            self.btn_check.setStyleSheet(
                "background: #4ADE80; color: #08111F; border-radius: 6px; font-size: 12px; font-weight: 700;"
            )
        else:
            self.btn_check.setStyleSheet(
                "background: #14213A; color: #6B7A98; border-radius: 6px; font-size: 12px; font-weight: 700;"
            )

    def toggle_star(self) -> None:
        self.is_starred = not self.is_starred
        if self.is_starred:
            self.is_completed = False
            self._apply_check_style()
        self._apply_star_style()
        self._apply_card_style()
        self.starred_toggled.emit(self.prompt_id, self.is_starred)
        if not self.is_starred and self.is_completed:
            self.completed_toggled.emit(self.prompt_id, False)

    def toggle_completed(self) -> None:
        self.is_completed = not self.is_completed
        if self.is_completed:
            self.is_starred = False
            self._apply_star_style()
        self._apply_check_style()
        self._apply_card_style()
        self.completed_toggled.emit(self.prompt_id, self.is_completed)


class PrepDeckPanel(QFrame):
    """Floating prep workspace."""

    closed = pyqtSignal()

    def __init__(self, prep_manager, parent=None):
        super().__init__(parent)
        self.manager = prep_manager
        self.prompt_widgets = []
        self.is_resizing = False
        self.is_dragging = False
        self.resize_edge = None
        self.drag_start_pos = None
        self.drag_start_geometry = None
        self._build_ui()
        self.load_prompts()

    def _build_ui(self) -> None:
        self.setObjectName("prep_deck_panel")
        self.setMinimumSize(450, 400)
        self.setMouseTracking(True)
        self.setStyleSheet(
            """
            QFrame#prep_deck_panel {
                background-color: #08111F;
                border: 1px solid rgba(130, 166, 249, 0.35);
                border-radius: 16px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #101B31; border-radius: 16px 16px 0 0;")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel(PREP_DECK_NAME)
        title.setStyleSheet("color: #F8F8FF; font-size: 18px; font-weight: 700;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.counter_label = QLabel("0 prompts")
        self.counter_label.setStyleSheet("color: #9FB0CC; font-size: 12px; margin-right: 15px;")
        header_layout.addWidget(self.counter_label)

        btn_add = QPushButton("+ Add")
        btn_add.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add.setStyleSheet(
            "background: #4F86F7; color: white; border-radius: 6px; padding: 6px 12px; font-weight: 700;"
        )
        btn_add.clicked.connect(self.add_prompt)
        header_layout.addWidget(btn_add)

        btn_close = QPushButton("x")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("background: #16213A; color: #9FB0CC; border-radius: 15px; font-size: 14px;")
        btn_close.clicked.connect(self.close_panel)
        header_layout.addWidget(btn_close)

        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; } QScrollBar:vertical { background: #111; width: 10px; }"
        )

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        grip = QLabel("::")
        grip.setAlignment(Qt.AlignCenter)
        grip.setStyleSheet("color: #42506C; font-size: 12px; padding: 2px;")
        layout.addWidget(grip)

    def load_prompts(self) -> None:
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

    def add_prompt_widget(self, prompt, number: int) -> None:
        widget = PrepDeckItem(
            prompt.id,
            prompt.title,
            prompt.content,
            number,
            starred=prompt.starred,
            completed=prompt.completed,
        )
        widget.prompt_updated.connect(self.on_update)
        widget.prompt_deleted.connect(self.on_delete)
        widget.starred_toggled.connect(self.on_star_toggled)
        widget.completed_toggled.connect(self.on_completed_toggled)
        widget.move_up_requested.connect(self.on_move_up)
        widget.move_down_requested.connect(self.on_move_down)
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
        self.prompt_widgets.append(widget)

    def add_prompt(self) -> None:
        title, ok = QInputDialog.getText(self, "New Prompt", "Title:", flags=Qt.WindowStaysOnTopHint)
        if ok and title.strip():
            self.manager.add(title.strip())
            self.load_prompts()

    def on_update(self, prompt_id: str, title: str, content: str) -> None:
        self.manager.update(prompt_id, title=title, content=content)

    def on_delete(self, prompt_id: str) -> None:
        if self.manager.delete(prompt_id):
            self.load_prompts()

    def on_star_toggled(self, prompt_id: str, starred: bool) -> None:
        self.manager.update(prompt_id, starred=starred)
        if starred:
            self.manager.update(prompt_id, completed=False)

    def on_completed_toggled(self, prompt_id: str, completed: bool) -> None:
        self.manager.update(prompt_id, completed=completed)
        if completed:
            self.manager.update(prompt_id, starred=False)

    def on_move_up(self, prompt_id: str) -> None:
        if self.manager.move_up(prompt_id):
            self.load_prompts()

    def on_move_down(self, prompt_id: str) -> None:
        if self.manager.move_down(prompt_id):
            self.load_prompts()

    def update_counter(self) -> None:
        self.counter_label.setText(f"{len(self.manager.get_all())} prompts")

    def close_panel(self) -> None:
        self.hide()
        self.closed.emit()

    def get_resize_edge(self, pos: QPoint):
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

        return edge or None

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
