#!/usr/bin/env python3
"""Floating bar UI wired to the real backend session orchestrator."""

from __future__ import annotations

import sys

from backend.contracts import AssistProviderKind, AudioSource, SessionMode, SttProviderKind
from backend.session.orchestrator import SessionOrchestrator
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QRect,
    QRectF,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


C_CARD_BG = QColor(18, 18, 20)
C_PILL_BG = QColor(28, 28, 31)
C_BORDER = QColor(255, 255, 255, 18)
C_ICON = QColor(235, 235, 245, 200)
C_ICON_DIM = QColor(235, 235, 245, 110)
C_WHITE = QColor(255, 255, 255, 245)
C_ACCENT = QColor(10, 132, 255)
C_SEP = QColor(255, 255, 255, 11)
C_INPUT_BG = QColor(255, 255, 255, 7)
C_INPUT_BD = QColor(255, 255, 255, 16)
C_BADGE_BG = QColor(255, 255, 255, 14)
C_BADGE_BD = QColor(255, 255, 255, 26)
SHM = 22


def _best_family():
    for name in (
        "Inter",
        "SF Pro Text",
        ".SF NS Text",
        "Helvetica Neue",
        "Segoe UI Variable",
        "Segoe UI",
    ):
        if QFont(name).exactMatch():
            return name
    return "Segoe UI"


_FAM = None


def F(px, weight=QFont.Weight.DemiBold, tracking=-0.07):
    global _FAM
    if _FAM is None:
        _FAM = _best_family()
    font = QFont(_FAM)
    font.setPixelSize(max(1, int(px)))
    font.setWeight(weight)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
    )
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px * tracking)
    return font


def _format_elapsed(ms):
    total_seconds = max(0, int(ms) // 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _mode_text(mode):
    return {
        SessionMode.IDLE: "Idle",
        SessionMode.LISTENING: "Listening",
        SessionMode.PAUSED: "Paused",
        SessionMode.TRANSCRIBING: "Transcribing",
        SessionMode.ANALYZING: "Analyzing screen",
        SessionMode.GENERATING: "Generating",
        SessionMode.ERROR: "Error",
        SessionMode.STOPPED: "Stopped",
    }.get(mode, str(mode).title())


def _mode_color(mode):
    return {
        SessionMode.LISTENING: QColor(102, 212, 125),
        SessionMode.PAUSED: QColor(255, 196, 77),
        SessionMode.TRANSCRIBING: QColor(90, 175, 255),
        SessionMode.ANALYZING: QColor(120, 185, 255),
        SessionMode.GENERATING: QColor(150, 170, 255),
        SessionMode.ERROR: QColor(255, 107, 107),
        SessionMode.STOPPED: QColor(215, 215, 215),
    }.get(mode, QColor(235, 235, 245, 200))


def _rp(p, col=None, w=1.5):
    pen = QPen(
        col or C_ICON,
        w,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)


def ic_eye(p, cx, cy):
    p.save()
    _rp(p, w=1.5)
    rx, ry = 5.5, 3.4
    path = QPainterPath()
    path.moveTo(cx - rx, cy)
    path.cubicTo(cx - rx * 0.5, cy - ry, cx + rx * 0.5, cy - ry, cx + rx, cy)
    path.cubicTo(cx + rx * 0.5, cy + ry, cx - rx * 0.5, cy + ry, cx - rx, cy)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))
    p.drawEllipse(QRectF(cx - 2.0, cy - 2.0, 4.0, 4.0))
    p.restore()


def ic_spy(p, cx, cy):
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))
    crown = QPainterPath()
    crown.moveTo(cx - 4.2, cy + 1.0)
    crown.lineTo(cx - 4.2, cy - 0.8)
    crown.cubicTo(cx - 4.2, cy - 6.0, cx + 4.2, cy - 6.0, cx + 4.2, cy - 0.8)
    crown.lineTo(cx + 4.2, cy + 1.0)
    crown.closeSubpath()
    p.drawPath(crown)
    p.drawRoundedRect(QRectF(cx - 6.5, cy + 1.0, 13.0, 3.0), 1.5, 1.5)
    p.restore()


def ic_pause(p, cx, cy):
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))
    p.drawRoundedRect(QRectF(cx - 4.8, cy - 5.0, 3.4, 10.0), 1.6, 1.6)
    p.drawRoundedRect(QRectF(cx + 1.4, cy - 5.0, 3.4, 10.0), 1.6, 1.6)
    p.restore()


def ic_stop(p, cx, cy):
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))
    p.drawRoundedRect(QRectF(cx - 4.6, cy - 4.6, 9.2, 9.2), 2.2, 2.2)
    p.restore()


def ic_chevup(p, cx, cy):
    p.save()
    _rp(p, w=1.8)
    p.drawPolyline(
        [QPointF(cx - 4.5, cy + 2.5), QPointF(cx, cy - 2.8), QPointF(cx + 4.5, cy + 2.5)]
    )
    p.restore()


def ic_grid(p, cx, cy):
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))
    gap, radius = 4.2, 1.1
    for row in range(3):
        for col in range(2):
            p.drawEllipse(
                QRectF(
                    cx - gap / 2 + col * gap - radius,
                    cy - gap + row * gap - radius,
                    radius * 2,
                    radius * 2,
                )
            )
    p.restore()


