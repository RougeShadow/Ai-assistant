# gui/app.py
"""
HelionApp — wires together the sprite, popup, wakeword, and tray.
"""
import tkinter as tk
from core.log import log
from core.config import get


class HelionApp:
    def __init__(self):
        self._root   = None
        self._sprite = None
        self._tray   = None

    def run(self):
        if get("sprite_enabled", True):
            self._run_with_sprite()
        else:
            self._run_headless()

    def _run_with_sprite(self):
        from gui.sprite import HelionSprite
        from core import wakeword

        sprite = HelionSprite()
        self._sprite = sprite
        self._root   = sprite       # sprite IS the tk root

        # Wire wake word to sprite window
        wakeword.set_root(sprite)
        wakeword.start()

        # System tray
        self._start_tray(sprite)

        log.info("HELION ready. Click the sprite or say the wake word.")
        sprite.mainloop()

    def _run_headless(self):
        """No sprite — just tray icon and popup."""
        from core import wakeword

        root = tk.Tk()
        root.withdraw()
        self._root = root

        wakeword.set_root(root)
        wakeword.start()
        self._start_tray(root)

        from gui.popup import open_popup
        open_popup(root)

        log.info("HELION ready (headless mode).")
        root.mainloop()

    def _start_tray(self, root):
        try:
            from gui.tray import HelionTray
            tray = HelionTray(root)
            tray.start()
            self._tray = tray
        except Exception as e:
            log.warning(f"Tray icon unavailable: {e}")
