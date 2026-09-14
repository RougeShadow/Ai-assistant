# gui/pages/settings.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QPushButton, QSlider, QFormLayout, QFrame,
)
from PySide6.QtCore import Qt
from core.config import get, set as cfg_set


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 32, 28, 28)

        card = QFrame()
        card.setObjectName("PageCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Settings")
        title.setObjectName("Title")
        inner.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self._voice = QCheckBox("Speak replies out loud")
        self._voice.setChecked(bool(get("voice_enabled", True)))
        self._voice.toggled.connect(lambda v: cfg_set("voice_enabled", v))
        form.addRow("Voice", self._voice)

        self._wake = QLineEdit(get("wake_word", "arise"))
        save_wake = QPushButton("Save")
        save_wake.setObjectName("Action")
        save_wake.clicked.connect(lambda: cfg_set("wake_word", self._wake.text().strip() or "arise"))
        wake_row = QHBoxLayout()
        wake_row.addWidget(self._wake)
        wake_row.addWidget(save_wake)
        form.addRow("Wake word", wake_row)

        self._rate = QSlider(Qt.Horizontal)
        self._rate.setRange(100, 250)
        self._rate.setValue(int(get("voice_rate", 165)))
        self._rate.valueChanged.connect(lambda v: cfg_set("voice_rate", int(v)))
        form.addRow("Voice rate", self._rate)

        inner.addLayout(form)

        provider = get("llm_provider", "groq")
        model_name = get("llm_model", "llama-3.1-8b-instant")
        model = QLabel(f"Provider: {provider} · Model: {model_name}")
        model.setObjectName("Eyebrow")
        inner.addWidget(model)
        ver = QLabel("Helion — desktop")
        ver.setObjectName("Eyebrow")
        inner.addWidget(ver)
        root.addWidget(card)
        root.addStretch(1)
