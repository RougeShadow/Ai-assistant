# core/speaker.py
import threading
import pyttsx3

_engine = None
_engine_lock = threading.Lock()

def _init_engine():
    global _engine
    try:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
    except Exception:
        _engine = None

_init_engine()

def speak(text: str):
    """
    Non-blocking TTS speaker.
    Matches Orion v5 behavior.
    """
    if not text:
        return

    print(f"[HELION] {text}")

    if _engine is None:
        return

    def _speak():
        with _engine_lock:
            try:
                _engine.say(text)
                _engine.runAndWait()
            except Exception:
                pass

    threading.Thread(target=_speak, daemon=True).start()
