import numpy as np
from scipy.special import gammaincc


def frequency_block_test(bits, M):
    """
    NIST SP 800-22: 2.2 Frequency Test within a Block
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 100:
        print("Предупреждение: Block Frequency Test неприменим. Требуется минимум 100 бит")
        return 0.0

    if M > n:
        print("Предупреждение: Block Frequency Test неприменим. Размер блока M больше длины последовательности")
        return 0.0
    
    # Рекомендация: M >= 20, M > 0.01*n, N < 100
    if M < 20:
        print("Предупреждение: Размер блока M меньше рекомендованных 20 бит")
    
    N = n // M
    if N == 0:
        print("Предупреждение: Недостаточно данных для формирования блоков")
        return 0.0

    blocks = bits[:N * M].reshape(N, M)
    pi = blocks.sum(axis=1) / M

    chi2_obs = 4 * M * np.sum((pi - 0.5) ** 2)
    p_value = gammaincc(N / 2, chi2_obs / 2)

    return p_value
