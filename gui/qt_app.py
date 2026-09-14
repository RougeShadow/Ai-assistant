# gui/qt_app.py
"""Helion desktop shell — PySide6 main window + tray."""
import sys

from PySide6.QtCore import Qt, QSize, Slot, QMetaObject
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSystemTrayIcon, QMenu,
)

from gui.theme import STYLESHEET, hex_icon
from gui.chat_view import ChatView
from gui.pages.stocks import StocksPage
from gui.pages.notes import NotesPage
from gui.pages.settings import SettingsPage
from gui.pages.marketing import MarketingPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helion")
        self.setMinimumSize(QSize(960, 620))
        self.resize(1100, 720)
        icon = hex_icon()
        self.setWindowIcon(icon)

        root = QWidget()
        root.setObjectName("HelionRoot")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("Nav")
        nav.setFixedWidth(168)
        nav_l = QVBoxLayout(nav)
        nav_l.setContentsMargins(10, 16, 10, 12)
        nav_l.setSpacing(2)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        mark = QLabel()
        mark.setPixmap(icon.pixmap(22, 22))
        brand_row.addWidget(mark)
        brand = QLabel("Helion")
        brand.setObjectName("Brand")
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        nav_l.addLayout(brand_row)
        self._status = QLabel("Ready")
        self._status.setObjectName("Status")
        nav_l.addWidget(self._status)
        nav_l.addSpacing(8)

        self._stack = QStackedWidget()
        self._chat = ChatView()
        self._chat.status_changed.connect(self._set_status)
        self._stocks = StocksPage()
        self._notes = NotesPage()
        self._marketing = MarketingPage(self._send_marketing)
        self._settings = SettingsPage()

        self._stack.addWidget(self._chat)
        self._stack.addWidget(self._stocks)
        self._stack.addWidget(self._marketing)
        self._stack.addWidget(self._notes)
        self._stack.addWidget(self._settings)

        self._nav_btns = []
        for i, label in enumerate(["Chat", "Stocks", "Marketing", "Notes", "Settings"]):
            btn = QPushButton(label)
            btn.setObjectName("NavBtn")
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda _=False, idx=i: self._goto(idx))
            nav_l.addWidget(btn)
            self._nav_btns.append(btn)
        nav_l.addStretch(1)

        layout.addWidget(nav)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        top = QFrame()
        top.setObjectName("TopBar")
        top.setFixedHeight(44)
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(24, 0, 24, 0)
        self._title = QLabel("Chat")
        self._title.setObjectName("Title")
        top_l.addWidget(self._title)
        top_l.addStretch(1)
        self._chip = QLabel("Ready")
        self._chip.setObjectName("Chip")
        top_l.addWidget(self._chip)
        right.addWidget(top)
        right.addWidget(self._stack, 1)
        layout.addLayout(right, 1)

        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._chat.clear_chat)
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self._goto(0))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self._goto(1))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self._goto(2))
        QShortcut(QKeySequence("Ctrl+4"), self, activated=lambda: self._goto(3))
        QShortcut(QKeySequence("Ctrl+5"), self, activated=lambda: self._goto(4))

        self._tray = None
        self._setup_tray()

    def _send_marketing(self, prompt: str):
        self._goto(0)
        self._chat.send_text(prompt)

    def _goto(self, idx: int):
        self._stack.setCurrentIndex(idx)
        names = ["Chat", "Stocks", "Marketing", "Notes", "Settings"]
        self._title.setText(names[idx])
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)
        if idx == 1:
            self._stocks.refresh()
        elif idx == 3:
            self._notes.refresh()

    def _set_status(self, text: str):
        self._status.setText(text)
        self._chip.setText(text)

    def _setup_tray(self):
        icon = hex_icon()
        tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        show = QAction("Open Helion", self)
        show.triggered.connect(self.bring_forward)
        voice = QAction("Toggle voice", self)
        voice.triggered.connect(self._toggle_voice)
        quit_a = QAction("Quit", self)
        quit_a.triggered.connect(QApplication.instance().quit)
        menu.addAction(show)
        menu.addAction(voice)
        menu.addSeparator()
        menu.addAction(quit_a)
        tray.setContextMenu(menu)
        tray.setToolTip("Helion")
        tray.activated.connect(self._tray_activated)
        tray.show()
        self._tray = tray

    def _toggle_voice(self):
        from core.config import toggle
        on = toggle("voice_enabled")
        self._set_status("Voice on" if on else "Voice off")

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.bring_forward()

    @Slot()
    def bring_forward(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        if self._tray:
            self._tray.showMessage("Helion", "Still running in the tray.", QSystemTrayIcon.Information, 2000)


def run_app():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Helion")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLESHEET)

    win = MainWindow()
    win.show()

    from core import wakeword

    def _show():
        QMetaObject.invokeMethod(win, "bring_forward", Qt.QueuedConnection)

    wakeword.set_show_callback(_show)
    wakeword.start()

    return app.exec()
