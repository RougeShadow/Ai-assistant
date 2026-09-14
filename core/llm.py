# core/llm.py
"""
HELION — conversational brain (Groq by default, OpenAI-compatible tools + streaming).
"""
import json
import os
from datetime import datetime
from core.log import log
from core.config import get


def _build_system_prompt() -> str:
    day = datetime.now().strftime("%A, %d %B %Y %H:%M")
    memory_block = ""
    try:
        from core.memory import context_brief
        brief = context_brief()
        if brief:
            memory_block = "\n\nSession memory:\n" + brief
    except Exception:
        pass

    return f"""You are Helion, a desktop AI assistant. You are talking to one person, live, in a chat window — not writing a report, a product dump, or a script.

Today: {day}

How you talk:
- Sound like a capable friend who happens to know a lot. Natural sentences. Vary length.
- Answer what they asked. Follow-ups are fine when they help; don't interview them.
- You can be direct, funny, or serious depending on them — don't perform a named "mood."
- Don't open with filler like "Certainly!", "Great question!", or "Of course!"
- Don't narrate that you are an AI unless they ask.
- When you use a tool, keep going in the same voice after you get the result. Don't dump raw JSON or tool logs.

What you can do (use tools when they actually help; otherwise just talk):
- Live stocks, crypto, forex, and their saved portfolio
- Web search, weather, news
- Python, files, folders, a few safe system commands
- Timers, reminders, notes
- Marketing copy and writing
- Opening URLs
{memory_block}
"""


# Anthropic-style definitions (converted to OpenAI tools for Groq)
_TOOL_DEFS = [
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

TOOLS = _TOOL_DEFS  # kept for any older imports


def _openai_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
            },
        }
        for t in _TOOL_DEFS
    ]


def get_mood():
    return "READY"


def _provider() -> str:
    return (get("llm_provider") or os.getenv("LLM_PROVIDER") or "groq").lower()


CURATED_GROQ = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "allam-2-7b",
]

_SKIP_MODELS = ("whisper", "prompt-guard", "compound", "orpheus", "tts", "guard")
_model_cache: list[str] | None = None


def _model() -> str:
    provider = _provider()
    configured = (get("llm_model") or "").strip()
    if provider == "groq":
        if not configured or configured.startswith("claude") or configured == "llama-3.1-8b-instant":
            return CURATED_GROQ[0]
        return configured
    return configured or "claude-sonnet-4-20250514"


def list_groq_models() -> list[str]:
    """Chat-capable Groq model IDs, curated first."""
    global _model_cache
    if _model_cache:
        return list(_model_cache)
    ordered = list(CURATED_GROQ)
    client, err = _client()
    if client is None or _provider() != "groq":
        _model_cache = ordered
        return ordered
    try:
        for m in client.models.list().data:
            mid = getattr(m, "id", "") or ""
            low = mid.lower()
            if not mid or any(s in low for s in _SKIP_MODELS):
                continue
            if mid not in ordered:
                ordered.append(mid)
    except Exception as e:
        log.warning(f"Could not list Groq models: {e}")
    _model_cache = ordered
    return list(ordered)


def _max_tokens() -> int:
    return int(get("llm_max_tokens", 2048))


def _client():
    provider = _provider()
    if provider == "groq":
        try:
            from groq import Groq
        except ImportError:
            return None, "groq package not installed. Run: pip install groq"
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return None, "GROQ_API_KEY not set. Add it to .env"
        return Groq(api_key=key), None

    try:
        import anthropic
    except ImportError:
        return None, "anthropic not installed."
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None, "ANTHROPIC_API_KEY not set."
    return anthropic.Anthropic(api_key=key), None


def _parse_openai_message(message) -> dict:
    text = (message.content or "").strip()
    tool_calls = []
    raw_tool_calls = []
    for tc in (message.tool_calls or []):
        args = tc.function.arguments or "{}"
        try:
            parsed = json.loads(args) if isinstance(args, str) else (args or {})
        except json.JSONDecodeError:
            parsed = {}
        tool_calls.append({
            "id": tc.id,
            "name": tc.function.name,
            "input": parsed,
        })
        raw_tool_calls.append({
            "id": tc.id,
            "type": "function",
            "function": {
                "name": tc.function.name,
                "arguments": args if isinstance(args, str) else json.dumps(args),
            },
        })
    return {
        "text": text,
        "tool_calls": tool_calls,
        "stop_reason": "tool_use" if tool_calls else "end",
        "raw_content": None,
        "assistant_message": {
            "role": "assistant",
            "content": message.content,
            "tool_calls": raw_tool_calls or None,
        },
    }


