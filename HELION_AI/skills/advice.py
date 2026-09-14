import random

ADVICES = [
    "Take breaks. Efficiency drops when fatigue rises.",
    "Consistency beats intensity.",
    "If something feels overwhelming, break it into smaller steps.",
    "Progress matters more than perfection.",
    "Rest is part of productivity.",
    "Focus on one task at a time.",
    "Learning compounds over time.",
    "Don’t rush clarity.",
    "Sometimes stepping away brings better solutions.",
]


def give() -> str:
    return random.choice(ADVICES)
