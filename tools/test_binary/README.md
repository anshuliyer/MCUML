# Prebuilt Test Binary (`tools/test_binary`)

Precompiled bare-metal ARM Cortex-M33 firmware for QEMU (`mps2-an505`). Outputs `"Test Binary For Sim"` over UART upon reset.

## Files
- **`firmware.elf`**: ELF executable with debug symbols (for QEMU & GDB).
- **`firmware.bin`**: Raw binary image (flashable).

## Run
```bash
python3 tools/sim/sim_connect.py --kernel tools/test_binary/firmware.elf
```
