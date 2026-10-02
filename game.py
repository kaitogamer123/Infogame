# -*- coding: utf-8 -*-
# =====================================================================
#  game.py — САМА ИГРА
#  Экран GameScreen, внутри него четыре фазы:
#    wheel   — колесо фортуны решает, кто стреляет первым (только в начале);
#    board   — поле 8x8, выбираем клетку и жмём «Подтвердить»;
#    question— вопрос, таймер, показ ответа;
#    score   — окно, где ведущий выдаёт баллы командам.
#  Плюс лист ответов, досрочное завершение (двойное нажатие) и запись
#  результата в историю.
# =====================================================================

import math
import random
import tkinter as tk

import storage
import sound
import questions as Q
from ui_theme import (C, px, f, title, text, caps, button, card, divider,
                      badge, Scroller, spinbox, HEAD_FAMILY, wraplen)

CELL_COLORS = [C["accent"], C["gold"], C["teal"], C["olive"], C["accent2"],
               C["yellow"], C["mint"], C["green"]]


class GameScreen(tk.Frame):
    def __init__(self, app, session=None, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.session = session or {}
        self.teams = self.session.get("teams", [])
        for t in self.teams:
            t.setdefault("score", 0)
            t.setdefault("log", [])

        self.settings = app.settings
        self.pool = storage.load_questions()
        self.board = Q.build_board(self.pool)
        self.turn = 0              # чей сейчас выстрел (индекс команды)
        self.round_no = 1
        self.phase = "wheel"
        self._after_id = None
        self._selected = None      # выбранная клетка
        self._angle = 0.0
        self.winner = 0

        self._build_top()
        self.content = tk.Frame(self, bg=C["bg"])
        self.content.pack(fill="both", expand=True)
        self._build_foot()
        self._show_wheel()

    # =============================================================
    #  ВЕРХНЯЯ ПОЛОСА
    # =============================================================
    def _build_top(self):
        top = tk.Frame(self, bg=C["ink"])
        top.pack(fill="x")
        left = tk.Frame(top, bg=C["ink"])
        left.pack(side="left", padx=px(20), pady=px(12))
        caps(left, "сейчас стреляет", size=10, color=C["gold"]).pack(anchor="w")
        self.turn_lbl = tk.Label(left, text="", bg=C["ink"], fg=C["cream"],
                                 font=f(26, "bold", HEAD_FAMILY))
        self.turn_lbl.pack(anchor="w")

        mid = tk.Frame(top, bg=C["ink"])
        mid.pack(side="left", padx=px(30))
        caps(mid, "раунд", size=10, color=C["gold"]).pack(anchor="w")
        self.round_lbl = tk.Label(mid, text="1", bg=C["ink"], fg=C["cream"],
                                  font=f(26, "bold", HEAD_FAMILY))
        self.round_lbl.pack(anchor="w")

        self.score_bar = tk.Frame(top, bg=C["ink"])
        self.score_bar.pack(side="right", padx=px(20))
        button(top, "Лист ответов", self._sheet, kind="dark", size=13, pady=9).pack(
            side="right", padx=px(10), pady=px(14))
        button(top, "Закончить", self._finish_click, kind="primary", size=13, pady=9).pack(
            side="right", padx=px(6), pady=px(14))
        self._update_top()

    def _update_top(self):
        self.turn_lbl.configure(text=self.teams[self.turn]["name"])
        self.round_lbl.configure(text=str(self.round_no))
        for w in self.score_bar.winfo_children():
            w.destroy()
        for t in self.teams:
            tk.Label(self.score_bar, text="%s  %d" % (t["name"], t["score"]),
                     bg=C["ink"], fg=C["gold"], font=f(13, "bold")).pack(side="left", padx=px(8))

    # =============================================================
    #  НИЖНЯЯ ПОЛОСА
    # =============================================================
    def _build_foot(self):
        foot = tk.Frame(self, bg=C["bg2"])
        foot.pack(fill="x", side="bottom")
        self.foot_left = tk.Frame(foot, bg=C["bg2"])
        self.foot_left.pack(side="left", padx=px(20), pady=px(12))
        self.foot_right = tk.Frame(foot, bg=C["bg2"])
        self.foot_right.pack(side="right", padx=px(20), pady=px(12))

    # =============================================================
    #  ФАЗА 1. КОЛЕСО ФОРТУНЫ
    # =============================================================
    def _show_wheel(self):
        self.phase = "wheel"
        self._clear()
        self._clear_foot()
        title(self.content, "Кто стреляет первым", size=40).pack(pady=px(24))
        wrap = tk.Frame(self.content, bg=C["bg"])
        wrap.pack(fill="both", expand=True)
        self.wheel = tk.Canvas(wrap, bg=C["bg"], highlightthickness=0)
        self.wheel.pack(fill="both", expand=True)
        self.wheel.bind("<Configure>", lambda e: self._draw_wheel(self._angle))
        self.wheel_btn = button(self.content, "Крутить колесо", self._spin,
                                kind="primary", size=22, width=360, pady=16)
        self.wheel_btn.pack(pady=px(30))
        self.wheel.after(60, lambda: self._draw_wheel(0))

    def _draw_wheel(self, angle):
        c = self.wheel
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 20 or h < 20:
            return
        side = min(w, h)
        cx, cy = w / 2, h / 2
        R = side / 2 - px(40)
        n = max(1, len(self.teams))
        step = 360.0 / n
        for i, t in enumerate(self.teams):
            start = angle + i * step
            c.create_arc(cx - R, cy - R, cx + R, cy + R, start=start, extent=step,
                         fill=CELL_COLORS[i % len(CELL_COLORS)], outline=C["ink"], width=3)
            mid = math.radians(start + step / 2)
            tx = cx + R * 0.62 * math.cos(mid)
            ty = cy - R * 0.62 * math.sin(mid)
            c.create_text(tx, ty, text=t["name"], font=f(15, "bold"), fill=C["ink"],
                          width=px(140))
        c.create_polygon(cx, cy - R - px(4), cx - px(22), cy - R - px(46),
                         cx + px(22), cy - R - px(46), fill=C["accent"], outline=C["ink"],
                         width=2)
        c.create_oval(cx - px(16), cy - px(16), cx + px(16), cy + px(16),
                      fill=C["surface"], outline=C["ink"], width=3)

    def _spin(self):
        self.wheel_btn.enable(False)
        n = len(self.teams)
        self.winner = random.randrange(n)
        step = 360.0 / n
        target = 90 - self.winner * step - step / 2 + 360 * 4 + random.uniform(-10, 10)
        self._spin_anim(0, 40.0, target)

    def _spin_anim(self, k, dur, target):
        p = min(1.0, k / dur)
        ease = 1 - (1 - p) ** 3
        self._angle = target * ease
        self._draw_wheel(self._angle)
        if p < 1.0:
            self._after_id = self.after(30, lambda: self._spin_anim(k + 1, dur, target))
        else:
            self.turn = self.winner
            self._update_top()
            self.wheel_btn.set_text("Первой стреляет %s — начать" % self.teams[self.winner]["name"])
            self.wheel_btn.set_command(self._show_board)
            self.wheel_btn.enable(True)

    # =============================================================
    #  ФАЗА 2. ПОЛЕ 8x8
    # =============================================================
    def _show_board(self):
        self.phase = "board"
        self._clear()
        self._clear_foot()
        self._selected = None

        hint = tk.Frame(self.content, bg=C["bg"])
        hint.pack(fill="x", padx=px(30), pady=(px(16), px(6)))
        text(hint, "Выберите клетку и нажмите «Подтвердить». "
                   "Промах — блиц-вопрос, попадание — задача для всех команд.",
             size=15).pack(side="left")
        text(hint, "осталось клеток: %d" % sum(1 for c in self.board if c["state"] == "hidden"),
             size=15, color=C["accent"], weight="bold").pack(side="right")

        holder = tk.Frame(self.content, bg=C["bg"])
        holder.pack(fill="both", expand=True, padx=px(20), pady=px(6))
        self.board_canvas = tk.Canvas(holder, bg=C["bg"], highlightthickness=0)
        self.board_canvas.pack(fill="both", expand=True)
        self.board_canvas.bind("<Configure>", lambda e: self._draw_board())
        self.board_canvas.bind("<Button-1>", self._board_click)

        button(self.foot_left, "Лист ответов", self._sheet, kind="ghost", size=13).pack(side="left")
        self._exit_button(self.foot_left)
        self.confirm_btn = button(self.foot_right, "Подтвердить", self._confirm,
                                  kind="primary", size=18, width=300, pady=14)
        self.confirm_btn.pack(side="right")
        self.confirm_btn.enable(False)

    def _cell_rect(self, r, col):
        g = self._geom
        x1 = g["x0"] + col * g["size"]
        y1 = g["y0"] + r * g["size"]
        return x1, y1, x1 + g["size"] - g["gap"], y1 + g["size"] - g["gap"]

    def _draw_board(self):
        c = self.board_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        margin_l, margin_t = px(64), px(48)
        size = min((w - margin_l - px(16)) / 8.0, (h - margin_t - px(16)) / 8.0)
        size = max(size, 18)
        gap = max(3, int(size * 0.11))
        self._geom = {"x0": margin_l, "y0": margin_t, "size": size, "gap": gap}

        letters = "АБВГДЕЖЗ"
        for col in range(8):
            x = margin_l + col * size + size / 2
            c.create_text(x, margin_t - px(22), text=letters[col], font=f(16, "bold"),
                          fill=C["ink"])
        for r in range(8):
            y = margin_t + r * size + size / 2
            c.create_text(margin_l - px(26), y, text=str(r + 1), font=f(16, "bold"),
                          fill=C["ink"])

        for cell in self.board:
            r, col = cell["row"], cell["col"]
            x1, y1, x2, y2 = self._cell_rect(r, col)
            used = cell["state"] == "used"
            fill = C.get(cell["rarity"], C["cell"]) if used else C["cell"]
            if self._selected == (r, col):
                fill = C["sel"]
            pts = [x1 + gap, y1, x2 - gap, y1, x2, y1, x2, y1 + gap,
                   x2, y2 - gap, x2, y2, x2 - gap, y2, x1 + gap, y2, x1, y2,
                   x1, y2 - gap, x1, y1 + gap, x1, y1]
            c.create_polygon(pts, smooth=True, fill=fill, outline=C["ink"], width=2)
            if used:
                c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=Q.SHORT[cell["rarity"]],
                              font=f(max(7, int(size / 7)), "bold"), fill=C["ink"])

    def _board_click(self, event):
        if self.phase != "board" or not hasattr(self, "_geom"):
            return
        g = self._geom
        col = int((event.x - g["x0"]) // g["size"])
        r = int((event.y - g["y0"]) // g["size"])
        if not (0 <= r < 8 and 0 <= col < 8):
            return
        cell = self.board[Q.cell_index(r, col)]
        if cell["state"] == "used":
            return
        self._selected = (r, col)
        self.confirm_btn.enable(True)
        self._draw_board()

    def _confirm(self):
        if self._selected is None:
            return
        r, col = self._selected
        self._open_question(Q.cell_index(r, col))

    # =============================================================
    #  ФАЗА 3. ВОПРОС
    # =============================================================
    def _open_question(self, idx):
        self.phase = "question"
        self.cell = self.board[idx]
        q = self.cell["q"]
        self._clear()
        self._clear_foot()

        # верх: сложность + таймер
        bar = tk.Frame(self.content, bg=C["bg"])
        bar.pack(fill="x", padx=px(40), pady=px(24))
        badge(bar, Q.LABELS[self.cell["rarity"]], C.get(self.cell["rarity"], C["normal"]),
              size=18).pack(side="left", ipadx=px(12), ipady=px(6))
        badge(bar, "клетка " + Q.cell_name(self.cell["row"], self.cell["col"]),
              C["bg2"], size=14).pack(side="left", padx=px(12))
        if self.cell["ship"]:
            text(bar, "попадание в корабль — задача для всех команд", size=15,
                 color=C["accent"], weight="bold").pack(side="left", padx=px(12))
        else:
            text(bar, "промах — блиц-вопрос для стреляющих", size=15,
                 color=C["ok"], weight="bold").pack(side="left", padx=px(12))

        self.timer_lbl = tk.Label(bar, text="", bg=C["bg"], fg=C["ink"],
                                  font=f(38, "bold", HEAD_FAMILY))
        self.timer_lbl.pack(side="right")

        # вопрос
        _, box = card(self.content, bg=C["surface"], pad=34)
        box.pack(fill="both", expand=True, padx=px(60), pady=px(10))
        # вопрос крупно, с переносом строк — вдруг он на полстраницы
        wl = wraplen(box, 1500)
        tk.Label(box, text=q["text"], bg=C["surface"], fg=C["ink"],
                 font=f(30, "bold", HEAD_FAMILY), wraplength=wl,
                 justify="left", anchor="w").pack(fill="x", pady=px(10))
        divider(box).pack(fill="x", pady=px(14))
        self.answer_lbl = tk.Label(box, text="ответ скрыт — нажмите «Показать ответ»",
                                   bg=C["surface"], fg=C["ink_soft"], font=f(20),
                                   wraplength=wl, justify="left")
        self.answer_lbl.pack(anchor="w")
        self.alert_band = tk.Label(self.content, text="", bg=C["bg"], fg=C["danger"],
                                   font=f(22, "bold"))
        self.alert_band.pack(fill="x", pady=px(6))

        button(self.foot_left, "Показать ответ", self._show_answer, kind="chip", size=15).pack(
            side="left")
        self._exit_button(self.foot_left)
        button(self.foot_right, "Продолжить", self._to_score, kind="primary", size=18,
               width=320, pady=14).pack(side="right")

        self.time_left = Q.time_for(q, self.settings.get("time"))
        self._update_timer()
        self._tick()

    def _update_timer(self):
        col = C["ink"]
        if self.time_left <= 10:
            col = C["danger"]
        elif self.time_left <= 30:
            col = C["orange"]
        self.timer_lbl.configure(text=Q.fmt_time(self.time_left), fg=col)

    def _tick(self):
        if self.phase != "question":
            return
        if self.time_left <= 0:
            self._time_over()
            return
        self.time_left -= 1
        self._update_timer()
        self._after_id = self.after(1000, self._tick)

    def _time_over(self):
        sound.play("over")
        self.alert_band.configure(text="ВРЕМЯ ВЫШЛО", bg=C["danger"], fg="#FFFFFF")
        self.content.configure(bg=C["bg"])
        self.timer_lbl.configure(text="00:00", fg=C["danger"])

    def _show_answer(self):
        self.answer_lbl.configure(text="Ответ: " + self.cell["q"]["answer"],
                                  fg=C["accent"], font=f(22, "bold"))

    # =============================================================
    #  ФАЗА 4. ВЫДАЧА БАЛЛОВ
    # =============================================================
    def _to_score(self):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self.phase = "score"
        q = self.cell["q"]
        pts = Q.points_for(q, self.settings.get("points"))
        self._clear()
        self._clear_foot()

        title(self.content, "Выдача баллов", size=38).pack(pady=px(20))

        _, box = card(self.content, bg=C["surface"], pad=22)
        box.pack(fill="both", expand=True, padx=px(60), pady=px(6))

        caps(box, "баллы команд за этот раунд").pack(anchor="w", pady=(0, px(10)))
        self.score_vars = []
        grid = tk.Frame(box, bg=C["surface"])
        grid.pack(fill="x")
        for i, t in enumerate(self.teams):
            row = tk.Frame(grid, bg=C["surface2"] if i % 2 else C["surface"])
            row.pack(fill="x", pady=px(3))
            tk.Label(row, text=t["name"], bg=row.cget("bg"), fg=C["ink"],
                     font=f(18, "bold"), width=px(22), anchor="w").pack(side="left", padx=px(8))
            tk.Label(row, text="сейчас %d" % t["score"], bg=row.cget("bg"), fg=C["ink_soft"],
                     font=f(14)).pack(side="left", padx=px(10))
            var = tk.StringVar(value="0")
            spinbox(row, var, size=18, width=6).pack(side="right", padx=px(12), pady=px(4))
            for val in (-10, -1, 1, 2, 3, pts):
                button(row, ("+%d" % val) if val > 0 else str(val),
                       lambda v=val, vv=var: self._bump(vv, v),
                       kind="chip", size=11, pady=7, padx=10).pack(side="right", padx=px(3))
            self.score_vars.append((t, var))

        divider(box).pack(fill="x", pady=px(12))
        text(box, "+%d за верный ответ   ·   +3 первой команде, давшей ответ   ·   "
                  "+2 второй   ·   +1 третьей   ·   +3 команде, которая стреляла"
             % pts, size=15, color=C["ink"], weight="bold", wrap=1500).pack(anchor="w")
        text(box, "Баллы можно править как угодно, в том числе ставить отрицательные "
                  "(например, -10 за списывание).", size=13, wrap=1500).pack(anchor="w")

        # кто стреляет следующим
        caps(box, "право следующего выстрела").pack(anchor="w", pady=(px(16), px(6)))
        row2 = tk.Frame(box, bg=C["surface"])
        row2.pack(anchor="w")
        self.next_var = tk.IntVar(value=(self.turn + 1) % len(self.teams))
        self.next_btns = []
        for i, t in enumerate(self.teams):
            b = button(row2, t["name"], lambda i=i: self._set_next(i),
                       kind="chip", size=13, pady=10)
            b.pack(side="left", padx=px(5))
            self.next_btns.append(b)
        self._paint_next()

        self._exit_button(self.foot_left)
        button(self.foot_right, "Продолжить", self._apply_score, kind="primary", size=18,
               width=320, pady=14).pack(side="right")

    def _bump(self, var, delta):
        try:
            cur = int(var.get())
        except Exception:
            cur = 0
        var.set(str(cur + delta))

    def _set_next(self, i):
        self.next_var.set(i)
        self._paint_next()

    def _paint_next(self):
        for i, b in enumerate(self.next_btns):
            b.set_kind("dark" if i == self.next_var.get() else "chip")

    def _apply_score(self):
        rnd = self.round_no
        for t, var in self.score_vars:
            try:
                val = int(var.get())
            except Exception:
                val = 0
            t["score"] += val
            if val != 0:
                t["log"].append({"round": rnd, "cell": Q.cell_name(self.cell["row"], self.cell["col"]),
                                 "pts": val})
        self.cell["state"] = "used"
        if all(c["state"] == "used" for c in self.board):
            self._finish()
            return
        self.turn = self.next_var.get()
        self.round_no += 1
        self._update_top()
        self._show_board()

    # =============================================================
    #  ЛИСТ ОТВЕТОВ
    # =============================================================
    def _sheet(self):
        win = tk.Toplevel(self)
        win.title("Лист ответов")
        win.configure(bg=C["bg"])
        win.geometry("%dx%d+%d+%d" % (px(760), px(760), px(120), px(80)))
        title(win, "Лист ответов", size=30).pack(anchor="w", padx=px(20), pady=px(16))
        sc = Scroller(win, bg=C["bg"])
        sc.pack(fill="both", expand=True, padx=px(20), pady=(0, px(16)))
        opened = [c for c in self.board if c["state"] == "used"]
        rows = opened + [c for c in self.board if c["state"] != "used"]
        for c in rows:
            used = c["state"] == "used"
            _, box = card(sc.body, bg=C["surface"] if used else C["surface2"], pad=12)
            box.pack(fill="x", pady=px(4))
            top = tk.Frame(box, bg=box.cget("bg"))
            top.pack(fill="x")
            badge(top, Q.cell_name(c["row"], c["col"]), C["ink"], fg=C["cream"], size=12).pack(side="left")
            badge(top, Q.SHORT[c["rarity"]], C.get(c["rarity"], C["normal"]), size=11).pack(
                side="left", padx=px(6))
            if not used:
                caps(top, "ещё не открыта", size=9).pack(side="left", padx=px(8))
            text(box, c["q"]["text"], size=13, color=C["ink"], wrap=1200).pack(anchor="w", pady=(px(4), 0))
            text(box, "Ответ: " + c["q"]["answer"], size=13, weight="bold",
                 color=C["accent"], wrap=1200).pack(anchor="w")
        button(win, "Закрыть", win.destroy, kind="secondary", size=14, width=220).pack(
            padx=px(20), pady=px(14), anchor="e")

    # =============================================================
    #  ЗАВЕРШЕНИЕ ИГРЫ
    # =============================================================
    def _exit_button(self, parent):
        """Кнопка досрочного выхода. Храним её в self.exit_btn — она меняет надпись."""
        self.exit_btn = button(parent, "Закончить досрочно", self._finish_click,
                               kind="ghost", size=13)
        self.exit_btn.pack(side="left", padx=px(8))
        return self.exit_btn

    def _finish_click(self):
        """Выход требует второго нажатия, чтобы не закрыть игру случайно."""
        if getattr(self, "_exit_armed", False):
            self._finish()
            return
        self._exit_armed = True
        btn = getattr(self, "exit_btn", None)
        if btn is not None:
            btn.set_text("Точно закончить? Нажмите ещё раз")
            btn.set_kind("danger")
        self.after(4000, self._disarm)

    def _disarm(self):
        self._exit_armed = False
        btn = getattr(self, "exit_btn", None)
        if btn is not None:
            btn.set_text("Закончить досрочно")
            btn.set_kind("ghost")

    def _finish(self):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        teams_data = [{"name": t["name"], "members": t.get("members", []),
                       "score": t.get("score", 0), "log": t.get("log", [])}
                      for t in self.teams]
        best = max([t["score"] for t in self.teams] or [0])
        winners = [t["name"] for t in self.teams if t["score"] == best]
        entry = {
            "date": self.session.get("date", storage.now_stamp()),
            "class": self.session.get("class_name", "—"),
            "teams": len(self.teams),
            "players": sum(len(t.get("members", [])) for t in self.teams),
            "teams_data": teams_data,
            "winner": ", ".join(winners) if best > 0 else "ничья",
            "note": "Игра остановлена на раунде %d." % self.round_no,
        }
        storage.append_history(entry)
        self.app.show("result", entry=entry)

    # =============================================================
    #  ПОМОЩНИКИ
    # =============================================================
    def _clear(self):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        for w in self.content.winfo_children():
            w.destroy()

    def _clear_foot(self):
        for w in self.foot_left.winfo_children():
            w.destroy()
        for w in self.foot_right.winfo_children():
            w.destroy()
        self._exit_armed = False
        self.exit_btn = None
