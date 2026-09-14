# gui/chat_view.py
"""Centered conversation + pill composer."""
import html
import re
import threading

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPlainTextEdit, QPushButton, QTextBrowser,
)

from gui.theme import C, hex_pixmap


def _md_lite(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"`([^`]+)`",
        r"<code style='background:#1a1a1a;padding:1px 4px;border-radius:4px;color:#ededed;'>\1</code>",
        escaped,
    )
    escaped = re.sub(r"^[-*] (.+)$", r"• \1", escaped, flags=re.M)
    return escaped.replace("\n", "<br>")


class ChatWorker(QThread):
    token = Signal(str)
    tool = Signal(str, str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text

    def run(self):
        from brain.agent import process
        try:
            result = process(
                self._text,
                on_token=lambda t: self.token.emit(t),
                on_tool=lambda n, p: self.tool.emit(n, p or ""),
            )
            self.finished_ok.emit(result or "")
        except Exception as e:
            self.failed.emit(str(e))


class Composer(QPlainTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            event.accept()
            self.send_requested.emit()
            return
        super().keyPressEvent(event)


class ChatView(QWidget):
    status_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._busy = False
        self._worker = None
        self._stream_browser = None
        self._stream_raw = ""
        self._empty = None
        self._build()

    def _column(self, child: QWidget) -> QWidget:
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        child.setMaximumWidth(720)
        row.addWidget(child, 1)
        row.addStretch(1)
        return wrap

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._inner = QWidget()
        self._msgs = QVBoxLayout(self._inner)
        self._msgs.setContentsMargins(24, 28, 24, 16)
        self._msgs.setSpacing(12)
        self._empty = self._welcome()
        self._msgs.addWidget(self._column(self._empty))
        self._msgs.addStretch(1)
        self._scroll.setWidget(self._inner)
        root.addWidget(self._scroll, 1)

        bar = QFrame()
        bar.setObjectName("ComposerBar")
        bar_l = QVBoxLayout(bar)
        bar_l.setContentsMargins(24, 14, 24, 18)
        composer_wrap = QWidget()
        composer_wrap.setMaximumWidth(720)
        row = QHBoxLayout(composer_wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._composer = Composer()
        self._composer.setObjectName("Composer")
        self._composer.setPlaceholderText("Ask Helion anything…  Enter to send")
        self._composer.setFixedHeight(52)
        self._composer.send_requested.connect(self.submit)
        row.addWidget(self._composer, 1)

        self._send = QPushButton("↑")
        self._send.setObjectName("Send")
        self._send.setCursor(Qt.PointingHandCursor)
        self._send.clicked.connect(self.submit)
        row.addWidget(self._send, 0, Qt.AlignVCenter)

        outer = QHBoxLayout()
        outer.addStretch(1)
        outer.addWidget(composer_wrap, 1)
        outer.addStretch(1)
        bar_l.addLayout(outer)
        root.addWidget(bar)

    def _welcome(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setAlignment(Qt.AlignHCenter)
        lay.setSpacing(12)
        art = QLabel()
        art.setAlignment(Qt.AlignCenter)
        pix = hex_pixmap(320)
        if not pix.isNull():
            art.setPixmap(pix)
        lay.addWidget(art)
        eyebrow = QLabel("Helion")
        eyebrow.setObjectName("Eyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        lay.addWidget(eyebrow)
        title = QLabel("What's on your mind?")
        title.setObjectName("HeroTitle")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        chips = QHBoxLayout()
        chips.setAlignment(Qt.AlignCenter)
        for label, prompt in (
            ("Write a pitch", "Write a short pitch for HELION."),
            ("Check BTC", "What's BTC doing right now?"),
            ("My notes", "What notes do I have saved?"),
        ):
            b = QPushButton(label)
            b.setObjectName("Suggest")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, p=prompt: self.send_text(p))
            chips.addWidget(b)
        lay.addLayout(chips)
        return box

    def _hide_empty(self):
        if self._empty:
            self._empty.hide()

    def clear_chat(self):
        while self._msgs.count() > 1:
            item = self._msgs.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        from core.memory import clear_history
        clear_history()
        self._empty = self._welcome()
        self._msgs.insertWidget(0, self._column(self._empty))

    def send_text(self, text: str):
        self._composer.setPlainText(text)
        self.submit()

    def submit(self):
        if self._busy:
            return
        text = self._composer.toPlainText().strip()
        if not text:
            return
        self._hide_empty()
        self._composer.clear()
        self.add_user(text)
        self._busy = True
        self._send.setEnabled(False)
        self.status_changed.emit("Thinking…")
        self._stream_raw = ""
        self._stream_browser = self._start_bot_stream()

        self._worker = ChatWorker(text, self)
        self._worker.token.connect(self._on_token)
        self._worker.tool.connect(self._on_tool)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def add_user(self, text: str):
        self._add_bubble(text, user=True)

    def add_bot(self, text: str):
        self._add_bubble(text, user=False)

    def _add_bubble(self, text: str, user: bool):
        bubble = QFrame()
        bubble.setObjectName("UserBubble" if user else "BotBubble")
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        cap = QLabel("You" if user else "Helion")
        cap.setStyleSheet(
            f"color: {C['text_dim'] if user else C['accent']}; font-size: 11px; letter-spacing: 0.4px;"
        )
        inner.addWidget(cap)
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(_md_lite(text))
        body.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body.document().contentsChanged.connect(lambda b=body: self._fit_browser(b))
        inner.addWidget(body)
        self._fit_browser(body)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if user:
            row.addStretch(1)
            row.addWidget(bubble, 0, Qt.AlignRight)
        else:
            row.addWidget(bubble, 0, Qt.AlignLeft)
            row.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(row)
        wrap.setMaximumWidth(720)
        self._msgs.insertWidget(self._msgs.count() - 1, self._column(wrap))
        self._scroll_bottom()
        return body

    def _start_bot_stream(self):
        bubble = QFrame()
        bubble.setObjectName("BotBubble")
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        cap = QLabel("Helion · …")
        cap.setObjectName("thinkingCap")
        cap.setStyleSheet(f"color: {C['accent']}; font-size: 11px; letter-spacing: 0.4px;")
        inner.addWidget(cap)
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml("<span style='color:#8a8a8a'>Thinking…</span>")
        body.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body.document().contentsChanged.connect(lambda: self._fit_browser(body))
        inner.addWidget(body)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(bubble, 0, Qt.AlignLeft)
        row.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(row)
        wrap.setMaximumWidth(720)
        wrap._cap = cap
        self._msgs.insertWidget(self._msgs.count() - 1, self._column(wrap))
        self._scroll_bottom()
        return body

    def _fit_browser(self, browser: QTextBrowser):
        doc = browser.document()
        h = int(doc.size().height()) + 8
        browser.setFixedHeight(max(28, min(h, 480)))

    def _on_token(self, token: str):
        self._stream_raw += token
        if self._stream_browser:
            self._stream_browser.setHtml(_md_lite(self._stream_raw))
            self._scroll_bottom()

    def _on_tool(self, name: str, preview: str):
        self.status_changed.emit(f"Using {name}…")
        label = name.replace("_", " ")
        if preview:
            label = f"{label} · {preview[:48]}"
        chip = QFrame()
        chip.setObjectName("ToolChip")
        lay = QHBoxLayout(chip)
        lay.setContentsMargins(10, 6, 10, 6)
        t = QLabel(f"Looking that up — {label}")
        t.setStyleSheet(f"color: {C['text_dim']}; font-size: 12px;")
        lay.addWidget(t)
        wrap = QWidget()
        wrap.setMaximumWidth(720)
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(chip)
        row.addStretch(1)
        self._msgs.insertWidget(self._msgs.count() - 1, self._column(wrap))
        self._scroll_bottom()

    def _on_done(self, response: str):
        if not self._stream_raw and response:
            self._stream_raw = response
            if self._stream_browser:
                self._stream_browser.setHtml(_md_lite(response))
        elif not self._stream_raw and not response:
            if self._stream_browser:
                self._stream_browser.setHtml(_md_lite("All set."))
        self._busy = False
        self._send.setEnabled(True)
        self.status_changed.emit("Ready")
        self._maybe_speak(self._stream_raw or response)
        self._scroll_bottom()

    def _on_fail(self, err: str):
        if self._stream_browser:
            self._stream_browser.setHtml(_md_lite(f"That didn't go through: {err}"))
        self._busy = False
        self._send.setEnabled(True)
        self.status_changed.emit("Ready")

    def _maybe_speak(self, text: str):
        from core.config import get
        if not get("voice_enabled", True) or not text:
            return
        parts = text.split(". ")
        spoken = ". ".join(parts[:2])
        if len(spoken) > 220:
            spoken = spoken[:220] + "…"

        def _go():
            try:
                from core.speaker import speak
                speak(spoken)
            except Exception:
                pass

        threading.Thread(target=_go, daemon=True).start()

    def _scroll_bottom(self):
        def _go():
            bar = self._scroll.verticalScrollBar()
            bar.setValue(bar.maximum())
        QTimer.singleShot(0, _go)
