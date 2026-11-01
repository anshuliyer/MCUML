# ==============================================================================
# MCUML Minimal Makefile
#
# Build:
#   make build [c=code.c] [i=headers] [s=startup] [l=linker] [o=outdir] [m=pico|qemu]
#
# Run:
#   make run-qemu [BIN=path/to/binary.elf]
#   make run-pico [BIN=path/to/binary]
#   make monitor
# ==============================================================================

.PHONY: all build run-qemu run-pico monitor clean help

all: build

# Simple build forwarding flags
build:
	@./build $(if $(C),-c $(C),$(if $(c),-c $(c),)) \
	         $(if $(I),-i $(I),$(if $(i),-i $(i),)) \
	         $(if $(S),-s $(S),$(if $(s),-s $(s),)) \
	         $(if $(L),-l $(L),$(if $(l),-l $(l),)) \
	         $(if $(O),-o $(O),$(if $(o),-o $(o),)) \
	         $(if $(M),-m $(M),$(if $(m),-m $(m),))

# Run in QEMU (Cortex-M)
run-qemu:
	@./run qemu $(if $(BIN),$(BIN),$(if $(b),$(b),))

# Flash to Raspberry Pi Pico (auto BOOTSEL, convert to UF2, flash)
run-pico:
	@./run pico $(if $(BIN),$(BIN),$(if $(b),$(b),))

# Open serial monitor
monitor:
	@./run monitor

clean:
	@./build clean

help:
	@./build -h
