import math
import numpy as np


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
