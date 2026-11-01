// systick arm timer reges
#include <stdint.h>
#define SYST_CSR ((volatile uint32_t *)0xE000E010)
#define SYST_RVR ((volatile uint32_t *)0xE000E014)
#define SYST_CVR ((volatile uint32_t *)0xE000E018)
#define SYST_CALIB ((volatile uint32_t *)0xE000E01C)
#define WATCHDOG_TICK ((volatile uint32_t *)0x4005802C)

typedef struct {
  uint8_t bytes[3];
} uint24_t;

int delay(int time);
