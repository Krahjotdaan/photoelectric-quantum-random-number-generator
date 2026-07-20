import math
import numpy as np
from scipy.special import erfc


def maurers_universal_test(bits):
    """
    NIST SP 800-22: 2.9 Maurer's Universal Statistical Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)

    if n < 387840:
        print(f"Предупреждение: Maurer's Universal Test неприменим. Требуется минимум 387840 бит, получено {n}")
        return 0.0
    
    min_lengths = {
        6: 387840, 7: 904960, 8: 2068480, 9: 4654080, 10: 10342400,
        11: 22753280, 12: 49643520, 13: 107560960, 14: 231669760, 
        15: 496435200, 16: 1059061760
    }

    idx = np.searchsorted(list(min_lengths.values()), n, side='right')
    L = int(list(min_lengths.keys())[idx - 1])
        
    Q = 10 * (2 ** L)
    K = (n // L) - Q
    
    if K <= 0:
        print("Предупреждение: Недостаточно тестовых блоков для Maurer's Test")
        return 0.0
        
    usable_len = (Q + K) * L
    usable_bits = bits[:usable_len]
    
    blocks = []
    for i in range(0, usable_len, L):
        block_val = 0
        for j in range(L):
            block_val = (block_val << 1) | usable_bits[i+j]
        blocks.append(block_val)
        
    init_blocks = blocks[:Q]
    test_blocks = blocks[Q:]
    
    last_pos = [-1] * (2 ** L)
    
    for idx, val in enumerate(init_blocks):
        last_pos[val] = idx + 1
        
    sum_log_dist = 0.0
    
    for idx, val in enumerate(test_blocks):
        current_idx = Q + idx + 1
        
        if last_pos[val] != -1:
            dist = current_idx - last_pos[val]
            sum_log_dist += math.log2(dist)
        last_pos[val] = current_idx
        
    fn = sum_log_dist / K
    
    expected_values = {
        6: 5.2177052, 7: 6.1962507, 8: 7.1836656, 9: 8.1764248, 10: 9.1723243,
        11: 10.170032, 12: 11.168765, 13: 12.168070, 14: 13.167693, 15: 14.167488, 16: 15.167379
    }
    variances = {
        6: 2.954, 7: 3.125, 8: 3.238, 9: 3.311, 10: 3.356,
        11: 3.384, 12: 3.401, 13: 3.410, 14: 3.416, 15: 3.419, 16: 3.421
    }
        
    E_L = expected_values[L]
    Var_L = variances[L]
    z_score = abs(fn - E_L) / math.sqrt(Var_L / K)
    p_value = erfc(z_score / math.sqrt(2))
    
    return p_value
    