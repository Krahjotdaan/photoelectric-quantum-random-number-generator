import time
import numpy as np
import serial


def collect_data_to_memory(samples, port_device, baud_rate=2000000, 
                           logger=None, progress_callback=None, 
                           reconnect_timeout=30, stop_flag=None):
    """
    Сбор данных с АЦП в память с поддержкой логирования и переподключения.
    
    Args:
        samples: Количество отсчетов для сбора
        port_device: Имя порта (например, 'COM5')
        baud_rate: Скорость UART
        logger: Функция для вывода логов (pyqtSignal.emit)
        reconnect_timeout: Время попытки переподключения при обрыве связи (сек)
        
    Returns:
        np.ndarray(dtype=np.uint16) или None при ошибке
    """
    PACKET_SAMPLES = 4096
    PACKET_BYTES = PACKET_SAMPLES * 2
    
    def log(msg):
        if logger:
            logger(msg)
        else:
            print(msg)

    def progress(msg):
        if progress_callback: progress_callback(msg)

    log(f" Подключение к {port_device}...")
    
    start_time = time.time()
    ser = None
    raw_buffer = bytearray()
    
    while True:
        try:
            ser = serial.Serial(port_device, baud_rate, timeout=1)
            time.sleep(1.0) 
            
            ser.write(b's')
            time.sleep(0.5)
            ser.reset_input_buffer()
            
            log(f"\nСбор {samples:,} отсчетов...")
            break
            
        except (serial.SerialException, OSError) as e:
            elapsed = time.time() - start_time
            if elapsed > reconnect_timeout:
                log(f"Не удалось подключиться за {reconnect_timeout} сек: {e}")
                return None
            log(f"Порт недоступен ({e}). Повторная попытка через 2 сек...")
            time.sleep(2)

    try:
        last_log_count = 0
        while len(raw_buffer) < samples * 2:
            if stop_flag and stop_flag():
                log("Сбор остановлен пользователем.")
                return None
            
            chunk = ser.read(PACKET_BYTES)
            
            if len(chunk) == PACKET_BYTES:
                raw_buffer.extend(chunk)
            elif len(chunk) > 0:
                log(f"Пропущен неполный пакет ({len(chunk)} байт)")
            else:
                # Проверка на обрыв связи во время сбора
                if ser.in_waiting == 0 and len(raw_buffer) > 0:
                    time.sleep(0.1)
                    if ser.in_waiting == 0:
                        log("Данные перестали поступать. Попытка переподключения...")
                        ser.close()
                        time.sleep(1)
                        try:
                            ser = serial.Serial(port_device, baud_rate, timeout=1)
                            time.sleep(0.5)
                            ser.write(b's')
                            time.sleep(0.5)
                            ser.reset_input_buffer()
                            log("Переподключение успешно. Продолжение сбора...")
                        except Exception as re_conn_err:
                            log(f"Не удалось переподключиться: {re_conn_err}")
                            return None

            collected = len(raw_buffer) // 2
            if collected - last_log_count >= max(10000, samples // 100):
                pct = min(100, int(collected * 100 / samples))
                progress(f"  Прогресс: {collected:,}/{samples:,} ({pct}%)")
                    
                last_log_count = collected

        end_time = time.time()
        total_bytes = min(len(raw_buffer), samples * 2)
        data = np.frombuffer(bytes(raw_buffer[:total_bytes]), dtype=np.uint16)
        
        elapsed = end_time - start_time
        rate = len(data) / elapsed if elapsed > 0 else 0
        
        log(f"\nСобрано: {len(data):,} отсчетов")
        log(f"Время: {elapsed:.1f} сек | Скорость: {rate:,.0f} отсчетов/сек")
        
        return data

    except KeyboardInterrupt:
        log("Сбор остановлен пользователем")
        return None
    except Exception as e:
        log(f"Ошибка при сборе данных: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception:
                pass


def load_data_bin(filename, logger=None):
    """Загрузка .bin файла с логированием"""
    def log(msg):
        if logger: logger(msg)
        else: print(msg)
        
    try:
        data = np.fromfile(filename, dtype=np.uint16)
        log(f"Загружено {len(data)} отсчетов из {filename}")
        return data
    except FileNotFoundError:
        log(f"Файл не найден: {filename}")
        return np.array([], dtype=np.uint16)
    except Exception as e:
        log(f"Ошибка чтения {filename}: {e}")
        return np.array([], dtype=np.uint16)