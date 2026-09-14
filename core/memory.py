# core/memory.py
"""
Persistent memory: history, facts, notes, reminders, portfolio.
"""
import json, threading
from datetime import datetime
from core.config import MEMORY_FILE
from core.log import log

_lock = threading.Lock()

def _default():
    return {
        "history": [],
        "facts": {},
        "notes": [],
        "reminders": [],
        "portfolio": [],
        "created": _now(),
        "updated": _now(),
    }

def _now():
    return datetime.utcnow().isoformat()

def _load():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _default()

def _save(mem):
    mem["updated"] = _now()
    MEMORY_FILE.write_text(json.dumps(mem, indent=2), encoding="utf-8")

_mem = _load()

# Ensure portfolio key exists in older memory files
if "portfolio" not in _mem:
    _mem["portfolio"] = []

# ── History ────────────────────────────────────────────────

def push(role: str, content: str):
    with _lock:
        _mem["history"].append({"role": role, "content": content, "ts": _now()})
        if len(_mem["history"]) > 200:
            _mem["history"] = _mem["history"][-200:]
        _save(_mem)

def history(n=20) -> list:
    raw = _mem["history"][-n:]
    return [{"role": m["role"], "content": m["content"]} for m in raw]

def clear_history():
    with _lock:
        _mem["history"] = []
        _save(_mem)

# ── Facts ──────────────────────────────────────────────────

def remember(key: str, value):
    with _lock:
        _mem["facts"][key] = value
        _save(_mem)

def recall(key: str, default=None):
    return _mem.get("facts", {}).get(key, default)

# ── Notes ──────────────────────────────────────────────────

def add_note(text: str):
    with _lock:
        _mem["notes"].append({"text": text, "ts": _now()})
        _save(_mem)

def get_notes(n=10) -> list:
    return _mem["notes"][-n:]

# ── Portfolio ──────────────────────────────────────────────

def add_to_portfolio(symbol: str):
    symbol = symbol.upper().strip()
    with _lock:
        if symbol not in _mem.get("portfolio", []):
            _mem.setdefault("portfolio", []).append(symbol)
            _save(_mem)
    return symbol

def remove_from_portfolio(symbol: str):
    symbol = symbol.upper().strip()
    with _lock:
        p = _mem.get("portfolio", [])
        if symbol in p:
            p.remove(symbol)
        _save(_mem)

def get_portfolio_symbols() -> list:
    return list(_mem.get("portfolio", []))

# ── Reminders ──────────────────────────────────────────────

def add_reminder(text: str, trigger_ts: str):
    with _lock:
        _mem["reminders"].append({"text": text, "trigger": trigger_ts, "done": False})
        _save(_mem)

def get_pending_reminders() -> list:
    now = _now()
    return [r for r in _mem.get("reminders", []) if not r["done"] and r["trigger"] <= now]

def mark_reminder_done(idx: int):
    with _lock:
        pending = get_pending_reminders()
        if idx < len(pending):
            pending[idx]["done"] = True
            _save(_mem)
