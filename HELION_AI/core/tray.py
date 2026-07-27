# core/tray.py
import threading
import sys
from PIL import Image
import pystray

from core.state import set_state
from core.settings import set_setting, get_setting

class HelionTray:
    def __init__(self, on_quit):
        self.on_quit = on_quit
        self.icon = None

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

        menu = pystray.Menu(
            pystray.MenuItem(
                "Mute Mic",
                self.toggle_mic,
                checked=lambda _: get_setting("mic_enabled", True)
            ),
            pystray.MenuItem(
                "Sleep",
                self.sleep
            ),
            pystray.MenuItem(
                "Wake",
                self.wake
            ),
            pystray.MenuItem(
                "Quit Helion",
                self.quit
            )
        )

        self.icon = pystray.Icon(
            "Helion",
            image,
            "Helion AI",
            menu
        )
        self.icon.run()

    # ---------------- MENU ACTIONS ----------------

    def toggle_mic(self):
        current = get_setting("mic_enabled", True)
        set_setting("mic_enabled", not current)

    def sleep(self):
        set_state("sleeping")

    def wake(self):
        set_state("waking")

    def quit(self):
        if self.icon:
            self.icon.stop()
        self.on_quit()
        sys.exit(0)
