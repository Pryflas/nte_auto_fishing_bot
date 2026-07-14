# NTE Auto-Fish Bot 🎣

Welcome to the **NTE Auto-Fish Bot**! This utility is designed to fully automate the fishing process in your game. Powered by OpenCV computer vision and built with a clean Tkinter GUI, it features smart anti-cheat bypasses (randomized delays and keypresses) to keep your account safe.

---

## ⚠️ Important: Resolution and Screen Setup

**The default configuration is set up for a 2560x1440 fullscreen monitor.** 

If your game runs in a different resolution (e.g., 1920x1080) or windowed mode, **the default coordinates will not work!** You must configure it for your screen:

### How to set up your resolution (2 methods):

#### Method 1: Using the GUI (Recommended & Easiest)
1. Launch the game in windowed or borderless windowed mode.
2. Run `python fishing_bot.py` and switch to the **"Захват шаблонов" (Template Capture)** tab.
3. Click **📸 Сделать снимок экрана (Take Screenshot)**.
4. Click and drag with your mouse to draw a box around the active fishing bar on the captured screen.
5. Click **«Шкала рыбалки (Bar)»**. The bot will automatically calculate your exact screen coordinates and save them to `config.json` for you!

#### Method 2: Manually editing `config.json`
Open `config.json` in a text editor and update the following static coordinate keys to match your screen layout:
*   `"BAR_ROI_X1"`: Top-left X coordinate of the bar
*   `"BAR_ROI_Y1"`: Top-left Y coordinate of the bar
*   `"BAR_ROI_X2"`: Bottom-right X coordinate of the bar
*   `"BAR_ROI_Y2"`: Bottom-right Y coordinate of the bar
*   `"GAME_REGION"`: If playing in windowed mode, set this to `[x, y, width, height]` of your game window instead of `null`.

---

## ✨ Features

*   **📍 Static ROI Cropping**: Directly crops the fishing bar coordinates without doing CPU-heavy template searches. It is 100% immune to background changes (time of day, weather, water reflections).
*   **🛡️ Anti-Cheat Protection**:
    *   Human-like randomized delays between states.
    *   Randomized press-and-hold durations for `F` and `Esc`.
    *   Adjustable randomized jitter strength slider in the GUI.
*   **⌨️ ESC Key Emulation**: Dismisses the loot screen (Step 4) by simulating an `Esc` key press instead of mouse clicks, bypassing game blocks on virtual mouse clicks.
*   **🛑 Emergency Stop**: Press `F12` at any time to instantly stop the bot and release all virtual keys.
*   **⚡ Customizable FPS**: Limit screenshots per second to reduce CPU usage.

---

## 📋 Installation

1.  Make sure you have Python 3.8+ installed.
2.  Install the required libraries:
    ```bash
    pip install opencv-python numpy mss pydirectinput Pillow
    ```

---

## 🚀 How to Run

1.  Launch the game.
2.  Run the bot:
    ```bash
    python fishing_bot.py
    ```
3.  Adjust your delays and timing in the **"Основные настройки"** (General Settings) tab if needed.
4.  Click **СТАРТ** (Start). You will have **5 seconds** to focus back onto the game window.
5.  Press **F12** (or click **СТОП**) to stop the bot at any time.

---

# NTE Auto-Fish Bot 🎣 (Русская версия)

Добро пожаловать в **NTE Auto-Fish Bot**! Эта утилита полностью автоматизирует процесс рыбалки в вашей игре. Бот работает на базе компьютерного зрения OpenCV, имеет интуитивно понятный графический интерфейс Tkinter и оснащен алгоритмами защиты от систем анти-чита (человекоподобная рандомизация нажатий и таймингов).

---

## ⚠️ Важное предупреждение: Разрешение экрана

**По умолчанию конфигурация настроена под разрешение 2560x1440 в полноэкранном режиме.**

Если у вас другое разрешение экрана (например, 1920x1080) или вы играете в оконном режиме, **дефолтные координаты не сработают!** Вам необходимо перенастроить область под свой экран.

### Как настроить разрешение (2 способа):

#### Способ 1: Через графический интерфейс (Рекомендуемый)
1. Запустите игру (желательно в оконном режиме или режиме без рамки).
2. Запустите бота (`python fishing_bot.py`) и перейдите во вкладку **«Захват шаблонов»**.
3. Нажмите кнопку **📸 Сделать снимок экрана**.
4. Зажмите левую кнопку мыши и выделите рамкой шкалу рыбалки на скриншоте.
5. Нажмите кнопку **«Шкала рыбалки (Bar)»**. Бот автоматически определит новые координаты и сохранит их в файл `config.json`.

#### Способ 2: Вручную в файле `config.json`
Откройте файл `config.json` в любом текстовом редакторе и укажите координаты вашей шкалы:
*   `"BAR_ROI_X1"`: Координата X левого верхнего угла шкалы.
*   `"BAR_ROI_Y1"`: Координата Y левого верхнего угла шкалы.
*   `"BAR_ROI_X2"`: Координата X правого нижнего угла шкалы.
*   `"BAR_ROI_Y2"`: Координата Y правого нижнего угла шкалы.
*   `"GAME_REGION"`: Если играете в окне, укажите `[x, y, ширина, высота]` окна вместо `null`.

---

## ✨ Возможности

*   **📍 Статические координаты (Стабильность)**: Бот мгновенно кадрирует шкалу без лишней нагрузки на процессор. Это на 100% защищает от ложных срабатываний из-за смены погоды, времени суток или бликов на воде.
*   **🛡️ Защита от бана (Анти-чит)**:
    *   Рандомизация всех задержек между действиями.
    *   Случайная длительность удержания клавиш `F` и `Esc`.
    *   Регулируемый ползунок силы рандомизации в GUI.
*   **⌨️ Закрытие через ESC**: Меню улова закрывается нажатием клавиши `Esc`, что обходит любые ограничения игры на симуляцию мыши.
*   **🛑 Быстрый сброс**: Горячая клавиша `F12` мгновенно останавливает бота и отпускает все клавиши в экстренной ситуации.
*   **⚡ Регулировка FPS**: Выбор частоты скриншотов в секунду для снижения нагрузки на процессор.

---

## 📋 Установка

1.  Установите Python версии 3.8 или выше.
2.  Установите необходимые библиотеки в терминале:
    ```bash
    pip install opencv-python numpy mss pydirectinput Pillow
    ```

---

## 🚀 Инструкция по запуску

1.  Запустите игру.
2.  Запустите бота:
    ```bash
    python fishing_bot.py
    ```
3.  При необходимости настройте тайминги на первой вкладке GUI.
4.  Нажмите **СТАРТ**. У вас будет **5 секунд**, чтобы переключиться на окно с игрой.
5.  Для остановки бота нажмите кнопку **СТОП** или клавишу **F12**.
