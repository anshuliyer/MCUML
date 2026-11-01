# Minimal Linker Script (`model/firmware/linker`)

Minimal bare-metal linker script for Cortex-M0+ (RP2040 / ARMv6-M) in QEMU.

## Memory Map
- **FLASH**: `0x10000000` (512 KB) – Boot address / vector table & code
- **RAM**: `0x20000000` (16 KB) – SRAM bank 0

## Sections
- `.vectors`: Vector table at base of FLASH
- `.text`: Program instructions and string constants
- `.data`: Initialized global variables (loaded from Flash to RAM)
- `.bss`: Zero-initialized global variables in RAM
- Stack: Initial `__StackTop` placed at `0x20004000` (top of RAM)

## Compilation Example
```bash
arm-none-eabi-gcc -mcpu=cortex-m0plus -mthumb -ffreestanding -nostdlib \
  -T model/firmware/linker/armv8m.ld \
  model/firmware/startup/startup.c \
  model/firmware/drivers/uart/uart.c \
  model/firmware/drivers/uart/test_uart.c -o test_uart.elf
```
