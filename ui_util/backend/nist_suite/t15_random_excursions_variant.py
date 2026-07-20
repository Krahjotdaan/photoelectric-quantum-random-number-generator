import math
import numpy as np
from scipy.special import erfc


def random_excursions_variant_test(bits):
    """
    NIST SP 800-22: 2.15 Random Excursions Variant Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Random Excursions Variant Test рекомендуется для последовательностей от 10^6 бит. Получено {n}. Результаты могут быть неточными")

    X = 2 * bits - 1
    S = np.cumsum(X)
    S_prime = np.concatenate([[0], S, [0]])
    
    zero_indices = np.where(S_prime == 0)[0]
    J = len(zero_indices) - 1
    
    if J < 500:
        print(f"Предупреждение: Random Excursions Variant Test неприменим. Требуется минимум 500 циклов, получено {J}")
        return 0.0
    
    states = list(range(-9, 0)) + list(range(1, 10))
    p_values = []
    
    for x in states:
        xi_x = np.sum(S_prime == x)
        numerator = abs(xi_x - J)
        denominator = math.sqrt(J * (4 * abs(x) - 2))
        
        if denominator == 0:
            p_val = 0.0
        else:
            z = numerator / denominator
            p_val = erfc(z / math.sqrt(2))
        p_values.append(p_val)
        
    return (np.array(p_values).mean()) if p_values else 0.0
