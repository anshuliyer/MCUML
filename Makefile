# ==============================================================================
# MCUML Top-Level Makefile
# Pure build management: presil, postsil, deps, clean.
# For running, use: ./run presil -b <binary> or ./run postsil -b <binary>
# ==============================================================================

.PHONY: all deps presil postsil clean help

all: presil postsil

# Pull external dependencies (Pico SDK submodules + Python packages)
deps:
	@bash $(CURDIR)/deps/pull_deps.sh

# Compile Pre-Silicon (QEMU / Cortex-M0+)
presil:
	@$(MAKE) -f makefiles/build presil $(MAKEOVERRIDES)

# Compile Post-Silicon (Pico RP2040)
postsil:
	@$(MAKE) -f makefiles/build postsil $(MAKEOVERRIDES)

# Remove build artifacts
clean:
	@$(MAKE) -f makefiles/build clean

help:
	@echo "MCUML Build System"
	@echo ""
	@echo "Build Targets:"
	@echo "  make deps      - Install SDK and Python requirements"
	@echo "  make presil    - Build Pre-Silicon ELF binary"
	@echo "  make postsil   - Build Post-Silicon UF2 binary"
	@echo "  make clean     - Clean build artifacts"
	@echo ""
	@echo "Run Commands (use ./run with -b flag):"
	@echo "  ./run presil -b <path/to/binary.elf>"
	@echo "  ./run postsil -b <path/to/binary.uf2>"
	@echo "  ./run monitor"
