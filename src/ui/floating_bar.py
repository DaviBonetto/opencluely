#!/usr/bin/env python3
"""
AI Assistant Floating Bar  —  v4  —  macOS-style, pixel-perfect
Font: Inter SemiBold  letter-spacing: -0.07em
Install: pip install PySide6
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QGraphicsDropShadowEffect, QSizePolicy,
)
from PySide6.QtCore import (
    Qt, QRect, QRectF, QPointF,
    QPropertyAnimation, QEasingCurve, Property,
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush,
    QFont, QFontMetrics, QLinearGradient, QRadialGradient,
)

C_CARD_BG  = QColor(18, 18, 20)
C_PILL_BG  = QColor(28, 28, 31)
C_BORDER   = QColor(255, 255, 255, 18)
C_ICON     = QColor(235, 235, 245, 200)
C_ICON_DIM = QColor(235, 235, 245, 110)
C_WHITE    = QColor(255, 255, 255, 245)
C_ACCENT   = QColor(10, 132, 255)
C_SEP      = QColor(255, 255, 255, 11)
C_INPUT_BG = QColor(255, 255, 255,  7)
C_INPUT_BD = QColor(255, 255, 255, 16)
C_BADGE_BG = QColor(255, 255, 255, 14)
C_BADGE_BD = QColor(255, 255, 255, 26)
SHM        = 22

def _best_family():
    for name in ("Inter","SF Pro Text",".SF NS Text","Helvetica Neue","Segoe UI Variable","Segoe UI"):
        if QFont(name).exactMatch():
            return name
    return "Segoe UI"

_FAM = None

def F(px, weight=QFont.Weight.DemiBold, tracking=-0.07):
    global _FAM
    if _FAM is None:
        _FAM = _best_family()
    f = QFont(_FAM)
    f.setPixelSize(max(1, int(px)))
    f.setWeight(weight)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px * tracking)
    return f

def _rp(p, col=None, w=1.5):
    """Round pen — uniform across all icons."""
    pen = QPen(col or C_ICON, w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)

# ── All icons share the same visual bounding box: ±5px from (cx,cy) ──────────

def ic_eye(p, cx, cy):
    """Almond eye — clean symmetric arcs + filled iris."""
    p.save(); _rp(p, w=1.5)
    rx, ry = 5.5, 3.4
    path = QPainterPath()
    path.moveTo(cx-rx, cy)
    path.cubicTo(cx-rx*.5, cy-ry, cx+rx*.5, cy-ry, cx+rx, cy)
    path.cubicTo(cx+rx*.5, cy+ry, cx-rx*.5, cy+ry, cx-rx, cy)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_ICON))
    p.drawEllipse(QRectF(cx-2.0, cy-2.0, 4.0, 4.0))
    p.restore()

def ic_spy(p, cx, cy):
    """
    Fedora / spy hat — rendered as a filled silhouette so it cannot
    accidentally look like a bell at small sizes.
    Shape: wide brim (flat rect) + dome crown on top.
    """
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(C_ICON))

    # Crown dome — filled rounded-top trapezoid
    crown = QPainterPath()
    crown.moveTo(cx - 4.2, cy + 1.0)       # bottom-left of crown
    crown.lineTo(cx - 4.2, cy - 0.8)       # left wall up
    crown.cubicTo(cx - 4.2, cy - 6.0,      # left control
                  cx + 4.2, cy - 6.0,      # right control
                  cx + 4.2, cy - 0.8)      # right wall top
    crown.lineTo(cx + 4.2, cy + 1.0)       # bottom-right of crown
    crown.closeSubpath()
    p.drawPath(crown)

    # Brim — wider flat rounded rect below crown
    p.drawRoundedRect(QRectF(cx - 6.5, cy + 1.0, 13.0, 3.0), 1.5, 1.5)
    p.restore()

def ic_pause(p, cx, cy):
    """Two rounded bars, perfectly centered."""
    p.save(); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_ICON))
    p.drawRoundedRect(QRectF(cx-4.8, cy-5.0, 3.4, 10.0), 1.6, 1.6)
    p.drawRoundedRect(QRectF(cx+1.4, cy-5.0, 3.4, 10.0), 1.6, 1.6)
    p.restore()

def ic_stop(p, cx, cy):
    """Rounded square, same visual weight as pause bars."""
    p.save(); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_ICON))
    p.drawRoundedRect(QRectF(cx-4.6, cy-4.6, 9.2, 9.2), 2.2, 2.2)
    p.restore()

def ic_chevup(p, cx, cy):
    """Chevron ^ — same stroke as eye/close."""
    p.save(); _rp(p, w=1.8)
    p.drawPolyline([QPointF(cx-4.5, cy+2.5),
                    QPointF(cx,     cy-2.8),
                    QPointF(cx+4.5, cy+2.5)])
    p.restore()

def ic_grid(p, cx, cy):
    """2 × 3 dot grid — dots same radius as iris."""
    p.save(); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_ICON))
    g, r = 4.2, 1.1
    for row in range(3):
        for col in range(2):
            p.drawEllipse(QRectF(cx - g/2 + col*g - r,
                                  cy - g   + row*g - r, r*2, r*2))
    p.restore()

def ic_close(p, cx, cy):
    """× close — same stroke weight as chevron."""
    p.save(); _rp(p, w=1.6); d = 4.2
    p.drawLine(QPointF(cx-d, cy-d), QPointF(cx+d, cy+d))
    p.drawLine(QPointF(cx+d, cy-d), QPointF(cx-d, cy+d))
    p.restore()

def ic_home(p, cx, cy):
    """Minimal house outline — stroke only, no door."""
    p.save(); _rp(p, col=C_ICON_DIM, w=1.5)
    # Roof
    p.drawPolyline([QPointF(cx-5.2, cy+0.8),
                    QPointF(cx,     cy-5.0),
                    QPointF(cx+5.2, cy+0.8)])
    # Walls — open top (connects to roof ends)
    walls = QPainterPath()
    walls.moveTo(cx-3.6, cy+0.8)
    walls.lineTo(cx-3.6, cy+5.5)
    walls.lineTo(cx+3.6, cy+5.5)
    walls.lineTo(cx+3.6, cy+0.8)
    p.drawPath(walls)
    p.restore()

def ic_expand(p, cx, cy):
    """↗↙ corner arrows — clean arrowheads, dim colour."""
    p.save(); _rp(p, col=QColor(235, 235, 245, 135), w=1.5)
    d, tip = 3.8, 2.4
    # top-right ↗
    tx, ty = cx+d, cy-d
    p.drawLine(QPointF(cx-.4, cy+.4), QPointF(tx, ty))
    p.drawPolyline([QPointF(tx-tip, ty),
                    QPointF(tx, ty),
                    QPointF(tx, ty+tip)])
    # bottom-left ↙
    bx, by_ = cx-d, cy+d
    p.drawLine(QPointF(cx+.4, cy-.4), QPointF(bx, by_))
    p.drawPolyline([QPointF(bx+tip, by_),
                    QPointF(bx, by_),
                    QPointF(bx, by_-tip)])
    p.restore()


class _Hover(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._hv=0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._an = QPropertyAnimation(self, b"_hp")
        self._an.setDuration(160); self._an.setEasingCurve(QEasingCurve.Type.OutCubic)

    @Property(float)
    def _hp(self): return self._hv
    @_hp.setter
    def _hp(self, v): self._hv=v; self.update()

    def enterEvent(self, _): self._an.stop(); self._an.setStartValue(self._hv); self._an.setEndValue(1.0); self._an.start()
    def leaveEvent(self, _): self._an.stop(); self._an.setStartValue(self._hv); self._an.setEndValue(0.0); self._an.start()


class IconBtn(_Hover):
    def __init__(self, draw_fn, sz=28, cb=None, parent=None):
        super().__init__(parent); self._draw=draw_fn; self._cb=cb; self.setFixedSize(sz,sz)
    def mousePressEvent(self, e):
        if e.button()==Qt.MouseButton.LeftButton and self._cb: self._cb()
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        if self._hv>.005:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255,255,255,int(18*self._hv))))
            p.drawEllipse(QRectF(3,3,w-6,h-6))
        self._draw(p,w/2,h/2); p.end()


class SendBtn(_Hover):
    """Blue glass circle — arrow points RIGHT →"""
    def __init__(self, cb=None, parent=None):
        super().__init__(parent); self._cb=cb; self.setFixedSize(32,32)
    def mousePressEvent(self, e):
        if e.button()==Qt.MouseButton.LeftButton and self._cb: self._cb()
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height(); cx,cy=w/2,h/2
        # glass gradient
        grad=QRadialGradient(cx-2, cy-3, w*.65)
        b=int(255*self._hv*.18)
        grad.setColorAt(0.0, QColor(min(255,C_ACCENT.red()+55+b), min(255,C_ACCENT.green()+20+b), 255))
        grad.setColorAt(1.0, QColor(max(0,C_ACCENT.red()-18), max(0,C_ACCENT.green()-8), min(255,C_ACCENT.blue()-12)))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(0,0,w,h))
        # sheen
        sheen=QLinearGradient(0,0,0,h/2)
        sheen.setColorAt(0.0,QColor(255,255,255,52)); sheen.setColorAt(1.0,QColor(255,255,255,0))
        clip=QPainterPath(); clip.addEllipse(QRectF(0,0,w,h))
        p.setClipPath(clip); p.setBrush(QBrush(sheen))
        p.drawRect(QRectF(0,0,w,h/2)); p.setClipping(False)
        # arrow → RIGHT
        pen=QPen(QColor(255,255,255,240), 2.0, Qt.PenStyle.SolidLine,
                 Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(QPointF(cx-5.5, cy), QPointF(cx+3.5, cy))
        p.drawPolyline([QPointF(cx+.5,cy-3.5), QPointF(cx+4.5,cy), QPointF(cx+.5,cy+3.5)])
        p.end()


class TabBtn(_Hover):
    def __init__(self, label, active=False, cb=None, parent=None):
        super().__init__(parent); self.label=label; self.active=active; self._cb=cb
        self._f=F(13.0); fm=QFontMetrics(self._f)
        self.setFixedHeight(28); self.setFixedWidth(fm.horizontalAdvance(label)+4)
    def setActive(self, v): self.active=v; self.update()
    def mousePressEvent(self, e):
        if e.button()==Qt.MouseButton.LeftButton and self._cb: self._cb()
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        col=C_WHITE if self.active else QColor(235,235,245,int(78+68*self._hv))
        p.setPen(QPen(col)); p.setFont(self._f)
        p.drawText(QRect(0,0,self.width(),self.height()), Qt.AlignmentFlag.AlignCenter, self.label); p.end()


class SlashSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._f=F(13.0, QFont.Weight.Normal, tracking=0)
        fm=QFontMetrics(self._f); self.setFixedSize(fm.horizontalAdvance("  /  ")+2, 28)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235,235,245,38))); p.setFont(self._f)
        p.drawText(QRect(0,0,self.width(),self.height()), Qt.AlignmentFlag.AlignCenter, "/"); p.end()


class DotSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(14,24)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(235,235,245,45)))
        p.drawEllipse(QRectF(5,10,3.5,3.5)); p.end()


class PillVSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(1,14)
    def paintEvent(self, _):
        p=QPainter(self); p.fillRect(0,0,1,14,QColor(255,255,255,22)); p.end()


class HSep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedHeight(1)
    def paintEvent(self, _):
        p=QPainter(self); p.fillRect(0,0,self.width(),1,C_SEP); p.end()


class Chip(_Hover):
    def __init__(self, text, accent=False, parent=None):
        super().__init__(parent); self.text=text; self.accent=accent
        # tracking=0 → real Inter feel, not compressed AI-look
        wt = QFont.Weight.Normal if accent else QFont.Weight.Light
        self._f = F(12.0, wt, tracking=0)
        fm = QFontMetrics(self._f)
        self.setFixedHeight(24)
        self.setFixedWidth(fm.horizontalAdvance(text) + (16 if accent else 2))
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        if self.accent:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(C_ACCENT.red(), C_ACCENT.green(), C_ACCENT.blue(), int(18+12*self._hv))))
            p.drawRoundedRect(QRectF(0,0,w,h), h/2, h/2)
            tc = QColor(88, 172, 255, 228)
        else:
            if self._hv > .01:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255,255,255, int(8*self._hv))))
                p.drawRoundedRect(QRectF(0,0,w,h), h/2, h/2)
            tc = QColor(235, 235, 245, int(148+52*self._hv))
        p.setPen(QPen(tc)); p.setFont(self._f)
        p.drawText(QRect(0,0,w,h), Qt.AlignmentFlag.AlignCenter, self.text)
        p.end()


class BottomChip(_Hover):
    """
    Clean pill chip — macOS style.
    variant='screen' : blue tint + tiny monitor icon (drawn cleanly at scale)
    variant='smart'  : plain pill, text only — no icon
    variant='general': plain pill, text + tiny drawn chevron on right
    """
    _PX  = 12      # horizontal padding
    _IPX = 10      # icon area width (screen only)

    def __init__(self, label, variant="smart", parent=None):
        super().__init__(parent)
        self.label   = label
        self.variant = variant
        # Tracking=0, Light weight → reads as real Inter
        self._f = F(11.5, QFont.Weight.Normal, tracking=0)
        fm = QFontMetrics(self._f)
        tw = fm.horizontalAdvance(label)
        if variant == "screen":
            w = self._PX + self._IPX + 5 + tw + self._PX
        elif variant == "general":
            w = self._PX + tw + 18 + self._PX   # room for chevron
        else:
            w = self._PX + tw + self._PX
        self.setFixedHeight(27)
        self.setFixedWidth(int(w))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        cy = h / 2

        # ── Background ──────────────────────────────────
        if self.variant == "screen":
            p.setPen(QPen(QColor(C_ACCENT.red(), C_ACCENT.green(), 255, 48), .85))
            p.setBrush(QBrush(QColor(C_ACCENT.red(), C_ACCENT.green(), C_ACCENT.blue(),
                                      int(30 + 20 * self._hv))))
            tc = QColor(90, 175, 255, 240)
        else:
            bd_a = int(26 + 14 * self._hv)
            bg_a = int(8  + 16 * self._hv)
            p.setPen(QPen(QColor(255, 255, 255, bd_a), .85))
            p.setBrush(QBrush(QColor(255, 255, 255, bg_a)))
            tc = QColor(235, 235, 245, int(160 + 55 * self._hv))

        p.drawRoundedRect(QRectF(.5, .5, w - 1, h - 1), r, r)

        # ── Icon (screen only) ───────────────────────────
        if self.variant == "screen":
            ix = self._PX + self._IPX / 2 + 1
            # Monitor: clean rounded rect + tiny stand
            mc = QColor(90, 175, 255, 200)
            p.setPen(QPen(mc, 1.2, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(ix - 4.5, cy - 3.5, 9, 6.5), 1.2, 1.2)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(mc))
            p.drawRoundedRect(QRectF(ix - 1.0, cy + 3.0, 2.0, 1.6), .5, .5)
            text_x = int(self._PX + self._IPX + 5)
        else:
            text_x = self._PX

        # ── Label ────────────────────────────────────────
        chev_w = 16 if self.variant == "general" else 0
        text_w = w - text_x - self._PX - chev_w
        p.setPen(QPen(tc)); p.setFont(self._f)
        p.drawText(QRect(int(text_x), 0, int(text_w), h),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   self.label)

        # ── Chevron ▾ (general only) — simple 3-point polyline ───
        if self.variant == "general":
            cx_chev = w - self._PX - 2
            p.setPen(QPen(QColor(235, 235, 245, int(100 + 80 * self._hv)),
                          1.4, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline([QPointF(cx_chev - 3.0, cy - 1.2),
                            QPointF(cx_chev,        cy + 1.8),
                            QPointF(cx_chev + 3.0,  cy - 1.2)])

        p.end()


class KeyBadge(QWidget):
    def __init__(self, glyph, parent=None):
        super().__init__(parent); self.glyph=glyph
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._f=F(9.5, QFont.Weight.Medium, tracking=0)
        fm=QFontMetrics(self._f); self.setFixedSize(fm.horizontalAdvance(glyph)+10, 17)
    def paintEvent(self, _):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w,h=self.width(),self.height()
        p.setPen(QPen(C_BADGE_BD,.7)); p.setBrush(QBrush(C_BADGE_BG))
        p.drawRoundedRect(QRectF(.5,.5,w-1,h-1),3.5,3.5)
        p.setPen(QPen(QColor(235,235,245,130))); p.setFont(self._f)
        p.drawText(QRect(0,0,w,h), Qt.AlignmentFlag.AlignCenter, self.glyph); p.end()


class _Dim(QWidget):
    def __init__(self, text, alpha=62, px=10.5, parent=None):
        super().__init__(parent); self.text=text; self._a=alpha
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._f=F(px, QFont.Weight.Normal, tracking=-0.02)
        fm=QFontMetrics(self._f); self.setFixedSize(fm.horizontalAdvance(text)+2, 20)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235,235,245,self._a))); p.setFont(self._f)
        p.drawText(QRect(0,0,self.width(),self.height()), Qt.AlignmentFlag.AlignCenter, self.text); p.end()


class BrandLabel(QWidget):
    """
    Displays 'Opencluely' centered — EMPTY STATE ONLY.
    Hide this widget once the user sends the first message:
        self._brand.hide()
    Show again if the conversation is cleared:
        self._brand.show()
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._f=F(17.0, QFont.Weight.DemiBold, tracking=-0.07)
        fm=QFontMetrics(self._f); self.setFixedSize(fm.horizontalAdvance("Opencluely")+4, 34)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(QPen(QColor(235,235,245,172))); p.setFont(self._f)
        p.drawText(QRect(0,0,self.width(),self.height()), Qt.AlignmentFlag.AlignCenter, "Opencluely"); p.end()


class InputRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedHeight(42)
        lay=QHBoxLayout(self); lay.setContentsMargins(14,0,8,0); lay.setSpacing(0)
        self.field=QLineEdit()
        self.field.setFont(F(12.5, QFont.Weight.Normal, tracking=-0.03))
        self.field.setPlaceholderText("Ask about your screen or conversation")
        self.field.setStyleSheet("""
            QLineEdit { background:transparent; border:none; color:rgba(235,235,245,195);
                        selection-background-color:rgba(10,132,255,100); }
        """)
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
        lay.addWidget(SendBtn())
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(C_INPUT_BD,.8)); p.setBrush(QBrush(C_INPUT_BG))
        p.drawRoundedRect(QRectF(0,0,self.width(),self.height()),21,21); p.end()


class TopPill(QWidget):
    def __init__(self, on_close=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(40)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 5, 8, 5)
        lay.setSpacing(0)

        def icon(fn, tip="", cb=None):
            b = IconBtn(fn, sz=28, cb=cb)
            b.setToolTip(tip)
            lay.addWidget(b)

        def sep():
            lay.addSpacing(4)
            s = PillVSep()
            lay.addWidget(s)
            lay.addSpacing(4)

        # Group 1: eye  spy
        icon(ic_eye,    "View screen")
        icon(ic_spy,    "Incognito")
        sep()
        # Group 2: pause  stop
        icon(ic_pause,  "Pause")
        icon(ic_stop,   "Stop")
        sep()
        # Group 3: chevron up
        icon(ic_chevup, "Collapse")
        sep()
        # Group 4: grid  close
        icon(ic_grid,   "Options")
        icon(ic_close,  "Close", cb=on_close)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        p.setPen(QPen(C_BORDER, 1.0))
        p.setBrush(QBrush(C_PILL_BG))
        p.drawRoundedRect(QRectF(0, 0, self.width(), h), h/2, h/2)
        p.end()


class MainCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 13)
        lay.setSpacing(0)

        # ── Tab row  [home] [stretch] Chat / Transcript / Notes [stretch] [expand] ──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0); tab_row.setContentsMargins(0, 0, 0, 0)

        home = IconBtn(ic_home, sz=22)
        home.setCursor(Qt.CursorShape.ArrowCursor)
        tab_row.addWidget(home)
        tab_row.addSpacing(4)
        tab_row.addStretch()

        self._t_chat  = TabBtn("Chat",       active=True,  cb=lambda: self._sw(0))
        self._t_trans = TabBtn("Transcript", active=False, cb=lambda: self._sw(1))
        self._t_notes = TabBtn("Notes",      active=False, cb=lambda: self._sw(2))
        tab_row.addWidget(self._t_chat)
        tab_row.addWidget(SlashSep())
        tab_row.addWidget(self._t_trans)
        tab_row.addWidget(SlashSep())
        tab_row.addWidget(self._t_notes)

        tab_row.addStretch()
        tab_row.addSpacing(4)
        tab_row.addWidget(IconBtn(ic_expand, sz=22))

        lay.addLayout(tab_row)
        lay.addSpacing(11)
        lay.addWidget(HSep())
        lay.addSpacing(12)

        # ── Brand label — EMPTY STATE ONLY ────────────────────────────────────
        # NOTE: Only visible when no message has been sent.
        # Call self._brand.hide() on first user send.
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.addStretch()
        self._brand = BrandLabel()
        brand_row.addWidget(self._brand)
        brand_row.addStretch()
        lay.addLayout(brand_row)
        lay.addSpacing(10)

        # ── Input bar ─────────────────────────────────────────────────────────
        lay.addWidget(InputRow())
        lay.addSpacing(10)

        # ── Action chips — BELOW input — CENTERED ─────────────────────────────
        chip_row = QHBoxLayout()
        chip_row.setSpacing(0); chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.addStretch()
        for i, (txt, acc) in enumerate([
            ("✦  Assist",           True),
            ("What should I say?",  False),
            ("Follow-up questions", False),
            ("↺  Recap",            False),
        ]):
            if i > 0:
                chip_row.addWidget(DotSep())
            chip_row.addWidget(Chip(txt, accent=acc))
        chip_row.addStretch()
        lay.addLayout(chip_row)
        lay.addSpacing(10)

        # ── Bottom row: centered  Use Screen  Smart  General ──────────────────
        bot = QHBoxLayout()
        bot.setSpacing(7); bot.setContentsMargins(0, 0, 0, 0)
        bot.addStretch()
        bot.addWidget(BottomChip("Use Screen", variant="screen"))
        bot.addWidget(BottomChip("Smart",      variant="smart"))
        bot.addWidget(BottomChip("General",    variant="general"))
        bot.addStretch()
        lay.addLayout(bot)

    def _sw(self, idx):
        self._t_chat.setActive(idx == 0)
        self._t_trans.setActive(idx == 1)
        self._t_notes.setActive(idx == 2)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(C_BORDER, 1.0)); p.setBrush(QBrush(C_CARD_BG))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16); p.end()


class FloatingBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint|
                            Qt.WindowType.FramelessWindowHint|Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._drag=None
        root=QVBoxLayout(self); root.setContentsMargins(SHM,SHM,SHM,SHM); root.setSpacing(8)
        pill_row=QHBoxLayout(); pill_row.setContentsMargins(0,0,0,0)
        pill_row.addStretch(); pill_row.addWidget(TopPill(on_close=self.close)); pill_row.addStretch()
        root.addLayout(pill_row)
        self._card=MainCard()
        sh=QGraphicsDropShadowEffect(self); sh.setBlurRadius(52)
        sh.setColor(QColor(0,0,0,120)); sh.setOffset(0,14); self._card.setGraphicsEffect(sh)
        card_row=QHBoxLayout(); card_row.addStretch(); card_row.addWidget(self._card); card_row.addStretch()
        root.addLayout(card_row); self.adjustSize()

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:
            self._drag=e.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def mouseMoveEvent(self,e):
        if self._drag and e.buttons()==Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint()-self._drag)
    def mouseReleaseEvent(self,_): self._drag=None


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app=QApplication(sys.argv); app.setStyle("Fusion")
    bar=FloatingBar()
    screen=app.primaryScreen().availableGeometry()
    bar.move((screen.width()-bar.width())//2, 80)
    bar.show(); sys.exit(app.exec())

if __name__=="__main__":
    main()