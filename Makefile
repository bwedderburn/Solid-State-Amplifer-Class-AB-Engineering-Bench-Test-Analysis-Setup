PYTHON := python

.PHONY: install-dev test lint type format build dist clean install-exodriver pre-commit

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev,test,gui]
	pre-commit install || true

test:
	pytest -q

lint:
	ruff check .

type:
	mypy amp_benchkit unified_gui_layout.py

format:
	black .
	ruff check --fix .

build:
	$(PYTHON) -m build --sdist --wheel

dist: clean build

clean:
	rm -rf build dist *.egg-info

install-exodriver:
	./scripts/install_exodriver_alpine.sh

pre-commit:
	pre-commit run --all-files
# Convenience Makefile for amp-benchkit
SHELL := /bin/bash
VENV = .venv
PY = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: help venv deps install-exodriver check-usb gui selftest clean docker-build lint format test coverage type

help:
	@echo 'Targets:'
	@echo '  make venv              - create virtual environment'
	@echo '  make deps              - install python dependencies'
	@echo '  make install-exodriver - build & install Exodriver (USB driver)'
	@echo '  make check-usb         - run LabJack USB diagnostic'
	@echo '  make gui               - launch GUI (if display available)'
	@echo '  make selftest          - run headless selftest mode'
	@echo '  make docker-build      - build container image'
	@echo '  make lint              - run ruff lint checks'
	@echo '  make format            - run black formatter'
	@echo '  make test              - run pytest (unit tests)'
	@echo '  make coverage          - run pytest with coverage'
	@echo '  make type              - run mypy (best effort)'
	@echo '  make clean             - remove build artifacts'

venv:
	python3 -m venv $(VENV)
	@echo 'Activate with: source $(VENV)/bin/activate'

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e .[test,dev,gui]
	# Ensure tooling is available even if optional extras change
	$(PIP) install black ruff mypy pytest pytest-cov

install-exodriver:
	chmod +x scripts/install_exodriver_alpine.sh
	./scripts/install_exodriver_alpine.sh || true

check-usb: deps install-exodriver
	$(PY) scripts/check_labjack_usb.py || true

selftest: deps
	$(PY) unified_gui_layout.py selftest

gui: deps
	$(PY) unified_gui_layout.py gui --gui

docker-build:
	docker build -t amp-benchkit:latest .

clean:
	rm -rf $(VENV) __pycache__ */__pycache__ build dist *.egg-info

lint: deps
	$(VENV)/bin/ruff check .

format: deps
	$(VENV)/bin/black .

test: deps
	$(PY) -m pytest -q

coverage: deps
	$(PY) -m pytest --cov=amp_benchkit --cov-report=term-missing

type: deps
	$(VENV)/bin/mypy amp_benchkit unified_gui_layout.py
