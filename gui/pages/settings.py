# gui/pages/settings.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QPushButton, QSlider, QFormLayout, QFrame, QComboBox,
)
from PySide6.QtCore import Qt, Signal
from core.config import get, set as cfg_set


class SettingsPage(QWidget):
    model_changed = Signal(str)
    mic_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        root.addWidget(self._ai_card())
        root.addWidget(self._voice_card())
        root.addStretch(1)

    def _card(self, title: str):
        card = QFrame()
        card.setObjectName("PageCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 20, 24, 20)
        lab = QLabel(title)
        lab.setObjectName("Title")
        inner.addWidget(lab)
        return card, inner

    def _ai_card(self):
        card, inner = self._card("AI")
        form = QFormLayout()
        form.setSpacing(12)
        row = QHBoxLayout()
        self._model = QComboBox()
        self._model.setMinimumWidth(280)
        row.addWidget(self._model, 1)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("Action")
        refresh.clicked.connect(self.reload_models)
        row.addWidget(refresh)
        form.addRow("Model", row)
        inner.addLayout(form)
        hint = QLabel("Groq models available on your key. Change applies to the next message.")
        hint.setObjectName("Eyebrow")
        hint.setWordWrap(True)
        inner.addWidget(hint)
        self._model.currentIndexChanged.connect(self._save_model)
        self.reload_models()
        return card

    def reload_models(self):
        self._model.blockSignals(True)
        self._model.clear()
        try:
            from core.llm import list_groq_models
            models = list_groq_models()
        except Exception:
            models = ["qwen/qwen3.8-27b"]
        current = get("llm_model", "qwen/qwen3.8-27b")
        for m in models:
            self._model.addItem(m, m)
        idx = self._model.findData(current)
        if idx < 0:
            self._model.insertItem(0, current, current)
            idx = 0
        self._model.setCurrentIndex(max(0, idx))
        self._model.blockSignals(False)

    def _save_model(self):
        mid = self._model.currentData() or self._model.currentText()
        if mid:
            cfg_set("llm_model", mid)
            self.model_changed.emit(mid)

    def _voice_card(self):
        card, inner = self._card("Voice")
        form = QFormLayout()
        form.setSpacing(12)

        self._speak = QCheckBox("Speak replies out loud")
        self._speak.setChecked(bool(get("voice_enabled", True)))
        self._speak.toggled.connect(lambda v: cfg_set("voice_enabled", v))
        form.addRow("Speech", self._speak)

        self._mic = QCheckBox("Open microphone (wake word)")
        self._mic.setChecked(bool(get("mic_enabled", False)))
        self._mic.toggled.connect(self._save_mic)
        form.addRow("Mic", self._mic)

        self._voice = QComboBox()
        self._voice.setMinimumWidth(280)
        form.addRow("Neural voice", self._voice)

        preview = QPushButton("Preview")
        preview.setObjectName("Action")
        preview.clicked.connect(self._preview)
        form.addRow("", preview)

        self._rate = QSlider(Qt.Horizontal)
        self._rate.setRange(100, 250)
        self._rate.setValue(int(get("voice_rate", 165)))
        self._rate.valueChanged.connect(lambda v: cfg_set("voice_rate", int(v)))
        form.addRow("Rate", self._rate)

        self._wake = QLineEdit(get("wake_word", "arise"))
        save_wake = QPushButton("Save")
        save_wake.setObjectName("Action")
        save_wake.clicked.connect(lambda: cfg_set("wake_word", self._wake.text().strip() or "arise"))
        wake_row = QHBoxLayout()
        wake_row.addWidget(self._wake)
        wake_row.addWidget(save_wake)
        form.addRow("Wake word", wake_row)

        inner.addLayout(form)
        self._load_voices()
        return card

    def _load_voices(self):
        self._voice.blockSignals(True)
        self._voice.clear()
        try:
            from core.speaker import list_edge_voices
            voices = list_edge_voices()
        except Exception:
            voices = [("en-US-GuyNeural", "en-US-GuyNeural (Male)")]
        current = get("tts_voice", "en-US-GuyNeural")
        for vid, label in voices:
            self._voice.addItem(label, vid)
        idx = self._voice.findData(current)
        if idx < 0:
            self._voice.insertItem(0, current, current)
            idx = 0
        self._voice.setCurrentIndex(max(0, idx))
        self._voice.blockSignals(False)
        self._voice.currentIndexChanged.connect(self._save_voice)

    def _save_voice(self):
        vid = self._voice.currentData() or self._voice.currentText()
        if vid:
            cfg_set("tts_voice", vid)
            cfg_set("tts_engine", "edge")

    def _save_mic(self, on: bool):
        cfg_set("mic_enabled", on)
        self.mic_changed.emit(on)

    def _preview(self):
        from core.speaker import speak
        speak("Helion here. This is how I sound with the voice you picked.")
