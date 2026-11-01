# ==============================================================================
# MCUML Top-Level Makefile
# Forwards commands to makefiles/build and makefiles/run.
# ==============================================================================

.PHONY: all deps presil postsil run-presil run-postsil monitor clean help

all: presil postsil

# Pull and install all dependencies (Pico SDK submodules + Python packages)
deps:
	@bash $(CURDIR)/deps/pull_deps.sh

presil:
	$(MAKE) -f makefiles/build presil $(MAKEOVERRIDES)

postsil:
	$(MAKE) -f makefiles/build postsil $(MAKEOVERRIDES)

run-presil:
	$(MAKE) -f makefiles/run presil $(MAKEOVERRIDES)

run-postsil:
	$(MAKE) -f makefiles/run postsil $(MAKEOVERRIDES)

monitor:
	$(MAKE) -f makefiles/run monitor $(MAKEOVERRIDES)

clean:
	$(MAKE) -f makefiles/build clean

help:
	@$(MAKE) -f makefiles/build help
