"""
Централизованная конфигурация для CLI-скриптов КГСЧ.

Параметры можно переопределить через переменные окружения:
  QRNG_BAUD_RATE=3000000
  QRNG_PACKET_SAMPLES=4096
  QRNG_SERIAL_TIMEOUT=1
  QRNG_RECONNECT_TIMEOUT=30
"""
import os


# === Сбор данных (collect.py) ===
PACKET_SAMPLES = int(os.environ.get("QRNG_PACKET_SAMPLES", "4096"))
PACKET_BYTES = PACKET_SAMPLES * 2

BAUD_RATE = int(os.environ.get("QRNG_BAUD_RATE", "2000000"))
SERIAL_TIMEOUT = int(os.environ.get("QRNG_SERIAL_TIMEOUT", "1"))
RECONNECT_TIMEOUT = int(os.environ.get("QRNG_RECONNECT_TIMEOUT", "30"))