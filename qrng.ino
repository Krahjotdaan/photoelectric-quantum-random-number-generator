#include <hardware/adc.h>
#include <pico/stdlib.h>

const size_t PACKET_SIZE = 256;
uint16_t adc_buffer[PACKET_SIZE];
bool isRunning = false;

void setup() {
  Serial.begin(1500000);

  unsigned long start = millis();
  while (!Serial && (millis() - start < 3000)) {}

  adc_init();
  adc_gpio_init(26);
  adc_select_input(0);

  adc_set_clkdiv(191.0f);
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

  for (size_t i = 0; i < PACKET_SIZE; i++) {
    adc_buffer[i] = adc_read();
  }

  Serial.write((const uint8_t*)adc_buffer, PACKET_SIZE * 2);
  Serial.flush();
}