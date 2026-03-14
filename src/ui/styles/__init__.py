"""Opencluely UI style package.

Re-exports the main artefacts so consumers can do:

    from src.ui.styles import LIVE_BAR_STYLESHEET, SVG_TEMPLATES, render_svg_icon
"""

from . import context_vault_styles
from .icons import SVG_TEMPLATES, render_svg_icon
from .live_bar_styles import LIVE_BAR_STYLESHEET, RESPONSE_ANSWER_STYLE

__all__ = [
    "context_vault_styles",
    "LIVE_BAR_STYLESHEET",
    "RESPONSE_ANSWER_STYLE",
    "SVG_TEMPLATES",
    "render_svg_icon",
]
