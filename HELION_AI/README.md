# HELION AI

HELION is a desktop AI assistant evolved from an earlier project (Orion). It runs as a
tray application with an animated on-screen sprite, wake-word listening, local LLM
reasoning (via Ollama), and a set of pluggable "skills" for automation, notes, OCR,
email, PowerPoint generation, jokes, and advice.

## Features
- 🖥️ Desktop tray app with an animated sprite GUI (idle, listen, think, work, fly, sleep states)
- 🎙️ Wake-word activated listening
- 🧠 Local reasoning via Ollama (`phi3` model) to decide whether to use a tool or respond directly
- 🧩 Skills system: automation, OCR, email, PowerPoint generation, notes, jokes, advice
- 💾 Encrypted local memory with automatic backups
- ⚙️ Configurable via `helion_settings.json` (persona, safe mode, theme, enabled modules)

## Requirements
- Python 3.11+
- [Ollama](https://ollama.com) installed locally, with the `phi3` model pulled:
  ```bash
  ollama pull phi3
  ```
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Setup
1. Copy `.env.example` to `.env` and fill in your own API key(s):
   ```bash
   cp .env.example .env
   ```
2. Run the assistant:
   ```bash
   python main.py
   ```

On first run, HELION creates its own settings file, encrypted memory store, and key —
none of these are included in this repo since they're user-specific and regenerated
automatically.

## Project structure
```
HELION_AI/
├── main.py            # entry point
├── brain/             # agent, router, intent parsing, memory
├── core/               # LLM reasoning, wake word, settings, speaker, tray
├── gui/                # sprite animation & skins
├── skills/             # automation, ocr, email, ppt, notes, jokes, advice
└── assets/             # sprite images
```

## Notes
- `safe_mode` is enabled by default in settings; automation and web features are
  disabled unless explicitly turned on.
- No personal data, memory database, or API keys are committed to this repo.
