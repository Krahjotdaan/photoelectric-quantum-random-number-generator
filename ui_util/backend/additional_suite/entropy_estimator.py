import time
import math
import numpy as np
from collections import Counter


def estimate_mcv(data, bits_per_sample):
    n = len(data)
    counts = Counter(data)
    p_max = max(counts.values()) / n
    h = -math.log2(p_max) if p_max > 0 else bits_per_sample
    return max(0.0, min(h, bits_per_sample))


def estimate_collision(data, bits_per_sample):
    n = len(data)
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
    if not collisions:
        return bits_per_sample
    mean_collision = np.mean(collisions)
    if mean_collision <= 0:
        return 0.0
    h = 2 * math.log2(mean_collision / math.sqrt(math.pi / 2))
    return max(0.0, min(h, bits_per_sample))


def estimate_markov(data, bits_per_sample):
    n = len(data)
    if bits_per_sample != 1 or n <= 10000:
        return None
    transitions = {(0,0): 0, (0,1): 0, (1,0): 0, (1,1): 0}
    for i in range(n - 1):
        transitions[(data[i], data[i+1])] += 1
    total_from_0 = transitions[(0,0)] + transitions[(0,1)]
    total_from_1 = transitions[(1,0)] + transitions[(1,1)]
    if total_from_0 == 0 or total_from_1 == 0:
        return None
    p_matrix = {
        (0,0): transitions[(0,0)] / total_from_0,
        (0,1): transitions[(0,1)] / total_from_0,
        (1,0): transitions[(1,0)] / total_from_1,
        (1,1): transitions[(1,1)] / total_from_1,
    }
    max_trans = max(p_matrix.values())
    h = -math.log2(max_trans) if max_trans > 0 else 1.0
    return max(0.0, min(h, bits_per_sample))


def estimate_compression(data, bits_per_sample):
    n = len(data)
    if n < 1000:
        return None
    dictionary = {}
    dict_size = 0
    i = 0
    while i < n:
        current = (data[i],)
        j = i + 1
        while j < n and current in dictionary:
            current = current + (data[j],)
            j += 1
        if current not in dictionary:
            dictionary[current] = dict_size
            dict_size += 1
        i = j if j > i + 1 else i + 1
    if dict_size == 0:
        return bits_per_sample
    avg_phrase_len = n / dict_size if dict_size > 0 else n
    h = math.log2(dict_size) / avg_phrase_len if avg_phrase_len > 0 else 0
    return max(0.0, min(h, bits_per_sample))


def estimate_t_tuple(data, bits_per_sample, t=5):
    n = len(data)
    if n < t * 10:
        return None
    t_gram_counts = Counter()
    for i in range(n - t + 1):
        t_gram = tuple(data[i:i + t])
        t_gram_counts[t_gram] += 1
    if not t_gram_counts:
        return bits_per_sample
    total_t_grams = n - t + 1
    p_max = max(t_gram_counts.values()) / total_t_grams
    h = (-math.log2(p_max) / t) if p_max > 0 else bits_per_sample
    return max(0.0, min(h, bits_per_sample))


