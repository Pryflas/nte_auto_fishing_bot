# -*- coding: utf-8 -*-
"""
Модуль захвата экрана.
Управляет поиском мониторов и созданием скриншотов с помощью mss.
"""

import cv2
import numpy as np
import mss

def list_monitors():
    """Возвращает список доступных физических мониторов."""
    with mss.mss() as sct:
        # sct.monitors[0] - это общий виртуальный рабочий стол,
        # физические экраны начинаются с индекса 1.
        return sct.monitors[1:]

def get_monitor_info(monitor_idx):
    """Возвращает параметры указанного монитора (индекс с 1)."""
    with mss.mss() as sct:
        num_monitors = len(sct.monitors)
        if monitor_idx < num_monitors:
            return sct.monitors[monitor_idx]
        return sct.monitors[1]  # Дефолт на основной монитор

def get_capture_geometry(monitor_idx, game_region=None):
    """
    Рассчитывает геометрию захвата экрана.
    Если game_region = [x, y, w, h], рассчитывает координаты относительно монитора.
    Возвращает dict для mss, а также абсолютные left и top.
    """
    monitor = get_monitor_info(monitor_idx)
    
    if game_region is not None:
        gx, gy, gw, gh = game_region
        capture_area = {
            "left": monitor["left"] + gx,
            "top": monitor["top"] + gy,
            "width": gw,
            "height": gh
        }
        abs_left = monitor["left"] + gx
        abs_top = monitor["top"] + gy
        w_ret, h_ret = gw, gh
    else:
        capture_area = monitor
        abs_left = monitor["left"]
        abs_top = monitor["top"]
        w_ret = monitor["width"]
        h_ret = monitor["height"]
        
    return capture_area, abs_left, abs_top, w_ret, h_ret

def grab_frame(sct, capture_area):
    """
    Выполняет захват кадра.
    Возвращает кадр в формате BGR и Grayscale.
    """
    sct_img = sct.grab(capture_area)
    frame = np.array(sct_img)
    # MSS возвращает BGRA. Конвертируем в BGR и Gray
    frame_bgr = frame[:, :, :3].copy()  # Быстрее, чем cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return frame_bgr, frame_gray
