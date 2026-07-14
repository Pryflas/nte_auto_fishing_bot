# -*- coding: utf-8 -*-
"""
Модуль конечного автомата (FSM) бота.
Управляет логикой перехода состояний рыбалки в отдельном потоке.
"""

import time
import random
import logging
import threading
import numpy as np
import mss

# Импортируем наши модули
import screen
import vision
import controller

logger = logging.getLogger("FishingBot")

# --- СОСТОЯНИЯ КОНЕЧНОГО АВТОМАТА (FSM) ---
STATE_WAITING = "WAITING"              # Ожидание начала (поиск start_fishing.png)
STATE_WAIT_BITE = "WAIT_BITE"          # Ожидание поклевки (поиск catch_fish.png)
STATE_FISHING_ACTIVE = "FISHING_ACTIVE"# Поиск шкалы мини-игры в верхней зоне (bar.png)
STATE_BALANCING = "BALANCING"          # Удержание ползунка в зеленой зоне
STATE_CLOSE_LOOT = "CLOSE_LOOT"        # Экран улова, клик ПКМ для выхода через таймер

def randomize_delay(base_value, cfg):
    """Применяет случайный джиттер к базовому таймингу, если включено в конфигурации."""
    if not cfg.get("RANDOMIZE_DELAYS", True):
        return base_value
    strength = cfg.get("RANDOM_STRENGTH", 0.15)
    jitter = base_value * strength
    return max(0.01, base_value + random.uniform(-jitter, jitter))

