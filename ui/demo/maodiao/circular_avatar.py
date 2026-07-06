"""Circular avatar label — PNG/JPG/GIF, demo-only."""
from __future__ import annotations

import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QBrush, QColor, QFont, QMovie, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QLabel

from ui.demo.maodiao.icons import maodiao_pixmap
from ui.demo.maodiao.image_alpha import load_transparent_pixmap
from ui.demo.maodiao.tokens import BG_WARM, PRIMARY, PRIMARY_DARK, TEXT_PRIMARY

AVATAR_SIZE = 36
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def _is_gif(path: str) -> bool:
    return path.lower().endswith(".gif")


def _is_image_file(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    return os.path.splitext(path)[1].lower() in _IMAGE_EXTS


class CircularAvatar(QLabel):
    """Round avatar; static images clipped in paintEvent, GIF via QMovie frames."""

    def __init__(self, role: str = "ai", parent=None):
        super().__init__(parent)
        self._role = role if role in ("ai", "user") else "ai"
        self.setObjectName("BubbleAvatar")
        self.setProperty("avatarRole", self._role)
        self.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._static_pixmap: QPixmap | None = None
        self._movie: QMovie | None = None
        self._custom_path: str | None = None
        self._fallback_pixmap = self._build_fallback()

    def _build_fallback(self) -> QPixmap:
        if self._role == "ai":
            return maodiao_pixmap("avatar", AVATAR_SIZE)
        pix = QPixmap(AVATAR_SIZE, AVATAR_SIZE)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(PRIMARY_DARK), 1.5))
        p.setBrush(QColor(BG_WARM))
        p.drawEllipse(1, 1, AVATAR_SIZE - 2, AVATAR_SIZE - 2)
        font = QFont("Segoe UI", 11, QFont.Bold)
        p.setFont(font)
        p.setPen(QColor(TEXT_PRIMARY))
        p.drawText(pix.rect(), Qt.AlignCenter, "我")
        p.end()
        return pix

    def _stop_movie(self) -> None:
        if self._movie is not None:
            self._movie.stop()
            self._movie.setParent(None)
            self._movie.deleteLater()
            self._movie = None

    def _current_frame(self) -> QPixmap:
        if self._movie is not None:
            frame = self._movie.currentPixmap()
            if not frame.isNull():
                return frame
        if self._static_pixmap is not None and not self._static_pixmap.isNull():
            return self._static_pixmap
        return self._fallback_pixmap

    def set_image_path(self, path: str | None) -> None:
        self._stop_movie()
        self._static_pixmap = None
        self._custom_path = None
        if path and _is_image_file(path):
            self._custom_path = path
            if _is_gif(path):
                movie = QMovie(path)
                movie.setBackgroundColor(QColor(0, 0, 0, 0))
                movie.setScaledSize(QSize(AVATAR_SIZE, AVATAR_SIZE))
                movie.frameChanged.connect(lambda _i: self.update())
                movie.start()
                self._movie = movie
            else:
                pix = load_transparent_pixmap(path)
                if not pix.isNull():
                    self._static_pixmap = pix
        self.update()

    def clear_custom(self) -> None:
        self.set_image_path(None)

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        if side <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        clip = QPainterPath()
        clip.addEllipse(0, 0, side, side)
        painter.setClipPath(clip)

        src = self._current_frame()
        scaled = src.scaled(
            side, side, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x = (side - scaled.width()) // 2
        y = (side - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

        painter.setClipping(False)
        border = QColor(PRIMARY_DARK if self._role == "user" else PRIMARY)
        border.setAlpha(90)
        painter.setPen(QPen(border, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, side - 2, side - 2)
        painter.end()