def ic_gear(p, cx, cy):
    p.save()
    _rp(p, w=1.5)
    p.drawEllipse(QRectF(cx - 4.2, cy - 4.2, 8.4, 8.4))
    p.drawEllipse(QRectF(cx - 1.2, cy - 1.2, 2.4, 2.4))
    for dx, dy in (
        (0.0, -5.8),
        (4.1, -4.1),
        (5.8, 0.0),
        (4.1, 4.1),
        (0.0, 5.8),
        (-4.1, 4.1),
        (-5.8, 0.0),
        (-4.1, -4.1),
    ):
        p.drawLine(QPointF(cx + dx * 0.62, cy + dy * 0.62), QPointF(cx + dx, cy + dy))
    p.restore()


def ic_close(p, cx, cy):
    p.save()
    _rp(p, w=1.6)
    delta = 4.2
    p.drawLine(QPointF(cx - delta, cy - delta), QPointF(cx + delta, cy + delta))
    p.drawLine(QPointF(cx + delta, cy - delta), QPointF(cx - delta, cy + delta))
    p.restore()


def ic_home(p, cx, cy):
    p.save()
    _rp(p, col=C_ICON_DIM, w=1.5)
    p.drawPolyline(
        [QPointF(cx - 5.2, cy + 0.8), QPointF(cx, cy - 5.0), QPointF(cx + 5.2, cy + 0.8)]
    )
    walls = QPainterPath()
    walls.moveTo(cx - 3.6, cy + 0.8)
    walls.lineTo(cx - 3.6, cy + 5.5)
    walls.lineTo(cx + 3.6, cy + 5.5)
    walls.lineTo(cx + 3.6, cy + 0.8)
    p.drawPath(walls)
    p.restore()


def ic_expand(p, cx, cy):
    p.save()
    _rp(p, col=QColor(235, 235, 245, 135), w=1.5)
    delta, tip = 3.8, 2.4
    tx, ty = cx + delta, cy - delta
    p.drawLine(QPointF(cx - .4, cy + .4), QPointF(tx, ty))
    p.drawPolyline([QPointF(tx - tip, ty), QPointF(tx, ty), QPointF(tx, ty + tip)])
    bx, by = cx - delta, cy + delta
    p.drawLine(QPointF(cx + .4, cy - .4), QPointF(bx, by))
    p.drawPolyline([QPointF(bx + tip, by), QPointF(bx, by), QPointF(bx, by - tip)])
    p.restore()


class _Hover(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hv = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._an = QPropertyAnimation(self, b"_hp")
        self._an.setDuration(160)
        self._an.setEasingCurve(QEasingCurve.Type.OutCubic)

    @Property(float)
    def _hp(self):
        return self._hv

    @_hp.setter
    def _hp(self, value):
        self._hv = value
        self.update()

    def enterEvent(self, _):
        self._an.stop()
        self._an.setStartValue(self._hv)
        self._an.setEndValue(1.0)
        self._an.start()

    def leaveEvent(self, _):
        self._an.stop()
        self._an.setStartValue(self._hv)
        self._an.setEndValue(0.0)
        self._an.start()


class IconBtn(_Hover):
    def __init__(self, draw_fn, sz=28, cb=None, parent=None):
        super().__init__(parent)
        self._draw = draw_fn
        self._cb = cb
        self._active = False
        self.setFixedSize(sz, sz)

    def setActive(self, value):
        self._active = value
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._cb:
            self._cb()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(C_ACCENT.red(), C_ACCENT.green(), C_ACCENT.blue(), 34)))
            p.drawEllipse(QRectF(2, 2, w - 4, h - 4))
        if self._hv > .005:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, int(18 * self._hv))))
            p.drawEllipse(QRectF(3, 3, w - 6, h - 6))
        self._draw(p, w / 2, h / 2)
        p.end()


class SendBtn(_Hover):
    def __init__(self, cb=None, parent=None):
        super().__init__(parent)
        self._cb = cb
        self.setFixedSize(32, 32)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._cb:
            self._cb()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        grad = QRadialGradient(cx - 2, cy - 3, w * .65)
        boost = int(255 * self._hv * .18)
        grad.setColorAt(
            0.0,
            QColor(min(255, C_ACCENT.red() + 55 + boost), min(255, C_ACCENT.green() + 20 + boost), 255),
        )
        grad.setColorAt(
            1.0,
            QColor(max(0, C_ACCENT.red() - 18), max(0, C_ACCENT.green() - 8), min(255, C_ACCENT.blue() - 12)),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(0, 0, w, h))
        sheen = QLinearGradient(0, 0, 0, h / 2)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 52))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        clip = QPainterPath()
        clip.addEllipse(QRectF(0, 0, w, h))
        p.setClipPath(clip)
        p.setBrush(QBrush(sheen))
        p.drawRect(QRectF(0, 0, w, h / 2))
        p.setClipping(False)
        pen = QPen(
            QColor(255, 255, 255, 240),
            2.0,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        p.setPen(pen)
        p.drawLine(QPointF(cx - 5.5, cy), QPointF(cx + 3.5, cy))
        p.drawPolyline([QPointF(cx + .5, cy - 3.5), QPointF(cx + 4.5, cy), QPointF(cx + .5, cy + 3.5)])
        p.end()


class TabBtn(_Hover):
    def __init__(self, label, active=False, cb=None, parent=None):
        super().__init__(parent)
        self.label = label
        self.active = active
        self._cb = cb
        self._font = F(13.0)
        fm = QFontMetrics(self._font)
        self.setFixedHeight(28)
        self.setFixedWidth(fm.horizontalAdvance(label) + 4)

    def setActive(self, value):
        self.active = value
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._cb:
            self._cb()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        color = C_WHITE if self.active else QColor(235, 235, 245, int(78 + 68 * self._hv))
        p.setPen(QPen(color))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, self.label)
        p.end()


class SlashSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._font = F(13.0, QFont.Weight.Normal, tracking=0)
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance("  /  ") + 2, 28)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235, 235, 245, 38)))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, "/")
        p.end()


class DotSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(14, 24)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(235, 235, 245, 45)))
        p.drawEllipse(QRectF(5, 10, 3.5, 3.5))
        p.end()


class PillVSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(1, 14)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(0, 0, 1, 14, QColor(255, 255, 255, 22))
        p.end()


class HSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(1)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), 1, C_SEP)
        p.end()


class Chip(_Hover):
    def __init__(self, text, accent=False, cb=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.accent = accent
        self._cb = cb
        weight = QFont.Weight.Normal if accent else QFont.Weight.Light
        self._font = F(12.0, weight, tracking=0)
        fm = QFontMetrics(self._font)
        self.setFixedHeight(24)
        self.setFixedWidth(fm.horizontalAdvance(text) + (16 if accent else 2))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._cb:
            self._cb()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        if self.accent:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(C_ACCENT.red(), C_ACCENT.green(), C_ACCENT.blue(), int(18 + 12 * self._hv))))
            p.drawRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
            text_color = QColor(88, 172, 255, 228)
        else:
            if self._hv > .01:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, int(8 * self._hv))))
                p.drawRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
            text_color = QColor(235, 235, 245, int(148 + 52 * self._hv))
        p.setPen(QPen(text_color))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.text)
        p.end()


class BottomChip(_Hover):
    _PX = 12
    _IPX = 10

    def __init__(self, label, variant="smart", cb=None, parent=None):
        super().__init__(parent)
        self.label = label
        self.variant = variant
        self._cb = cb
        self._active = False
        self._font = F(11.5, QFont.Weight.Normal, tracking=0)
        fm = QFontMetrics(self._font)
        text_width = fm.horizontalAdvance(label)
        if variant == "screen":
            width = self._PX + self._IPX + 5 + text_width + self._PX
        elif variant == "general":
            width = self._PX + text_width + 18 + self._PX
        else:
            width = self._PX + text_width + self._PX
        self.setFixedHeight(27)
        self.setFixedWidth(int(width))

    def setActive(self, value):
        self._active = value
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._cb:
            self._cb()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        radius = h / 2
        cy = h / 2
        if self.variant == "screen":
            p.setPen(QPen(QColor(C_ACCENT.red(), C_ACCENT.green(), 255, 48), .85))
            p.setBrush(QBrush(QColor(C_ACCENT.red(), C_ACCENT.green(), C_ACCENT.blue(), int((42 if self._active else 30) + 20 * self._hv))))
            text_color = QColor(90, 175, 255, 240)
        else:
            border_alpha = int(26 + 14 * self._hv)
            background_alpha = int((18 if self._active else 8) + 16 * self._hv)
            p.setPen(QPen(QColor(255, 255, 255, border_alpha), .85))
            p.setBrush(QBrush(QColor(255, 255, 255, background_alpha)))
            text_color = QColor(235, 235, 245, int(160 + 55 * self._hv))
        p.drawRoundedRect(QRectF(.5, .5, w - 1, h - 1), radius, radius)
        if self.variant == "screen":
            ix = self._PX + self._IPX / 2 + 1
            monitor_color = QColor(90, 175, 255, 200)
            p.setPen(QPen(monitor_color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(ix - 4.5, cy - 3.5, 9, 6.5), 1.2, 1.2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(monitor_color))
            p.drawRoundedRect(QRectF(ix - 1.0, cy + 3.0, 2.0, 1.6), .5, .5)
            text_x = int(self._PX + self._IPX + 5)
        else:
            text_x = self._PX
        chevron_width = 16 if self.variant == "general" else 0
        text_width = w - text_x - self._PX - chevron_width
        p.setPen(QPen(text_color))
        p.setFont(self._font)
        p.drawText(QRect(int(text_x), 0, int(text_width), h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.label)
        if self.variant == "general":
            cx_chev = w - self._PX - 2
            p.setPen(QPen(QColor(235, 235, 245, int(100 + 80 * self._hv)), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline([QPointF(cx_chev - 3.0, cy - 1.2), QPointF(cx_chev, cy + 1.8), QPointF(cx_chev + 3.0, cy - 1.2)])
        p.end()


class KeyBadge(QWidget):
    def __init__(self, glyph, parent=None):
        super().__init__(parent)
        self.glyph = glyph
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._font = F(9.5, QFont.Weight.Medium, tracking=0)
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance(glyph) + 10, 17)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(C_BADGE_BD, .7))
        p.setBrush(QBrush(C_BADGE_BG))
        p.drawRoundedRect(QRectF(.5, .5, w - 1, h - 1), 3.5, 3.5)
        p.setPen(QPen(QColor(235, 235, 245, 130)))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.glyph)
        p.end()


class _Dim(QWidget):
    def __init__(self, text, alpha=62, px=10.5, parent=None):
        super().__init__(parent)
        self.text = text
        self._alpha = alpha
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._font = F(px, QFont.Weight.Normal, tracking=-0.02)
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance(text) + 2, 20)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235, 235, 245, self._alpha)))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, self.text)
        p.end()


class BrandLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._font = F(17.0, QFont.Weight.DemiBold, tracking=-0.07)
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance("Opencluely") + 4, 34)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235, 235, 245, 172)))
        p.setFont(self._font)
        p.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, "Opencluely")
        p.end()


