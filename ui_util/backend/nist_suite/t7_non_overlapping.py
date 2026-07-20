import numpy as np
from scipy.special import gammaincc


def non_overlapping_template_test(bits, template_str="000000001"):
    """
    NIST SP 800-22: 2.7 Non-overlapping Template Matching Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    m = len(template_str)
    
    M = 1032
    N_blocks = n // M
    
    if N_blocks < 8: 
        print(f"Предупреждение: Non-overlapping Template Test может быть неточным. Получено {N_blocks} блоков при рекомендуемых 8+")
    
    if N_blocks == 0:
        print("Предупреждение: Non-overlapping Template Test неприменим. Недостаточно данных для формирования блоков")
        return 0.0
        
    template = np.array([int(b) for b in template_str], dtype=int)
    
    Wj = [] 
    
    for i in range(N_blocks):
        block_start = i * M
        block_end = block_start + M
        block = bits[block_start:block_end]
        
        count = 0
        pos = 0
        while pos <= M - m:
            if np.array_equal(block[pos:pos+m], template):
                count += 1
                pos += m
            else:
                pos += 1
        Wj.append(count)
    
    Wj = np.array(Wj)
    
    mu = (M - m + 1) / (2 ** m)
    sigma2 = M * ((1 / (2 ** m)) - ((2 * m - 1) / (2 ** (2 * m))))
    
    if sigma2 <= 0:
        print("Предупреждение: Ошибка вычисления дисперсии в Non-overlapping Template Test")
        return 0.0

    chi2_obs = np.sum((Wj - mu) ** 2) / sigma2
    p_value = gammaincc(N_blocks / 2, chi2_obs / 2)
    
    return p_value
