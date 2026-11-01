#include "hdrs/usb.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

#if defined(PICO_ON_DEVICE) || defined(LIB_PICO_STDIO_USB) || defined(PICO_BOARD)
#include "pico/stdlib.h"

int init_usb(void) {
    // stdio_init_all initializes the 48MHz USB PLL,
    // unresets the USB controller, and activates the TinyUSB CDC stack.
    stdio_init_all();
    return 0;
}

int init_usb_wrt(void) {
    return init_usb();
}

int write_usb(const char *s) {
    if (!s) return -1;
    fputs(s, stdout);
    fflush(stdout);
    return 0;
}

int read_usb(char *buf, int max_len) {
    if (!buf || max_len <= 0) return 0;
    int count = 0;
    while (count < max_len - 1) {
        // Non-blocking single-character read (0 microsecond timeout)
        int c = getchar_timeout_us(0);
        if (c == PICO_ERROR_TIMEOUT || c < 0) {
            break;
        }
        buf[count++] = (char)c;
    }
    buf[count] = '\0';
    return count;
}

#else
/*
 * Bare-metal / Simulation Fallback
 */
int init_usb(void) {
    return 0;
}

int init_usb_wrt(void) {
    return init_usb();
}

int write_usb(const char *s) {
    if (!s) return -1;
    return 0;
}

int read_usb(char *buf, int max_len) {
    if (!buf || max_len <= 0) return 0;
    buf[0] = '\0';
    return 0;
}
#endif
