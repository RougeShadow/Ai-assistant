# core/state.py
import threading
from enum import Enum

class State(str, Enum):
    IDLE      = "idle"
    LISTENING = "listening"
    THINKING  = "thinking"
    SPEAKING  = "speaking"
    WORKING   = "working"
    SLEEPING  = "sleeping"
    WAKING    = "waking"
    ERROR     = "error"

_state = State.IDLE
_lock  = threading.Lock()
_listeners: list = []

def get() -> State:
    return _state

def set(new: State):
    global _state
    with _lock:
        _state = new
    for cb in _listeners:
        try: cb(new)
        except Exception: pass

def subscribe(fn):
    _listeners.append(fn)

def unsubscribe(fn):
    if fn in _listeners:
        _listeners.remove(fn)
