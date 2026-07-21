"""
Бенчмарки производительности КГСЧ.

Измеряет:
  1. Скорость сбора данных с АЦП (отсчётов/сек)
  2. Скорость ARX-экстракции (бит/сек)
  3. Скорость hash-экстракции для каждого метода (бит/сек)
  4. Пропускную способность системы (бит/сек на выходе)

Использование:
  python benchmarks.py              # тест экстракции на синтетических данных
  python benchmarks.py --live       # тест с реальным сбором (требуется устройство)
  python benchmarks.py --samples 1000000  # размер тестовых данных
"""
import time
import argparse
import numpy as np

from extract import arx_extract, hash_extract


def benchmark_extraction(data, target_bits, ratio, n_runs=3):
    """Измерение скорости ARX-экстракции."""
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = arx_extract(data, target_bits, ratio)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    avg_time = np.mean(times)
    bits_per_sec = target_bits / avg_time
    return avg_time, bits_per_sec


def benchmark_hash_extraction(data, target_bits, ratio, hash_type, n_runs=3):
    """Измерение скорости hash-экстракции."""
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = hash_extract(data, target_bits, hash_type, ratio)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    avg_time = np.mean(times)
    bits_per_sec = target_bits / avg_time
    return avg_time, bits_per_sec


def benchmark_collect(samples, baud_rate=2000000):
    """Измерение скорости сбора данных (требуется устройство)."""
    from collect import collect
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        tmp_path = f.name

    try:
        collect(samples, tmp_path, baud_rate)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main():
    parser = argparse.ArgumentParser(description="Бенчмарки КГСЧ")
    parser.add_argument("--live", action="store_true",
                        help="Включить тест с реальным сбором данных (требуется устройство)")
    parser.add_argument("--samples", type=int, default=500000,
                        help="Количество сырых отсчётов для теста (по умолч. 500000)")
    parser.add_argument("--target-bits", type=int, default=100000,
                        help="Целевое количество бит на выходе (по умолч. 100000)")
    parser.add_argument("--ratio", type=int, default=2,
                        help="Коэффициент сжатия (по умолч. 2)")
    parser.add_argument("--runs", type=int, default=3,
                        help="Количество прогонов для усреднения (по умолч. 3)")
    args = parser.parse_args()

    print("=" * 65)
    print("  БЕНЧМАРКИ ПРОИЗВОДИТЕЛЬНОСТИ КГСЧ")
    print("=" * 65)

    # --- Генерация синтетических сырых данных ---
    print(f"\n[1] Генерация {args.samples:,} синтетических отсчётов АЦП...")
    raw_data = np.random.randint(0, 4096, size=args.samples, dtype=np.uint16)
    print(f"    Сгенерировано: {len(raw_data):,} отсчётов")

    # --- Бенчмарк ARX ---
    print(f"\n[2] ARX-экстрактор (ratio={args.ratio}, target={args.target_bits:,} бит)")
    t_arx, rate_arx = benchmark_extraction(raw_data, args.target_bits, args.ratio, args.runs)
    print(f"    Среднее время: {t_arx:.4f} сек ({args.runs} прогона)")
    print(f"    Скорость:      {rate_arx:,.0f} бит/сек")

    # --- Бенчмарк hash-методов ---
    hash_methods = ["sha256", "sha3_256", "sha512", "sha3_512", "blake2s", "blake2b", "streebog256", "streebog512"]
    print(f"\n[3] Hash-экстракторы (ratio={args.ratio}, target={args.target_bits:,} бит)")
    print(f"    {'Метод':<20} {'Время, сек':<15} {'Скорость, бит/сек':<20}")
    print(f"    {'-'*55}")
    for h in hash_methods:
        try:
            t_hash, rate_hash = benchmark_hash_extraction(raw_data, args.target_bits, args.ratio, h, args.runs)
            print(f"    {h:<20} {t_hash:<15.4f} {rate_hash:<20,.0f}")
        except Exception as e:
            print(f"    {h:<20} {'ОШИБКА':<15} {str(e)[:40]}")

    # --- Пропускная способность системы ---
    print(f"\n[4] Пропускная способность системы")
    print(f"    Сырые отсчёты:  {args.samples:,} шт")
    print(f"    Выходные биты:  {args.target_bits:,} бит")
    print(f"    Коэф. сжатия:   {args.ratio}")
    print(f"    ARX:            {rate_arx:,.0f} бит/сек")

    # --- Live-тест сбора ---
    if args.live:
        print(f"\n[5] Сбор данных с устройства (baud_rate=2000000)")
        try:
            benchmark_collect(args.samples)
        except Exception as e:
            print(f"    ОШИБКА: {e}")

    print("\n" + "=" * 65)
    print("  БЕНЧМАРКИ ЗАВЕРШЕНЫ")
    print("=" * 65)


if __name__ == "__main__":
    main()