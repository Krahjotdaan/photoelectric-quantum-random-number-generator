import numpy as np
from scipy.special import gammaincc


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
        print(f"Предупреждение: Longest Run of Ones Test неприменим. Требуется минимум 128 бит, получено {n}")
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
