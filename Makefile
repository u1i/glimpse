INSTALL_DIR := $(HOME)/.local/share/glimpse
BIN_DIR     := $(HOME)/.local/bin
VENV        := $(INSTALL_DIR)/venv

.PHONY: install uninstall

install:
	mkdir -p $(INSTALL_DIR) $(BIN_DIR)
	cp glimpse.py $(INSTALL_DIR)/glimpse.py
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet -r requirements.txt
	@printf '#!/bin/sh\nexec "%s" "%s" "$$@"\n' \
		"$(VENV)/bin/python" "$(INSTALL_DIR)/glimpse.py" \
		> $(BIN_DIR)/glimpse
	chmod +x $(BIN_DIR)/glimpse
	@echo "Installed: $(BIN_DIR)/glimpse"

uninstall:
	rm -f $(BIN_DIR)/glimpse
	rm -rf $(INSTALL_DIR)
	@echo "Removed glimpse"
