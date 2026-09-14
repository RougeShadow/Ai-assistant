# gui/app.py
"""Compatibility wrapper — Helion now launches the Qt desktop app."""


def run():
    from gui.qt_app import run_app
    return run_app()


class HelionApp:
    def run(self):
        return run()
