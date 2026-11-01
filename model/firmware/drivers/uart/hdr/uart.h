// header for uart
#include <stdint.h>

#ifdef POSTSIL
#define UART0_BASE (0x40009000)

typedef struct __attribute__((packed)) {
  uint32_t UARTDR;
  uint16_t allign[9];
  uint32_t UARTFR;
  uint32_t reserv[3];
  uint32_t UARTILPR;
  uint32_t UARTIBRD;
  uint32_t UARTRD;
} MCU_UART;

#define UART0 ((volatile MCU_UART *)UART0_BASE)
#endif
#ifdef PRESIL
#define UART0_BASE (0x40200000)

typedef struct {
  union {
    volatile uint32_t DATA;   /* Offset 0x00: Data Register (R/W) */
    volatile uint32_t UARTDR; /* Compatibility alias */
  };
  union {
    volatile uint32_t STATE;  /* Offset 0x04: Status Register (R/W) - bit 0:
                                 TXFULL, bit 1: RXFULL */
    volatile uint32_t UARTFR; /* Compatibility alias */
  };
  volatile uint32_t
      CTRL; /* Offset 0x08: Control Register (R/W) - bit 0: TXEN, bit 1: RXEN */
  volatile uint32_t
      INTSTATUS; /* Offset 0x0C: Interrupt Status / Clear Register */
  volatile uint32_t BAUDDIV; /* Offset 0x10: Baudrate Divider Register */
} MCU_UART;

/* CMSDK APB UART Bit Field Definitions */
#define UART_STATE_TXFULL (1U << 0)
#define UART_STATE_RXFULL (1U << 1)
#define UART_CTRL_TXEN (1U << 0)
#define UART_CTRL_RXEN (1U << 1)

#define UART0 ((volatile MCU_UART *)UART0_BASE)
#endif

int uart_wr(char *s);