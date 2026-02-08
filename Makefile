PYTHON ?= python3

.PHONY: install-dev lint format test build

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .
	$(PYTHON) -m mypy agents core tests

format:
	$(PYTHON) -m black .
	$(PYTHON) -m ruff check . --fix

test:
	$(PYTHON) -m pytest -q

build:
	$(PYTHON) -m build
