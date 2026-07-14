# -*- coding: utf-8 -*-
"""
Модуль эмуляции ввода.
Использует pydirectinput для эмуляции клавиатуры и мыши в играх с DirectX.
Обеспечивает безопасное отслеживание и отпускание зажатых клавиш.
"""

import time
import logging
import pydirectinput

# Отключаем дефолтную паузу 100мс pydirectinput после каждого вызова,
# чтобы все настроенные в GUI задержки отрабатывали с точностью до миллисекунды.
pydirectinput.PAUSE = 0.0
pydirectinput.FAILSAFE = False

logger = logging.getLogger("FishingBot")

# Множество зажатых в данный момент клавиш для безопасного сброса
_pressed_keys = set()

def press_key(key, duration=0.15):
    """Имитирует физическое нажатие и удержание клавиши на указанное время."""
    logger.debug(f"Имитация нажатия '{key}' на {duration} сек...")
    try:
        pydirectinput.keyDown(key)
        _pressed_keys.add(key)
        time.sleep(duration)
    finally:
        pydirectinput.keyUp(key)
        if key in _pressed_keys:
            _pressed_keys.remove(key)


def key_down(key):
    """Зажимает клавишу и регистрирует её в системе безопасности."""
    if key not in _pressed_keys:
        pydirectinput.keyDown(key)
        _pressed_keys.add(key)


def key_up(key):
    """Отпускает клавишу и удаляет из регистрации."""
    pydirectinput.keyUp(key)
    if key in _pressed_keys:
        _pressed_keys.remove(key)


def release_all_keys():
    """Отпускает ВСЕ зажатые ботом клавиши. Важно при экстренной остановке!"""
    if _pressed_keys:
        logger.info(f"Сброс зажатых клавиш: {list(_pressed_keys)}")
    
    # Копируем список для безопасной итерации
    keys_to_release = list(_pressed_keys)
    for key in keys_to_release:
        try:
            pydirectinput.keyUp(key)
        except Exception as e:
            logger.error(f"Не удалось отпустить клавишу {key}: {e}")
            
    _pressed_keys.clear()
    
    # Дополнительно отпускаем стандартные клавиши балансировки
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('d')


def click_rmb(x, y):
    """Выполняет клик правой кнопкой мыши (ПКМ) в указанных координатах экрана."""
    logger.info(f"Имитация клика ПКМ по координатам ({x}, {y})")
    try:
        pydirectinput.moveTo(int(x), int(y))
        time.sleep(0.15)
        pydirectinput.mouseDown(button='right')
        time.sleep(0.15)
        pydirectinput.mouseUp(button='right')
    except Exception as e:
        logger.error(f"Ошибка при клике ПКМ: {e}")
