# skills/automation.py
import os
import subprocess
import platform
import time
import webbrowser

from brain.agent import Skill
from core.settings import get_setting
from brain.memory import has_consent, set_consent

# ============================================================
# AUTOMATION SKILL (ORION v5)
# ============================================================

class AutomationSkill(Skill):
    name = "automation"
    triggers = [
        "open",
        "launch",
        "run",
        "close",
        "shutdown",
        "restart",
        "lock",
        "sleep",
        "website",
        "browser",
        "url",
    ]

    def run(self, text: str) -> str:
        if not has_consent("automation"):
            return (
                "Automation is disabled for safety. "
                "Say 'enable automation' to allow system control."
            )

        t = text.lower()

        # ------------------------------
        # ENABLE / DISABLE CONSENT
        # ------------------------------
        if "enable automation" in t:
            set_consent("automation", True)
            return "Automation enabled. I can now control the system."

        if "disable automation" in t:
            set_consent("automation", False)
            return "Automation disabled."

        # ------------------------------
        # OPEN APPLICATIONS
        # ------------------------------
        if "open" in t or "launch" in t or "run" in t:
            return self._open_application(t)

        # ------------------------------
        # SYSTEM POWER COMMANDS
        # ------------------------------
        if "shutdown" in t:
            return self._shutdown()

        if "restart" in t:
            return self._restart()

        if "lock" in t:
            return self._lock()

        if "sleep" in t:
            return self._sleep()

        # ------------------------------
        # WEB / URL
        # ------------------------------
        if "http" in t or "www" in t:
            return self._open_url(text)

        return "I could not determine the automation action."

    # ============================================================
    # ACTION HANDLERS
    # ============================================================

    def _open_application(self, text):
        system = platform.system()

        apps = {
            "windows": {
                "notepad": "notepad",
                "calculator": "calc",
                "cmd": "cmd",
                "explorer": "explorer",
            }
        }

        for app, cmd in apps.get(system.lower(), {}).items():
            if app in text:
                subprocess.Popen(cmd)
                return f"Opening {app}."

        return "I don’t recognize that application."

    def _shutdown(self):
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /s /t 1")
        elif system == "Linux":
            os.system("shutdown now")
        return "Shutting down system."

    def _restart(self):
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 1")
        elif system == "Linux":
            os.system("reboot")
        return "Restarting system."

    def _lock(self):
        system = platform.system()
        if system == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "System locked."
        return "Lock not supported on this OS."

    def _sleep(self):
        system = platform.system()
        if system == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "System going to sleep."
        return "Sleep not supported on this OS."

    def _open_url(self, text):
        for word in text.split():
            if word.startswith("http") or word.startswith("www"):
                webbrowser.open(word)
                return f"Opening {word}"
        return "No valid URL found."

# ============================================================
# REGISTRATION
# ============================================================

def setup():
    from brain.agent import register_skill
    register_skill(AutomationSkill())
