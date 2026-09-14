# gui/sprite.py
"""
HELION floating sprite.
Wanders the screen, reacts to cursor, sleeps when idle, opens popup on click.
Gracefully degrades if no sprite images are found (uses a placeholder).
"""
import tkinter as tk
import threading, random, math, time, os
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
from core.config import get
from core.state import State, subscribe
from core import state as _state_mod
from core.log import log

SIZE       = 140
TRANSPARENT = "magenta"

SPEED      = (0.6, 2.2)
DIR_CHANGE = (3.0, 7.0)
AVOID_R    = 110
PANIC_R    = 55
AVOID_F    = 0.9
IDLE_SLEEP = 30        # seconds before auto-sleep
COLLISION_COOLDOWN = 1.2

SPRITES_ROOT = Path(__file__).parent.parent / "assets" / "skins" / "default" / "sprites"

STATE_MAP = {
    State.IDLE:      "idle",
    State.LISTENING: "listen",
    State.THINKING:  "think",
    State.SPEAKING:  "hover",
    State.WORKING:   "work",
    State.SLEEPING:  "sleep",
    State.WAKING:    "wake",
    State.ERROR:     "confused",
}


def _load_frames(folder_name) -> list:
    folder = SPRITES_ROOT / folder_name
    frames = []
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() == ".png":
                try:
                    img = Image.open(f).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)
                    frames.append(ImageTk.PhotoImage(img))
                except Exception:
                    pass
    return frames


