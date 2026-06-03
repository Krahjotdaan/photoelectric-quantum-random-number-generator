import numpy as np
from scipy.special import gammaincc


def serial_test(bits, m=2):
    """
    NIST SP 800-22: 2.11 Serial Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    max_m = int(np.floor(np.log2(n))) - 2
    if m > max_m:
        print(f"Предупреждение: Serial Test неприменим для m={m}. Требуется m <= log2(n) - 2 ({max_m})")
        return 0.0
        
    if m >= n:
        print("Предупреждение: Serial Test неприменим. m >= n")
        return 0.0
        
    def count_patterns(seq, length):
        counts = {}
        total_patterns = 2 ** length
        for i in range(total_patterns):
            counts[i] = 0
            
        extended_seq = np.concatenate([seq, seq[:length - 1]])
        
        for i in range(n): 
            val = 0
            for j in range(length):
                val = (val << 1) | extended_seq[i+j]
            counts[val] += 1
        return counts

    counts_m = count_patterns(bits, m)
    counts_m1 = count_patterns(bits, m - 1) if m > 1 else None
    counts_m2 = count_patterns(bits, m - 2) if m > 2 else None
    
    def calc_psi(counts, n, length):
        sum_sq = sum(v * v for v in counts.values())
        return (sum_sq * (2 ** length) / n) - n

    psi_m = calc_psi(counts_m, n, m)
    psi_m1 = calc_psi(counts_m1, n, m - 1) if m > 1 else 0
    psi_m2 = calc_psi(counts_m2, n, m - 2) if m > 2 else 0
    
    delta1 = psi_m - psi_m1
    delta2 = psi_m - 2 * psi_m1 + psi_m2
    
    df1 = 2 ** (m - 1)
    df2 = 2 ** (m - 2)
    
    p_value1 = gammaincc(df1 / 2, delta1 / 2)
    p_value2 = gammaincc(df2 / 2, delta2 / 2) if m > 2 else 1.0
    p_value = min(p_value1, p_value2)

    return p_value
