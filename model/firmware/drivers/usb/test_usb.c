#include "hdrs/usb.h"
#include <stdint.h>
#include <string.h>

#if defined(PICO_ON_DEVICE) || defined(PICO_BOARD)
#include "pico/stdlib.h"
#define LED_PIN 25
#endif

int main(void) {
    // 1. Initialize USB CDC serial protocol
    init_usb();

#if defined(PICO_ON_DEVICE) || defined(PICO_BOARD)
    // Initialize onboard LED (GPIO 25 on standard Raspberry Pi Pico)
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 1);
#endif

    char in[] = "ready\n";
    char rx_buf[64];

    // Transmit initial ready notification
    write_usb(in);

    uint32_t counter = 0;
    while (1) {
        // 2. Check for incoming USB data using read_usb
        int bytes = read_usb(rx_buf, sizeof(rx_buf));
        if (bytes > 0) {
            write_usb("Echo: ");
            write_usb(rx_buf);
            write_usb("\n");
        }

        // 3. Periodically transmit status and toggle LED
        counter++;
        if (counter >= 200000) {
            counter = 0;
            write_usb(in);
#if defined(PICO_ON_DEVICE) || defined(PICO_BOARD)
            gpio_xor_mask(1u << LED_PIN);
#endif
        }
    }

    return 0;
}