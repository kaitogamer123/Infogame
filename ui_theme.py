# -*- coding: utf-8 -*-
# =====================================================================
#  ui_theme.py — ОФОРМЛЕНИЕ
#  Цвета (палитра с рис.7), шрифты, скруглённые кнопки, карточки,
#  прокручиваемые области и мелкие виджеты. Все размеры считаются
#  через px() от масштаба окна, поэтому интерфейс одинаково выглядит
#  и на 512x512, и на полный экран.
# =====================================================================

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ---------------------------------------------------------------------
#  ПАЛИТРА (рис.7) — 21 цвет, подписан как в оригинале
# ---------------------------------------------------------------------

PALETTE = [
    ("#B65037", "Терракота"),
    ("#CF7147", "Ржавчина"),
    ("#F17602", "Оранжевый"),
    ("#CCA898", "Пыльная роза"),
    ("#B7A6A1", "Тёплая серо-бежевая"),
    ("#DCB67D", "Песок"),
    ("#EDDDF0", "Светлый песок"),
    ("#F2D19B", "Светлый песок 2"),
    ("#E9DCC7", "Картон"),
    ("#F9E69F", "Солома"),
    ("#DFB14B", "Охра"),
    ("#F8EED7", "Крем"),
    ("#FEC75C", "Жёлтый"),
    ("#F3F299", "Бледный лимон"),
    ("#E3F7B3", "Светлая зелень"),
    ("#C9CE93", "Олива светлая"),
    ("#A9A94C", "Олива"),
    ("#A2A999", "Зелёно-серый"),
    ("#CFE9CA", "Мятный"),
    ("#CFE2C4", "Мятный 2"),
    ("#9FC8A", "Бирюзовый"),
]
# последний цвет в оригинале был #9FC8A (5 знаков) — дописываем недостающий ноль
PALETTE[-1] = ("#9FC8AA", "Бирюзовый")

# Семантические цвета: что за что отвечает в интерфейсе
C = {
    "bg":        "#EFE9DC",   # фон окна — тёплый картон
    "bg2":       "#E4DCC8",   # полосы, фальцы
    "surface":   "#FBF6EA",   # карточки
    "surface2":  "#F2EBDA",   # вложенные карточки
    "ink":       "#2B2622",   # основной текст и рамки
    "ink_soft":  "#6E6257",   # подписи
    "line":      "#2B2622",
    "accent":    "#B65037",   # главная кнопка / корпус корабля
    "accent2":   "#CF7147",
    "orange":    "#F17602",   # тревога таймера
    "gold":      "#DFB14B",
    "yellow":    "#FEC75C",
    "olive":     "#8C8F5E",
    "green":     "#A9A94C",
    "teal":      "#9FC8AA",
    "mint":      "#CFE9CA",
    "cream":     "#F8EED7",
    "danger":    "#B65037",
    "ok":        "#7E9B6B",
    "sel":       "#FEC75C",
    # цвета сложностей (берутся из палитры)
    "blc":       "#9FC8AA",
    "easy":      "#E3F7B3",
    "normal":    "#F2D19B",
    "hard":      "#CF7147",
    "sphard":    "#B65037",
    # поле
    "cell":      "#E9DCC7",
    "cell_over": "#DCB67D",
    "cell_used": "#C9CE93",
    "alert":     "#D9534F",   # фон, когда время вышло
}

HEAD_FAMILY = "Georgia"
UI_FAMILY = "Segoe UI"

# ---------------------------------------------------------------------
#  Масштаб
# ---------------------------------------------------------------------

class _Scale:
    value = 1.0


def set_scale(v):
    _Scale.value = max(0.4, min(2.5, float(v)))


def get_scale():
    return _Scale.value


def px(v):
    """Переводит 'виртуальные' пиксели 1080x1920 в реальные."""
    return int(round(v * _Scale.value))


_fonts = {}


def clear_fonts():
    """Вызывать после смены масштаба, иначе шрифты останутся старого размера."""
    _fonts.clear()


def f(size, weight="normal", family=None):
    """Шрифт с учётом масштаба. f(18, 'bold', HEAD_FAMILY)."""
    family = family or UI_FAMILY
    key = (family, size, weight)
    if key not in _fonts:
        _fonts[key] = tkfont.Font(family=family, size=max(6, px(size)), weight=weight)
    return _fonts[key]


