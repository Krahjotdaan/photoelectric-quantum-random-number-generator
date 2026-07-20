import os
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from backend.collector import collect_data_to_memory
from backend.extractor import arx_extract, hash_extract
from backend.additional_suite.entropy_estimator import min_entropy_nist_90b
from backend.run_tests import * 


class QrngWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            p = self.params
            
            def ui_logger(msg):
                if self._is_running:
                    self.log_signal.emit(msg)
            
            def ui_progress(msg):
                if self._is_running:
                    self.progress_signal.emit(msg)

            if not self._is_running:
                self.finished_signal.emit(False, "Остановлено пользователем")
                return

            # 1. СБОР ДАННЫХ
            raw_data = collect_data_to_memory(
                samples=p['samples'], 
                port_device=p['port'], 
                baud_rate=p['baud_rate'],
                logger=ui_logger,
                progress_callback=ui_progress,
                reconnect_timeout=30,
                stop_flag=lambda: not self._is_running
            )
            
            if not self._is_running:
                self.finished_signal.emit(False, "Остановлено пользователем")
                return
                
            if raw_data is None or len(raw_data) == 0:
                raise Exception("Не удалось собрать данные или порт недоступен.")
                
            if self._is_running:
                with open(p['raw_file'], 'wb') as f:
                    f.write(raw_data.tobytes())
                ui_logger(f"\nСырые данные сохранены: {os.path.basename(p['raw_file'])}")

            # 2. ОЦЕНКА ЭНТРОПИИ
            if self._is_running:
                diff_array = np.diff(raw_data)
                raw_bits = (diff_array & 1).astype(np.uint8)
                h_min = min_entropy_nist_90b(raw_bits, logger=ui_logger)
                
                ui_logger(f"Мин-энтропия: {h_min:.4f} бит/бит")

            # 3. ЭКСТРАКЦИЯ
            if self._is_running:
                ui_logger(f"\nМетод: {p['method']} | Коэф. сжатия: {p['ratio']} | Цель: {p['target_bits']:,}")
                
                if p['method'] == 'arx':
                    extracted = arx_extract(raw_data, p['target_bits'], p['ratio'])
                else:
                    extracted = hash_extract(raw_data, p['target_bits'], p['method'], p['ratio'])
                    
                extracted_bytes = np.packbits(extracted.reshape(-1, 8), axis=1, bitorder='big').tobytes()
                with open(p['ext_file'], 'wb') as f:
                    f.write(extracted_bytes)
                ui_logger(f"Извлеченные данные сохранены: {os.path.basename(p['ext_file'])}")

            # 4. ТЕСТИРОВАНИЕ
            report_content = ""
            if self._is_running and p.get('run_tests', False):
                report_content = run_nist_custom(
                    extracted, 
                    selected_tests=p.get('selected_tests', []),
                    h_min=h_min,
                    raw_len=len(raw_data),
                    method=p['method'],
                    ratio=p['ratio'],
                    logger=ui_logger
                )
                
                if self._is_running and p.get('save_report', False):
                    with open(p['rep_file'], 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    ui_logger(f"Отчет сохранен: {os.path.basename(p['rep_file'])}")

            if self._is_running:
                self.finished_signal.emit(True, "Процесс успешно завершен!")
            else:
                self.finished_signal.emit(False, "Остановлено пользователем")

        except Exception as e:
            if self._is_running:
                self.log_signal.emit(f"[ERROR] {str(e)}")
                import traceback
                self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(False, str(e))
