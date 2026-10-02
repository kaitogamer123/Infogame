# -*- coding: utf-8 -*-
# =====================================================================
#  main.py — ТОЧКА ВХОДА
#  Запуск:  python main.py
#  Тут живёт:
#    App — класс окна: размеры, масштаб интерфейса, F11, реестр экранов;
#    загрузка фона oboi.png (если файл положили рядом);
#    поддержка перетаскивания файлов (работает, если установлен tkinterdnd2);
#    ловля ошибок в crash.log, чтобы программа не падала молча.
# =====================================================================

import os
import re
import sys
import traceback
import tkinter as tk

# перетаскивание файлов мышью — необязательная фича
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_OK = True
    _Base = TkinterDnD.Tk
except Exception:
    DND_OK = False
    _Base = tk.Tk

import storage
import sound
from ui_theme import C, px, set_scale, get_scale, clear_fonts, apply_styles, f
from screens_menu import (MenuScreen, SettingsScreen, ConfigScreen,
                          RulesScreen, HistoryScreen, ResultScreen)
from screens_questions import QuestionsScreen, ImportScreen, LoadClassScreen
from screens_setup import NewGameScreen, TeamsScreen
from game import GameScreen

SCREENS = {
    "menu": MenuScreen,
    "settings": SettingsScreen,
    "config": ConfigScreen,
    "rules": RulesScreen,
    "history": HistoryScreen,
    "result": ResultScreen,
    "questions": QuestionsScreen,
    "import": ImportScreen,
    "loadclass": LoadClassScreen,
    "newgame": NewGameScreen,
    "teams": TeamsScreen,
    "game": GameScreen,
}


class App(_Base):
    def __init__(self):
        _Base.__init__(self)
        self.settings = storage.load_settings()
        sound.set_volume(self.settings.get("sound", 5))

        self.title("Морской бой — игра к Дню учителя")
        self.configure(bg=C["bg"])
        self.minsize(px(420), px(420))

        # иконка/фон из файла, если есть
        self.bg_photo = self._load_background("oboi.png")

        apply_styles(self)

        self.container = tk.Frame(self, bg=C["bg"])
        self.container.pack(fill="both", expand=True)

        self.current = None
        self.current_name = None
        self._ui_scale = 1.0
        self._fullscreen = False
        self._resize_job = None

        # стартовый размер окна
        w = int(self.settings.get("width", 1080))
        h = int(self.settings.get("height", 1920))
        self.set_window_size(w, h, remember=False)

        # клавиши
        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.bind("<Escape>", lambda e: self.toggle_fullscreen(False))
        self.bind("<Configure>", self._on_configure)

        self.show("menu")

    # ---------------------------------------------------------
    #  Экраны
    # ---------------------------------------------------------
    def show(self, name, **kwargs):
        """Убирает текущий экран и рисует новый. Все экраны вызываются так."""
        if self.current is not None:
            self.current.destroy()
        cls = SCREENS.get(name, MenuScreen)
        self.current = cls(self, **kwargs)
        self.current.pack(fill="both", expand=True)
        self.current_name = name

    # ---------------------------------------------------------
    #  Окно и масштаб
    # ---------------------------------------------------------
    def set_window_size(self, w, h, remember=True):
        """Ставит размер окна и пересчитывает масштаб интерфейса."""
        if self._fullscreen:
            self.toggle_fullscreen(False)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = max(360, min(int(w), sw))
        h = max(360, min(int(h), sh))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))
        if remember:
            self.settings["width"] = w
            self.settings["height"] = h
            storage.save_settings(self.settings)
        self.update_idletasks()
        self._apply_scale(w, h)

    def toggle_fullscreen(self, force=None):
        """F11: убираем рамку и разворачиваем на весь экран."""
        want = not self._fullscreen if force is None else bool(force)
        self._fullscreen = want
        try:
            self.overrideredirect(want)
            self.attributes("-fullscreen", want)
        except Exception:
            pass
        if want:
            self.geometry("%dx%d+0+0" % (self.winfo_screenwidth(), self.winfo_screenheight()))
        else:
            self.set_window_size(self.settings.get("width", 1080),
                                 self.settings.get("height", 1920), remember=False)
        self.update_idletasks()
        self._apply_scale(self.winfo_screenwidth(), self.winfo_screenheight())

    def set_ui_scale(self, value):
        """Ручной множитель масштаба (кнопки «Мельче / Крупнее» в настройках)."""
        self._ui_scale = float(value)
        self._apply_scale()

    def _apply_scale(self, w=None, h=None):
        """Считает масштаб от размера окна. w/h можно передать явно —
        сразу после geometry() реальные размеры tkinter ещё не знает."""
        w = w or self.winfo_width()
        h = h or self.winfo_height()
        if w < 50:
            w = self.settings.get("width", 1080)
        if h < 50:
            h = self.settings.get("height", 1920)
        auto = min(w / 1080.0, h / 900.0)
        sc = max(0.45, min(2.5, auto * self._ui_scale))
        if abs(sc - get_scale()) > 0.02:
            set_scale(sc)
            clear_fonts()
            self._rerender()

    def _rerender(self):
        """Перерисовывает текущий экран с новым масштабом.
        Игру и экраны с данными не трогаем — там всё равно потеряется состояние."""
        safe = ("menu", "settings", "rules", "history", "questions",
                "import", "loadclass", "newgame", "config")
        if self.current_name in safe:
            self.show(self.current_name)

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._resize_job:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(250, self._apply_scale)

    # ---------------------------------------------------------
    #  Фон
    # ---------------------------------------------------------
    def _load_background(self, name):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        if not os.path.isfile(path):
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img = img.resize((max(1, self.winfo_screenwidth() // 2), 1200))
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
        try:
            return tk.PhotoImage(file=path)
        except Exception:
            return None

    # ---------------------------------------------------------
    #  Перетаскивание файлов
    # ---------------------------------------------------------
    def register_drop(self, widget, callback):
        """Вешает на виджет приём файлов. False, если tkinterdnd2 не установлен."""
        if not DND_OK:
            return False
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", callback)
            return True
        except Exception:
            return False

    def drop_paths(self, event):
        """Разбирает event.data из перетаскивания в список путей."""
        data = getattr(event, "data", "") or ""
        out = []
        for m in re.finditer(r'\{([^}]+)\}|(\S+)', data):
            out.append((m.group(1) or m.group(2)).strip())
        return [p for p in out if p]


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # пишем ошибку в файл, чтобы можно было показать её тому, кто чинит
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log"),
                      "a", encoding="utf-8") as fh:
                fh.write("=== ошибка ===\n")
                traceback.print_exc(file=fh)
        except Exception:
            pass
        raise