def estimate_lrs_fft(data, bits_per_sample):
    n = len(data)
    if n < 1000:
        return None
    x = 2 * np.asarray(data, dtype=np.float64) - 1
    fft_vals = np.fft.rfft(x)
    power = np.abs(fft_vals) ** 2
    freqs = np.fft.rfftfreq(n)
    power[0] = 0
    p99 = np.percentile(power, 99.9)
    peak_power = np.max(power)
    if peak_power < p99 * 3:
        max_len = max(1, int(math.log2(n)))
    else:
        peak_idx = np.argmax(power)
        peak_freq = freqs[peak_idx]
        if peak_freq > 0:
            period = max(1, int(1.0 / peak_freq))
            max_len = max(1, n // period)
        else:
            max_len = n
    h = math.log2(n) / max_len if max_len > 0 else 0
    return max(0.0, min(h, bits_per_sample))


def estimate_multimcw(data, bits_per_sample, window_size=256):
    n = len(data)
    max_n = 500000
    if n > max_n:
        data = data[:max_n]
        n = max_n
    if n < window_size * 2:
        return None
    counts = Counter(data[:window_size])
    correct_predictions = 0
    total_predictions = 0
    for i in range(window_size, n):
        prediction = counts.most_common(1)[0][0]
        if prediction == data[i]:
            correct_predictions += 1
        total_predictions += 1
        old_val = data[i - window_size]
        new_val = data[i]
        counts[old_val] -= 1
        if counts[old_val] == 0:
            del counts[old_val]
        counts[new_val] += 1
    if total_predictions == 0:
        return bits_per_sample
    p_correct = correct_predictions / total_predictions
    p_correct = min(p_correct, 0.9999)
    h = -math.log2(p_correct) if p_correct > 0 else bits_per_sample
    return max(0.0, min(h, bits_per_sample))


def estimate_lag(data, bits_per_sample, max_lag=128):
    n = len(data)
    max_n = 500000
    if n > max_n:
        data = data[:max_n]
        n = max_n
    if n < max_lag * 2:
        return None
    best_p = 0.5
    data_arr = np.asarray(data)
    for lag in range(1, max_lag + 1):
        matches = np.sum(data_arr[lag:] == data_arr[:-lag])
        p = matches / (n - lag)
        if p > best_p:
            best_p = p
    best_p = min(best_p, 0.9999)
    h = -math.log2(best_p) if best_p > 0 else bits_per_sample
    return max(0.0, min(h, bits_per_sample))


def estimate_multimmc(data, bits_per_sample, max_order=4):
    n = len(data)
    max_n = 500000
    if n > max_n:
        data = data[:max_n]
        n = max_n
    if n < 1000:
        return None
    best_p = 0.5
    for order in range(1, max_order + 1):
        if n <= order:
            continue
        context_counts = {}
        context_totals = {}
        for i in range(order, n):
            context = tuple(data[i - order:i])
            next_val = data[i]
            if context not in context_counts:
                context_counts[context] = Counter()
                context_totals[context] = 0
            context_counts[context][next_val] += 1
            context_totals[context] += 1
        correct = 0
        total = 0
        for i in range(order, n):
            context = tuple(data[i - order:i])
            if context in context_counts and context_totals[context] > 0:
                prediction = context_counts[context].most_common(1)[0][0]
                if prediction == data[i]:
                    correct += 1
                total += 1
        if total > 0:
            p = correct / total
            if p > best_p:
                best_p = p
    best_p = min(best_p, 0.9999)
    h = -math.log2(best_p) if best_p > 0 else bits_per_sample
    return max(0.0, min(h, bits_per_sample))


import math
import numpy as np


def estimate_lz78y(data, bits_per_sample=1):
    n = len(data)
    if n < 1000:
        return None
    
    B = 16 
    max_dict_size = 65536
    N = n - B - 1 
    
    if N <= 0:
        return None
    
    dictionary = {}
    dict_size = 0
    
    correct = np.zeros(N, dtype=np.int8)
    
    for i in range(B + 2, n):
        idx = i - B - 1 
        
        for j in range(B, 0, -1):
            start = i - j - 1
            end = i - 1
            if start < 0:
                continue
                
            prev_tuple = tuple(data[start:end])
            
            if prev_tuple not in dictionary:
                if dict_size < max_dict_size:
                    dictionary[prev_tuple] = {}
                    dict_size += 1
            
            if prev_tuple in dictionary:
                next_sym = data[i - 1]
                dictionary[prev_tuple][next_sym] = dictionary[prev_tuple].get(next_sym, 0) + 1
        
        prediction = None
        max_count = 0
        
        for j in range(B, 0, -1):
            start = i - j
            end = i
            if start < 0:
                continue
                
            prev_tuple = tuple(data[start:end])
            
            if prev_tuple in dictionary and dictionary[prev_tuple]:
                best_sym = max(dictionary[prev_tuple], 
                              key=lambda s: (dictionary[prev_tuple][s], s))
                count = dictionary[prev_tuple][best_sym]
                
                if count > max_count:
                    max_count = count
                    prediction = best_sym
        
        if prediction is not None and prediction == data[i]:
            correct[idx] = 1
    
    C = int(np.sum(correct))
    P_global = C / N if N > 0 else 0.0
    
    if P_global == 0.0:
        P_global_prime = 1.0 - (0.01 ** (1.0 / N))
    else:
        z = 2.576  # Z(1-0.005)
        se = math.sqrt(P_global * (1.0 - P_global) / (N - 1))
        P_global_prime = min(1.0, P_global + z * se)
    
    max_run = 0
    current_run = 0
    for val in correct:
        if val == 1:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    
    r = max_run + 1
    
    P_local = _solve_p_local(r, N)
    
    k = 2 ** bits_per_sample  # Размер алфавита
    
    p_max = max(P_global_prime, P_local, 1.0 / k)
    
    if p_max >= 1.0:
        return 0.0
    
    h = -math.log2(p_max)
    return max(0.0, min(h, float(bits_per_sample)))


def _solve_p_local(r, N, tol=1e-12, max_iter=1000):
    lo, hi = 1e-15, 1.0 - 1e-15
    
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_val = _compute_equation(mid, r, N)
        
        if abs(f_val - 0.99) < tol:
            return mid
        
        if f_val < 0.99:
            lo = mid
        else:
            hi = mid
    
    return (lo + hi) / 2.0


def _compute_equation(p_local, r, N):
    q = 1.0 - p_local
    
    x = 1.0
    for _ in range(10):
        if p_local <= 0 or r <= 0:
            break
        ratio = (q * p_local ** r) / (r + 1)
        x = 1.0 + ratio * x ** r
    
    if x <= 0 or x >= 1:
        return 0.0
    
    term1 = p_local ** x
    term2 = (r + 1 - r * x) * q
    denominator = x ** (N + 1)
    
    if denominator == 0:
        return 0.0
    
    result = 1.0 - (term1 * term2) / denominator
    return result


def min_entropy_nist_90b(data, bits_per_sample=1, logger=None):
    def log(msg):
        if logger:
            logger(msg)
        else:
            print(msg)

    data = np.asarray(data, dtype=int)
    n = len(data)

    if n == 0:
        log("Ошибка: пустые данные")
        return 0.0

    estimates = []
    total_time = 0.0

    estimators = [
        ("MCV", lambda: estimate_mcv(data, bits_per_sample)),
        ("Collision", lambda: estimate_collision(data, bits_per_sample)),
        ("Markov", lambda: estimate_markov(data, bits_per_sample)),
        ("Compression", lambda: estimate_compression(data, bits_per_sample)),
        ("t-Tuple", lambda: estimate_t_tuple(data, bits_per_sample)),
        # ("LRS (FFT)", lambda: estimate_lrs_fft(data, bits_per_sample)),
        ("MultiMCW", lambda: estimate_multimcw(data, bits_per_sample)),
        ("Lag", lambda: estimate_lag(data, bits_per_sample)),
        ("MultiMMC", lambda: estimate_multimmc(data, bits_per_sample)),
        # ("LZ78Y", lambda: estimate_lz78y(data, bits_per_sample)),
    ]

    for name, func in estimators:
        t0 = time.time()
        h = func()
        t1 = time.time()
        elapsed = t1 - t0
        total_time += elapsed

        if h is not None:
            estimates.append((name, h))
            log(f"{name:>25}: {h:.4f} бит/символ  ({elapsed:.3f} сек)")
        else:
            log(f"{name:>25}: N/A  ({elapsed:.3f} сек)")

    _, min_entropy = min(estimates, key=lambda x: x[1])

    log(f"\n{'Мин-энтропия':>25}: {min_entropy:.4f} бит/бит")
    log(f"{'Общее время':>25}: {total_time:.3f} сек")

    return min_entropy


def calculate_safe_compression_ratio(min_entropy, epsilon=2**-64):
    if min_entropy <= 0:
        return 1.0
    security_margin = 2 * math.log2(1 / epsilon)
    input_block = 256
    max_output_bits = input_block * min_entropy - security_margin
    if max_output_bits <= 0:
        return 10.0
    ratio = input_block / max_output_bits
    return max(1.0, ratio)