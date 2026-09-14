# brain/agent.py
import threading
from core.llm import llm_reason
import traceback
from core.state import set_state
from datetime import datetime

from core.settings import get_setting
from core.events import start_event_loop, publish_event
from core.speaker import speak
from brain.memory import (
    add_episodic,
    add_journal,
    get_preferences,
)

# ============================================================
# SKILL SYSTEM (ORION v5 STYLE)
# ============================================================

class Skill:
    """
    Base class for all skills.
    """
    name = "base"
    triggers = []

    def can_handle(self, text: str) -> bool:
        t = text.lower()
        return any(trigger in t for trigger in self.triggers)

    def run(self, text: str) -> str:
        raise NotImplementedError


_SKILLS = []
_SKILLS_LOCK = threading.Lock()

def register_skill(skill: Skill):
    with _SKILLS_LOCK:
        _SKILLS.append(skill)

def list_skills():
    return [s.name for s in _SKILLS]

# ============================================================
# PERSONALITY / STYLE (ORION v5 FEATURE)
# ============================================================

def style_text(text: str) -> str:
    """
    Applies personality styling.
    Orion v5 kept this minimal and safe.
    """
    if not text:
        return text

    persona = get_setting("persona", "")
    if persona:
        return text

    return text

# ============================================================
# ROUTER (THE HEART)
# ============================================================

def route_query(text: str) -> str:
    """
    Orion v5 router + Helion LLM reasoning layer.
    """
    if not text:
        return ""

    add_episodic("query", {"text": text})

    # -------------------------------------------------
    # LLM REASONING (DECIDE TOOL VS DIRECT RESPONSE)
    # -------------------------------------------------
    llm_result = llm_reason(text)

    if llm_result.get("use_tool"):
        tool_cmd = llm_result.get("command", text)

        for skill in list(_SKILLS):
            try:
                if skill.name == llm_result.get("tool") or skill.can_handle(tool_cmd):
                    result = skill.run(tool_cmd)
                    add_episodic("skill_used", {
                        "skill": skill.name,
                        "input": tool_cmd
                    })
                    return style_text(result)
            except Exception:
                traceback.print_exc()
                return "An internal error occurred."

    # -------------------------------------------------
    # DIRECT LLM RESPONSE
    # -------------------------------------------------
    if "response" in llm_result:
        return style_text(llm_result["response"])

    # -------------------------------------------------
    # FALLBACK: ORIGINAL ORION SKILL ROUTING
    # -------------------------------------------------
    for skill in list(_SKILLS):
        try:
            if skill.can_handle(text):
                result = skill.run(text)
                add_episodic("skill_used", {
                    "skill": skill.name,
                    "input": text
                })
                return style_text(result)
        except Exception:
            traceback.print_exc()
            return "An internal error occurred."

    return style_text("I understand you, but I’m unsure how to proceed.")

# ============================================================
# JOURNAL HOOK (USED BY SOME SKILLS)
# ============================================================

def journal(text: str):
    add_journal(text)

# ============================================================
# SERVICES STARTUP (ORION v5 STYLE)
# ============================================================

def start_services():
    """
    Starts background systems.
    Called once at startup.
    """
    start_event_loop()

    publish_event("startup", {
        "time": datetime.utcnow().isoformat(),
        "agent": "HELION"
    })

    if get_setting("voice_enabled", True):
        speak("Helion systems online.")
# brain/agent.py

def handle_input(text: str) -> str:
    """
    Main entry point for GUI / popup commands
    """
    try:
        # basic routing (expand later)
        text_l = text.lower()

        if "hello" in text_l:
            return "Hello. Helion is online."

        if "sleep" in text_l:
            return "Entering sleep mode."

        if "wake" in text_l:
            return "I am awake."

        if "joke" in text_l:
            return "Why do engineers love dark mode? Because light attracts bugs."

        return f"I heard you say: {text}"

    except Exception as e:
        return "An internal error occurred."
