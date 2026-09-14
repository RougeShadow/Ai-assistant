# core/events.py
import threading
import time
from datetime import datetime

from brain.memory import backup_memory
from core.settings import get_setting

# ============================================================
# EVENT REGISTRY
# ============================================================

_EVENT_HANDLERS = {}
_EVENT_LOCK = threading.Lock()

# ============================================================
# EVENT BUS (ORION v5 STYLE)
# ============================================================

def on_event(event_name, handler):
    """
    Register a handler for a named event.
    """
    with _EVENT_LOCK:
        _EVENT_HANDLERS.setdefault(event_name, []).append(handler)

def publish_event(event_name, payload=None):
    """
    Publish an event to all registered handlers.
    """
    handlers = _EVENT_HANDLERS.get(event_name, [])
    for h in handlers:
        try:
            h(payload)
        except Exception:
            pass

# ============================================================
# SCHEDULER LOOP
# ============================================================

def scheduler_loop():
    """
    Background loop that drives periodic system tasks.
    Matches Orion v5 behavior.
    """
    last_backup = time.time()

    while True:
        time.sleep(1)

        now = time.time()

        # periodic memory backup
        if now - last_backup >= 600:  # 10 minutes
            if get_setting("memory_enabled", True):
                backup_memory()
            last_backup = now

        # heartbeat event (used by planner, monitoring, etc.)
        publish_event("heartbeat", {
            "time": datetime.utcnow().isoformat()
        })

# ============================================================
# START EVENTS
# ============================================================

def start_event_loop():
    """
    Starts the scheduler in a daemon thread.
    """
    if not get_setting("scheduler_enabled", True):
        return

    t = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )
    t.start()
