# gui/tray.py
import threading, sys
from core.log import log
from core.config import get, toggle


class HelionTray:
    def __init__(self, root):
        self._root = root
        self._icon = None

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            from PIL import Image, ImageDraw
            import pystray

            # Build a simple teal circle icon
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill="#00d4aa")
            draw.ellipse([22, 22, 42, 42], fill="black")

            def _open(_):
                from gui.popup import open_popup
                self._root.after(0, lambda: open_popup(self._root))

            def _toggle_voice(_):
                toggle("voice_enabled")

            def _quit(_):
                if self._icon:
                    self._icon.stop()
                self._root.after(0, self._root.quit)
                sys.exit(0)

            menu = pystray.Menu(
                pystray.MenuItem("Open HELION",    _open),
                pystray.MenuItem("Toggle Voice",   _toggle_voice),
                pystray.MenuItem("Quit",           _quit),
            )

            self._icon = pystray.Icon("HELION", img, "HELION", menu)
            self._icon.run()

        except ImportError:
            log.warning("pystray/PIL not installed — tray icon disabled.")
        except Exception as e:
            log.warning(f"Tray error: {e}")
