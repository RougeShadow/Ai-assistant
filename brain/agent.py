# brain/agent.py
"""
HELION v4 agent loop — multi-turn with tools, mood-aware.
"""
import traceback
from core import llm, tools, memory, state
from core.state import State
from core.log import log


def process(user_text: str, notify_fn=None) -> str:
    if not user_text.strip():
        return ""

    state.set(State.THINKING)
    log.info(f"User: {user_text[:80]}")

    hist = memory.history(20)

    try:
        result = llm.chat(user_text, hist)
        memory.push("user", user_text)

        MAX_TOOL_ROUNDS = 6
        rounds = 0

        while result.get("tool_calls") and rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            tool_results = []

            for tc in result["tool_calls"]:
                tool_name  = tc["name"]
                tool_input = tc["input"]
                tool_id    = tc["id"]

                log.info(f"Tool: {tool_name}({list(tool_input.keys())})")
                state.set(State.WORKING)

                # Handle portfolio memory ops inline
                if tool_name == "save_note" and "portfolio" in tool_input.get("text", "").lower():
                    # Parse and save to portfolio
                    pass

                result_text = tools.execute(tool_name, tool_input, notify_fn)
                log.info(f"Result ({tool_name}): {result_text[:80]}")

                tool_results.append({
                    "tool_use_id": tool_id,
                    "content":     result_text,
                })

            current_hist = memory.history(20)
            current_hist.append({"role": "user", "content": user_text})

            raw = result.get("raw_content", [])
            if raw:
                current_hist.append({
                    "role": "assistant",
                    "content": [
                        {"type": b.type, **({
                            "text": b.text} if b.type == "text" else
                            {"id": b.id, "name": b.name, "input": b.input})}
                        for b in raw
                    ]
                })

            result = llm.continue_with_tool_results(current_hist, tool_results)

        response = result.get("text", "").strip() or "Done."
        memory.push("assistant", response)
        state.set(State.IDLE)
        log.info(f"HELION: {response[:100]}")
        return response

    except Exception:
        traceback.print_exc()
        state.set(State.ERROR)
        return "Something went wrong. Check the log."
