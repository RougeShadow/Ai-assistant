# gui/popup.py
"""
HELION v4 — Full desktop app GUI
Multi-panel: Chat · Stocks · Notes · Marketing · Settings
Mood indicator · Portfolio sidebar · Task queue
"""
import tkinter as tk
from tkinter import ttk, font as tkfont
import threading, time, json
from core.config import get, set as cfg_set
from core.log import log

# ══════════════════════════════════════════════
# DESIGN TOKENS
# ══════════════════════════════════════════════
T = {
    # Backgrounds
    "bg":          "#080c10",
    "surface":     "#0d1117",
    "surface2":    "#161b22",
    "surface3":    "#1c2230",
    "panel":       "#0f1520",

    # Borders / dividers
    "border":      "#1e2a38",
    "border2":     "#263345",

    # Text
    "text":        "#cdd9e5",
    "text_dim":    "#768390",
    "text_bright": "#e6edf3",

    # Brand accent — electric teal
    "accent":      "#39d0b0",
    "accent_dim":  "#1a7a68",
    "accent_glow": "#39d0b050",

    # Financial
    "green":       "#2ea043",
    "green_bright":"#3fb950",
    "red":         "#f85149",
    "red_dim":     "#8b2020",

    # Warnings / tools
    "amber":       "#d29922",
    "amber_dim":   "#6e4f00",
    "purple":      "#8b5cf6",
    "blue":        "#2f81f7",

    # UI states
    "user_bg":     "#0d2030",
    "bot_bg":      "#0d1117",
    "hover":       "#1c2a3a",
    "selected":    "#1f3044",
    "input_bg":    "#0d1520",
}

MOOD_COLORS = {
    "FOCUSED":    "#39d0b0",
    "CURIOUS":    "#2f81f7",
    "SHARP":      "#f85149",
    "CALM":       "#768390",
    "ENERGISED":  "#d29922",
    "REFLECTIVE": "#8b5cf6",
    "GRUMPY":     "#e36209",
}

MOOD_ICONS = {
    "FOCUSED":    "◎",
    "CURIOUS":    "◉",
    "SHARP":      "◈",
    "CALM":       "○",
    "ENERGISED":  "◆",
    "REFLECTIVE": "◇",
    "GRUMPY":     "●",
}

# Fonts
F = {
    "mono_sm":    ("Consolas", 8),
    "mono":       ("Consolas", 10),
    "mono_md":    ("Consolas", 11),
    "mono_lg":    ("Consolas", 13, "bold"),
    "ui":         ("Segoe UI", 9),
    "ui_md":      ("Segoe UI", 10),
    "ui_bold":    ("Segoe UI", 10, "bold"),
    "ui_lg":      ("Segoe UI", 13, "bold"),
    "chat":       ("Segoe UI", 11),
    "num":        ("Consolas", 12, "bold"),
    "num_sm":     ("Consolas", 10),
}


_popup_instance = None

def open_popup(parent):
    global _popup_instance
    try:
        if _popup_instance and _popup_instance.winfo_exists():
            _popup_instance.lift()
            _popup_instance.focus()
            return
    except Exception:
        pass
    _popup_instance = HelionApp(parent)


class HelionApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg=T["bg"])
        self.title("HELION")
        self.geometry("1020x680")
        self.minsize(800, 500)
        self.attributes("-topmost", False)  # Don't force on top for app feel

        self._processing = False
        self._current_tab = "chat"
        self._task_queue = []   # background tasks
        self._mood = "FOCUSED"

        self._build_ui()
        self._bind_keys()
        self._start_background_tickers()

        # Welcome
        self._add_bot_message("HELION v4 online. Chat · Stocks · Marketing · Notes — all in one place.")

    # ══════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════

    def _build_ui(self):
        # ── Top bar ──────────────────────────
        topbar = tk.Frame(self, bg=T["surface"], height=48)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # Left: Brand
        brand_frame = tk.Frame(topbar, bg=T["surface"])
        brand_frame.pack(side="left", padx=16, pady=8)

        tk.Label(brand_frame, text="⬡ HELION", bg=T["surface"], fg=T["accent"],
                 font=("Consolas", 15, "bold")).pack(side="left")
        tk.Label(brand_frame, text=" v4", bg=T["surface"], fg=T["accent_dim"],
                 font=("Consolas", 9)).pack(side="left", pady=4)

        # Centre: Tab bar
        tab_frame = tk.Frame(topbar, bg=T["surface"])
        tab_frame.pack(side="left", padx=32, pady=0)

        self._tab_buttons = {}
        tabs = [
            ("chat",      "💬  CHAT"),
            ("stocks",    "📈  STOCKS"),
            ("marketing", "🚀  MARKETING"),
            ("notes",     "📝  NOTES"),
            ("settings",  "⚙   SETTINGS"),
        ]
        for tab_id, label in tabs:
            btn = tk.Button(
                tab_frame, text=label,
                bg=T["surface"], fg=T["text_dim"],
                font=F["mono_sm"], relief="flat", bd=0,
                cursor="hand2", padx=12, pady=4,
                activebackground=T["surface2"],
                activeforeground=T["accent"],
                command=lambda tid=tab_id: self._switch_tab(tid)
            )
            btn.pack(side="left", padx=2)
            self._tab_buttons[tab_id] = btn

        # Right: mood + status
        right_frame = tk.Frame(topbar, bg=T["surface"])
        right_frame.pack(side="right", padx=16)

        self._mood_label = tk.Label(right_frame, text="◎ FOCUSED",
                                     bg=T["surface"], fg=T["accent"],
                                     font=F["mono_sm"])
        self._mood_label.pack(side="right", padx=8)

        self._status_dot = tk.Label(right_frame, text="●",
                                     bg=T["surface"], fg=T["green_bright"],
                                     font=F["mono_sm"])
        self._status_dot.pack(side="right")

        tk.Frame(self, bg=T["border"], height=1).pack(fill="x")

        # ── Body ─────────────────────────────
        self._body = tk.Frame(self, bg=T["bg"])
        self._body.pack(fill="both", expand=True)

        # Build all tabs (hidden by default)
        self._panels = {}
        self._build_chat_panel()
        self._build_stocks_panel()
        self._build_marketing_panel()
        self._build_notes_panel()
        self._build_settings_panel()

        self._switch_tab("chat")

    # ══════════════════════════════════════════
    # TAB SWITCHING
    # ══════════════════════════════════════════

    def _switch_tab(self, tab_id):
        # Hide all panels
        for panel in self._panels.values():
            panel.pack_forget()

        # Reset all tab buttons
        for tid, btn in self._tab_buttons.items():
            btn.configure(
                fg=T["text_dim"] if tid != tab_id else T["accent"],
                bg=T["surface"] if tid != tab_id else T["surface2"],
            )

        # Show target panel
        self._panels[tab_id].pack(fill="both", expand=True)
        self._current_tab = tab_id

        # Auto-refresh
        if tab_id == "stocks":
            self.after(100, self._refresh_portfolio_display)
        elif tab_id == "notes":
            self.after(100, self._refresh_notes_display)

    # ══════════════════════════════════════════
    # CHAT PANEL
    # ══════════════════════════════════════════

    def _build_chat_panel(self):
        panel = tk.Frame(self._body, bg=T["bg"])
        self._panels["chat"] = panel

        # Main layout: sidebar + chat
        pane = tk.Frame(panel, bg=T["bg"])
        pane.pack(fill="both", expand=True)

        # ── Left sidebar: task queue + quick actions ──
        sidebar = tk.Frame(pane, bg=T["panel"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="QUICK ACTIONS", bg=T["panel"],
                 fg=T["text_dim"], font=F["mono_sm"], pady=8).pack(fill="x", padx=10)

        quick_actions = [
            ("Stock market summary", "📊"),
            ("Today's news", "📰"),
            ("Weather here", "🌤"),
            ("My notes", "📝"),
            ("Portfolio check", "💼"),
            ("Set 25min timer", "⏱"),
        ]
        for text, icon in quick_actions:
            btn = tk.Button(
                sidebar, text=f"{icon}  {text}",
                bg=T["panel"], fg=T["text_dim"],
                font=F["ui"], relief="flat", bd=0,
                cursor="hand2", anchor="w", padx=10, pady=4,
                activebackground=T["hover"],
                activeforeground=T["text"],
                command=lambda t=text: self._quick_send(t)
            )
            btn.pack(fill="x", padx=4, pady=1)

        tk.Frame(sidebar, bg=T["border"], height=1).pack(fill="x", pady=8, padx=8)

        tk.Label(sidebar, text="TASKS", bg=T["panel"],
                 fg=T["text_dim"], font=F["mono_sm"]).pack(fill="x", padx=10)
        self._task_list = tk.Frame(sidebar, bg=T["panel"])
        self._task_list.pack(fill="both", expand=True, padx=6)

        # ── Right: chat + input ──
        chat_area = tk.Frame(pane, bg=T["bg"])
        chat_area.pack(side="left", fill="both", expand=True)

        # Chat messages scrollable canvas
        self._chat_frame = tk.Frame(chat_area, bg=T["bg"])
        self._chat_frame.pack(fill="both", expand=True)

        self._chat_canvas = tk.Canvas(self._chat_frame, bg=T["bg"],
                                       highlightthickness=0, bd=0)
        self._chat_scrollbar = tk.Scrollbar(self._chat_frame, orient="vertical",
                                             command=self._chat_canvas.yview,
                                             bg=T["surface"], troughcolor=T["bg"],
                                             relief="flat", bd=0)
        self._chat_canvas.configure(yscrollcommand=self._chat_scrollbar.set)
        self._chat_scrollbar.pack(side="right", fill="y")
        self._chat_canvas.pack(side="left", fill="both", expand=True)

        self._messages_frame = tk.Frame(self._chat_canvas, bg=T["bg"])
        self._canvas_window = self._chat_canvas.create_window(
            (0, 0), window=self._messages_frame, anchor="nw"
        )

        self._messages_frame.bind("<Configure>", self._on_messages_configure)
        self._chat_canvas.bind("<Configure>", self._on_canvas_configure)
        self._chat_canvas.bind("<MouseWheel>", lambda e: self._chat_canvas.yview_scroll(-1*(e.delta//120), "units"))

        # ── Input area ──
        tk.Frame(chat_area, bg=T["border"], height=1).pack(fill="x")

        inp_frame = tk.Frame(chat_area, bg=T["surface"], pady=10, padx=12)
        inp_frame.pack(fill="x")

        self._chat_entry = tk.Entry(
            inp_frame,
            bg=T["input_bg"], fg=T["text_bright"],
            insertbackground=T["accent"],
            font=("Segoe UI", 12),
            relief="flat", bd=0,
        )
        self._chat_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

        send_btn = tk.Button(
            inp_frame, text="SEND ↵",
            bg=T["accent_dim"], fg=T["accent"],
            font=F["mono"], relief="flat", bd=0,
            cursor="hand2", padx=12, pady=6,
            activebackground=T["accent"],
            activeforeground=T["bg"],
            command=self._submit
        )
        send_btn.pack(side="right")

        hint = tk.Label(chat_area, text="Enter  send   ·   Ctrl+L  clear   ·   Esc  close   ·   Tab  switch panels",
                        bg=T["bg"], fg=T["text_dim"], font=F["mono_sm"], pady=3)
        hint.pack(fill="x")

    def _on_messages_configure(self, event):
        self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._chat_canvas.itemconfig(self._canvas_window, width=event.width)

    def _add_user_message(self, text):
        self._add_message_bubble(text, role="user")

    def _add_bot_message(self, text, mood=None):
        self._add_message_bubble(text, role="bot", mood=mood)

    def _add_tool_message(self, tool_name, preview):
        frame = tk.Frame(self._messages_frame, bg=T["bg"], pady=2)
        frame.pack(fill="x", padx=16)
        tk.Label(frame, text=f"⚙ {tool_name}", bg=T["bg"], fg=T["amber"],
                 font=F["mono_sm"]).pack(side="left")
        tk.Label(frame, text=" → " + preview[:80].replace("\n", " "),
                 bg=T["bg"], fg=T["text_dim"], font=F["mono_sm"]).pack(side="left")
        self._scroll_to_bottom()

    def _add_message_bubble(self, text, role="bot", mood=None):
        is_user = role == "user"

        outer = tk.Frame(self._messages_frame, bg=T["bg"], pady=4)
        outer.pack(fill="x", padx=10)

        # Label row
        label_row = tk.Frame(outer, bg=T["bg"])
        label_row.pack(fill="x", padx=6)

        if is_user:
            label_color = T["blue"]
            label_text = "you"
        else:
            mood_color = MOOD_COLORS.get(mood or self._mood, T["accent"])
            mood_icon = MOOD_ICONS.get(mood or self._mood, "◈")
            label_color = mood_color
            label_text = f"{mood_icon} helion"

        tk.Label(label_row, text=label_text, bg=T["bg"], fg=label_color,
                 font=F["mono_sm"]).pack(side="left")

        # Timestamp
        ts = time.strftime("%H:%M")
        tk.Label(label_row, text=ts, bg=T["bg"], fg=T["text_dim"],
                 font=F["mono_sm"]).pack(side="left", padx=6)

        # Bubble
        bubble_bg = T["user_bg"] if is_user else T["surface"]
        bubble = tk.Frame(outer, bg=bubble_bg,
                           highlightbackground=T["border"],
                           highlightthickness=1)
        bubble.pack(fill="x", padx=4, pady=2)

        # Text widget for selectable, wrapping text
        txt = tk.Text(
            bubble,
            bg=bubble_bg, fg=T["text_bright"] if not is_user else T["text"],
            font=F["chat"],
            relief="flat", bd=0,
            wrap="word",
            padx=12, pady=8,
            cursor="arrow",
            state="normal",
            height=1,
        )
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        # Auto-height
        lines = text.count("\n") + max(1, len(text) // 80)
        txt.configure(height=min(lines + 1, 20))
        txt.pack(fill="x")

        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self.after(50, lambda: self._chat_canvas.yview_moveto(1.0))

    def _quick_send(self, text):
        self._chat_entry.delete(0, "end")
        self._chat_entry.insert(0, text)
        self._submit()

    # ══════════════════════════════════════════
    # STOCKS PANEL
    # ══════════════════════════════════════════

    def _build_stocks_panel(self):
        panel = tk.Frame(self._body, bg=T["bg"])
        self._panels["stocks"] = panel

        # Top action bar
        action_bar = tk.Frame(panel, bg=T["surface"], pady=8, padx=12)
        action_bar.pack(fill="x")

        tk.Label(action_bar, text="Symbol:", bg=T["surface"], fg=T["text_dim"],
                 font=F["ui"]).pack(side="left")
        self._stock_entry = tk.Entry(
            action_bar, bg=T["input_bg"], fg=T["text_bright"],
            insertbackground=T["accent"], font=F["mono_md"],
            relief="flat", bd=0, width=14
        )
        self._stock_entry.pack(side="left", padx=6, ipady=4)
        self._stock_entry.bind("<Return>", lambda e: self._lookup_stock())

        tk.Button(action_bar, text="LOOK UP", bg=T["accent_dim"], fg=T["accent"],
                  font=F["mono"], relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=4, command=self._lookup_stock).pack(side="left", padx=4)

        tk.Button(action_bar, text="+ PORTFOLIO", bg=T["surface2"], fg=T["text_dim"],
                  font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=4, command=self._add_to_portfolio).pack(side="left", padx=4)

        tk.Button(action_bar, text="⟳ REFRESH", bg=T["surface2"], fg=T["text_dim"],
                  font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=4, command=self._refresh_portfolio_display).pack(side="left", padx=4)

        # Popular quick-pick buttons
        popular = ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "MSFT", "NIFTY50.NS", "RELIANCE.NS", "GOLD"]
        for sym in popular:
            tk.Button(
                action_bar, text=sym,
                bg=T["surface3"], fg=T["text_dim"],
                font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                padx=6, pady=3,
                command=lambda s=sym: self._quick_stock(s)
            ).pack(side="left", padx=2)

        tk.Frame(panel, bg=T["border"], height=1).pack(fill="x")

        # Main body: portfolio + detail
        body = tk.Frame(panel, bg=T["bg"])
        body.pack(fill="both", expand=True)

        # Portfolio sidebar
        port_sidebar = tk.Frame(body, bg=T["panel"], width=240)
        port_sidebar.pack(side="left", fill="y")
        port_sidebar.pack_propagate(False)

        tk.Label(port_sidebar, text="PORTFOLIO", bg=T["panel"],
                 fg=T["text_dim"], font=F["mono_sm"], pady=8).pack(fill="x", padx=10)

        self._portfolio_frame = tk.Frame(port_sidebar, bg=T["panel"])
        self._portfolio_frame.pack(fill="both", expand=True, padx=4)

        tk.Frame(port_sidebar, bg=T["border"], height=1).pack(fill="x", pady=4)
        tk.Button(port_sidebar, text="Manage portfolio →",
                  bg=T["panel"], fg=T["text_dim"], font=F["mono_sm"],
                  relief="flat", bd=0, cursor="hand2",
                  command=self._open_portfolio_manager).pack(pady=4)

        # Detail area
        detail = tk.Frame(body, bg=T["bg"])
        detail.pack(side="left", fill="both", expand=True)

        self._stock_detail = tk.Text(
            detail,
            bg=T["bg"], fg=T["text_bright"],
            font=("Consolas", 11),
            relief="flat", bd=0,
            wrap="word", padx=20, pady=16,
            state="disabled",
        )
        self._stock_detail.pack(fill="both", expand=True)
        self._stock_detail.tag_configure("green", foreground=T["green_bright"])
        self._stock_detail.tag_configure("red", foreground=T["red"])
        self._stock_detail.tag_configure("amber", foreground=T["amber"])
        self._stock_detail.tag_configure("accent", foreground=T["accent"])
        self._stock_detail.tag_configure("dim", foreground=T["text_dim"])
        self._stock_detail.tag_configure("big", font=("Consolas", 18, "bold"))

        self._set_stock_detail("Enter a ticker symbol above (e.g. AAPL, BTC-USD, RELIANCE.NS)\nor click a quick-pick button.\n\nYour portfolio shows on the left.")

    def _set_stock_detail(self, text):
        self._stock_detail.configure(state="normal")
        self._stock_detail.delete("1.0", "end")
        self._stock_detail.insert("end", text)
        self._stock_detail.configure(state="disabled")

    def _lookup_stock(self):
        symbol = self._stock_entry.get().strip().upper()
        if not symbol:
            return
        self._set_stock_detail(f"Fetching {symbol}…")
        threading.Thread(target=self._fetch_and_show_stock, args=(symbol,), daemon=True).start()

    def _quick_stock(self, symbol):
        self._stock_entry.delete(0, "end")
        self._stock_entry.insert(0, symbol)
        self._lookup_stock()

    def _fetch_and_show_stock(self, symbol):
        from core.tools import _get_stock
        result = _get_stock({"symbol": symbol, "include_news": True}, None)
        self.after(0, lambda: self._set_stock_detail(result))

    def _add_to_portfolio(self):
        symbol = self._stock_entry.get().strip().upper()
        if not symbol:
            return
        from core.memory import add_to_portfolio
        add_to_portfolio(symbol)
        self._refresh_portfolio_display()

    def _open_portfolio_manager(self):
        from core.memory import get_portfolio_symbols, remove_from_portfolio

        win = tk.Toplevel(self)
        win.title("Portfolio Manager")
        win.configure(bg=T["bg"])
        win.geometry("320x400")

        tk.Label(win, text="YOUR PORTFOLIO", bg=T["bg"], fg=T["accent"],
                 font=F["mono_lg"], pady=12).pack()

        frame = tk.Frame(win, bg=T["bg"])
        frame.pack(fill="both", expand=True, padx=16)

        def refresh():
            for w in frame.winfo_children():
                w.destroy()
            for sym in get_portfolio_symbols():
                row = tk.Frame(frame, bg=T["surface"], pady=4, padx=8)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=sym, bg=T["surface"], fg=T["text"],
                         font=F["mono_md"]).pack(side="left")
                tk.Button(row, text="✕", bg=T["surface"], fg=T["red"],
                          font=F["mono"], relief="flat", bd=0, cursor="hand2",
                          command=lambda s=sym: [remove_from_portfolio(s), refresh()]
                          ).pack(side="right")

        refresh()

        # Add new
        add_frame = tk.Frame(win, bg=T["bg"], pady=8, padx=16)
        add_frame.pack(fill="x")
        new_sym = tk.Entry(add_frame, bg=T["input_bg"], fg=T["text_bright"],
                           font=F["mono_md"], relief="flat", bd=0)
        new_sym.pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(add_frame, text="ADD", bg=T["accent_dim"], fg=T["accent"],
                  font=F["mono"], relief="flat", bd=0, cursor="hand2",
                  command=lambda: [
                      add_to_portfolio(new_sym.get().strip().upper()),
                      new_sym.delete(0, "end"), refresh()
                  ]).pack(side="right", padx=4)

    def _refresh_portfolio_display(self):
        from core.memory import get_portfolio_symbols
        symbols = get_portfolio_symbols()

        for w in self._portfolio_frame.winfo_children():
            w.destroy()

        if not symbols:
            tk.Label(self._portfolio_frame, text="No symbols.\nAdd one above.",
                     bg=T["panel"], fg=T["text_dim"], font=F["ui"],
                     justify="center").pack(pady=20)
            return

        for sym in symbols:
            card = tk.Frame(self._portfolio_frame, bg=T["surface"],
                            highlightbackground=T["border"], highlightthickness=1)
            card.pack(fill="x", pady=2, padx=2)
            tk.Label(card, text=sym, bg=T["surface"], fg=T["text"],
                     font=F["mono"], padx=8, pady=4).pack(side="left")
            lbl = tk.Label(card, text="…", bg=T["surface"], fg=T["text_dim"],
                           font=F["num_sm"])
            lbl.pack(side="right", padx=6)
            card.bind("<Button-1>", lambda e, s=sym: self._quick_stock(s))
            # Fetch in bg
            threading.Thread(target=self._update_portfolio_card,
                             args=(sym, lbl), daemon=True).start()

    def _update_portfolio_card(self, symbol, label_widget):
        try:
            from core.tools import _get_stock
            result = _get_stock({"symbol": symbol}, None)
            lines = result.split("\n")
            # Parse price and change from result
            price_line = next((l for l in lines if "Price:" in l), "")
            change_line = next((l for l in lines if "Change:" in l), "")

            price = price_line.replace("Price:", "").strip().split()[-1] if price_line else "?"
            is_up = "▲" in change_line
            color = T["green_bright"] if is_up else T["red"]
            change_val = ""
            if change_line:
                parts = change_line.split()
                if len(parts) >= 2:
                    change_val = " ".join(parts[1:3])

            def update():
                try:
                    label_widget.configure(text=f"{price}\n{change_val}", fg=color)
                except Exception:
                    pass
            self.after(0, update)
        except Exception:
            pass

    # ══════════════════════════════════════════
    # MARKETING PANEL
    # ══════════════════════════════════════════

    def _build_marketing_panel(self):
        panel = tk.Frame(self._body, bg=T["bg"])
        self._panels["marketing"] = panel

        # Controls
        ctrl = tk.Frame(panel, bg=T["surface"], pady=10, padx=16)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Product / Brand:", bg=T["surface"], fg=T["text_dim"],
                 font=F["ui"]).pack(side="left")
        self._mkt_product = tk.Entry(ctrl, bg=T["input_bg"], fg=T["text_bright"],
                                      font=F["chat"], relief="flat", bd=0, width=28)
        self._mkt_product.pack(side="left", padx=8, ipady=4)
        self._mkt_product.insert(0, "HELION AI Assistant")

        tk.Label(ctrl, text="Type:", bg=T["surface"], fg=T["text_dim"],
                 font=F["ui"]).pack(side="left", padx=(16, 4))
        self._mkt_type = ttk.Combobox(ctrl, values=[
            "tagline", "ad_copy", "social_post", "email", "pitch", "slogan"
        ], width=12, state="readonly", font=F["ui"])
        self._mkt_type.set("tagline")
        self._mkt_type.pack(side="left", padx=4)

        tk.Label(ctrl, text="Tone:", bg=T["surface"], fg=T["text_dim"],
                 font=F["ui"]).pack(side="left", padx=(12, 4))
        self._mkt_tone = ttk.Combobox(ctrl, values=[
            "bold", "luxury", "playful", "urgent", "minimal", "witty", "professional"
        ], width=12, state="readonly", font=F["ui"])
        self._mkt_tone.set("bold")
        self._mkt_tone.pack(side="left", padx=4)

        tk.Button(ctrl, text="GENERATE ⚡",
                  bg=T["accent_dim"], fg=T["accent"],
                  font=F["mono"], relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=6,
                  command=self._generate_marketing).pack(side="left", padx=12)

        tk.Frame(panel, bg=T["border"], height=1).pack(fill="x")

        # Output area with copy button
        output_top = tk.Frame(panel, bg=T["surface"], pady=6, padx=12)
        output_top.pack(fill="x")
        tk.Label(output_top, text="OUTPUT", bg=T["surface"], fg=T["text_dim"],
                 font=F["mono_sm"]).pack(side="left")
        tk.Button(output_top, text="COPY", bg=T["surface2"], fg=T["text_dim"],
                  font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=2, command=self._copy_marketing).pack(side="right")
        tk.Button(output_top, text="SAVE TO NOTES", bg=T["surface2"], fg=T["text_dim"],
                  font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=2, command=self._save_marketing_to_notes).pack(side="right", padx=4)

        self._mkt_output = tk.Text(
            panel, bg=T["surface"], fg=T["text_bright"],
            font=("Segoe UI", 12),
            relief="flat", bd=0,
            wrap="word", padx=20, pady=16,
        )
        self._mkt_output.pack(fill="both", expand=True)
        self._mkt_output.insert("1.0", "Enter your product/brand above and click GENERATE.\n\n"
                                 "HELION will craft copy tailored to your tone and format.\n\n"
                                 "💡 Tips:\n"
                                 "  • Try 'tagline' + 'bold' for punchy one-liners\n"
                                 "  • Try 'social_post' + 'witty' for Twitter/X content\n"
                                 "  • Try 'pitch' + 'luxury' for investor decks\n"
                                 "  • Try 'email' + 'urgent' for campaigns")

        # History sidebar
        # (quick: show in main chat if the user wants more context)

    def _generate_marketing(self):
        product = self._mkt_product.get().strip()
        copy_type = self._mkt_type.get()
        tone = self._mkt_tone.get()

        if not product:
            self._mkt_output.delete("1.0", "end")
            self._mkt_output.insert("1.0", "Enter a product or brand name first.")
            return

        self._mkt_output.delete("1.0", "end")
        self._mkt_output.insert("1.0", f"Generating {copy_type} for '{product}'…\n")

        threading.Thread(
            target=self._do_generate_marketing,
            args=(product, copy_type, tone), daemon=True
        ).start()

    def _do_generate_marketing(self, product, copy_type, tone):
        from core.tools import _generate_marketing
        result = _generate_marketing({
            "product": product,
            "type": copy_type,
            "tone": tone
        }, None)
        def update():
            self._mkt_output.delete("1.0", "end")
            self._mkt_output.insert("1.0", result)
        self.after(0, update)

    def _copy_marketing(self):
        text = self._mkt_output.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)

    def _save_marketing_to_notes(self):
        text = self._mkt_output.get("1.0", "end-1c")[:500]
        from core.memory import add_note
        add_note(f"[Marketing] {text[:200]}…")
        self._switch_tab("notes")
        self.after(200, self._refresh_notes_display)

    # ══════════════════════════════════════════
    # NOTES PANEL
    # ══════════════════════════════════════════

    def _build_notes_panel(self):
        panel = tk.Frame(self._body, bg=T["bg"])
        self._panels["notes"] = panel

        # Quick add bar
        add_bar = tk.Frame(panel, bg=T["surface"], pady=8, padx=12)
        add_bar.pack(fill="x")

        self._note_entry = tk.Entry(add_bar, bg=T["input_bg"], fg=T["text_bright"],
                                     insertbackground=T["accent"],
                                     font=F["chat"], relief="flat", bd=0)
        self._note_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        self._note_entry.insert(0, "Quick note…")
        self._note_entry.bind("<FocusIn>", lambda e: self._note_entry_focus())
        self._note_entry.bind("<Return>", lambda e: self._quick_add_note())

        tk.Button(add_bar, text="ADD NOTE", bg=T["accent_dim"], fg=T["accent"],
                  font=F["mono"], relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=5, command=self._quick_add_note).pack(side="right")

        tk.Frame(panel, bg=T["border"], height=1).pack(fill="x")

        # Notes list
        self._notes_canvas = tk.Canvas(panel, bg=T["bg"], highlightthickness=0)
        notes_scrollbar = tk.Scrollbar(panel, orient="vertical",
                                       command=self._notes_canvas.yview,
                                       bg=T["surface"])
        self._notes_canvas.configure(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.pack(side="right", fill="y")
        self._notes_canvas.pack(fill="both", expand=True)

        self._notes_inner = tk.Frame(self._notes_canvas, bg=T["bg"])
        self._notes_win = self._notes_canvas.create_window(
            (0, 0), window=self._notes_inner, anchor="nw"
        )
        self._notes_inner.bind("<Configure>",
            lambda e: self._notes_canvas.configure(scrollregion=self._notes_canvas.bbox("all")))
        self._notes_canvas.bind("<Configure>",
            lambda e: self._notes_canvas.itemconfig(self._notes_win, width=e.width))

        self._refresh_notes_display()

    def _note_entry_focus(self):
        if self._note_entry.get() == "Quick note…":
            self._note_entry.delete(0, "end")
            self._note_entry.configure(fg=T["text_bright"])

    def _quick_add_note(self):
        text = self._note_entry.get().strip()
        if not text or text == "Quick note…":
            return
        from core.memory import add_note
        add_note(text)
        self._note_entry.delete(0, "end")
        self._refresh_notes_display()

    def _refresh_notes_display(self):
        from core.memory import get_notes
        notes = get_notes(50)

        for w in self._notes_inner.winfo_children():
            w.destroy()

        if not notes:
            tk.Label(self._notes_inner, text="\n\nNo notes yet.\nAdd one above or ask HELION to 'note' something.",
                     bg=T["bg"], fg=T["text_dim"], font=F["ui"], justify="center").pack(pady=20)
            return

        for note in reversed(notes):
            card = tk.Frame(self._notes_inner, bg=T["surface"],
                            highlightbackground=T["border"], highlightthickness=1)
            card.pack(fill="x", padx=12, pady=3)

            ts_str = note.get("ts", "")[:10]
            tk.Label(card, text=ts_str, bg=T["surface"], fg=T["text_dim"],
                     font=F["mono_sm"], padx=10, pady=4).pack(side="left")
            tk.Label(card, text=note.get("text", ""), bg=T["surface"], fg=T["text"],
                     font=F["chat"], wraplength=600, justify="left",
                     padx=4, pady=4).pack(side="left", fill="x", expand=True)

    # ══════════════════════════════════════════
    # SETTINGS PANEL
    # ══════════════════════════════════════════

    def _build_settings_panel(self):
        panel = tk.Frame(self._body, bg=T["bg"])
        self._panels["settings"] = panel

        tk.Label(panel, text="SETTINGS", bg=T["bg"], fg=T["accent"],
                 font=F["mono_lg"], pady=20).pack()

        settings_area = tk.Frame(panel, bg=T["bg"])
        settings_area.pack(fill="both", expand=True, padx=60)

        def row(label, widget_factory):
            r = tk.Frame(settings_area, bg=T["surface"], pady=6, padx=16)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, bg=T["surface"], fg=T["text"],
                     font=F["ui_md"], width=24, anchor="w").pack(side="left")
            widget_factory(r)

        # Voice toggle
        self._voice_var = tk.BooleanVar(value=get("voice_enabled", True))
        row("Voice responses", lambda p: tk.Checkbutton(
            p, variable=self._voice_var, bg=T["surface"], fg=T["accent"],
            selectcolor=T["surface"], activebackground=T["surface"],
            command=lambda: cfg_set("voice_enabled", self._voice_var.get())
        ).pack(side="left"))

        # Sprite toggle
        self._sprite_var = tk.BooleanVar(value=get("sprite_enabled", True))
        row("Floating sprite", lambda p: tk.Checkbutton(
            p, variable=self._sprite_var, bg=T["surface"], fg=T["accent"],
            selectcolor=T["surface"], activebackground=T["surface"],
            command=lambda: cfg_set("sprite_enabled", self._sprite_var.get())
        ).pack(side="left"))

        # Wake word
        def wake_row(p):
            e = tk.Entry(p, bg=T["input_bg"], fg=T["text_bright"],
                         font=F["mono"], relief="flat", bd=0, width=14)
            e.insert(0, get("wake_word", "arise"))
            e.pack(side="left", padx=4, ipady=3)
            tk.Button(p, text="Save", bg=T["surface2"], fg=T["text_dim"],
                      font=F["mono_sm"], relief="flat", bd=0, cursor="hand2",
                      command=lambda: cfg_set("wake_word", e.get())).pack(side="left", padx=4)
        row("Wake word", wake_row)

        # Voice rate
        def rate_row(p):
            s = tk.Scale(p, from_=100, to=250, orient="horizontal",
                         bg=T["surface"], fg=T["text"], troughcolor=T["border"],
                         highlightthickness=0, relief="flat", bd=0,
                         command=lambda v: cfg_set("voice_rate", int(v)))
            s.set(get("voice_rate", 165))
            s.pack(side="left", padx=4)
        row("Voice rate", rate_row)

        # Sprite size
        def size_row(p):
            s = tk.Scale(p, from_=80, to=200, orient="horizontal",
                         bg=T["surface"], fg=T["text"], troughcolor=T["border"],
                         highlightthickness=0, relief="flat", bd=0,
                         command=lambda v: cfg_set("sprite_size", int(v)))
            s.set(get("sprite_size", 140))
            s.pack(side="left", padx=4)
        row("Sprite size", size_row)

        # Model info
        tk.Label(settings_area, text=f"\nModel: {get('llm_model', 'claude-sonnet-4-20250514')}",
                 bg=T["bg"], fg=T["text_dim"], font=F["mono_sm"]).pack(anchor="w", pady=8)

        # Version
        tk.Label(settings_area, text="HELION v4 — 2026 Edition",
                 bg=T["bg"], fg=T["text_dim"], font=F["mono_sm"]).pack(anchor="w")

    # ══════════════════════════════════════════
    # SUBMIT / PROCESSING
    # ══════════════════════════════════════════

    def _submit(self, _event=None):
        if self._processing:
            return
        text = self._chat_entry.get().strip()
        if not text:
            return
        self._chat_entry.delete(0, "end")
        self._add_user_message(text)
        self._set_status("thinking", T["amber"])
        self._processing = True

        threading.Thread(target=self._run, args=(text,), daemon=True).start()

    def _run(self, text):
        # Handle portfolio commands inline
        lower = text.lower()
        if any(k in lower for k in ["add to portfolio", "track "]):
            import re
            match = re.search(r'\b([A-Z]{1,5}(?:-[A-Z]+)?(?:\.NS|\.BSE)?)\b', text.upper())
            if match:
                from core.memory import add_to_portfolio
                sym = add_to_portfolio(match.group(1))
                self.after(0, lambda: self._add_bot_message(f"Added {sym} to portfolio."))
                self.after(100, self._refresh_portfolio_display)
                self.after(0, lambda: self._set_status("ready"))
                self._processing = False
                return

        from brain.agent import process
        try:
            response = process(text, notify_fn=self._notify)
        except Exception as e:
            response = f"Error: {e}"

        # Get current mood from llm module
        try:
            from core.llm import get_mood
            mood = get_mood()
        except Exception:
            mood = "FOCUSED"

        self.after(0, lambda: self._on_done(response, mood))

    def _on_done(self, response, mood="FOCUSED"):
        self._processing = False
        self._mood = mood
        self._set_status("ready")
        self._update_mood_display(mood)
        self._add_bot_message(response, mood=mood)

        if get("voice_enabled", True):
            parts = response.split(". ")
            spoken = ". ".join(parts[:2])
            if len(spoken) > 200:
                spoken = spoken[:200] + "…"
            threading.Thread(target=self._speak, args=(spoken,), daemon=True).start()

    def _speak(self, text):
        try:
            from core.speaker import speak
            speak(text)
        except Exception:
            pass

    def _notify(self, text):
        self.after(0, lambda: self._add_bot_message(f"🔔 {text}"))

    # ══════════════════════════════════════════
    # STATUS / MOOD
    # ══════════════════════════════════════════

    def _set_status(self, state, color=None):
        states = {
            "ready":    ("●", T["green_bright"]),
            "thinking": ("◌", T["amber"]),
            "working":  ("◉", T["blue"]),
            "error":    ("✕", T["red"]),
        }
        dot, col = states.get(state, ("●", T["green_bright"]))
        self._status_dot.configure(text=dot, fg=color or col)

    def _update_mood_display(self, mood):
        icon = MOOD_ICONS.get(mood, "◈")
        color = MOOD_COLORS.get(mood, T["accent"])
        self._mood_label.configure(text=f"{icon} {mood}", fg=color)

    # ══════════════════════════════════════════
    # BACKGROUND TICKERS
    # ══════════════════════════════════════════

    def _start_background_tickers(self):
        def refresh_loop():
            while True:
                time.sleep(120)  # refresh portfolio every 2 min
                try:
                    if self._current_tab == "stocks":
                        self.after(0, self._refresh_portfolio_display)
                except Exception:
                    pass

        threading.Thread(target=refresh_loop, daemon=True).start()

    # ══════════════════════════════════════════
    # KEYBOARD BINDINGS
    # ══════════════════════════════════════════

    def _bind_keys(self):
        self._chat_entry.bind("<Return>", self._submit)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-l>", lambda e: self._clear_chat())
        self.bind("<Control-L>", lambda e: self._clear_chat())

        # Tab shortcuts
        self.bind("<Control-1>", lambda e: self._switch_tab("chat"))
        self.bind("<Control-2>", lambda e: self._switch_tab("stocks"))
        self.bind("<Control-3>", lambda e: self._switch_tab("marketing"))
        self.bind("<Control-4>", lambda e: self._switch_tab("notes"))
        self.bind("<Control-5>", lambda e: self._switch_tab("settings"))

    def _clear_chat(self):
        for w in self._messages_frame.winfo_children():
            w.destroy()
        from core.memory import clear_history
        clear_history()
        self._add_bot_message("Chat cleared.")
