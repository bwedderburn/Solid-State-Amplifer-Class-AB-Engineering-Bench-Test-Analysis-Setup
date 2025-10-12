# Repository Guidelines

## Project Structure & Module Organization
Core modules live in `amp_benchkit/`, spanning instrument drivers, DSP helpers, Qt panes, and shared utilities. Integration and regression tests reside in `tests/`, defaulting to fake hardware fixtures so contributors can validate flows without lab gear. Documentation sources (MkDocs) live under `docs/`, while `unified_gui_layout.py` provides the unified entry point for both `gui` and `selftest` modes. Supporting automation—`pyproject.toml`, `.pre-commit-config.yaml`, `requirements*.txt`, and `Makefile`—sits at the repository root.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create and enter an isolated environment.
- `pip install -r requirements.txt` (plus `-r requirements-dev.txt`) — install runtime and developer tooling.
- `pre-commit run --all-files --show-diff-on-failure` — enforce Ruff, Black, MyPy, and ancillary checks.
- `python unified_gui_layout.py selftest` — run a headless smoke test against the fake hardware stack.
- `python unified_gui_layout.py gui` — launch the Qt GUI for manual workflows.
- `pytest -q` (`pytest -q -m "hardware"`) — execute the automated suite; hardware runs stay opt-in.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, expressive `snake_case` for modules and functions, and `UpperCamelCase` for Qt widget classes. Keep public APIs typed, prefer dataclasses or TypedDicts for structured payloads, and let pre-commit tools manage formatting and import ordering. Document complex signal-processing routines with concise docstrings describing units and expectations.

## Testing Guidelines
Add new coverage under `tests/`, naming files `test_<area>.py` and functions `test_<behavior>`. Reuse fake instrument fixtures to keep CI deterministic; mark real-device scenarios with `@pytest.mark.hardware`. Exercise DSP code with numeric tolerances, validate instrument protocol parsing round-trips, and confirm GUI flows via headless `selftest` or Qt bot helpers. Capture artifacts by setting `AMPBENCHKIT_SESSION_DIR=/path/to/results` when appropriate.

## Commit & Pull Request Guidelines
Write focused commits with imperative subjects (e.g., `Add LabJack voltage scaling`) and include rationale plus validation commands in the body. Pull requests should summarize scope, link issues or roadmap items, state `pre-commit`/`pytest` results, and attach screenshots or logs when changing GUI or capture behavior. Update `CHANGELOG.md` for user-facing adjustments and tag domain owners (instrumentation, GUI, QA) when their components are affected.

## Configuration & Environment Tips
Set `AMPBENCHKIT_FAKE_HW=1` to force simulators during development. Override device discovery with `FY_PORT`, `VISA_RESOURCE`, or `U3_CONNECTION` for targeted sessions. Keep work inside the virtual environment to ensure consistent driver versions, and stash session outputs under `results/` or a custom directory referenced by `AMPBENCHKIT_SESSION_DIR`.
