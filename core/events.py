# core/events.py
import threading

_handlers: dict[str, list] = {}
_lock = threading.Lock()

def on(event: str, fn):
    with _lock:
        _handlers.setdefault(event, []).append(fn)

def off(event: str, fn):
    with _lock:
        if event in _handlers and fn in _handlers[event]:
            _handlers[event].remove(fn)

def emit(event: str, payload=None):
    for fn in _handlers.get(event, []):
        try: fn(payload)
        except Exception: pass
