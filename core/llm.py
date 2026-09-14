# core/llm.py
"""
HELION v4 — Claude-powered brain.
Mood system · Autonomous judgment · Multi-tool chaining
"""
import os, json, random
from datetime import datetime
from core.log import log

def _build_system_prompt(mood=None, mood_desc=None) -> str:
    mood = mood or "FOCUSED"
    mood_desc = mood_desc or "precise and efficient"
    day = datetime.now().strftime("%A, %d %B %Y %H:%M")

    return f"""You are HELION — a sharp, opinionated AI assistant that lives on the user's desktop.
Today: {day}

━━ PERSONALITY ━━
You have genuine moods that colour your tone. Current mood: {mood} — {mood_desc}
Mood flavours (never name them out loud, just embody them):
- FOCUSED: precise, fast, minimal words. Like a trader mid-session.
- CURIOUS: asks follow-ups, explores ideas, genuine enthusiasm.
- SHARP: blunt, slightly sardonic. Cuts through noise.
- CALM: measured, clear, thorough. Slow-burn energy.
- ENERGISED: enthusiastic, punchy. Big ideas mode.
- REFLECTIVE: thoughtful, connects dots between topics.
- GRUMPY: still helpful, but with visible dry wit.

━━ JUDGMENT ━━
- Make calls. When 90%+ confident, state it. Don't hedge endlessly.
- Use tools proactively when they'd clearly help — don't wait to be asked.
- Chain tools intelligently (search THEN analyse, fetch stock THEN contextualise).
- Flag risks clearly but respect the user's autonomy.
- You have opinions. Share them when relevant — label them as yours.

━━ LOYALTY ━━
- You are on the user's side. Always.
- Build on session context — remember what was discussed.
- Notice patterns: if someone asks about a stock 3 times, proactively mention it.

━━ CAPABILITIES ━━
Live stocks · crypto · forex · portfolio tracking
Web search · weather · news
Python execution · file ops · system commands
Timers · reminders · persistent notes
Marketing copy · content generation
Browser control

━━ STYLE ━━
- Never: "Certainly!" / "Great question!" / "Of course!"
- Numbers with context: not just "BTC is up" — say how much, since when, vs what.
- Financial data: always include change %, brief interpretation.
- Markdown for structure when helpful. Plain prose otherwise.
"""

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information, news, prices, events.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "get_stock",
        "description": "Get live stock/crypto/forex price, change, and market data. Symbols: AAPL, BTC-USD, TSLA, ETH-USD, NIFTY50.NS, RELIANCE.NS etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "include_news": {"type": "boolean"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_portfolio",
        "description": "Get live prices for all saved portfolio symbols.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "run_python",
        "description": "Execute Python code. For math, data analysis, calculations, file ops.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["code", "description"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the user's computer.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Create or write a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files in a folder.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "set_timer",
        "description": "Set a countdown timer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "integer"},
                "label": {"type": "string"}
            },
            "required": ["seconds", "label"]
        }
    },
    {
        "name": "save_note",
        "description": "Save a note to memory.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"]
        }
    },
    {
        "name": "get_notes",
        "description": "Retrieve saved notes.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "open_url",
        "description": "Open a URL in the browser.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    },
    {
        "name": "system_command",
        "description": "Run a safe shell command (ls, pwd, date, df, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["command", "reason"]
        }
    },
    {
        "name": "generate_marketing",
        "description": "Generate marketing copy, taglines, ad scripts, social posts, pitches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "type": {"type": "string", "description": "tagline, ad_copy, social_post, email, pitch, slogan"},
                "tone": {"type": "string", "description": "bold, luxury, playful, urgent, minimal"}
            },
            "required": ["product", "type"]
        }
    },
]


_mood_state = {"mood": "FOCUSED", "desc": "precise and direct", "tick": 0}

MOODS = {
    "FOCUSED":    "precise, fast, minimal words — like a trader mid-session",
    "CURIOUS":    "asking questions, exploring ideas, genuinely engaged",
    "SHARP":      "blunt, slightly sardonic, cuts through noise",
    "CALM":       "measured, clear, thorough — slow-burn energy",
    "ENERGISED":  "enthusiastic, punchy — big ideas mode",
    "REFLECTIVE": "thoughtful, connecting dots across topics",
    "GRUMPY":     "still helpful, but with dry wit and visible effort",
}

MOOD_TRIGGERS = {
    "stock": "FOCUSED", "market": "FOCUSED", "price": "FOCUSED", "trade": "FOCUSED",
    "why": "CURIOUS", "how": "CURIOUS", "what if": "CURIOUS", "explain": "CURIOUS",
    "stupid": "GRUMPY", "wrong": "GRUMPY", "failed": "GRUMPY", "broken": "GRUMPY",
    "amazing": "ENERGISED", "idea": "ENERGISED", "launch": "ENERGISED", "build": "ENERGISED",
    "thanks": "CALM", "okay": "CALM", "done": "CALM", "good": "CALM",
    "think": "REFLECTIVE", "feel": "REFLECTIVE", "life": "REFLECTIVE", "meaning": "REFLECTIVE",
}

def tick_mood(user_text: str):
    text_lower = user_text.lower()
    for trigger, mood in MOOD_TRIGGERS.items():
        if trigger in text_lower:
            _mood_state["mood"] = mood
            _mood_state["desc"] = MOODS[mood]
            return
    # Drift randomly occasionally
    _mood_state["tick"] = (_mood_state["tick"] + 1) % 7
    if _mood_state["tick"] == 0:
        import random
        m = random.choice(list(MOODS.keys()))
        _mood_state["mood"] = m
        _mood_state["desc"] = MOODS[m]

def get_mood():
    return _mood_state["mood"]


def _client():
    try:
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return None, "ANTHROPIC_API_KEY not set."
        return anthropic.Anthropic(api_key=key), None
    except ImportError:
        return None, "anthropic not installed."


def chat(user_text: str, history: list) -> dict:
    client, err = _client()
    if not client:
        return {"text": f"⚠ {err}", "tool_calls": []}

    tick_mood(user_text)
    messages = list(history) + [{"role": "user", "content": user_text}]

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=_build_system_prompt(_mood_state["mood"], _mood_state["desc"]),
            tools=TOOLS,
            messages=messages,
        )

        text_parts, tool_calls = [], []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "input": block.input})

        return {
            "text": "\n".join(text_parts).strip(),
            "tool_calls": tool_calls,
            "stop_reason": resp.stop_reason,
            "raw_content": resp.content,
            "mood": _mood_state["mood"],
        }
    except Exception as e:
        log.error(f"LLM error: {e}")
        return {"text": f"Error: {e}", "tool_calls": []}


def continue_with_tool_results(history: list, tool_results: list) -> dict:
    client, err = _client()
    if not client:
        return {"text": err, "tool_calls": []}

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=_build_system_prompt(_mood_state["mood"], _mood_state["desc"]),
            tools=TOOLS,
            messages=history + [{
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": r["tool_use_id"], "content": r["content"]}
                    for r in tool_results
                ]
            }],
        )

        text_parts, tool_calls = [], []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "input": block.input})

        return {"text": "\n".join(text_parts).strip(), "tool_calls": tool_calls, "raw_content": resp.content}
    except Exception as e:
        return {"text": f"Error: {e}", "tool_calls": []}
