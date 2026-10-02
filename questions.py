# -*- coding: utf-8 -*-
# =====================================================================
#  questions.py — ВОПРОСЫ
#  Тут лежит всё, что связано с самими вопросами:
#    - как выглядит один вопрос (словарь);
#    - разбор текстового файла с вопросами (формат «// Answ: // Time: // Rarity:»);
#    - справочники: сколько даётся времени на сложность и сколько баллов она стоит;
#    - раскладка кораблей на поле 8x8 (как в морском бою).
#  Файл ни от чего не зависит, кроме re. Его можно гонять отдельно.
# =====================================================================

import re

# ---------------------------------------------------------------------
#  Справочники сложностей.
#  Время — в секундах. Изменить можно в окне «Создание конфигурации»,
#  тут только значения по умолчанию.
# ---------------------------------------------------------------------

RARITY_ORDER = ["blc", "easy", "normal", "hard", "sphard"]

# базовое время (bas) для каждой сложности
BASE_TIME = {
    "blc": 30,      # 00:30
    "easy": 60,     # 01:00
    "normal": 100,  # 01:40
    "hard": 140,    # 02:20
    "sphard": 210,  # 03:30
}

# как сложность показывается на экране (по-русски, как просили)
LABELS = {
    "blc": "Блиц-вопрос",
    "easy": "Лёгкая задача",
    "normal": "Средняя задача",
    "hard": "Сложная задача",
    "sphard": "Очень сложная задача",
}

# короткая подпись для плашки
SHORT = {
    "blc": "БЛИЦ",
    "easy": "ЛЁГКАЯ",
    "normal": "СРЕДНЯЯ",
    "hard": "СЛОЖНАЯ",
    "sphard": "ОЧЕНЬ СЛОЖНАЯ",
}

# сколько баллов даётся за верный ответ.
# Один sphard = 4 лёгким = 8 блицам, ровно как просили в пропорции.
POINTS = {
    "blc": 1,
    "easy": 2,
    "normal": 4,
    "hard": 6,
    "sphard": 8,
}

# корабль -> сложность вопроса
SHIP_SIZE = {4: "easy", 2: "normal", 1: "hard"}
# сколько каких кораблей кладём на поле (в сумме 26 клеток из 64)
SHIP_COUNT = {4: 3, 2: 4, 1: 5}
SHIP_LABEL = {
    4: "Четырёхпалубник · лёгкая задача",
    2: "Двухпалубник · средняя задача",
    1: "Однопалубник · сложная задача",
}

# цвета клеток подбираются в ui_theme по этим ключам
RARITY_COLOR_KEY = {
    "blc": "blc",
    "easy": "easy",
    "normal": "normal",
    "hard": "hard",
    "sphard": "sphard",
}

# разные написания сложности в файлах -> наш ключ
_ALIASES = {
    "blc": "blc", "blitz": "blc", "блиц": "blc", "блиц-вопрос": "blc",
    "easy": "easy", "лёгкая": "easy", "легкая": "easy", "light": "easy",
    "normal": "normal", "norm": "normal", "средняя": "normal", "medium": "normal",
    "hard": "hard", "сложная": "hard", "difficult": "hard",
    "sphard": "sphard", "sp": "sphard", "очень сложная": "sphard",
    "особо сложная": "sphard", "extra": "sphard",
}


# ---------------------------------------------------------------------
#  Мелкие помощники
# ---------------------------------------------------------------------

def norm_rarity(raw):
    """Приводит то, что написано в файле, к одному из ключей сложности."""
    if raw is None:
        return None
    key = str(raw).strip().lower().replace("  ", " ")
    key = key.replace("(bas)", "").strip()
    if not key:
        return None
    if key in _ALIASES:
        return _ALIASES[key]
    for alias, val in _ALIASES.items():
        if alias in key:
            return val
    return None


