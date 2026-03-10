import math
import numpy as np
from scipy.stats import norm
from scipy.special import erfc, gammaincc


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


def random_excursions_test(bits):
    """
    NIST SP 800-22 Rev 1a: Section 2.14 Random Excursions Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Random Excursions Test рекомендуется для последовательностей от 10^6 бит. Получено {n}")

    if n == 0:
        return 0.0
        
    X = 2 * bits - 1
    S = np.cumsum(X)
    S_prime = np.concatenate(([0], S, [0]))
    zero_indices = np.where(S_prime == 0)[0]
    J = len(zero_indices) - 1
    
    if J < 500:
        print(f"Предупреждение: Random Excursions Test неприменим. Требуется минимум 500 циклов, получено {J}")
        return 0.0 

    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    p_values = []

    def get_theoretical_probs(x):
        x_abs = abs(x)
        pi = np.zeros(6)
        pi[0] = 1.0 - 1.0 / (2.0 * x_abs)
        factor = 1.0 - 1.0 / (2.0 * x_abs)
        for k in range(1, 5):
            pi[k] = (1.0 / (4.0 * x_abs)) * (factor ** (k - 1))
            
        pi[5] = 1.0 - np.sum(pi[:5])
        
        return pi

    for x in states:
        nu = np.zeros(6, dtype=int) 
        for i in range(J):
            start_idx = zero_indices[i]
            end_idx = zero_indices[i+1]
            cycle = S_prime[start_idx + 1 : end_idx]
            
            if len(cycle) == 0:
                continue
                
            count = np.sum(cycle == x)
            if count >= 5:
                nu[5] += 1
            else:
                nu[count] += 1
        
        pi = get_theoretical_probs(x)
        expected = J * pi
        
        chi2_obs = 0.0
        for k in range(6):
            if expected[k] > 0:
                chi2_obs += ((nu[k] - expected[k]) ** 2) / expected[k]
            elif nu[k] > 0:
                chi2_obs = float('inf')
                break
        
        p_val = gammaincc(5.0 / 2.0, chi2_obs / 2.0)
        p_values.append(p_val)

    return (np.array(p_values).mean()) if p_values else 0.0


def random_excursions_variant_test(bits):
    """
    NIST SP 800-22: 2.15 Random Excursions Variant Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Random Excursions Variant Test рекомендуется для последовательностей от 10^6 бит. Получено {n}")

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
        
    return min(p_values) if p_values else 0.0
