import time
import numpy as np
import serial
import serial.tools.list_ports
from config import PACKET_SAMPLES, PACKET_BYTES, BAUD_RATE, SERIAL_TIMEOUT

def collect(samples, filename='data.bin', baud_rate=None):
    """
    Сбор данных с АЦП и сохранение в бинарный файл
    """
    if baud_rate is None:
        baud_rate = BAUD_RATE

    ports = serial.tools.list_ports.comports()
    port_name = None
    for p in ports:
        print(f"Найден порт: {p.device} - {p.description}")
        if 'Arduino' in p.description or 'USB Serial' in p.description or 'COM5' in p.description or 'COM3' in p.description:
            port_name = p.device
            break

    if not port_name:
        print("Ошибка: Устройство не найдено. Проверьте подключение.")
        return
    
    ser = serial.Serial(port_name, baud_rate, timeout=SERIAL_TIMEOUT)

    try:
        time.sleep(1) 
        ser.write(b's')
        time.sleep(0.5)
        ser.reset_input_buffer()

        print(f"Сбор {samples:,} отсчетов... (Ctrl+C для остановки)")

        raw_buffer = bytearray()
        start_time = time.time()

        while len(raw_buffer) < samples * 2:
            chunk = ser.read(PACKET_BYTES)

            if len(chunk) == PACKET_BYTES:
                raw_buffer.extend(chunk)
            elif len(chunk) > 0:
                print(f"\nПропущен неполный пакет ({len(chunk)} байт)")
            else:
                elapsed = time.time() - start_time
                if elapsed > 5 and len(raw_buffer) == 0:
                    print("\nОшибка: Данные не приходят.")
                    break

            collected = len(raw_buffer) // 2
            if collected % 10000 < PACKET_SAMPLES:
                pct = min(100, collected * 100 // samples)
                print(f"\r  Прогресс: {collected:,}/{samples:,} ({pct}%)", end='', flush=True)

        end_time = time.time()

        total_bytes = min(len(raw_buffer), samples * 2)
        
        if total_bytes == 0:
            print("Нет данных для сохранения.")
            return

        data = np.frombuffer(bytes(raw_buffer[:total_bytes]), dtype=np.uint16)

        with open(filename, 'wb') as f:
            f.write(data.tobytes())

        elapsed = end_time - start_time
        rate = len(data) / elapsed if elapsed > 0 else 0

        print(f"\n\nСобрано: {len(data):,} отсчетов")
        print(f"Время сбора: {elapsed:.1f} сек")
        print(f"Скорость: {rate:,.0f} отсчетов/сек")
        print(f"Файл сохранён: {filename} (Размер: {total_bytes / 1024 / 1024:.2f} МБ)")

    except KeyboardInterrupt:
        print("\n\nОстановлено пользователем.")
        end_time = time.time()
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()


def load_data_bin(filename):
    try:
        data = np.fromfile(filename, dtype=np.uint16)
        print(f"Загружено {len(data)} отсчетов из {filename}.")
        return data
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден.")
        return np.array([], dtype=np.uint16)
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return np.array([], dtype=np.uint16)
    