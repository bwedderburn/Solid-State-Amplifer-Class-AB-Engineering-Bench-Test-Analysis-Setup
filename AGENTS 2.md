# Repository Guidelines

## Project Structure & Module Organization
Core drivers, automation flows, and shared widgets live in `amp_benchkit/`; mirror this layout in `tests/` for straightforward discovery. Keep quick-launch scripts such as `unified_gui_layout.py` at the repository root for GUI smoke checks. Store developer utilities in `scripts/`, persistent captures in `results/`, and documentation updates in `docs/` or `ROADMAP.md`.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create and enter the repo-local virtual environment.
- `pip install -e .[dev,test,gui]` — install runtime dependencies with linting, typing, and GUI extras.
- `make deps` — bootstrap the same dependency set for fresh clones.
- `pytest -q` — run the unit suite; export `AMPBENCHKIT_FAKE_HW=1` when hardware is offline.
- `make gui` or `python unified_gui_layout.py gui` — launch the Qt interface for manual verification.

## Coding Style & Naming Conventions
Target Python 3.10+ with typed public APIs. Run `black` (configured for 100-character lines) and `ruff` via `pre-commit` before committing. Use `snake_case` for functions and modules, `CamelCase` for Qt widgets and drivers, and uppercase constants for configuration keys. Document hardware assumptions inline whenever behavior diverges from lab defaults.

## Testing Guidelines
Name pytest modules `test_<module>.py` and place shared fixtures under `tests/fixtures/`. Skip hardware-dependent tests automatically when devices are absent, and exercise simulator paths with `AMPBENCHKIT_FAKE_HW=1`. Maintain coverage across signal generation, instrument I/O, and GUI command flows, keeping golden CSV/JSON artifacts next to tests when validating capture pipelines.

## Commit & Pull Request Guidelines
Write imperative, present-tense commit subjects (for example, “Add scope simulator hooks”) and keep bodies concise. Run `pre-commit run --all-files` plus `pytest -q` before pushing. Pull requests should link related issues, summarize user-facing changes, and attach screenshots or captured artifacts for GUI or plotting updates. Record release-impacting notes in `CHANGELOG.md` within the same PR.

## Security & Configuration Tips
Never commit device serial numbers or lab credentials. Override discovery via environment variables such as `FY_PORT`, `VISA_RESOURCE`, and `AMPBENCHKIT_SESSION_DIR` when scripting. Document new hardware setup steps in `EXODRIVER.md` or `SECURITY.md`, and surface missing dependencies (VISA backends, Exodriver) with actionable error messages.
