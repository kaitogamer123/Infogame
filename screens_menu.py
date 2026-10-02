# -*- coding: utf-8 -*-
# =====================================================================
#  screens_menu.py — ЛОББ И ВСЁ ВОКРУГ НЕГО
#  Тут лежат экраны:
#    MenuScreen    — главное меню (рис.2)
#    SettingsScreen— настройки (рис.5)
#    ConfigScreen  — создание конфигурации (баллы и время по сложностям)
#    RulesScreen   — правила игры
#    HistoryScreen — история игр (рис.3)
#    ResultScreen  — окно результатов одной игры (рис.4)
# =====================================================================

import tkinter as tk
from tkinter import ttk

import storage
import sound
import questions as Q
from ui_theme import (C, px, f, title, text, caps, button, card, divider,
                      Scroller, entry, apply_styles, HEAD_FAMILY, badge)


# =====================================================================
#  ГЛАВНОЕ МЕНЮ
# =====================================================================

class MenuScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app

        # верхняя полоса-фальц как на коробке настольной игры
        top = tk.Frame(self, bg=C["ink"], height=px(46))
        top.pack(fill="x")
        top.pack_propagate(False)
        caps(top, "интеллектуальный бой за партой", size=11, color=C["cream"]).pack(
            side="left", padx=px(20))
        caps(top, "день учителя", size=11, color=C["gold"]).pack(side="right", padx=px(20))

        hero = tk.Frame(self, bg=C["bg"])
        hero.pack(fill="both", expand=True)

        # фон из файла oboi.png, если его положили рядом
        if app.bg_photo is not None:
            bg_lbl = tk.Label(hero, image=app.bg_photo, bg=C["bg"])
            bg_lbl.place(relwidth=1, relheight=1)
            bg_lbl.lower()

        title(hero, "МОРСКОЙ БОЙ", size=88, family=HEAD_FAMILY).pack(pady=(px(70), 0))
        text(hero, "игра для класса: вопросы, корабли и баллы", size=22,
             color=C["accent"], weight="bold").pack(pady=(px(8), px(40)))

        box = tk.Frame(hero, bg=C["bg"])
        box.pack()

        items = [
            ("Новая игра", "primary", lambda: self.app.show("newgame")),
            ("Настройки", "secondary", lambda: self.app.show("settings")),
            ("История игр", "secondary", lambda: self.app.show("history")),
            ("Правила", "secondary", lambda: self.app.show("rules")),
        ]
        for label, kind, cmd in items:
            button(box, label, cmd, kind=kind, size=22, width=340, pady=16).pack(pady=px(10))

        # нижняя полоса с текущим состоянием базы
        bottom = tk.Frame(self, bg=C["bg2"])
        bottom.pack(fill="x", side="bottom")
        qs = len(storage.load_questions())
        cls = storage.load_classes()
        hist = storage.load_history()
        caps(bottom, "вопросов в базе: %d" % qs, size=11).pack(side="left", padx=px(20), pady=px(12))
        caps(bottom, "классов: %d" % len(cls), size=11).pack(side="left", padx=px(20))
        caps(bottom, "сыграно игр: %d" % len(hist), size=11).pack(side="left", padx=px(20))
        caps(bottom, "F11 — во весь экран", size=11, color=C["accent"]).pack(side="right", padx=px(20))


# =====================================================================
#  НАСТРОЙКИ (рис.5)
# =====================================================================

class SettingsScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.settings = app.settings

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(24))
        button(head, "В главное меню", lambda: app.show("menu"), kind="ghost", size=14).pack(side="left")
        title(head, "Настройки", size=40).pack(side="left", padx=px(24))

        _, body = card(self, bg=C["surface"], pad=26)
        body.pack(fill="both", expand=True, padx=px(40), pady=px(10))

        # ---- звук ----
        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill="x", pady=(0, px(18)))
        text(row, "Настроить звук", size=20, weight="bold", color=C["ink"]).pack(side="left")
        self.vol_lbl = text(row, "%d/10" % self.settings.get("sound", 5), size=20,
                            weight="bold", color=C["accent"])
        self.vol_lbl.pack(side="right")

        slider = tk.Scale(body, from_=0, to=10, orient="horizontal", showvalue=False,
                          bg=C["surface"], highlightthickness=0, troughcolor=C["bg2"],
                          activebackground=C["accent"], fg=C["ink"],
                          font=f(12), command=self._vol)
        slider.set(self.settings.get("sound", 5))
        slider.pack(fill="x", pady=(0, px(22)))
        button(body, "Проверить звук", lambda: sound.play("over"), kind="chip", size=14).pack(
            anchor="w", pady=(0, px(20)))

        divider(body).pack(fill="x", pady=px(10))

        for label, cmd in [
            ("Добавить вопросы из файла", lambda: app.show("import")),
            ("Настроить вопросы в окне", lambda: app.show("questions")),
            ("Создание конфигурации", lambda: app.show("config")),
            ("Загрузить новый класс", lambda: app.show("loadclass")),
        ]:
            button(body, label, cmd, kind="secondary", size=18, width=420, pady=12).pack(
                anchor="w", pady=px(8))

        divider(body).pack(fill="x", pady=px(16))

        # ---- окно ----
        text(body, "Размер окна", size=20, weight="bold", color=C["ink"]).pack(anchor="w")
        row2 = tk.Frame(body, bg=C["surface"])
        row2.pack(anchor="w", pady=px(10))
        for label, (w, h) in [
            ("512x512", (512, 512)),
            ("800x800", (800, 800)),
            ("1080x1350", (1080, 1350)),
            ("1080x1920", (1080, 1920)),
            ("Во весь экран", None),
        ]:
            button(row2, label, lambda w=w, h=h: self._resize(w, h),
                   kind="chip", size=13, pady=10).pack(side="left", padx=px(6))

        text(body, "Масштаб интерфейса", size=20, weight="bold", color=C["ink"]).pack(
            anchor="w", pady=(px(18), 0))
        row3 = tk.Frame(body, bg=C["surface"])
        row3.pack(anchor="w", pady=px(10))
        for label, sc in [("Мельче", 0.8), ("Как есть", 1.0), ("Крупнее", 1.2), ("Очень крупно", 1.5)]:
            button(row3, label, lambda sc=sc: self._scale(sc), kind="chip", size=13, pady=10).pack(
                side="left", padx=px(6))
        text(body, "Окно можно тянуть за край — интерфейс пересчитается. "
                   "F11 убирает рамку и разворачивает на весь экран.",
             size=13, wrap=1400).pack(anchor="w", pady=px(8))

    def _vol(self, val):
        v = int(float(val))
        self.settings["sound"] = v
        self.vol_lbl.configure(text="%d/10" % v)
        sound.set_volume(v)
        storage.save_settings(self.settings)

    def _resize(self, w, h):
        if w is None:
            self.app.toggle_fullscreen(True)
        else:
            self.app.set_window_size(w, h)
        self.app.show("settings")

    def _scale(self, s):
        self.app.set_ui_scale(s)
        self.app.show("settings")


# =====================================================================
#  СОЗДАНИЕ КОНФИГУРАЦИИ
# =====================================================================

