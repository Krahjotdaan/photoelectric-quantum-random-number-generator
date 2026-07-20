import numpy as np
from scipy.stats import norm


def cusum_test(bits):
    """
    NIST SP 800-22: 2.13 Cumulative Sums (Cusum) Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 100:
        print("Предупреждение: Cusum Test неприменим. Требуется минимум 100 бит")
        return 0.0

    X = 2 * bits - 1
    
    def calculate_p_value(sequence):
        S = np.cumsum(sequence)
        z = np.max(np.abs(S))
        
        if z == 0:
            return 1.0
            
        k_start = int(np.floor((-n / z + 1) / 4))
        k_end = int(np.floor((n / z - 1) / 4))
        
        sum_val = 0.0
        for k in range(k_start, k_end + 1):
            term1 = norm.cdf((4 * k + 1) * z / np.sqrt(n))
            term2 = norm.cdf((4 * k - 1) * z / np.sqrt(n))
            sum_val += (term1 - term2)
            
        k_start_2 = int(np.floor((-n / z - 3) / 4))
        k_end_2 = int(np.floor((n / z - 1) / 4))
        
        for k in range(k_start_2, k_end_2 + 1):
            term1 = norm.cdf((4 * k + 3) * z / np.sqrt(n))
            term2 = norm.cdf((4 * k + 1) * z / np.sqrt(n))
            sum_val -= (term1 - term2)
            
        p_val = 1.0 - sum_val
        return max(0.0, min(1.0, p_val)) 

    p_forward = calculate_p_value(X)
    p_backward = calculate_p_value(X[::-1])
    p_value = min(p_forward, p_backward)

    return p_value
