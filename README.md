# NTE Auto-Fish Bot 🎣

An automatic fishing bot powered by OpenCV computer vision algorithms and a Tkinter GUI. The bot is optimized to bypass anti-cheat systems using smart timing randomization and human-like input emulation.

---

## ✨ Key Features

*   **📍 Static Coordinates (Stability)**: Completely avoids unreliable search patterns on dynamically changing game backgrounds. You select the fishing bar coordinates in the GUI once, and the bot will always crop this exact area with pixel-perfect accuracy.
*   **🛡️ Anti-Cheat Randomization**:
    *   Randomized jitter applied to all delay steps (cast, hook, balance, close).
    *   Randomized press durations for key inputs (`F`, `Esc`).
    *   Adjustable randomization strength percentage (0–50%).
*   **⌨️ ESC Key Emulation**: Dismisses the loot screen (Step 4) by simulating an `Esc` key press instead of mouse clicks, bypassing game blocks on virtual mouse clicks.
*   **💻 Safe Input Emulation**: Utilizes `pydirectinput` with default action pauses disabled (`PAUSE = 0.0`) to register inputs with millisecond timing accuracy.
*   **📺 Triple Live Previews**: The GUI displays three real-time streams concurrently:
    1.  The raw cropped fishing bar.
    2.  The green sweet spot mask.
    3.  The yellow slider mask.
*   **🛑 Emergency Stop**: A global hotkey (`F12`) instantly stops the bot and releases all active virtual inputs at any time.
*   **⚡ Adjustable FPS**: Limit screenshot frequency to fine-tune bot loop speed and CPU load.

---

## 📋 System Requirements

*   **OS**: Windows
*   **Python**: 3.8 or higher
*   **Screen Resolution**: Tested at 2560x1440 (supports any resolution thanks to custom ROI selection).

### Dependencies:
```bash
pip install opencv-python numpy mss pydirectinput Pillow
```

---

## 🚀 Quick Start

1.  Launch the game in Windowed or Borderless Windowed mode.
2.  Launch the bot GUI:
    ```bash
    python fishing_bot.py
    ```
3.  Go to the **"Захват шаблонов"** (Template Capture) tab.
4.  Click **📸 Сделать снимок экрана** (Take Screenshot), click and drag to select your fishing bar area on the canvas, then click **«Шкала рыбалки (Bar)»**. The coordinates will automatically be saved to configuration.
5.  Return to the main tab and click **СТАРТ**. You will have 5 seconds to switch focus to the game window.

---

## ⚙️ Settings Description in GUI

*   **Скриншотов в сек (FPS)**: Limits the frame rate. A value of `30` is recommended for high accuracy with low CPU usage.
*   **Рандомизация задержек**: Enable/disable randomized delay variations.
*   **Разброс задержек (%)**: Randomization strength. Recommended value: `15%`.
*   **Длительность нажатия F (сек)**: The duration that the cast key is held down.
*   **Задержка после заброса (сек)**: The base waiting time for a fish bite.
*   **Задержка после подсечки (сек)**: The delay before the fishing bar appears on the screen.
*   **Задержка после улова (сек)**: The delay before pressing the `Esc` key to close the loot.
*   **Отступ безопасности (px)**: Sweet spot margin on the edges to prevent unnecessary control corrections.
*   **Режим удержания**:
    *   `hold` — continuously holds keys to balance.
    *   `click` — applies rapid taps to balance.

---

# NTE Auto-Fish Bot 🎣 (Русская версия)

Автоматический бот для рыбалки, использующий алгоритмы компьютерного зрения OpenCV и графический интерфейс Tkinter. Бот оптимизирован для обхода систем анти-чита за счет интеллектуальной рандомизации задержек и человекоподобного ввода.

---

## ✨ Ключевые особенности

*   **📍 Статические координаты (Стабильность)**: Полный отказ от ненадежного поиска шаблона шкалы на меняющемся игровом фоне. Вы один раз выделяете шкалу в GUI, и бот всегда вырезает именно эту область с точностью до пикселя.
*   **🛡️ Anti-чит рандомизация**:
    *   Случайные отклонения для всех пауз (заброс, подсечка, удержание, закрытие улова).
    *   Рандомизация длительности зажатия функциональных клавиш (`F`, `Esc`).
    *   Регулируемый процент разброса джиттера (0–50%).
*   **⌨️ Имитация клавиши ESC**: Выход из окна улова (Шаг 4) осуществляется через симуляцию клавиши `Esc` вместо кликов мыши, что решает проблему блокировки кликов игрой.
*   **💻 Безопасный эмулятор ввода**: Интегрирован `pydirectinput` с отключенными системными задержками (`PAUSE = 0.0`), обеспечивающий реакцию клавиш с точностью до миллисекунды.
*   **📺 Живой тройной предпросмотр**: GUI одновременно отображает три видеопотока в реальном времени:
    1.  Оригинальный вырезанный кадр шкалы.
    2.  Маску зеленой зоны (Sweet Spot).
    3.  Маску желтого ползунка (Slider).
*   **🛑 Экстренный стоп**: Глобальная горячая клавиша `F12` мгновенно останавливает бота и сбрасывает все зажатые виртуальные клавиши в любой момент.
*   **⚡ Настройка FPS**: Выбор частоты скриншотов в секунду для гибкого контроля нагрузки на процессор.

---

## 📋 Системные требования

*   **ОС**: Windows
*   **Python**: 3.8 или выше
*   **Разрешение экрана**: Протестировано на 2560x1440 (поддерживает любые разрешения экрана за счет кастомного выделения).

### Зависимости:
```bash
pip install opencv-python numpy mss pydirectinput Pillow
```

---

## 🚀 Быстрый старт

1.  Запустите игру в оконном режиме или режиме «в окне без рамки».
2.  Запустите графический интерфейс бота:
    ```bash
    python fishing_bot.py
    ```
3.  Перейдите во вкладку **«Захват шаблонов»**.
4.  Нажмите **📸 Сделать снимок экрана**, выделите мышкой вашу шкалу рыбалки на скриншоте и нажмите кнопку **«Шкала рыбалки (Bar)»**. Координаты автоматически запишутся в конфигурацию.
5.  Вернитесь на главную вкладку и нажмите **СТАРТ**. У вас будет 5 секунд, чтобы переключить фокус на окно игры.

---

## ⚙️ Настройка параметров в GUI

*   **Скриншотов в сек (FPS)**: Ограничение частоты обработки кадров. Значение `30` обеспечивает высокую точность и низкую нагрузку.
*   **Рандомизация задержек**: Включение/выключение случайных отклонений таймингов.
*   **Разброс задержек (%)**: Сила джиттера. Рекомендуемое значение: `15%`.
*   **Длительность нажатия F (сек)**: Время, в течение которого кнопка удерживается нажатой.
*   **Задержка после заброса (сек)**: Время ожидания поклевки (базовое).
*   **Задержка после подсечки (сек)**: Пауза до появления шкалы мини-игры.
*   **Задержка после улова (сек)**: Время ожидания анимации перед нажатием `Esc`.
*   **Отступ безопасности (px)**: Зона нечувствительности на краях зеленого ползунка, предотвращающая лишние дергания.
*   **Режим удержания**:
    *   `hold` — непрерывное удержание клавиш влево/вправо.
    *   `click` — прерывистые частые клики.
