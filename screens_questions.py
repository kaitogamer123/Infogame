# -*- coding: utf-8 -*-
# =====================================================================
#  screens_questions.py — ВОПРОСЫ И КЛАССЫ
#  Экраны:
#    QuestionsScreen — список всех вопросов, открыть/удалить/добавить (рис.5, ветка)
#    QuestionDialog  — маленькое окно «вопрос + верный ответ»
#    ImportScreen    — добавить вопросы из файла (выбор файла или перетаскивание)
#    LoadClassScreen — загрузить новый класс из txt со списком участников
# =====================================================================

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import storage
import questions as Q
from ui_theme import (C, px, f, title, text, caps, button, card, divider,
                      Scroller, entry, badge)


# =====================================================================
#  СПИСОК ВОПРОСОВ
# =====================================================================

class QuestionsScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.questions = storage.load_questions()

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(20))
        button(head, "Назад", lambda: app.show("settings"), kind="ghost", size=14).pack(side="left")
        title(head, "Настроить вопросы в окне", size=34).pack(side="left", padx=px(20))
        self.counter = text(head, "", size=15, color=C["accent"], weight="bold")
        self.counter.pack(side="right")

        tools = tk.Frame(self, bg=C["bg"])
        tools.pack(fill="x", padx=px(40), pady=(0, px(12)))
        button(tools, "Добавить вопрос", self._add, kind="primary", size=15).pack(side="left")
        button(tools, "Добавить вопросы из файла", lambda: app.show("import"),
               kind="secondary", size=15).pack(side="left", padx=px(10))
        button(tools, "Сохранить", self._save, kind="chip", size=14).pack(side="right")

        self.sc = Scroller(self, bg=C["bg"])
        self.sc.pack(fill="both", expand=True, padx=px(40), pady=(0, px(20)))
        self._rebuild()

    def _rebuild(self):
        for w in self.sc.body.winfo_children():
            w.destroy()
        self.counter.configure(text="вопросов: %d" % len(self.questions))
        if not self.questions:
            _, box = card(self.sc.body, bg=C["surface"], pad=26)
            box.pack(fill="x", pady=px(20))
            title(box, "Вопросов пока нет", size=24).pack(anchor="w")
            text(box, "Добавьте их вручную или загрузите из файла в формате:\n"
                      "1. Какого цвета лось // Answ: Розовый // Time: bas // Rarity: easy",
                 size=15, wrap=1300).pack(anchor="w", pady=px(6))
            return
        for i, q in enumerate(self.questions):
            self._card(i, q)

    def _card(self, i, q):
        _, box = card(self.sc.body, bg=C["surface"] if i % 2 == 0 else C["surface2"], pad=14)
        box.pack(fill="x", pady=px(6))

        top = tk.Frame(box, bg=box.cget("bg"))
        top.pack(fill="x")
        badge(top, "%02d" % (i + 1), C["ink"], fg=C["cream"], size=13).pack(side="left")
        badge(top, Q.SHORT[q.get("rarity", "normal")], C.get(q.get("rarity"), C["normal"]), size=12).pack(
            side="left", padx=px(8))
        badge(top, Q.fmt_time(Q.time_for(q)), C["bg2"], size=12).pack(side="left")

        btns = tk.Frame(top, bg=box.cget("bg"))
        btns.pack(side="right")
        button(btns, "Открыть", lambda i=i: self._toggle(i), kind="chip", size=12, pady=8).pack(side="left", padx=px(4))
        button(btns, "Удалить", lambda i=i: self._delete(i), kind="danger", size=12, pady=8).pack(side="left")

        short = q["text"] if len(q["text"]) <= 160 else q["text"][:157] + "…"
        text(box, short, size=15, color=C["ink"], wrap=1400).pack(anchor="w", pady=(px(8), 0))

    def _toggle(self, i):
        q = self.questions[i]
        win = tk.Toplevel(self)
        win.title("Вопрос %d" % (i + 1))
        win.configure(bg=C["bg"])
        win.geometry("+%d+%d" % (px(140), px(120)))
        _, body = card(win, bg=C["surface"], pad=22)
        body.pack(fill="both", expand=True, padx=px(16), pady=px(16))
        badge(body, Q.LABELS[q.get("rarity", "normal")], C.get(q.get("rarity"), C["normal"]), size=14).pack(anchor="w")
        text(body, q["text"], size=19, color=C["ink"], wrap=1100).pack(anchor="w", pady=px(14))
        divider(body).pack(fill="x", pady=px(6))
        caps(body, "верный ответ").pack(anchor="w")
        text(body, q["answer"], size=19, weight="bold", color=C["accent"], wrap=1100).pack(anchor="w")
        text(body, "Время на ответ: %s" % Q.fmt_time(Q.time_for(q)), size=14).pack(anchor="w", pady=px(10))
        button(body, "Закрыть", win.destroy, kind="secondary", size=14, width=220).pack(anchor="e", pady=px(10))

    def _delete(self, i):
        del self.questions[i]
        self._save(quiet=True)
        self._rebuild()

    def _add(self):
        QuestionDialog(self, on_save=self._append)

    def _append(self, q):
        self.questions.append(q)
        self._save(quiet=True)
        self._rebuild()

    def _save(self, quiet=False):
        storage.save_questions(self.questions)
        if not quiet:
            self.counter.configure(text="сохранено · вопросов: %d" % len(self.questions))


