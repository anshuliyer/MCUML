# ==============================================================================
# MCUML Top-Level Makefile
# Forwards commands to makefiles/build and makefiles/run.
# ==============================================================================

.PHONY: all deps presil postsil run-presil run-postsil monitor clean help

all: presil postsil

# Pull and install all dependencies (Pico SDK submodules + Python packages)
deps:
	@bash $(CURDIR)/model/firmware/drivers/usb/pull_dependencies.sh
	@pip3 install -r $(CURDIR)/tools/requirements.txt

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
