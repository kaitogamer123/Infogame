# -*- coding: utf-8 -*-
# =====================================================================
#  storage.py — ХРАНИЛИЩЕ
#  Всё, что программа помнит между запусками, лежит в папке data/:
#    data/settings.json  — настройки (звук, размер окна, баллы и время);
#    data/questions.json — список вопросов;
#    data/classes.json   — сохранённые классы (название -> список участников);
#    data/history.json   — история игр.
#  Формат обычный JSON, поэтому при желании файлы можно править руками.
# =====================================================================

import json
import os
import time as _time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
CLASSES_FILE = os.path.join(DATA_DIR, "classes.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

import questions as Q

DEFAULT_SETTINGS = {
    "sound": 5,          # громкость 0..10
    "width": 1080,
    "height": 1920,
    "fullscreen": False,
    "time": dict(Q.BASE_TIME),   # время по сложностям, секунды
    "points": dict(Q.POINTS),    # баллы по сложностям
    "blind_penalty": -10,        # штраф за списывание
}

# Стартовый набор вопросов, чтобы программа была играбельной сразу.
# Всё это спокойно удаляется в окне «Настроить вопросы в окне».
SEED_QUESTIONS = [
    ("Сколько будет 2 в десятой степени?", "1024", "normal", None),
    ("Какого цвета лось?", "Розовый", "blc", None),
    ("Какого цвета шишка?", "42", "hard", None),
    ("Кто самый крутой на паре?", "Я крутой", "blc", None),
    ("Столица Австралии?", "Канберра", "easy", None),
    ("Сколько будет 17 * 19?", "323", "normal", None),
    ("Что такое HTTP?", "Протокол передачи гипертекста", "easy", None),
    ("Кто написал «Мёртвые души»?", "Николай Гоголь", "easy", None),
    ("Сколько костей в теле взрослого человека?", "206", "normal", None),
    ("Чему равен квадратный корень из 1296?", "36", "normal", None),
    ("Какой химический символ у золота?", "Au", "easy", None),
    ("Что покажет выражение: 5! (факториал)?", "120", "normal", None),
    ("Сколько бит в одном байте?", "8", "blc", None),
    ("Как называется самая длинная река России?", "Лена", "easy", None),
    ("Кто изобрёл лампу накаливания?", "Томас Эдисон", "easy", None),
    ("Сколько планет в Солнечной системе?", "8", "blc", None),
    ("Что такое рекурсия?", "Функция, которая вызывает сама себя", "normal", None),
    ("Какой год считается годом рождения интернета?", "1969", "hard", None),
    ("Сколько будет синус 30 градусов?", "0,5", "normal", None),
    ("Что такое бинарный поиск и какова его сложность?", "Поиск по отсортированному массиву, O(log n)", "hard", None),
    ("Какой язык программирования назван в честь комедийной труппы?", "Python", "easy", None),
    ("Что выведет код: print(type([]) is list)?", "True", "normal", None),
    ("Чему равна скорость света в вакууме (км/с, округлённо)?", "300000", "hard", None),
    ("Сколько цветов в радуге?", "7", "blc", None),
    ("Назовите три закона Ньютона одним словом каждый", "Инерция, F=ma, действие-противодействие", "sphard", 240),
    ("Почему небо голубое?", "Рассеяние Рэлея на молекулах воздуха", "sphard", 240),
]


def _ensure_dir():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(path, default):
    """Читает JSON. Если файла нет или он битый — отдаёт значение по умолчанию."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def _write_json(path, data):
    """Пишет JSON красиво и с русскими буквами."""
    _ensure_dir()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# --------------------------- настройки -------------------------------

def load_settings():
    """Настройки + подтягивание недостающих полей из DEFAULT_SETTINGS."""
    data = _read_json(SETTINGS_FILE, {})
    res = dict(DEFAULT_SETTINGS)
    res.update(data or {})
    # вложенные словари собираем по ключам, чтобы новые сложности не потерялись
    for key in ("time", "points"):
        merged = dict(DEFAULT_SETTINGS[key])
        merged.update(res.get(key) or {})
        res[key] = merged
    return res


def save_settings(settings):
    _write_json(SETTINGS_FILE, settings)


# --------------------------- вопросы ---------------------------------

def load_questions():
    """Список вопросов. При первом запуске засевается стартовым набором."""
    data = _read_json(QUESTIONS_FILE, None)
    if data is None:
        seed = [Q.make_question(t, a, r, tm) for (t, a, r, tm) in SEED_QUESTIONS]
        save_questions(seed)
        return seed
    return data


def save_questions(qlist):
    _write_json(QUESTIONS_FILE, qlist)


def add_questions(qlist, new_ones):
    """Докидывает вопросы в конец списка и сразу сохраняет."""
    qlist = list(qlist) + list(new_ones)
    save_questions(qlist)
    return qlist


# --------------------------- классы ----------------------------------

def load_classes():
    """{'11В': ['Артеменко Антон', ...], '9В': [...]}"""
    return _read_json(CLASSES_FILE, {})


def save_classes(classes):
    _write_json(CLASSES_FILE, classes)


def add_class(name, members):
    """Сохраняет класс под именем name. Имя нормализуется: '10 в' -> '10В'."""
    name = (name or "").strip().replace(" ", "")
    classes = load_classes()
    classes[name] = list(members)
    save_classes(classes)
    return name


def read_class_file(path):
    """Читает txt со списком фио, по одной фамилии на строку. Пустые строки игнорирует."""
    members = []
    for enc in ("utf-8-sig", "utf-8", "cp1251", "utf-16"):
        try:
            with open(path, "r", encoding=enc) as fh:
                for line in fh:
                    s = line.strip()
                    if s:
                        members.append(s)
            return members
        except Exception:
            continue
    return members


def suggest_class_name(path):
    """Предлагает имя файла без расширения: '10V.txt' -> '10V'."""
    base = os.path.basename(path or "")
    name, _ = os.path.splitext(base)
    return name.strip()


# --------------------------- история ---------------------------------

def load_history():
    """Список игр, новые сверху."""
    data = _read_json(HISTORY_FILE, [])
    return data or []


def append_history(entry):
    """Одна запись истории:
       {"date": "16.09.2026 17:30", "class": "11В", "teams": 5, "players": 11,
        "teams_data": [{"name","members","score","log"}], "winner": "Команда 2"}
    """
    hist = load_history()
    hist.insert(0, entry)
    _write_json(HISTORY_FILE, hist)
    return hist


def clear_history():
    _write_json(HISTORY_FILE, [])


def now_stamp():
    """Красивая дата-время для истории."""
    return _time.strftime("%d.%m.%Y %H:%M", _time.localtime())
