"""SVG icon templates for Opencluely UI.

Each template is a parameterised SVG string with a ``{color}`` placeholder.
The shapes lean on Lucide-style strokes so the shell stays visually cohesive.
"""

from __future__ import annotations

from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer


SVG_TEMPLATES: dict[str, str] = {
    "eye": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z"/>
            <circle cx="12" cy="12" r="3"/>
        </svg>
    """,
    "anonymous": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6.4 0 10 7 10 7a20.2 20.2 0 0 1-2.2 3.1"/>
            <path d="M6.7 6.7A19.6 19.6 0 0 0 2 12s3.6 7 10 7a9.7 9.7 0 0 0 5.3-1.5"/>
            <path d="m2 2 20 20"/>
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>
        </svg>
    """,
    "pause": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 4v16"/>
            <path d="M14 4v16"/>
        </svg>
    """,
    "stop": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">
            <rect x="6" y="6" width="12" height="12" rx="2.6"/>
        </svg>
    """,
    "chevron_up": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
            <path d="m18 15-6-6-6 6"/>
        </svg>
    """,
    "grip": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">
            <circle cx="9" cy="5" r="1.45"/>
            <circle cx="15" cy="5" r="1.45"/>
            <circle cx="9" cy="12" r="1.45"/>
            <circle cx="15" cy="12" r="1.45"/>
            <circle cx="9" cy="19" r="1.45"/>
            <circle cx="15" cy="19" r="1.45"/>
        </svg>
    """,
    "close": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
        </svg>
    """,
    "home": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 10.5 9-7 9 7"/>
            <path d="M6 9.8V20h12V9.8"/>
        </svg>
    """,
    "expand": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3h6v6"/>
            <path d="m21 3-7 7"/>
            <path d="M9 21H3v-6"/>
            <path d="m3 21 7-7"/>
        </svg>
    """,
    "chevron_down": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 9 6 6 6-6"/>
        </svg>
    """,
    "sparkles": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l1.8 4.8L19 9.6l-5.2 1.8L12 16l-1.8-4.6L5 9.6l5.2-1.8L12 3Z"/>
            <path d="M5 18.5 5.8 21l.8-2.5L9 17.7l-2.4-.8-.8-2.5-.8 2.5L2.6 17.7 5 18.5Z"/>
        </svg>
    """,
    "wand": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 4V2"/>
            <path d="M15 16v-2"/>
            <path d="M8 9H6"/>
            <path d="M20 9h-2"/>
            <path d="M17.8 6.2 19.2 4.8"/>
            <path d="M10.2 13.8 8.8 15.2"/>
            <path d="M17.8 11.8 19.2 13.2"/>
            <path d="M10.2 4.2 8.8 5.6"/>
            <path d="m3 21 9.4-9.4"/>
            <path d="m11.5 4.5 8 8"/>
        </svg>
    """,
    "message_plus": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 10h7"/>
            <path d="M10.5 6.5v7"/>
            <path d="M21 15a3 3 0 0 1-3 3H9l-5 4V6a3 3 0 0 1 3-3h11a3 3 0 0 1 3 3Z"/>
        </svg>
    """,
    "rotate": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 15.4-6.4L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"/>
            <path d="M8 21H3v-5"/>
        </svg>
    """,
    "image": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="16" rx="3"/>
            <circle cx="9" cy="10" r="1.5"/>
            <path d="m21 15-4.5-4.5L7 20"/>
        </svg>
    """,
    "zap": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">
            <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"/>
        </svg>
    """,
    "send": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h12"/>
            <path d="m13 6 6 6-6 6"/>
        </svg>
    """,
}


def render_svg_icon(icon_key: str, color: str, size: QSize | None = None) -> QIcon:
    """Render an SVG template to a QIcon with the given colour."""
    template = SVG_TEMPLATES[icon_key]
    renderer = QSvgRenderer(QByteArray(template.format(color=color).encode("utf-8")))
    target_size = size or QSize(18, 18)
    pixmap = QPixmap(target_size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
