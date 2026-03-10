import math
import numpy as np
from scipy.special import erfc, gammaincc


def spectral_test_corrected(bits):
    """
    Исправленный Спектральный тест (DFT) согласно статье:
    Kim, Umeno, Hasegawa, "Corrections of the NIST Statistical Test Suite for Randomness", 2004.
    https://arxiv.org/pdf/nlin/0401040
    
    Основные изменения:
    1. Уточненный расчет порогового значения T
    2. Использование корректной дисперсии для нормализации отклонения
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000:
        print("Предупреждение: Spectral Test неприменим. Рекомендуется минимум 1000 бит.")
        return 0.0

    X = 2 * bits - 1
    fft_vals = np.fft.fft(X)
    
    half_n = n // 2
    modulus = np.abs(fft_vals[1:half_n]) 
    m = len(modulus)
    
    if m == 0:
        return 0.0

    T = math.sqrt(n * math.log(1 / 0.05))
    
    q = 0.05 
    N1_obs = np.sum(modulus > T)
    N0_exp = m * q
    variance_corrected = m * q * (1.0 - q)
    
    if variance_corrected <= 0:
        return 0.0
        
    sigma_corrected = math.sqrt(variance_corrected)
    z_score = (N1_obs - N0_exp) / sigma_corrected
    p_value = erfc(abs(z_score) / math.sqrt(2))
    
    return p_value


def non_overlapping_template_test(bits, template_str="000000001"):
    """
    NIST SP 800-22: 2.7 Non-overlapping Template Matching Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    m = len(template_str)
    
    M = 1032
    N_blocks = n // M
    
    if N_blocks < 8: 
        print(f"Предупреждение: Non-overlapping Template Test может быть неточным. Получено только {N_blocks} блоков при рекомендуемых 8+")
    
    if N_blocks == 0:
        print("Предупреждение: Non-overlapping Template Test неприменим. Недостаточно данных для формирования блоков")
        return 0.0
        
    template = np.array([int(b) for b in template_str], dtype=int)
    
    Wj = [] 
    
    for i in range(N_blocks):
        block_start = i * M
        block_end = block_start + M
        block = bits[block_start:block_end]
        
        count = 0
        pos = 0
        while pos <= M - m:
            if np.array_equal(block[pos:pos+m], template):
                count += 1
                pos += m
            else:
                pos += 1
        Wj.append(count)
    
    Wj = np.array(Wj)
    
    mu = (M - m + 1) / (2 ** m)
    sigma2 = M * ((1 / (2 ** m)) - ((2 * m - 1) / (2 ** (2 * m))))
    
    if sigma2 <= 0:
        print("Предупреждение: Ошибка вычисления дисперсии в Non-overlapping Template Test")
        return 0.0

    chi2_obs = np.sum((Wj - mu) ** 2) / sigma2
    p_value = gammaincc(N_blocks / 2, chi2_obs / 2)
    
    return p_value


