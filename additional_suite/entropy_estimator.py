import math
import numpy as np
from collections import Counter


def min_entropy_nist_90b(data, bits_per_sample=1):
    data = np.asarray(data, dtype=int)
    n = len(data)
    
    estimates = []
    
    # === Тест 1: Most Common Value (MCV) Estimate ===
    counts = Counter(data)
    p_max = max(counts.values()) / n
    h_mcv = -math.log2(p_max) if p_max > 0 else bits_per_sample
    estimates.append(("MCV", h_mcv))
    
    # === Тест 2: Collision Estimate ===
    collisions = []
    i = 0
    while i < n:
        val = data[i]
        j = i + 1
        while j < n and data[j] != val:
            j += 1
        if j < n:
            collisions.append(j - i)
        i = j + 1
    
    if collisions:
        mean_collision = np.mean(collisions)
        h_collision = 2 * math.log2(mean_collision / math.sqrt(math.pi / 2))
        h_collision = max(0, min(h_collision, bits_per_sample))
        estimates.append(("Collision", h_collision))
    
    # === Тест 3: Markov Estimate ===
    if bits_per_sample == 1 and n > 10000:
        transitions = {(0,0): 0, (0,1): 0, (1,0): 0, (1,1): 0}
        for i in range(n - 1):
            transitions[(data[i], data[i+1])] += 1
        
        total_from_0 = transitions[(0,0)] + transitions[(0,1)]
        total_from_1 = transitions[(1,0)] + transitions[(1,1)]
        
        if total_from_0 > 0 and total_from_1 > 0:
            p_matrix = {
                (0,0): transitions[(0,0)] / total_from_0,
                (0,1): transitions[(0,1)] / total_from_0,
                (1,0): transitions[(1,0)] / total_from_1,
                (1,1): transitions[(1,1)] / total_from_1,
            }
            max_trans = max(p_matrix.values())
            h_markov = -math.log2(max_trans) if max_trans > 0 else 1.0
            estimates.append(("Markov", h_markov))
    
    _, min_entropy = min(estimates, key=lambda x: x[1])
    
    print("\nОценки энтропии (NIST SP 800-90B):")
    for name, h in estimates:
        print(f"{name:>2}: {h:.4f} бит/символ")
    
    return min_entropy


def calculate_safe_compression_ratio(min_entropy, epsilon=2**-64):
    """
    Расчет безопасного коэффициента сжатия по Leftover Hash Lemma
    """
    if min_entropy <= 0:
        return 1.0
    
    security_margin = 2 * math.log2(1 / epsilon)
    
    input_block = 256
    max_output_bits = input_block * min_entropy - security_margin
    
    if max_output_bits <= 0:
        return 10.0 
        
    ratio = input_block / max_output_bits

    return max(1.0, ratio)
