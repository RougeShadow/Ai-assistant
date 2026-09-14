# core/wakeword.py
"""
Background wake word listener.
Listens for the configured wake word and brings the app forward.
"""
import threading, time
from core.config import get
from core.log import log

_show_fn = None
_active = False
_thread = None


def set_show_callback(fn):
    global _show_fn
    _show_fn = fn


def set_root(root):
    """Legacy tkinter hook — ignored by the Qt app."""
    _ = root


def start():
    global _active, _thread
    if not get("voice_enabled", True):
        return

    _active = True
    _thread = threading.Thread(target=_listen_loop, daemon=True)
    _thread.start()
    log.info("Wake word listener started.")


def stop():
    global _active
    _active = False


def _listen_loop():
    try:
        import speech_recognition as sr
    except ImportError:
        log.warning("speech_recognition not installed — wake word disabled.")
        log.warning("Run: pip install SpeechRecognition pyaudio")
        return

    wake_word = get("wake_word", "arise").lower()
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    try:
        mic = sr.Microphone()
    except Exception as e:
        log.warning(f"Microphone not available: {e}")
        return

    log.info(f"Listening for wake word: '{wake_word}'")

    with mic as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception:
            pass

    while _active:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=3)

            text = recognizer.recognize_google(audio).lower()
            log.debug(f"Heard: {text}")

            if wake_word in text:
                log.info("Wake word detected!")
                _on_wake()

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            log.debug(f"Wake word loop error: {e}")
            time.sleep(1)


def _on_wake():
    from core import state
    from core.state import State
    from core.speaker import speak
    state.set(State.LISTENING)
    speak("I'm here.")
    if _show_fn is not None:
        try:
            _show_fn()
        except Exception as e:
            log.error(f"Failed to show window: {e}")
