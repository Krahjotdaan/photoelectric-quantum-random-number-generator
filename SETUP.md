# Установка и настройка КГСЧ

## Содержание

1. [Установка зависимостей](#1-установка-зависимостей)
2. [Прошивка микроконтроллера](#2-прошивка-микроконтроллера)
3. [Запуск CLI-сценария](#3-запуск-cli-сценария)
4. [Запуск UI-утилиты](#4-запуск-ui-утилиты)
5. [Сборка UI в исполняемый файл (PyInstaller)](#5-сборка-ui-в-исполняемый-файл-pyinstaller)
6. [Бенчмарки](#6-бенчмарки)
7. [Конфигурация](#7-конфигурация)

---

## 1. Установка зависимостей

### 1.1. Python

Требуется Python 3.10 или выше. Проверить версию:

```bash
python --version
```

### 1.2. Виртуальное окружение (рекомендуется)

```bash
# Создание
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/macOS)
source .venv/bin/activate
```

### 1.3. Установка пакетов

**Для CLI (корневой каталог проекта):**

```bash
pip install -r requirements.txt
```

**Для UI-утилиты:**

```bash
cd ui_util
pip install -r requirements.txt
```

Содержимое [`requirements.txt`](requirements.txt):

- `numpy` — обработка данных
- `scipy` — статистические тесты
- `pyserial` — связь с микроконтроллером по UART
- `gostcrypto` — хеш-функции Streebog
- `matplotlib` — визуализация (ACF-графики)

Дополнительно для UI:

- `PyQt6` — графический интерфейс

---

## 2. Прошивка микроконтроллера

### 2.1. Требования

- Плата: Waveshare RP2040 One (или любой RP2040 с АЦП)
- [Arduino IDE](https://www.arduino.cc/en/software) (рекомендуется) или Raspberry Pi Pico SDK

### 2.2. Прошивка через Arduino IDE (рекомендуется)

1. **Установите поддержку RP2040 в Arduino IDE:**
   - Откройте Arduino IDE → **File** → **Preferences**
   - В поле "Additional boards manager URLs" добавьте:
     ```
     https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
     ```
   - Нажмите **OK**
   - Перейдите: **Tools** → **Board** → **Boards Manager**
   - Найдите "Raspberry Pi Pico/RP2040" и установите пакет

2. **Откройте прошивку:**
   - В Arduino IDE: **File** → **Open**
   - Выберите файл [`firmware/firmware.ino`](firmware/firmware.ino)

3. **Выберите плату:**
   - **Tools** → **Board** → **Raspberry Pi RP2040 Boards** → **Waveshare RP2040 One** (или вашу плату)

4. **Загрузите прошивку:**
   - Подключите RP2040 через USB
   - Нажмите кнопку **Upload** (→) в Arduino IDE
   - При необходимости удерживайте BOOTSEL на плате при подключении

### 2.3. Альтернатива: прошивка через Pico SDK

Если вы предпочитаете сборку через CMake:

```bash
# Клонировать SDK
git clone https://github.com/raspberrypi/pico-sdk
cd pico-sdk
git submodule update --init
cd ..

# Собрать
cd firmware
mkdir build && cd build
cmake .. -DPICO_SDK_PATH=../../pico-sdk
make
```

Затем скопируйте `firmware/build/firmware.uf2` на диск `RPI-RP2` (удерживая BOOTSEL при подключении).

### 2.4. Проверка

После прошивки подключите плату к компьютеру. В системе должен появиться COM-порт:
- **Windows:** `COM3`, `COM5` и т.д. (проверьте в Диспетчере устройств)
- **Linux:** `/dev/ttyACM0` или `/dev/ttyUSB0`
- **macOS:** `/dev/cu.usbmodem*`

---

## 3.  Полный цикл: сбор → экстракция → тестирование

```python
from collect import collect, load_data_bin
from extract import arx_extract
from run_tests import run_nist
from additional_suite.entropy_estimator import min_entropy_nist_90b, calculate_safe_compression_ratio

# 1. Сбор 3 млн отсчётов
collect(3_000_000, "data.bin")

# 2. Загрузка
raw = load_data_bin("data.bin")

# 3. Расчет мин. энтропии и безопасного коэффициента сжатия
diff_array = np.diff(raw)
diff_bits = (diff_array & 1).astype(np.uint8)

min_entropy = min_entropy_nist_90b(diff_bits)
safe_compression_ratio = calculate_safe_compression_ratio(min_entropy)

print(f"\nМин-энтропия: {min_entropy:.4f} бит/бит")
print(f"Рекомендуемый коэффициент сжатия: ≤ {safe_compression_ratio:.2f}")

# 4. Экстракция (ARX, коэффициент сжатия 2)
bits = arx_extract(raw, 1_000_000, 2)

# 5. Запуск NIST-тестов
run_nist(bits)
```

---

## 4. Запуск UI-утилиты

```bash
cd ui_util
python main.py
```

UI-утилита предоставляет:

- Выбор метода экстракции (ARX, SHA-256, SHA3-256, SHA-512, SHA3-512, Blake2s, Blake2b, Streebog-256, Streebog-512)
- Настройка целевого количества бит и коэффициента сжатия
- Выбор тестов NIST для запуска
- Автоопределение COM-порта
- Сохранение сырых данных, извлечённых данных и отчётов
- Логирование процесса в реальном времени

---

## 5. Сборка UI в исполняемый файл (PyInstaller)

### 5.1. Установка PyInstaller

```bash
cd ui_util
pip install pyinstaller
```

### 5.2. Сборка в один exe-файл

```bash
cd ui_util
pyinstaller --onefile --windowed --name "QRNG_Utility" main.py
```

Параметры:

- `--onefile` — упаковать всё в один исполняемый файл
- `--windowed` — без консольного окна (только GUI)
- `--name "QRNG_Utility"` — имя выходного файла

Готовый файл появится в `ui_util/dist/QRNG_Utility.exe`.

### 5.3. Сборка с иконкой (опционально)

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name "QRNG_Utility" main.py
```

### 5.4. Примечания

- При сборке PyInstaller автоматически включает все импортируемые зависимости.
- Если возникают ошибки с `gostcrypto` или `scipy`, укажите их явно:

```bash
pyinstaller --onefile --windowed --hidden-import=gostcrypto --name "QRNG_Utility" main.py
```

- Готовый exe можно запускать на любом компьютере с Windows без установки Python.

---

## 6. Бенчмарки

Запуск тестов производительности:

```bash
# Тест экстракции на синтетических данных
python benchmarks.py

# С указанием размера данных
python benchmarks.py --samples 1000000 --target-bits 200000

# С тестом реального сбора (требуется устройство)
python benchmarks.py --live
```

Результаты:

- Скорость ARX-экстракции (бит/сек)
- Скорость каждого hash-метода (бит/сек)
- Пропускная способность системы
- Скорость сбора с устройства (с флагом `--live`)

---

## 7. Конфигурация

### 7.1. CLI-конфигурация ([`config.py`](config.py))

Параметры можно переопределить через переменные окружения:

| Переменная | По умолчанию | Описание |
|---|---|---|
| `QRNG_BAUD_RATE` | `2000000` | Скорость UART |
| `QRNG_PACKET_SAMPLES` | `4096` | Размер пакета АЦП |
| `QRNG_SERIAL_TIMEOUT` | `1` | Таймаут последовательного порта (сек) |
| `QRNG_RECONNECT_TIMEOUT` | `30` | Таймаут переподключения (сек) |

Пример:

```bash
set QRNG_BAUD_RATE=3000000
python -c "from collect import collect; collect(3_000_000, 'data.bin')"
```

### 7.2. UI-конфигурация ([`ui_util/config_manager.py`](ui_util/config_manager.py))

Настройки UI сохраняются в файл `qrng_config.json` в корне проекта:

- Пути сохранения сырых данных, извлечённых данных и отчётов
- Последний выбранный метод экстракции
- Целевое количество бит и коэффициент сжатия
- Скорость UART
- Счётчик последовательности (автоинкремент)

---

## Структура проекта

```
photoelectric-quantum-random-number-generator/
├── firmware/
│   └── firmware.ino          # Прошивка RP2040
├── nist_suite/               # 15 тестов NIST SP 800-22
├── additional_suite/         # Дополнительные метрики
├── ui_util/                  # UI-утилита (PyQt6)
│   ├── main.py               # Точка входа UI
│   ├── config_manager.py     # Конфигурация UI
│   ├── qrng_worker.py        # Фоновый поток
│   ├── ui_main_window.py     # Главное окно
│   └── backend/              # Копия core-модулей для самодостаточности
├── collect.py                # Сбор данных с АЦП
├── extract.py                # Экстракция энтропии
├── run_tests.py              # Запуск тестов NIST
├── config.py                 # Централизованная конфигурация CLI
├── benchmarks.py             # Бенчмарки производительности
├── process.ipynb             # Jupyter Notebook (полный цикл)
├── requirements.txt          # Зависимости CLI
├── SETUP.md                  # Данный файл
└── README.md                 # Описание проекта