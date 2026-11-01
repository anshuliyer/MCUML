// header for uart
#include <stdint.h>

#ifdef POSTSIL
#define UART0_BASE (0x40034000)

typedef struct {
  volatile uint32_t UARTDR;        /* 0x00: Data Register */
  volatile uint32_t UARTRSR;       /* 0x04: Receive Status Register / Error Clear */
  volatile uint32_t _reserved0[4]; /* 0x08 - 0x14 */
  volatile uint32_t UARTFR;        /* 0x18: Flag Register (bit 5: TXFF) */
  volatile uint32_t _reserved1;    /* 0x1C */
  volatile uint32_t UARTILPR;      /* 0x20: IrDA Low-power Counter */
  volatile uint32_t UARTIBRD;      /* 0x24: Integer Baud Rate */
  volatile uint32_t UARTFBRD;      /* 0x28: Fractional Baud Rate */
  volatile uint32_t UARTLCR_H;     /* 0x2C: Line Control */
  volatile uint32_t UARTCR;        /* 0x30: Control Register */
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