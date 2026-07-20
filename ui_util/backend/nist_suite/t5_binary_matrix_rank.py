import numpy as np
from scipy.special import gammaincc


def binary_matrix_rank_test(bits):
    """
    NIST SP 800-22: 2.5 Binary Matrix Rank Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    M = 32
    Q = 32
    
    min_bits = 38 * M * Q 
    
    if n < min_bits:
        print(f"Предупреждение: Binary Matrix Rank Test неприменим. Требуется минимум {min_bits} бит (38 матриц 32x32), получено {n}")
        return 0.0
        
    N_blocks = n // (M * Q)
    
    p_full = 0.2887880951
    p_full_minus_1 = 0.5775761902
    p_others = 1.0 - p_full - p_full_minus_1
    
    probs = np.array([p_full, p_full_minus_1, p_others])
    counts = np.zeros(3, dtype=int)
    
    for i in range(N_blocks):
        start_idx = i * M * Q
        block_bits = bits[start_idx : start_idx + M * Q]
        matrix = block_bits.reshape(M, Q)

        def compute_rank_gf2(matrix):
            rows, cols = matrix.shape
            r = 0
            for c in range(cols):
                if r >= rows:
                    break
                pivot_row = None
                for i in range(r, rows):
                    if matrix[i, c] == 1:
                        pivot_row = i
                        break
                
                if pivot_row is None:
                    continue
                    
                if pivot_row != r:
                    matrix[[r, pivot_row]] = matrix[[pivot_row, r]]
                    
                for i in range(rows):
                    if i != r and matrix[i, c] == 1:
                        matrix[i] = (matrix[i] + matrix[r]) % 2
                r += 1

            return r

        rank = compute_rank_gf2(matrix.copy())
        
        if rank == M:
            counts[0] += 1
        elif rank == M - 1:
            counts[1] += 1
        else:
            counts[2] += 1
            
    expected = N_blocks * probs
    chi2_obs = np.sum((counts - expected) ** 2 / (expected + 1e-10))
    
    p_value = gammaincc(2 / 2, chi2_obs / 2)
    
    return p_value
