# ==============================================================================
# MCUML Unified Makefile (makefiles/Makefile)
# Convenient wrapper forwarding to makefiles/build and makefiles/run.
# ==============================================================================

ROOT_DIR ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

.PHONY: all deps presil postsil run-presil run-postsil monitor clean help

all: presil postsil

# Dependency management
deps:
	@bash $(ROOT_DIR)/deps/pull_deps.sh

# Build targets
presil:
	$(MAKE) -f $(ROOT_DIR)/makefiles/build presil $(MAKEOVERRIDES)

postsil:
	$(MAKE) -f $(ROOT_DIR)/makefiles/build postsil $(MAKEOVERRIDES)

# Run targets
run-presil:
	$(MAKE) -f $(ROOT_DIR)/makefiles/run presil $(MAKEOVERRIDES)

run-postsil:
	$(MAKE) -f $(ROOT_DIR)/makefiles/run postsil $(MAKEOVERRIDES)

monitor:
	$(MAKE) -f $(ROOT_DIR)/makefiles/run monitor $(MAKEOVERRIDES)

clean:
	$(MAKE) -f $(ROOT_DIR)/makefiles/build clean

help:
	@echo "MCUML Build & Run System"
	@echo "Usage:"
	@echo "  make -f makefiles/build presil   [SRCS=...] [INCS=...] [TARGET=...]"
	@echo "  make -f makefiles/build postsil  [SRCS=...] [INCS=...] [TARGET=...]"
	@echo "  make -f makefiles/run presil     [KERNEL=...] [TIMEOUT=...]"
	@echo "  make -f makefiles/run postsil    [UF2=...]"
	@echo "  make -f makefiles/run monitor"
