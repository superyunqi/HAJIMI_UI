"""Orange cat icons — demo-only."""
from __future__ import annotations

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor

from ui.demo.maodiao.image_alpha import load_transparent_pixmap, scale_to_square
from ui.demo.maodiao.image_pool import resolve_icon_path
from ui.demo.maodiao.tokens import PRIMARY, PRIMARY_DARK, TEXT_MUTED
from ui.native.nav_icons import svg_icon

_ICON_FILES = {
    "mark": "mark.png",
    "menu": "menu.png",
    "mic": "mic.png",
    "send": "send.png",
    "badge": "badge.png",
    "avatar": "avatar.png",
    "guide": "guide.png",
    "steps": "steps.png",
    "blueprint": "blueprint.png",
    "notifications": "notifications.png",
    "settings": "settings.png",
    "compact": "compact.png",
    "logout": "logout.png",
}

_NAV_KEYS = frozenset(
    {"guide", "steps", "blueprint", "notifications", "settings", "compact", "logout"}
)

_FALLBACK_SVG = {
    "menu": "menu",
    "mic": "mic",
    "send": "send",
}

_NAV_INACTIVE_OPACITY = 0.55

_icon_square_cache: dict[tuple[str, int], QPixmap] = {}


def _with_opacity(pix: QPixmap, opacity: float) -> QPixmap:
    if pix.isNull() or opacity >= 0.999:
        return pix
    out = QPixmap(pix.size())
    out.fill(Qt.transparent)
    painter = QPainter(out)
    painter.setOpacity(max(0.0, min(1.0, opacity)))
    painter.drawPixmap(0, 0, pix)
    painter.end()
    return out


def _load_png_icon(name: str, size: int) -> QIcon | None:
    path = resolve_icon_path(name)
    if not path:
        return None
    cache_key = (path, size)
    if cache_key in _icon_square_cache:
        return QIcon(_icon_square_cache[cache_key])
    pix = load_transparent_pixmap(path)
    if pix.isNull():
        return None
    scaled = scale_to_square(pix, size)
    _icon_square_cache[cache_key] = scaled
    return QIcon(scaled)


def maodiao_icon(name: str, size: int = 24) -> QIcon:
    loaded = _load_png_icon(name, size)
    if loaded is not None:
        return loaded
    fallback = _FALLBACK_SVG.get(name)
    if fallback:
        icon = svg_icon(fallback, size, PRIMARY)
        if not icon.isNull():
            return icon
    if name == "mark":
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor("#FFB366"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, size - 4, size - 4)
        p.setPen(QColor("#3A271B"))
        p.drawEllipse(size // 3, size // 3, 3, 3)
        p.drawEllipse(2 * size // 3, size // 3, 3, 3)
        p.end()
        return QIcon(pix)
    return QIcon()


def maodiao_nav_icon(key: str, active: bool = False, size: int = 18) -> QIcon:
    loaded = _load_png_icon(key, size)
    if loaded is not None:
        if active:
            return loaded
        pix = loaded.pixmap(QSize(size, size))
        return QIcon(_with_opacity(pix, _NAV_INACTIVE_OPACITY))
    if key in _NAV_KEYS or key in _FALLBACK_SVG:
        color = PRIMARY_DARK if active else TEXT_MUTED
        icon = svg_icon(key, size, color)
        if not icon.isNull():
            return icon
    return QIcon()


def maodiao_pixmap(name: str, size: int = 24) -> QPixmap:
    icon = maodiao_icon(name, size)
    return icon.pixmap(QSize(size, size))
