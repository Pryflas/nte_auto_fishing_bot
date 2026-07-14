# -*- coding: utf-8 -*-
"""
Модуль графического интерфейса управления (GUI) автокликером.
Построен на tkinter. Обеспечивает запуск/остановку бота, калибровку цветов
и порогов CV в реальном времени с выводом превью.
"""

import sys
import os
import time
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import ctypes
from ctypes import wintypes

# Импортируем наши модули
import config
from bot import FishingBot
import screen
import vision

class FishingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NTE Auto-Fish Калибровочная Панель")
        self.root.geometry("1180x720")
        self.root.configure(bg="#1c1c1c")
        
        # Делаем адаптивный грид
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)
        
        # Стилизация ttk
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("TNotebook", background="#1c1c1c", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#2b2b2b", foreground="#bbbbbb", padding=[15, 5], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[("selected", "#00adb5")], foreground=[("selected", "#ffffff")])
        
        # Загружаем текущие настройки
        self.cfg = config.load_config()
        
        # Ссылка на объект бота
        self.bot = None
        
        # Очередь кадров для превью (поток бота кладет, поток GUI забирает)
        self.preview_queue = queue.Queue(maxsize=1)
        
        # Переменные захвата и калибровки кастомных шаблонов
        self.captured_frame = None
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None
        self.rect_id = None
        self.screenshot_scale_x = 1.0
        self.screenshot_scale_y = 1.0
        
        # Создаем элементы интерфейса
        self._create_widgets()
        
        # Инициализируем глобальный поток горячей клавиши F12 (Экстренный стоп)
        self._start_global_hotkey_listener()
        
        # Запускаем таймер проверки очереди кадров
        self.root.after(30, self._check_preview_queue)
        
        # Выводим приветствие
        self.write_log("Добро пожаловать в панель управления авторыбалкой NTE!")
        self.write_log("Запустите игру, настройте параметры и нажмите 'СТАРТ'.")
        self.write_log("Горячая клавиша F12 остановит бота из любого окна.")

    def _create_widgets(self):
        # ------------------------------------------------------------
        # ЛЕВАЯ ПАНЕЛЬ: Управление, Статус и Логи
        # ------------------------------------------------------------
        left_frame = tk.Frame(self.root, bg="#212121", width=380, bd=0)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_propagate(False)
        left_frame.columnconfigure(0, weight=1)
        
        # Заголовок
        lbl_title = tk.Label(left_frame, text="NTE AUTO-FISH BOT", fg="#00adb5", bg="#212121", font=("Segoe UI", 16, "bold"))
        lbl_title.grid(row=0, column=0, pady=15)
        
        # Статусы и счетчик
        status_frame = tk.Frame(left_frame, bg="#2d2d2d", bd=1, relief="flat")
        status_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        
        # Текущее состояние
        tk.Label(status_frame, text="Статус бота:", fg="#888888", bg="#2d2d2d", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.lbl_status = tk.Label(status_frame, text="ОСТАНОВЛЕН", fg="#ff1744", bg="#2d2d2d", font=("Segoe UI", 10, "bold"))
        self.lbl_status.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        
        # Счетчик рыбы
        tk.Label(status_frame, text="Поймано рыбы:", fg="#888888", bg="#2d2d2d", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.lbl_count = tk.Label(status_frame, text="0", fg="#00e676", bg="#2d2d2d", font=("Segoe UI", 14, "bold"))
        self.lbl_count.grid(row=1, column=1, sticky="e", padx=10, pady=2)
        

        
        # Кнопки Старт / Стоп
        btn_frame = tk.Frame(left_frame, bg="#212121")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=10)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        self.btn_start = tk.Button(btn_frame, text="СТАРТ", bg="#00e676", fg="#121212", font=("Segoe UI", 11, "bold"),
                                   activebackground="#00c853", activeforeground="#ffffff", bd=0, height=2,
                                   command=self.start_bot)
        self.btn_start.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_stop = tk.Button(btn_frame, text="СТОП (F12)", bg="#ff1744", fg="#ffffff", font=("Segoe UI", 11, "bold"),
                                  activebackground="#d50000", activeforeground="#ffffff", bd=0, height=2,
                                  command=self.stop_bot, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Консоль логов
        tk.Label(left_frame, text="Лог работы:", fg="#aaaaaa", bg="#212121", font=("Segoe UI", 9)).grid(row=5, column=0, sticky="w", padx=15, pady=(10, 2))
        
        log_frame = tk.Frame(left_frame, bg="#121212")
        log_frame.grid(row=6, column=0, sticky="nsew", padx=15, pady=(0, 15))
        left_frame.rowconfigure(6, weight=1)
        
        self.log_text = tk.Text(log_frame, bg="#121212", fg="#dcdcdc", wrap="word", font=("Consolas", 9), state="disabled", bd=0, highlightthickness=0)
        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Подсветка ошибок/предупреждений в логе
        self.log_text.tag_config("WARNING", foreground="#ffb300")
        self.log_text.tag_config("ERROR", foreground="#ff1744")
        self.log_text.tag_config("SUCCESS", foreground="#00e676")
        
        # ------------------------------------------------------------
        # ПРАВАЯ ПАНЕЛЬ: Вкладки калибровки и превью
        # ------------------------------------------------------------
        right_frame = tk.Frame(self.root, bg="#1c1c1c")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=0) # для превью
        right_frame.columnconfigure(0, weight=1)
        
        # Создаем Notebook (Вкладки)
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Инициализируем страницы вкладок
        self._setup_tab_general()
        self._setup_tab_hsv()
        self._setup_tab_template_capture()
        
        # Панель Визуального Превью (внизу справа)
        preview_panel = tk.Frame(right_frame, bg="#252525", bd=1, relief="flat")
        preview_panel.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        preview_panel.columnconfigure(0, weight=1)
        
        # 1. Оригинальный кадр
        tk.Label(preview_panel, text="Оригинальный кадр шкалы (Кадр):", fg="#00adb5", bg="#252525", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(5, 1))
        self.canvas_raw = tk.Canvas(preview_panel, width=680, height=40, bg="#121212", highlightthickness=1, highlightbackground="#3d3d3d")
        self.canvas_raw.grid(row=1, column=0, padx=15, pady=(0, 5))
        
        # 2. Зеленая маска
        tk.Label(preview_panel, text="Фильтр зеленой зоны (Sweet Spot):", fg="#00e676", bg="#252525", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", padx=15, pady=(2, 1))
        self.canvas_green = tk.Canvas(preview_panel, width=680, height=40, bg="#121212", highlightthickness=1, highlightbackground="#3d3d3d")
        self.canvas_green.grid(row=3, column=0, padx=15, pady=(0, 5))
        
        # 3. Желтая маска
        tk.Label(preview_panel, text="Фильтр желтого ползунка (Slider):", fg="#ffb300", bg="#252525", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", padx=15, pady=(2, 1))
        self.canvas_yellow = tk.Canvas(preview_panel, width=680, height=40, bg="#121212", highlightthickness=1, highlightbackground="#3d3d3d")
        self.canvas_yellow.grid(row=5, column=0, padx=15, pady=(0, 10))
        
        self._draw_no_signal()

    def _setup_tab_general(self):
        tab = tk.Frame(self.notebook, bg="#252525")
        self.notebook.add(tab, text=" Основные настройки ")
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        
        # Левая колонка - Экраны и Захват
        frame_left = tk.LabelFrame(tab, text="Настройки захвата и экрана", fg="#00adb5", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        frame_left.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # Монитор
        tk.Label(frame_left, text="Номер монитора:", fg="#cccccc", bg="#252525").grid(row=0, column=0, sticky="w", pady=5)
        self.var_monitor = tk.IntVar(value=self.cfg["MONITOR_INDEX"])
        # Считываем количество экранов
        monitors_list = screen.list_monitors()
        options = [i+1 for i in range(len(monitors_list))] if monitors_list else [1]
        opt_monitor = ttk.OptionMenu(frame_left, self.var_monitor, self.cfg["MONITOR_INDEX"], *options, command=self._on_general_change)
        opt_monitor.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Полноэкранный режим
        self.var_fullscreen = tk.BooleanVar(value=(self.cfg["GAME_REGION"] is None))
        chk_full = tk.Checkbutton(frame_left, text="Полноэкранный режим (захват всего экрана)", variable=self.var_fullscreen,
                                  bg="#252525", fg="#cccccc", selectcolor="#1c1c1c", activebackground="#252525", activeforeground="#ffffff",
                                  command=self._toggle_fullscreen_inputs)
        chk_full.grid(row=1, column=0, columnspan=2, sticky="w", pady=8)
        
        # Координаты окна (если не полный экран)
        self.frame_coords = tk.Frame(frame_left, bg="#252525")
        self.frame_coords.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        tk.Label(self.frame_coords, text="Координаты X, Y:", fg="#999999", bg="#252525").grid(row=0, column=0, sticky="w")
        self.ent_x = tk.Entry(self.frame_coords, bg="#333333", fg="#ffffff", bd=0, width=5, justify="center")
        self.ent_x.grid(row=0, column=1, padx=5)
        self.ent_y = tk.Entry(self.frame_coords, bg="#333333", fg="#ffffff", bd=0, width=5, justify="center")
        self.ent_y.grid(row=0, column=2, padx=5)
        
        tk.Label(self.frame_coords, text="Ширина x Высота:", fg="#999999", bg="#252525").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_w = tk.Entry(self.frame_coords, bg="#333333", fg="#ffffff", bd=0, width=5, justify="center")
        self.ent_w.grid(row=1, column=1, padx=5, pady=5)
        self.ent_h = tk.Entry(self.frame_coords, bg="#333333", fg="#ffffff", bd=0, width=5, justify="center")
        self.ent_h.grid(row=1, column=2, padx=5, pady=5)
        
        # Заполняем координаты оконного режима, если они сохранены
        if self.cfg["GAME_REGION"] is not None:
            gx, gy, gw, gh = self.cfg["GAME_REGION"]
            self.ent_x.insert(0, str(gx))
            self.ent_y.insert(0, str(gy))
            self.ent_w.insert(0, str(gw))
            self.ent_h.insert(0, str(gh))
        else:
            self.ent_x.insert(0, "0")
            self.ent_y.insert(0, "0")
            self.ent_w.insert(0, "1920")
            self.ent_h.insert(0, "1080")


        
        # Правая колонка - Клики, Задержки
        frame_right = tk.LabelFrame(tab, text="Настройки задержек и клавиш", fg="#00adb5", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        frame_right.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        # Режим управления
        tk.Label(frame_right, text="Режим удержания:", fg="#cccccc", bg="#252525").grid(row=0, column=0, sticky="w", pady=5)
        self.var_ctrl_mode = tk.StringVar(value=self.cfg["CONTROL_MODE"])
        opt_ctrl = ttk.OptionMenu(frame_right, self.var_ctrl_mode, self.cfg["CONTROL_MODE"], "hold", "click", command=self._on_general_change)
        opt_ctrl.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Запас безопасностиSweet Spot Margin
        tk.Label(frame_right, text="Отступ безопасности (px):", fg="#cccccc", bg="#252525").grid(row=1, column=0, sticky="w", pady=5)
        self.var_margin = tk.IntVar(value=self.cfg["SWEET_SPOT_MARGIN"])
        sld_margin = tk.Scale(frame_right, from_=0, to_=20, orient="horizontal", variable=self.var_margin,
                              bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_general_change)
        sld_margin.grid(row=1, column=1, sticky="ew", padx=10)
        
        # Задержка зажатия клавиши F
        tk.Label(frame_right, text="Длительность нажатия F (сек):", fg="#cccccc", bg="#252525").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_key_f = tk.Entry(frame_right, bg="#333333", fg="#ffffff", bd=0, width=8, justify="center")
        self.ent_key_f.insert(0, str(self.cfg["KEY_PRESS_DURATION"]))
        self.ent_key_f.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.ent_key_f.bind("<FocusOut>", self._on_general_change)
        
        # Частота скриншотов (SCREENSHOT_FPS)
        tk.Label(frame_right, text="Скриншотов в сек (FPS):", fg="#cccccc", bg="#252525").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_fps = tk.Entry(frame_right, bg="#333333", fg="#ffffff", bd=0, width=8, justify="center")
        self.ent_fps.insert(0, str(self.cfg.get("SCREENSHOT_FPS", 30)))
        self.ent_fps.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        self.ent_fps.bind("<FocusOut>", self._on_general_change)
        
        # Задержка после заброса (DELAY_AFTER_CAST)
        tk.Label(frame_right, text="Задержка после заброса (сек):", fg="#cccccc", bg="#252525").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_delay_cast = tk.Entry(frame_right, bg="#333333", fg="#ffffff", bd=0, width=8, justify="center")
        self.ent_delay_cast.insert(0, str(self.cfg["DELAY_AFTER_CAST"]))
        self.ent_delay_cast.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        self.ent_delay_cast.bind("<FocusOut>", self._on_general_change)
        
        # Задержка после подсечки (DELAY_AFTER_BITE)
        tk.Label(frame_right, text="Задержка после подсечки (сек):", fg="#cccccc", bg="#252525").grid(row=5, column=0, sticky="w", pady=5)
        self.ent_delay_bite = tk.Entry(frame_right, bg="#333333", fg="#ffffff", bd=0, width=8, justify="center")
        self.ent_delay_bite.insert(0, str(self.cfg["DELAY_AFTER_BITE"]))
        self.ent_delay_bite.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        self.ent_delay_bite.bind("<FocusOut>", self._on_general_change)
        
        # Задержка после улова (DELAY_AFTER_DONE)
        tk.Label(frame_right, text="Задержка после улова (сек):", fg="#cccccc", bg="#252525").grid(row=6, column=0, sticky="w", pady=5)
        self.ent_delay_done = tk.Entry(frame_right, bg="#333333", fg="#ffffff", bd=0, width=8, justify="center")
        self.ent_delay_done.insert(0, str(self.cfg["DELAY_AFTER_DONE"]))
        self.ent_delay_done.grid(row=6, column=1, sticky="w", padx=10, pady=5)
        self.ent_delay_done.bind("<FocusOut>", self._on_general_change)
        
        # Случайные задержки (RANDOMIZE_DELAYS)
        self.var_randomize = tk.BooleanVar(value=self.cfg.get("RANDOMIZE_DELAYS", True))
        tk.Checkbutton(frame_right, text="Рандомизация задержек (Анти-чит)", variable=self.var_randomize,
                       bg="#252525", fg="#cccccc", selectcolor="#1c1c1c", activebackground="#252525", activeforeground="#ffffff",
                       command=self._on_general_change).grid(row=7, column=0, columnspan=2, sticky="w", pady=5)
                       
        # Разброс задержек (RANDOM_STRENGTH)
        tk.Label(frame_right, text="Разброс задержек (%):", fg="#cccccc", bg="#252525").grid(row=8, column=0, sticky="w", pady=5)
        self.var_random_strength = tk.IntVar(value=int(self.cfg.get("RANDOM_STRENGTH", 0.15) * 100))
        self.scale_random_strength = tk.Scale(frame_right, from_=0, to_=50, orient="horizontal", variable=self.var_random_strength,
                                              bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0,
                                              command=self._on_general_change)
        self.scale_random_strength.grid(row=8, column=1, sticky="ew", padx=10, pady=5)
        
        # Синхронизируем состояние полей ввода с чекбоксом в конце инициализации вкладки
        self._toggle_fullscreen_inputs()
        
        # Сохранение ручных изменений
        btn_save = tk.Button(tab, text="Сохранить настройки конфигурации", bg="#00adb5", fg="#ffffff",
                             font=("Segoe UI", 10, "bold"), bd=0, height=2, command=self.save_settings)
        btn_save.grid(row=1, column=0, columnspan=2, pady=10)



    def _setup_tab_hsv(self):
        tab = tk.Frame(self.notebook, bg="#252525")
        self.notebook.add(tab, text=" Калибровка цвета ")
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        
        # ----------------------------------------
        # ЗЕЛЕНАЯ ЗОНА (Sweet Spot)
        # ----------------------------------------
        green_frame = tk.LabelFrame(tab, text="Зеленая зона (Sweet Spot)", fg="#00e676", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        green_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        green_frame.columnconfigure(1, weight=1)
        
        # Мин H, S, V
        tk.Label(green_frame, text="Мин Hue:", fg="#cccccc", bg="#252525").grid(row=0, column=0, sticky="w")
        self.var_g_h_min = tk.IntVar(value=self.cfg["GREEN_HSV_LOW"][0])
        tk.Scale(green_frame, from_=0, to_=180, orient="horizontal", variable=self.var_g_h_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=0, column=1, sticky="ew", padx=5)
        
        tk.Label(green_frame, text="Мин Saturation:", fg="#cccccc", bg="#252525").grid(row=1, column=0, sticky="w")
        self.var_g_s_min = tk.IntVar(value=self.cfg["GREEN_HSV_LOW"][1])
        tk.Scale(green_frame, from_=0, to_=255, orient="horizontal", variable=self.var_g_s_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=1, column=1, sticky="ew", padx=5)
        
        tk.Label(green_frame, text="Мин Value:", fg="#cccccc", bg="#252525").grid(row=2, column=0, sticky="w")
        self.var_g_v_min = tk.IntVar(value=self.cfg["GREEN_HSV_LOW"][2])
        tk.Scale(green_frame, from_=0, to_=255, orient="horizontal", variable=self.var_g_v_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=2, column=1, sticky="ew", padx=5)
        
        # Макс H, S, V
        tk.Label(green_frame, text="Макс Hue:", fg="#cccccc", bg="#252525").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.var_g_h_max = tk.IntVar(value=self.cfg["GREEN_HSV_HIGH"][0])
        tk.Scale(green_frame, from_=0, to_=180, orient="horizontal", variable=self.var_g_h_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=3, column=1, sticky="ew", padx=5, pady=(10, 0))
        
        tk.Label(green_frame, text="Макс Saturation:", fg="#cccccc", bg="#252525").grid(row=4, column=0, sticky="w")
        self.var_g_s_max = tk.IntVar(value=self.cfg["GREEN_HSV_HIGH"][1])
        tk.Scale(green_frame, from_=0, to_=255, orient="horizontal", variable=self.var_g_s_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=4, column=1, sticky="ew", padx=5)
        
        tk.Label(green_frame, text="Макс Value:", fg="#cccccc", bg="#252525").grid(row=5, column=0, sticky="w")
        self.var_g_v_max = tk.IntVar(value=self.cfg["GREEN_HSV_HIGH"][2])
        tk.Scale(green_frame, from_=0, to_=255, orient="horizontal", variable=self.var_g_v_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=5, column=1, sticky="ew", padx=5)
        
        # ----------------------------------------
        # ЖЕЛТЫЙ ПОЛЗУНОК (Slider)
        # ----------------------------------------
        yellow_frame = tk.LabelFrame(tab, text="Желтый ползунок (Slider)", fg="#ffb300", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        yellow_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        yellow_frame.columnconfigure(1, weight=1)
        
        # Мин H, S, V
        tk.Label(yellow_frame, text="Мин Hue:", fg="#cccccc", bg="#252525").grid(row=0, column=0, sticky="w")
        self.var_y_h_min = tk.IntVar(value=self.cfg["YELLOW_HSV_LOW"][0])
        tk.Scale(yellow_frame, from_=0, to_=180, orient="horizontal", variable=self.var_y_h_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=0, column=1, sticky="ew", padx=5)
        
        tk.Label(yellow_frame, text="Мин Saturation:", fg="#cccccc", bg="#252525").grid(row=1, column=0, sticky="w")
        self.var_y_s_min = tk.IntVar(value=self.cfg["YELLOW_HSV_LOW"][1])
        tk.Scale(yellow_frame, from_=0, to_=255, orient="horizontal", variable=self.var_y_s_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=1, column=1, sticky="ew", padx=5)
        
        tk.Label(yellow_frame, text="Мин Value:", fg="#cccccc", bg="#252525").grid(row=2, column=0, sticky="w")
        self.var_y_v_min = tk.IntVar(value=self.cfg["YELLOW_HSV_LOW"][2])
        tk.Scale(yellow_frame, from_=0, to_=255, orient="horizontal", variable=self.var_y_v_min, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=2, column=1, sticky="ew", padx=5)
        
        # Макс H, S, V
        tk.Label(yellow_frame, text="Макс Hue:", fg="#cccccc", bg="#252525").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.var_y_h_max = tk.IntVar(value=self.cfg["YELLOW_HSV_HIGH"][0])
        tk.Scale(yellow_frame, from_=0, to_=180, orient="horizontal", variable=self.var_y_h_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=3, column=1, sticky="ew", padx=5, pady=(10, 0))
        
        tk.Label(yellow_frame, text="Макс Saturation:", fg="#cccccc", bg="#252525").grid(row=4, column=0, sticky="w")
        self.var_y_s_max = tk.IntVar(value=self.cfg["YELLOW_HSV_HIGH"][1])
        tk.Scale(yellow_frame, from_=0, to_=255, orient="horizontal", variable=self.var_y_s_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=4, column=1, sticky="ew", padx=5)
        
        tk.Label(yellow_frame, text="Макс Value:", fg="#cccccc", bg="#252525").grid(row=5, column=0, sticky="w")
        self.var_y_v_max = tk.IntVar(value=self.cfg["YELLOW_HSV_HIGH"][2])
        tk.Scale(yellow_frame, from_=0, to_=255, orient="horizontal", variable=self.var_y_v_max, bg="#252525", fg="#ffffff", troughcolor="#3d3d3d", highlightthickness=0, bd=0, command=self._on_hsv_change).grid(row=5, column=1, sticky="ew", padx=5)

    def _toggle_fullscreen_inputs(self):
        """Включает/отключает поля ввода координат в зависимости от чекбокса полного экрана."""
        state_fs = "disabled" if self.var_fullscreen.get() else "normal"
        self.ent_x.configure(state=state_fs)
        self.ent_y.configure(state=state_fs)
        self.ent_w.configure(state=state_fs)
        self.ent_h.configure(state=state_fs)
        
        self._on_general_change()

    def _on_general_change(self, *args):
        """Срабатывает при изменении параметров на первой вкладке."""
        self.cfg["MONITOR_INDEX"] = self.var_monitor.get()
        self.cfg["CONTROL_MODE"] = self.var_ctrl_mode.get()
        self.cfg["SWEET_SPOT_MARGIN"] = self.var_margin.get()
        
        # Проверяем и сохраняем GAME_REGION
        if self.var_fullscreen.get():
            self.cfg["GAME_REGION"] = None
        else:
            try:
                x = int(self.ent_x.get())
                y = int(self.ent_y.get())
                w = int(self.ent_w.get())
                h = int(self.ent_h.get())
                self.cfg["GAME_REGION"] = [x, y, w, h]
            except ValueError:
                pass # Игнорируем ошибки при частичном вводе
                
        # Проверяем и сохраняем числовые поля
        try:
            self.cfg["KEY_PRESS_DURATION"] = float(self.ent_key_f.get())
        except ValueError:
            pass
        try:
            self.cfg["SCREENSHOT_FPS"] = int(self.ent_fps.get())
        except ValueError:
            pass
        try:
            self.cfg["DELAY_AFTER_CAST"] = float(self.ent_delay_cast.get())
        except ValueError:
            pass
        try:
            self.cfg["DELAY_AFTER_BITE"] = float(self.ent_delay_bite.get())
        except ValueError:
            pass
        try:
            self.cfg["DELAY_AFTER_DONE"] = float(self.ent_delay_done.get())
        except ValueError:
            pass
        try:
            self.cfg["RANDOMIZE_DELAYS"] = self.var_randomize.get()
            self.cfg["RANDOM_STRENGTH"] = self.var_random_strength.get() / 100.0
        except Exception:
            pass



    def _on_hsv_change(self, *args):
        """Срабатывает при изменении значений HSV."""
        self.cfg["GREEN_HSV_LOW"] = [
            self.var_g_h_min.get(),
            self.var_g_s_min.get(),
            self.var_g_v_min.get()
        ]
        self.cfg["GREEN_HSV_HIGH"] = [
            self.var_g_h_max.get(),
            self.var_g_s_max.get(),
            self.var_g_v_max.get()
        ]
        self.cfg["YELLOW_HSV_LOW"] = [
            self.var_y_h_min.get(),
            self.var_y_s_min.get(),
            self.var_y_v_min.get()
        ]
        self.cfg["YELLOW_HSV_HIGH"] = [
            self.var_y_h_max.get(),
            self.var_y_s_max.get(),
            self.var_y_v_max.get()
        ]
        self.update_hsv_preview_from_screenshot()

    def save_settings(self):
        """Записывает текущую конфигурацию на диск в config.json."""
        self._on_general_change() # Финальное считывание текстовых полей
        if config.save_config(self.cfg):
            self.write_log("Конфигурация успешно сохранена на диск в config.json.", "SUCCESS")
        else:
            self.write_log("Ошибка при сохранении конфигурации!", "ERROR")

    # --- УПРАВЛЕНИЕ ПОТОКОМ БОТА ---

    def start_bot(self):
        """Запуск логики автоматической ловли рыбы."""
        if self.bot and self.bot.running:
            return
            
        # Обновляем конфиг перед стартом
        self._on_general_change()
        
        self.write_log("Запуск бота...", "SUCCESS")
        
        # Задаем коллбеки от потока к графическому окну
        callbacks = {
            "status": self.on_bot_status,
            "log": self.on_bot_log,
            "fish_count": self.on_bot_fish_count,
            "preview": self.on_bot_preview
        }
        
        self.bot = FishingBot(lambda: self.cfg, callbacks)
        self.bot.start()
        
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

    def stop_bot(self):
        """Остановка потока авторыбалки."""
        if not self.bot or not self.bot.running:
            return
            
        self.write_log("Инициирована остановка бота...", "WARNING")
        self.bot.stop()
        
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._draw_no_signal()

    def on_bot_status(self, state):
        """Коллбек: обновление строки состояния."""
        fg_colors = {
            "START_DELAY": "#ffb300",
            "WAITING": "#00adb5",
            "WAIT_BITE": "#ffb300",
            "FISHING_ACTIVE": "#00e676",
            "BALANCING": "#00e676",
            "DONE": "#d500f9",
            "CLOSE_LOOT": "#d500f9",
            "STOPPED": "#ff1744"
        }
        ru_states = {
            "START_DELAY": "ПОДГОТОВКА (5 сек)",
            "WAITING": "ОЖИДАНИЕ КРЮЧКА",
            "WAIT_BITE": "ОЖИДАНИЕ ПОКЛЕВКИ",
            "FISHING_ACTIVE": "ПОИСК БАРА",
            "BALANCING": "УДЕРЖАНИЕ",
            "DONE": "ЭКРАН УЛОВА",
            "CLOSE_LOOT": "ЗАКРЫТИЕ УЛОВА",
            "STOPPED": "ОСТАНОВЛЕН"
        }
        
        color = fg_colors.get(state, "#bbbbbb")
        text = ru_states.get(state, state)
        
        self.lbl_status.configure(text=text, fg=color)
        
        # Обновляем превью-заглушку в зависимости от состояния
        if state == "STOPPED":
            self._draw_no_signal()
        elif state != "BALANCING":
            self._draw_waiting_for_game()

    def on_bot_log(self, msg):
        """Коллбек: вывод лога из потока."""
        self.write_log(msg)

    def on_bot_fish_count(self, count):
        """Коллбек: обновление счетчика улова."""
        self.lbl_count.configure(text=str(count))



    def on_bot_preview(self, crop_img, green_mask, yellow_mask):
        """Коллбек: прием кадров с OpenCV и добавление в очередь для отрисовки."""
        try:
            self.preview_queue.put_nowait((crop_img.copy(), green_mask.copy(), yellow_mask.copy()))
        except queue.Full:
            pass

    # --- ОТРИСОВКА И ПРЕВЬЮ ---

    def _check_preview_queue(self):
        """Опрашивает очередь кадров от потока бота и перерисовывает Canvas."""
        try:
            crop_img, g_mask, y_mask = self.preview_queue.get_nowait()
            
            # Подготавливаем изображения
            img_raw = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
            img_green = cv2.cvtColor(g_mask, cv2.COLOR_GRAY2RGB)
            img_yellow = cv2.cvtColor(y_mask, cv2.COLOR_GRAY2RGB)
            
            for canvas, img in [
                (self.canvas_raw, img_raw),
                (self.canvas_green, img_green),
                (self.canvas_yellow, img_yellow)
            ]:
                # Масштабируем до размеров Canvas (680x40)
                display_img = cv2.resize(img, (680, 40), interpolation=cv2.INTER_NEAREST)
                img_pil = Image.fromarray(display_img)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                
                canvas.delete("all")
                canvas.image = img_tk
                canvas.create_image(0, 0, anchor="nw", image=img_tk)
                
        except queue.Empty:
            pass
            
        # Зацикливаем проверку
        self.root.after(30, self._check_preview_queue)

    def _draw_no_signal(self):
        """Рисует заглушку 'НЕТ СИГНАЛА' на всех Canvas."""
        for canvas, text, color in [
            (self.canvas_raw, "НЕТ СИГНАЛА (ЗАПУСТИТЕ БОТА)", "#555555"),
            (self.canvas_green, "НЕТ СИГНАЛА", "#444444"),
            (self.canvas_yellow, "НЕТ СИГНАЛА", "#444444")
        ]:
            canvas.delete("all")
            canvas.create_rectangle(0, 0, 680, 40, fill="#121212", outline="#3d3d3d")
            canvas.create_text(340, 20, text=text, fill=color, font=("Segoe UI", 10, "bold"))

    def _draw_waiting_for_game(self):
        """Рисует заглушку 'ОЖИДАНИЕ МИНИ-ИГРЫ' на всех Canvas."""
        for canvas, text, color in [
            (self.canvas_raw, "ОЖИДАНИЕ МИНИ-ИГРЫ (ИДЕТ ПОИСК ШКАЛЫ...)", "#00adb5"),
            (self.canvas_green, "ОЖИДАНИЕ ШКАЛЫ...", "#444444"),
            (self.canvas_yellow, "ОЖИДАНИЕ ШКАЛЫ...", "#444444")
        ]:
            canvas.delete("all")
            canvas.create_rectangle(0, 0, 680, 40, fill="#121212", outline="#3d3d3d")
            canvas.create_text(340, 20, text=text, fill=color, font=("Segoe UI", 10, "bold"))

    def write_log(self, text, tag=None):
        """Пишет строку в текстовую консоль с временной меткой."""
        self.log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {text}\n"
        
        # Определяем теги для раскраски
        line_tag = tag
        if line_tag is None:
            if "[ПРЕДУПРЕЖДЕНИЕ]" in text or "Warning" in text:
                line_tag = "WARNING"
            elif "[ОШИБКА]" in text or "Ошибка" in text or "Error" in text:
                line_tag = "ERROR"
            elif "Успешно" in text or "НАЙДЕНА" in text or "подтвержден" in text:
                line_tag = "SUCCESS"
                
        if line_tag:
            self.log_text.insert("end", log_line, line_tag)
        else:
            self.log_text.insert("end", log_line)
            
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # --- ГЛОБАЛЬНАЯ ГОРЯЧАЯ КЛАВИША F12 ---

    def _start_global_hotkey_listener(self):
        """Запускает фоновый поток прослушивания глобального нажатия F12 на Windows."""
        def listener():
            user32 = ctypes.windll.user32
            # Уникальный ID хоткея
            HOTKEY_ID = 1999
            # Код клавиши F12 = 0x7B. Без модификаторов = 0
            if user32.RegisterHotKey(None, HOTKEY_ID, 0, 0x7B):
                try:
                    msg = wintypes.MSG()
                    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312:  # WM_HOTKEY
                            if msg.wParam == HOTKEY_ID:
                                # Вызов через root.after, чтобы безопасно остановить из главного потока
                                self.root.after(0, self._on_emergency_stop)
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                finally:
                    user32.UnregisterHotKey(None, HOTKEY_ID)
                    
        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def _on_emergency_stop(self):
        """Вызывается при глобальном нажатии F12 для экстренной остановки."""
        if self.bot and self.bot.running:
            self.write_log("⚠️ Сработал ЭКСТРЕННЫЙ СТОП (клавиша F12)! Отключение автоматики...", "ERROR")
            self.stop_bot()
            messagebox.showwarning("Экстренная остановка", "Бот принудительно остановлен горячей клавишей F12.\nВсе эмулируемые клавиши сброшены.")

    def _setup_tab_template_capture(self):
        """Создает вкладку кастомного захвата шаблонов."""
        tab = tk.Frame(self.notebook, bg="#252525")
        self.notebook.add(tab, text=" Захват шаблонов ")
        
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=3) # левая колонка для скриншота
        tab.columnconfigure(1, weight=1) # правая колонка для управления
        
        # Левая часть: скриншот
        frame_screen = tk.LabelFrame(tab, text=" Снимок экрана монитора ", fg="#00adb5", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        frame_screen.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        frame_screen.rowconfigure(0, weight=1)
        frame_screen.columnconfigure(0, weight=1)
        
        # Холст для скриншота (640x360)
        self.canvas_screenshot = tk.Canvas(frame_screen, width=640, height=360, bg="#121212", highlightthickness=1, highlightbackground="#3d3d3d", cursor="cross")
        self.canvas_screenshot.grid(row=0, column=0, sticky="nsew")
        
        # Привязываем мышь для выделения рамки
        self.canvas_screenshot.bind("<ButtonPress-1>", self._on_crop_press)
        self.canvas_screenshot.bind("<B1-Motion>", self._on_crop_drag)
        self.canvas_screenshot.bind("<ButtonRelease-1>", self._on_crop_release)
        
        # Правая часть: управление и превью выделения
        frame_ctrl = tk.LabelFrame(tab, text=" Управление шаблонами ", fg="#00adb5", bg="#252525", font=("Segoe UI", 10, "bold"), bd=1, relief="flat", padx=10, pady=10)
        frame_ctrl.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        # Превью обрезки
        tk.Label(frame_ctrl, text="Выделенная область:", fg="#cccccc", bg="#252525").pack(pady=(10, 2))
        self.canvas_crop_preview = tk.Canvas(frame_ctrl, width=150, height=150, bg="#121212", highlightthickness=1, highlightbackground="#3d3d3d")
        self.canvas_crop_preview.pack(pady=5)
        
        # Кнопка снимка
        btn_capture = tk.Button(frame_ctrl, text="📸 Сделать снимок экрана", bg="#00adb5", fg="#ffffff", font=("Segoe UI", 10, "bold"), bd=0, height=2, command=self.capture_screen_for_templates)
        btn_capture.pack(fill="x", padx=10, pady=15)
        
        # Кнопки сохранения шаблонов
        tk.Label(frame_ctrl, text="Сохранить шаблон как:", fg="#aaaaaa", bg="#252525", font=("Segoe UI", 9)).pack(pady=(10, 2))
        
        btn_save_bar = tk.Button(frame_ctrl, text="Шкала рыбалки (Bar)", bg="#2b2b2b", fg="#00e676", activebackground="#00e676", activeforeground="#ffffff", font=("Segoe UI", 9, "bold"), bd=1, relief="solid", height=2, command=lambda: self.save_custom_template("bar"))
        btn_save_bar.pack(fill="x", padx=10, pady=5)

    def _on_crop_press(self, event):
        if not hasattr(self, 'captured_frame') or self.captured_frame is None:
            self.write_log("Сначала сделайте снимок экрана!", "WARNING")
            return
            
        self.crop_start_x = event.x
        self.crop_start_y = event.y
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        
        if hasattr(self, 'rect_id') and self.rect_id:
            self.canvas_screenshot.delete(self.rect_id)
        self.rect_id = self.canvas_screenshot.create_rectangle(self.crop_start_x, self.crop_start_y, self.crop_start_x, self.crop_start_y, outline="#00adb5", width=2)

    def _on_crop_drag(self, event):
        if not hasattr(self, 'captured_frame') or self.captured_frame is None:
            return
            
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        self.canvas_screenshot.coords(self.rect_id, self.crop_start_x, self.crop_start_y, self.crop_end_x, self.crop_end_y)

    def _on_crop_release(self, event):
        if not hasattr(self, 'captured_frame') or self.captured_frame is None:
            return
            
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        
        # Получаем границы выделения
        x1 = min(self.crop_start_x, self.crop_end_x)
        x2 = max(self.crop_start_x, self.crop_end_x)
        y1 = min(self.crop_start_y, self.crop_end_y)
        y2 = max(self.crop_start_y, self.crop_end_y)
        
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            return # Слишком маленькая область
            
        # Масштабируем обратно в разрешение монитора
        h, w = self.captured_frame.shape[:2]
        scale_x = 640.0 / w
        scale_y = 360.0 / h
        
        nx1 = int(x1 / scale_x)
        nx2 = int(x2 / scale_x)
        ny1 = int(y1 / scale_y)
        ny2 = int(y2 / scale_y)
        
        # Ограничиваем координаты
        nx1 = max(0, min(nx1, w - 1))
        nx2 = max(nx1 + 5, min(nx2, w))
        ny1 = max(0, min(ny1, h - 1))
        ny2 = max(ny1 + 5, min(ny2, h))
        
        # Вырезаем и отображаем в превью
        crop = self.captured_frame[ny1:ny2, nx1:nx2]
        self.current_crop = crop
        self.current_crop_coords = (nx1, ny1, nx2, ny2)
        
        disp_crop = cv2.resize(crop, (150, 150), interpolation=cv2.INTER_AREA)
        disp_rgb = cv2.cvtColor(disp_crop, cv2.COLOR_BGR2RGB)
        
        img_pil = Image.fromarray(disp_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas_crop_preview.delete("all")
        self.canvas_crop_preview.image = img_tk
        self.canvas_crop_preview.create_image(0, 0, anchor="nw", image=img_tk)
        
        # Если это выделение шкалы, сразу обновляем превью масок HSV
        self.update_hsv_preview_from_screenshot()

    def capture_screen_for_templates(self):
        """Захватывает полный кадр с выбранного монитора для калибровки."""
        try:
            import mss
            with mss.mss() as sct:
                # Получаем параметры выбранного монитора
                mon_idx = self.cfg["MONITOR_INDEX"]
                if mon_idx <= 0 or mon_idx > len(sct.monitors):
                    mon_idx = 1
                monitor = sct.monitors[mon_idx]
                
                # Захватываем кадр
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                # Конвертируем BGRA в BGR
                self.captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Показываем на холсте
                self.show_captured_frame()
                self.write_log("Снимок экрана успешно сделан. Выделите нужный элемент мышкой.", "SUCCESS")
                
                # Сбрасываем прямоугольник
                if hasattr(self, 'rect_id') and self.rect_id:
                    self.canvas_screenshot.delete(self.rect_id)
                    self.rect_id = None
                self.crop_start_x = self.crop_start_y = self.crop_end_x = self.crop_end_y = None
                self.current_crop = None
        except Exception as e:
            self.write_log(f"Ошибка при захвате экрана: {e}", "ERROR")

    def show_captured_frame(self):
        """Выводит захваченный кадр на Canvas."""
        if self.captured_frame is None:
            return
            
        h, w = self.captured_frame.shape[:2]
        self.screenshot_scale_x = 640.0 / w
        self.screenshot_scale_y = 360.0 / h
        
        disp_img = cv2.resize(self.captured_frame, (640, 360), interpolation=cv2.INTER_AREA)
        disp_rgb = cv2.cvtColor(disp_img, cv2.COLOR_BGR2RGB)
        
        img_pil = Image.fromarray(disp_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas_screenshot.delete("all")
        self.canvas_screenshot.image = img_tk
        self.canvas_screenshot.create_image(0, 0, anchor="nw", image=img_tk)

    def save_custom_template(self, template_name):
        """Сохраняет выделенный кроп как кастомный шаблон."""
        if not hasattr(self, 'current_crop') or self.current_crop is None:
            self.write_log("Сначала сделайте снимок экрана и выделите область рамкой!", "WARNING")
            return
            
        try:
            filename = f"custom_{template_name}.png"
            filepath = os.path.join("assets", filename)
            cv2.imwrite(filepath, self.current_crop)
            self.write_log(f"Шаблон сохранен в assets/{filename}", "SUCCESS")
            
            # Если это шкала, записываем статические координаты в конфигурацию
            if template_name == "bar" and hasattr(self, 'current_crop_coords'):
                nx1, ny1, nx2, ny2 = self.current_crop_coords
                self.cfg["BAR_ROI_X1"] = nx1
                self.cfg["BAR_ROI_Y1"] = ny1
                self.cfg["BAR_ROI_X2"] = nx2
                self.cfg["BAR_ROI_Y2"] = ny2
                config.save_config(self.cfg)
                self.write_log(f"Статические координаты шкалы сохранены: [{nx1}, {ny1}] -> [{nx2}, {ny2}]", "SUCCESS")
            
            # Проверяем совпадение шаблона на текущем кадре и рисуем рамку
            self.verify_saved_template_on_screenshot(template_name)
        except Exception as e:
            self.write_log(f"Ошибка сохранения шаблона: {e}", "ERROR")

    def verify_saved_template_on_screenshot(self, template_name):
        """Проверяет совпадение шаблона на текущем снимке и визуализирует рамкой."""
        if self.captured_frame is None:
            return
            
        try:
            # Загружаем кастомный шаблон
            filepath = os.path.join("assets", f"custom_{template_name}.png")
            template = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return
                
            frame_gray = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2GRAY)
            
            # Для шкалы (bar) мы ищем в верхней зоне, для остальных по всему экрану
            roi = None
            if template_name == "bar":
                h, w = frame_gray.shape
                roi = (int(0.02 * h), int(0.18 * h), int(0.15 * w), int(0.85 * w))
                
            # Ищем совпадение
            score, loc = vision.match_template_on_frame(
                frame_gray, template, 0.1, roi_coords=roi
            )
            
            if loc is not None:
                # Перерисовываем скриншот на канве
                self.show_captured_frame()
                
                # Масштабируем координаты рамки для вывода на канве
                th, tw = template.shape[:2]
                rx1 = int(loc[0] * self.screenshot_scale_x)
                ry1 = int(loc[1] * self.screenshot_scale_y)
                rx2 = int((loc[0] + tw) * self.screenshot_scale_x)
                ry2 = int((loc[1] + th) * self.screenshot_scale_y)
                
                # Рисуем рамку
                self.canvas_screenshot.create_rectangle(rx1, ry1, rx2, ry2, outline="#00e676", width=3)
                
                # Пишем счет на холсте
                self.canvas_screenshot.create_text(
                    (rx1 + rx2) // 2, ry1 - 10,
                    text=f"Совпадение: {score:.3f}",
                    fill="#00e676",
                    font=("Segoe UI", 10, "bold")
                )
                
                self.write_log(f"Проверка: Шаблон '{template_name}' распознан! Совпадение: {score:.4f}", "SUCCESS")
            else:
                self.write_log(f"Проверка: Шаблон '{template_name}' НЕ найден на скриншоте.", "WARNING")
        except Exception as e:
            self.write_log(f"Ошибка проверки шаблона: {e}", "ERROR")

    def update_hsv_preview_from_screenshot(self):
        """Обновляет превью масок HSV на Canvas на основе сделанного скриншота."""
        if not hasattr(self, 'current_crop') or self.current_crop is None:
            return
            
        try:
            # Преобразуем кроп шкалы в HSV
            hsv = cv2.cvtColor(self.current_crop, cv2.COLOR_BGR2HSV)
            
            # Читаем границы из GUI
            g_low = np.array([self.var_g_h_min.get(), self.var_g_s_min.get(), self.var_g_v_min.get()])
            g_high = np.array([self.var_g_h_max.get(), self.var_g_s_max.get(), self.var_g_v_max.get()])
            
            y_low = np.array([self.var_y_h_min.get(), self.var_y_s_min.get(), self.var_y_v_min.get()])
            y_high = np.array([self.var_y_h_max.get(), self.var_y_s_max.get(), self.var_y_v_max.get()])
            
            img_raw = cv2.cvtColor(self.current_crop, cv2.COLOR_BGR2RGB)
            img_green = cv2.cvtColor(cv2.inRange(hsv, g_low, g_high), cv2.COLOR_GRAY2RGB)
            img_yellow = cv2.cvtColor(cv2.inRange(hsv, y_low, y_high), cv2.COLOR_GRAY2RGB)
            
            for canvas, img in [
                (self.canvas_raw, img_raw),
                (self.canvas_green, img_green),
                (self.canvas_yellow, img_yellow)
            ]:
                display_img = cv2.resize(img, (680, 40), interpolation=cv2.INTER_NEAREST)
                img_pil = Image.fromarray(display_img)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                
                canvas.delete("all")
                canvas.image = img_tk
                canvas.create_image(0, 0, anchor="nw", image=img_tk)
        except Exception as e:
            pass


def main():
    root = tk.Tk()
    
    # Стилизуем элементы
    root.tk_setPalette(background='#1c1c1c', foreground='#ffffff',
                       activeBackground='#2c2c2c', activeForeground='#ffffff')
                       
    app = FishingBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
