# CONTRIBUTING — amp-benchkit

Thanks for helping improve the audio amplifier bench kit! This guide covers setup, style, tests, and PR etiquette.

## Dev setup
```bash
git clone https://github.com/bwedderburn/amp-benchkit.git
cd amp-benchkit
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt || true
```
Optional:
```bash
# docs
pip install .[docs] || true
mkdocs serve
```

## Pre-commit & style
```bash
pip install pre-commit && pre-commit install
pre-commit run --all-files --show-diff-on-failure
```
- Formatting: `black`/`ruff-format` (as configured), lint with `ruff`.
- Typing: prefer type hints on public APIs; `mypy` if configured.
- Keep imports tidy and files with a trailing newline.

## Project structure
```
amp_benchkit/            # package modules (drivers, dsp, gui helpers, utils)
tests/                   # pytest suite
unified_gui_layout.py    # entrypoint (gui/selftest)
docs/                    # MkDocs
```
Add new modules under `amp_benchkit/`; keep tests mirrored in `tests/`.

## Tests
- Default mode uses **fake hardware** so CI can run anywhere.
- Hardware tests are marked; run only when devices are connected:
```bash
pytest -q             # fake-hw by default
pytest -q -m hardware # gated hardware tests
```
- Prefer deterministic fixtures (CSV/JSON/PNG), and small, fast tests.
- Add at least one smoke test when changing behavior.

## Running locally
```bash
# headless smoke
python unified_gui_layout.py selftest
# GUI
python unified_gui_layout.py gui
```

## Commit & PR guidelines
- Use imperative present tense: “Add…”, “Fix…”, “Refactor…”
- Keep commits focused; squash noisy fixups.
- PR description checklist:
  - What changed and why (problem/solution)
  - Test impact (new or updated tests, markers used)
  - Screenshots/artifacts if GUI/plots affected
  - Docs updated if user-facing behavior changed

## Troubleshooting quick notes
- **LabJack U3‑HV**: install Exodriver (`liblabjackusb`); otherwise DAQ paths skip.
- **Tek VISA**: NI‑VISA preferred; fallback `pyvisa-py`. Use `VISA_RESOURCE` to override.
- **Qt**: `pip install PySide6` if GUI fails to launch.
- **Serial port (FY3200S)**: use `FY_PORT=/dev/tty.usbserial-*` or GUI selector.

## Releasing (maintainers)
- Update version in `pyproject.toml` (and package `__init__` if present).
- Update `CHANGELOG.md`.
- Tag and push: `git tag vX.Y.Z && git push --tags`.
- Create GitHub Release and attach any sample artifacts.
