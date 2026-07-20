import math
import numpy as np
from scipy.special import gammaincc


def approximate_entropy_test(bits, m=2):
    """
    NIST SP 800-22: 2.12 Approximate Entropy Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    max_m = int(np.floor(np.log2(n))) - 5
    if m > max_m:
        print(f"Предупреждение: Approximate Entropy Test неприменим для m={m}. Требуется m <= log2(n) - 5 ({max_m})")
        return 0.0
    
    if m >= n:
        print("Предупреждение: Approximate Entropy Test неприменим. m >= n")
        return 0.0
    
    def calc_phi(seq_len, block_len):
        extended = np.concatenate([bits, bits[:block_len-1]])
        counts = {}
        total_combinations = 2 ** block_len
        
        for i in range(seq_len):
            val = 0
            for j in range(block_len):
                val = (val << 1) | extended[i+j]
            counts[val] = counts.get(val, 0) + 1
            
        phi = 0.0
        for i in range(total_combinations):
            Ci = counts.get(i, 0)
            if Ci > 0:
                pi_val = Ci / seq_len
                phi += pi_val * math.log(pi_val)

        return phi
        
    phi_m = calc_phi(n, m)
    phi_m1 = calc_phi(n, m+1)
    ap_en = phi_m - phi_m1
    
    chi2_obs = 2 * n * (math.log(2) - ap_en)
    df = 2 ** m
    p_value = gammaincc(df / 2, chi2_obs / 2)
    
    return p_value
