import time
import csv
import serial
import serial.tools.list_ports


def collect(samples, filename='data.csv'):
    BAUD_RATE = 500000

    ports = serial.tools.list_ports.comports()
    port_name = None
    for p in ports:
        if 'Arduino' in p.description or 'CH340' in p.description or 'USB Serial' in p.description:
            port_name = p.device
            break

    if not port_name:
        print("Ошибка: Arduino не найдена")
        exit()

    print(f"Найдено устройство: {port_name}")

    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
        time.sleep(2)
        
        print("Отправка команды старта...")
        ser.write(b's')
        time.sleep(0.5)
        
        print(f"Сбор {samples} отсчетов... (нажмите Ctrl+C для досрочной остановки)")
        
        data = []
        
        start_time = time.time()
        while len(data) < samples:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.isdigit():
                    data.append(int(line))
                    if len(data) % 500 == 0:
                        print(f"Собрано: {len(data)}", end='\r')
            
            if time.time() - start_time > 5 and len(data) == 0:
                print("\nОшибка: Данные не приходят. Проверьте, закрыт ли Serial Monitor в Arduino IDE.")
                break
        end_time = time.time()
                
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
    except Exception as e:
        print(f"\nОшибка: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

    if len(data) > 0:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'value'])
            for i, val in enumerate(data):
                writer.writerow([i, val])

        print(f"\nВремя генерации: {end_time - start_time}")
        print(f"\nСохранено {len(data)} значений в файл {filename}")
