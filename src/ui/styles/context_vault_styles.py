"""Stylesheet helpers for the ContextVaultPanel (Prep Deck).

Unlike the LiveBar stylesheet, the Prep Deck uses inline styles
applied per-widget.  This module centralises the constant values
so that the panel code stays clean.
"""

from . import tokens as T

# ── Panel frame ──────────────────────────────────────────────
VAULT_PANEL_STYLE = """
QFrame#context_vault_panel {
    background-color: #0d0d0d;
    border: 2px solid #333;
    border-radius: 16px;
}
"""

VAULT_HEADER_STYLE = "background: #1a1a1a; border-radius: 16px 16px 0 0;"
VAULT_TITLE_STYLE = "color: white; font-size: 18px; font-weight: bold;"
VAULT_COUNTER_STYLE = "color: #888; font-size: 12px; margin-right: 15px;"
VAULT_ADD_BUTTON_STYLE = (
    "background: #22c55e; color: white; border-radius: 6px;"
    " padding: 6px 12px; font-weight: bold;"
)
VAULT_CLOSE_BUTTON_STYLE = (
    "background: #333; color: #aaa; border-radius: 15px;"
    " font-size: 14px; margin-left: 10px;"
)
VAULT_SCROLL_STYLE = (
    "QScrollArea { background: transparent; border: none; }"
    " QScrollBar:vertical { background: #111; width: 10px; }"
)
VAULT_GRIP_STYLE = "color: #444; font-size: 12px; padding: 2px;"


# ── Prompt item card ─────────────────────────────────────────
def card_style(starred: bool, completed: bool) -> str:
    """Return card QSS based on current state."""
    if starred:
        bg, border, hover = "#2a2a1a", "#f59e0b", "#3a3a2a"
    elif completed:
        bg, border, hover = "#1a2a1a", "#22c55e", "#2a3a2a"
    else:
        bg, border, hover = "#1a1a1a", "#2a2a2a", "#202020"

    return f"""
    QFrame#context_prompt_item {{
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 10px;
        margin: 3px 0;
    }}
    QFrame#context_prompt_item:hover {{
        border-color: #444;
        background-color: {hover};
    }}
    """


NUM_LABEL_STYLE = (
    "color: #0a84ff; font-size: 18px; font-weight: bold;"
    " background: #1a2a3a; padding: 4px 10px; border-radius: 6px;"
)
TITLE_STYLE = "color: #ffffff; font-size: 16px; font-weight: 500;"
EXPAND_COLLAPSED = "color: #666; font-size: 14px;"
EXPAND_EXPANDED = "color: #0a84ff; font-size: 14px;"
BTN_MOVE_STYLE = (
    "background: #333; color: #aaa; border-radius: 4px;"
    " font-size: 14px; font-weight: bold;"
)
STAR_ON = "background: #f59e0b; color: #000; border-radius: 6px; font-size: 16px;"
STAR_OFF = "background: #333; color: #888; border-radius: 6px; font-size: 16px;"
CHECK_ON = (
    "background: #22c55e; color: #fff; border-radius: 6px;"
    " font-size: 14px; font-weight: bold;"
)
CHECK_OFF = (
    "background: #333; color: #666; border-radius: 6px;"
    " font-size: 14px; font-weight: bold;"
)
CONTENT_VIEW_STYLE = (
    "QTextEdit { background: #222; color: #e0e0e0; font-size: 16px; padding: 15px;"
    " border: none; border-radius: 8px; border-left: 4px solid #0a84ff; }"
)
CONTENT_EDIT_STYLE = (
    "QTextEdit { background: #1a1a1a; border: 2px solid #0a84ff;"
    " font-size: 15px; padding: 10px; color: white; }"
)
EDIT_BUTTON_STYLE = "background: #333; border-radius: 6px; padding: 6px 12px; color: #ccc;"
DELETE_BUTTON_STYLE = (
    "background: #3a2a2a; color: #f3d6d6; border-radius: 6px; padding: 0 10px;"
)
SAVE_BUTTON_STYLE = (
    "background: #22c55e; color: white; padding: 8px;"
    " border-radius: 6px; font-weight: bold;"
)


def status_dot_color(has_content: bool) -> str:
    """Return the dot colour based on whether content exists."""
    c = "#4ade80" if has_content else "#666"
    return f"color: {c}; font-size: 10px;"
