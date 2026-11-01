#include "hdr/uart.h"

int uart_wr(char *s) {
#ifdef PRESIL
  /* Ensure CMSDK transmitter is enabled and baud divider is set */
  if ((UART0->CTRL & UART_CTRL_TXEN) == 0) {
    UART0->BAUDDIV = 16;
    UART0->CTRL |= UART_CTRL_TXEN;
  }
#endif

  int i = 0;
  while (s[i] != '\0') {
#ifdef PRESIL
    /* CMSDK APB UART: bit 0 (TXFULL) is 1 when buffer is full */
    if (((UART0->STATE) & UART_STATE_TXFULL) == 0) {
#else
    /* PL011 UART: bit 5 (TXFF) is 1 when FIFO is full */
    if (((UART0->UARTFR) & 0x0020) == 0) {
#endif
      UART0->UARTDR = s[i];
      i = i + 1;
    } else {
      continue;
    }
  }
  return 0;
}