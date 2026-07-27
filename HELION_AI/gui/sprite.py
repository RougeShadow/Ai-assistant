# gui/sprite.py
import tkinter as tk
import random
import os
import time
import math
from PIL import Image, ImageTk
import pyautogui

from gui.popup import CommandPopup
from core.settings import get_setting
from core.state import subscribe, set_state, get_state

SPRITE_SIZE = 150
TRANSPARENT = "blue"

SPRITES_BASE = os.path.join(
    "assets", "skins", "default", "sprites"
)

STATE_TO_FOLDER = {
    "idle": "idle",
    "listening": "listen",
    "thinking": "think",
    "speaking": "hover",
    "working": "work",
    "scanning": "scan",
    "confused": "confused",
    "sleeping": "sleep",
    "waking": "wake",
    "flying": "fly",
}

IDLE_BEFORE_SLEEP = 25
CONFUSED_TIME = 1.2
COLLISION_COOLDOWN = 1.5

CURSOR_AVOID_RADIUS = 120
CURSOR_PANIC_RADIUS = 60
AVOID_FORCE = 0.8

DIRECTION_CHANGE_INTERVAL = (2.5, 6.0)
SPEED_RANGE = (0.8, 2.5)


class HelionSprite(tk.Tk):
    def __init__(self):
        super().__init__()

        if not get_setting("sprite_enabled", True):
            self.destroy()
            return

        # Window config
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=TRANSPARENT)
        self.wm_attributes("-transparentcolor", TRANSPARENT)

        self.geometry(f"{SPRITE_SIZE}x{SPRITE_SIZE}+300+300")

        # Canvas
        self.canvas = tk.Canvas(
            self,
            width=SPRITE_SIZE,
            height=SPRITE_SIZE,
            bg=TRANSPARENT,
            highlightthickness=0
        )
        self.canvas.pack()

        # Load sprites
        self.frames = {}
        for state, folder in STATE_TO_FOLDER.items():
            path = os.path.join(SPRITES_BASE, folder)
            if not os.path.isdir(path):
                continue

            imgs = []
            for f in sorted(os.listdir(path)):
                if f.lower().endswith(".png"):
                    img = Image.open(os.path.join(path, f)).convert("RGBA")
                    img = img.resize((SPRITE_SIZE, SPRITE_SIZE), Image.NEAREST)
                    imgs.append(ImageTk.PhotoImage(img))

            if imgs:
                self.frames[state] = imgs

        if "idle" not in self.frames:
            raise RuntimeError("Missing idle sprite")

        self.current_state = "idle"
        self.frame_index = 0

        self.sprite_id = self.canvas.create_image(
            SPRITE_SIZE // 2,
            SPRITE_SIZE // 2,
            image=self.frames["idle"][0]
        )

        # Movement vector
        angle = random.uniform(0, math.tau)
        speed = random.uniform(*SPEED_RANGE)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.next_dir_change = time.time() + random.uniform(*DIRECTION_CHANGE_INTERVAL)

        self.last_collision = 0
        self.confused_until = 0
        self.last_activity = time.time()
        self.sleeping = False

        # Drag state
        self.dragging = False

        # Bindings (IMPORTANT: bind to WINDOW, not canvas)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

        subscribe(self.on_state_change)

        self.after(120, self.animate)
        self.after(40, self.move)

    # ---------------- STATE ----------------
    def on_state_change(self, state):
        self.last_activity = time.time()

        if self.sleeping and state != "sleeping":
            self.wake_up()

        if state in self.frames:
            self.current_state = state
            self.frame_index = 0

    # ---------------- ANIMATION ----------------
    def animate(self):
        frames = self.frames.get(self.current_state)
        if frames:
            self.canvas.itemconfig(
                self.sprite_id,
                image=frames[self.frame_index]
            )
            self.frame_index = (self.frame_index + 1) % len(frames)

        self.after(120, self.animate)

    # ---------------- MOVEMENT ----------------
    def move(self):
        now = time.time()

        # Sleep logic
        if not self.sleeping and get_state() == "idle" and now - self.last_activity > IDLE_BEFORE_SLEEP:
            self.go_to_sleep()
            return

        if self.sleeping:
            self.after(200, self.move)
            return

        # Recover from confused
        if self.current_state == "confused" and now > self.confused_until:
            set_state("idle")

        if get_state() == "idle":
            self.current_state = "flying"

        # Cursor avoidance
        if not self.dragging:
            cx, cy = pyautogui.position()
            sx = self.winfo_x() + SPRITE_SIZE // 2
            sy = self.winfo_y() + SPRITE_SIZE // 2

            dx = sx - cx
            dy = sy - cy
            dist = math.hypot(dx, dy)

            if dist < CURSOR_PANIC_RADIUS:
                angle = math.atan2(dy, dx)
                self.vx += math.cos(angle) * AVOID_FORCE * 2
                self.vy += math.sin(angle) * AVOID_FORCE * 2
            elif dist < CURSOR_AVOID_RADIUS:
                angle = math.atan2(dy, dx)
                self.vx += math.cos(angle) * AVOID_FORCE
                self.vy += math.sin(angle) * AVOID_FORCE

        # Direction change
        if now >= self.next_dir_change:
            angle = math.atan2(self.vy, self.vx)
            angle += random.uniform(-math.pi / 3, math.pi / 3)
            speed = random.uniform(*SPEED_RANGE)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.next_dir_change = now + random.uniform(*DIRECTION_CHANGE_INTERVAL)

        x = self.winfo_x() + self.vx
        y = self.winfo_y() + self.vy

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        collided = False

        if x <= 0 or x >= sw - SPRITE_SIZE:
            self.vx *= -1
            collided = True
        if y <= 0 or y >= sh - SPRITE_SIZE:
            self.vy *= -1
            collided = True

        if collided and now - self.last_collision > COLLISION_COOLDOWN:
            self.last_collision = now
            self.trigger_confused()

        self.geometry(f"+{int(x)}+{int(y)}")
        self.after(40, self.move)

    # ---------------- CONFUSED ----------------
    def trigger_confused(self):
        self.confused_until = time.time() + CONFUSED_TIME
        set_state("confused")

        ox, oy = self.winfo_x(), self.winfo_y()
        for dx in (-4, 4, -2, 2, 0):
            self.geometry(f"+{ox+dx}+{oy}")
            self.update()
            self.after(30)

    # ---------------- SLEEP ----------------
    def go_to_sleep(self):
        self.sleeping = True
        set_state("sleeping")

        x = self.winfo_x()
        bottom = self.winfo_screenheight() - SPRITE_SIZE - 6
        self.geometry(f"+{x}+{bottom}")

        self.current_state = "sleeping"
        self.frame_index = 0

    def wake_up(self):
        self.sleeping = False
        set_state("waking")
        self.current_state = "waking"
        self.frame_index = 0

        angle = random.uniform(0, math.tau)
        speed = random.uniform(*SPEED_RANGE)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.after(600, lambda: set_state("idle"))

    # ---------------- DRAG / CLICK ----------------
    def on_press(self, event):
        self.dragging = False
        self._drag_x = event.x
        self._drag_y = event.y

    def on_drag(self, event):
        self.dragging = True
        self.sleeping = False

        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def on_release(self, event):
        if not self.dragging:
            self.open_popup()

    # ---------------- POPUP ----------------
    def open_popup(self):
        CommandPopup(self)
