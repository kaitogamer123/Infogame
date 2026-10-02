# -*- coding: utf-8 -*-
# =====================================================================
#  screens_setup.py — ПОДГОТОВКА ИГРЫ
#  Экраны:
#    NewGameScreen — выбор класса из сохранённых и числа команд (рис.1, начало)
#    TeamsScreen   — раскидка участников по командам мышью (рис.1)
#  Перетаскивание сделано так: берём плашку мышью, тащим призрак за курсором,
#  отпускаем над нужным блоком. Если мышь «залипла» — работает и простой
#  вариант: клик по плашке (она подсвечивается), потом клик по блоку.
# =====================================================================

import tkinter as tk
from tkinter import ttk, messagebox

import storage
import questions as Q
from ui_theme import (C, px, f, title, text, caps, button, card, divider,
                      entry, RoundButton)

MAX_TEAMS = 8


class NewGameScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.classes = storage.load_classes()

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(20))
        button(head, "В главное меню", lambda: app.show("menu"), kind="ghost", size=14).pack(side="left")
        self.head_lbl = title(head, "Новая игра", size=36)
        self.head_lbl.pack(side="left", padx=px(20))

        _, body = card(self, bg=C["surface"], pad=26)
        body.pack(fill="x", padx=px(40), pady=px(6))

        # ---- класс ----
        caps(body, "выберите класс из сохранённых").pack(anchor="w")
        self.class_var = tk.StringVar()
        names = sorted(self.classes.keys())
        self.combo = ttk.Combobox(body, textvariable=self.class_var, state="readonly",
                                  values=names, font=f(17), width=28)
        self.combo.pack(anchor="w", pady=px(8))
        if names:
            self.combo.set(names[-1])
        else:
            text(body, "Сохранённых классов нет. Загрузите класс в Настройках → "
                       "«Загрузить новый класс».", size=14, color=C["danger"]).pack(anchor="w")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self._show_roster())

        self.roster_box = tk.Frame(body, bg=C["surface"])
        self.roster_box.pack(fill="x", pady=px(12))

        divider(body).pack(fill="x", pady=px(12))

        # ---- число команд ----
        caps(body, "введите количество команд").pack(anchor="w")
        row = tk.Frame(body, bg=C["surface"])
        row.pack(anchor="w", pady=px(8))
        self.teams_var = tk.StringVar(value="4")
        entry(row, self.teams_var, size=20, width=6).pack(side="left")
        text(row, "от 2 до %d команд, по 3-5 человек в каждой" % MAX_TEAMS,
             size=14).pack(side="left", padx=px(14))

        btns = tk.Frame(body, bg=C["surface"])
        btns.pack(fill="x", pady=px(18))
        button(btns, "Продолжить", self._next, kind="primary", size=18, width=300).pack(side="left")
        button(btns, "Назад", lambda: app.show("menu"), kind="secondary", size=16, width=220).pack(
            side="left", padx=px(12))
        self.err = text(btns, "", size=14, color=C["danger"])
        self.err.pack(side="left", padx=px(14))

        self._show_roster()

    def _show_roster(self):
        for w in self.roster_box.winfo_children():
            w.destroy()
        name = self.class_var.get()
        members = self.classes.get(name, [])
        self.head_lbl.configure(text="Новая игра для %s" % (name or "класса"))
        caps(self.roster_box, "состав · %d участников" % len(members)).pack(anchor="w")
        grid = tk.Frame(self.roster_box, bg=C["surface"])
        grid.pack(fill="x", pady=px(6))
        for i, m in enumerate(members):
            chip = tk.Label(grid, text=m, bg=C["cream"], fg=C["ink"], font=f(13, "bold"),
                            padx=px(10), pady=px(6), relief="flat")
            chip.grid(row=i // 4, column=i % 4, sticky="w", padx=px(4), pady=px(4))

    def _next(self):
        name = self.class_var.get()
        members = self.classes.get(name, [])
        if not members:
            self.err.configure(text="Сначала загрузите класс")
            return
        try:
            n = int(self.teams_var.get().strip())
        except Exception:
            n = 0
        if not (2 <= n <= MAX_TEAMS):
            self.err.configure(text="Количество команд от 2 до %d" % MAX_TEAMS)
            return
        self.app.show("teams", class_name=name, members=list(members), teams=n)


# =====================================================================
#  РАСКИДКА ПО КОМАНДАМ (рис.1)
# =====================================================================

class TeamsScreen(tk.Frame):
    def __init__(self, app, class_name="", members=None, teams=4, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.class_name = class_name
        self.n_teams = max(2, int(teams))

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(16))
        button(head, "Назад", lambda: app.show("newgame"), kind="ghost", size=14).pack(side="left")
        title(head, "Новая игра для %s" % class_name, size=32).pack(side="left", padx=px(20))
        text(head, "перетащите участников по командам", size=14).pack(side="right")

        # ---- блоки команд ----
        grid = tk.Frame(self, bg=C["bg"])
        grid.pack(fill="both", expand=True, padx=px(40), pady=px(6))
        self.blocks = {}
        self.teams = []
        for i in range(self.n_teams):
            grid.columnconfigure(i, weight=1)
            outer = tk.Frame(grid, bg=C["ink"])
            outer.grid(row=0, column=i, sticky="nsew", padx=px(8), pady=px(8))
            inner = tk.Frame(outer, bg=C["surface"], padx=px(12), pady=px(12))
            inner.pack(padx=2, pady=2, fill="both", expand=True)
            caps(inner, "состав", size=10).pack(anchor="w")
            holder = tk.Frame(inner, bg=C["surface"])
            holder.pack(fill="both", expand=True, pady=px(8))
            tk.Label(inner, text="команда %d" % (i + 1), bg=C["accent"],
                     fg="#FFFFFF", font=f(15, "bold"), pady=px(6)).pack(fill="x")
            self.blocks[holder] = ("team", i)
            self.teams.append({"name": "Команда %d" % (i + 1), "members": [], "score": 0, "log": []})

        # ---- нижняя лента: свободные + отсутствуют ----
        bottom = tk.Frame(self, bg=C["bg2"])
        bottom.pack(fill="x", padx=px(40), pady=px(12))

        free_wrap = tk.Frame(bottom, bg=C["bg2"])
        free_wrap.pack(side="left", fill="both", expand=True)
        caps(free_wrap, "свободные участники", size=10).pack(anchor="w")
        self.free_holder = tk.Frame(free_wrap, bg=C["bg2"])
        self.free_holder.pack(fill="x", pady=px(6))
        self.blocks[self.free_holder] = ("free", None)

        abs_wrap = tk.Frame(bottom, bg=C["bg2"])
        abs_wrap.pack(side="right")
        tk.Label(abs_wrap, text="отсутствуют", bg=C["ink"], fg=C["cream"],
                 font=f(13, "bold"), padx=px(14), pady=px(6)).pack(anchor="e")
        self.absent_holder = tk.Frame(abs_wrap, bg=C["bg2"])
        self.absent_holder.pack(pady=px(6))
        self.blocks[self.absent_holder] = ("absent", None)

        # ---- чипы участников ----
        self.chips = {}
        for m in (members or []):
            self._make_chip(m)

        foot = tk.Frame(self, bg=C["bg"])
        foot.pack(fill="x", padx=px(40), pady=px(10))
        button(foot, "Начать игру", self._start, kind="primary", size=18, width=320).pack(side="left")
        button(foot, "Распределить автоматически", self._auto, kind="chip", size=14).pack(
            side="left", padx=px(12))
        button(foot, "В главное меню", lambda: app.show("menu"), kind="ghost", size=14).pack(side="right")

        self.selected = None
        self.dragging = None
        self.ghost = None

    # ------------------------- чипы -------------------------
    def _make_chip(self, name):
        chip = RoundButton(self.free_holder, name, lambda n=name: self._pick(n),
                           kind="chip", size=13, padx=14, pady=9)
        chip.pack(side="left", padx=px(5), pady=px(5))
        chip.bind("<ButtonPress-1>", lambda e, n=name: self._press(e, n), add="+")
        chip.bind("<B1-Motion>", self._motion, add="+")
        chip.bind("<ButtonRelease-1>", self._release, add="+")
        self.chips[name] = chip

    def _pick(self, name):
        if self.selected and self.selected in self.chips:
            self.chips[self.selected].set_kind("chip")
        self.selected = name
        self.chips[name].set_kind("dark")

    # ------------------------- перетаскивание -------------------------
    def _press(self, event, name):
        self.dragging = name
        self._moved = False
        self._start_xy = (event.x_root, event.y_root)
        self._make_ghost(name, event.x_root, event.y_root)

    def _make_ghost(self, name, x, y):
        self.ghost = tk.Toplevel(self)
        self.ghost.overrideredirect(True)
        self.ghost.attributes("-topmost", True)
        tk.Label(self.ghost, text=name, bg=C["accent"], fg="#FFFFFF",
                 font=f(13, "bold"), padx=px(12), pady=px(8)).pack()
        self.ghost.geometry("+%d+%d" % (x + px(10), y + px(10)))

    def _motion(self, event):
        if not self.dragging or self.ghost is None:
            return
        if abs(event.x_root - self._start_xy[0]) + abs(event.y_root - self._start_xy[1]) > 6:
            self._moved = True
        self.ghost.geometry("+%d+%d" % (event.x_root + px(10), event.y_root + px(10)))

    def _release(self, event):
        name, moved = self.dragging, self._moved
        if self.ghost is not None:
            self.ghost.destroy()
            self.ghost = None
        self.dragging = None
        if name is None:
            return
        if not moved:
            self._pick(name)
            return
        target = self._block_at(event.x_root, event.y_root)
        if target is not None:
            self._move(name, target)

    def _block_at(self, x, y):
        """Какой блок лежит под курсором (ищем среди наших контейнеров)."""
        w = self.winfo_containing(x, y)
        while w is not None:
            if w in self.blocks:
                return w
            w = w.master
        return None

    def _move(self, name, holder):
        chip = self.chips[name]
        chip.pack_forget()
        chip.pack(in_=holder, side="left", padx=px(5), pady=px(5))
        chip.set_kind("chip")
        if self.selected == name:
            self.selected = None

    def _auto(self):
        """Раздаёт участников по командам по кругу."""
        names = list(self.chips.keys())
        for i, name in enumerate(names):
            self._move(name, list(self.blocks.keys())[i % self.n_teams])

    # ------------------------- старт -------------------------
    def _collect(self):
        for t in self.teams:
            t["members"] = []
        free, absent = [], []
        for name, chip in self.chips.items():
            target = self._owner_of(chip)
            kind, idx = self.blocks[target]
            if kind == "team":
                self.teams[idx]["members"].append(name)
            elif kind == "absent":
                absent.append(name)
            else:
                free.append(name)
        return free, absent

    def _owner_of(self, chip):
        w = chip
        while w is not None:
            if w in self.blocks:
                return w
            w = w.master
        return self.free_holder

    def _start(self):
        free, absent = self._collect()
        if any(len(t["members"]) == 0 for t in self.teams):
            if not messagebox.askyesno(
                    "Пустые команды",
                    "В каких-то командах нет участников. Всё равно начать?"):
                return
        session = {
            "class_name": self.class_name,
            "teams": [dict(t) for t in self.teams],
            "free": free,
            "absent": absent,
            "date": storage.now_stamp(),
            "round": 1,
        }
        self.app.show("game", session=session)
