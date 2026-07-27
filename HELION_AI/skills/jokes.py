import random

JOKES = [
    "Why do programmers hate nature? Too many bugs.",
    "I tried to optimize my life, but it caused a segmentation fault.",
    "Why did the computer get cold? It forgot to close its Windows.",
    "I would tell you a UDP joke, but you might not get it.",
    "Why do Java developers wear glasses? Because they don’t see sharp.",
    "Debugging is like being the detective in a crime movie where you are the murderer.",
    "There are only 10 kinds of people. Those who understand binary and those who don’t.",
    "I’m not lazy. I’m in power-saving mode.",
    "My brain has too many tabs open.",
    "I tried machine learning, but the machine learned to procrastinate.",
]


def tell() -> str:
    return random.choice(JOKES)
