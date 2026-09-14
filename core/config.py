# core/config.py
"""
Central config and environment loader for HELION.
"""
import os, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SETTINGS_FILE = PROJECT_ROOT / "helion_settings.json"
MEMORY_FILE   = PROJECT_ROOT / "helion_memory.json"
LOG_FILE      = PROJECT_ROOT / "helion.log"

DEFAULTS = {
    "app_name":         "HELION",
    "voice_enabled":    True,
    "voice_rate":       165,
    "voice_volume":     0.9,
    "memory_enabled":   True,
    "sprite_enabled":   True,
    "sprite_size":      140,
    "wake_word":        "arise",
    "theme":            "dark",
    "llm_model":        "claude-sonnet-4-20250514",
    "llm_max_tokens":   1024,
}

_settings: dict = {}


def load_env():
    """Load .env / apikey.env into os.environ."""
    for fname in [".env", "apikey.env", str(PROJECT_ROOT / ".env"),
                  str(PROJECT_ROOT / "apikey.env")]:
        p = Path(fname)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


def load_settings() -> dict:
    global _settings
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            _settings = {**DEFAULTS, **data}
            return _settings
        except Exception:
            pass
    _settings = dict(DEFAULTS)
    save_settings()
    return _settings


def save_settings():
    SETTINGS_FILE.write_text(
        json.dumps(_settings, indent=2), encoding="utf-8"
    )


def get(key, default=None):
    if not _settings:
        load_settings()
    return _settings.get(key, default)


def set(key, value):
    _settings[key] = value
    save_settings()


def toggle(key) -> bool:
    _settings[key] = not _settings.get(key, False)
    save_settings()
    return _settings[key]


# Load on import
load_settings()
