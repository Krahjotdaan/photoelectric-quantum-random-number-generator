import numpy as np
from scipy.stats import chisquare, kstest


def chi_square_byte_test(bits):
    """Проверка равномерности распределения байт"""
    n_bytes = len(bits) // 8
    if n_bytes == 0: return 0.0
    
    usable_bits = bits[:n_bytes * 8].reshape(n_bytes, 8)
    bytes_arr = np.packbits(usable_bits, axis=1, bitorder='big').ravel()
    
    counts = np.bincount(bytes_arr, minlength=256)
    expected = n_bytes / 256
    
    chi2, p_val = chisquare(counts, f_exp=[expected] * 256)

    return p_val


def autocorrelation_test(bits, max_lag=100):
    """Проверка автокорреляции"""
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    X = 2 * bits - 1
    
    acf_values = []
    for k in range(1, max_lag + 1):
        autocorr = np.dot(X[:n-k], X[k:]) / n
        acf_values.append(autocorr)
        
    z_scores = np.array(acf_values) * np.sqrt(n)
    ks_stat, p_val = kstest(z_scores, 'norm')

    return p_val
