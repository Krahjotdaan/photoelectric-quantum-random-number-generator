import time
import csv
import numpy as np
import serial
import serial.tools.list_ports


def collect(samples, filename='data.csv', baud_rate=1500000):
    PACKET_SAMPLES = 256
    PACKET_BYTES = PACKET_SAMPLES * 2

    ports = serial.tools.list_ports.comports()
    port_name = None
    for p in ports:
        print(f"Найден порт: {p.device} - {p.description}")
        if 'Arduino' in p.description or 'USB Serial' in p.description or 'COM5' in p.description:
            port_name = p.device
            break

    if not port_name:
        print("Ошибка: Устройство не найдено. Проверьте подключение.")
        return

    try:
        ser = serial.Serial(port_name, baud_rate, timeout=1)
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

    except KeyboardInterrupt:
        print("\n\nОстановлено пользователем.")
        end_time = time.time()
    except Exception as e:
        print(f"\nОшибка: {e}")
        return
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

    total_bytes = min(len(raw_buffer), samples * 2)
    data = np.frombuffer(bytes(raw_buffer[:total_bytes]), dtype=np.uint16)

    if len(data) == 0:
        print("Нет данных для сохранения.")
        return

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index', 'value'])
        for i, val in enumerate(data):
            writer.writerow([i, int(val)])

    elapsed = end_time - start_time
    rate = len(data) / elapsed if elapsed > 0 else 0

    print(f"\n\nСобрано: {len(data):,} отсчетов")
    print(f"Время: {elapsed:.1f} сек")
    print(f"Скорость: {rate:,.0f} отсчетов/сек")
    print(f"Файл сохранён: {filename}")
