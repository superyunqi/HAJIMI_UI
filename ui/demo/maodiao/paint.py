"""Orange cat shell painting — demo-only."""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen

from ui.demo.maodiao.palettes import MaodiaoPalette, get_palette
from ui.demo.maodiao.tokens import (
    DEFAULT_TOPBAR_STYLE,
    TOPBAR_HERO_FADE_RATIO,
    TOPBAR_STYLE_GLASS,
    TOPBAR_STYLE_HERO,
)

_PRIMARY_DARK_RGB = (232, 149, 64)


def _rounded_path(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def paint_maodiao_frame(
    painter: QPainter,
    rect: QRectF,
    *,
    compact: bool = False,
    radius: float | None = None,
    palette: MaodiaoPalette | None = None,
) -> None:
    """Warm cream glass pill — aligned with default compact shell structure."""
    if rect.width() <= 0 or rect.height() <= 0:
        return
    pal = palette or get_palette(None)
    h = rect.height()
    if radius is None:
        radius = min(h / 2, rect.width() / 2) if compact else 20.0

    path = _rounded_path(rect, radius)
    sr, sg, sb, sa = pal.shell_glass
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setClipPath(path)
    painter.fillPath(path, QColor(sr, sg, sb, sa))

    edge = QLinearGradient(rect.x(), rect.y(), rect.x(), rect.bottom())
    edge.setColorAt(0.0, QColor(255, 255, 255, 22))
    edge.setColorAt(0.35, QColor(255, 255, 255, 0))
    painter.fillPath(path, QBrush(edge))
    painter.restore()

    br, bg, bb, ba = pal.shell_border
    pen = QPen(QColor(br, bg, bb, ba))
    pen.setWidthF(1.0)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)


def paint_maodiao_topbar_hero_gradient(
    painter: QPainter,
    rect: QRectF,
    *,
    topbar_h: float,
    fade_ratio: float,
    radius: float,
    palette: MaodiaoPalette | None = None,
) -> None:
    """Rich orange through top bar, fading to dialog cream over upper window quarter."""
    if rect.width() <= 0 or rect.height() <= 0 or topbar_h <= 0:
        return
    pal = palette or get_palette(None)
    fade_h = max(topbar_h, rect.height() * max(0.05, min(1.0, fade_ratio)))
    zone = QRectF(rect.x(), rect.y(), rect.width(), fade_h)
    shell_path = _rounded_path(rect, radius)

    tr, tg, tb = pal.topbar_hero_top
    mr, mg, mb = pal.topbar_hero_mid
    er, eg, eb, ea = pal.topbar_hero_end
    bar_stop = min(0.92, topbar_h / fade_h)

    grad = QLinearGradient(zone.x(), zone.y(), zone.x(), zone.bottom())
    grad.setColorAt(0.0, QColor(tr, tg, tb, 252))
    grad.setColorAt(bar_stop * 0.55, QColor(tr, tg, tb, 248))
    grad.setColorAt(bar_stop, QColor(mr, mg, mb, 240))
    grad.setColorAt(1.0, QColor(er, eg, eb, ea))

    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setClipPath(shell_path)
    painter.fillRect(zone, QBrush(grad))
    painter.restore()


def paint_maodiao_topbar_glass(
    painter: QPainter,
    rect: QRectF,
    *,
    topbar_h: float,
    radius: float,
    palette: MaodiaoPalette | None = None,
) -> None:
    """Solid orange-tinted glass cap — slightly deeper than dialog cream body."""
    if rect.width() <= 0 or topbar_h <= 0:
        return
    pal = palette or get_palette(None)
    band_h = min(topbar_h, rect.height())
    top_rect = QRectF(rect.x(), rect.y(), rect.width(), band_h)
    shell_path = _rounded_path(rect, radius)

    gr, gg, gb, ga = pal.topbar_glass_fill
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setClipPath(shell_path)
    painter.fillRect(top_rect, QColor(gr, gg, gb, ga))

    edge = QLinearGradient(top_rect.x(), top_rect.y(), top_rect.x(), top_rect.bottom())
    edge.setColorAt(0.0, QColor(255, 255, 255, 28))
    edge.setColorAt(0.45, QColor(255, 255, 255, 0))
    painter.fillRect(top_rect, QBrush(edge))

    dr, dg, db = _PRIMARY_DARK_RGB
    line_y = top_rect.bottom() - 0.5
    border = QPen(QColor(dr, dg, db, 89))
    border.setWidthF(1.0)
    painter.setPen(border)
    painter.drawLine(
        int(top_rect.left() + radius * 0.2),
        int(line_y),
        int(top_rect.right() - radius * 0.2),
        int(line_y),
    )
    painter.restore()


def paint_maodiao_topbar(
    painter: QPainter,
    rect: QRectF,
    *,
    style: str,
    topbar_h: float,
    radius: float,
    fade_ratio: float = TOPBAR_HERO_FADE_RATIO,
    palette: MaodiaoPalette | None = None,
) -> None:
    """Dispatch top-bar shell overlay; TopBar widget stays transparent."""
    mode = style or DEFAULT_TOPBAR_STYLE
    if mode == TOPBAR_STYLE_HERO:
        paint_maodiao_topbar_hero_gradient(
            painter,
            rect,
            topbar_h=topbar_h,
            fade_ratio=fade_ratio,
            radius=radius,
            palette=palette,
        )
    else:
        paint_maodiao_topbar_glass(
            painter,
            rect,
            topbar_h=topbar_h,
            radius=radius,
            palette=palette,
        )
