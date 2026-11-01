#include "../drivers/timer/hdrs/systick.h"
#include "../drivers/usb/hdrs/usb.h"
#include "string.h"
int main() {
  init_usb();
  for (int i = 0; i < 3000000; i++) {
    write_usb("..\n");
    delay(20000);
    write_usb("MCMU USB BL1\n");
  }
  return 0;
}