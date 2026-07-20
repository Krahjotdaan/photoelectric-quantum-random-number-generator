import math
import numpy as np


def frequency_monobit_test(bits):
    """
    NIST SP 800-22: 2.1 Frequency (Monobit) Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 100:
        print("Предупреждение: Frequency Test неприменим. Требуется минимум 100 бит")
        return 0.0

    xi = 2 * bits - 1
    Sn = np.sum(xi)

    s_obs = abs(Sn) / np.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2))

    return p_value
