from brain.llm import ask

def write(prompt):
    return ask(f"Write a professional email: {prompt}")
