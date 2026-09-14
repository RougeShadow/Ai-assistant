# gui/popup.py
import tkinter as tk
from brain.agent import handle_input
from core.speaker import speak

BG = "#000000"
FG = "#ffffff"

class CommandPopup(tk.Toplevel):
    def __init__(self, parent, initial_text=None):
        super().__init__(parent)

        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.geometry("420x180")
        self.title("Helion")

        self.entry = tk.Entry(
            self,
            bg="#111111",
            fg=FG,
            insertbackground=FG,
            font=("Segoe UI", 12),
            relief="flat"
        )
        self.entry.pack(padx=12, pady=(12, 6), fill="x")
        self.entry.focus()

        self.output = tk.Label(
            self,
            text="",
            bg=BG,
            fg=FG,
            wraplength=380,
            justify="left",
            font=("Segoe UI", 10)
        )
        self.output.pack(padx=12, pady=(4, 12), fill="x")

        if initial_text:
            self.set_output(initial_text)

        self.entry.bind("<Return>", self.process)
        self.bind("<Escape>", lambda e: self.destroy())

    def set_output(self, text):
        print("[POPUP OUTPUT]", text)
        self.output.config(text=text)
        speak(text)

    def process(self, event=None):
        query = self.entry.get().strip()
        if not query:
            return

        print("[POPUP QUERY]", query)
        self.entry.delete(0, tk.END)

        response = handle_input(query)

        if response:
            self.set_output(response)