class FishingBot:
    def __init__(self, config_provider, gui_callbacks=None):
        """
        Инициализация бота.
        :param config_provider: функция или объект, возвращающий текущий dict конфигурации.
        :param gui_callbacks: dict с коллбеками для обновления интерфейса:
                              - 'status': func(state_string)
                              - 'log': func(message_string)
                              - 'fish_count': func(count)
                              - 'progress': func(percentage)
                              - 'preview': func(crop_img, green_mask, yellow_mask)
        """
        self.config_provider = config_provider
        self.callbacks = gui_callbacks or {}
        
        self.state = STATE_WAITING
        self.fish_count = 0
        self.running = False
        self.thread = None
        
        # Переменные таймаутов и времени
        self.active_start_time = None
        self.done_start_time = None
        self.last_click_time = 0.0
        
        # Координаты найденной шкалы
        self.bar_left = 0
        self.bar_top = 0
        self.bar_width = 0
        self.bar_height = 0
        self.lost_frames_count = 0
        
        # Флаг экстренной остановки
        self.stop_event = threading.Event()

    def log(self, message, level=logging.INFO):
        """Логирует сообщение и передает его в GUI."""
        if level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        else:
            logger.info(message)
            
        callback = self.callbacks.get("log")
        if callback:
            callback(message)

    def set_state(self, new_state):
        """Меняет состояние и оповещает GUI."""
        self.state = new_state
        self.log(f"Переход в состояние: {new_state}")
        callback = self.callbacks.get("status")
        if callback:
            callback(new_state)

    def start(self):
        """Запускает поток бота."""
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Останавливает работу бота."""
        if not self.running:
            return
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1.0)
        controller.release_all_keys()
        self.set_state("STOPPED")
        self.log("Бот остановлен.")

    def _run_loop(self):
        """Основной цикл работы бота в фоновом потоке."""
        self.log("Поток авторыбалки запущен.")
        
        # Задержка 5 секунд для переключения в окно игры
        self.set_state("START_DELAY")
        for i in range(5, 0, -1):
            if not self.running or self.stop_event.is_set():
                return
            self.log(f"[СИСТЕМА] Запуск авторыбалки через {i} сек... Переключитесь в окно игры!")
            time.sleep(1.0)
            
        if not self.running or self.stop_event.is_set():
            return
            
        self.set_state(STATE_WAITING)
        
        # Загружаем первоначальный масштаб
        cfg = self.config_provider()
        
        # Инициализируем MSS
        try:
            with mss.mss() as sct:
                # Рассчитываем геометрию захвата один раз при старте
                capture_area, abs_left, abs_top, game_w, game_h = screen.get_capture_geometry(
                    cfg["MONITOR_INDEX"], cfg["GAME_REGION"]
                )
                
                self.log(f"Запуск захвата: {game_w}x{game_h} на мониторе {cfg['MONITOR_INDEX']}.")
                
                while self.running and not self.stop_event.is_set():
                    # Перечитываем настройки на лету для реактивного управления в GUI
                    cfg = self.config_provider()
                    
                    # Захватываем BGR кадр
                    frame_bgr, _ = screen.grab_frame(sct, capture_area)
                    
                    # --- STATE: WAITING (Ожидание начала - Сразу заброс) ---
                    if self.state == STATE_WAITING:
                        self.active_start_time = None
                        self.done_start_time = None
                        
                        self.log("[ОЖИДАНИЕ] Забрасываем удочку (нажатие F)...")
                        duration = randomize_delay(cfg["KEY_PRESS_DURATION"], cfg)
                        controller.press_key('f', duration)
                        
                        delay = randomize_delay(cfg["DELAY_AFTER_CAST"], cfg)
                        self.log(f"[ОЖИДАНИЕ] Ждем поклевку по таймеру: {delay:.2f} сек (базовая: {cfg['DELAY_AFTER_CAST']:.1f} сек)...")
                        time.sleep(delay)
                        self.set_state(STATE_WAIT_BITE)
                        
                    # --- STATE: WAIT_BITE (Подсечка по таймеру) ---
                    elif self.state == STATE_WAIT_BITE:
                        self.log("[ПОКЛЕВКА] Подсекаем рыбу (нажатие F)...")
                        duration = randomize_delay(cfg["KEY_PRESS_DURATION"], cfg)
                        controller.press_key('f', duration)
                        
                        # Ждем появления шкалы мини-игры
                        delay = randomize_delay(cfg["DELAY_AFTER_BITE"], cfg)
                        self.log(f"[ПОКЛЕВКА] Ждем появление шкалы: {delay:.2f} сек (базовая: {cfg['DELAY_AFTER_BITE']:.1f} сек)...")
                        time.sleep(delay)
                        self.set_state(STATE_FISHING_ACTIVE)
                            
                    # --- STATE: FISHING_ACTIVE (Запуск шкалы по статическим координатам) ---
                    elif self.state == STATE_FISHING_ACTIVE:
                        self.bar_left = cfg.get("BAR_ROI_X1", 713)
                        self.bar_top = cfg.get("BAR_ROI_Y1", 84)
                        self.bar_width = cfg.get("BAR_ROI_X2", 1701) - self.bar_left
                        self.bar_height = cfg.get("BAR_ROI_Y2", 115) - self.bar_top
                        
                        self.log(f"[ПОИСК БАРА] Используем статические координаты: [Л: {self.bar_left}, В: {self.bar_top}, Ш: {self.bar_width}, В: {self.bar_height}].")
                        self.lost_frames_count = 0
                        self.set_state(STATE_BALANCING)
                        
                    # --- STATE: BALANCING (Удержание ползунка) ---
                    elif self.state == STATE_BALANCING:
                        # Вырезаем шкалу по статическим координатам
                        bar_crop = frame_bgr[self.bar_top : self.bar_top + self.bar_height, self.bar_left : self.bar_left + self.bar_width]
                            
                        # Сегментируем элементы шкалы
                        green_left, green_right, slider_center, g_mask, y_mask = vision.segment_bar_elements(
                            bar_crop,
                            np.array(cfg["GREEN_HSV_LOW"]), np.array(cfg["GREEN_HSV_HIGH"]),
                            np.array(cfg["YELLOW_HSV_LOW"]), np.array(cfg["YELLOW_HSV_HIGH"])
                        )
                        
                        # Передаем превью в GUI
                        preview_cb = self.callbacks.get("preview")
                        if preview_cb:
                            preview_cb(bar_crop, g_mask, y_mask)
                            
                        # Проверяем активность шкалы по наличию зеленого и желтого элементов
                        if green_left is None or slider_center is None:
                            self.lost_frames_count += 1
                            if self.lost_frames_count > 15:  # ~450мс при задержке цикла
                                self.log("[УДЕРЖАНИЕ] Шкала исчезла (ползунки не обнаружены). Завершение рыбалки.")
                                controller.release_all_keys()
                                self.set_state(STATE_CLOSE_LOOT)
                                continue
                            controller.release_all_keys()
                        else:
                            self.lost_frames_count = 0  # Сброс счетчика при успешном обнаружении
                            margin = cfg["SWEET_SPOT_MARGIN"]
                            
                            # Балансировка
                            if slider_center < (green_left + margin):
                                # Двигаем вправо
                                if cfg["CONTROL_MODE"] == "hold":
                                    controller.key_up('a')
                                    controller.key_down('d')
                                else:
                                    controller.key_up('a')
                                    cooldown = randomize_delay(cfg["CLICK_COOLDOWN"], cfg)
                                    if time.time() - self.last_click_time > cooldown:
                                        controller.key_down('d')
                                        duration = randomize_delay(cfg["CLICK_TAP_DURATION"], cfg)
                                        time.sleep(duration)
                                        controller.key_up('d')
                                        self.last_click_time = time.time()
                            elif slider_center > (green_right - margin):
                                # Двигаем влево
                                if cfg["CONTROL_MODE"] == "hold":
                                    controller.key_up('d')
                                    controller.key_down('a')
                                else:
                                    controller.key_up('d')
                                    cooldown = randomize_delay(cfg["CLICK_COOLDOWN"], cfg)
                                    if time.time() - self.last_click_time > cooldown:
                                        controller.key_down('a')
                                        duration = randomize_delay(cfg["CLICK_TAP_DURATION"], cfg)
                                        time.sleep(duration)
                                        controller.key_up('a')
                                        self.last_click_time = time.time()
                            else:
                                # Внутри зоны - отпускаем клавиши
                                controller.release_all_keys()
                            
                    # --- STATE: CLOSE_LOOT (Закрытие экрана улова) ---
                    elif self.state == STATE_CLOSE_LOOT:
                        if self.done_start_time is None:
                            self.done_start_time = time.time()
                            self.log(f"[ЗАВЕРШЕНИЕ] Рыба поймана. Ожидаем {cfg['DELAY_AFTER_DONE']:.1f} сек...")
                            
                        # Ждем окончания анимации поимки и отображения окна улова с рандомизацией
                        delay = randomize_delay(cfg["DELAY_AFTER_DONE"], cfg)
                        if time.time() - self.done_start_time >= delay:
                            self.log("[ЗАВЕРШЕНИЕ] Нажимаем клавишу ESC для закрытия интерфейса улова.")
                            duration = randomize_delay(cfg["KEY_PRESS_DURATION"], cfg)
                            controller.press_key('esc', duration)
                            
                            # Пауза для анимации закрытия меню, чтобы следующий заброс не проигнорировался
                            time.sleep(randomize_delay(1.5, cfg))
                            
                            # Инкрементируем улов
                            self.fish_count += 1
                            fish_cb = self.callbacks.get("fish_count")
                            if fish_cb:
                                fish_cb(self.fish_count)
                                
                            self.set_state(STATE_WAITING)
                        else:
                            time.sleep(0.1)
                                
                    # Пауза цикла в соответствии с частотой скриншотов (FPS)
                    fps = cfg.get("SCREENSHOT_FPS", 30)
                    base_delay = 1.0 / fps
                    actual_delay = randomize_delay(base_delay, cfg)
                    time.sleep(actual_delay)
                    
        except Exception as e:
            self.log(f"Критическая ошибка в потоке бота: {e}", level=logging.ERROR)
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.running = False
            controller.release_all_keys()
            self.log("Поток авторыбалки завершен.")
