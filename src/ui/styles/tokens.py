"""Design tokens for Opencluely UI.

Single source of truth for colours, radii, shadows, and typography
used across every stylesheet in the application.
"""

# Backgrounds
BG_BASE = "rgba(47, 47, 52, 0.84)"       # Top-bar / pill surfaces
BG_INNER = "rgba(10, 10, 12, 0.34)"      # Nested group inside top bar
BG_SHEET = "rgba(45, 45, 49, 0.67)"      # Glass content sheet
BG_COMPOSER = "rgba(21, 21, 24, 0.46)"   # Composer shell
BG_INPUT = "transparent"                 # Chat input background
BG_RESPONSE = "rgba(22, 23, 27, 0.48)"   # Response cards
BG_DEEP = "rgba(19, 20, 24, 0.78)"       # Deep inset (code blocks etc)
BG_TRANSCRIPT = "rgba(20, 21, 25, 0.68)" # Transcript box
BG_DROPDOWN = "rgba(28, 29, 34, 0.98)"   # ComboBox dropdown list

# Button and hover states
BG_HOVER_SUBTLE = "rgba(255, 255, 255, 0.08)"
BG_HOVER_FAINT = "rgba(255, 255, 255, 0.05)"
BG_HOVER_LIGHT = "rgba(255, 255, 255, 0.12)"
BG_ACTIVE_BUTTON = "rgba(255, 255, 255, 0.09)"
BG_TAB_ACTIVE = "rgba(255, 255, 255, 0.085)"
BG_TOOLBAR_PRIMARY = "#173762"
BG_TOOLBAR_PRIMARY_HOVER = "#204777"
BG_TOOLBAR_WARM = "rgba(255, 255, 255, 0.045)"
BG_TOOLBAR_WARM_HOVER = "rgba(255, 255, 255, 0.075)"
BG_TOOLBAR_WARM_ACTIVE = "rgba(245, 191, 63, 0.17)"
BG_SEND = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2A6DE6, stop:1 #1D54C7)"
BG_SEND_HOVER = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3F83F5, stop:1 #2A6DE6)"
BG_SHORTCUT_CHIP = "rgba(36, 37, 41, 0.92)"
BG_NOTES_ACTION = "rgba(255, 255, 255, 0.06)"
BG_NOTES_ACTION_HOVER = "rgba(255, 255, 255, 0.10)"
BG_CARD_BUTTON = "rgba(255, 255, 255, 0.045)"
BG_CARD_BUTTON_HOVER = "rgba(255, 255, 255, 0.08)"
BG_HEADER_ACTIVE = "rgba(255, 255, 255, 0.055)"

# Borders
BORDER_GLASS = "rgba(255, 255, 255, 0.18)"
BORDER_INNER = "rgba(255, 255, 255, 0.08)"
BORDER_FAINT = "rgba(255, 255, 255, 0.07)"
BORDER_SUBTLE = "rgba(255, 255, 255, 0.10)"
BORDER_TAB_ACTIVE = "rgba(255, 255, 255, 0.11)"
BORDER_HEADER_ACTIVE = "rgba(255, 255, 255, 0.12)"
BORDER_CHIP = "rgba(255, 255, 255, 0.14)"
BORDER_WARM_ACTIVE = "rgba(255, 211, 104, 0.45)"
BORDER_RESPONSE = "rgba(255, 255, 255, 0.12)"
BORDER_INPUT_FOCUS = "rgba(255, 255, 255, 0.22)"

# Text
TEXT_PRIMARY = "#F4F5F8"
TEXT_SECONDARY = "#D5D7DD"
TEXT_MUTED = "#979BA5"
TEXT_TAB_HOVER = "#FFFFFF"
TEXT_HINT = "#AFB3BC"
TEXT_CHIP = "#C9CCD4"
TEXT_TOOLBAR_PRIMARY = "#95BEFF"
TEXT_TOOLBAR_WARM = "#F1F2F5"
TEXT_TOOLBAR_WARM_ACTIVE = "#FFD66B"
TEXT_TOOLBAR_DROPDOWN = "#CDD0D8"
TEXT_TOOLBAR_DROPDOWN_HOVER = "#F4F5F8"
TEXT_EMPTY_STATE = "#9599A3"
TEXT_CARD = "#F4F5F8"
TEXT_RESPONSE = "#F4F5F8"
TEXT_QUICK_DOT = "rgba(255, 255, 255, 0.24)"

# Radii
RADIUS_PILL = "999px"
RADIUS_SHEET = "30px"
RADIUS_COMPOSER = "20px"
RADIUS_TOP_BAR = "19px"
RADIUS_CARD = "20px"
RADIUS_INPUT = "16px"
RADIUS_INNER = "15px"
RADIUS_ICON_LG = "16px"
RADIUS_ICON_SM = "13px"
RADIUS_EXPAND = "12px"
RADIUS_NOTES = "12px"
RADIUS_BUTTON = "12px"
RADIUS_CHIP = "7px"
RADIUS_SCROLLBAR = "5px"

# Sizes
ICON_SM = "26px"
ICON_MD = "28px"
ICON_LG = "32px"
ICON_CLOSE = "38px"
TOOLBAR_H = "32px"
SCROLLBAR_W = "10px"
SCROLLBAR_MIN_H = "24px"

# Selection
SELECTION_BG = "rgba(81, 133, 244, 0.42)"

# Accents
ACCENT_DANGER = "#EF4444"

# Typography
FONT_FAMILY = "'Inter', 'Segoe UI', sans-serif"
