import os
import serial.tools.list_ports
from PyQt6.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout,  
                             QPushButton, QComboBox, QTextEdit, QProgressBar, 
                             QFileDialog, QGroupBox, QFormLayout, QLineEdit, 
                             QCheckBox, QSpinBox, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config_manager import load_config, save_config, get_next_filenames, increment_counter
from qrng_worker import QrngWorker


class MainWindow(QWidget):
    TESTS_LIST = [
        "1. Frequency (Monobit)", "2. Block Frequency", "3. Runs",
        "4. Longest Run of Ones", "5. Binary Matrix Rank", "6. Spectral (DFT)",
        "7. Non-overlapping Template", "8. Overlapping Template", "9. Maurer's Universal",
        "10. Linear Complexity", "11. Serial Test", "12. Approximate Entropy",
        "13. Cumulative Sums", "14. Random Excursions", "15. Random Excursions Variant",
        "1 Additional. Chi Square Byte", "2 Additional. Autocorrelation"
    ]

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.worker = None
        self.refresh_ports()
        self.METHOD = ["arx", "sha_256", "sha3_256", "sha_512", "sha3_512", "blake2s", "blake2b", "streebog256", "streebog512"]
        self.METHODS_NAMES = ["ARX", "SHA-256", "SHA3-256", "SHA-512", "SHA3-512", "Blake2s (256 bits)", "Blake2b (512 bits)", "Стрибог-256", "Стрибог-512"]
        self.METHODS = dict(zip(self.METHODS_NAMES, self.METHOD))
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("QRNG Utility v1.0")
        self.resize(1100, 800)
        
        main_layout = QHBoxLayout(self)
        
        # === ЛЕВАЯ ПАНЕЛЬ ===
        left_panel = QWidget()
        left_panel.setFixedWidth(450)
        left_layout = QVBoxLayout(left_panel)
        
        # 1. ЭКСТРАКЦИЯ 
        grp_ext = QGroupBox("Экстракция")
        frm_ext = QFormLayout(grp_ext)
        
        self.spn_target = QSpinBox()
        self.spn_target.setRange(100000, 100000000)
        self.spn_target.setSingleStep(200000)
        self.spn_target.setValue(1000000)
        
        self.spn_ratio = QSpinBox()
        self.spn_ratio.setRange(2, 16)
        self.spn_ratio.setValue(2)
        
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(self.METHODS_NAMES)
        
        frm_ext.addRow("Целевые биты:", self.spn_target)
        frm_ext.addRow("Коэф. сжатия:", self.spn_ratio)
        frm_ext.addRow("Метод:", self.cmb_method)
        left_layout.addWidget(grp_ext)
        
        # 2. ТЕСТИРОВАНИЕ 
        grp_tests = QGroupBox("Тестирование")
        vlay_tests = QVBoxLayout(grp_tests)
        
        self.chk_all_tests = QCheckBox("Выбрать все")
        self.chk_all_tests.setChecked(True)
        self.chk_all_tests.stateChanged.connect(self.toggle_all_tests)
        vlay_tests.addWidget(self.chk_all_tests)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        
        scroll_wid = QWidget()
        scroll_vlay = QVBoxLayout(scroll_wid)
        scroll_vlay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.test_checkboxes = []
        for t in self.TESTS_LIST:
            cb = QCheckBox(t)
            cb.setChecked(True)
            self.test_checkboxes.append(cb)
            scroll_vlay.addWidget(cb)
            
        scroll.setWidget(scroll_wid)
        vlay_tests.addWidget(scroll)
        left_layout.addWidget(grp_tests)
        
        # 3. ПУТИ СОХРАНЕНИЯ
        grp_paths = QGroupBox("Пути сохранения")
        frm_paths = QFormLayout(grp_paths)
        self.paths = {}
        for key, label in [("raw_path", "Сырые:"), ("extracted_path", "Извлеченные:"), ("report_path", "Отчеты:")]:
            line = QLineEdit(self.config.get(key, ""))
            btn = QPushButton("Обзор")
            btn.clicked.connect(lambda checked, l=line, k=key: self.browse_folder(l, k))
            row = QHBoxLayout()
            row.addWidget(line)
            row.addWidget(btn)
            frm_paths.addRow(label, row)
            self.paths[key] = line
        left_layout.addWidget(grp_paths)
        
        # 4. ОПЦИИ И КНОПКИ
        self.chk_test = QCheckBox("Тестировать после экстракции")
        self.chk_test.setChecked(True)
        self.chk_report = QCheckBox("Сохранять отчет")
        self.chk_report.setChecked(True)
        self.chk_overwrite = QCheckBox("Перезаписывать существующие файлы")
        
        left_layout.addWidget(self.chk_test)
        left_layout.addWidget(self.chk_report)
        left_layout.addWidget(self.chk_overwrite)
        
        # Кнопки управления
        btns_row = QHBoxLayout()
        self.btn_run = QPushButton("Запуск генерации")
        self.btn_run.setStyleSheet("""
            QPushButton { 
                font-weight: bold; padding: 12px; 
                background-color: #4CAF50; color: white; border-radius: 4px; 
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #555; color: #888; }
        """)
        self.btn_run.clicked.connect(self.start_process)
        
        self.btn_stop = QPushButton("СТОП")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_process)
        
        self.btn_clear_log = QPushButton("Очистить лог")
        self.btn_clear_log.clicked.connect(self.clear_log)
        
        btns_row.addWidget(self.btn_run, stretch=2)
        btns_row.addWidget(self.btn_stop, stretch=1)
        btns_row.addWidget(self.btn_clear_log, stretch=1)
        
        left_layout.addLayout(btns_row)
        left_layout.addStretch() 
        
        main_layout.addWidget(left_panel)
        
        # === ПРАВАЯ ПАНЕЛЬ (ЛОГ) ===
        right_panel = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setPlaceholderText("Здесь будет отображаться ход выполнения процесса...")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self._last_was_progress = False

        right_panel.addWidget(self.log_view)
        right_panel.addWidget(self.progress_bar)
        main_layout.addLayout(right_panel)

    def toggle_all_tests(self, state):
        checked = state == 2
        for cb in self.test_checkboxes:
            cb.setChecked(checked)

    def browse_folder(self, line_edit, config_key):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку", line_edit.text())
        if folder:
            line_edit.setText(folder)
            self.config[config_key] = folder
            save_config(self.config)

    def refresh_ports(self):
        """Автоопределение доступных COM-портов"""
        ports = serial.tools.list_ports.comports()
        self.detected_port = None
        
        for p in ports:
            desc_lower = p.description.lower()
            dev_lower = p.device.lower()
            if 'arduino' in desc_lower or 'usb serial' in desc_lower or 'com5' in dev_lower or 'com3' in dev_lower:
                self.detected_port = p.device
                break
                
        if not self.detected_port and ports:
            for p in ports:
                if 'usb' in p.description.lower():
                    self.detected_port = p.device
                    break
                    
        if not self.detected_port and ports:
            self.detected_port = ports[0].device
            
        if not self.detected_port:
            self.detected_port = "COM3"

    def log(self, msg):
        self._last_was_progress = False
        self.log_view.append(msg)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_progress_line(self, msg):
        cursor = self.log_view.textCursor()
        
        if not hasattr(self, '_last_was_progress') or not self._last_was_progress:
            self.log_view.append("") 
            cursor.movePosition(cursor.MoveOperation.End)
            
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        
        cursor.insertText(msg)
        
        self._last_was_progress = True
        
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_log(self):
        reply = QMessageBox.question(
            self, "Очистка лога", 
            "Вы действительно хотите очистить журнал событий?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_view.clear()

    def start_process(self):
        method = self.METHODS[self.cmb_method.currentText()]
        raw_f, ext_f, rep_f = get_next_filenames(self.config, method)
        
        # Проверка перезаписи
        if not self.chk_overwrite.isChecked():
            existing = []
            if os.path.exists(raw_f): existing.append(os.path.basename(raw_f))
            if os.path.exists(ext_f): existing.append(os.path.basename(ext_f))
            if os.path.exists(rep_f): existing.append(os.path.basename(rep_f))
            if existing:
                reply = QMessageBox.question(self, "Файлы существуют", 
                    f"Следующие файлы уже существуют:\n{', '.join(existing)}\n\nПерезаписать?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
        
        for path in [raw_f, ext_f, rep_f]:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
        selected_tests = [cb.text() for cb in self.test_checkboxes if cb.isChecked()]
        
        target_bits = self.spn_target.value()
        ratio = self.spn_ratio.value()
        samples_needed = int(target_bits * ratio * 1.01)
        
        params = {
            'samples': samples_needed,
            'port': self.detected_port, 
            'baud_rate': 2000000,
            'method': method,
            'ratio': ratio,
            'target_bits': target_bits,
            'raw_file': raw_f,
            'ext_file': ext_f,
            'rep_file': rep_f,
            'run_tests': self.chk_test.isChecked(),
            'save_report': self.chk_report.isChecked(),
            'selected_tests': selected_tests
        }
        
        self.log(f"\nЗапуск процесса. Порт: {self.detected_port}")
        
        self.worker = QrngWorker(params)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress_line)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) 

    def stop_process(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log("Процесс остановлен пользователем.")

    def on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.config = increment_counter(self.config)
            self.log(f"\n{msg}")
        else:
            self.log(f"\n{msg}")
