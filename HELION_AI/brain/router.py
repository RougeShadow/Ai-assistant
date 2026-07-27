from brain.intent import detect_intent
from skills import jokes, advice, ppt


def route(text: str) -> str:
    intent = detect_intent(text)

    if intent == "JOKE":
        return jokes.tell()

    if intent == "ADVICE":
        return advice.give()

    if intent == "PPT":
        return ppt.create(text)

    return "HELION online. Try: joke, advice, or create a ppt."
