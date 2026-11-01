# Raspberry Pi Pico USB CDC Driver (`model/firmware/drivers/usb`)

Full-duplex USB CDC Serial driver for the Raspberry Pi Pico (RP2040 / Cortex-M0+).

---

## 1. Driver API

The driver exports three primary functions in [`hdrs/usb.h`](hdrs/usb.h):

```c
#include "hdrs/usb.h"

// 1. Initialize USB CDC subsystem (clocks, transceiver, enumeration state machine)
int init_usb(void);

// 2. Transmit null-terminated string over USB
int write_usb(const char *s);

// 3. Read incoming bytes non-blocking (returns number of bytes read)
int read_usb(char *buf, int max_len);
```

---

## 2. External Dependencies Manifest

External git dependencies are formally declared in [`manifest.json`](manifest.json):

| Dependency | Repository | Submodules | Purpose |
| :--- | :--- | :--- | :--- |
| **`pico-sdk`** (v2.1.0) | `https://github.com/raspberrypi/pico-sdk.git` | `lib/tinyusb` | RP2040 boot2 loader, 48 MHz USB PLL, and TinyUSB CDC stack |

To pull or link dependencies, run:
```bash
./model/firmware/drivers/usb/pull_dependencies.sh
```

---

## 3. Build Instructions

```bash
# 1. Ensure Arm GNU Toolchain (arm-none-eabi-gcc) is in your PATH
# export PATH="/path/to/arm-none-eabi/bin:$PATH"

# 2. Build via CMake
mkdir -p model/firmware/drivers/usb/build
cd model/firmware/drivers/usb/build
cmake ..
make -j4
```

This generates `test_usb.uf2`.

---

## 4. Flash and Monitor

```bash
# Flash to Pico (when in BOOTSEL mode)
picotool load test_usb.uf2 -f
picotool reboot

# Or drag-and-drop to /Volumes/RPI-RP2
cp test_usb.uf2 /Volumes/RPI-RP2/

# Monitor live serial logs
screen /dev/cu.usbmodem* 115200
```
