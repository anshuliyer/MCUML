# Simulation Tools (`tools/sim`)

Cortex-M33 simulation, UART streaming, and GDB debugging for QEMU (`mps2-an505`).

## Modules
- **`sim_connect.py`**: QEMU runner targeting Cortex-M33. Flashes binaries via `--kernel` and exposes all native QEMU flags. Supports `--h`.
- **`uart.py`**: Bi-directional UART client/server over TCP, UNIX socket, or serial TTY with pattern matching (`--expect`). Supports `--h`.
- **`debug.py`**: GDB wrapper (interactive/batch) to inspect registers (`--read-regs`) and dump memory (`--read-mem`). Supports `--h`.

## Quickstart (Linux VM)
```bash
# 1. System packages
sudo apt update && sudo apt install -y qemu-system-arm gdb-multiarch python3 python3-pip

# 2. Python dependencies
pip install -r tools/requirements.txt

# 3. Run prebuilt test binary
python3 tools/sim/sim_connect.py --kernel tools/test_binary/firmware.elf
```

## Common Commands
```bash
# Run simulation
python3 tools/sim/sim_connect.py --kernel <path.elf>

# Stream UART output (QEMU listening on TCP 5555)
python3 tools/sim/sim_connect.py --kernel <path.elf> --serial tcp:127.0.0.1:5555,server,wait &
python3 tools/sim/uart.py --port 5555 --expect "Test Binary For Sim"

# Connect GDB (paused at startup)
python3 tools/sim/sim_connect.py --kernel <path.elf> -s -S &
python3 tools/sim/debug.py --elf <path.elf> --read-regs
```

## Python API
```python
from tools.sim import QemuSimulator, UartStreamer, GdbSession

sim = QemuSimulator(kernel="tools/test_binary/firmware.elf")
sim.start()
sim.wait(timeout=2.0)
sim.stop()
```
