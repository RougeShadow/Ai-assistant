# gui/pages/notes.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QLabel,
)


class NotesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Notes")
        title.setObjectName("Title")
        root.addWidget(title)

        bar = QHBoxLayout()
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Quick note…")
        self._entry.returnPressed.connect(self.add_note)
        bar.addWidget(self._entry, 1)
        btn = QPushButton("Add note")
        btn.setObjectName("Primary")
        btn.clicked.connect(self.add_note)
        bar.addWidget(btn)
        root.addLayout(bar)

        hint = QLabel("Helion can also save notes from chat — just ask.")
        hint.setObjectName("Eyebrow")
        root.addWidget(hint)

        self._list = QListWidget()
        root.addWidget(self._list, 1)
        self.refresh()

    def add_note(self):
        text = self._entry.text().strip()
        if not text:
            return
        from core.memory import add_note
        add_note(text)
        self._entry.clear()
        self.refresh()

    def refresh(self):
        from core.memory import get_notes
        self._list.clear()
        notes = get_notes(50)
        if not notes:
            self._list.addItem("No notes yet.")
            return
        for note in reversed(notes):
            ts = (note.get("ts") or "")[:10]
            self._list.addItem(f"{ts}  {note.get('text', '')}")
