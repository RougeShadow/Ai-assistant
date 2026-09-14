def detect_intent(text: str) -> str:
    t = text.lower()

    if "joke" in t:
        return "JOKE"
    if "advice" in t:
        return "ADVICE"
    if "ppt" in t or "presentation" in t:
        return "PPT"

    return "CHAT"
