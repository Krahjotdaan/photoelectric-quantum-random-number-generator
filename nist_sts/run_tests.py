import numpy as np
from nist_sts.tests1_5 import *
from nist_sts.tests6_10 import *
from nist_sts.tests11_15 import *


def run_tests(bits):
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    print(f"Длина последовательности: {n} бит")
    mean = bits.mean()
    print(f"Распределение: {mean:.4f} (1) / {1 - mean:.4f} (0)")
    print("-" * 70)
    print(f"{'Название теста':<45} | {'P-value':<10} | {'Статус'}")
    print("-" * 70)

    results_summary = []
    passed_count = 0
    total_executed = 0
    alpha = 0.01

    def log_test_result(name, p_val, flag):
        nonlocal passed_count, total_executed
        if p_val is None:
            status = "Пропущен"
            print(f"{name:<45} | {'N/A':<10} | {status}")
        else:
            total_executed += 1
            if flag:
                passed_count += 1
                status = "Пройден"
            else:
                status = "Не пройден"
            print(f"{name:<45} | {p_val:<10.6f} | {status}")
        results_summary.append((name, p_val, flag))

    # 1. Frequency (Monobit) Test
    try:
        p_val = frequency_monobit_test(bits)
        log_test_result("1. Frequency (Monobit) Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("1. Frequency (Monobit) Test", 0.0, False)

    # 2. Frequency Test within a Block
    try:
        M = 128 if n >= 12800 else max(20, int(0.01 * n))
        p_val = frequency_block_test(bits, M)
        log_test_result("2. Block Frequency Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("2. Block Frequency Test", 0.0, False)

    # 3. Runs Test
    try:
        p_val = runs_test(bits)
        log_test_result("3. Runs Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("3. Runs Test", 0.0, False)

    # 4. Longest Run of Ones in a Block
    try:
        p_val = longest_run_ones_in_block(bits)
        log_test_result("4. Longest Run of Ones in a Block", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("4. Longest Run of Ones in a Block", 0.0, False)

    # 5. Binary Matrix Rank Test
    try:
        p_val = binary_matrix_rank_test(bits)
        log_test_result("5. Binary Matrix Rank Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("5. Binary Matrix Rank Test", 0.0, False)

    # 6. Discrete Fourier Transform (Spectral) Test
    try:
        p_val = spectral_test_corrected(bits)
        log_test_result("6. Spectral (DFT) Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("6. Spectral (DFT) Test", 0.0, False)

    # 7. Non-overlapping Template Matching Test (Множественный запуск)
    try:
        templates = [
            "000000001", "000000011", "000000101", "000000111", "000001001", 
            "000001011", "000001101", "000001111", "000010001", "000010011",
            "000010101", "000010111", "000011001", "000011011", "000011101",
            "000011111", "000100001", "000100011", "000100101", "000100111"
        ]
        p_vals_7 = []
        for tmpl in templates:
            pv = non_overlapping_template_test(bits, template_str=tmpl)
            p_vals_7.append(pv)
        
        mean_p = np.array(p_vals_7, dtype=float).mean() if p_vals_7 else 0.0
        log_test_result("7. Non-overlapping Template (mean P)", mean_p, mean_p >= alpha)
    except Exception: 
        log_test_result("7. Non-overlapping Template", 0.0, False)

    # 8. Overlapping Template Matching Test
    try:
        p_val = overlapping_template_test(bits, m=9)
        log_test_result("8. Overlapping Template Matching (m=9)", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("8. Overlapping Template Matching", 0.0, False)

    # 9. Maurer's "Universal Statistical" Test
    try:
        if n > 380000:
            p_val = maurers_universal_test(bits, L=6)
            log_test_result("9. Maurer's Universal Test (L=6)", p_val, p_val >= alpha)
        else:
            log_test_result("9. Maurer's Universal Test", None, False)
    except Exception: 
        log_test_result("9. Maurer's Universal Test", 0.0, False)

    # 10. Linear Complexity Test
    try:
        if n > 100000:
            p_val = linear_complexity_test(bits, M=500)
            log_test_result("10. Linear Complexity Test", p_val, p_val >= alpha)
        else:
             log_test_result("10. Linear Complexity Test", None, False)
    except Exception: 
        log_test_result("10. Linear Complexity Test", 0.0, False)

    # 11. Serial Test
    try:
        m_ser = 2
        if n > 10000: m_ser = 3
        if n > 100000: m_ser = 4
        
        p_val = serial_test(bits, m=m_ser) 
        log_test_result(f"11. Serial Test (m={m_ser})", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("11. Serial Test", 0.0, False)

    # 12. Approximate Entropy Test
    try:
        m_apen = 2
        if n > 10000: m_apen = 3
        if n > 100000: m_apen = 4
        
        p_val = approximate_entropy_test(bits, m=m_apen)
        log_test_result(f"12. Approximate Entropy Test (m={m_apen})", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("12. Approximate Entropy Test", 0.0, False)

    # 13. Cumulative Sums (Cusum) Test
    try:
        p_val = cusum_test(bits)
        log_test_result("13. Cumulative Sums (Cusum) Test", p_val, p_val >= alpha)
    except Exception: 
        log_test_result("13. Cumulative Sums (Cusum) Test", 0.0, False)

    # 14. Random Excursions Test
    try:
        if n > 500000:
            p_val = random_excursions_test(bits)
            log_test_result("14. Random Excursions Test (mean P)", p_val, p_val >= alpha)
        else:
            log_test_result("14. Random Excursions Test", None, False)
    except Exception: 
        log_test_result("14. Random Excursions Test", 0.0, False)

    # 15. Random Excursions Variant Test
    try:
        if n > 500000:
            p_val = random_excursions_variant_test(bits)
            log_test_result("15. Random Excursions Variant Test", p_val, p_val >= alpha)
        else:
            log_test_result("15. Random Excursions Variant Test", None, False)
    except Exception: 
        log_test_result("15. Random Excursions Variant Test", 0.0, False)

    print("-" * 70)
    print(f"ИТОГО: Пройдено {passed_count} из {total_executed} выполненных тестов.")
