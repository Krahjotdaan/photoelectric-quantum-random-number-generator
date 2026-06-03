import numpy as np
from scipy.special import gammaincc


def overlapping_template_test(bits, m=9):
    """
    NIST SP 800-22: 2.8 Overlapping Template Matching Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Overlapping Template Test рекомендуется для последовательностей от 10^6 бит. Получено {n}. Результаты могут быть неточными")
    
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
    
    if np.any(expected < 5):
        print("Предупреждение: Условие применимости хи-квадрат нарушено (ожидаемые частоты < 5). Результаты теста могут быть некорректны")

    chi2_obs = np.sum((nu - expected) ** 2 / (expected + 1e-10))
    p_value = gammaincc(K / 2, chi2_obs / 2)
    
    return p_value