class ContentPane(QPlainTextEdit):
    def __init__(self, placeholder, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameStyle(0)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.document().setDocumentMargin(8)
        self.setPlaceholderText(placeholder)
        self.setFont(F(12.0, QFont.Weight.Normal, tracking=0))
        self.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 16);
                border-radius: 14px;
                padding: 8px;
                color: rgba(235, 235, 245, 215);
                selection-background-color: rgba(10, 132, 255, 90);
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 8px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 28);
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                height: 0px;
            }
        """)

    def set_text(self, text):
        self.setPlainText(text)
        scroll = self.verticalScrollBar()
        scroll.setValue(scroll.maximum())


class InputRow(QWidget):
    def __init__(self, on_submit, parent=None):
        super().__init__(parent)
        self._on_submit = on_submit
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(42)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(0)
        self.field = QLineEdit()
        self.field.setFont(F(12.5, QFont.Weight.Normal, tracking=-0.03))
        self.field.setPlaceholderText("Ask about your screen or conversation")
        self.field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: rgba(235, 235, 245, 195);
                selection-background-color: rgba(10, 132, 255, 100);
            }
        """)
        self.field.returnPressed.connect(self.submit)
        lay.addWidget(self.field, 1)
        lay.addSpacing(6)
        lay.addWidget(_Dim("or", alpha=55, px=10.5))
        lay.addSpacing(5)
        lay.addWidget(KeyBadge("^"))
        lay.addSpacing(3)
        lay.addWidget(KeyBadge("↵"))
        lay.addSpacing(4)
        lay.addWidget(_Dim("for Assist", alpha=55, px=10.5))
        lay.addSpacing(8)
        lay.addWidget(SendBtn(cb=self.submit))

    def submit(self):
        text = self.field.text().strip()
        if not text:
            return
        self._on_submit(text)
        self.field.clear()

    def focus_input(self):
        self.field.setFocus(Qt.FocusReason.OtherFocusReason)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(C_INPUT_BD, .8))
        p.setBrush(QBrush(C_INPUT_BG))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 21, 21)
        p.end()


class TopPill(QWidget):
    def __init__(self, on_action, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(40)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 5, 8, 5)
        lay.setSpacing(0)

        def icon(name, fn, tip):
            b = IconBtn(fn, sz=28, cb=lambda action=name: on_action(action))
            b.setToolTip(tip)
            lay.addWidget(b)
            self._buttons[name] = b

        def sep():
            lay.addSpacing(4)
            lay.addWidget(PillVSep())
            lay.addSpacing(4)

        icon("view_screen", ic_eye, "View screen")
        icon("incognito", ic_spy, "Incognito")
        sep()
        icon("pause", ic_pause, "Pause or resume")
        icon("stop", ic_stop, "Stop session")
        sep()
        icon("collapse", ic_chevup, "Collapse")
        sep()
        icon("options", ic_gear, "Options")
        icon("close", ic_close, "Close")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_button_active(self, name, value):
        button = self._buttons.get(name)
        if button:
            button.setActive(value)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        p.setPen(QPen(C_BORDER, 1.0))
        p.setBrush(QBrush(C_PILL_BG))
        p.drawRoundedRect(QRectF(0, 0, self.width(), h), h / 2, h / 2)
        p.end()


