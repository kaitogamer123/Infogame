# -*- coding: utf-8 -*-
# =====================================================================
#  sound.py — ЗВУК
#  Проигрывает mp3/wav из папки sounds/ без сторонних библиотек.
#    sounds/over.mp3   — звук окончания времени (самый важный)
#    sounds/click.mp3  — клик по кнопке (необязательно)
#    sounds/win.mp3    — финал игры (необязательно)
#  Если файла нет — на Windows тихо пищим системным динамиком, чтобы
#  тишина не выглядела как поломка.
# =====================================================================

import os
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

_volume = 5   # 0..10, обновляется из настроек
_mci_lock = threading.Lock()
_mci_index = 0


def set_volume(value):
    """Громкость от 0 до 10."""
    global _volume
    try:
        _volume = max(0, min(10, int(value)))
    except Exception:
        _volume = 5


def get_volume():
    return _volume


def _find(name):
    """Ищет файл звука: sounds/имя.mp3, .wav или прямо 'имя' с расширением."""
    for ext in (".mp3", ".wav"):
        p = os.path.join(SOUNDS_DIR, name + ext)
        if os.path.isfile(p):
            return p
    p = os.path.join(SOUNDS_DIR, name)
    if os.path.isfile(p):
        return p
    return None


def play(name):
    """Главный вход: play('over'). Ничего не бросает, если звука нет."""
    if _volume <= 0:
        return
    path = _find(name)
    if path is None:
        _beep()
        return
    threading.Thread(target=_play_file, args=(path,), daemon=True).start()


def play_over():
    """Короткий вызов для конца времени."""
    play("over")


def _play_file(path):
    try:
        if sys.platform.startswith("win"):
            _play_win(path)
        elif sys.platform == "darwin":
            os.system('afplay "%s" >/dev/null 2>&1' % path)
        else:
            os.system('aplay "%s" >/dev/null 2>&1 || paplay "%s" >/dev/null 2>&1' % (path, path))
    except Exception:
        _beep()


def _play_win(path):
    """Проигрывание через winmm (mciSendString). Работает и с mp3."""
    import ctypes
    global _mci_index
    with _mci_lock:
        _mci_index += 1
        alias = "mb_snd_%d" % _mci_index
    mci = ctypes.windll.winmm.mciSendStringW
    # громкость у mci от 0 до 1000
    vol = int(_volume * 100)
    mci('open "%s" type mpegvideo alias %s' % (path, alias), None, 0, 0)
    mci("setaudio %s volume to %d" % (alias, vol), None, 0, 0)
    mci("play %s" % alias, None, 0, 0)


def _beep():
    """Запасной писк, если файла нет."""
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.Beep(660, 180)
            winsound.Beep(440, 260)
        else:
            print("\a", end="")
    except Exception:
        pass


def stop_all():
    """На будущее: заглушить всё, что играет."""
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.winmm.mciSendStringW("close all", None, 0, 0)
    except Exception:
        pass