# ---------------------------------------------------------------------
#  Текстовые виджеты
# ---------------------------------------------------------------------

def _bg_of(master):
    try:
        return master.cget("bg")
    except Exception:
        return C["bg"]


def title(parent, text, size=44, color=None, family=None, anchor="w", **kw):
    lbl = tk.Label(parent, text=text, bg=_bg_of(parent), fg=color or C["ink"],
                   font=f(size, "bold", family or HEAD_FAMILY), anchor=anchor, **kw)
    return lbl


def text(parent, text_, size=16, color=None, weight="normal", anchor="w",
         wrap=0, family=None, **kw):
    lbl = tk.Label(parent, text=text_, bg=_bg_of(parent), fg=color or C["ink_soft"],
                   font=f(size, weight, family), anchor=anchor,
                   wraplength=wraplen(parent, wrap), justify=kw.pop("justify", "left"), **kw)
    return lbl


def wraplen(parent, wrap):
    """Ширина переноса: не шире реального окна, иначе текст уедет за край."""
    if not wrap:
        return 0
    wl = px(wrap)
    try:
        tw = parent.winfo_toplevel().winfo_width()
        if tw > 200:
            wl = min(wl, int(tw * 0.92))
    except Exception:
        pass
    return max(px(200), wl)


def caps(parent, text_, size=12, color=None, **kw):
    """Мелкая подпись капслоком с трекингом — как подписи под чипами палитры."""
    shown = "\u2009".join(list(str(text_).upper().replace(" ", "\u00a0")))
    return text(parent, shown, size=size, color=color or C["ink_soft"],
                weight="bold", anchor="w", **kw)


def badge(parent, text_, color, fg=None, size=12):
    """Цветная плашка со сложностью."""
    return tk.Label(parent, text=" " + str(text_) + " ", bg=color,
                    fg=fg or C["ink"], font=f(size, "bold"), padx=px(6), pady=px(2))


# ---------------------------------------------------------------------
#  Скруглённая кнопка
# ---------------------------------------------------------------------

