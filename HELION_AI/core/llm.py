# core/llm.py
import subprocess
import json

OLLAMA_MODEL = "phi3"

SYSTEM_PROMPT = """
You are HELION, an AI assistant evolved from Orion.
You reason carefully and decide whether a user request
should be handled by tools or answered directly.

If a tool should be used, respond ONLY in JSON like:

{
  "use_tool": true,
  "tool": "automation|ppt|ocr|dialogue",
  "command": "cleaned user command"
}

If no tool is needed, respond normally.
"""

def llm_reason(user_input: str) -> dict:
    """
    Calls Ollama locally and returns parsed intent.
    """
    prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}\nHELION:"

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout.strip()

        # Try JSON parse
        if output.startswith("{"):
            return json.loads(output)

        return {
            "use_tool": False,
            "response": output
        }

    except Exception as e:
        return {
            "use_tool": False,
            "response": "I couldn't reason locally right now."
        }