def overlapping_template_test(bits, m=9):
    """
    NIST SP 800-22: 2.8 Overlapping Template Matching Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Overlapping Template Test требует минимум 10^6 бит для надежности. Получено {n}. Результаты могут быть неточными")
    
    M = 1032
    N_blocks_target = 968 
    N_blocks = n // M
    
    if N_blocks < N_blocks_target:
        N_blocks = n // M
        if N_blocks == 0:
            print("Предупреждение: Overlapping Template Test неприменим. Недостаточно данных")
            return 0.0
        
    template = np.ones(m, dtype=int)
    K = 5
    nu = np.zeros(K + 1, dtype=int)
    pi = np.array([0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865])
    
    for i in range(N_blocks):
        block_start = i * M
        block_end = block_start + M
        block = bits[block_start:block_end]
        
        count = 0
        for pos in range(M - m + 1):
            if np.array_equal(block[pos:pos+m], template):
                count += 1
        
        if count >= K:
            nu[K] += 1
        else:
            nu[count] += 1
            
    expected = N_blocks * pi
    
    # Проверка условия N * min(pi) > 5
    if np.any(expected < 5):
        print("Предупреждение: Условие применимости хи-квадрат нарушено (ожидаемые частоты < 5). Результаты теста могут быть некорректны")

    chi2_obs = np.sum((nu - expected) ** 2 / (expected + 1e-10))
    p_value = gammaincc(K / 2, chi2_obs / 2)
    
    return p_value


def maurers_universal_test(bits, L=6):
    """
    NIST SP 800-22: 2.9 Maurer's Universal Statistical Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    # Минимальные требования к длине для разных L
    min_lengths = {
        6: 387840, 7: 904960, 8: 2068480, 9: 4654080, 10: 10342400,
        11: 22753280, 12: 49643520, 13: 107560960, 14: 231669760, 
        15: 496435200, 16: 1059061760
    }
    
    if L not in min_lengths:
        print("Предупреждение: Неверное значение L для Maurer's Test. Должно быть от 6 до 16")
        return 0.0

    required_len = min_lengths[L]
    
    if n < required_len:
        print(f"Предупреждение: Maurer's Universal Test неприменим. Для L={L} требуется минимум {required_len} бит, получено {n}")
        return 0.0
        
    Q = 10 * (2 ** L)
    K = (n // L) - Q
    
    if K <= 0:
        print("Предупреждение: Недостаточно тестовых блоков для Maurer's Test")
        return 0.0
        
    usable_len = (Q + K) * L
    usable_bits = bits[:usable_len]
    
    blocks = []
    for i in range(0, usable_len, L):
        block_val = 0
        for j in range(L):
            block_val = (block_val << 1) | usable_bits[i+j]
        blocks.append(block_val)
        
    init_blocks = blocks[:Q]
    test_blocks = blocks[Q:]
    
    last_pos = [-1] * (2 ** L)
    
    for idx, val in enumerate(init_blocks):
        last_pos[val] = idx + 1
        
    sum_log_dist = 0.0
    
    for idx, val in enumerate(test_blocks):
        current_idx = Q + idx + 1
        
        if last_pos[val] != -1:
            dist = current_idx - last_pos[val]
            sum_log_dist += math.log2(dist)
        last_pos[val] = current_idx
        
    fn = sum_log_dist / K
    
    expected_values = {
        6: 5.2177052, 7: 6.1962507, 8: 7.1836656, 9: 8.1764248, 10: 9.1723243,
        11: 10.170032, 12: 11.168765, 13: 12.168070, 14: 13.167693, 15: 14.167488, 16: 15.167379
    }
    variances = {
        6: 2.954, 7: 3.125, 8: 3.238, 9: 3.311, 10: 3.356,
        11: 3.384, 12: 3.401, 13: 3.410, 14: 3.416, 15: 3.419, 16: 3.421
    }
        
    E_L = expected_values[L]
    Var_L = variances[L]
    z_score = abs(fn - E_L) / math.sqrt(Var_L / K)
    p_value = erfc(z_score / math.sqrt(2))
    
    return p_value


def linear_complexity_test(bits, M=500):
    """
    NIST SP 800-22: 2.10 Linear Complexity Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Linear Complexity Test рекомендуется для последовательностей от 10^6 бит. Получено {n}")

    N_blocks = n // M
    
    if N_blocks < 200:
        print(f"Предупреждение: Linear Complexity Test требует минимум 200 блоков (N>=200) для достоверности хи-квадрат. Получено {N_blocks}")
    
    if N_blocks == 0:
        print("Предупреждение: Linear Complexity Test неприменим. Длина блока M больше длины последовательности")
        return 0.0
        
    pi = np.array([0.010417, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833])
    K_degrees = 6
    
    nu = np.zeros(K_degrees + 1, dtype=int)

    def berlekamp_massey(s):
        n_len = len(s)
        C = [0] * n_len
        B = [0] * n_len
        C[0] = 1
        B[0] = 1
        L = 0
        m = 1
        
        for i in range(n_len):
            d = s[i]
            for j in range(1, L + 1):
                d ^= (C[j] & s[i-j])
                
            if d == 1:
                T = C[:]
                for j in range(n_len - m):
                    if j < n_len:
                        C[j + m] ^= B[j]
                
                if 2 * L <= i:
                    L = i + 1 - L
                    B = T
                    m = 1
                else:
                    m += 1
            else:
                m += 1
                
        return L
    
    for i in range(N_blocks):
        block = bits[i*M : (i+1)*M]
        L = berlekamp_massey(block)
        
        mu = (M / 2.0) + (9.0 + ((-1) ** (M + 1))) / 36.0 - (1.0 / (2 ** M))
        Ti = ((-1) ** M) * (L - mu) + (2.0 / 9.0)
        
        if Ti <= -2.5:
            nu[0] += 1
        elif -2.5 < Ti <= -1.5:
            nu[1] += 1
        elif -1.5 < Ti <= -0.5:
            nu[2] += 1
        elif -0.5 < Ti <= 0.5:
            nu[3] += 1
        elif 0.5 < Ti <= 1.5:
            nu[4] += 1
        elif 1.5 < Ti <= 2.5:
            nu[5] += 1
        else: 
            nu[6] += 1
            
    expected = N_blocks * pi
    chi2_obs = np.sum((nu - expected) ** 2 / (expected + 1e-10))
    p_value = gammaincc(K_degrees / 2, chi2_obs / 2)
    
    return p_value