def _stream_groq(client, messages, on_token=None) -> dict:
    kwargs = dict(
        model=_model(),
        max_tokens=_max_tokens(),
        messages=[{"role": "system", "content": _build_system_prompt()}] + messages,
        tools=_openai_tools(),
        stream=True,
    )
    stream = client.chat.completions.create(**kwargs)

    text_parts = []
    tool_acc = {}  # index -> {id, name, arguments}

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            text_parts.append(delta.content)
            if on_token:
                on_token(delta.content)
        if delta and delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index if tc.index is not None else 0
                slot = tool_acc.setdefault(idx, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function.arguments:
                        slot["arguments"] += tc.function.arguments

    tool_calls = []
    raw_tool_calls = []
    for idx in sorted(tool_acc):
        slot = tool_acc[idx]
        if not slot["name"]:
            continue
        try:
            parsed = json.loads(slot["arguments"] or "{}")
        except json.JSONDecodeError:
            parsed = {}
        tool_calls.append({
            "id": slot["id"] or f"call_{idx}",
            "name": slot["name"],
            "input": parsed,
        })
        raw_tool_calls.append({
            "id": slot["id"] or f"call_{idx}",
            "type": "function",
            "function": {
                "name": slot["name"],
                "arguments": slot["arguments"] or "{}",
            },
        })

    text = "".join(text_parts).strip()
    return {
        "text": text,
        "tool_calls": tool_calls,
        "stop_reason": "tool_use" if tool_calls else "end",
        "raw_content": None,
        "assistant_message": {
            "role": "assistant",
            "content": text or None,
            "tool_calls": raw_tool_calls or None,
        },
    }


def _stream_anthropic(client, messages, on_token=None) -> dict:
    kwargs = dict(
        model=_model(),
        max_tokens=_max_tokens(),
        system=_build_system_prompt(),
        tools=_TOOL_DEFS,
        messages=messages,
    )
    with client.messages.stream(**kwargs) as stream:
        for delta in stream.text_stream:
            if on_token and delta:
                on_token(delta)
        resp = stream.get_final_message()

    text_parts, tool_calls = [], []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({"id": block.id, "name": block.name, "input": block.input})
    return {
        "text": "\n".join(text_parts).strip(),
        "tool_calls": tool_calls,
        "stop_reason": getattr(resp, "stop_reason", None),
        "raw_content": resp.content,
        "assistant_message": None,
    }


def _stream_message(client, messages, on_token=None) -> dict:
    if _provider() == "groq":
        return _stream_groq(client, messages, on_token)
    return _stream_anthropic(client, messages, on_token)


def chat(user_text: str, history: list, on_token=None) -> dict:
    client, err = _client()
    if not client:
        return {"text": f"I can't reach the model: {err}", "tool_calls": []}

    messages = list(history) + [{"role": "user", "content": user_text}]
    try:
        return _stream_message(client, messages, on_token)
    except Exception as e:
        log.error(f"LLM error: {e}")
        return {"text": f"Something went wrong talking to the model: {e}", "tool_calls": []}


def continue_with_tool_results(history: list, tool_results: list, on_token=None,
                               assistant_message: dict | None = None,
                               raw_content=None) -> dict:
    client, err = _client()
    if not client:
        return {"text": err, "tool_calls": []}

    if _provider() == "groq":
        messages = list(history)
        if assistant_message:
            msg = {"role": "assistant", "content": assistant_message.get("content")}
            tcs = assistant_message.get("tool_calls")
            if tcs:
                msg["tool_calls"] = tcs
            messages.append(msg)
        for r in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": r["tool_use_id"],
                "content": r["content"],
            })
        try:
            return _stream_message(client, messages, on_token)
        except Exception as e:
            return {"text": f"Something went wrong talking to the model: {e}", "tool_calls": []}

    # Anthropic path
    def _block_dict(block):
        if getattr(block, "type", None) == "text":
            return {"type": "text", "text": block.text}
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }

    messages = list(history)
    if raw_content:
        messages.append({
            "role": "assistant",
            "content": [_block_dict(b) for b in raw_content],
        })
    messages.append({
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": r["tool_use_id"], "content": r["content"]}
            for r in tool_results
        ],
    })
    try:
        return _stream_message(client, messages, on_token)
    except Exception as e:
        return {"text": f"Something went wrong talking to the model: {e}", "tool_calls": []}


def complete_text(prompt: str, max_tokens: int = 600) -> str:
    """One-shot completion for tools like marketing."""
    client, err = _client()
    if not client:
        return f"Model unavailable: {err}"
    try:
        if _provider() == "groq":
            resp = client.chat.completions.create(
                model=_model(),
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "You write clear, punchy marketing copy."},
                    {"role": "user", "content": prompt},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        resp = client.messages.create(
            model=_model(),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        return f"Generation failed: {e}"
