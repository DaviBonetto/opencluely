"""Stylesheet for the LiveBar window and all its sub-surfaces."""

from . import tokens as T

LIVE_BAR_STYLESHEET = f"""
QMainWindow, QWidget#central, QWidget#top_row,
QWidget#ask_page, QWidget#transcript_page {{
    background: transparent;
}}

QLabel, QTextEdit, QLineEdit, QComboBox, QPushButton {{
    color: {T.TEXT_PRIMARY};
    font-family: {T.FONT_FAMILY};
}}

QFrame#top_bar {{
    background-color: {T.BG_BASE};
    border: 1px solid {T.BORDER_GLASS};
    border-radius: {T.RADIUS_TOP_BAR};
}}

QFrame#top_inner_group {{
    background-color: {T.BG_INNER};
    border: 1px solid {T.BORDER_INNER};
    border-radius: {T.RADIUS_INNER};
}}

QFrame#line_divider {{
    background-color: rgba(255, 255, 255, 0.14);
    border: none;
    min-width: 1px;
    max-width: 1px;
}}

QPushButton#glass_icon_button {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {T.RADIUS_ICON_SM};
    min-width: {T.ICON_SM};
    max-width: {T.ICON_SM};
    min-height: {T.ICON_SM};
    max-height: {T.ICON_SM};
    padding: 0;
}}

QPushButton#glass_icon_button:hover {{
    background-color: {T.BG_HOVER_SUBTLE};
}}

QPushButton#glass_icon_button[active="true"] {{
    background-color: {T.BG_ACTIVE_BUTTON};
    border-color: rgba(255, 255, 255, 0.14);
}}

QLabel#record_indicator {{
    color: {T.ACCENT_DANGER};
    font-size: 11px;
    font-weight: 700;
    padding: 0 4px;
}}

QLabel#record_indicator[pulse="true"] {{
    color: rgba(239, 68, 68, 0.22);
}}

QLabel#timer_label {{
    color: {T.TEXT_PRIMARY};
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#top_close_button {{
    background-color: {T.BG_BASE};
    border: 1px solid {T.BORDER_GLASS};
    border-radius: {T.RADIUS_TOP_BAR};
    min-width: {T.ICON_CLOSE};
    max-width: {T.ICON_CLOSE};
    min-height: {T.ICON_CLOSE};
    max-height: {T.ICON_CLOSE};
    padding: 0;
}}

QPushButton#top_close_button:hover {{
    background-color: {T.BG_HOVER_LIGHT};
}}

QFrame#glass_sheet, QFrame#context_container {{
    background-color: {T.BG_SHEET};
    border: 1px solid {T.BORDER_GLASS};
    border-radius: {T.RADIUS_SHEET};
}}

QPushButton#header_home_button {{
    background-color: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: {T.RADIUS_PILL};
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    padding: 0;
}}

QPushButton#header_home_button:hover {{
    background-color: rgba(255, 255, 255, 0.07);
}}

QPushButton#header_home_button[active="true"] {{
    background-color: rgba(255, 255, 255, 0.075);
    border-color: rgba(255, 255, 255, 0.13);
}}

QPushButton#header_icon_button {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {T.RADIUS_ICON_LG};
    min-width: {T.ICON_LG};
    max-width: {T.ICON_LG};
    min-height: {T.ICON_LG};
    max-height: {T.ICON_LG};
    padding: 0;
}}

QPushButton#header_icon_button:hover,
QPushButton#header_expand_button:hover {{
    background-color: {T.BG_HOVER_FAINT};
}}

QPushButton#header_icon_button[active="true"] {{
    background-color: {T.BG_HEADER_ACTIVE};
    border-color: {T.BORDER_HEADER_ACTIVE};
}}

QPushButton#surface_tab {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {T.RADIUS_PILL};
    color: {T.TEXT_MUTED};
    font-size: 14px;
    font-weight: 600;
    min-height: 29px;
    padding: 0 12px;
}}

QPushButton#surface_tab:hover {{
    color: {T.TEXT_TAB_HOVER};
}}

QPushButton#surface_tab[active="true"] {{
    background-color: {T.BG_TAB_ACTIVE};
    border-color: {T.BORDER_TAB_ACTIVE};
    color: {T.TEXT_PRIMARY};
}}

QPushButton#header_expand_button {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {T.RADIUS_EXPAND};
    min-width: {T.ICON_MD};
    max-width: {T.ICON_MD};
    min-height: {T.ICON_MD};
    max-height: {T.ICON_MD};
    padding: 0;
}}

QFrame#quick_actions_row {{
    background: transparent;
    border: none;
}}

QPushButton#quick_action_button {{
    background: transparent;
    border: none;
    color: {T.TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 600;
    min-height: 24px;
    padding: 0 1px;
    text-align: left;
}}

QPushButton#quick_action_button:hover {{
    color: {T.TEXT_PRIMARY};
}}

QLabel#quick_action_dot {{
    color: {T.TEXT_QUICK_DOT};
    font-size: 10px;
}}

QFrame#composer_shell {{
    background-color: {T.BG_COMPOSER};
    border: 1px solid {T.BORDER_SUBTLE};
    border-radius: {T.RADIUS_COMPOSER};
}}

QLineEdit#chat_input {{
    background: {T.BG_INPUT};
    border: none;
    color: {T.TEXT_PRIMARY};
    font-size: 14px;
    padding: 0;
    selection-background-color: {T.SELECTION_BG};
}}

QLineEdit#chat_input:focus {{
    border: none;
}}

QLabel#shortcut_hint {{
    color: {T.TEXT_HINT};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#shortcut_chip {{
    background-color: {T.BG_SHORTCUT_CHIP};
    border: 1px solid {T.BORDER_CHIP};
    border-radius: {T.RADIUS_CHIP};
    color: {T.TEXT_CHIP};
    font-size: 11px;
    font-weight: 600;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    padding: 0;
}}

QPushButton#toolbar_button_primary {{
    background-color: {T.BG_TOOLBAR_PRIMARY};
    border: 1px solid rgba(149, 190, 255, 0.20);
    border-radius: {T.RADIUS_PILL};
    color: {T.TEXT_TOOLBAR_PRIMARY};
    font-size: 13px;
    font-weight: 600;
    min-height: {T.TOOLBAR_H};
    padding: 0 14px;
}}

QPushButton#toolbar_button_primary:hover {{
    background-color: {T.BG_TOOLBAR_PRIMARY_HOVER};
}}

QPushButton#toolbar_button_warm {{
    background-color: {T.BG_TOOLBAR_WARM};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: {T.RADIUS_PILL};
    color: {T.TEXT_TOOLBAR_WARM};
    font-size: 13px;
    font-weight: 600;
    min-height: {T.TOOLBAR_H};
    padding: 0 14px;
}}

QPushButton#toolbar_button_warm:hover {{
    background-color: {T.BG_TOOLBAR_WARM_HOVER};
}}

QPushButton#toolbar_button_warm[active="true"] {{
    background-color: {T.BG_TOOLBAR_WARM_ACTIVE};
    color: {T.TEXT_TOOLBAR_WARM_ACTIVE};
    border-color: {T.BORDER_WARM_ACTIVE};
}}

QPushButton#toolbar_button_dropdown {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {T.RADIUS_PILL};
    color: {T.TEXT_TOOLBAR_DROPDOWN};
    font-size: 13px;
    font-weight: 600;
    min-height: {T.TOOLBAR_H};
    padding: 0 8px;
}}

QPushButton#toolbar_button_dropdown:hover,
QPushButton#toolbar_button_dropdown[active="true"] {{
    color: {T.TEXT_TOOLBAR_DROPDOWN_HOVER};
    background-color: rgba(255, 255, 255, 0.05);
}}

QPushButton#send_button {{
    background-color: {T.BG_SEND};
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: {T.RADIUS_INPUT};
    color: {T.TEXT_PRIMARY};
    min-width: {T.ICON_LG};
    max-width: {T.ICON_LG};
    min-height: {T.ICON_LG};
    max-height: {T.ICON_LG};
    padding: 0;
}}

QPushButton#send_button:hover {{
    background-color: {T.BG_SEND_HOVER};
}}

QScrollArea#response_scroll,
QWidget#response_pool {{
    background: transparent;
    border: none;
}}

QLabel#empty_state {{
    background-color: transparent;
    border: none;
    color: {T.TEXT_EMPTY_STATE};
    padding: 0;
}}

QTextEdit#transcript_box {{
    background-color: {T.BG_TRANSCRIPT};
    border: 1px solid {T.BORDER_SUBTLE};
    border-radius: {T.RADIUS_COMPOSER};
    padding: 14px 16px;
    color: {T.TEXT_PRIMARY};
}}

QScrollBar:vertical {{
    background: transparent;
    border: none;
    width: {T.SCROLLBAR_W};
    margin: 4px 0 4px 0;
}}

QScrollBar::handle:vertical {{
    background: {T.BORDER_GLASS};
    border-radius: {T.RADIUS_SCROLLBAR};
    min-height: {T.SCROLLBAR_MIN_H};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

QFrame#response_card {{
    background-color: {T.BG_RESPONSE};
    border: 1px solid {T.BORDER_FAINT};
    border-radius: {T.RADIUS_CARD};
}}

QLabel#response_title {{
    color: {T.TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#card_button {{
    background-color: {T.BG_CARD_BUTTON};
    border: 1px solid {T.BORDER_SUBTLE};
    border-radius: {T.RADIUS_BUTTON};
    color: {T.TEXT_CARD};
    min-height: 28px;
    padding: 0 10px;
}}

QPushButton#card_button:hover {{
    background-color: {T.BG_CARD_BUTTON_HOVER};
}}

QPushButton#notes_action_button {{
    background-color: {T.BG_NOTES_ACTION};
    border: 1px solid {T.BORDER_SUBTLE};
    border-radius: {T.RADIUS_NOTES};
    color: {T.TEXT_CARD};
    font-size: 12px;
    font-weight: 600;
    min-height: {T.TOOLBAR_H};
    padding: 0 12px;
}}

QPushButton#notes_action_button:hover {{
    background-color: {T.BG_NOTES_ACTION_HOVER};
}}

QComboBox, QTextEdit#notes_editor {{
    background-color: rgba(0, 0, 0, 0.22);
    border: 1px solid {T.BORDER_SUBTLE};
    border-radius: {T.RADIUS_INPUT};
    padding: 10px 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {T.BG_DROPDOWN};
    border: 1px solid {T.BORDER_SUBTLE};
    selection-background-color: {T.BG_HOVER_SUBTLE};
    color: {T.TEXT_PRIMARY};
}}
"""

RESPONSE_ANSWER_STYLE = (
    "QTextEdit {"
    f" background-color: {T.BG_DEEP};"
    f" border: 1px solid {T.BORDER_RESPONSE};"
    f" border-radius: {T.RADIUS_INNER};"
    " padding: 12px;"
    f" color: {T.TEXT_RESPONSE};"
    " }"
)
