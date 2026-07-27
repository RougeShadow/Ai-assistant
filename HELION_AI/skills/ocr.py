# skills/ocr.py
import pytesseract
from PIL import ImageGrab

from brain.agent import Skill
from core.settings import get_setting
from brain.memory import has_consent, set_consent

# ============================================================
# OCR / SCREEN READING SKILL (ORION v5)
# ============================================================

class OCRSkill(Skill):
    name = "ocr"
    triggers = [
        "read screen",
        "what is on screen",
        "scan screen",
        "ocr",
        "read display",
        "read this",
    ]

    def run(self, text: str) -> str:
        if not has_consent("web") and not has_consent("automation"):
            return (
                "Screen reading is disabled for privacy. "
                "Say 'enable screen access' to allow it."
            )

        if "enable screen access" in text.lower():
            set_consent("web", True)
            return "Screen access enabled."

        if not get_setting("automation_enabled", True):
            return "Screen analysis is disabled in settings."

        try:
            img = ImageGrab.grab()
            extracted = pytesseract.image_to_string(img)
            extracted = extracted.strip()

            if not extracted:
                return "I couldn't read any text on the screen."

            return extracted[:1500]  # Orion v5 safety limit
        except Exception as e:
            return "An error occurred while reading the screen."

# ============================================================
# REGISTRATION
# ============================================================

def setup():
    from brain.agent import register_skill
    register_skill(OCRSkill())
