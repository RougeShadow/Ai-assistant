# core/wakeword.py
import threading
import time
from core.state import set_state
import speech_recognition as sr

from brain.agent import route_query
from core.speaker import speak

WAKE_WORD = "arise"
EXIT_WORDS = ["sleep", "stop listening", "go idle"]
CONFIRM_WORDS = ["yes", "confirm", "do it", "go ahead"]
CANCEL_WORDS = ["no", "cancel", "don't", "stop"]

class WakeWordListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.active = True
        self.conversation_active = False

    def start(self):
        t = threading.Thread(target=self._listen_loop, daemon=True)
        t.start()

    # ---------------------------------------------------------
    # MAIN LISTEN LOOP
    # ---------------------------------------------------------

    def _listen_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        speak("Voice listener ready.")

        while self.active:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=4
                    )

                text = self.recognizer.recognize_google(audio).lower()
                print("[WAKE]", text)

                if WAKE_WORD in text:
                    print("[WAKE WORD DETECTED]")

                    from core.state import set_state
                    from gui.popup import CommandPopup

                    set_state("listen")

    # Open popup and prompt user
                    self.root.after(
                        0,
                        lambda: CommandPopup(
                            self.root,
                            initial_text="I'm awake. What do you need?"
                        )
                    )



            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception:
                time.sleep(1)

    # ---------------------------------------------------------
    # CONVERSATION MODE WITH CONFIRMATION
    # ---------------------------------------------------------

    def _conversation_mode(self):
        self.conversation_active = True
        speak("I'm listening.")

        idle_timer = time.time()

        while self.conversation_active:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=6,
                        phrase_time_limit=8
                    )

                command = self.recognizer.recognize_google(audio).lower()
                print("[COMMAND]", command)

                idle_timer = time.time()

                # exit
                if any(x in command for x in EXIT_WORDS):
                    speak("Going idle.")
                    self.conversation_active = False
                    break

                # ask for confirmation
                speak(f"You said: {command}. Should I proceed?")

                if not self._wait_for_confirmation():
                    speak("Cancelled.")
                    continue

                # execute
                response = route_query(command)
                speak(response)

            except sr.WaitTimeoutError:
                if time.time() - idle_timer > 15:
                    speak("No input detected. Going idle.")
                    self.conversation_active = False
                    break

            except sr.UnknownValueError:
                speak("I didn't catch that.")
            except Exception:
                time.sleep(1)

    # ---------------------------------------------------------
    # CONFIRMATION HANDLER
    # ---------------------------------------------------------

    def _wait_for_confirmation(self, timeout=6):
        start = time.time()

        while time.time() - start < timeout:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=3,
                        phrase_time_limit=3
                    )

                reply = self.recognizer.recognize_google(audio).lower()
                print("[CONFIRM]", reply)

                if any(x in reply for x in CONFIRM_WORDS):
                    return True
                if any(x in reply for x in CANCEL_WORDS):
                    return False

            except sr.UnknownValueError:
                continue
            except sr.WaitTimeoutError:
                continue
            except Exception:
                break

        return False
