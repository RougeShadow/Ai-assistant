# core/speaker.py
"""Neural TTS via Edge; pyttsx3 fallback."""
import asyncio
import os
import tempfile
import threading
from pathlib import Path

from core.config import get
from core.log import log

_lock = threading.Lock()
_player = None


def _edge_rate() -> str:
    rate = int(get("voice_rate", 165))
    # Map 100–250 WPM-ish slider to Edge ±%
    pct = int((rate - 165) / 165 * 50)
    pct = max(-50, min(50, pct))
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


def _play_file(path: str):
    import time
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(float(get("voice_volume", 0.9)))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        return
    except Exception as e:
        log.warning(f"pygame playback: {e}")
    try:
        from PySide6.QtCore import QUrl, QEventLoop, QTimer
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PySide6.QtWidgets import QApplication
        if QApplication.instance() is None:
            raise RuntimeError("no qt")
        player = QMediaPlayer()
        audio = QAudioOutput()
        player.setAudioOutput(audio)
        audio.setVolume(float(get("voice_volume", 0.9)))
        loop = QEventLoop()
        player.mediaStatusChanged.connect(
            lambda s: loop.quit() if s == QMediaPlayer.MediaStatus.EndOfMedia else None
        )
        player.setSource(QUrl.fromLocalFile(path))
        player.play()
        QTimer.singleShot(180000, loop.quit)
        loop.exec()
    except Exception as e:
        log.warning(f"TTS playback failed: {e}")


def _speak_edge(text: str) -> bool:
    try:
        import edge_tts
    except ImportError:
        return False
    voice = get("tts_voice", "en-US-GuyNeural") or "en-US-GuyNeural"
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    async def _run():
        comm = edge_tts.Communicate(text, voice, rate=_edge_rate())
        await comm.save(path)

    try:
        asyncio.run(_run())
        _play_file(path)
        return True
    except Exception as e:
        log.warning(f"Edge TTS failed: {e}")
        return False
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def _speak_sapi(text: str) -> bool:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", int(get("voice_rate", 165)))
        engine.setProperty("volume", float(get("voice_volume", 0.9)))
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        log.warning(f"SAPI TTS failed: {e}")
        return False


def list_edge_voices() -> list[tuple[str, str]]:
    """Return (ShortName, display) for English neural voices."""
    try:
        import edge_tts

        async def _list():
            voices = await edge_tts.list_voices()
            out = []
            for v in voices:
                locale = (v.get("Locale") or "")
                if not locale.startswith("en"):
                    continue
                name = v.get("ShortName") or ""
                gender = v.get("Gender") or ""
                out.append((name, f"{name} ({gender})"))
            out.sort(key=lambda x: x[0])
            return out

        return asyncio.run(_list())
    except Exception as e:
        log.warning(f"Could not list Edge voices: {e}")
        return [
            ("en-US-GuyNeural", "en-US-GuyNeural (Male)"),
            ("en-US-JennyNeural", "en-US-JennyNeural (Female)"),
            ("en-GB-RyanNeural", "en-GB-RyanNeural (Male)"),
            ("en-GB-SoniaNeural", "en-GB-SoniaNeural (Female)"),
        ]


def speak(text: str):
    if not text or not get("voice_enabled", True):
        return

    def _do():
        with _lock:
            engine = get("tts_engine", "edge")
            ok = False
            if engine == "edge":
                ok = _speak_edge(text)
            if not ok:
                _speak_sapi(text)

    threading.Thread(target=_do, daemon=True).start()
