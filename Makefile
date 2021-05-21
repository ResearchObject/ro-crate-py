.DEFAULT_GOAL := install

SHELL := /bin/bash
PYTHON ?= python3
VENV_DIR ?= venv
IN_VENV = [ -f $(VENV_DIR)/bin/activate ] && . $(VENV_DIR)/bin/activate;


$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)
	$(IN_VENV) pip install --upgrade pip

$(VENV_DIR)/bin/flake8: $(VENV_DIR)
	$(IN_VENV) pip install flake8

$(VENV_DIR)/bin/pytest: $(VENV_DIR)
	$(IN_VENV) pip install pytest

init-venv: $(VENV_DIR)

install: $(VENV_DIR)
	$(IN_VENV) pip install -r requirements.txt
	$(IN_VENV) pip install ./

lint: $(VENV_DIR)/bin/flake8
	$(IN_VENV) flake8 --exclude $(VENV_DIR) ./

test: $(VENV_DIR)/bin/pytest install
	$(IN_VENV) pytest test

# WARNING: removes ALL untracked files
clean:
	git clean -fdx -e $(VENV_DIR)

.PHONY: init-venv install lint test clean $(VENV_DIR)
