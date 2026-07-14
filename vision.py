# -*- coding: utf-8 -*-
"""
Модуль компьютерного зрения.
Управляет загрузкой шаблонов, поиском изображений на экране и анализом цветов шкалы.
"""

import os
import cv2
import numpy as np

ASSETS_DIR = "assets"

def load_templates(scale):
    """Загружает шаблоны из папки assets (сначала ищет кастомные) и масштабирует дефолтные."""
    templates = {}
    
    # 1. start_fishing.png (Кастомный или дефолтный)
    path_custom_start = os.path.join(ASSETS_DIR, "custom_start_fishing.png")
    path_start = os.path.join(ASSETS_DIR, "start_fishing.png")
    if os.path.exists(path_custom_start):
        img_start = cv2.imread(path_custom_start, cv2.IMREAD_GRAYSCALE)
        # Кастомный шаблон НЕ масштабируется, так как он взят с родного экрана
    else:
        img_start = cv2.imread(path_start, cv2.IMREAD_GRAYSCALE)
        if img_start is None:
            raise FileNotFoundError(f"Не найден шаблон: {path_start}")
        if scale != 1.0:
            w = int(img_start.shape[1] * scale)
            h = int(img_start.shape[0] * scale)
            img_start = cv2.resize(img_start, (w, h), interpolation=cv2.INTER_AREA)
    templates["start_fishing"] = img_start
    
    # 2. bar.png (Кастомный или дефолтный)
    path_custom_bar = os.path.join(ASSETS_DIR, "custom_bar.png")
    path_bar = os.path.join(ASSETS_DIR, "bar.png")
    if os.path.exists(path_custom_bar):
        img_bar = cv2.imread(path_custom_bar)
        # Кастомный шаблон НЕ масштабируется
    else:
        img_bar = cv2.imread(path_bar)
        if img_bar is None:
            raise FileNotFoundError(f"Не найден шаблон: {path_bar}")
        if scale != 1.0:
            w = int(img_bar.shape[1] * scale)
            h = int(img_bar.shape[0] * scale)
            img_bar = cv2.resize(img_bar, (w, h), interpolation=cv2.INTER_AREA)
    templates["bar_bgr"] = img_bar
    templates["bar_gray"] = cv2.cvtColor(img_bar, cv2.COLOR_BGR2GRAY)
    
    # 3. catch_fish.png (Кастомный или дефолтный)
    path_custom_catch = os.path.join(ASSETS_DIR, "custom_catch_fish.png")
    path_catch = os.path.join(ASSETS_DIR, "catch_fish.png")
    if os.path.exists(path_custom_catch):
        img_catch = cv2.imread(path_custom_catch, cv2.IMREAD_GRAYSCALE)
        # Кастомный шаблон НЕ масштабируется
    else:
        img_catch = cv2.imread(path_catch, cv2.IMREAD_GRAYSCALE)
        if img_catch is None:
            raise FileNotFoundError(f"Не найден шаблон: {path_catch}")
        if scale != 1.0:
            w = int(img_catch.shape[1] * scale)
            h = int(img_catch.shape[0] * scale)
            img_catch = cv2.resize(img_catch, (w, h), interpolation=cv2.INTER_AREA)
    templates["catch_fish"] = img_catch
    
    # 4. done.png (Сохраняем для обратной совместимости тестов)
    path_done = os.path.join(ASSETS_DIR, "done.png")
    img_done = cv2.imread(path_done, cv2.IMREAD_GRAYSCALE)
    if img_done is not None:
        crop_done = img_done[1280:1340, 1000:1600]
        if scale != 1.0:
            w = int(crop_done.shape[1] * scale)
            h = int(crop_done.shape[0] * scale)
            crop_done = cv2.resize(crop_done, (w, h), interpolation=cv2.INTER_AREA)
        templates["done_crop"] = crop_done
    
    return templates


