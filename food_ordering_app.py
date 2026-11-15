"""
FoodieHub - Online Food Ordering & Billing System
=================================================
A modern, animated tkinter micro front-end (standard library only).

Highlights
  * Rounded menu cards drawn on a canvas, with hover-lift + shadow
  * Veg badge, rating, favourites (heart), category chips, live search,
    veg-only switch, sort cycle, "Surprise me" button
  * Add-to-cart button turns into a quantity stepper; item "flies" to the cart
  * Cart panel: quantity controls, row flash, animated totals,
    order type selector, coupon chips, free-delivery progress bar
  * Light / Dark theme toggle
  * Checkout with progress, receipt window, confetti, live order tracker,
    save / copy bill

Run:  python food_ordering_app.py
"""

import sys
import math
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import TypedDict

# ---------------------------------------------------------------------------
# Platform fonts
# ---------------------------------------------------------------------------
if sys.platform.startswith("win"):
    UI, EMOJI, MONO = "Segoe UI", "Segoe UI Emoji", "Consolas"
elif sys.platform == "darwin":
    UI, EMOJI, MONO = "Helvetica Neue", "Apple Color Emoji", "Menlo"
else:
    UI, EMOJI, MONO = "DejaVu Sans", "Noto Color Emoji", "DejaVu Sans Mono"

# ---------------------------------------------------------------------------
# Business data
# ---------------------------------------------------------------------------
class Theme(TypedDict):
    name: str
    bg: str
    card: str
    panel: str
    input: str
    soft: str
    text: str
    muted: str
    border: str
    shadow: str
    shadow_hi: str
    tint: float
    toast: str
    toast_fg: str
    paper: str


class MenuItem(TypedDict):
    price: int
    cat: str
    emoji: str
    veg: bool
    rating: float
    desc: str


GST_RATE = 0.05
DELIVERY_FEE = 40
FREE_DELIVERY_ABOVE = 500

MENU = [
    # name, price, category, emoji, veg, rating, description
    ("Samosa (2 pcs)", 40, "Starters", "🥟", True, 4.4, "Crispy pastry with spiced potato filling"),
    ("Paneer Tikka", 190, "Starters", "🍢", True, 4.6, "Char-grilled paneer with mint chutney"),
    ("Spring Rolls", 120, "Starters", "🌯", True, 4.2, "Golden rolls stuffed with fresh veggies"),
    ("Chicken 65", 210, "Starters", "🍗", False, 4.7, "Spicy, crispy South Indian fried chicken"),
    ("Veg Biryani", 180, "Main Course", "🍛", True, 4.3, "Fragrant basmati with veggies and spices"),
    ("Chicken Biryani", 240, "Main Course", "🍲", False, 4.8, "Dum-cooked biryani served with raita"),
    ("Paneer Butter Masala", 220, "Main Course", "🧈", True, 4.5, "Creamy tomato gravy with soft paneer"),
    ("Masala Dosa", 110, "Main Course", "🥞", True, 4.6, "Crisp dosa with potato masala, chutneys"),
    ("Margherita Pizza", 299, "Fast Food", "🍕", True, 4.4, "Stone-baked with mozzarella and basil"),
    ("Veg Burger", 129, "Fast Food", "🍔", True, 4.1, "Crunchy patty, cheese and fresh lettuce"),
    ("Chicken Burger", 159, "Fast Food", "🥪", False, 4.5, "Juicy fried chicken with spicy mayo"),
    ("French Fries", 99, "Fast Food", "🍟", True, 4.0, "Salted, golden and extra crispy"),
    ("Hakka Noodles", 150, "Fast Food", "🍜", True, 4.2, "Wok-tossed noodles with crunchy veggies"),
    ("Gulab Jamun", 70, "Desserts", "🍮", True, 4.7, "Warm milk dumplings in rose syrup"),
    ("Chocolate Brownie", 99, "Desserts", "🍫", True, 4.6, "Fudgy brownie with chocolate drizzle"),
    ("Ice Cream Sundae", 130, "Desserts", "🍨", True, 4.5, "Vanilla scoops, nuts and hot fudge"),
    ("Filter Coffee", 45, "Beverages", "☕", True, 4.8, "Authentic South Indian decoction coffee"),
    ("Masala Chai", 30, "Beverages", "🍵", True, 4.5, "Ginger and cardamom spiced tea"),
    ("Fresh Lime Soda", 50, "Beverages", "🍋", True, 4.3, "Sweet, salty or mixed - refreshing"),
    ("Cold Coffee", 90, "Beverages", "🥤", True, 4.4, "Chilled, creamy and frothy"),
]
ITEMS: dict[str, MenuItem] = {
    n: {"price": p, "cat": c, "emoji": e, "veg": v, "rating": r, "desc": d}
    for n, p, c, e, v, r, d in MENU
}

CAT_COLOR = {"Starters": "#F59F00", "Main Course": "#E8590C", "Fast Food": "#E03131",
             "Desserts": "#D6336C", "Beverages": "#1C7ED6"}
CHIPS = [("All", "🍽️"), ("Starters", "🥟"), ("Main Course", "🍛"), ("Fast Food", "🍔"),
         ("Desserts", "🍮"), ("Beverages", "🥤"), ("Favorites", "❤️")]
SORTS = ["Recommended", "Price: Low → High", "Price: High → Low", "Top Rated"]

COUPONS = {  # code: (kind, value, min_subtotal, description)
    "SAVE10": ("percent", 10, 0, "10% off"),
    "FOOD20": ("percent", 20, 400, "20% off above ₹400"),
    "FLAT50": ("flat", 50, 300, "Flat ₹50 off above ₹300"),
}

STAGES = {
    "Delivery": [("Order confirmed ✔", "Confirmed"), ("The chef is preparing your food 👨‍🍳", "Preparing"),
                 ("Out for delivery 🛵", "On the way"), ("Delivered - enjoy! 🎉", "Delivered")],
    "Takeaway": [("Order confirmed ✔", "Confirmed"), ("The chef is preparing your food 👨‍🍳", "Preparing"),
                 ("Ready for pickup 🥡", "Ready"), ("Picked up - enjoy! 🎉", "Picked up")],
    "Dine-in": [("Order confirmed ✔", "Confirmed"), ("The chef is preparing your food 👨‍🍳", "Preparing"),
                ("Being served to your table 🍽️", "Serving"), ("Bon appétit! 🎉", "Served")],
}

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
PRIMARY, PRIMARY_D = "#FF6B2C", "#E5521A"
GREEN, RED, STAR = "#2FB344", "#E5484D", "#F08C00"