class MainCard(QWidget):
    def __init__(
        self,
        on_submit,
        on_home,
        on_capture_screen,
        on_quick_prompt,
        on_toggle_screen,
        on_response_mode,
        on_tab_change=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)
        self._on_tab_change = on_tab_change
        self._active_tab = 0
        self._chat_history = []
        self._transcript_segments = []
        self._partial_transcript = ""
        self._notes_text = ""
        self._screen_summary = ""
        self._provider_text = "STT: Auto | Chat: Auto"
        self._detail_text = "Smart"
        self._error_message = ""
        self._mode = SessionMode.IDLE

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 13)
        lay.setSpacing(0)

        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        tab_row.setContentsMargins(0, 0, 0, 0)
        tab_row.addWidget(IconBtn(ic_home, sz=22, cb=on_home))
        tab_row.addSpacing(4)
        tab_row.addStretch()
        self._tab_chat = TabBtn("Chat", active=True, cb=lambda: self._switch_tab(0))
        self._tab_transcript = TabBtn("Transcript", active=False, cb=lambda: self._switch_tab(1))
        self._tab_notes = TabBtn("Notes", active=False, cb=lambda: self._switch_tab(2))
        tab_row.addWidget(self._tab_chat)
        tab_row.addWidget(SlashSep())
        tab_row.addWidget(self._tab_transcript)
        tab_row.addWidget(SlashSep())
        tab_row.addWidget(self._tab_notes)
        tab_row.addStretch()
        tab_row.addSpacing(4)
        capture_icon = IconBtn(ic_expand, sz=22, cb=on_capture_screen)
        capture_icon.setToolTip("Capture screen now")
        tab_row.addWidget(capture_icon)
        lay.addLayout(tab_row)
        lay.addSpacing(11)
        lay.addWidget(HSep())
        lay.addSpacing(12)

        self._center_stack = QStackedWidget()
        self._center_stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._chat_center = QWidget()
        chat_center_layout = QVBoxLayout(self._chat_center)
        chat_center_layout.setContentsMargins(0, 0, 0, 0)
        chat_center_layout.setSpacing(0)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.addStretch()
        self._brand = BrandLabel()
        brand_row.addWidget(self._brand)
        brand_row.addStretch()
        chat_center_layout.addLayout(brand_row)
        self._chat_reply = QLabel("")
        self._chat_reply.setWordWrap(True)
        self._chat_reply.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chat_reply.setFont(F(12.0, QFont.Weight.Normal, tracking=0))
        self._chat_reply.setStyleSheet("color: rgba(235, 235, 245, 170);")
        self._chat_reply.hide()
        chat_center_layout.addWidget(self._chat_reply)

        self._transcript_center = QWidget()
        transcript_layout = QVBoxLayout(self._transcript_center)
        transcript_layout.setContentsMargins(0, 0, 0, 0)
        transcript_layout.setSpacing(5)
        self._transcript_meta = QLabel("")
        self._transcript_meta.setFont(F(10.5, QFont.Weight.DemiBold, tracking=0))
        self._transcript_meta.setStyleSheet("color: rgba(235, 235, 245, 200);")
        transcript_layout.addWidget(self._transcript_meta)
        self._transcript_detail = QLabel("")
        self._transcript_detail.setWordWrap(True)
        self._transcript_detail.setFont(F(10.2, QFont.Weight.Normal, tracking=0))
        self._transcript_detail.setStyleSheet("color: rgba(235, 235, 245, 128);")
        transcript_layout.addWidget(self._transcript_detail)
        self._transcript_screen = QLabel("")
        self._transcript_screen.setWordWrap(True)
        self._transcript_screen.setFont(F(10.0, QFont.Weight.Normal, tracking=0))
        self._transcript_screen.setStyleSheet("color: rgba(140, 190, 255, 200);")
        self._transcript_screen.hide()
        transcript_layout.addWidget(self._transcript_screen)
        self._transcript_pane = ContentPane("Transcript will appear here once audio starts flowing.")
        self._transcript_pane.setFixedHeight(148)
        transcript_layout.addWidget(self._transcript_pane)

        self._notes_center = QWidget()
        notes_layout = QVBoxLayout(self._notes_center)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(5)
        self._notes_meta = QLabel("")
        self._notes_meta.setFont(F(10.5, QFont.Weight.DemiBold, tracking=0))
        self._notes_meta.setStyleSheet("color: rgba(235, 235, 245, 200);")
        notes_layout.addWidget(self._notes_meta)
        self._notes_detail = QLabel("")
        self._notes_detail.setWordWrap(True)
        self._notes_detail.setFont(F(10.2, QFont.Weight.Normal, tracking=0))
        self._notes_detail.setStyleSheet("color: rgba(235, 235, 245, 128);")
        notes_layout.addWidget(self._notes_detail)
        self._notes_screen = QLabel("")
        self._notes_screen.setWordWrap(True)
        self._notes_screen.setFont(F(10.0, QFont.Weight.Normal, tracking=0))
        self._notes_screen.setStyleSheet("color: rgba(140, 190, 255, 200);")
        self._notes_screen.hide()
        notes_layout.addWidget(self._notes_screen)
        self._notes_pane = ContentPane("Live notes will build as the meeting progresses.")
        self._notes_pane.setFixedHeight(148)
        notes_layout.addWidget(self._notes_pane)

        self._center_stack.addWidget(self._chat_center)
        self._center_stack.addWidget(self._transcript_center)
        self._center_stack.addWidget(self._notes_center)
        lay.addWidget(self._center_stack)
        lay.addSpacing(10)

        self._input = InputRow(on_submit)
        lay.addWidget(self._input)
        lay.addSpacing(10)

        chip_row = QHBoxLayout()
        chip_row.setSpacing(0)
        chip_row.addStretch()
        prompts = [
            ("✦  Assist", "Give me a short practical reply I can say next.", True),
            ("What should I say?", "What should I say next in one short answer?", False),
            ("Follow-up questions", "Give me three short follow-up questions I can ask next.", False),
            ("↺  Recap", "Recap the latest context in short bullets.", False),
        ]
        for index, (label, prompt, accent) in enumerate(prompts):
            if index:
                chip_row.addWidget(DotSep())
            chip_row.addWidget(Chip(label, accent=accent, cb=lambda text=prompt: on_quick_prompt(text)))
        chip_row.addStretch()
        lay.addLayout(chip_row)
        lay.addSpacing(10)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(7)
        bottom_row.addStretch()
        self._screen_chip = BottomChip("Use Screen", variant="screen", cb=on_toggle_screen)
        self._smart_chip = BottomChip("Smart", variant="smart", cb=lambda: on_response_mode("smart"))
        self._general_chip = BottomChip("General", variant="general", cb=lambda: on_response_mode("general"))
        bottom_row.addWidget(self._screen_chip)
        bottom_row.addWidget(self._smart_chip)
        bottom_row.addWidget(self._general_chip)
        bottom_row.addStretch()
        lay.addLayout(bottom_row)
        self._apply_center_state()

    def focus_input(self):
        self._input.focus_input()

    def clear_content(self):
        self.set_chat_history([])
        self.set_transcript([], "")
        self.set_notes("")
        self.set_screen_summary("")

    def set_status(self, mode, provider_text, detail_text, error_message=""):
        self._mode = mode
        self._provider_text = provider_text
        self._detail_text = detail_text
        self._error_message = error_message
        self._refresh_meta()

    def set_session_flags(self, *, screen_enabled, response_mode):
        self._screen_chip.setActive(screen_enabled)
        self._smart_chip.setActive(response_mode == "smart")
        self._general_chip.setActive(response_mode == "general")

    def set_screen_summary(self, summary):
        self._screen_summary = summary.strip()
        self._refresh_meta()

    def set_chat_history(self, turns):
        self._chat_history = list(turns)
        last_turn = self._chat_history[-1] if self._chat_history else None
        if last_turn:
            self._chat_reply.setText(getattr(last_turn, "text", "").strip())
        else:
            self._chat_reply.clear()
        self._refresh_empty_state()
        self._apply_center_state()

    def set_transcript(self, segments, partial_text=""):
        self._transcript_segments = list(segments)
        self._partial_transcript = partial_text.strip()
        lines = []
        for segment in self._transcript_segments:
            stamp = _format_elapsed(getattr(segment, "start_ms", 0))
            source = getattr(getattr(segment, "source", None), "value", "")
            suffix = f" {source}" if source else ""
            lines.append(f"[{stamp}{suffix}] {getattr(segment, 'text', '').strip()}".strip())
        if self._partial_transcript:
            lines.append("")
            lines.append(f"Listening... {self._partial_transcript}")
        self._transcript_pane.set_text("\n".join(lines).strip())
        self._refresh_meta()

    def set_notes(self, text):
        self._notes_text = text.strip()
        self._notes_pane.set_text(self._notes_text)
        self._refresh_meta()

    def set_response_mode(self, mode):
        self._smart_chip.setActive(mode == "smart")
        self._general_chip.setActive(mode == "general")

    def _switch_tab(self, index):
        self._active_tab = index
        self._tab_chat.setActive(index == 0)
        self._tab_transcript.setActive(index == 1)
        self._tab_notes.setActive(index == 2)
        self._apply_center_state()
        if self._on_tab_change:
            self._on_tab_change(index)

    def _apply_center_state(self):
        if self._active_tab == 0:
            self._center_stack.setCurrentIndex(0)
            if self._chat_history:
                self._center_stack.setFixedHeight(min(max(self._chat_reply.sizeHint().height() + 6, 42), 78))
            else:
                self._center_stack.setFixedHeight(38)
        else:
            self._center_stack.setCurrentIndex(self._active_tab)
            self._center_stack.setFixedHeight(210)
        self._request_resize()

    def _refresh_empty_state(self):
        is_empty = not self._chat_history
        self._brand.setVisible(is_empty)
        self._chat_reply.setVisible(not is_empty)

    def _refresh_meta(self):
        meta_text = self._error_message or f"{_mode_text(self._mode)} · {self._provider_text}"
        detail_text = self._detail_text
        detail_style = "color: rgba(255, 107, 107, 220);" if self._error_message else "color: rgba(235, 235, 245, 128);"
        for meta_label in (self._transcript_meta, self._notes_meta):
            meta_label.setText(meta_text)
        for detail_label in (self._transcript_detail, self._notes_detail):
            detail_label.setText(detail_text)
            detail_label.setStyleSheet(detail_style)
        for screen_label in (self._transcript_screen, self._notes_screen):
            if self._screen_summary:
                screen_label.setText(f"Screen: {self._screen_summary}")
                screen_label.show()
            else:
                screen_label.clear()
                screen_label.hide()

    def _request_resize(self):
        window = self.window()
        if window is not None:
            window.adjustSize()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(C_BORDER, 1.0))
        p.setBrush(QBrush(C_CARD_BG))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
        p.end()


