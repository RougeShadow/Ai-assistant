# core/settings.py
import json
import os
import threading
from datetime import datetime

SETTINGS_FILE = "helion_settings.json"
SETTINGS_LOCK = threading.Lock()

# ============================================================
# DEFAULT SETTINGS (ORION v5 STYLE)
# ============================================================

DEFAULT_SETTINGS = {
    "app_name": "HELION",
    "persona": "A calm, capable, loyal AI assistant.",
    "voice_enabled": True,
    "automation_enabled": False,
    "web_enabled": False,
    "memory_enabled": True,
    "safe_mode": True,
    "ui_theme": "dark",
    "sprite_enabled": True,
    "scheduler_enabled": True,
    "logging": True,
    "created": datetime.utcnow().isoformat(),
}

# ============================================================
# LOAD / SAVE SETTINGS
# ============================================================

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================

SETTINGS = load_settings()

# ============================================================
# ACCESSORS (USED BY ORION CORE)
# ============================================================

def get_setting(key, default=None):
    return SETTINGS.get(key, default)

def set_setting(key, value):
    with SETTINGS_LOCK:
        SETTINGS[key] = value
        save_settings(SETTINGS)

def toggle_setting(key):
    with SETTINGS_LOCK:
        SETTINGS[key] = not SETTINGS.get(key, False)
        save_settings(SETTINGS)
        return SETTINGS[key]
