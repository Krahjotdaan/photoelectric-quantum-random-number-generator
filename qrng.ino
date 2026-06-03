#include <hardware/adc.h>
#include <pico/stdlib.h>
#include <hardware/pwm.h>

const size_t PACKET_SIZE = 2048;
const int LED_PIN = 6; 
uint16_t adc_buffer[PACKET_SIZE];
bool isRunning = false;

void setup() {
  Serial.begin(2000000);
  unsigned long start = millis();
  while (!Serial && (millis() - start < 3000)) {}

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  adc_init();
  adc_gpio_init(26);
  adc_select_input(0);
  adc_set_clkdiv(191.0f); // ~250 кГц
}

void loop() {
  if (!isRunning) {
    if (Serial.available() > 0) {
      char cmd = Serial.read();
      if (cmd == 's' || cmd == 'S') {
        isRunning = true;
        while (Serial.available() > 0) Serial.read();
      }
    }
    return;
  }

  // === БЫСТРЫЙ ЦИКЛ МОДУЛЯЦИИ ===
  for (size_t i = 0; i < PACKET_SIZE; i++) {
    // 1. Включаем LED
    gpio_put(LED_PIN, 1);
    
    // 2. Читаем АЦП (занимает ~4-8 мкс)
    // За это время сигнал на фотодиоде уже успеет нарасти, если цепь быстрая
    adc_buffer[i] = adc_read();
    
    // 3. Выключаем LED
    gpio_put(LED_PIN, 0);
    
    // 4. Короткая пауза, чтобы разделить импульсы (опционально)
    // Если фотодиод медленный, оставьте busy_wait_us(1);
    // Если быстрый, можно убрать совсем для максимума скорости
    // busy_wait_us(1); 
  }

  Serial.write((const uint8_t*)adc_buffer, PACKET_SIZE * 2);
  Serial.flush();
}