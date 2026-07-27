# core/state.py
import threading

_STATE = "idle"
_STATE_LOCK = threading.Lock()
_LISTENERS = []

def set_state(state: str):
    global _STATE
    with _STATE_LOCK:
        _STATE = state
    for cb in _LISTENERS:
        try:
            cb(state)
        except Exception:
            pass

def get_state():
    return _STATE

def subscribe(callback):
    _LISTENERS.append(callback)
