# -*- coding: utf-8 -*-
"""
Модуль конфигурации бота.
Управляет сохранением и загрузкой параметров из config.json.
"""

import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "MONITOR_INDEX": 1,
    "GAME_REGION": None,            # None для полноэкранного или [x, y, w, h] для оконного
    "CONTROL_MODE": "hold",          # "hold" или "click"
    "SWEET_SPOT_MARGIN": 5,
    "CLICK_TAP_DURATION": 0.04,
    "CLICK_COOLDOWN": 0.05,
    "KEY_PRESS_DURATION": 0.15,
    "SCREENSHOT_FPS": 30,            # Частота скриншотов (кадров в секунду)
    "GREEN_HSV_LOW": [50, 45, 45],
    "GREEN_HSV_HIGH": [90, 255, 255],
    "YELLOW_HSV_LOW": [18, 90, 90],
    "YELLOW_HSV_HIGH": [38, 255, 255],
    "DELAY_AFTER_CAST": 8.0,        # Время ожидания поклевки после заброса (сек)
    "DELAY_AFTER_BITE": 1.5,        # Задержка после подсечки до появления шкалы удержания
    "DELAY_AFTER_DONE": 3.0,        # Задержка после улова до начала нового цикла
    "BAR_ROI_X1": 713,              # Статические координаты шкалы (X1)
    "BAR_ROI_Y1": 84,               # Статические координаты шкалы (Y1)
    "BAR_ROI_X2": 1701,             # Статические координаты шкалы (X2)
    "BAR_ROI_Y2": 115,              # Статические координаты шкалы (Y2)
    "RANDOMIZE_DELAYS": True,       # Включить рандомизацию задержек и кликов
    "RANDOM_STRENGTH": 0.15         # Сила рандомизации (процент разброса задержек)
}

def load_config():
    """Загружает настройки из файла config.json. Если файла нет, возвращает дефолтные."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Дополняем отсутствующие ключи значениями по умолчанию
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Сохраняет настройки в файл config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False
