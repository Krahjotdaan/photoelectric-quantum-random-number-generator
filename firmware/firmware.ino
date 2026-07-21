#include <Arduino.h>
#include <hardware/adc.h>
#include <hardware/dma.h>
#include <hardware/pwm.h>
#include <hardware/irq.h>
#include <hardware/watchdog.h>

#define LED_PIN         6
#define PACKET_SAMPLES  4096
#define PACKET_BYTES    (PACKET_SAMPLES * 2)
#define NUM_BUFFERS     3
#define WATCHDOG_TIMEOUT_MS 1000

static uint16_t dma_buffers[NUM_BUFFERS][PACKET_SAMPLES];
static volatile uint8_t buffer_ready[NUM_BUFFERS] = {0, 0, 0};
static volatile uint8_t active_buffer = 0;
static volatile bool running = false;

static uint dma_chan;
static uint pwm_slice;

void dma_handler(void) {
    dma_hw->ints0 = 1u << dma_chan;
    
    uint8_t ready = active_buffer;
    buffer_ready[ready] = 1;
    active_buffer = (active_buffer + 1) % NUM_BUFFERS;
    
    dma_channel_set_write_addr(dma_chan, dma_buffers[active_buffer], false);
    dma_channel_set_trans_count(dma_chan, PACKET_SAMPLES, true);
}

void setup_pwm_optimized(void) {
    pwm_slice = pwm_gpio_to_slice_num(LED_PIN);
    gpio_set_function(LED_PIN, GPIO_FUNC_PWM);
    
    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_clkdiv(&cfg, 1.0f);
    pwm_config_set_wrap(&cfg, 499);
    pwm_init(pwm_slice, &cfg, false);
    pwm_set_chan_level(pwm_slice, PWM_CHAN_A, 50);
}

void setup_adc_dma_optimized(void) {
    adc_init();
    adc_gpio_init(26);
    adc_select_input(0);
    
    adc_set_clkdiv(0.0f);
    adc_hw->cs = (adc_hw->cs & ~ADC_CS_TS_EN_BITS) | 
                 (1 << ADC_CS_TS_EN_LSB);
    
    adc_fifo_setup(true, true, 1, false, false);
    
    dma_chan = dma_claim_unused_channel(true);
    
    dma_channel_config cfg = dma_channel_get_default_config(dma_chan);
    channel_config_set_transfer_data_size(&cfg, DMA_SIZE_16);
    channel_config_set_read_increment(&cfg, false);
    channel_config_set_write_increment(&cfg, true);
    channel_config_set_dreq(&cfg, DREQ_ADC);
    channel_config_set_ring(&cfg, false, 0);
    channel_config_set_bswap(&cfg, false);
    
    dma_channel_configure(
        dma_chan,
        &cfg,
        dma_buffers[0],
        &adc_hw->fifo,
        PACKET_SAMPLES,
        false
    );
    
    dma_channel_set_irq0_enabled(dma_chan, true);
    irq_set_exclusive_handler(DMA_IRQ_0, dma_handler);
    irq_set_enabled(DMA_IRQ_0, true);
    
    // ✅ ПРАВИЛЬНЫЙ способ установки приоритета для RP2040:
    irq_set_priority(DMA_IRQ_0, 0);  // 0 - самый высокий приоритет
}

void start_sampling_optimized(void) {
    memset((void*)buffer_ready, 0, sizeof(buffer_ready));
    active_buffer = 0;
    
    dma_channel_set_write_addr(dma_chan, dma_buffers[0], false);
    dma_channel_set_trans_count(dma_chan, PACKET_SAMPLES, true);
    dma_channel_start(dma_chan);
    
    adc_run(true);
    pwm_set_enabled(pwm_slice, true);
    running = true;
}

void loop_optimized(void) {
    if (!running) {
        if (Serial.available() > 0) {
            char cmd = Serial.read();
            if (cmd == 's' || cmd == 'S') {
                start_sampling_optimized();
            }
        }
        return;
    }
    
    for (int i = 0; i < NUM_BUFFERS; i++) {
        if (buffer_ready[i]) {
            Serial.write((uint8_t*)dma_buffers[i], PACKET_BYTES);
            buffer_ready[i] = 0;
        }
    }
}

void setup() {
    Serial.begin(2000000);
    while (!Serial) { delay(10); }
    
    // Watchdog: если loop() зависнет, МК перезагрузится через 1 сек
    watchdog_enable(WATCHDOG_TIMEOUT_MS, true);
    
    setup_pwm_optimized();
    setup_adc_dma_optimized();
}

void loop() {
    loop_optimized();
    
    // Сброс watchdog — выполняется за несколько тактов (~50 нс)
    watchdog_update();
}