LIGHT: Theme = {
    "name": "light", "bg": "#F6F1EB", "card": "#FFFFFF", "panel": "#FFFFFF", "input": "#FFFFFF",
    "soft": "#F3EDE6", "text": "#241F1B", "muted": "#7D746B", "border": "#EAE3DB",
    "shadow": "#E6DED4", "shadow_hi": "#D3C8BB", "tint": 0.17,
    "toast": "#2B2622", "toast_fg": "#FFFFFF", "paper": "#FFFDF8",
}
DARK: Theme = {
    "name": "dark", "bg": "#151210", "card": "#211C19", "panel": "#1C1815", "input": "#2A2420",
    "soft": "#2D2723", "text": "#F6EFE8", "muted": "#A59B91", "border": "#332C27",
    "shadow": "#0E0C0B", "shadow_hi": "#050404", "tint": 0.30,
    "toast": "#F6EFE8", "toast_fg": "#241F1B", "paper": "#262019",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def money(x):
    return f"₹{x:,.2f}"


def rs(x):
    return f"₹{x:,.0f}" if abs(x - round(x)) < 0.005 else f"₹{x:,.2f}"


def lerp_color(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


def rrect(c, x1, y1, x2, y2, r=12, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


class Btn(tk.Label):
    """Flat button with hover + pressed feedback."""

    def __init__(self, parent, text, command, bg=PRIMARY, fg="white", font=None,
                 padx=14, pady=7, hover=None, **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font or (UI, 10, "bold"),
                         padx=padx, pady=pady, cursor="hand2", **kw)
        self.command = command
        self.recolor(bg, hover)
        self.bind("<Enter>", lambda e: self.config(bg=self.hover))
        self.bind("<Leave>", lambda e: self.config(bg=self.base))
        self.bind("<ButtonPress-1>", lambda e: self.config(bg=self.press))
        self.bind("<ButtonRelease-1>", self._release)

    def recolor(self, bg, hover=None):
        self.base = bg
        self.hover = hover or lerp_color(bg, "#000000", 0.10)
        self.press = lerp_color(bg, "#000000", 0.22)
        self.config(bg=bg)

    def _release(self, e):
        inside = 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height()
        try:
            self.config(bg=self.hover if inside else self.base)
        except tk.TclError:
            return
        if inside and self.command:
            self.command()


class AnimatedNumber:
    """Counts a label smoothly from its current value to a new value."""

    def __init__(self, widget, fmt=money, value=0.0):
        self.w, self.fmt, self.cur, self.job = widget, fmt, value, None
        widget.config(text=fmt(value))

    def set(self, target, frames=10):
        try:
            root = self.w.winfo_toplevel()
            if self.job:
                root.after_cancel(self.job)
        except tk.TclError:
            return
        start = self.cur
        if abs(target - start) < 0.005:
            self.cur = target
            self.w.config(text=self.fmt(target))
            return

        def step(i=1):
            try:
                t = i / frames
                e = 1 - (1 - t) ** 3
                self.cur = start + (target - start) * e
                self.w.config(text=self.fmt(self.cur))
                if i < frames:
                    self.job = root.after(16, step, i + 1)
                else:
                    self.cur = target
            except tk.TclError:
                pass
        step()


class Toggle(tk.Canvas):
    """Animated on/off switch."""

    def __init__(self, parent, on, bg, command, on_color=GREEN, off_color="#C9C2BA"):
        super().__init__(parent, width=46, height=26, bg=bg, highlightthickness=0, cursor="hand2")
        self.on, self.command = on, command
        self.on_color, self.off_color = on_color, off_color
        self.pos = 1.0 if on else 0.0
        self.bind("<Button-1>", self.flip)
        self._draw()

    def _draw(self):
        self.delete("all")
        rrect(self, 2, 2, 44, 24, 11, fill=lerp_color(self.off_color, self.on_color, self.pos), outline="")
        x = 13 + 20 * self.pos
        self.create_oval(x - 9, 4, x + 9, 22, fill="white", outline="")

    def flip(self, _=None):
        self.on = not self.on
        self.command(self.on)
        self._anim()

    def _anim(self):
        try:
            target = 1.0 if self.on else 0.0
            if abs(self.pos - target) < 0.05:
                self.pos = target
                self._draw()
                return
            self.pos += 0.22 if target > self.pos else -0.22
            self._draw()
            self.winfo_toplevel().after(14, self._anim)
        except tk.TclError:
            pass


class ScrollFrame(tk.Frame):
    """Vertically scrollable frame; put widgets into `.inner`."""

    def __init__(self, parent, bg, style="Vertical.TScrollbar", **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, yscrollincrement=20)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style=style)
        self.inner = tk.Frame(self.canvas, bg=bg)
        win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(win, width=e.width))


# ---------------------------------------------------------------------------
# Menu cards (canvas-drawn)
# ---------------------------------------------------------------------------
class MenuView(tk.Frame):
    MIN_W, GAP, CARD_H = 225, 16, 232

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.T["bg"])
        self.app, self.T = app, app.T
        self.canvas = tk.Canvas(self, bg=self.T["bg"], highlightthickness=0, yscrollincrement=24)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.names, self.empty_msg = [], ""
        self.cards = {}
        self._hover = None
        self._uid = 0
        self._width = 0
        self._job = None

        self.canvas.bind("<Configure>", self._on_config)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))

    # ---- layout ----
    def set_items(self, names, empty_msg=""):
        self.names, self.empty_msg = names, empty_msg
        self.layout(keep_scroll=False)

    def _on_config(self, e):
        if abs(e.width - self._width) < 2:
            return
        self._width = e.width
        if self._job:
            self.app.root.after_cancel(self._job)
        self._job = self.app.root.after(40, self._relayout)

    def _relayout(self):
        try:
            self.layout()
        except tk.TclError:
            pass

    def _tag(self):
        self._uid += 1
        return f"t{self._uid}"

    def layout(self, keep_scroll=True):
        c, T = self.canvas, self.T
        for g in self.cards.values():
            if g["anim"]:
                self.app.root.after_cancel(g["anim"])
        frac = c.yview()[0] if keep_scroll else 0
        c.delete("all")
        self.cards.clear()
        self._hover = None
        W = max(c.winfo_width(), 320)

        if not self.names:
            c.create_text(W / 2, 120, text="🍽️", font=(EMOJI, 46))
            c.create_text(W / 2, 190, text="Nothing found", font=(UI, 15, "bold"), fill=T["text"])
            c.create_text(W / 2, 218, text=self.empty_msg, font=(UI, 10), fill=T["muted"])
            c.configure(scrollregion=(0, 0, W, 300))
            return

        cols = max(1, int((W - self.GAP) // (self.MIN_W + self.GAP)))
        cw = (W - self.GAP * (cols + 1)) / cols
        for i, name in enumerate(self.names):
            r, col = divmod(i, cols)
            x = self.GAP + col * (cw + self.GAP)
            y = 8 + r * (self.CARD_H + self.GAP)
            self._draw_card(i, name, x, y, cw)
        rows = math.ceil(len(self.names) / cols)
        c.configure(scrollregion=(0, 0, W, rows * (self.CARD_H + self.GAP) + 20))
        c.yview_moveto(frac)

    def _draw_card(self, i, name, x, y, w):
        c, T, it = self.canvas, self.T, ITEMS[name]
        h, cd = self.CARD_H, f"cd{i}"
        tint = lerp_color(T["card"], CAT_COLOR[it["cat"]], T["tint"])

        rrect(c, x + 4, y + 7, x + w - 4, y + h + 3, 18, fill=T["shadow"], outline="", tags=(f"sh{i}",))
        rrect(c, x, y, x + w, y + h, 18, fill=T["card"], outline=T["border"], tags=(cd,))
        rrect(c, x + 8, y + 8, x + w - 8, y + 112, 14, fill=tint, outline="", tags=(cd,))
        c.create_text(x + w / 2, y + 60, text=it["emoji"], font=(EMOJI, 42), tags=(cd,))

        vc = GREEN if it["veg"] else RED            # veg / non-veg mark
        c.create_rectangle(x + 18, y + 18, x + 34, y + 34, outline=vc, width=2, fill=T["card"], tags=(cd,))
        c.create_oval(x + 22, y + 22, x + 30, y + 30, fill=vc, outline="", tags=(cd,))

        rrect(c, x + w - 66, y + 17, x + w - 18, y + 37, 10, fill=T["card"], outline="", tags=(cd,))
        c.create_text(x + w - 42, y + 27, text=f"★ {it['rating']}", font=(UI, 9, "bold"), fill=STAR, tags=(cd,))

        c.create_text(x + 14, y + 124, text=name, anchor="nw", font=(UI, 11, "bold"),
                      fill=T["text"], width=w - 28, tags=(cd,))
        c.create_text(x + 14, y + 147, text=it["desc"], anchor="nw", font=(UI, 9),
                      fill=T["muted"], width=w - 28, tags=(cd,))
        c.create_text(x + 14, y + h - 30, text=rs(it["price"]), anchor="w", font=(UI, 15, "bold"),
                      fill=PRIMARY, tags=(cd,))

        self.cards[name] = dict(i=i, x=x, y=y, w=w, lift=0, target=0, anim=None)
        self._draw_heart(name)
        self._draw_ctl(name)

    # ---- interactive pieces ----
    def _wire(self, tag, shape, fill, hover, cb):
        c = self.canvas
        c.tag_bind(tag, "<Enter>", lambda e: (c.config(cursor="hand2"), c.itemconfig(shape, fill=hover)))
        c.tag_bind(tag, "<Leave>", lambda e: (c.config(cursor=""), c.itemconfig(shape, fill=fill)))
        c.tag_bind(tag, "<Button-1>", lambda e: cb())

    def _pill(self, x1, y1, x2, y2, text, fill, hover, tags, cb):
        c, tag = self.canvas, self._tag()
        shape = rrect(c, x1, y1, x2, y2, (y2 - y1) / 2, fill=fill, outline="", tags=tags + (tag,))
        c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="white",
                      font=(UI, 10, "bold"), tags=tags + (tag,))
        self._wire(tag, shape, fill, hover, cb)

    def _circle(self, cx, cy, r, text, fill, hover, fg, tags, cb):
        c, tag = self.canvas, self._tag()
        shape = c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline="", tags=tags + (tag,))
        c.create_text(cx, cy - 1, text=text, fill=fg, font=(UI, 13, "bold"), tags=tags + (tag,))
        self._wire(tag, shape, fill, hover, cb)

    def origin(self, name):
        g = self.cards[name]
        return g["x"] + g["w"] - 30, g["y"] + g["lift"] + self.CARD_H - 30

    def _draw_heart(self, name):
        c, T, g = self.canvas, self.T, self.cards[name]
        i = g["i"]
        c.delete(f"hr{i}")
        fav = name in self.app.fav
        cx, cy = g["x"] + g["w"] - 28, g["y"] + g["lift"] + 98
        tag, tags = self._tag(), (f"cd{i}", f"hr{i}")
        oval = c.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill=T["card"], outline=T["border"],
                             tags=tags + (tag,))
        c.create_text(cx, cy - 1, text="♥" if fav else "♡", font=(UI, 14),
                      fill=RED if fav else T["muted"], tags=tags + (tag,))
        c.tag_bind(tag, "<Enter>", lambda e: (c.config(cursor="hand2"), c.itemconfig(oval, fill=T["soft"])))
        c.tag_bind(tag, "<Leave>", lambda e: (c.config(cursor=""), c.itemconfig(oval, fill=T["card"])))
        c.tag_bind(tag, "<Button-1>", lambda e: self.app.toggle_fav(name))

    def _draw_ctl(self, name):
        c, T, g = self.canvas, self.T, self.cards[name]
        i = g["i"]
        c.delete(f"ct{i}")
        qty = self.app.cart.get(name, 0)
        cy = g["y"] + g["lift"] + self.CARD_H - 30
        right = g["x"] + g["w"] - 14
        tags = (f"cd{i}", f"ct{i}")
        if qty == 0:
            self._pill(right - 88, cy - 16, right, cy + 16, "+  Add", PRIMARY, PRIMARY_D, tags,
                       lambda: self.app.add(name, self.origin(name)))
        else:
            rrect(c, right - 112, cy - 16, right, cy + 16, 16, fill=T["soft"], outline="", tags=tags)
            self._circle(right - 96, cy, 13, "−", T["card"], T["border"], T["text"], tags,
                         lambda: self.app.change(name, -1))
            c.create_text(right - 56, cy, text=str(qty), font=(UI, 12, "bold"), fill=T["text"], tags=tags)
            self._circle(right - 16, cy, 13, "+", PRIMARY, PRIMARY_D, "white", tags,
                         lambda: self.app.change(name, +1, self.origin(name)))
        c.config(cursor="")

    def update_card(self, name):
        if name in self.cards:
            self._draw_ctl(name)

    def update_all(self):
        for n in list(self.cards):
            self._draw_ctl(n)

    def update_heart(self, name):
        if name in self.cards:
            self._draw_heart(name)

    # ---- hover lift ----
    def _on_motion(self, e):
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        hit = None
        for n, g in self.cards.items():
            if g["x"] <= cx <= g["x"] + g["w"] and g["y"] - 6 <= cy <= g["y"] + self.CARD_H:
                hit = n
                break
        self._set_hover(hit)

    def _set_hover(self, name):
        if name == self._hover:
            return
        old, self._hover = self._hover, name
        for n, tgt in ((old, 0), (name, -5)):
            if n and n in self.cards:
                g = self.cards[n]
                g["target"] = tgt
                self.canvas.itemconfig(f"sh{g['i']}", fill=self.T["shadow_hi"] if tgt else self.T["shadow"])
                if g["anim"] is None:
                    self._step_lift(n)

    def _step_lift(self, name):
        g = self.cards.get(name)
        if not g:
            return
        if g["lift"] == g["target"]:
            g["anim"] = None
            return
        d = 1 if g["target"] > g["lift"] else -1
        try:
            self.canvas.move(f"cd{g['i']}", 0, d)
        except tk.TclError:
            return
        g["lift"] += d
        g["anim"] = self.app.root.after(10, lambda: self._step_lift(name))


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("FoodieHub – Online Food Ordering & Billing")
        self.theme = "light"
        self.cart = {}
        self.fav = set()
        self.category = "All"
        self.sort_idx = 0
        self.veg_only = False
        self.order_type = "Dine-in"
        self.coupon_code = None
        self.search_text = ""
        self.customer = ""
        self.order_no = 1000
        self.last_changed = None
        self.new_item = False
        self.busy = False
        self.toast_lbl = None
        self.toast_job = None
        self.toast_hiding = False
        self.coupon_bad = False
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            root.bind_all(ev, self._wheel)
        root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        root.bind("<Escape>", lambda e: self.search_var.set(""))
        self.build()

    def _wheel(self, e):
        """Scroll whichever scrollable area is under the pointer."""
        try:
            w = self.root.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        target = step = None
        while w is not None:
            if w is getattr(self, "menu", None):
                target, step = self.menu.canvas, 3
                break
            if w is getattr(self, "cart_list", None):
                target, step = self.cart_list.canvas, 2
                break
            w = w.master
        if target is None:
            return
        if step is None:
            return
        try:
            top, bot = target.yview()
            if top <= 0 and bot >= 1:
                return
            up = e.num == 4 or getattr(e, "delta", 0) > 0
            target.yview_scroll(-step if up else step, "units")
        except tk.TclError:
            pass

    @property
    def T(self) -> Theme:
        return LIGHT if self.theme == "light" else DARK

    # ------------------------------------------------------------------ build
    def rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.toast_lbl = None
        self.toast_hiding = False
        self.build()

    def build(self):
        T = self.T
        self.root.configure(bg=T["bg"])
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        for name, trough in (("Vertical.TScrollbar", T["bg"]), ("Cart.Vertical.TScrollbar", T["panel"])):
            s.configure(name, background=T["border"], troughcolor=trough, bordercolor=trough,
                        lightcolor=T["border"], darkcolor=T["border"], arrowcolor=T["muted"],
                        relief="flat", gripcount=0)
            s.map(name, background=[("active", T["muted"])])

        self.search_var = tk.StringVar(value=self.search_text)
        self.name_var = tk.StringVar(value=self.customer)
        self.coupon_var = tk.StringVar(value=self.coupon_code or "")
        self.search_var.trace_add("write", self._on_search)
        self.name_var.trace_add("write", lambda *_: setattr(self, "customer", self.name_var.get()))

        self._build_header()
        body = tk.Frame(self.root, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=(12, 16))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_left(body)
        self._build_cart(body)
        self.render_menu()
        self.refresh_cart()

    # ----------------------------------------------------------------- header
    def _build_header(self):
        self.header = tk.Canvas(self.root, height=72, highlightthickness=0, bg=PRIMARY)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", lambda e: self._draw_header())

    def _draw_header(self):
        c, T = self.header, self.T
        c.delete("all")
        W, H = max(c.winfo_width(), 400), 72
        for x in range(0, W + 6, 6):
            c.create_rectangle(x, 0, x + 6, H, outline="", fill=lerp_color("#FF9448", "#EE4B2B", x / W))
        blob = lerp_color(lerp_color("#FF9448", "#EE4B2B", 0.5), "#FFFFFF", 0.10)
        c.create_oval(W * 0.40, -60, W * 0.40 + 160, 70, fill=blob, outline="")
        c.create_oval(W * 0.52, 20, W * 0.52 + 120, 150, fill=blob, outline="")
        c.create_text(24, 34, text="🍽️", font=(EMOJI, 24), anchor="w")
        c.create_text(70, 27, text="FoodieHub", font=(UI, 20, "bold"), fill="white", anchor="w")
        c.create_text(72, 53, text="Hungry? Order in a few taps.", font=(UI, 9), fill="#FFE6D3", anchor="w")

        # cart pill
        pw, px2 = 238, W - 22
        px1 = px2 - pw
        rrect(c, px1, 14, px2, 58, 22, fill="white", outline="", tags=("cartpill",))
        c.create_text(px1 + 26, 36, text="🛒", font=(EMOJI, 18), tags=("cartpill",))
        c.create_oval(px1 + 33, 12, px1 + 51, 30, fill=RED, outline="white", width=2, tags=("cartpill", "badge"))
        self.h_badge = c.create_text(px1 + 42, 21, text="0", fill="white", font=(UI, 8, "bold"),
                                     tags=("cartpill", "badge"))
        c.create_text(px1 + 60, 28, text="My Cart", anchor="w", font=(UI, 10, "bold"),
                      fill="#241F1B", tags=("cartpill",))
        self.h_sub = c.create_text(px1 + 60, 45, text="", anchor="w", font=(UI, 9),
                                   fill="#7D746B", tags=("cartpill",))
        self.cart_icon = (px1 + 26, 36)
        c.tag_bind("cartpill", "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind("cartpill", "<Leave>", lambda e: c.config(cursor=""))
        c.tag_bind("cartpill", "<Button-1>", lambda e: self._cart_peek())

        # theme toggle
        tx = px1 - 36
        circ = c.create_oval(tx - 20, 16, tx + 20, 56, fill="#FFB27A", outline="", tags=("themebtn",))
        c.create_text(tx, 36, text="🌙" if T["name"] == "light" else "☀️", font=(EMOJI, 16), tags=("themebtn",))
        c.tag_bind("themebtn", "<Enter>", lambda e: (c.config(cursor="hand2"), c.itemconfig(circ, fill="#FFC49C")))
        c.tag_bind("themebtn", "<Leave>", lambda e: (c.config(cursor=""), c.itemconfig(circ, fill="#FFB27A")))
        c.tag_bind("themebtn", "<Button-1>", lambda e: self.toggle_theme())
        self.update_header()

    def update_header(self):
        if not hasattr(self, "h_badge"):
            return
        c = self.header
        n = sum(self.cart.values())
        try:
            c.itemconfig(self.h_badge, text=str(n))
            c.itemconfig("badge", state="normal" if n else "hidden")
            c.itemconfig(self.h_sub, text=f"{n} item{'s' if n != 1 else ''}  ·  {rs(self.calculate()['total'])}")
        except tk.TclError:
            pass

    def bounce_cart(self):
        def step(k=0):
            offs = [-4, -3, 3, 4, -2, 2]
            if k < len(offs):
                try:
                    self.header.move("cartpill", 0, offs[k])
                    self.root.after(40, step, k + 1)
                except tk.TclError:
                    pass
        step()

    def _cart_peek(self):
        n = sum(self.cart.values())
        if not n:
            self.toast("🛒 Your cart is empty")
        else:
            self.toast(f"🛒 {n} item{'s' if n != 1 else ''} in cart · {rs(self.calculate()['total'])}")

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.rebuild()
        self.toast("🌙 Dark mode on" if self.theme == "dark" else "☀️ Light mode on")

    # ------------------------------------------------------------- left panel
    def make_input(self, parent, placeholder, var, clearable=False, size=10):
        T = self.T
        box = tk.Frame(parent, bg=T["input"], highlightthickness=2, highlightbackground=T["border"])
        entry = tk.Entry(box, textvariable=var, bd=0, relief="flat", bg=T["input"], fg=T["text"],
                         insertbackground=T["text"], font=(UI, size), highlightthickness=0)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 6), ipady=7)
        ph = tk.Label(box, text=placeholder, bg=T["input"], fg=T["muted"], font=(UI, size))
        clear = tk.Label(box, text="✕", bg=T["input"], fg=T["muted"], cursor="hand2", font=(UI, 10, "bold"))
        clear.bind("<Button-1>", lambda e: var.set(""))
        ph.bind("<Button-1>", lambda e: entry.focus_set())

        def sync(*_):
            if var.get():
                ph.place_forget()
                if clearable:
                    clear.pack(side="right", padx=(0, 10), before=entry)
            else:
                ph.place(in_=entry, x=2, rely=0.5, anchor="w")
                clear.pack_forget()
        var.trace_add("write", sync)
        sync()
        entry.bind("<FocusIn>", lambda e: box.config(highlightbackground=PRIMARY))
        entry.bind("<FocusOut>", lambda e: box.config(highlightbackground=T["border"]))
        return box, entry

    def _build_left(self, parent):
        T = self.T
        left = tk.Frame(parent, bg=T["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        r0 = tk.Frame(left, bg=T["bg"])
        r0.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box, self.search_entry = self.make_input(r0, "🔍  Search dishes, e.g. biryani…  (Ctrl+F)",
                                                 self.search_var, clearable=True, size=11)
        box.pack(side="left", fill="x", expand=True)
        self.sort_btn = Btn(r0, f"⇅  {SORTS[self.sort_idx]}", self.cycle_sort, bg=T["card"], fg=T["text"],
                            hover=T["soft"], pady=9, highlightthickness=1, highlightbackground=T["border"])
        self.sort_btn.pack(side="right", padx=(10, 0))
        vf = tk.Frame(r0, bg=T["bg"])
        vf.pack(side="right", padx=(12, 0))
        tk.Label(vf, text="Veg only", bg=T["bg"], fg=T["text"], font=(UI, 10, "bold")).pack(side="left", padx=(0, 8))
        Toggle(vf, self.veg_only, T["bg"], self.set_veg).pack(side="left")

        r1 = tk.Frame(left, bg=T["bg"])
        r1.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.chip_labels = {}
        for name, icon in CHIPS:
            lb = tk.Label(r1, text=f"{icon} {name}", font=(UI, 9, "bold"), padx=11, pady=6,
                          cursor="hand2", highlightthickness=1)
            lb.pack(side="left", padx=(0, 7))
            lb.bind("<Button-1>", lambda e, n=name: self.set_category(n))
            lb.bind("<Enter>", lambda e, n=name: self.category != n and self.chip_labels[n].config(bg=T["soft"]))
            lb.bind("<Leave>", lambda e: self.paint_chips())
            self.chip_labels[name] = lb
        self.count_lbl = tk.Label(r1, text="", bg=T["bg"], fg=T["muted"], font=(UI, 9))
        self.count_lbl.pack(side="right")
        Btn(r1, "🎲 Surprise me", self.surprise, bg=T["soft"], fg=PRIMARY, pady=4, padx=10,
            font=(UI, 9, "bold")).pack(side="right", padx=(0, 10))
        self.paint_chips()

        self.menu = MenuView(left, self)
        self.menu.grid(row=2, column=0, sticky="nsew")

    def paint_chips(self):
        T = self.T
        for n, lb in self.chip_labels.items():
            if n == self.category:
                lb.config(bg=PRIMARY, fg="white", highlightbackground=PRIMARY)
            else:
                lb.config(bg=T["card"], fg=T["text"], highlightbackground=T["border"])

    def set_category(self, name):
        self.category = name
        self.paint_chips()
        self.render_menu()

    def set_veg(self, on):
        self.veg_only = on
        self.render_menu()
        self.toast("🥦 Showing vegetarian dishes only" if on else "🍗 Showing all dishes")

    def cycle_sort(self):
        self.sort_idx = (self.sort_idx + 1) % len(SORTS)
        self.sort_btn.config(text=f"⇅  {SORTS[self.sort_idx]}")
        self.render_menu()

    def _on_search(self, *_):
        self.search_text = self.search_var.get()
        self.render_menu()

    def visible(self):
        q = self.search_text.strip().lower()
        names = []
        for n, it in ITEMS.items():
            if self.category == "Favorites" and n not in self.fav:
                continue
            if self.category not in ("All", "Favorites") and it["cat"] != self.category:
                continue
            if self.veg_only and not it["veg"]:
                continue
            if q and q not in n.lower() and q not in it["cat"].lower() and q not in it["desc"].lower():
                continue
            names.append(n)
        if self.sort_idx == 1:
            names.sort(key=lambda n: ITEMS[n]["price"])
        elif self.sort_idx == 2:
            names.sort(key=lambda n: -ITEMS[n]["price"])
        elif self.sort_idx == 3:
            names.sort(key=lambda n: -ITEMS[n]["rating"])
        return names

    def render_menu(self):
        names = self.visible()
        msg = ("Tap the ♡ on a dish to save it here" if self.category == "Favorites"
               else "Try a different search or filter")
        self.menu.set_items(names, msg)
        self.count_lbl.config(text=f"{len(names)} dish{'es' if len(names) != 1 else ''}")

    def toggle_fav(self, name):
        if name in self.fav:
            self.fav.discard(name)
            self.toast(f"💔 Removed {name} from favorites")
        else:
            self.fav.add(name)
            self.toast(f"❤️ Saved {name} to favorites")
        if self.category == "Favorites":
            self.render_menu()
        else:
            self.menu.update_heart(name)

    def surprise(self):
        pool = self.visible() or list(ITEMS)
        name = random.choice(pool)
        self.toast(f"🎲 Surprise! {ITEMS[name]['emoji']} {name} added")
        self.add(name, None, quiet=True)

    # ------------------------------------------------------------ cart panel
    def _build_cart(self, parent):
        T = self.T
        outer = tk.Frame(parent, bg=T["panel"], width=410, highlightthickness=1, highlightbackground=T["border"])
        outer.grid(row=0, column=1, sticky="ns")
        outer.pack_propagate(False)

        top = tk.Frame(outer, bg=T["panel"])
        top.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(top, text="Your Order", font=(UI, 14, "bold"), bg=T["panel"], fg=T["text"]).pack(side="left")
        self.count_pill = tk.Label(top, text="0", font=(UI, 9, "bold"), bg=lerp_color(T["panel"], PRIMARY, 0.18),
                                   fg=PRIMARY, padx=8, pady=1)
        self.count_pill.pack(side="left", padx=8)
        clr = tk.Label(top, text="🗑 Clear", font=(UI, 9, "bold"), bg=T["panel"], fg=RED, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self.clear_cart())

        nb, _ = self.make_input(outer, "👤  Customer name (optional)", self.name_var)
        nb.pack(fill="x", padx=16, pady=(0, 8))

        seg = tk.Frame(outer, bg=T["soft"], padx=3, pady=3)
        seg.pack(fill="x", padx=16, pady=(0, 8))
        self.seg_labels = {}
        for t, icon in (("Dine-in", "🍴"), ("Takeaway", "🥡"), ("Delivery", "🛵")):
            lb = tk.Label(seg, text=f"{icon} {t}", font=(UI, 9, "bold"), cursor="hand2", pady=6)
            lb.pack(side="left", fill="x", expand=True, padx=1)
            lb.bind("<Button-1>", lambda e, t=t: self.set_order_type(t))
            lb.bind("<Enter>", lambda e, t=t: self.order_type != t and self.seg_labels[t].config(bg=T["border"]))
            lb.bind("<Leave>", lambda e: self.paint_seg())
            self.seg_labels[t] = lb
        self.paint_seg()

        tk.Frame(outer, bg=T["border"], height=1).pack(fill="x", padx=16)

        # fixed bottom block is packed first (side=bottom) so the list gets the leftover space
        bottom = tk.Frame(outer, bg=T["panel"])
        bottom.pack(side="bottom", fill="x")
        self.bill_btn = Btn(bottom, "🧾  Generate Bill", self.checkout, font=(UI, 12, "bold"), pady=12)
        self.bill_btn.pack(side="bottom", fill="x", padx=16, pady=(8, 16))

        self.totals = tk.Frame(bottom, bg=T["panel"])
        self.totals.pack(side="bottom", fill="x", padx=16)
        self.num = {}
        for key, text in (("sub", "Subtotal"), ("disc", "Discount"), ("gst", f"GST ({int(GST_RATE * 100)}%)"),
                          ("del", "Delivery")):
            row = tk.Frame(self.totals, bg=T["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=text, font=(UI, 10), bg=T["panel"], fg=T["muted"]).pack(side="left")
            lbl = tk.Label(row, font=(UI, 10), bg=T["panel"], fg=T["text"])
            lbl.pack(side="right")
            if key == "disc":
                self.num[key] = AnimatedNumber(lbl, lambda v: f"− {money(v)}" if v > 0.005 else money(0))
            elif key == "del":
                self.del_lbl = lbl
            else:
                self.num[key] = AnimatedNumber(lbl)
        sep = tk.Frame(self.totals, bg=T["border"], height=1)
        sep.pack(fill="x", pady=6)
        row = tk.Frame(self.totals, bg=T["panel"])
        row.pack(fill="x")
        tk.Label(row, text="Total", font=(UI, 13, "bold"), bg=T["panel"], fg=T["text"]).pack(side="left")
        tl = tk.Label(row, font=(UI, 17, "bold"), bg=T["panel"], fg=PRIMARY)
        tl.pack(side="right")
        self.num["total"] = AnimatedNumber(tl)

        self.prog = tk.Canvas(bottom, height=34, bg=T["panel"], highlightthickness=0)
        self.prog.bind("<Configure>", lambda e: self.draw_progress())
        self.prog_shown = False

        # packed bottom-up: message, coupon chips, coupon input, separator
        self.coupon_msg = tk.Label(bottom, font=(UI, 9), bg=T["panel"], anchor="w")
        self.coupon_msg.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
        chips = tk.Frame(bottom, bg=T["panel"])
        chips.pack(side="bottom", fill="x", padx=16, pady=(0, 4))
        cp = tk.Frame(bottom, bg=T["panel"])
        cp.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
        cb, _ = self.make_input(cp, "🏷  Have a coupon code?", self.coupon_var)
        cb.pack(side="left", fill="x", expand=True)
        Btn(cp, "Apply", lambda: self.apply_coupon(self.coupon_var.get()), bg=T["text"], fg=T["panel"],
            pady=7).pack(side="left", padx=(8, 0))
        self.coupon_chips = {}
        for code in COUPONS:
            lb = tk.Label(chips, text=f"🏷 {code}", font=(UI, 9, "bold"), padx=9, pady=3, cursor="hand2")
            lb.pack(side="left", padx=(0, 6))
            lb.bind("<Button-1>", lambda e, c=code: self.apply_coupon(c))
            self.coupon_chips[code] = lb
        tk.Frame(bottom, bg=T["border"], height=1).pack(side="bottom", fill="x", padx=16, pady=(8, 8))
        self.totals_frame = self.totals
        self.bottom = bottom

        self.cart_list = ScrollFrame(outer, bg=T["panel"], style="Cart.Vertical.TScrollbar")
        self.cart_list.pack(fill="both", expand=True, padx=(16, 6), pady=(8, 0))

    def paint_seg(self):
        T = self.T
        for t, lb in self.seg_labels.items():
            lb.config(bg=PRIMARY if t == self.order_type else T["soft"],
                      fg="white" if t == self.order_type else T["text"])

    def set_order_type(self, t):
        self.order_type = t
        self.paint_seg()
        self.refresh_cart()

    # --------------------------------------------------------- cart operations
    def add(self, name, origin=None, quiet=False):
        self.new_item = name not in self.cart
        self.cart[name] = min(self.cart.get(name, 0) + 1, 20)
        self.last_changed = name
        if origin:
            self.fly(name, origin)
            self.toast(f"{ITEMS[name]['emoji']} {name} added")
        else:
            self.bounce_cart()
        self._after_change(name)

    def change(self, name, delta, origin=None):
        qty = self.cart.get(name, 0) + delta
        self.new_item = False
        self.last_changed = name
        if qty <= 0:
            self.cart.pop(name, None)
            self.last_changed = None
        else:
            self.cart[name] = min(qty, 20)
        if delta > 0 and origin:
            self.fly(name, origin)
        self._after_change(name)

    def remove(self, name):
        self.cart.pop(name, None)
        self.last_changed = None
        self.toast(f"🗑 {name} removed")
        self._after_change(name)

    def _after_change(self, name):
        self.menu.update_card(name)
        self.refresh_cart()

    def clear_cart(self):
        if not self.cart:
            self.toast("🛒 Cart is already empty")
            return
        if messagebox.askyesno("Clear cart", "Remove all items from your order?", parent=self.root):
            self.reset_order(keep_name=True)

    def reset_order(self, keep_name=False):
        self.cart.clear()
        self.coupon_code = None
        self.coupon_bad = False
        self.coupon_var.set("")
        if not keep_name:
            self.name_var.set("")
        self.last_changed = None
        self.menu.update_all()
        self.refresh_cart()

    # ----------------------------------------------------------------- pricing
    def calculate(self):
        sub = sum(ITEMS[n]["price"] * q for n, q in self.cart.items())
        disc = 0.0
        if self.coupon_code and sub > 0:
            kind, val, mn, _ = COUPONS[self.coupon_code]
            if sub >= mn:
                disc = sub * val / 100 if kind == "percent" else min(val, sub)
        taxable = sub - disc
        gst = taxable * GST_RATE
        delivery = DELIVERY_FEE if (self.order_type == "Delivery" and 0 < sub < FREE_DELIVERY_ABOVE) else 0
        return dict(subtotal=sub, discount=disc, gst=gst, delivery=delivery, total=taxable + gst + delivery)

    def apply_coupon(self, code):
        code = (code or "").strip().upper()
        if not code:
            return
        if code not in COUPONS:
            self.coupon_code = None
            self.coupon_bad = True
            self.coupon_var.set(code)
            self.toast("❌ Invalid coupon code")
        else:
            self.coupon_bad = False
            self.coupon_code = code
            self.coupon_var.set(code)
            sub = self.calculate()["subtotal"]
            if sub and sub >= COUPONS[code][2]:
                self.toast(f"🎉 {code} applied - {COUPONS[code][3]}")
        self.refresh_cart()

    def _coupon_state(self, sub):
        T = self.T
        if self.coupon_code:
            need = COUPONS[self.coupon_code][2]
            if sub <= 0:
                return f"{self.coupon_code} will apply once you add items", T["muted"]
            if sub >= need:
                return f"✔ {self.coupon_code} applied – {COUPONS[self.coupon_code][3]}", GREEN
            return f"{self.coupon_code} needs a minimum order of {rs(need)}", RED
        if self.coupon_bad:
            return "Invalid coupon code", RED
        return "Tap a coupon below or type your own code", T["muted"]

    # ----------------------------------------------------------------- refresh
    def refresh_cart(self):
        T = self.T
        sf = self.cart_list
        yv = sf.canvas.yview()[0]
        for w in sf.inner.winfo_children():
            w.destroy()
        flash_widgets = []
        if not self.cart:
            box = tk.Frame(sf.inner, bg=T["panel"])
            box.pack(fill="x", pady=40)
            tk.Label(box, text="🛒", font=(EMOJI, 40), bg=T["panel"]).pack()
            tk.Label(box, text="Your cart is empty", font=(UI, 12, "bold"), bg=T["panel"], fg=T["text"]).pack(pady=(8, 0))
            tk.Label(box, text="Pick something delicious from the menu", font=(UI, 9), bg=T["panel"],
                     fg=T["muted"]).pack()
        else:
            for name, qty in self.cart.items():
                ws = self._cart_row(sf.inner, name, qty)
                if name == self.last_changed:
                    flash_widgets = ws
        to_end = self.new_item
        sf.canvas.after_idle(lambda: self._restore_scroll(yv, to_end))
        self.new_item = False
        if flash_widgets:
            self.flash(flash_widgets)

        t = self.calculate()
        n = sum(self.cart.values())
        self.count_pill.config(text=str(n))
        self.num["sub"].set(t["subtotal"])
        self.num["disc"].set(t["discount"])
        self.num["gst"].set(t["gst"])
        self.num["total"].set(t["total"])
        if self.order_type == "Delivery" and t["subtotal"] > 0:
            self.del_lbl.config(text=money(t["delivery"]) if t["delivery"] else "FREE", fg=GREEN if not t["delivery"] else T["text"])
        else:
            self.del_lbl.config(text=money(0), fg=T["text"])

        msg, col = self._coupon_state(t["subtotal"])
        self.coupon_msg.config(text=msg, fg=col)
        for code, lb in self.coupon_chips.items():
            ok = code == self.coupon_code and t["subtotal"] > 0 and t["subtotal"] >= COUPONS[code][2]
            if ok:
                lb.config(bg=lerp_color(T["panel"], GREEN, 0.2), fg=GREEN)
            else:
                lb.config(bg=T["soft"], fg=T["text"])

        want = self.order_type == "Delivery" and t["subtotal"] > 0
        if want and not self.prog_shown:
            self.prog.pack(after=self.totals_frame, side="bottom", fill="x", padx=16, pady=(0, 6))
            self.prog_shown = True
        elif not want and self.prog_shown:
            self.prog.pack_forget()
            self.prog_shown = False
        if self.prog_shown:
            self.draw_progress()

        if n:
            self.bill_btn.config(text=f"🧾  Generate Bill   •   {rs(t['total'])}")
            self.bill_btn.recolor(PRIMARY, PRIMARY_D)
        else:
            self.bill_btn.config(text="Add items to continue")
            self.bill_btn.recolor(T["muted"])
        self.update_header()
        self.last_changed = None

    def _restore_scroll(self, yv, to_end=False):
        try:
            self.cart_list.canvas.yview_moveto(1.0 if to_end else yv)
        except tk.TclError:
            pass

    def draw_progress(self):
        c, T = self.prog, self.T
        c.delete("all")
        W = max(c.winfo_width(), 300)
        sub = self.calculate()["subtotal"]
        left = FREE_DELIVERY_ABOVE - sub
        if left > 0:
            msg, frac = f"🛵  Add {rs(left)} more for FREE delivery", sub / FREE_DELIVERY_ABOVE
        else:
            msg, frac = "🎉  You've unlocked FREE delivery!", 1
        c.create_text(0, 8, text=msg, anchor="w", font=(UI, 9, "bold"), fill=T["text"])
        rrect(c, 0, 22, W, 30, 4, fill=T["soft"], outline="")
        if frac > 0:
            rrect(c, 0, 22, max(10, W * frac), 30, 4, fill=GREEN if frac >= 1 else PRIMARY, outline="")

    def _cart_row(self, parent, name, qty):
        T, it = self.T, ITEMS[name]
        bg = T["panel"]
        tint = lerp_color(T["panel"], CAT_COLOR[it["cat"]], T["tint"])
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=it["emoji"], font=(EMOJI, 17), bg=tint, width=3, pady=5).pack(side="left", padx=(0, 10))
        mid = tk.Frame(row, bg=bg)
        mid.pack(side="left", fill="x", expand=True)
        nl = tk.Label(mid, text=name, font=(UI, 10, "bold"), bg=bg, fg=T["text"], anchor="w",
                      justify="left", wraplength=120)
        nl.pack(fill="x")
        sl = tk.Label(mid, text=f"{rs(it['price'])} each", font=(UI, 9), bg=bg, fg=T["muted"], anchor="w")
        sl.pack(fill="x")

        x = tk.Label(row, text="✕", font=(UI, 10, "bold"), bg=bg, fg=T["muted"], cursor="hand2")
        x.pack(side="right", padx=(6, 0))
        x.bind("<Button-1>", lambda e: self.remove(name))
        x.bind("<Enter>", lambda e: x.config(fg=RED))
        x.bind("<Leave>", lambda e: x.config(fg=T["muted"]))
        amt = tk.Label(row, text=rs(it["price"] * qty), font=(UI, 10, "bold"), bg=bg, fg=T["text"],
                       width=7, anchor="e")
        amt.pack(side="right")
        st = tk.Frame(row, bg=T["soft"])
        st.pack(side="right", padx=8)
        Btn(st, "−", lambda: self.change(name, -1), bg=T["soft"], fg=T["text"], hover=T["border"],
            font=(UI, 11, "bold"), padx=7, pady=1).pack(side="left")
        ql = tk.Label(st, text=str(qty), font=(UI, 10, "bold"), bg=T["soft"], fg=T["text"], width=2)
        ql.pack(side="left")
        Btn(st, "+", lambda: self.change(name, +1), bg=PRIMARY, fg="white",
            font=(UI, 11, "bold"), padx=7, pady=1).pack(side="left")
        return [row, mid, nl, sl, amt, x]

    def flash(self, widgets):
        T = self.T
        hi = lerp_color(T["panel"], PRIMARY, 0.22)

        def step(k=0):
            t = k / 14
            col = lerp_color(hi, T["panel"], t)
            try:
                for w in widgets:
                    w.config(bg=col)
                if k < 14:
                    self.root.after(30, step, k + 1)
            except tk.TclError:
                pass
        step()

    # ------------------------------------------------------------- animations
    def fly(self, name, canvas_xy):
        cv, root = self.menu.canvas, self.root
        sx = cv.winfo_rootx() - root.winfo_rootx() + canvas_xy[0]
        sy = cv.winfo_rooty() - root.winfo_rooty() + canvas_xy[1] - cv.canvasy(0)
        ex = self.header.winfo_rootx() - root.winfo_rootx() + self.cart_icon[0]
        ey = self.header.winfo_rooty() - root.winfo_rooty() + self.cart_icon[1]
        it = ITEMS[name]
        chip = tk.Label(root, text=it["emoji"], font=(EMOJI, 16), bg=lerp_color("#FFFFFF", CAT_COLOR[it["cat"]], 0.25),
                        highlightthickness=2, highlightbackground=PRIMARY, padx=4, pady=2)
        N = 18

        def step(k=0):
            try:
                t = (k + 1) / N
                e = t * t * (3 - 2 * t)
                chip.place(x=sx + (ex - sx) * e, y=sy + (ey - sy) * e - 80 * math.sin(math.pi * t), anchor="center")
                if k + 1 < N:
                    root.after(16, step, k + 1)
                else:
                    chip.destroy()
                    self.bounce_cart()
            except tk.TclError:
                pass
        step()

    def toast(self, msg):
        T, root = self.T, self.root
        if self.toast_job:
            root.after_cancel(self.toast_job)
        if self.toast_lbl is not None and self.toast_lbl.winfo_exists() and not self.toast_hiding:
            self.toast_lbl.config(text=msg)
        else:
            if self.toast_lbl is not None and self.toast_lbl.winfo_exists():
                self.toast_lbl.destroy()
            self.toast_hiding = False
            self.toast_lbl = tk.Label(root, text=msg, bg=T["toast"], fg=T["toast_fg"], font=(UI, 10, "bold"),
                                      padx=20, pady=11)
            self._slide(self.toast_lbl, 70, -34)
        self.toast_job = root.after(1900, self._hide_toast)

    def _slide(self, w, y0, y1, done=None):
        N = 8

        def step(k=0):
            try:
                t = (k + 1) / N
                e = 1 - (1 - t) ** 3
                w.place(relx=0.5, rely=1.0, anchor="s", y=y0 + (y1 - y0) * e)
                if k + 1 < N:
                    self.root.after(14, step, k + 1)
                elif done:
                    done()
            except tk.TclError:
                pass
        step()

    def _hide_toast(self):
        lbl = self.toast_lbl
        if lbl is None:
            return
        self.toast_hiding = True

        def done():
            try:
                lbl.destroy()
            except tk.TclError:
                pass
            if self.toast_lbl is lbl:
                self.toast_lbl = None
                self.toast_hiding = False
        self._slide(lbl, -34, 70, done)

    def _shake(self, w):
        def step(k=0):
            offs = [-6, 12, -10, 8, -4, 2]
            try:
                if k < len(offs):
                    w.pack_configure(padx=(16 + offs[k], 16 - offs[k]))
                    self.root.after(30, step, k + 1)
                else:
                    w.pack_configure(padx=16)
            except tk.TclError:
                pass
        step()

    # ---------------------------------------------------------------- checkout
    def checkout(self):
        if not self.cart:
            self.toast("🛒 Your cart is empty – add something tasty!")
            self._shake(self.bill_btn)
            return
        if self.busy:
            return
        self.busy = True
        T = self.T
        card = tk.Frame(self.root, bg=T["card"], highlightthickness=2, highlightbackground=PRIMARY, padx=34, pady=24)
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(card, text="🍳", font=(EMOJI, 34), bg=T["card"]).pack()
        msg = tk.Label(card, text="Placing your order…", font=(UI, 13, "bold"), bg=T["card"], fg=T["text"])
        msg.pack(pady=(6, 10))
        bar = tk.Canvas(card, width=260, height=10, bg=T["card"], highlightthickness=0)
        bar.pack()
        N = 28

        def step(k=0):
            try:
                bar.delete("all")
                rrect(bar, 0, 1, 260, 9, 4, fill=T["soft"], outline="")
                rrect(bar, 0, 1, max(8, 260 * k / N), 9, 4, fill=PRIMARY, outline="")
                if k == 10:
                    msg.config(text="Confirming with the kitchen…")
                if k == 20:
                    msg.config(text="Generating your bill…")
                if k < N:
                    self.root.after(32, step, k + 1)
                else:
                    card.destroy()
                    self.busy = False
                    self.generate_bill()
            except tk.TclError:
                self.busy = False
        step()

    def bill_text(self, bill_no, customer):
        t = self.calculate()
        W = 44
        line, dash = "=" * W, "-" * W
        out = [line, "FOODIEHUB".center(W), "Online Food Ordering & Billing".center(W), line,
               f"Bill No    : FH{bill_no}",
               f"Date       : {datetime.now():%d-%m-%Y  %I:%M %p}",
               f"Customer   : {customer}",
               f"Order Type : {self.order_type}",
               dash, f"{'Item':<20}{'Qty':>4}{'Rate':>9}{'Amount':>11}", dash]
        for name, qty in self.cart.items():
            rate = ITEMS[name]["price"]
            nm = name if len(name) <= 19 else name[:18] + "."
            out.append(f"{nm:<20}{qty:>4}{rate:>9.2f}{rate * qty:>11.2f}")
        out.append(dash)
        out.append(f"{'Subtotal':<28}{t['subtotal']:>16.2f}")
        if t["discount"]:
            out.append(f"{'Discount (' + (self.coupon_code or '') + ')':<28}{-t['discount']:>16.2f}")
        out.append(f"{'GST @ ' + str(int(GST_RATE * 100)) + '%':<28}{t['gst']:>16.2f}")
        if self.order_type == "Delivery":
            out.append(f"{'Delivery fee':<28}{t['delivery']:>16.2f}")
        out += [dash, f"{'GRAND TOTAL (Rs.)':<28}{t['total']:>16.2f}", line,
                "Thank you! Visit again.".center(W), line]
        return "\n".join(out), t

    def generate_bill(self):
        self.order_no += 1
        customer = self.name_var.get().strip() or "Guest"
        text, t = self.bill_text(self.order_no, customer)
        self.show_bill(text, t["total"], self.order_no, self.order_type)

    def show_bill(self, text, total, bill_no, otype):
        T = self.T
        win = tk.Toplevel(self.root)
        win.title(f"Bill FH{bill_no}")
        win.configure(bg=T["bg"])
        sh = win.winfo_screenheight()
        win.geometry(f"500x{min(790, sh - 90)}")
        win.resizable(False, False)
        win.transient(self.root)
        try:
            win.grab_set()
        except tk.TclError:
            pass

        # header with check mark + confetti
        W, H = 500, 124
        hc = tk.Canvas(win, width=W, height=H, highlightthickness=0, bg=GREEN)
        hc.pack(fill="x")
        for y in range(0, H, 4):
            hc.create_rectangle(0, y, W, y + 4, outline="", fill=lerp_color("#3BCB62", "#1B9446", y / H))
        hc.create_oval(34, 32, 94, 92, fill="white", outline="")
        hc.create_text(118, 46, text="Order placed!", anchor="w", font=(UI, 19, "bold"), fill="white")
        hc.create_text(118, 74, text=f"Bill FH{bill_no}  ·  {otype}", anchor="w", font=(UI, 10), fill="#D7F7DF")
        hc.create_text(118, 96, text=f"Total payable  {money(total)}", anchor="w", font=(UI, 11, "bold"), fill="white")
        pts = [(50, 63), (60, 73), (79, 52)]

        def draw_check(f):
            try:
                _draw_check(f)
            except tk.TclError:
                pass

        def _draw_check(f):
            hc.delete("chk")
            prog = f / 14 * 2
            path = [pts[0]]
            if prog > 0:
                seg = min(prog, 1)
                path.append((pts[0][0] + (pts[1][0] - pts[0][0]) * seg, pts[0][1] + (pts[1][1] - pts[0][1]) * seg))
            if prog > 1:
                seg = prog - 1
                path.append((pts[1][0] + (pts[2][0] - pts[1][0]) * seg, pts[1][1] + (pts[2][1] - pts[1][1]) * seg))
            if len(path) > 1:
                hc.create_line(*[v for p in path for v in p], width=6, fill=GREEN, capstyle="round",
                               joinstyle="round", tags="chk")
            if f < 14:
                self.root.after(24, draw_check, f + 1)
        draw_check(0)

        colors = ["#FFD43B", "#FF6B6B", "#4DABF7", "#FFFFFF", "#F783AC", "#69DB7C", "#FFA94D"]
        parts = []
        for _ in range(80):
            x, s = random.uniform(0, W), random.uniform(4, 8)
            y = random.uniform(-80, -4)
            pid = hc.create_rectangle(x, y, x + s, y + s * 0.6, fill=random.choice(colors), outline="", tags="conf")
            parts.append([pid, random.uniform(-1.2, 1.2), random.uniform(2.5, 5.5)])

        def confetti(k=0):
            try:
                alive = False
                for p in parts:
                    hc.move(p[0], p[1], p[2])
                    if hc.coords(p[0])[1] < H:
                        alive = True
                if alive and k < 120:
                    self.root.after(22, confetti, k + 1)
                else:
                    hc.delete("conf")
            except tk.TclError:
                pass
        confetti()

        # order tracker
        stages = STAGES[otype]
        tc = tk.Canvas(win, width=W, height=112, highlightthickness=0, bg=T["bg"])
        tc.pack(fill="x")
        xs = [64 + i * (372 / 3) for i in range(4)]
        state = {"stage": 0, "x": xs[0]}

        def draw_tracker():
            tc.delete("all")
            tc.create_text(W / 2, 20, text=stages[state["stage"]][0], font=(UI, 11, "bold"), fill=T["text"])
            tc.create_line(xs[0], 58, xs[-1], 58, width=6, fill=T["border"], capstyle="round")
            tc.create_line(xs[0], 58, state["x"], 58, width=6, fill=GREEN, capstyle="round")
            for i, x in enumerate(xs):
                done, cur = i < state["stage"], i == state["stage"]
                col = GREEN if done or (cur and i == 3) else (PRIMARY if cur else T["border"])
                if cur and i != 3:
                    tc.create_oval(x - 19, 39, x + 19, 77, fill=lerp_color(T["bg"], PRIMARY, 0.25), outline="")
                tc.create_oval(x - 13, 45, x + 13, 71, fill=col, outline="")
                tc.create_text(x, 58, text="✓" if done or (cur and i == 3) else str(i + 1),
                               fill="white" if (done or cur) else T["muted"], font=(UI, 10, "bold"))
                tc.create_text(x, 92, text=stages[i][1], font=(UI, 9, "bold" if cur else "normal"),
                               fill=T["text"] if (done or cur) else T["muted"])

        def glide():
            tgt = xs[state["stage"]]
            if abs(state["x"] - tgt) < 1.5:
                state["x"] = tgt
                draw_tracker()
                return
            state["x"] += (tgt - state["x"]) * 0.2
            try:
                draw_tracker()
                self.root.after(20, glide)
            except tk.TclError:
                pass

        def advance():
            try:
                if not win.winfo_exists() or state["stage"] >= 3:
                    return
                state["stage"] += 1
                glide()
                self.root.after(2200, advance)
            except tk.TclError:
                pass
        draw_tracker()
        self.root.after(1800, advance)

        # receipt
        paper = tk.Frame(win, bg=T["paper"], highlightthickness=1, highlightbackground=T["border"])
        paper.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        sb = ttk.Scrollbar(paper, orient="vertical")
        sb.pack(side="right", fill="y")
        txt = tk.Text(paper, font=(MONO, 10), bg=T["paper"], fg=T["text"], bd=0, padx=14, pady=12,
                      wrap="none", yscrollcommand=sb.set, highlightthickness=0, cursor="arrow")
        txt.pack(side="left", fill="both", expand=True)
        sb.config(command=txt.yview)
        txt.insert("1.0", text)
        txt.config(state="disabled")

        btns = tk.Frame(win, bg=T["bg"])
        btns.pack(fill="x", padx=18, pady=(0, 16))

        def save():
            path = filedialog.asksaveasfilename(parent=win, defaultextension=".txt",
                                                initialfile=f"bill_FH{bill_no}.txt",
                                                filetypes=[("Text file", "*.txt")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("Saved", f"Bill saved to:\n{path}", parent=win)

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            copy_btn.config(text="✔ Copied!")
            self.root.after(1400, lambda: copy_btn.winfo_exists() and copy_btn.config(text="📋 Copy"))

        def new_order():
            win.destroy()
            self.reset_order()
            self.toast("✅ Ready for a new order")

        Btn(btns, "💾 Save", save, bg=T["text"], fg=T["panel"]).pack(side="left")
        copy_btn = Btn(btns, "📋 Copy", copy, bg=T["text"], fg=T["panel"])
        copy_btn.pack(side="left", padx=8)
        Btn(btns, "✔ New Order", new_order, bg=GREEN).pack(side="right")


def main():
    root = tk.Tk()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = min(1280, sw - 60), min(800, sh - 90)
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 20)}")
    root.minsize(1100, 680)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()