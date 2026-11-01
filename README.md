# MCUML

Embedded Machine Learning and ARM Cortex-M0+ (Raspberry Pi Pico / RP2040) Simulation Framework.

## Quickstart (Fresh Linux VM)

```bash
# 1. Install QEMU & GDB
sudo apt update && sudo apt install -y qemu-system-arm gdb-multiarch python3 python3-pip

# 2. Install Python dependencies
pip install -r tools/requirements.txt

# 3. Run simulation with prebuilt Cortex-M0+ test binary
python3 tools/sim/sim_connect.py --kernel tools/test_binary/firmware.elf
```

Expected output:
```text
Test Binary For Sim
```

---

## Directory Layout

- **[`tools/sim/`](tools/sim/)**: Simulation tooling.
  - [`sim_connect.py`](tools/sim/sim_connect.py): Cortex-M33 QEMU launcher with passthrough flag support.
  - [`uart.py`](tools/sim/uart.py): UART streaming, logging, and test assertion utility.
  - [`debug.py`](tools/sim/debug.py): GDB automation and register/memory inspection.
- **[`tools/test_binary/`](tools/test_binary/)**: Prebuilt Cortex-M33 test firmware (`firmware.elf`, `firmware.bin`).
- **[`tools/requirements.txt`](tools/requirements.txt)**: Python package requirements.
