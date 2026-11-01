#include "hdr/uart.h"

void main() {
  char s[4] = "abc";
  uart_wr(s);
}