class RoundButton(tk.Canvas):
    KINDS = {
        "primary":   (C["accent"], "#FFFFFF", C["ink"]),
        "secondary": (C["surface"], C["ink"], C["ink"]),
        "danger":    (C["orange"], "#FFFFFF", C["ink"]),
        "ghost":     (C["bg2"], C["ink_soft"], C["ink"]),
        "chip":      (C["cream"], C["ink"], C["accent"]),
        "dark":      (C["ink"], C["cream"], C["ink"]),
    }

    def __init__(self, master, text_, command=None, kind="primary", size=16,
                 padx=26, pady=12, width=None, bg=None, weight="bold",
                 wrap=0, hover=True):
        self._bg = bg or _bg_of(master)
        tk.Canvas.__init__(self, master, bg=self._bg, highlightthickness=0, bd=0,
                           cursor="hand2")
        self._text = str(text_)
        self._command = command
        self._kind = kind
        self._hover = hover
        self._enabled = True
        self._wrap = wrap
        self._font = f(size, weight)
        self._padx, self._pady = px(padx), px(pady)

        txt_w = self._font.measure(self._text)
        if wrap:
            txt_w = min(txt_w, px(wrap))
        if width:
            self._w = px(width)
        else:
            self._w = txt_w + self._padx * 2
        self._h = self._font.metrics("linespace") + self._pady * 2
        self.configure(width=self._w, height=self._h)

        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._leave)
        self._draw()

    # --- отрисовка ---
    def _round(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
               x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2,
               x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self, hot=False):
        self.delete("all")
        fill, fg, outline = self.KINDS.get(self._kind, self.KINDS["secondary"])
        if not self._enabled:
            fill, fg, outline = C["bg2"], "#A79C8E", "#C4B8A5"
        if hot and self._enabled and self._hover:
            fill = _lighten(fill, 14)
        r = min(self._h // 2, px(14))
        # тень-подложка как у чипов палитры
        self._round(4, 4, self._w, self._h, r, fill=C["bg2"], outline="")
        self._round(0, 0, self._w - 4, self._h - 4, r, fill=fill, outline=outline, width=2)
        self.create_text(self._w / 2 - 2, (self._h - 4) / 2, text=self._text,
                         font=self._font, fill=fg,
                         width=px(self._wrap) if self._wrap else 0)

    def _click(self, _=None):
        if self._enabled and self._command:
            self._command()

    def _enter(self, _=None):
        self._draw(hot=True)

    def _leave(self, _=None):
        self._draw(hot=False)

    def set_text(self, t):
        self._text = str(t)
        self._draw()

    def set_command(self, cmd):
        self._command = cmd

    def enable(self, flag=True):
        self._enabled = bool(flag)
        self.configure(cursor="hand2" if flag else "arrow")
        self._draw()

    def set_kind(self, kind):
        self._kind = kind
        self._draw()


def _lighten(hex_color, amount):
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, r + amount * 255 // 100)
    g = min(255, g + amount * 255 // 100)
    b = min(255, b + amount * 255 // 100)
    return "#%02x%02x%02x" % (r, g, b)


def button(parent, text_, command=None, kind="primary", **kw):
    """Обычная кнопка — так проще, чем плодить RoundButton вручную."""
    return RoundButton(parent, text_, command=command, kind=kind, **kw)


# ---------------------------------------------------------------------
#  Карточка с рамкой-тенью
# ---------------------------------------------------------------------

def card(parent, bg=None, border=2, pad=14):
    """Карточка с толстой рамкой. Возвращает (рамка, рамка) —
    содержимое кладём во второй элемент:  _, box = card(...); box.pack(...)"""
    box = tk.Frame(parent, bg=bg or C["surface"],
                   highlightthickness=border, highlightbackground=C["ink"],
                   highlightcolor=C["ink"], padx=px(pad), pady=px(pad))
    return box, box


def divider(parent, color=None):
    return tk.Frame(parent, bg=color or C["bg2"], height=px(2))


# ---------------------------------------------------------------------
#  Прокручиваемая область
# ---------------------------------------------------------------------

class Scroller(tk.Frame):
    def __init__(self, master, bg=None):
        tk.Frame.__init__(self, master, bg=bg or _bg_of(master))
        self.canvas = tk.Canvas(self, bg=bg or _bg_of(master), highlightthickness=0)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=bg or _bg_of(master))
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", self._wheel)
        self.canvas.bind_all("<Button-5>", self._wheel)

    def _on_body(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _wheel(self, event):
        try:
            if not self.winfo_ismapped():
                return
            delta = getattr(event, "delta", 0)
            if delta:
                self.canvas.yview_scroll(int(-delta / 120), "units")
            elif getattr(event, "num", 0) == 4:
                self.canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", 0) == 5:
                self.canvas.yview_scroll(3, "units")
        except Exception:
            pass


# ---------------------------------------------------------------------
#  Поля ввода
# ---------------------------------------------------------------------

def entry(parent, textvariable=None, size=16, width=20, **kw):
    e = tk.Entry(parent, textvariable=textvariable, font=f(size),
                 bg=C["surface"], fg=C["ink"], insertbackground=C["ink"],
                 relief="flat", highlightthickness=2,
                 highlightbackground=C["ink"], highlightcolor=C["accent"],
                 width=px(width), **kw)
    return e


def spinbox(parent, textvariable, from_=-100, to=200, size=16, width=6, **kw):
    s = tk.Spinbox(parent, textvariable=textvariable, from_=from_, to=to,
                   font=f(size, "bold"), width=width, relief="flat",
                   buttonbackground=C["bg2"], bg=C["surface"], fg=C["ink"],
                   highlightthickness=2, highlightbackground=C["ink"],
                   highlightcolor=C["accent"], **kw)
    return s


def apply_styles(root):
    """Стили ttk — полосы прокрутки, выпадающие списки, слайдер звука."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TCombobox", fieldbackground=C["surface"], background=C["bg2"],
                    foreground=C["ink"], arrowcolor=C["ink"], padding=px(6))
    style.map("TCombobox", fieldbackground=[("readonly", C["surface"])])
    style.configure("Vertical.TScrollbar", background=C["bg2"], troughcolor=C["surface"],
                    bordercolor=C["bg"], arrowcolor=C["ink"])
    style.configure("Horizontal.TScale", background=C["bg"], troughcolor=C["bg2"])
    style.configure("TSpinbox", fieldbackground=C["surface"], arrowcolor=C["ink"])
