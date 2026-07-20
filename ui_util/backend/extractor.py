import hashlib
import numpy as np
from gostcrypto import gosthash


_BYTE_TO_BITS = np.unpackbits(np.arange(256, dtype=np.uint8).reshape(-1, 1), bitorder='big').reshape(256, 8)


def arx_extract(raw_data, target_bits, compression_ratio=2):
    raw_array = np.asarray(raw_data, dtype=np.uint16)
    diff_array = np.diff(raw_array)
    raw_bits = (diff_array & 1).astype(np.uint8)
    
    input_block_bytes = 32
    output_bits = 256 // compression_ratio
    output_bytes = max(1, (output_bits + 7) // 8)
    
    n_blocks = min(
        len(raw_bits) // (input_block_bytes * 8),
        (target_bits + output_bytes * 8 - 1) // (output_bytes * 8)
    )
    
    if n_blocks == 0:
        return np.array([], dtype=np.int8)
    
    usable = raw_bits[:n_blocks * input_block_bytes * 8].reshape(n_blocks, input_block_bytes * 8)
    block_bytes = np.packbits(usable, axis=1, bitorder='big')
    
    result = bytearray(n_blocks * output_bytes)
    
    ARX_CONSTANTS = np.array([
        0x9E3779B97F4A7C15,  # φ
        0x6A09E667F3BCC908,  # √2
        0x243F6A8885A308D3,  # π
        0xB7E151628AED2A6A,  # e
        0xBB67AE8584CAA73B,  # √3
        0xB17217F7D1CF79AB,  # ln(2)
        0x33BA004F00621383,  # apery
        0x93C467E37DB0C7A4   # euler-maskeroni
    ], dtype=np.uint64)
    
    MASK64 = np.uint64(0xFFFFFFFFFFFFFFFF)
    
    # === IV: первые 4 константы (совпадают с размером state) ===
    prev_state = ARX_CONSTANTS[:4].copy()
    
    for i in range(n_blocks):
        state = np.frombuffer(bytes(block_bytes[i]), dtype=np.uint64).copy()
        
        # === Chaining: связывание с предыдущим блоком ===
        state ^= prev_state
        
        for round_idx in range(16):
            state ^= ARX_CONSTANTS[round_idx % 8]
            state = ((state << np.uint64(13)) | (state >> np.uint64(51))) & MASK64
            state[0] ^= state[1]
            state[2] ^= state[3]
            state[1] ^= state[2]
            state[3] ^= state[0]
            state = ((state << np.uint64(17)) | (state >> np.uint64(47))) & MASK64
        
        prev_state = state.copy()
        
        out_bytes = state.tobytes()[:output_bytes]
        result[i * output_bytes : (i + 1) * output_bytes] = out_bytes
    
    result_array = np.frombuffer(bytes(result), dtype=np.uint8)
    all_bits = _BYTE_TO_BITS[result_array].ravel()
    
    return all_bits[:target_bits].astype(np.int8)


def hash_extract(raw_data, target_bits, hash_type="sha3_256", compression_ratio=2):
    HASH_CONFIG = {
        "sha256":      {"func": lambda d: hashlib.sha256(d).digest(),                   "bits": 256},
        "sha3_256":    {"func": lambda d: hashlib.sha3_256(d).digest(),                 "bits": 256},

        "sha512":      {"func": lambda d: hashlib.sha512(d).digest(),                   "bits": 512},
        "sha3_512":    {"func": lambda d: hashlib.sha3_512(d).digest(),                 "bits": 512},

        "blake2s":     {"func": lambda d: hashlib.blake2s(d, digest_size=32).digest(),  "bits": 256},
        "blake2b":     {"func": lambda d: hashlib.blake2b(d, digest_size=64).digest(),  "bits": 512},
        
        "streebog256": {"func": lambda d: gosthash.new('streebog256', data=d).digest(), "bits": 256},
        "streebog512": {"func": lambda d: gosthash.new('streebog512', data=d).digest(), "bits": 512},
    }

    if hash_type not in HASH_CONFIG:
        raise ValueError(f"Неизвестный хеш: {hash_type}. Доступны: {list(HASH_CONFIG.keys())}")

    cfg = HASH_CONFIG[hash_type]
    hash_func, hash_bits = cfg["func"], cfg["bits"]

    output_bits_per_hash = hash_bits // compression_ratio
    output_bytes = (output_bits_per_hash + 7) // 8 

    raw_array = np.diff(np.asarray(raw_data, dtype=np.uint16))
    diff_array = np.diff(raw_array)
    raw_bits = (diff_array & 1).astype(np.uint8)

    n_blocks = min(len(raw_bits) // hash_bits, 
                   (target_bits + output_bits_per_hash - 1) // output_bits_per_hash)
    
    if n_blocks == 0:
        return np.array([], dtype=np.int8)

    usable = raw_bits[:n_blocks * hash_bits].reshape(n_blocks, hash_bits)
    block_bytes = np.packbits(usable, axis=1, bitorder='big')

    total_output_bits = n_blocks * output_bits_per_hash
    result_bytes = bytearray(total_output_bits // 8 + 8) 
    offset = 0

    for i in range(n_blocks):
        if offset * 8 >= target_bits:
            break
        
        digest = hash_func(bytes(block_bytes[i]))
        
        result_bytes[offset:offset + output_bytes] = digest[:output_bytes]
        offset += output_bytes

    needed_bytes = min(offset, (target_bits + 7) // 8)
    result_array = np.frombuffer(bytes(result_bytes[:needed_bytes]), dtype=np.uint8)
    
    all_bits = _BYTE_TO_BITS[result_array].ravel()

    return all_bits[:target_bits].astype(np.int8)