def parse_time(raw):
    """
    Разбирает поле Time.
      'bas' / '' / 'base'  -> None (то есть берём базовое время сложности)
      '03:40' или '3:40'   -> 220 секунд
      '220'                -> 220 секунд
    """
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in ("", "bas", "base", "база", "базовое", "-"):
        return None
    m = re.match(r'^(\d{1,2})\s*:\s*(\d{1,2})$', s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    if re.match(r'^\d+$', s):
        return int(s)
    return None


def fmt_time(sec):
    """220 -> '03:40' (красиво для таймера и списков)."""
    sec = int(sec or 0)
    return "%02d:%02d" % (sec // 60, sec % 60)


def time_for(q, overrides=None):
    """Сколько секунд даётся на конкретный вопрос."""
    if q.get("time"):
        return int(q["time"])
    if overrides and q.get("rarity") in overrides:
        return int(overrides[q["rarity"]])
    return BASE_TIME.get(q.get("rarity"), 100)


def points_for(q, overrides=None):
    """Сколько баллов стоит конкретный вопрос."""
    if overrides and q.get("rarity") in overrides:
        return int(overrides[q["rarity"]])
    return POINTS.get(q.get("rarity"), 2)


def make_question(text, answer, rarity="normal", time=None):
    """Собирает словарь-вопрос. Больше нигде вопрос вручную не собирается."""
    return {
        "text": str(text).strip(),
        "answer": str(answer).strip(),
        "rarity": rarity if rarity in LABELS else "normal",
        "time": int(time) if time else None,
    }


# ---------------------------------------------------------------------
#  Разбор файла с вопросами
# ---------------------------------------------------------------------

_MARKS = [
    (r'//\s*time\s*:', 'time'),
    (r'//\s*время\s*:', 'time'),
    (r'//\s*rarity\s*:', 'rarity'),
    (r'//\s*сложность\s*:', 'rarity'),
    (r'//\s*rar\s*:', 'rarity'),
]


def parse_questions_text(text):
    """
    Разбирает текст с вопросами. Возвращает (список вопросов, список замечаний).

    Строка живёт так:
        2. Какого цвета шишка Answ: "42" // Time: 03:40 // Rarity: hard
    Всё между 'Answ:' и следующей меткой '// Time:' или '// Rarity:' — ответ.
    Номер в начале строки и кавычки вокруг ответа срезаются.
    """
    out, notes = [], []
    for num, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # срезаем «1. » или «2) » в начале, если есть
        body = re.sub(r'^\s*\d+\s*[\.\):\-]\s*', '', line)

        m_ans = re.search(r'an[s]?w\s*:', body, re.I)
        if not m_ans:
            notes.append("Строка %d: нет метки Answ: — пропустил. Строка: %s" % (num, line[:70]))
            continue

        q_text = body[:m_ans.start()].strip()
        rest = body[m_ans.end():]

        # ищем метки Time/Rarity и запоминаем, где они
        marks = []
        for pat, key in _MARKS:
            m = re.search(pat, rest, re.I)
            if m:
                marks.append((m.start(), m.end(), key))
        marks.sort()

        answer = rest[:marks[0][0]] if marks else rest
        vals = {"time": None, "rarity": None}
        for i, (s, e, key) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(rest)
            vals[key] = rest[e:end].strip()

        answer = answer.strip()
        # кавычки вокруг ответа (нужны только для чисел) срезаем
        if len(answer) >= 2 and answer[0] == answer[-1] and answer[0] in ("\"", "'"):
            answer = answer[1:-1].strip()

        if not q_text:
            notes.append("Строка %d: пустой текст вопроса — пропустил." % num)
            continue
        if not answer:
            notes.append("Строка %d: пустой ответ — пропустил." % num)
            continue

        rarity = norm_rarity(vals["rarity"])
        if rarity is None:
            rarity = "normal"
            notes.append("Строка %d: сложность не распознана (%s), поставил «normal»."
                         % (num, vals["rarity"]))

        t = parse_time(vals["time"])
        if vals["time"] and t is None:
            notes.append("Строка %d: время «%s» не разобрал, беру базовое."
                         % (num, vals["time"]))

        out.append(make_question(q_text, answer, rarity, t))

    return out, notes


def read_questions_file(path):
    """Читает файл с вопросами в любой из трёх кодировок и разбирает его."""
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "cp1251", "utf-16"):
        try:
            with open(path, "r", encoding=enc) as fh:
                return parse_questions_text(fh.read())
        except Exception as exc:
            last_err = exc
    raise last_err


# ---------------------------------------------------------------------
#  Раскладка кораблей на поле 8x8
# ---------------------------------------------------------------------

def _free(grid, r, c):
    """Клетка внутри поля и вокруг неё никого нет (корабли не касаются)."""
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and grid[rr][cc] is not None:
                return False
    return True


def build_board(pool, rng=None):
    """
    Собирает поле 8x8. Возвращает список из 64 словарей:
        {"row":0..7, "col":0..7, "ship": id корабля или None,
         "rarity": сложность вопроса, "q": вопрос}
    Пустая клетка = промах = блиц-вопрос.
    """
    import random
    rng = rng or random

    grid = [[None] * 8 for _ in range(8)]
    ships = []
    ship_id = 0

    for size, count in SHIP_COUNT.items():
        placed = 0
        tries = 0
        while placed < count and tries < 2000:
            tries += 1
            horiz = rng.random() < 0.5
            r = rng.randrange(8)
            c = rng.randrange(8)
            cells = []
            ok = True
            for k in range(size):
                rr, cc = (r, c + k) if horiz else (r + k, c)
                if not (0 <= rr < 8 and 0 <= cc < 8) or not _free(grid, rr, cc):
                    ok = False
                    break
                cells.append((rr, cc))
            if not ok:
                continue
            ship_id += 1
            for rr, cc in cells:
                grid[rr][cc] = ship_id
            ships.append({"id": ship_id, "size": size, "cells": cells})
            placed += 1

    # раздаём вопросы по клеткам
    by_rarity = {}
    for q in pool:
        by_rarity.setdefault(q.get("rarity", "normal"), []).append(q)
    for key in by_rarity:
        rng.shuffle(by_rarity[key])

    def take(rarity):
        lst = by_rarity.get(rarity)
        if lst:
            return lst.pop()
        # если вопросов такой сложности не хватило — берём любой оставшийся
        for key in RARITY_ORDER:
            if by_rarity.get(key):
                return by_rarity[key].pop()
        return make_question("Вопросы закончились — придумайте свой", "—", rarity)

    cells = []
    for r in range(8):
        for c in range(8):
            ship = grid[r][c]
            if ship is None:
                rarity = "blc"
            else:
                size = next(s["size"] for s in ships if s["id"] == ship)
                rarity = SHIP_SIZE[size]
            cells.append({
                "row": r, "col": c,
                "ship": ship,
                "size": 0 if ship is None else next(s["size"] for s in ships if s["id"] == ship),
                "rarity": rarity,
                "q": take(rarity),
                "state": "hidden",   # hidden | used
            })
    return cells


def cell_index(row, col):
    """Номер клетки 0..63 по координатам."""
    return row * 8 + col


def cell_name(row, col):
    """Как клетка подписывается для ведущего: «Г-4»."""
    letters = "АБВГДЕЖЗ"
    return "%s-%d" % (letters[col], row + 1)
