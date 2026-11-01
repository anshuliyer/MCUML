#ifndef USB_H
#define USB_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the USB CDC serial subsystem.
 * Handles the 48 MHz USB PLL, peripheral unreset, transceiver PHY pull-up,
 * and the Endpoint 0 USB enumeration state machine.
 *
 * @return 0 on success, non-zero on failure.
 */
int init_usb(void);

/**
 * @brief Backward-compatible alias for init_usb.
 */
int init_usb_wrt(void);

/**
 * @brief Transmit a null-terminated string over USB CDC.
 *
 * @param s String to transmit.
 * @return 0 on success, non-zero on error.
 */
int write_usb(const char *s);

/**
 * @brief Read incoming bytes from USB CDC.
 * Non-blocking: returns available bytes immediately up to max_len.
 *
 * @param buf Destination buffer.
 * @param max_len Maximum number of bytes to store in buf.
 * @return Number of bytes read (0 if no data is currently available).
 */
int read_usb(char *buf, int max_len);

#ifdef __cplusplus
}
#endif

#endif /* USB_H */