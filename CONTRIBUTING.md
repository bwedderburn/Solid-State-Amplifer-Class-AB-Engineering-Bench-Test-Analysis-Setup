# Repository Guidelines

## Project Structure & Module Organization
`amp_benchkit/` houses instrument drivers, DSP helpers, GUI utilities, and shared configuration. Tests live in `tests/` and default to fake hardware so they can run on any workstation or CI runner. Documentation sources reside under `docs/`, while `unified_gui_layout.py` is the launcher for both the Qt GUI (`gui`) and headless smoke (`selftest`).

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create an isolated environment.
- `pip install -r requirements.txt && pip install -r requirements-dev.txt || true` — install runtime and optional tooling dependencies.
- `pre-commit run --all-files --show-diff-on-failure` — enforce formatting, linting, and type checks.
- `pytest -q` — execute the fake-hardware test suite; add `-m hardware` only when instruments are attached.
- `python unified_gui_layout.py selftest` — run the CLI smoke test to validate the current stack.
- `python unified_gui_layout.py gui` — launch the Qt interface for manual verification.

## Coding Style & Naming Conventions
Follow Python 3 standards with 4-space indentation and explicit type hints. Keep module and function names in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Formatting and import order are enforced by Black and Ruff; never hand-edit around their expectations, instead rely on `pre-commit`. Favor descriptive names that reference the instrument or signal being handled (e.g., `scope_capture`, `generator_profile`).

## Testing Guidelines
Write tests with `pytest` and place fixtures in `tests/conftest.py` when they support multiple modules. Default to fake hardware, but guard real-instrument coverage with `@pytest.mark.hardware` so CI can skip it gracefully. Name new tests after the behavior under scrutiny (e.g., `test_generator_waveform_limits`).

## Commit & Pull Request Guidelines
Craft commit subjects in the imperative mood (e.g., “Add crest-factor sweep”), limit them to ~72 characters, and group logical changes together. Reference relevant modules or instruments in the body, and note any hardware dependency. Pull requests should summarize behavior changes, list test commands executed, link to related issues, and include screenshots or log snippets for GUI or capture updates.

## Configuration & Security Notes
Use environment variables to control runtime behavior: `AMPBENCHKIT_FAKE_HW=1` to force simulators, `AMPBENCHKIT_SESSION_DIR` to store captures, and instrument overrides such as `FY_PORT`, `VISA_RESOURCE`, or `U3_CONNECTION`. Avoid committing credentials or machine-specific VISA strings; prefer documenting them in local `.env` files ignored by git.
