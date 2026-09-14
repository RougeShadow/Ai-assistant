# skills/dialogue.py
import random
import datetime

from brain.agent import Skill
from brain.memory import (
    add_journal,
    add_fact,
    get_preferences,
)
from core.settings import get_setting, set_setting, toggle_setting

# ============================================================
# DIALOGUE / SYSTEM SKILL (ORION v5)
# ============================================================

class DialogueSkill(Skill):
    name = "dialogue"
    triggers = [
        "hello",
        "hi",
        "hey",
        "how are you",
        "what can you do",
        "help",
        "joke",
        "advice",
        "note",
        "remember",
        "who are you",
        "time",
        "date",
        "settings",
        "enable",
        "disable",
    ]

    def run(self, text: str) -> str:
        t = text.lower()

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------
        if "who are you" in t:
            return "I am Helion. An embodied intelligence evolved from Orion."

        # ----------------------------------------------------
        # GREETINGS
        # ----------------------------------------------------
        if any(x in t for x in ["hello", "hi", "hey"]):
            return random.choice([
                "Hello.",
                "Hi there.",
                "I'm here.",
                "Ready when you are."
            ])

        # ----------------------------------------------------
        # CAPABILITIES
        # ----------------------------------------------------
        if "what can you do" in t or "help" in t:
            return (
                "I can control your system, generate documents, read the screen, "
                "manage memory, assist with planning, and grow with you."
            )

        # ----------------------------------------------------
        # TIME / DATE
        # ----------------------------------------------------
        if "time" in t:
            return datetime.datetime.now().strftime("The time is %H:%M.")

        if "date" in t:
            return datetime.datetime.now().strftime("Today is %B %d, %Y.")

        # ----------------------------------------------------
        # JOKES
        # ----------------------------------------------------
        if "joke" in t:
            return random.choice([
                "I don't need sleep. I just idle efficiently.",
                "I was going to optimize today, but I already am.",
                "My favorite music genre is binary.",
                "I tried debugging myself. Still perfect."
            ])

        # ----------------------------------------------------
        # ADVICE
        # ----------------------------------------------------
        if "advice" in t:
            return random.choice([
                "Focus on one problem at a time.",
                "Consistency beats intensity.",
                "Rest is part of progress.",
                "Learn deeply, not quickly."
            ])

        # ----------------------------------------------------
        # NOTES / MEMORY
        # ----------------------------------------------------
        if t.startswith("note"):
            entry = text.replace("note", "").strip()
            if entry:
                add_journal(entry)
                return "Noted."
            return "What would you like me to note?"

        if t.startswith("remember"):
            parts = text.replace("remember", "").split("is")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                add_fact(key, value)
                return f"I will remember that {key} is {value}."
            return "Tell me what to remember."

        # ----------------------------------------------------
        # SETTINGS CONTROL
        # ----------------------------------------------------
        if t.startswith("enable"):
            key = t.replace("enable", "").strip().replace(" ", "_")
            set_setting(key, True)
            return f"{key} enabled."

        if t.startswith("disable"):
            key = t.replace("disable", "").strip().replace(" ", "_")
            set_setting(key, False)
            return f"{key} disabled."

        if "settings" in t:
            prefs = get_preferences()
            return f"Current preferences: {prefs}"

        # ----------------------------------------------------
        # FALLBACK (ORION v5 STYLE)
        # ----------------------------------------------------
        return (
            "I understand you. "
            "If you want me to act, be more specific."
        )

# ============================================================
# REGISTRATION
# ============================================================

def setup():
    from brain.agent import register_skill
    register_skill(DialogueSkill())
