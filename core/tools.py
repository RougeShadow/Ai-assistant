# core/tools.py
"""
HELION v4 Tool Executor
Stocks · Marketing · Web · Files · System · Timers · Notes
"""
import os, subprocess, traceback, threading, json
from datetime import datetime
from pathlib import Path
from core.log import log

BLOCKED_COMMANDS = [
    "rm -rf", "rmdir /s", "format", "mkfs", "dd if=",
    ":(){:|:&};:", "shutdown", "reboot", "halt", "poweroff",
    "sudo rm", "del /f", "reg delete",
]


def execute(tool_name: str, tool_input: dict, notify_fn=None) -> str:
    try:
        fn = _DISPATCH.get(tool_name)
        if fn:
            return fn(tool_input, notify_fn)
        return f"Unknown tool: {tool_name}"
    except Exception as e:
        log.error(f"Tool {tool_name} error: {e}")
        return f"Tool error: {e}"


# ── Stocks / Finance ──────────────────────────────────────

def _get_stock(inp, _notify):
    symbol = inp.get("symbol", "").upper().strip()
    include_news = inp.get("include_news", False)

    try:
        import urllib.request, urllib.parse, json as _json

        # Use Yahoo Finance v8 API (no key needed)
        encoded = urllib.parse.quote(symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1d&range=5d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req, timeout=10) as r:
            data = _json.loads(r.read())

        result = data["chart"]["result"][0]
        meta = result["meta"]

        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", meta.get("previousClose", price))
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        currency = meta.get("currency", "USD")
        name = meta.get("shortName", symbol)
        market_state = meta.get("marketState", "UNKNOWN")
        volume = meta.get("regularMarketVolume", 0)
        high = meta.get("regularMarketDayHigh", 0)
        low = meta.get("regularMarketDayLow", 0)

        arrow = "▲" if change >= 0 else "▼"
        sign = "+" if change >= 0 else ""

        lines = [
            f"📊 {name} ({symbol})",
            f"Price: {currency} {price:,.2f}",
            f"Change: {arrow} {sign}{change:+.2f} ({sign}{change_pct:+.2f}%)",
            f"Day range: {low:,.2f} – {high:,.2f}",
            f"Volume: {volume:,}",
            f"Market: {market_state}",
        ]

        # 52-week if available
        week_52_high = meta.get("fiftyTwoWeekHigh")
        week_52_low = meta.get("fiftyTwoWeekLow")
        if week_52_high and week_52_low:
            lines.append(f"52W: {week_52_low:,.2f} – {week_52_high:,.2f}")

        result_str = "\n".join(lines)

        if include_news:
            news = _fetch_stock_news(symbol)
            if news:
                result_str += f"\n\n📰 Recent headlines:\n{news}"

        return result_str

    except Exception as e:
        return f"Could not fetch {symbol}: {e}\nTip: Check the symbol (e.g. RELIANCE.NS for NSE, BTC-USD for crypto)"


def _fetch_stock_news(symbol: str) -> str:
    try:
        import urllib.request, urllib.parse, json as _json
        query = urllib.parse.quote_plus(f"{symbol} stock news")
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        with urllib.request.urlopen(url, timeout=6) as r:
            data = _json.loads(r.read())
        topics = data.get("RelatedTopics", [])[:3]
        lines = [f"• {t['Text'][:120]}" for t in topics if isinstance(t, dict) and t.get("Text")]
        return "\n".join(lines) if lines else ""
    except Exception:
        return ""


def get_chart_series(symbol: str, range_key: str = "5d") -> dict:
    """OHLC + volume from Yahoo. range_key: 1d, 5d, 1mo."""
    import urllib.request, urllib.parse, json as _json
    symbol = symbol.upper().strip()
    interval = {"1d": "5m", "5d": "15m", "1mo": "1h"}.get(range_key, "15m")
    rng = range_key if range_key in ("1d", "5d", "1mo") else "5d"
    encoded = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval={interval}&range={rng}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = _json.loads(r.read())
    result = data["chart"]["result"][0]
    meta = result["meta"]
    ts = result.get("timestamp") or []
    quote = (result.get("indicators") or {}).get("quote") or [{}]
    q = quote[0]
    closes = q.get("close") or []
    highs = q.get("high") or closes
    lows = q.get("low") or closes
    opens = q.get("open") or closes
    vols = q.get("volume") or [0] * len(closes)
    bars = []
    for i, t in enumerate(ts):
        c = closes[i] if i < len(closes) else None
        if c is None:
            continue
        bars.append({
            "t": t,
            "o": opens[i] if i < len(opens) and opens[i] is not None else c,
            "h": highs[i] if i < len(highs) and highs[i] is not None else c,
            "l": lows[i] if i < len(lows) and lows[i] is not None else c,
            "c": c,
            "v": vols[i] if i < len(vols) and vols[i] is not None else 0,
        })
    profile = _volume_at_price(bars)
    return {
        "symbol": symbol,
        "name": meta.get("shortName", symbol),
        "price": meta.get("regularMarketPrice"),
        "currency": meta.get("currency", "USD"),
        "bars": bars,
        "profile": profile,
    }


