# core/services.py
"""
Starts all HELION background services.
"""
import threading
from core.log import log


def start_all():
    _start_reminder_loop()
    log.info("Background services started.")


def _start_reminder_loop():
    def _loop():
        import time
        from core.memory import get_pending_reminders, mark_reminder_done
        from core.speaker import speak
        while True:
            time.sleep(30)
            try:
                pending = get_pending_reminders()
                for i, r in enumerate(pending):
                    speak(f"Reminder: {r['text']}")
                    mark_reminder_done(i)
            except Exception:
                pass

    threading.Thread(target=_loop, daemon=True).start()
