"""Orange cat QSS composer — demo-only."""
from __future__ import annotations

from ui.demo.maodiao.palettes import DEFAULT_MOOD, MaodiaoPalette, get_palette
from ui.demo.maodiao.tokens import ACCENT_PINK, COMPACT_RADIUS, SHELL_RADIUS

BODY_FONT_DEFAULT = '"Segoe UI", "Microsoft YaHei UI", sans-serif'


def compose_maodiao_qss(
    font_size: int = 12,
    *,
    body_font: str = BODY_FONT_DEFAULT,
    shell_radius: int = SHELL_RADIUS,
    compact_radius: int = COMPACT_RADIUS,
    mood: str = DEFAULT_MOOD,
) -> str:
    pal = get_palette(mood)
    bubble_label = font_size + 1
    br = pal.bubble_radius
    ir = pal.input_radius
    system_left = pal.bubble_system_border_left
    system_left_css = (
        f"border-left: {system_left};" if system_left and system_left != "none" else ""
    )
    return f"""
* {{
    font-family: {body_font};
    font-size: {font_size}px;
}}
QWidget#NativeShell, QWidget#CompactShell, QWidget#NativeShell *, QWidget#CompactShell * {{
    color: {pal.text_primary};
}}
QWidget#NativeShell, QWidget#CompactShell {{
    background: transparent;
    background-color: transparent;
    border: none;
    border-radius: {shell_radius}px;
}}
QWidget#TopBar {{
    background: transparent;
}}
QWidget#TitleArt, QWidget#OrangeCatTitle {{
    background: transparent;
}}
QLabel#TopTitleRestrained {{
    font-size: 13px;
    font-weight: 600;
    color: {pal.text_primary};
}}
QLabel#TopSub {{
    font-size: 12px;
    color: {pal.top_sub_color};
    font-weight: 500;
}}
QLabel#TopTitleSep {{
    font-size: 12px;
    color: rgba(232, 149, 64, 0.55);
    padding: 0 2px;
}}
QLabel#TopErrorChip {{
    font-size: 11px;
    font-weight: 600;
    color: {ACCENT_PINK};
}}
QPushButton#StatusBadge {{
    padding: 6px 16px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    background: {pal.status_idle_bg};
    color: {pal.status_idle_color};
    border: 1px solid {pal.status_idle_border};
}}
QPushButton#StatusBadge[status="processing"] {{
    background: {pal.status_processing_bg};
    color: {pal.status_processing_color};
    border: 1px solid {pal.status_processing_border};
}}
QPushButton#StatusBadge[status="idle"] {{
    background: {pal.status_idle_bg};
    color: {pal.status_idle_color};
}}
QPushButton#MenuBtn, QPushButton#OrangeCatIconBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    min-width: 34px;
    min-height: 34px;
    color: {pal.text_muted};
}}
QPushButton#MenuBtn:hover, QPushButton#OrangeCatIconBtn:hover {{
    background: {pal.menu_hover};
    color: {pal.primary_dark};
}}
QScrollArea#PreviewContent, QWidget#PreviewContentWrap, QWidget#InputDock {{
    background: transparent;
    border: none;
}}
QFrame#bubble-user {{
    background-color: {pal.bubble_user_bg};
    border: 1px solid {pal.bubble_user_border};
    border-radius: {br}px;
    border-top-right-radius: 2px;
}}
QFrame#bubble-system {{
    background-color: {pal.bubble_system_bg};
    border: 1px solid {pal.bubble_system_border};
    border-radius: {br}px;
    border-top-left-radius: 2px;
    {system_left_css}
}}
QLabel#bubbleUserLabel, QLabel#bubbleSystemLabel {{
    color: {pal.text_primary};
    font-size: {bubble_label}px;
}}
QFrame#InputFloat {{
    background: {pal.input_bg};
    border: 1px solid {pal.input_border};
    border-radius: {ir}px;
}}
QFrame#InputFloat:focus-within {{
    border: 1px solid {pal.input_focus_border};
}}
QFrame#InputFloat QTextEdit#ChatInput {{
    background: transparent;
    border: none;
    color: {pal.text_primary};
    font-size: {font_size}px;
}}
QPushButton#IconBtnGhost {{
    background: transparent;
    border: none;
    border-radius: 8px;
}}
QPushButton#IconBtnGhost:hover {{
    background: {pal.primary_hover};
}}
QPushButton#SendBtnAccent, QPushButton#SendBtnOrange {{
    {pal.send_btn_css}
    border-radius: 8px;
    font-size: 14px;
    min-width: 32px;
    min-height: 32px;
}}
QPushButton#SendBtnAccent:hover, QPushButton#SendBtnOrange:hover {{
    {pal.send_btn_hover_css}
}}
QLabel#CompactMark {{
    background: transparent;
    border: none;
    color: {pal.primary_dark};
    font-size: 15px;
}}
QLineEdit#CompactInput {{
    background: transparent;
    border: none;
    color: {pal.text_primary};
    font-size: 13px;
    padding: 0 4px;
}}
QLabel#CompactHint {{
    color: {pal.text_muted};
    font-size: 11px;
    padding-right: 4px;
}}
QLabel#BubbleAvatar {{
    background: transparent;
    border: 2px solid rgba(232, 149, 64, 0.35);
    border-radius: 18px;
}}
QLabel#BubbleAvatar[avatarRole="user"] {{
    border: 2px solid rgba(232, 149, 64, 0.55);
}}
QWidget#NavBackdrop {{
    background: rgba(58, 39, 27, 0.35);
}}
QWidget#NavDrawer {{
    background: {pal.drawer_bg};
    border-right: 1px solid rgba(139, 115, 96, 0.22);
}}
QFrame#DrawerSep {{
    background: rgba(139, 115, 96, 0.18);
    max-height: 1px;
}}
QLabel#DrawerHead {{
    color: {pal.text_primary};
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#NavItem {{
    text-align: left;
    padding: 9px 10px;
    border: none;
    border-radius: 10px;
    color: {pal.text_muted};
    background: transparent;
    font-size: 12px;
}}
QPushButton#NavItem:hover {{
    background: {pal.primary_soft};
    color: {pal.text_primary};
}}
QPushButton#NavItem[active="true"] {{
    background: rgba(255, 179, 102, 0.32);
    color: {pal.primary_dark};
    border: 1px solid rgba(232, 149, 64, 0.35);
}}
QPushButton#NavItemQuit {{
    text-align: left;
    padding: 9px 10px;
    border: none;
    border-radius: 10px;
    color: #C45A4A;
    background: transparent;
    font-size: 12px;
    margin-top: 4px;
}}
QPushButton#NavItemQuit:hover {{
    background: rgba(196, 90, 74, 0.12);
    color: #A84838;
}}
QWidget#ControlPanel {{
    background: {pal.bg_cream};
    border-left: 1px solid rgba(139, 115, 96, 0.18);
    color: {pal.text_primary};
}}
QWidget#ControlPanel QLabel {{
    color: {pal.text_primary};
}}
QWidget#ControlPanel QRadioButton, QWidget#ControlPanel QCheckBox {{
    color: {pal.text_primary};
    spacing: 6px;
}}
QWidget#ControlPanel QComboBox {{
    background: #FFFFFF;
    color: {pal.text_primary};
    border: 1px solid rgba(139, 115, 96, 0.22);
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 22px;
}}
QWidget#ControlPanel QLineEdit {{
    background: #FFFFFF;
    color: {pal.text_primary};
    border: 1px solid rgba(139, 115, 96, 0.22);
    border-radius: 6px;
    padding: 4px 8px;
}}
QWidget#ControlPanel QSlider::groove:horizontal {{
    background: {pal.bg_warm};
    height: 4px;
    border-radius: 2px;
}}
QWidget#ControlPanel QSlider::handle:horizontal {{
    background: {pal.primary};
    width: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QLabel#ControlTitle, QLabel#SectionLabel {{
    color: {pal.text_primary};
    font-weight: 600;
}}
QLabel#DemoHint, QLabel#SliderValue {{
    color: {pal.text_muted};
}}
QPushButton#DemoActionBtn {{
    background: rgba(255, 179, 102, 0.28);
    border: 1px solid rgba(232, 149, 64, 0.45);
    border-radius: 8px;
    color: {pal.text_primary};
    font-weight: 600;
    padding: 6px 10px;
}}
QPushButton#DemoActionBtn:hover {{
    background: rgba(255, 179, 102, 0.42);
    border: 1px solid {pal.primary_dark};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
}}
QScrollBar::handle:vertical {{
    background: rgba(139, 115, 96, 0.35);
    border-radius: 3px;
    min-height: 24px;
}}
QWidget#ControlPanel QScrollBar::handle:vertical {{
    background: rgba(139, 115, 96, 0.45);
}}
"""
