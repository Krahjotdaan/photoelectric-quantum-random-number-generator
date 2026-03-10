import math
import numpy as np
from scipy.special import gammaincc


def frequency_monobit_test(bits):
    """
    NIST SP 800-22: 2.1 Frequency (Monobit) Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 100:
        print("Предупреждение: Frequency Test неприменим. Требуется минимум 100 бит.")
        return 0.0

    xi = 2 * bits - 1
    Sn = np.sum(xi)

    s_obs = abs(Sn) / np.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2))

    return p_value


def frequency_block_test(bits, M):
    """
    NIST SP 800-22: 2.2 Frequency Test within a Block
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 100:
        print("Предупреждение: Block Frequency Test неприменим. Требуется минимум 100 бит.")
        return 0.0

    if M > n:
        print("Предупреждение: Block Frequency Test неприменим. Размер блока M больше длины последовательности.")
        return 0.0
    
    # Рекомендация: M >= 20, M > 0.01*n, N < 100
    if M < 20:
        print("Предупреждение: Размер блока M меньше рекомендованных 20 бит.")
    
    N = n // M
    if N == 0:
        print("Предупреждение: Недостаточно данных для формирования блоков.")
        return 0.0

    blocks = bits[:N * M].reshape(N, M)
    pi = blocks.sum(axis=1) / M

    chi2_obs = 4 * M * np.sum((pi - 0.5) ** 2)
    p_value = gammaincc(N / 2, chi2_obs / 2)

    return p_value


def runs_test(bits):
    """
    NIST SP 800-22: 2.3 Runs Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 100:
        print("Предупреждение: Runs Test неприменим. Требуется минимум 100 бит")
        return 0.0

    pi = np.mean(bits)

    tau = 2 / np.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return 0.0

    r = (bits[:-1] != bits[1:]).astype(int)
    Vn_obs = np.sum(r) + 1

    numerator = abs(Vn_obs - 2 * n * pi * (1 - pi))
    denominator = 2 * np.sqrt(2 * n) * pi * (1 - pi)

    if denominator == 0:
        return 0.0
        
    p_value = math.erfc(numerator / denominator)

    return p_value


def longest_run_ones_in_block(bits):
    """
    NIST SP 800-22: 2.4 Test for the Longest Run of Ones in a Block
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n >= 750_000:
        M, K, N = 10_000, 6, 75
        bounds = [10, 11, 12, 13, 14, 15]
        pi = np.array([0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727])
    elif n >= 6272:
        M, K, N = 128, 5, 49
        bounds = [4, 5, 6, 7, 8]
        pi = np.array([0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124])
    elif n >= 128:
        M, K, N = 8, 3, 16
        bounds = [1, 2, 3]
        pi = np.array([0.2148, 0.3672, 0.2305, 0.1875])
    else:
        print("Предупреждение: Longest Run of Ones Test неприменим. Требуется минимум 128 бит")
        return 0.0

    if n < N * M:
        print(f"Предупреждение: Longest Run of Ones Test неприменим. Для выбранных параметров требуется минимум {N * M} бит, получено {n}")
        return 0.0

    usable_bits = bits[:N * M]
    blocks = usable_bits.reshape(N, M)

    def longest_run_of_ones(block):
        max_run = current = 0
        for b in block:
            if b == 1:
                current += 1
                if current > max_run:
                    max_run = current
            else:
                current = 0
        return max_run

    longest_runs = np.array([longest_run_of_ones(block) for block in blocks])

    nu = np.zeros(K + 1, dtype=int)
    for run_len in longest_runs:
        assigned = False
        for i, b in enumerate(bounds):
            if run_len <= b:
                nu[i] += 1
                assigned = True
                break
        if not assigned:
            nu[-1] += 1

    nu = nu.astype(float)
    expected = N * pi

    chi2_obs = np.sum((nu - expected) ** 2 / (expected + 1e-12))
    p_value = gammaincc(K / 2, chi2_obs / 2)

    return p_value


def binary_matrix_rank_test(bits):
    """
    NIST SP 800-22: 2.5 Binary Matrix Rank Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    M = 32
    Q = 32
    
    # Требуется минимум 38 матриц для статистической значимости
    min_bits = 38 * M * Q 
    
    if n < min_bits:
        print(f"Предупреждение: Binary Matrix Rank Test неприменим. Требуется минимум {min_bits} бит (38 матриц 32x32), получено {n}")
        return 0.0
        
    N_blocks = n // (M * Q)
    
    p_full = 0.2887880951
    p_full_minus_1 = 0.5775761902
    p_others = 1.0 - p_full - p_full_minus_1
    
    probs = np.array([p_full, p_full_minus_1, p_others])
    counts = np.zeros(3, dtype=int)
    
    for i in range(N_blocks):
        start_idx = i * M * Q
        block_bits = bits[start_idx : start_idx + M * Q]
        matrix = block_bits.reshape(M, Q)

        def compute_rank_gf2(matrix):
            rows, cols = matrix.shape
            r = 0
            for c in range(cols):
                if r >= rows:
                    break
                pivot_row = None
                for i in range(r, rows):
                    if matrix[i, c] == 1:
                        pivot_row = i
                        break
                
                if pivot_row is None:
                    continue
                    
                if pivot_row != r:
                    matrix[[r, pivot_row]] = matrix[[pivot_row, r]]
                    
                for i in range(rows):
                    if i != r and matrix[i, c] == 1:
                        matrix[i] = (matrix[i] + matrix[r]) % 2
                r += 1

            return r

        rank = compute_rank_gf2(matrix.copy())
        
        if rank == M:
            counts[0] += 1
        elif rank == M - 1:
            counts[1] += 1
        else:
            counts[2] += 1
            
    expected = N_blocks * probs
    chi2_obs = np.sum((counts - expected) ** 2 / (expected + 1e-10))
    
    p_value = gammaincc(2 / 2, chi2_obs / 2)
    
    return p_value
