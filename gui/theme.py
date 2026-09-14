# gui/theme.py
"""Cursor Start-inspired palette for the Helion desktop app."""
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "brand"
HEX_PATH = ASSETS / "helion_hex.png"

C = {
    "bg": "#0a0a0a",
    "surface": "#141414",
    "surface2": "#1a1a1a",
    "panel": "#111111",
    "border": "#262626",
    "text": "#ededed",
    "text_dim": "#8a8a8a",
    "text_bright": "#fafafa",
    "accent": "#f54e00",
    "accent_dim": "#ff6a3d",
    "user": "#1c1c1c",
    "green": "#3fb950",
    "red": "#f85149",
    "amber": "#f54e00",
}


def hex_icon() -> QIcon:
    if HEX_PATH.exists():
        return QIcon(str(HEX_PATH))
    pix = QPixmap(64, 64)
    pix.fill("#0a0a0a")
    return QIcon(pix)


def hex_pixmap(width: int = 280) -> QPixmap:
    if HEX_PATH.exists():
        pix = QPixmap(str(HEX_PATH))
        return pix.scaledToWidth(width)
    return QPixmap()


STYLESHEET = """
QMainWindow, QWidget#HelionRoot {
    background: #0a0a0a;
    color: #ededed;
    font-family: "Segoe UI";
    font-size: 13px;
}
QWidget {
    background: transparent;
    color: #ededed;
    font-family: "Segoe UI";
}
QFrame#Nav {
    background: #0a0a0a;
    border-right: 1px solid #262626;
}
QPushButton#NavBtn {
    background: transparent;
    color: #8a8a8a;
    border: none;
    border-left: 2px solid transparent;
    text-align: left;
    padding: 9px 14px;
    border-radius: 0;
    font-size: 13px;
}
QPushButton#NavBtn:hover {
    color: #ededed;
    background: #141414;
}
QPushButton#NavBtn:checked {
    background: #141414;
    color: #fafafa;
    border-left: 2px solid #f54e00;
}
QLabel#Brand {
    color: #fafafa;
    font-size: 15px;
    font-weight: 600;
    padding: 4px 8px 0 8px;
    letter-spacing: 0.4px;
}
QLabel#Status {
    color: #8a8a8a;
    font-size: 11px;
    padding: 0 12px 10px 12px;
}
QFrame#TopBar {
    background: #0a0a0a;
    border-bottom: 1px solid #262626;
}
QFrame#ComposerBar {
    background: #0a0a0a;
    border-top: 1px solid #262626;
}
QLabel#Title {
    color: #fafafa;
    font-size: 15px;
    font-weight: 600;
}
QLabel#Chip {
    color: #f54e00;
    font-size: 11px;
    padding: 3px 10px;
    background: #1a1a1a;
    border: 1px solid #262626;
    border-radius: 999px;
}
QLabel#Eyebrow {
    color: #8a8a8a;
    font-size: 12px;
}
QLabel#HeroTitle {
    color: #fafafa;
    font-size: 26px;
    font-weight: 600;
}
QScrollArea {
    border: none;
    background: #0a0a0a;
}
QFrame#UserBubble {
    background: #1c1c1c;
    border: 1px solid #262626;
    border-radius: 14px;
}
QFrame#BotBubble {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 14px;
}
QFrame#ToolChip {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 8px;
}
QFrame#PageCard {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 12px;
}
QTextBrowser {
    background: transparent;
    border: none;
    color: #fafafa;
    font-size: 14px;
    padding: 4px;
}
QPlainTextEdit#Composer {
    background: #141414;
    color: #fafafa;
    border: 1px solid #262626;
    border-radius: 14px;
    padding: 12px 14px;
    font-size: 14px;
    selection-background-color: #f54e00;
}
QPushButton#Send {
    background: #fafafa;
    color: #0a0a0a;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    font-size: 16px;
    font-weight: 600;
}
QPushButton#Send:hover { background: #e8e8e8; }
QPushButton#Send:disabled { background: #1a1a1a; color: #8a8a8a; }
QPushButton#Suggest {
    background: #141414;
    color: #ededed;
    border: 1px solid #262626;
    border-radius: 999px;
    padding: 8px 14px;
    font-size: 12px;
}
QPushButton#Suggest:hover {
    border-color: #f54e00;
    color: #fafafa;
}
QLineEdit, QComboBox {
    background: #141414;
    color: #fafafa;
    border: 1px solid #262626;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 20px;
}
QComboBox QAbstractItemView {
    background: #141414;
    color: #fafafa;
    selection-background-color: #262626;
    border: 1px solid #262626;
}
QPushButton#Action {
    background: transparent;
    color: #ededed;
    border: 1px solid #262626;
    border-radius: 999px;
    padding: 8px 14px;
}
QPushButton#Action:hover { border-color: #f54e00; color: #fafafa; }
QPushButton#Primary {
    background: #fafafa;
    color: #0a0a0a;
    border: none;
    border-radius: 999px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton#Primary:hover { background: #e8e8e8; }
QListWidget {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 12px;
    color: #ededed;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #262626;
}
QListWidget::item:selected { background: #1a1a1a; color: #fafafa; }
QCheckBox { spacing: 8px; color: #ededed; }
QSlider::groove:horizontal {
    height: 4px;
    background: #262626;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #f54e00;
    width: 14px;
    margin: -6px 0;
    border-radius: 7px;
}
QTextEdit#PageBody {
    background: #141414;
    color: #fafafa;
    border: 1px solid #262626;
    border-radius: 12px;
    font-size: 13px;
    padding: 16px;
}
QMenu {
    background: #141414;
    color: #ededed;
    border: 1px solid #262626;
}
QMenu::item:selected { background: #1a1a1a; }
"""
