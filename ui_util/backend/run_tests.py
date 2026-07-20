import numpy as np

from backend.nist_suite.t1_frequency import frequency_monobit_test
from backend.nist_suite.t2_frequency_within_block import frequency_block_test
from backend.nist_suite.t3_runs import runs_test
from backend.nist_suite.t4_longest_run import longest_run_ones_in_block
from backend.nist_suite.t5_binary_matrix_rank import binary_matrix_rank_test
from backend.nist_suite.t6_spectral import spectral_test_corrected
from backend.nist_suite.t7_non_overlapping import non_overlapping_template_test
from backend.nist_suite.t8_overlapping import overlapping_template_test
from backend.nist_suite.t9_maurer import maurers_universal_test
from backend.nist_suite.t10_linear_complexity import linear_complexity_test
from backend.nist_suite.t11_serial import serial_test
from backend.nist_suite.t12_approximate_entropy import approximate_entropy_test
from backend.nist_suite.t13_cumulative_sums import cusum_test
from backend.nist_suite.t14_random_excursions import random_excursions_test
from backend.nist_suite.t15_random_excursions_variant import random_excursions_variant_test
from backend.additional_suite.additional_stats import chi_square_byte_test, autocorrelation_test


def run_nist_custom(bits, selected_tests=None, h_min=None,
                    raw_len=None, method=None, ratio=None, logger=None):
    """
    Запуск выбранных тестов NIST + доп. метрик.
    Возвращает строку с форматированным отчетом.
    """
    def log(msg):
        if logger: logger(msg)
        else: print(msg)

    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    alpha = 0.01
    
    if not selected_tests:
        selected_tests = [f"{i}. {name}" for i, name in enumerate([
            "Frequency (Monobit)", "Block Frequency", "Runs",
            "Longest Run of Ones", "Binary Matrix Rank", "Spectral (DFT)",
            "Non-overlapping Template", "Overlapping Template", "Maurer's Universal",
            "Linear Complexity", "Serial Test", "Approximate Entropy",
            "Cumulative Sums", "Random Excursions", "Random Excursions Variant",
            "Chi Square Byte", "Autocorrelation"
        ], 1)]

    report_lines = []
    passed_count = 0
    total_executed = 0

    def add_line(text):
        report_lines.append(text)
        log(text)

    def log_test_result(name, p_val, flag):
        nonlocal passed_count, total_executed
        if p_val is None:
            status = "Пропущен"
            line = f"{name:<45} | {'N/A':<10} | {status}"
        else:
            total_executed += 1
            if flag:
                passed_count += 1
                status = "Пройден"
            else:
                status = "Не пройден"
            line = f"{name:<45} | {p_val:<10.6f} | {status}"
        add_line(line)

    add_line('\n' + "=" * 70)
    add_line("ОТЧЕТ О ТЕСТИРОВАНИИ")
    add_line("=" * 70)
    if raw_len is not None:
        add_line(f"Исходная последовательность: {raw_len:,} отсчетов АЦП")
    if h_min is not None:
        add_line(f"Мин-энтропия источника: {h_min:.4f} бит/бит")
    if method:
        add_line(f"Метод экстракции: {method} | Коэффициент сжатия: {ratio}")
        
    add_line(f"\nДлина тестируемой последовательности: {n:,} бит")
    mean = bits.mean()
    add_line(f"Распределение: {mean:.4f} (1) / {1-mean:.4f} (0)")
    
    add_line("-" * 70)
    add_line(f"{'Название теста':<45} | {'P-value':<10} | {'Статус'}")
    add_line("-" * 70)

    test_map = {
        "1. Frequency (Monobit)": lambda: frequency_monobit_test(bits),
        "2. Block Frequency": lambda: frequency_block_test(bits, 128 if n >= 12800 else max(20, int(0.01*n))),
        "3. Runs": lambda: runs_test(bits),
        "4. Longest Run of Ones": lambda: longest_run_ones_in_block(bits),
        "5. Binary Matrix Rank": lambda: binary_matrix_rank_test(bits),
        "6. Spectral (DFT)": lambda: spectral_test_corrected(bits),
        "7. Non-overlapping Template": lambda: _non_overlapping_mean(bits),
        "8. Overlapping Template": lambda: overlapping_template_test(bits, m=9),
        "9. Maurer's Universal": lambda: maurers_universal_test(bits),
        "10. Linear Complexity": lambda: linear_complexity_test(bits, M=500),
        "11. Serial Test": lambda: serial_test(bits, m=4 if n > 100000 else (3 if n > 10000 else 2)),
        "12. Approximate Entropy": lambda: approximate_entropy_test(bits, m=4 if n > 100000 else (3 if n > 10000 else 2)),
        "13. Cumulative Sums": lambda: cusum_test(bits),
        "14. Random Excursions": lambda: random_excursions_test(bits),
        "15. Random Excursions Variant": lambda: random_excursions_variant_test(bits),
        "1 Additional. Chi Square Byte": lambda: chi_square_byte_test(bits),
        "2 Additional. Autocorrelation": lambda: autocorrelation_test(bits),
    }

    def _non_overlapping_mean(b):
        templates = [
            "000000001", "000000011", "000000101", "000000111", "000001001",
            "000001011", "000001101", "000001111", "000010001", "000010011",
            "000010101", "000010111", "000011001", "000011011", "000011101",
            "000011111", "000100001", "000100011", "000100101", "000100111"
        ]
        p_vals = []
        for tmpl in templates:
            pv = non_overlapping_template_test(b, template_str=tmpl)
            p_vals.append(pv)
        return np.array(p_vals, dtype=float).mean() if p_vals else 0.0

    for test_name_ui in selected_tests:
        matched_func = None
        display_name = test_name_ui
        
        for key, func in test_map.items():
            if key in test_name_ui or test_name_ui.startswith(key.split(". ")[1]):
                matched_func = func
                display_name = test_name_ui
                break
                
        if matched_func is None:
            num = test_name_ui.split(".")[0].strip()
            for key, func in test_map.items():
                if key.startswith(num + "."):
                    matched_func = func
                    display_name = key
                    break

        if matched_func:
            try:
                p_val = matched_func()
                log_test_result(display_name, p_val, p_val >= alpha)
            except Exception as e:
                log_test_result(display_name, 0.0, False)
                add_line(f"  ─ Ошибка: {str(e)[:80]}")
        else:
            add_line(f"Тест '{test_name_ui}' не найден в маппинге")

    add_line("-" * 70)
    add_line(f"ИТОГО: Пройдено {passed_count} из {total_executed} выполненных тестов.")
    add_line("=" * 70)

    return "\n".join(report_lines)
