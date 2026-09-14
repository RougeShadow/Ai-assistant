# core/speaker.py
import threading
from core.config import get
from core.log import log

_engine = None
_lock   = threading.Lock()
_ready  = False

def _init():
    global _engine, _ready
    try:
        import pyttsx3
        _engine = pyttsx3.init()
        _engine.setProperty("rate",   get("voice_rate",   165))
        _engine.setProperty("volume", get("voice_volume", 0.9))
        _ready = True
        log.info("TTS engine ready.")
    except Exception as e:
        log.warning(f"TTS unavailable: {e}")
        _ready = False

threading.Thread(target=_init, daemon=True).start()


def speak(text: str):
    if not text or not get("voice_enabled", True):
        return

    print(f"[HELION] {text}")

    def _do():
        if not _ready or _engine is None:
            return
        with _lock:
            try:
                _engine.say(text)
                _engine.runAndWait()
            except Exception as e:
                log.warning(f"TTS error: {e}")

    threading.Thread(target=_do, daemon=True).start()
