# MCUML External Dependencies (`deps/`)

This directory contains external repositories and SDK dependencies required for bare-metal firmware and drivers.

## Components

### `pico-sdk`
- **Repository:** `https://github.com/raspberrypi/pico-sdk.git`
- **Submodules:** `lib/tinyusb` (`https://github.com/hathach/tinyusb.git`)
- **Usage:** Provides RP2040 boot2 stage, hardware clocks, peripheral abstractions, and USB CDC TinyUSB stack for the Raspberry Pi Pico.

## Fetch All Dependencies (Fresh Machine)

Run from the repository root:
```bash
make deps
```
Or directly:
```bash
./deps/pull_deps.sh
```
