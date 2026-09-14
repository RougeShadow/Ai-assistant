# HELION v4 — Desktop AI Assistant

> Claude-powered · Voice · Floating Sprite · Full System Access
> Stocks · Portfolio · Marketing · Moods · Multi-panel App

---

## What's New in v4

| Feature | Details |
|---|---|
| **Multi-panel App** | Chat · Stocks · Marketing · Notes · Settings — all in one window |
| **Live Stocks** | Real-time prices, change %, 52W range, volume for any ticker |
| **Portfolio Tracker** | Add symbols, live refresh every 2 mins, sidebar display |
| **Crypto & Forex** | BTC-USD, ETH-USD, RELIANCE.NS, NIFTY50.NS, GOLD — all supported |
| **Marketing Studio** | Generate taglines, ad copy, social posts, pitches, slogans |
| **Mood Engine** | HELION's tone shifts between 7 moods based on context |
| **Autonomous Judgment** | Proactively uses tools, chains them intelligently |
| **Keyboard Shortcuts** | Ctrl+1–5 to switch panels, Ctrl+L to clear |
| **Quick Actions** | One-click common tasks in the sidebar |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Windows PyAudio:
```bash
pip install pipwin && pipwin install pyaudio
```

### 2. Set your API key

Create `.env` in the project root:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run

```bash
python main.py
```

---

## What HELION can do

### 💬 Chat
- Any question, analysis, writing, code
- Persistent memory across the session
- Voice responses (optional)

### 📈 Stocks
- `AAPL`, `TSLA`, `MSFT`, `BTC-USD`, `ETH-USD`
- Indian markets: `RELIANCE.NS`, `NIFTY50.NS`, `INFY.NS`
- Commodities: `GOLD`, `SILVER`, `CL=F` (oil)
- Type in chat: *"What's TSLA doing?"* or *"Check my portfolio"*

### 🚀 Marketing
- Taglines, slogans, ad copy, social posts, email campaigns, pitches
- Tone control: bold · luxury · playful · urgent · minimal · witty
- Save outputs to Notes

### 📝 Notes
- Quick-add from the Notes panel
- Save via chat: *"Note: call dentist tomorrow"*
- Persisted to `helion_memory.json`

### ⚙ Tools
- Web search · Weather · Python execution
- File read/write · System commands
- Timers & reminders

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+1` | Switch to Chat |
| `Ctrl+2` | Switch to Stocks |
| `Ctrl+3` | Switch to Marketing |
| `Ctrl+4` | Switch to Notes |
| `Ctrl+5` | Switch to Settings |
| `Ctrl+L` | Clear chat |
| `Esc` | Close window |
| `Enter` | Send message |

---

## Mood System

HELION has 7 moods that shift its tone based on your messages:

| Mood | When | Tone |
|---|---|---|
| FOCUSED | Stock/market talk | Precise, efficient |
| CURIOUS | "Why?" / "How?" | Engaged, exploring |
| SHARP | Errors, problems | Blunt, direct |
| CALM | Acknowledgements | Measured, clear |
| ENERGISED | Ideas, launches | Enthusiastic, punchy |
| REFLECTIVE | Deep topics | Thoughtful, connecting |
| GRUMPY | Frustration detected | Dry wit, still helpful |

Mood icon and name show in the top-right corner.

---

## Portfolio Management

Add symbols:
- Chat: *"Add AAPL to my portfolio"* / *"Track BTC-USD"*
- Stocks panel: enter ticker → click `+ PORTFOLIO`
- Click `Manage portfolio →` to remove symbols

Portfolio auto-refreshes every 2 minutes when the Stocks panel is open.

---

## Controls

| Action | Result |
|---|---|
| **Click sprite** | Opens app |
| **Right-click sprite** | Context menu |
| **Drag sprite** | Move anywhere |
| **Say "arise"** | Wake word |

---

## Project Structure

```
helion/
├── main.py
├── requirements.txt
├── .env                  ← YOUR API KEY
├── core/
│   ├── config.py
│   ├── llm.py            ← Claude + mood engine
│   ├── tools.py          ← Stocks, marketing, files, timers
│   ├── memory.py         ← History, notes, portfolio
│   ├── state.py
│   ├── events.py
│   ├── speaker.py
│   ├── wakeword.py
│   └── services.py
├── brain/
│   └── agent.py          ← Tool orchestration loop
├── gui/
│   ├── app.py
│   ├── popup.py          ← Multi-panel app UI (v4)
│   ├── sprite.py
│   └── tray.py
└── assets/
    └── skins/default/sprites/
```

---

## Troubleshooting

**No API key** → Create `.env` with `ANTHROPIC_API_KEY=sk-ant-...`

**Stock data fails** → Requires internet. Uses Yahoo Finance (no API key needed).

**No voice** → `pip install pyttsx3` + on Linux: `sudo apt install espeak`

**No wake word** → `pip install SpeechRecognition pyaudio` + microphone

**Sprite missing** → `pip install Pillow pyautogui`