def _volume_at_price(bars: list) -> dict:
    if not bars:
        return {"buckets": [], "poc": None, "vah": None, "val": None}
    prices = [b["c"] for b in bars]
    lo, hi = min(prices), max(prices)
    if hi <= lo:
        return {"buckets": [{"price": lo, "vol": sum(b["v"] for b in bars)}], "poc": lo, "vah": hi, "val": lo}
    n = 24
    width = (hi - lo) / n
    buckets = [{"price": lo + (i + 0.5) * width, "vol": 0.0} for i in range(n)]
    for b in bars:
        idx = int((b["c"] - lo) / width)
        idx = max(0, min(n - 1, idx))
        buckets[idx]["vol"] += b["v"] or 0
    poc_i = max(range(n), key=lambda i: buckets[i]["vol"])
    total = sum(x["vol"] for x in buckets) or 1
    # 70% value area around POC
    used = buckets[poc_i]["vol"]
    left, right = poc_i, poc_i
    while used / total < 0.70 and (left > 0 or right < n - 1):
        lv = buckets[left - 1]["vol"] if left > 0 else -1
        rv = buckets[right + 1]["vol"] if right < n - 1 else -1
        if rv >= lv:
            right += 1
            used += buckets[right]["vol"]
        else:
            left -= 1
            used += buckets[left]["vol"]
    return {
        "buckets": buckets,
        "poc": buckets[poc_i]["price"],
        "val": buckets[left]["price"],
        "vah": buckets[right]["price"],
    }


def _get_portfolio(inp, _notify):
    from core.memory import get_portfolio_symbols
    portfolio = get_portfolio_symbols()
    if not portfolio:
        return "No portfolio saved. Ask me to add a symbol, or use the Stocks page."

    results = []
    for symbol in portfolio:
        r = _get_stock({"symbol": symbol}, None)
        # Get just first 3 lines (compact)
        lines = r.split("\n")[:3]
        results.append("\n".join(lines))

    return "\n\n".join(results)


# ── Web Search ────────────────────────────────────────────

def _web_search(inp, _notify):
    query = inp.get("query", "")
    try:
        import urllib.request, urllib.parse, json as _json
        encoded = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = _json.loads(r.read())

        parts = []
        if data.get("AbstractText"):
            parts.append(data["AbstractText"])
        if data.get("Answer"):
            parts.append(f"Answer: {data['Answer']}")
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"• {topic['Text']}")

        if parts:
            return "\n".join(parts)

        if any(w in query.lower() for w in ["weather", "temperature", "forecast"]):
            return _weather_search(query)

        return f"No instant results for '{query}'."

    except Exception as e:
        return f"Search failed: {e}"


def _weather_search(query):
    try:
        import urllib.request, json as _json, re
        match = re.search(r'(?:weather|temperature|forecast|rain)\s+(?:in\s+)?([a-zA-Z\s,]+)', query, re.I)
        city = match.group(1).strip().replace(" ", "+") if match else "auto"
        url = f"https://wttr.in/{city}?format=j1"
        with urllib.request.urlopen(url, timeout=6) as r:
            data = _json.loads(r.read())
        c = data["current_condition"][0]
        area = data["nearest_area"][0]["areaName"][0]["value"]
        country = data["nearest_area"][0]["country"][0]["value"]
        desc = c["weatherDesc"][0]["value"]
        temp_c = c["temp_C"]
        feels = c["FeelsLikeC"]
        humidity = c["humidity"]
        wind = c["windspeedKmph"]
        uv = c.get("uvIndex", "—")
        return (f"📍 {area}, {country}\n"
                f"🌤 {desc}\n"
                f"🌡 {temp_c}°C (feels like {feels}°C)\n"
                f"💧 Humidity: {humidity}%  |  💨 Wind: {wind} km/h  |  ☀ UV: {uv}")
    except Exception as e:
        return f"Weather fetch failed: {e}"


# ── Python Execution ──────────────────────────────────────

def _run_python(inp, _notify):
    code = inp.get("code", "")
    desc = inp.get("description", "code")
    log.info(f"Running Python: {desc}")
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=20,
            cwd=str(Path.home())
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode == 0:
            return out if out else "(ran successfully, no output)"
        else:
            return f"Error:\n{err}"
    except subprocess.TimeoutExpired:
        return "Timed out (20s limit)."
    except Exception as e:
        return f"Could not run: {e}"