def match_template_on_frame(frame_gray, template, threshold, roi_coords=None):
    """
    Ищет совпадение шаблона на кадре.
    Если передан roi_coords как (y1, y2, x1, x2), поиск происходит только в этой области.
    Возвращает (score, (abs_x, abs_y)) или (0.0, None).
    """
    if roi_coords is not None:
        y1, y2, x1, x2 = roi_coords
        # Безопасное отсечение границ
        h, w = frame_gray.shape
        y1 = max(0, min(y1, h - 1))
        y2 = max(y1 + 1, min(y2, h))
        x1 = max(0, min(x1, w - 1))
        x2 = max(x1 + 1, min(x2, w))
        
        search_area = frame_gray[y1:y2, x1:x2]
        
        # Проверяем корректность размеров
        if search_area.shape[0] < template.shape[0] or search_area.shape[1] < template.shape[1]:
            return 0.0, None
            
        res = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            abs_x = max_loc[0] + x1
            abs_y = max_loc[1] + y1
            return max_val, (abs_x, abs_y)
        return max_val, None
    else:
        if frame_gray.shape[0] < template.shape[0] or frame_gray.shape[1] < template.shape[1]:
            return 0.0, None
            
        res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            return max_val, max_loc
        return max_val, None


def get_progress_percentage(crop_img, scale, blue_hsv_low, blue_hsv_high):
    """Определяет процент поимки рыбы по синему кольцу прогресса вокруг крючка."""
    hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
    
    # Центр иконки крючка относительно шаблона catch_fish в 1440p
    cx = 92.87 * scale
    cy = 95.11 * scale
    
    # Диапазон радиуса кольца прогресса
    min_r = 42 * scale
    max_r = 63 * scale
    
    blue_mask = cv2.inRange(hsv, blue_hsv_low, blue_hsv_high)
    y_indices, x_indices = np.where(blue_mask > 0)
    
    if len(x_indices) == 0:
        return 0.0
        
    dx = x_indices - cx
    dy = y_indices - cy
    distances = np.sqrt(dx**2 + dy**2)
    
    # Оставляем пиксели только в границах кольца
    ring_mask = (distances >= min_r) & (distances <= max_r)
    dx_filtered = dx[ring_mask]
    dy_filtered = dy[ring_mask]
    
    if len(dx_filtered) == 0:
        return 0.0
        
    # Считаем углы в градусах [0, 360]
    angles = np.arctan2(dy_filtered, dx_filtered) * 180 / np.pi
    angles = (angles + 360) % 360
    
    # Разбиваем круг на 36 секторов по 10 градусов
    num_bins = 36
    bin_size = 360 / num_bins
    bins = (angles / bin_size).astype(int)
    
    unique_bins = np.unique(bins)
    coverage = len(unique_bins) / num_bins
    return coverage * 100.0


def segment_bar_elements(bar_crop, green_hsv_low, green_hsv_high, yellow_hsv_low, yellow_hsv_high):
    """
    Разделяет зеленую зону (sweet spot) и желтый ползунок (slider) на шкале.
    Возвращает кортеж:
      (green_left, green_right, slider_center, green_mask, yellow_mask)
    Каждое значение может быть None, если цветной элемент не найден.
    """
    hsv_crop = cv2.cvtColor(bar_crop, cv2.COLOR_BGR2HSV)
    
    green_mask = cv2.inRange(hsv_crop, green_hsv_low, green_hsv_high)
    yellow_mask = cv2.inRange(hsv_crop, yellow_hsv_low, yellow_hsv_high)
    
    green_ys, green_xs = np.where(green_mask > 0)
    yellow_ys, yellow_xs = np.where(yellow_mask > 0)
    
    green_left = int(np.min(green_xs)) if len(green_xs) > 0 else None
    green_right = int(np.max(green_xs)) if len(green_xs) > 0 else None
    slider_center = float(np.mean(yellow_xs)) if len(yellow_xs) > 0 else None
    
    return green_left, green_right, slider_center, green_mask, yellow_mask