# =====================================================================
#  ОКНО ДОБАВЛЕНИЯ ВОПРОСА
# =====================================================================

class QuestionDialog(tk.Toplevel):
    def __init__(self, master, on_save):
        tk.Toplevel.__init__(self, master)
        self.title("Новый вопрос")
        self.configure(bg=C["bg"])
        self.on_save = on_save
        self.geometry("+%d+%d" % (px(120), px(100)))
        self.resizable(False, False)

        _, body = card(self, bg=C["surface"], pad=22)
        body.pack(fill="both", expand=True, padx=px(16), pady=px(16))

        caps(body, "вопрос").pack(anchor="w")
        self.q_var = tk.StringVar()
        self.q_entry = tk.Text(body, height=5, width=54, font=f(15), bg=C["surface"],
                               fg=C["ink"], insertbackground=C["ink"], relief="flat",
                               highlightthickness=2, highlightbackground=C["ink"],
                               highlightcolor=C["accent"], wrap="word")
        self.q_entry.pack(anchor="w", pady=(px(4), px(12)))

        caps(body, "верный ответ").pack(anchor="w")
        self.a_var = tk.StringVar()
        entry(body, self.a_var, size=15, width=52).pack(anchor="w", pady=(px(4), px(12)))

        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill="x")
        caps(row, "сложность").pack(side="left")
        self.r_var = tk.StringVar(value="normal")
        cb = ttk.Combobox(row, textvariable=self.r_var, state="readonly", width=18,
                          values=[Q.LABELS[r] for r in Q.RARITY_ORDER])
        cb.pack(side="left", padx=px(10))

        row2 = tk.Frame(body, bg=C["surface"])
        row2.pack(fill="x", pady=px(12))
        caps(row2, "время (пусто = базовое)").pack(side="left")
        self.t_var = tk.StringVar(value="")
        entry(row2, self.t_var, size=15, width=10).pack(side="left", padx=px(10))

        row3 = tk.Frame(body, bg=C["surface"])
        row3.pack(fill="x", pady=px(8))
        button(row3, "Сохранить", self._save, kind="primary", size=15).pack(side="left")
        button(row3, "Отмена", self.destroy, kind="ghost", size=14).pack(side="left", padx=px(10))
        self.err = text(row3, "", size=13, color=C["danger"])
        self.err.pack(side="left", padx=px(10))

    def _save(self):
        q_text = self.q_entry.get("1.0", "end").strip()
        answer = self.a_var.get().strip()
        if not q_text or not answer:
            self.err.configure(text="Заполните вопрос и ответ")
            return
        label = self.r_var.get()
        rarity = next((r for r in Q.RARITY_ORDER if Q.LABELS[r] == label), "normal")
        t = Q.parse_time(self.t_var.get())
        self.on_save(Q.make_question(q_text, answer, rarity, t))
        self.destroy()


# =====================================================================
#  ИМПОРТ ВОПРОСОВ ИЗ ФАЙЛА
# =====================================================================

class ImportScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.parsed = []

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(20))
        button(head, "Назад", lambda: app.show("settings"), kind="ghost", size=14).pack(side="left")
        title(head, "Добавить вопросы из файла", size=32).pack(side="left", padx=px(20))

        _, body = card(self, bg=C["surface"], pad=22)
        body.pack(fill="x", padx=px(40), pady=px(6))

        text(body, "Формат строки:\n"
                   "1. Какого цвета лось // Answ: Розовый // Time: bas // Rarity: easy\n"
                   "2. Какого цвета шишка Answ: \"42\" // Time: 03:40 // Rarity: hard\n"
                   "Всё после Answ: — верный ответ. Числовой ответ пишется в кавычках. "
                   "Time: bas — базовое время сложности.",
             size=14, wrap=1500, color=C["ink_soft"]).pack(anchor="w", pady=(0, px(12)))

        # зона перетаскивания
        self.drop = tk.Canvas(body, height=px(120), bg=C["surface2"],
                              highlightthickness=0, cursor="hand2")
        self.drop.pack(fill="x", pady=px(8))
        self.drop.bind("<Configure>", self._draw_drop)
        self.drop.bind("<Button-1>", lambda e: self._pick())
        self._drop_ready = app.register_drop(self.drop, self._on_drop)
        self.drop_hint = ("Перетащите файл сюда или нажмите, чтобы выбрать"
                          if self._drop_ready else
                          "Нажмите, чтобы выбрать файл (перетаскивание доступно, "
                          "если установлен tkinterdnd2)")

        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill="x", pady=px(10))
        button(row, "Выбрать файл", self._pick, kind="secondary", size=15).pack(side="left")
        self.path_lbl = text(row, "файл не выбран", size=14)
        self.path_lbl.pack(side="left", padx=px(14))

        self.notes = text(body, "", size=13, color=C["danger"], wrap=1500)
        self.notes.pack(anchor="w")
        self.count_lbl = text(body, "", size=15, weight="bold", color=C["accent"])
        self.count_lbl.pack(anchor="w")

        self.preview = Scroller(self, bg=C["bg"])
        self.preview.pack(fill="both", expand=True, padx=px(40), pady=px(10))

        foot = tk.Frame(self, bg=C["bg"])
        foot.pack(fill="x", padx=px(40), pady=px(16))
        self.add_btn = button(foot, "Добавить вопросы в базу", self._apply,
                              kind="primary", size=16)
        self.add_btn.pack(side="left")
        self.add_btn.enable(False)
        button(foot, "В настройки", lambda: app.show("settings"), kind="ghost", size=14).pack(side="right")

    def _draw_drop(self, event=None):
        c = self.drop
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            return
        c.create_rectangle(6, 6, w - 6, h - 6, dash=(8, 6), outline=C["accent"], width=3)
        c.create_text(w / 2, h / 2, text=self.drop_hint, font=f(15, "bold"),
                      fill=C["ink"], width=w - px(60))

    def _on_drop(self, event):
        paths = self.app.drop_paths(event)
        if paths:
            self._load(paths[0])

    def _pick(self):
        path = filedialog.askopenfilename(
            title="Выберите файл с вопросами",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            self._load(path)

    def _load(self, path):
        try:
            self.parsed, notes = Q.read_questions_file(path)
        except Exception as exc:
            self.notes.configure(text="Не смог прочитать файл: %s" % exc)
            return
        self.path_lbl.configure(text=os.path.basename(path))
        self.count_lbl.configure(text="Распознано вопросов: %d" % len(self.parsed))
        self.notes.configure(text="\n".join(notes[:6]))
        self.add_btn.enable(len(self.parsed) > 0)
        self.add_btn.set_text("Добавить %d вопросов в базу" % len(self.parsed))

        for w in self.preview.body.winfo_children():
            w.destroy()
        for i, q in enumerate(self.parsed, 1):
            _, box = card(self.preview.body, bg=C["surface"], pad=12)
            box.pack(fill="x", pady=px(4))
            top = tk.Frame(box, bg=box.cget("bg"))
            top.pack(fill="x")
            badge(top, "%02d" % i, C["ink"], fg=C["cream"], size=12).pack(side="left")
            badge(top, Q.SHORT[q["rarity"]], C.get(q["rarity"], C["normal"]), size=11).pack(
                side="left", padx=px(6))
            badge(top, Q.fmt_time(Q.time_for(q)), C["bg2"], size=11).pack(side="left")
            text(box, q["text"], size=14, color=C["ink"], wrap=1400).pack(anchor="w", pady=(px(6), 0))
            text(box, "Ответ: " + q["answer"], size=14, color=C["accent"], weight="bold",
                 wrap=1400).pack(anchor="w")

    def _apply(self):
        base = storage.load_questions()
        storage.add_questions(base, self.parsed)
        messagebox.showinfo("Готово", "Добавлено вопросов: %d" % len(self.parsed))
        self.app.show("questions")


# =====================================================================
#  ЗАГРУЗКА КЛАССА
# =====================================================================

class LoadClassScreen(tk.Frame):
    def __init__(self, app, **kw):
        tk.Frame.__init__(self, app.container, bg=C["bg"], **kw)
        self.app = app
        self.members = []

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=px(40), pady=px(20))
        button(head, "Назад", lambda: app.show("settings"), kind="ghost", size=14).pack(side="left")
        title(head, "Загрузить новый класс", size=34).pack(side="left", padx=px(20))

        _, body = card(self, bg=C["surface"], pad=22)
        body.pack(fill="x", padx=px(40), pady=px(6))

        text(body, "В файле — по одному участнику на строку:\n"
                   "Артеменко Антон\nВеселая Ольга\nГаврилова Полина",
             size=14, wrap=1400, color=C["ink_soft"]).pack(anchor="w", pady=(0, px(10)))

        self.drop = tk.Canvas(body, height=px(110), bg=C["surface2"], highlightthickness=0,
                              cursor="hand2")
        self.drop.pack(fill="x", pady=px(8))
        self.drop.bind("<Configure>", self._draw_drop)
        self.drop.bind("<Button-1>", lambda e: self._pick())
        self._drop_ready = app.register_drop(self.drop, self._on_drop)
        self.drop_hint = ("Перетащите txt со списком сюда или нажмите"
                          if self._drop_ready else "Нажмите, чтобы выбрать файл txt")

        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill="x", pady=px(10))
        button(row, "Выбрать файл", self._pick, kind="secondary", size=15).pack(side="left")
        self.path_lbl = text(row, "файл не выбран", size=14)
        self.path_lbl.pack(side="left", padx=px(14))

        row2 = tk.Frame(body, bg=C["surface"])
        row2.pack(fill="x", pady=px(8))
        caps(row2, "как подписать класс в памяти").pack(side="left")
        self.name_var = tk.StringVar(value="")
        entry(row2, self.name_var, size=16, width=16).pack(side="left", padx=px(12))
        self.count_lbl = text(row2, "", size=15, weight="bold", color=C["accent"])
        self.count_lbl.pack(side="left", padx=px(12))

        self.preview = Scroller(self, bg=C["bg"])
        self.preview.pack(fill="both", expand=True, padx=px(40), pady=px(10))

        foot = tk.Frame(self, bg=C["bg"])
        foot.pack(fill="x", padx=px(40), pady=px(16))
        button(foot, "Сохранить класс", self._save, kind="primary", size=16).pack(side="left")
        button(foot, "В настройки", lambda: app.show("settings"), kind="ghost", size=14).pack(side="right")

    def _draw_drop(self, event=None):
        c = self.drop
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            return
        c.create_rectangle(6, 6, w - 6, h - 6, dash=(8, 6), outline=C["accent"], width=3)
        c.create_text(w / 2, h / 2, text=self.drop_hint, font=f(15, "bold"),
                      fill=C["ink"], width=w - px(60))

    def _on_drop(self, event):
        paths = self.app.drop_paths(event)
        if paths:
            self._load(paths[0])

    def _pick(self):
        path = filedialog.askopenfilename(
            title="Выберите txt со списком класса",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            self._load(path)

    def _load(self, path):
        self.members = storage.read_class_file(path)
        self.path_lbl.configure(text=os.path.basename(path))
        if not self.name_var.get().strip():
            self.name_var.set(storage.suggest_class_name(path))
        self.count_lbl.configure(text="Участников: %d" % len(self.members))

        for w in self.preview.body.winfo_children():
            w.destroy()
        grid = tk.Frame(self.preview.body, bg=C["bg"])
        grid.pack(fill="x")
        for i, m in enumerate(self.members):
            _, box = card(grid, bg=C["cream"], pad=10)
            box.grid(row=i // 4, column=i % 4, sticky="nsew", padx=px(5), pady=px(5))
            grid.columnconfigure(i % 4, weight=1)
            text(box, m, size=14, color=C["ink"], weight="bold", wrap=520).pack(anchor="w")

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Имя", "Подпишите класс, например 10В")
            return
        if not self.members:
            messagebox.showwarning("Список", "Сначала выберите файл со списком")
            return
        storage.add_class(name, self.members)
        messagebox.showinfo("Готово", "Класс %s сохранён: %d участников"
                                      % (name, len(self.members)))
        self.app.show("settings")