# ── File Operations ───────────────────────────────────────

def _read_file(inp, _notify):
    path = Path(inp.get("path", "")).expanduser()
    if not path.exists():
        return f"File not found: {path}"
    if path.stat().st_size > 500_000:
        return "File too large. Showing first 2000 chars:\n" + path.read_text(errors="replace")[:2000] + "\n…(truncated)"
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Could not read: {e}"


def _write_file(inp, _notify):
    path = Path(inp.get("path", "")).expanduser()
    content = inp.get("content", "")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✓ Wrote {len(content):,} chars to {path}"
    except Exception as e:
        return f"Could not write: {e}"


def _list_directory(inp, _notify):
    path = Path(inp.get("path", ".")).expanduser()
    if not path.exists():
        return f"Directory not found: {path}"
    try:
        items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        lines = []
        for item in items[:100]:
            icon = "📁" if item.is_dir() else "📄"
            size = f"  {item.stat().st_size:,}B" if item.is_file() else ""
            lines.append(f"{icon} {item.name}{size}")
        return f"{path}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Could not list: {e}"


# ── Timer ─────────────────────────────────────────────────

def _set_timer(inp, notify_fn):
    seconds = int(inp.get("seconds", 60))
    label = inp.get("label", "Timer")

    def _ring():
        import time
        time.sleep(seconds)
        msg = f"⏰ {label}"
        log.info(msg)
        if notify_fn:
            notify_fn(msg)
        try:
            from core.speaker import speak
            speak(f"Timer done. {label}.")
        except Exception:
            pass

    threading.Thread(target=_ring, daemon=True).start()
    mins, secs = seconds // 60, seconds % 60
    readable = f"{mins}m {secs}s" if mins else f"{secs}s"
    return f"⏱ Timer set: {label} — {readable}"


# ── Notes ─────────────────────────────────────────────────

def _save_note(inp, _notify):
    from core.memory import add_note
    text = inp.get("text", "")
    add_note(text)
    return f"✓ Noted: {text}"


def _get_notes(inp, _notify):
    from core.memory import get_notes
    notes = get_notes(20)
    if not notes:
        return "No notes yet."
    return "Notes:\n" + "\n".join(f"[{n['ts'][:10]}] {n['text']}" for n in notes)


# ── Open URL ──────────────────────────────────────────────

def _open_url(inp, _notify):
    import webbrowser
    url = inp.get("url", "")
    webbrowser.open(url)
    return f"✓ Opened: {url}"


# ── System Command ────────────────────────────────────────

def _system_command(inp, _notify):
    cmd = inp.get("command", "")
    reason = inp.get("reason", "")
    cmd_lower = cmd.lower()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return f"❌ Blocked for safety: '{blocked}'"
    log.info(f"System: {cmd} ({reason})")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=10, cwd=str(Path.home())
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        return out if result.returncode == 0 else f"Exit {result.returncode}:\n{err or out}"
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Failed: {e}"


# ── Marketing Copy ────────────────────────────────────────

def _generate_marketing(inp, _notify):
    """Generate marketing copy using Claude itself as a sub-call."""
    product = inp.get("product", "")
    copy_type = inp.get("type", "tagline")
    tone = inp.get("tone", "bold")

    # Build a focused prompt for marketing
    prompts = {
        "tagline":     f"Write 5 powerful taglines for: {product}. Tone: {tone}. Each on its own line. No numbering.",
        "ad_copy":     f"Write a compelling 3-paragraph ad for: {product}. Tone: {tone}. Hook, value prop, CTA.",
        "social_post": f"Write 3 social media posts (Twitter/X style) for: {product}. Tone: {tone}. Include relevant hashtags.",
        "email":       f"Write a marketing email for: {product}. Tone: {tone}. Subject line + body. Under 200 words.",
        "pitch":       f"Write a 30-second elevator pitch for: {product}. Tone: {tone}. Punchy and memorable.",
        "slogan":      f"Create 5 memorable slogans for: {product}. Tone: {tone}. Short, punchy, sticky.",
    }

    prompt = prompts.get(copy_type, prompts["tagline"])
    from core.llm import complete_text
    return complete_text(prompt, max_tokens=600)


_DISPATCH = {
    "web_search":         _web_search,
    "get_stock":          _get_stock,
    "get_portfolio":      _get_portfolio,
    "run_python":         _run_python,
    "read_file":          _read_file,
    "write_file":         _write_file,
    "list_directory":     _list_directory,
    "set_timer":          _set_timer,
    "save_note":          _save_note,
    "get_notes":          _get_notes,
    "open_url":           _open_url,
    "system_command":     _system_command,
    "generate_marketing": _generate_marketing,
}
