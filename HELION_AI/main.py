# main.py
import sys

from brain.agent import start_services
from gui.sprite import HelionSprite
from core.wakeword import WakeWordListener
from core.tray import HelionTray

if __name__ == "__main__":
    start_services()

    sprite = HelionSprite()

    wake = WakeWordListener()
    wake.start()

    tray = HelionTray(on_quit=lambda: sprite.destroy())
    tray.start()

    sprite.mainloop()
