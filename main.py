#!/usr/bin/env python3
"""
HELION — Desktop AI Assistant
Claude-powered | Voice | Floating Sprite | Full System Access
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from core.config import load_env
    load_env()

    from core.log import log
    log.info("=" * 44)
    log.info("  HELION — Starting up")
    log.info("=" * 44)

    from core.services import start_all
    start_all()

    from gui.app import HelionApp
    app = HelionApp()
    app.run()

if __name__ == "__main__":
    main()