class FloatingBar(QWidget):
    def __init__(self, session_context=None, autostart=True):
        super().__init__()
        self._session_context = session_context or {}
        self._autostart = autostart
        self._drag_offset = None
        self._collapsed = False
        self._response_mode = "smart"
        self._screen_enabled = False
        self._last_status_message = ""
        self._provider_health = {}
        self._orchestrator = SessionOrchestrator(session_context=self._session_context)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        root = QVBoxLayout(self)
        root.setContentsMargins(SHM, SHM, SHM, SHM)
        root.setSpacing(8)

        pill_row = QHBoxLayout()
        pill_row.setContentsMargins(0, 0, 0, 0)
        pill_row.addStretch()
        self._top_pill = TopPill(self._handle_top_action)
        pill_row.addWidget(self._top_pill)
        pill_row.addStretch()
        root.addLayout(pill_row)

        self._card = MainCard(
            on_submit=self._submit_prompt,
            on_home=self._clear_session,
            on_capture_screen=self._capture_screen_now,
            on_quick_prompt=self._submit_prompt,
            on_toggle_screen=self._toggle_screen_awareness,
            on_response_mode=self._set_response_mode,
            on_tab_change=self._handle_tab_change,
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(52)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 14)
        self._card.setGraphicsEffect(shadow)

        self._card_row = QHBoxLayout()
        self._card_row.setContentsMargins(0, 0, 0, 0)
        self._card_row.addStretch()
        self._card_row.addWidget(self._card)
        self._card_row.addStretch()
        root.addLayout(self._card_row)
        self.adjustSize()

        self._connect_orchestrator()
        self._refresh_status()
        if self._autostart:
            QTimer.singleShot(180, self._start_session)

    def _connect_orchestrator(self):
        self._orchestrator.state_changed.connect(self._on_state_changed)
        self._orchestrator.transcript_changed.connect(self._on_transcript_changed)
        self._orchestrator.partial_transcript_changed.connect(self._on_partial_transcript_changed)
        self._orchestrator.notes_changed.connect(self._on_notes_changed)
        self._orchestrator.chat_turn_added.connect(self._on_chat_turn_added)
        self._orchestrator.screen_context_changed.connect(self._on_screen_context_changed)
        self._orchestrator.provider_health_changed.connect(self._on_provider_health_changed)
        self._orchestrator.status_message.connect(self._on_status_message)
        self._orchestrator.error_occurred.connect(self._on_error)

    def _handle_top_action(self, action):
        handlers = {
            "view_screen": self._toggle_screen_awareness,
            "incognito": self._toggle_incognito,
            "pause": self._toggle_pause,
            "stop": self._stop_session,
            "collapse": self._toggle_collapse,
            "options": self._show_options_menu,
            "close": self.close,
        }
        handler = handlers.get(action)
        if handler:
            handler()

    def _start_session(self):
        self._orchestrator.start_session()
        self._card.focus_input()

    def _stop_session(self):
        self._orchestrator.stop_session()
        self._refresh_status()

    def _toggle_pause(self):
        mode = self._orchestrator.state.mode
        if mode in {
            SessionMode.LISTENING,
            SessionMode.TRANSCRIBING,
            SessionMode.ANALYZING,
            SessionMode.GENERATING,
        }:
            self._orchestrator.pause_session()
        else:
            self._start_session()

    def _toggle_screen_awareness(self):
        self._screen_enabled = self._orchestrator.toggle_screen_awareness()
        self._refresh_status()

    def _capture_screen_now(self):
        self._orchestrator.capture_screen_context()

    def _toggle_incognito(self):
        self._orchestrator.toggle_incognito()
        self._refresh_status()

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._card.setVisible(not self._collapsed)
        self.adjustSize()

    def _set_response_mode(self, mode):
        self._response_mode = mode
        self._card.set_response_mode(mode)
        self._refresh_status()

    def _handle_tab_change(self, _index):
        self.adjustSize()

    def _clear_session(self):
        self._orchestrator.clear_session()
        self._card.clear_content()
        self._refresh_status()

    def _submit_prompt(self, text):
        prompt = text.strip()
        if not prompt:
            return
        if self._response_mode == "general":
            prompt = (
                "Answer briefly and prefer a general reply. "
                "Only rely on meeting or screen context if it is directly necessary.\n\n"
                f"User request: {prompt}"
            )
        self._orchestrator.submit_prompt(prompt)

    def _build_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgb(24, 24, 27);
                border: 1px solid rgba(255, 255, 255, 22);
                color: rgba(235, 235, 245, 220);
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 8px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background: rgba(10, 132, 255, 40);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 18);
                margin: 6px 8px;
            }
        """)

        stt_menu = menu.addMenu("Transcription provider")
        stt_group = QActionGroup(stt_menu)
        stt_group.setExclusive(True)
        for provider, label in (
            (SttProviderKind.AUTO, "Auto"),
            (SttProviderKind.GROQ, "Groq Whisper Turbo"),
            (SttProviderKind.GEMINI, "Gemini Live"),
        ):
            action = QAction(label, stt_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.desired_stt_provider == provider)
            action.triggered.connect(lambda checked=False, value=provider: self._orchestrator.set_stt_provider(value))
            stt_group.addAction(action)
            stt_menu.addAction(action)

        assist_menu = menu.addMenu("Assistant provider")
        assist_group = QActionGroup(assist_menu)
        assist_group.setExclusive(True)
        for provider, label in (
            (AssistProviderKind.AUTO, "Auto"),
            (AssistProviderKind.GEMINI, "Gemini"),
            (AssistProviderKind.GROQ, "Groq"),
        ):
            action = QAction(label, assist_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.desired_assist_provider == provider)
            action.triggered.connect(
                lambda checked=False, value=provider: self._orchestrator.set_assist_provider(value)
            )
            assist_group.addAction(action)
            assist_menu.addAction(action)

        groq_model_menu = menu.addMenu("Groq model")
        groq_group = QActionGroup(groq_model_menu)
        groq_group.setExclusive(True)
        for model in ("whisper-large-v3-turbo", "whisper-large-v3"):
            action = QAction(model, groq_model_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.current_groq_audio_model == model)
            action.triggered.connect(lambda checked=False, value=model: self._orchestrator.set_groq_audio_model(value))
            groq_group.addAction(action)
            groq_model_menu.addAction(action)

        gemini_model_menu = menu.addMenu("Gemini Live model")
        gemini_group = QActionGroup(gemini_model_menu)
        gemini_group.setExclusive(True)
        for model in (
            "gemini-2.5-flash-native-audio-preview-12-2025",
            "gemini-2.5-flash-native-audio-preview-09-2025",
        ):
            action = QAction(model, gemini_model_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.current_gemini_live_model == model)
            action.triggered.connect(lambda checked=False, value=model: self._orchestrator.set_gemini_live_model(value))
            gemini_group.addAction(action)
            gemini_model_menu.addAction(action)

        gemini_chat_model_menu = menu.addMenu("Gemini chat model")
        gemini_chat_group = QActionGroup(gemini_chat_model_menu)
        gemini_chat_group.setExclusive(True)
        for model in (
            "gemini-3.1-flash-lite-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
        ):
            action = QAction(model, gemini_chat_model_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.current_gemini_assist_model == model)
            action.triggered.connect(
                lambda checked=False, value=model: self._orchestrator.set_gemini_assist_model(value)
            )
            gemini_chat_group.addAction(action)
            gemini_chat_model_menu.addAction(action)

        audio_menu = menu.addMenu("Audio source")
        audio_group = QActionGroup(audio_menu)
        audio_group.setExclusive(True)
        for source, label in (
            (AudioSource.AUTO, "Auto"),
            (AudioSource.MICROPHONE, "Microphone"),
            (AudioSource.LOOPBACK, "Loopback"),
            (AudioSource.MIXED, "Mixed"),
        ):
            action = QAction(label, audio_menu)
            action.setCheckable(True)
            action.setChecked(self._orchestrator.requested_audio_source == source)
            action.triggered.connect(lambda checked=False, value=source: self._orchestrator.set_audio_source(value))
            audio_group.addAction(action)
            audio_menu.addAction(action)

        menu.addSeparator()
        groq_health = self._orchestrator.state.provider_health.get("groq_stt")
        gemini_health = self._orchestrator.state.provider_health.get("gemini_stt")
        gemini_assist_health = self._orchestrator.state.provider_health.get("gemini_assist")
        for text in (
            "Groq key detected" if self._orchestrator._settings.has_groq_key else "Groq key missing",
            (
                "Gemini Live key detected"
                if self._orchestrator._settings.has_gemini_live_key
                else "Gemini Live key missing"
            ),
            (
                "Gemini Chat key detected"
                if self._orchestrator._settings.has_gemini_assist_key
                else "Gemini Chat key missing"
            ),
            "Groq STT ready" if groq_health and groq_health.available else "Groq STT unavailable",
            "Gemini Live ready" if gemini_health and gemini_health.available else "Gemini Live unavailable",
            (
                "Gemini Chat ready"
                if gemini_assist_health and gemini_assist_health.available
                else "Gemini Chat unavailable"
            ),
        ):
            status_action = QAction(text, menu)
            status_action.setEnabled(False)
            menu.addAction(status_action)

        menu.addSeparator()
        capture_action = QAction("Capture screen now", menu)
        capture_action.triggered.connect(self._capture_screen_now)
        menu.addAction(capture_action)
        reset_action = QAction("Reset visible session data", menu)
        reset_action.triggered.connect(self._clear_session)
        menu.addAction(reset_action)
        restart_action = QAction("Restart listening", menu)
        restart_action.triggered.connect(self._start_session)
        menu.addAction(restart_action)
        return menu

    def _show_options_menu(self):
        self._build_menu().popup(QCursor.pos())

    def _on_state_changed(self, state):
        self._card.set_chat_history(state.chat_history)
        self._refresh_status()

    def _on_transcript_changed(self, segments):
        self._card.set_transcript(segments, self._card._partial_transcript)

    def _on_partial_transcript_changed(self, text):
        self._card.set_transcript(self._orchestrator.state.transcript_segments, text)

    def _on_notes_changed(self, text):
        self._card.set_notes(text)

    def _on_chat_turn_added(self, _turn):
        self._card.set_chat_history(self._orchestrator.state.chat_history)

    def _on_screen_context_changed(self, context):
        summary = getattr(context, "summary", "") if context else ""
        self._card.set_screen_summary(summary)
        self._refresh_status()

    def _on_provider_health_changed(self, provider_health):
        self._provider_health = provider_health
        self._refresh_status()

    def _on_status_message(self, message):
        self._last_status_message = message
        self._refresh_status()

    def _on_error(self, message):
        self._last_status_message = message
        self._refresh_status()

    def _refresh_status(self):
        state = self._orchestrator.state
        stt_provider = state.stt_provider
        assist_provider = self._orchestrator.current_assist_provider
        if stt_provider == SttProviderKind.GROQ:
            stt_text = self._orchestrator.current_groq_audio_model.replace("whisper-", "Groq ")
        elif stt_provider == SttProviderKind.GEMINI:
            stt_text = self._orchestrator.current_gemini_live_model.replace(
                "gemini-2.5-flash-native-audio-preview-",
                "Gemini ",
            )
        elif stt_provider == SttProviderKind.LOCAL:
            stt_text = "Local"
        else:
            stt_text = "Auto"
        if assist_provider == AssistProviderKind.GEMINI:
            assist_text = "Gemini"
        elif assist_provider == AssistProviderKind.GROQ:
            assist_text = "Groq"
        elif assist_provider == AssistProviderKind.LOCAL:
            assist_text = "Local"
        else:
            assist_text = "Auto"
        provider_text = f"STT: {stt_text} | Chat: {assist_text}"
        detail_parts = [self._response_mode.title()]
        detail_parts.append(f"Audio {state.audio_source.value.replace('_', ' ')}")
        if assist_provider == AssistProviderKind.GEMINI:
            detail_parts.append(self._orchestrator.current_gemini_assist_model)
        if self._screen_enabled:
            detail_parts.append("Screen-aware")
        if state.is_incognito:
            detail_parts.append("Incognito")
        if state.mode == SessionMode.STOPPED:
            detail_parts.append("Session stopped")
        elif state.mode == SessionMode.PAUSED:
            detail_parts.append("Capture paused")
        if self._last_status_message and self._last_status_message.lower() not in {"listening", "paused", "connecting", "ready", "stopped"}:
            detail_parts.append(self._last_status_message)
        self._card.set_status(
            state.mode,
            provider_text,
            " | ".join(detail_parts),
            error_message=state.error_message if state.mode == SessionMode.ERROR else "",
        )
        self._card.set_session_flags(
            screen_enabled=self._screen_enabled,
            response_mode=self._response_mode,
        )
        self._top_pill.set_button_active("view_screen", self._screen_enabled)
        self._top_pill.set_button_active("incognito", state.is_incognito)
        self._top_pill.set_button_active("pause", state.mode == SessionMode.PAUSED)
        self._top_pill.set_button_active("stop", state.mode == SessionMode.STOPPED)
        self._top_pill.set_button_active("collapse", self._collapsed)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _):
        self._drag_offset = None

    def closeEvent(self, event):
        try:
            self._orchestrator.close_session()
        finally:
            super().closeEvent(event)


def main():
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    bar = FloatingBar(
        {
            "profile_name": "Before Meeting",
            "brief_name": "General",
            "system_instructions": "",
            "user_context": "",
            "language": "pt-BR",
        }
    )
    screen = app.primaryScreen().availableGeometry()
    bar.move((screen.width() - bar.width()) // 2, 80)
    bar.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