def _make_placeholder(color="#00d4aa", shape="circle") -> list:
    """Fallback when no sprite PNGs exist."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 20
    draw.ellipse([pad, pad, SIZE - pad, SIZE - pad], fill=color + "cc", outline=color, width=2)
    # inner dot
    draw.ellipse([SIZE//2-8, SIZE//2-8, SIZE//2+8, SIZE//2+8], fill="white")
    return [ImageTk.PhotoImage(img)]


class HelionSprite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=TRANSPARENT)
        self.wm_attributes("-transparentcolor", TRANSPARENT)
        self.geometry(f"{SIZE}x{SIZE}+400+400")

        self.canvas = tk.Canvas(self, width=SIZE, height=SIZE,
                                bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack()

        # Load sprite frames
        self.frames: dict[str, list] = {}
        for state_enum, folder in STATE_MAP.items():
            loaded = _load_frames(folder)
            if loaded:
                self.frames[state_enum] = loaded

        # Fallback placeholder for all states
        _placeholder = _make_placeholder()
        for state_enum in STATE_MAP:
            self.frames.setdefault(state_enum, _placeholder)

        # Current display state
        self._cur_state = State.IDLE
        self._frame_idx = 0
        self._sprite_id = self.canvas.create_image(
            SIZE // 2, SIZE // 2, image=self.frames[State.IDLE][0]
        )

        # Movement
        angle = random.uniform(0, math.tau)
        spd   = random.uniform(*SPEED)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self._next_dir = time.time() + random.uniform(*DIR_CHANGE)
        self._last_collision = 0.0
        self._last_activity  = time.time()
        self._sleeping       = False
        self._dragging       = False
        self._drag_ox = self._drag_oy = 0

        # Bindings
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<ButtonPress-3>",   self._on_right_click)

        subscribe(self._on_state_change)

        # Kick off loops
        self.after(100, self._anim_loop)
        self.after(40,  self._move_loop)

    # ── State changes ───────────────────────────────────────

    def _on_state_change(self, new_state: State):
        self._last_activity = time.time()
        if self._sleeping and new_state != State.SLEEPING:
            self._wake()
        self._cur_state = new_state
        self._frame_idx = 0

    # ── Animation loop ──────────────────────────────────────

    def _anim_loop(self):
        frames = self.frames.get(self._cur_state, self.frames[State.IDLE])
        self.canvas.itemconfig(self._sprite_id, image=frames[self._frame_idx])
        self._frame_idx = (self._frame_idx + 1) % len(frames)
        self.after(110, self._anim_loop)

    # ── Movement loop ───────────────────────────────────────

    def _move_loop(self):
        if self._dragging:
            self.after(40, self._move_loop)
            return

        now = time.time()

        # Sleep check
        if not self._sleeping and now - self._last_activity > IDLE_SLEEP:
            self._sleep()
            return

        if self._sleeping:
            self.after(200, self._move_loop)
            return

        if self._cur_state == State.IDLE:
            self._cur_state = State.IDLE  # fly visual handled by state

        # Cursor avoidance
        try:
            import pyautogui
            cx, cy = pyautogui.position()
        except Exception:
            cx, cy = -999, -999

        sx = self.winfo_x() + SIZE // 2
        sy = self.winfo_y() + SIZE // 2
        dx, dy = sx - cx, sy - cy
        dist = math.hypot(dx, dy)

        if dist < PANIC_R:
            ang = math.atan2(dy, dx)
            self.vx += math.cos(ang) * AVOID_F * 2.5
            self.vy += math.sin(ang) * AVOID_F * 2.5
        elif dist < AVOID_R:
            ang = math.atan2(dy, dx)
            self.vx += math.cos(ang) * AVOID_F
            self.vy += math.sin(ang) * AVOID_F

        # Speed cap
        spd = math.hypot(self.vx, self.vy)
        if spd > SPEED[1] * 2:
            self.vx = self.vx / spd * SPEED[1] * 2
            self.vy = self.vy / spd * SPEED[1] * 2

        # Periodic direction change
        if now >= self._next_dir:
            ang = math.atan2(self.vy, self.vx) + random.uniform(-math.pi / 2, math.pi / 2)
            spd = random.uniform(*SPEED)
            self.vx = math.cos(ang) * spd
            self.vy = math.sin(ang) * spd
            self._next_dir = now + random.uniform(*DIR_CHANGE)

        # Move
        nx = self.winfo_x() + self.vx
        ny = self.winfo_y() + self.vy
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        bounced = False
        if nx <= 0:
            nx = 0; self.vx = abs(self.vx); bounced = True
        elif nx >= sw - SIZE:
            nx = sw - SIZE; self.vx = -abs(self.vx); bounced = True
        if ny <= 0:
            ny = 0; self.vy = abs(self.vy); bounced = True
        elif ny >= sh - SIZE:
            ny = sh - SIZE; self.vy = -abs(self.vy); bounced = True

        if bounced and now - self._last_collision > COLLISION_COOLDOWN:
            self._last_collision = now
            self._confused_shake()

        self.geometry(f"+{int(nx)}+{int(ny)}")
        self.after(40, self._move_loop)

    # ── Sleep / Wake ────────────────────────────────────────

    def _sleep(self):
        self._sleeping = True
        _state_mod.set(State.SLEEPING)
        x = self.winfo_x()
        bottom = self.winfo_screenheight() - SIZE - 4
        self.geometry(f"+{x}+{bottom}")
        self._cur_state = State.SLEEPING
        self._frame_idx = 0
        self.after(200, self._move_loop)

    def _wake(self):
        self._sleeping = False
        self._last_activity = time.time()
        _state_mod.set(State.WAKING)
        self._cur_state = State.WAKING
        self._frame_idx = 0
        ang = random.uniform(0, math.tau)
        spd = random.uniform(*SPEED)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.after(800, lambda: _state_mod.set(State.IDLE))
        self.after(40, self._move_loop)

    # ── Confused shake ──────────────────────────────────────

    def _confused_shake(self):
        _state_mod.set(State.ERROR)
        ox = self.winfo_x()
        oy = self.winfo_y()
        for dx in (5, -5, 3, -3, 1, -1, 0):
            self.geometry(f"+{ox+dx}+{oy}")
            self.update()
            time.sleep(0.03)
        self.after(600, lambda: _state_mod.set(State.IDLE))

    # ── Drag ────────────────────────────────────────────────

    def _on_press(self, e):
        self._dragging = False
        self._drag_ox = e.x
        self._drag_oy = e.y
        if self._sleeping:
            self._wake()

    def _on_drag(self, e):
        self._dragging = True
        nx = self.winfo_x() + e.x - self._drag_ox
        ny = self.winfo_y() + e.y - self._drag_oy
        self.geometry(f"+{nx}+{ny}")

    def _on_release(self, e):
        if not self._dragging:
            self._open_popup()
        self._dragging = False

    def _on_right_click(self, e):
        self._show_context_menu(e)

    # ── Popup ────────────────────────────────────────────────

    def _open_popup(self):
        from gui.popup import open_popup
        open_popup(self)

    # ── Right-click context menu ────────────────────────────

    def _show_context_menu(self, e):
        menu = tk.Menu(self, tearoff=0,
                       bg="#111", fg="#e2e2e2",
                       activebackground="#222",
                       activeforeground="#00d4aa",
                       font=("Consolas", 10))
        menu.add_command(label="Open HELION",   command=self._open_popup)
        menu.add_separator()
        menu.add_command(label="Sleep",         command=self._sleep)
        menu.add_command(label="Wake",          command=self._wake)
        menu.add_separator()
        from core.config import toggle
        menu.add_command(
            label="Voice: ON" if get("voice_enabled") else "Voice: OFF",
            command=lambda: toggle("voice_enabled")
        )
        menu.add_separator()
        menu.add_command(label="Quit HELION",   command=self._quit)
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _quit(self):
        log.info("HELION shutting down.")
        self.destroy()
