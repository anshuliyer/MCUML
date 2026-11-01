#include "hdrs/systick.h"

int watchdog_init(void) {
  *WATCHDOG_TICK = 0x20C;
  return 0;
}

int delay(int time) {
  watchdog_init();
  *SYST_CSR = 0;
  *SYST_RVR = time & 0x00FFFFFF;
  *SYST_CVR = 0;
  *SYST_CSR = 5;
  while ((*SYST_CSR & (1 << 16)) == 0) {
  }
  *SYST_CSR = 0;
  return 0;
}