class ConfigScreen(tk.Frame):
    """Правка времени и баллов по сложностям + сохранение конфигурации."""

    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.settings = app.settings

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(24))
        button(head, "Назад", lambda: app.show("settings"), kind="ghost", size=14).pack(side="left")
        title(head, "Создание конфигурации", size=36).pack(side="left", padx=px(24))

        _, body = card(self, bg=C["surface"], pad=22)
        body.pack(fill="both", expand=True, padx=px(40), pady=px(10))

        hdr = tk.Frame(body, bg=C["surface"])
        hdr.pack(fill="x")
        for lbl, w in (("Сложность", 30), ("Время (мм:сс)", 18), ("Баллов за ответ", 20)):
            text(hdr, lbl, size=14, weight="bold", color=C["ink"], width=w).pack(side="left", padx=px(6))

        self.vars = {}
        for rar in Q.RARITY_ORDER:
            row = tk.Frame(body, bg=C["surface"])
            row.pack(fill="x", pady=px(6))
            badge(row, Q.LABELS[rar], C[rar], size=13).pack(side="left", padx=px(6), ipadx=px(8))

            t_var = tk.StringVar(value=Q.fmt_time(self.settings["time"].get(rar, Q.BASE_TIME[rar])))
            p_var = tk.StringVar(value=str(self.settings["points"].get(rar, Q.POINTS[rar])))
            entry(row, t_var, width=12).pack(side="left", padx=px(6))
            entry(row, p_var, width=12).pack(side="left", padx=px(6))
            self.vars[rar] = (t_var, p_var)

        text(body, "Время пишется как 03:30. Баллы — целым числом, можно отрицательным.",
             size=13).pack(anchor="w", pady=px(10))

        btns = tk.Frame(body, bg=C["surface"])
        btns.pack(fill="x", pady=px(16))
        button(btns, "Сохранить конфигурацию", self._save, kind="primary", size=16).pack(side="left")
        self.status = text(btns, "", size=14, color=C["ok"])
        self.status.pack(side="left", padx=px(16))

    def _save(self):
        for rar, (t_var, p_var) in self.vars.items():
            sec = Q.parse_time(t_var.get())
            if sec is None:
                sec = Q.BASE_TIME[rar]
            self.settings["time"][rar] = sec
            try:
                self.settings["points"][rar] = int(p_var.get().strip())
            except Exception:
                pass
        storage.save_settings(self.settings)
        self.status.configure(text="Сохранено в data/settings.json", fg=C["ok"])


# =====================================================================
#  ПРАВИЛА
# =====================================================================

RULES = [
    ("Поле", "Играем на поле 8x8, как в морском бою. Слева идут цифры 1-8, "
             "сверху буквы А-З. В клетках спрятаны корабли, вокруг них — вода."),
    ("Корабли", "Четырёхпалубник (4 клетки) — лёгкие задачи.\n"
                "Двухпалубник (2 клетки) — средние задачи.\n"
                "Однопалубник (1 клетка) — сложные задачи.\n"
                "Пустая клетка — это промах, в ней прячется блиц-вопрос."),
    ("Ход", "Команды стреляют по очереди. Очередь определяет колесо фортуны "
            "перед первым выстрелом: выпала третья — значит дальше четвёртая, "
            "пятая, потом снова первая и так по кругу."),
    ("Промах", "Попали в пустую клетку — команда отвечает на блиц-вопрос. "
               "Успели ответить за отведённое время — балл ваш, и вы стреляете ещё раз. "
               "Не успели или ошиблись — без выкриков отвечает любая другая команда "
               "(например, по поднятию руки капитана). Верный ответ даёт ей 1 балл "
               "и право стрелять следующей. Если не ответил никто — стреляет та же команда."),
    ("Попадание", "Попали в корабль — вопрос получают ВСЕ команды, а не только та, "
                  "кто стрелял. Побеждает тот, кто первым принесёт ответ на листочке. "
                  "Остальные команды могут донести ответ на этот же вопрос в любой "
                  "момент игры и тоже получить баллы, но права стрелять за это уже не получают."),
    ("Несколько задач", "В ходу у вас может быть открыто сразу несколько задач. "
                        "Пока идёт таймер по новой задаче, к вам могут приносить ответы "
                        "на старые. Поэтому у команды должен быть лист: номер задачи — ответ. "
                        "В программе для этого есть кнопка «Лист ответов»."),
    ("Не успели", "Если за отведённое время никто не решил задачу, стреляет снова та же "
                  "команда. Сама задача при этом остаётся в игре — её можно дорешать позже."),
    ("Баллы", "За верный ответ команде начисляются баллы по сложности задачи "
              "(см. «Создание конфигурации»). Команда, которая стреляла и попала, "
              "получает бонус. Первые три команды, давшие ответ на общую задачу, "
              "получают +3, +2 и +1 соответственно."),
    ("Состав", "В команде 3-5 человек. Роли команда распределяет сама: кто следит "
               "за полем и таймером, кто дорешивает прошлые задачи. Можно даже "
               "выдать по два компьютера на команду."),
    ("Списывание", "За попытку списать команде минус 10 баллов. Попались дважды — "
                   "вся команда получает двойку по информатике. Строго, но честно."),
    ("Победа", "Побеждает команда, набравшая больше всего баллов."),
]


class RulesScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(24))
        button(head, "Назад", lambda: app.show("menu"), kind="ghost", size=14).pack(side="left")
        title(head, "Правила игры", size=40).pack(side="left", padx=px(24))

        sc = Scroller(self, bg=C["bg"])
        sc.pack(fill="both", expand=True, padx=px(40), pady=(0, px(30)))
        body = sc.body

        for i, (name, descr) in enumerate(RULES, 1):
            _, box = card(body, bg=C["surface"] if i % 2 else C["surface2"], pad=18)
            box.pack(fill="x", pady=px(8))
            row = tk.Frame(box, bg=box.cget("bg"))
            row.pack(fill="x")
            badge(row, str(i), C["accent"], fg="#FFFFFF", size=15).pack(side="left", padx=(0, px(12)))
            text(row, name, size=20, weight="bold", color=C["ink"]).pack(side="left")
            text(box, descr, size=15, wrap=1500, color=C["ink_soft"]).pack(
                anchor="w", pady=(px(8), 0))

        button(body, "В главное меню", lambda: app.show("menu"), kind="primary",
               size=16, width=300).pack(pady=px(20))


# =====================================================================
#  ИСТОРИЯ ИГР (рис.3)
# =====================================================================

class HistoryScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(24))
        button(head, "Назад", lambda: app.show("menu"), kind="ghost", size=14).pack(side="left")
        title(head, "История игр", size=40).pack(side="left", padx=px(24))

        sc = Scroller(self, bg=C["bg"])
        sc.pack(fill="both", expand=True, padx=px(40), pady=(0, px(20)))
        self.body = sc.body

        hist = storage.load_history()
        if not hist:
            _, empty = card(self.body, bg=C["surface"], pad=30)
            empty.pack(fill="x", pady=px(30))
            title(empty, "Игр пока нет", size=26).pack(anchor="w")
            text(empty, "Как только первая партия закончится, здесь появится её запись: "
                        "дата, класс, число команд и участников.", size=15, wrap=1200).pack(
                anchor="w", pady=px(6))

        for i, entry_ in enumerate(hist):
            self._row(entry_, i)

        foot = tk.Frame(self, bg=C["bg"])
        foot.pack(fill="x", padx=px(40), pady=px(16))
        button(foot, "В главное меню", lambda: app.show("menu"), kind="secondary", size=15).pack(side="left")
        button(foot, "Очистить историю", self._clear, kind="chip", size=13).pack(side="right")

    def _row(self, entry_, i):
        _, box = card(self.body, bg=C["surface"] if i % 2 == 0 else C["surface2"], pad=16)
        box.pack(fill="x", pady=px(8))
        line = ('%s   "%s"   "%d Команд"   "%d участников"'
                % (entry_.get("date", "—"), entry_.get("class", "—"),
                   len(entry_.get("teams_data", [])), entry_.get("players", 0)))
        lbl = tk.Label(box, text=line, bg=box.cget("bg"), fg=C["ink"],
                       font=f(17, "bold"), anchor="w", cursor="hand2")
        lbl.pack(fill="x")
        lbl.bind("<Button-1>", lambda e, en=entry_: self.app.show("result", entry=en))
        text(box, "Победила %s · нажмите, чтобы открыть таблицу"
                  % entry_.get("winner", "—"), size=13).pack(anchor="w")

    def _clear(self):
        storage.clear_history()
        self.app.show("history")


# =====================================================================
#  ОКНО РЕЗУЛЬТАТОВ (рис.4)
# =====================================================================

