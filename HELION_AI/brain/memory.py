# brain/memory.py
import json
import os
import threading
import time
from datetime import datetime
from cryptography.fernet import Fernet

# ============================================================
# FILES & LOCKS
# ============================================================

MEMORY_FILE = "helion_memory.enc"
BACKUP_DIR = "memory_backups"
KEY_FILE = "helion.key"

MEMORY_LOCK = threading.Lock()

# ============================================================
# ENCRYPTION SETUP (ORION v5 STYLE)
# ============================================================

def _load_or_create_key():
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE, "rb").read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

FERNET = Fernet(_load_or_create_key())

# ============================================================
# DEFAULT MEMORY STRUCTURE
# ============================================================

def _default_memory():
    return {
        "facts": {},
        "episodic": [],
        "journal": [],
        "preferences": {},
        "consent": {
            "automation": False,
            "web": False,
            "memory": True,
        },
        "created": datetime.utcnow().isoformat(),
        "updated": datetime.utcnow().isoformat(),
    }

# ============================================================
# LOAD / SAVE
# ============================================================

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return _default_memory()

    try:
        encrypted = open(MEMORY_FILE, "rb").read()
        decrypted = FERNET.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))
    except Exception:
        return _default_memory()

def save_memory(mem):
    mem["updated"] = datetime.utcnow().isoformat()
    raw = json.dumps(mem, indent=2).encode("utf-8")
    encrypted = FERNET.encrypt(raw)
    with open(MEMORY_FILE, "wb") as f:
        f.write(encrypted)

# ============================================================
# GLOBAL MEMORY INSTANCE
# ============================================================

MEMORY = load_memory()

# ============================================================
# BACKUPS (ORION v5 FEATURE)
# ============================================================

def backup_memory():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"memory_{ts}.enc")
    try:
        with open(path, "wb") as f:
            f.write(open(MEMORY_FILE, "rb").read())
    except Exception:
        pass

# ============================================================
# MEMORY WRITE HELPERS
# ============================================================

def add_fact(key, value):
    with MEMORY_LOCK:
        MEMORY["facts"][key] = value
        save_memory(MEMORY)

def add_episodic(event, meta=None):
    with MEMORY_LOCK:
        MEMORY["episodic"].append({
            "time": datetime.utcnow().isoformat(),
            "event": event,
            "meta": meta or {},
        })
        save_memory(MEMORY)

def add_journal(entry):
    with MEMORY_LOCK:
        MEMORY["journal"].append({
            "time": datetime.utcnow().isoformat(),
            "entry": entry,
        })
        save_memory(MEMORY)

def set_preference(key, value):
    with MEMORY_LOCK:
        MEMORY["preferences"][key] = value
        save_memory(MEMORY)

# ============================================================
# CONSENT SYSTEM (ORION v5 SAFETY)
# ============================================================

def has_consent(area):
    return MEMORY.get("consent", {}).get(area, False)

def set_consent(area, value: bool):
    with MEMORY_LOCK:
        MEMORY["consent"][area] = value
        save_memory(MEMORY)

# ============================================================
# READ HELPERS
# ============================================================

def get_fact(key, default=None):
    return MEMORY["facts"].get(key, default)

def get_preferences():
    return MEMORY.get("preferences", {})

def get_journal(limit=10):
    return MEMORY["journal"][-limit:]

def get_episodic(limit=10):
    return MEMORY["episodic"][-limit:]

# ============================================================
# PERIODIC BACKUP LOOP (USED BY EVENTS)
# ============================================================

def backup_loop(interval=600):
    while True:
        time.sleep(interval)
        backup_memory()
