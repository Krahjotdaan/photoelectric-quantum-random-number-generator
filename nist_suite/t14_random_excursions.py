import numpy as np
from scipy.special import gammaincc


def random_excursions_test(bits):
    """
    NIST SP 800-22 Rev 1a: Section 2.14 Random Excursions Test
    """
    bits = np.asarray(bits, dtype=int)
    n = len(bits)
    
    if n < 1000000:
        print(f"Предупреждение: Random Excursions Test рекомендуется для последовательностей от 10^6 бит. Получено {n}. Результаты могут быть неточными")

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
