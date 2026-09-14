# brain/agent.py
"""
HELION agent loop — streaming multi-turn with tools.
"""
import traceback
from core import llm, tools, memory, state
from core.state import State
from core.log import log


def process(user_text: str, notify_fn=None, on_token=None, on_tool=None) -> str:
    if not user_text.strip():
        return ""

    state.set(State.THINKING)
    log.info(f"User: {user_text[:80]}")

    hist = memory.history(40)

    try:
        result = llm.chat(user_text, hist, on_token=on_token)
        memory.push("user", user_text)

        working = list(hist) + [{"role": "user", "content": user_text}]
        MAX_TOOL_ROUNDS = 6
        rounds = 0

        while result.get("tool_calls") and rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            tool_results = []
            assistant_message = result.get("assistant_message")
            raw_content = result.get("raw_content")

            for tc in result["tool_calls"]:
                tool_name = tc["name"]
                tool_input = tc["input"] or {}
                tool_id = tc["id"]

                log.info(f"Tool: {tool_name}({list(tool_input.keys())})")
                state.set(State.WORKING)
                if on_tool:
                    preview = ""
                    if isinstance(tool_input, dict):
                        preview = str(
                            tool_input.get("symbol")
                            or tool_input.get("query")
                            or tool_input.get("path")
                            or ""
                        )
                    on_tool(tool_name, preview)

                result_text = tools.execute(tool_name, tool_input, notify_fn)
                log.info(f"Result ({tool_name}): {result_text[:80]}")

                tool_results.append({
                    "tool_use_id": tool_id,
                    "content": result_text,
                })

            result = llm.continue_with_tool_results(
                working,
                tool_results,
                on_token=on_token,
                assistant_message=assistant_message,
                raw_content=raw_content,
            )

            # Keep transcript for further tool rounds (Groq / OpenAI format)
            if assistant_message:
                msg = {"role": "assistant", "content": assistant_message.get("content")}
                tcs = assistant_message.get("tool_calls")
                if tcs:
                    msg["tool_calls"] = tcs
                working.append(msg)
                for r in tool_results:
                    working.append({
                        "role": "tool",
                        "tool_call_id": r["tool_use_id"],
                        "content": r["content"],
                    })

        response = (result.get("text") or "").strip()
        if response:
            memory.push("assistant", response)
        state.set(State.IDLE)
        log.info(f"HELION: {response[:100]}")
        return response

    except Exception:
        traceback.print_exc()
        state.set(State.ERROR)
        return "Something went wrong on my side. Check the log if it keeps happening."
