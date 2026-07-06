"""Orange cat (耄耋) color tokens — demo-only."""
from __future__ import annotations

from dataclasses import dataclass

THEME_ID = "variant_orange_cat"
THEME_LABEL = "橘猫耄耋"

PRIMARY = "#FFB366"
PRIMARY_DARK = "#E89540"
PRIMARY_RGB = (255, 179, 102)
BG_CREAM = "#FFF2E2"
BG_WARM = "#F7D4A8"
TEXT_PRIMARY = "#3A271B"
TEXT_MUTED = "#8B7360"
DIVIDER = "rgba(139, 115, 96, 0.1)"
ACCENT_PINK = "#F0A89A"
SHELL_GLASS = (255, 242, 226, 230)
SHELL_BORDER = (247, 212, 168, 180)

# Top bar paint styles (demo shell paintEvent)
TOPBAR_STYLE_GLASS = "glass_orange"
TOPBAR_STYLE_HERO = "hero_gradient"
DEFAULT_TOPBAR_STYLE = TOPBAR_STYLE_GLASS
TOPBAR_HERO_FADE_RATIO = 0.25
TOPBAR_HERO_TOP = (255, 179, 102)
TOPBAR_HERO_MID = (245, 200, 150)
TOPBAR_GLASS_FILL = (255, 225, 195, 248)

SHELL_RADIUS = 20
COMPACT_RADIUS = 24

DEFAULT_SCALE_IN_MS = 500
DEFAULT_HOLD_MS = 800
DEFAULT_FADE_OUT_MS = 400
DEFAULT_IDLE_MINUTES = 0

TITLE_GRADIENT_START = PRIMARY_DARK
TITLE_GRADIENT_END = "#FFD4A3"


@dataclass(frozen=True)
class OrangeCatTokens:
    primary: str = PRIMARY
    primary_dark: str = PRIMARY_DARK
    bg_cream: str = BG_CREAM
    bg_warm: str = BG_WARM
    text_primary: str = TEXT_PRIMARY
    text_muted: str = TEXT_MUTED
    divider: str = DIVIDER
    accent_pink: str = ACCENT_PINK


TOKENS = OrangeCatTokens()
