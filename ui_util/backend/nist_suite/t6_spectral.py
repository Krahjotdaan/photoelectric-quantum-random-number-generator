import math
import numpy as np
from scipy.special import erfc


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
        print(f"Предупреждение: Spectral Test неприменим. Требуется минимум 1000 бит, получено {n}")
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
