import numpy as np
from scipy.special import gammaincc


def linear_complexity_test(bits, M=500):
    """
    NIST SP 800-22: 2.10 Linear Complexity Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Linear Complexity Test рекомендуется для последовательностей от 10^6 бит. Получено {n}. Результаты могут быть неточными")

    N_blocks = n // M
    
    if N_blocks < 200:
        print(f"Предупреждение: Linear Complexity Test требует минимум 200 блоков для достоверности хи-квадрат. Получено {N_blocks}. Результаты могут быть неточными")
    
    if N_blocks == 0:
        print("Предупреждение: Linear Complexity Test неприменим. Длина блока M больше длины последовательности")
        return 0.0
        
    pi = np.array([0.010417, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833])
    K_degrees = 6
    
    nu = np.zeros(K_degrees + 1, dtype=int)

    def berlekamp_massey(s):
        n_len = len(s)
        C = [0] * n_len
        B = [0] * n_len
        C[0] = 1
        B[0] = 1
        L = 0
        m = 1
        
        for i in range(n_len):
            d = s[i]
            for j in range(1, L + 1):
                d ^= (C[j] & s[i-j])
                
            if d == 1:
                T = C[:]
                for j in range(n_len - m):
                    if j < n_len:
                        C[j + m] ^= B[j]
                
                if 2 * L <= i:
                    L = i + 1 - L
                    B = T
                    m = 1
                else:
                    m += 1
            else:
                m += 1
                
        return L
    
    for i in range(N_blocks):
        block = bits[i*M : (i+1)*M]
        L = berlekamp_massey(block)
        
        mu = (M / 2.0) + (9.0 + ((-1) ** (M + 1))) / 36.0 - (1.0 / (2 ** M))
        Ti = ((-1) ** M) * (L - mu) + (2.0 / 9.0)
        
        if Ti <= -2.5:
            nu[0] += 1
        elif -2.5 < Ti <= -1.5:
            nu[1] += 1
        elif -1.5 < Ti <= -0.5:
            nu[2] += 1
        elif -0.5 < Ti <= 0.5:
            nu[3] += 1
        elif 0.5 < Ti <= 1.5:
            nu[4] += 1
        elif 1.5 < Ti <= 2.5:
            nu[5] += 1
        else: 
            nu[6] += 1
            
    expected = N_blocks * pi
    chi2_obs = np.sum((nu - expected) ** 2 / (expected + 1e-10))
    p_value = gammaincc(K_degrees / 2, chi2_obs / 2)
    
    return p_value