class ResultScreen(tk.Frame):
    """Принимает запись истории entry=..., либо живую сессию session=..."""

    def __init__(self, app, entry=None, session=None, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        data = entry or self._from_session(session)

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(22))
        button(head, "В главное меню", lambda: app.show("menu"), kind="ghost", size=14).pack(side="left")
        title(head, "Итоги игры", size=40).pack(side="left", padx=px(24))
        text(head, data.get("date", ""), size=15).pack(side="right")

        sc = Scroller(self, bg=C["bg"])
        sc.pack(fill="both", expand=True, padx=px(40), pady=(0, px(16)))
        body = sc.body

        # --- верхняя строка: чем закончилось ---
        _, top = card(body, bg=C["ink"], pad=18)
        top.pack(fill="x", pady=px(10))
        title(top, "Победила %s" % data.get("winner", "—"), size=30, color=C["gold"]).pack(anchor="w")
        text(top, 'Класс %s · %d команд · %d участников'
                  % (data.get("class", "—"), len(data.get("teams_data", [])),
                     data.get("players", 0)), size=15, color=C["cream"]).pack(anchor="w")

        # --- таблицы по командам ---
        grid = tk.Frame(body, bg=C["bg"])
        grid.pack(fill="x", pady=px(10))
        teams = data.get("teams_data", [])
        cols = 3 if len(teams) > 2 else max(1, len(teams))
        for i, t in enumerate(teams):
            _, box = card(grid, bg=C["surface"], pad=16)
            box.grid(row=i // cols, column=i % cols, sticky="nsew", padx=px(6), pady=px(6))
            grid.columnconfigure(i % cols, weight=1)
            top_row = tk.Frame(box, bg=box.cget("bg"))
            top_row.pack(fill="x")
            text(top_row, t.get("name", "Команда"), size=19, weight="bold",
                 color=C["ink"]).pack(side="left")
            text(top_row, "%d баллов" % t.get("score", 0), size=19, weight="bold",
                 color=C["accent"]).pack(side="right")
            for m in t.get("members", []):
                text(box, "• " + m, size=14, color=C["ink_soft"]).pack(anchor="w")

        # --- доп. инфа: сколько набрали в каждом раунде ---
        _, logbox = card(body, bg=C["surface2"], pad=18)
        logbox.pack(fill="x", pady=px(10))
        text(logbox, "Доп. информация за каждый раунд — сколько баллов набрано",
             size=17, weight="bold", color=C["ink"]).pack(anchor="w", pady=(0, px(10)))

        rounds = {}
        for ti, t in enumerate(teams):
            for rec in t.get("log", []):
                rounds.setdefault(rec.get("round", 0), {})[ti] = rec.get("pts", 0)

        hdr = tk.Frame(logbox, bg=logbox.cget("bg"))
        hdr.pack(fill="x")
        text(hdr, "Раунд", size=13, weight="bold", width=10).pack(side="left")
        for t in teams:
            text(hdr, t.get("name", ""), size=13, weight="bold", width=14).pack(side="left", padx=px(4))
        for rn in sorted(rounds.keys()):
            row = tk.Frame(logbox, bg=logbox.cget("bg"))
            row.pack(fill="x")
            text(row, "Раунд %d" % rn, size=13, width=10, color=C["ink"]).pack(side="left")
            for ti in range(len(teams)):
                val = rounds[rn].get(ti)
                cell_txt = "+%d" % val if (val or 0) > 0 else (str(val) if val else "—")
                col = C["ok"] if (val or 0) > 0 else (C["danger"] if (val or 0) < 0 else C["ink_soft"])
                text(row, cell_txt, size=13, weight="bold", width=14, color=col).pack(
                    side="left", padx=px(4))

        if data.get("note"):
            text(body, data["note"], size=14, wrap=1500).pack(anchor="w", pady=px(6))

        button(body, "В главное меню", lambda: app.show("menu"), kind="primary",
               size=16, width=320).pack(pady=px(18))

    @staticmethod
    def _from_session(session):
        if not session:
            return {"date": "—", "class": "—", "players": 0, "teams_data": [], "winner": "—"}
        teams = []
        for t in session.get("teams", []):
            teams.append({"name": t.get("name"), "members": t.get("members", []),
                          "score": t.get("score", 0), "log": t.get("log", [])})
        best = max([t.get("score", 0) for t in teams] or [0])
        winners = [t["name"] for t in teams if t.get("score", 0) == best]
        return {
            "date": session.get("date", storage.now_stamp()),
            "class": session.get("class_name", "—"),
            "players": sum(len(t.get("members", [])) for t in teams),
            "teams_data": teams,
            "winner": ", ".join(winners) if best > 0 else "ничья",
        }
