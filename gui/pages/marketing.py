# gui/pages/marketing.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QFrame,
)


class MarketingPage(QWidget):
    def __init__(self, send_to_chat, parent=None):
        super().__init__(parent)
        self._send_to_chat = send_to_chat

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 32, 28, 28)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("PageCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(14)

        title = QLabel("Write with Helion")
        title.setObjectName("Title")
        inner.addWidget(title)

        blurb = QLabel(
            "Helion will write in chat, so you can push back, change the angle, or ask for another pass."
        )
        blurb.setWordWrap(True)
        blurb.setObjectName("Eyebrow")
        inner.addWidget(blurb)

        row = QHBoxLayout()
        self._product = QLineEdit()
        self._product.setPlaceholderText("Product or brand")
        row.addWidget(self._product, 1)
        inner.addLayout(row)

        row2 = QHBoxLayout()
        self._kind = QComboBox()
        self._kind.addItems(["tagline", "ad_copy", "social_post", "email", "pitch", "slogan"])
        self._tone = QComboBox()
        self._tone.addItems(["bold", "luxury", "playful", "urgent", "minimal", "witty", "professional"])
        row2.addWidget(QLabel("Type"))
        row2.addWidget(self._kind)
        row2.addWidget(QLabel("Tone"))
        row2.addWidget(self._tone)
        row2.addStretch(1)
        inner.addLayout(row2)

        go = QPushButton("Talk it through in chat")
        go.setObjectName("Primary")
        go.setCursor(Qt.PointingHandCursor)
        go.clicked.connect(self._go)
        inner.addWidget(go)
        root.addWidget(card)
        root.addStretch(1)

    def _go(self):
        product = self._product.text().strip()
        if not product:
            return
        kind = self._kind.currentText()
        tone = self._tone.currentText()
        prompt = (
            f"Write {kind.replace('_', ' ')} for {product}. "
            f"Keep the tone {tone}. Talk to me like we're working on it together — "
            f"give me the copy, then a sentence on why it works."
        )
        self._send_to_chat(prompt)
