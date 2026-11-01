#include <stdint.h>
uint32_t volatile *RESETS_RESET = (uint32_t *)0x4000C000;
uint32_t volatile *RESETS_RESET_DONE = (uint32_t *)0x4000C008;
uint32_t volatile *PADS_BANK0_GPIO25 = (uint32_t *)0x4001C068;
uint32_t volatile *GPIO25_CTRL = (uint32_t *)0x400140CC;
uint32_t volatile *SIO_GPIO_OE_SET = (uint32_t *)0xD0000024;
uint32_t volatile *SIO_GPIO_OUT_SET = (uint32_t *)0xD0000014;
uint32_t volatile *SIO_GPIO_OUT_CLR = (uint32_t *)0xD0000018;

int main() {
  *RESETS_RESET = (*RESETS_RESET) & ~((1 << 5) | (1 << 8));

  while (((*RESETS_RESET_DONE) & ((1 << 5) | (1 << 8))) !=
         ((1 << 5) | (1 << 8))) {
  }

  // Clear Output Disable (OD, bit 7) and enable Input Enable (IE, bit 6)
  *PADS_BANK0_GPIO25 = (*PADS_BANK0_GPIO25 & ~(1 << 7)) | (1 << 6);

  *GPIO25_CTRL = 5;
  *SIO_GPIO_OE_SET = (1 << 25);

  while (1) {
    *SIO_GPIO_OUT_SET = (1 << 25);
  }
  return 0;
}