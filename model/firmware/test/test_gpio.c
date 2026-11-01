
#include <stdint.h>
uint32_t volatile *RESETS_RESET = 0x4000C000;
uint32_t volatile *RESETS_RESET_DONE = 0x4000C008;
uint32_t volatile *GPIO25_CTRL = 0x400140C8;
uint32_t volatile *SIO_GPIO_OE_SET = 0xD0000024;
uint32_t volatile *SIO_GPIO_OUT_SET = 0xD0000014;
uint32_t volatile *SIO_GPIO_OUT_CLR = 0xD0000018;

int main() {
  *RESETS_RESET = (*RESETS_RESET) & (0xFFDF);

  while (((*RESETS_RESET_DONE) & (1 << 5)) == 0) {
  }
  *GPIO25_CTRL = 5;
  *SIO_GPIO_OE_SET = (1 << 25);
  while (1) {

    *SIO_GPIO_OUT_SET = (*SIO_GPIO_OUT_SET) | (1 << 25);
  }
  return 0;
}
