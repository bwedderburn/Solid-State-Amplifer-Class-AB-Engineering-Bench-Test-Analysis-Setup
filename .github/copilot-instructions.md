# Copilot / AI Agent Project Instructions

Concise, codebase-specific guidance for productive, safe AI-driven changes. Focus on actionable, project-unique patterns and workflows.

## 1. Architecture & Key Patterns
- **Legacy entrypoint**: `unified_gui_layout.py` (monolithic, ~1300 lines) orchestrates CLI and multi-tab GUI. New logic should be extracted to modules in `amp_benchkit/`.
- **Modular helpers**:
  - `amp_benchkit.deps`: Dependency detection (Qt, pyvisa, pyserial, LabJack). Always gate hardware/GUI logic via flags like `HAVE_QT`.
  - `amp_benchkit.fy`, `tek`, `u3util`, `u3config`: Instrument abstraction layers (FY function gen, Tektronix VISA, LabJack U3). Use/reuse custom exceptions (`FYError`, `TekError`).
  - `amp_benchkit.dsp`: Signal KPIs (RMS, PkPk, THD FFT, bandwidth knees). Always return Python floats or tuples; return `nan` on invalid input.
  - `amp_benchkit.automation`: Headless sweep orchestration; inject instrument functions for testability. Used by both GUI and CLI.
  - `amp_benchkit.gui/*.py`: Each tab is a pure builder function returning a `QWidget` given a context. No side effects; follow the extraction pattern.
- **Public API**: Only functions listed in README's "Public API" section are stable. Do not break signatures without a minor version bump.

## 2. CLI & Entry Points
- Use console scripts (`amp-benchkit`, `amp-benchkit-gui`)—these map to `amp_benchkit.cli:main`/`main_gui` and delegate to `unified_gui_layout.main()`.
- **Available subcommands**: `selftest`, `diag`, `gui`, `config-dump`, `config-reset`, `sweep` (generates frequency points).
- Add new CLI subcommands by extracting logic to a new module, then wiring into `unified_gui_layout.py` (see `argparse`).
- Frequency sweeps: Use `automation.build_freq_points` (6-decimal rounding, inclusive endpoints). Tests assert tight tolerances.
- **CLI invocation**: `python unified_gui_layout.py <subcommand>` or `amp-benchkit <subcommand>` after install.

## 3. Dependency & Environment Handling
- **Python versions**: Support Python 3.10, 3.11, 3.12 (CI tests on 3.11 & 3.12).
- Always feature-detect using flags from `deps.py` (e.g., `HAVE_QT`, `HAVE_PYVISA`, `HAVE_SERIAL`, `HAVE_U3`).
- GUI must run headless: guard all Qt usage; force `matplotlib.use('Agg')` at top.
- LabJack/Exodriver is optional; tests must not hard-fail if USB is absent. Wrap hardware access in try/except.
- **Dependency groups**: Core deps in `requirements.txt` / `pyproject.toml`. Optional: `[gui]`, `[dev]`, `[test]`, `[publish]`.
- Always check feature flags before importing optional dependencies (prevents import errors in minimal environments).

## 4. Conventions & Patterns
- **Logging**: Use `amp_benchkit.logging.get_logger()`. Enable DEBUG with `--verbose`. Avoid `print()` except for CLI output.
- **Config**: Use `amp_benchkit.config.update_config(...)`/`load_config()`. Never write ad-hoc files; config persists under `~/.config/amp-benchkit/`.
- **DSP return shapes**: Always return Python floats or tuples. THD returns `(thd_ratio, f0_est, fund_amp)`.
- **Fail soft**: Instrument operations must catch/log individual frequency failures but continue sweeps.
- **Error handling**: Use custom exceptions (`FYError`, `TekError`, `FYTimeoutError`, `TekTimeoutError`). Hardware operations should gracefully handle timeouts and missing devices.
- **Testing**: Use `pytest` (see `tests/`). New features require at least one targeted test unless purely internal. Coverage gate: 70% (CI).
- **Pre-commit**: Enable with `pre-commit install`. Blocks large binaries/venvs and runs ruff/mypy.
- **Return values**: Prefer explicit return types. Use `nan` for invalid numeric results. Avoid exceptions in DSP unless input is catastrophically malformed.

## 5. GUI Tab Extraction
- New tabs: Add `build_<name>_tab(ctx) -> QWidget` in `amp_benchkit/gui/`. Wire into `unified_gui_layout.UnifiedGUI.__init__` using `tabs.addTab(builder(...), "Label")`.
- Use `deps.fixed_font()` and feature flags. Avoid blocking calls in GUI thread.

## 6. Build, Test, and Release
- **Testing**: `pytest -q` (basic) or `pytest -q --cov=amp_benchkit --cov-report=term-missing --cov-fail-under=70` (with coverage as in CI).
- **Linting**: `ruff check .` (errors/warnings) or `ruff check . --fix` (auto-fix).
- **Type checking**: `mypy --ignore-missing-imports amp_benchkit` (best-effort; some modules incomplete).
- **Pre-commit**: Install hooks with `pre-commit install`. Runs ruff/mypy automatically on commit.
- **CI**: GitHub Actions runs tests on Python 3.11/3.12, enforces 70% coverage threshold, and builds distributions.
- **Make targets**: Currently minimal (Makefile mostly empty). Use direct commands above instead.
- **Release**: Update `pyproject.toml` version and `CHANGELOG.md`, commit, tag (e.g., `v0.3.2`), then `python -m build && twine upload dist/*`. See README and CONTRIBUTING for full release workflow.

## 7. File Organization & Structure
- **Core modules** live in `amp_benchkit/`: Each instrument type, utility, and GUI tab in its own file.
- **Tests** in `tests/`: One `test_*.py` per module. Use `conftest.py` for shared fixtures.
- **Legacy entrypoint**: `unified_gui_layout.py` at repo root (will gradually shrink as extraction continues).
- **Scripts**: `scripts/` for installers and utilities (e.g., Exodriver installer).
- **Documentation**: `README.md` (user-facing), `CONTRIBUTING.md` (developer), `ROADMAP.md` (planning), specialized docs (`EXODRIVER.md`, `VERIFY_SIGNING.md`).
- **Config files**: `.pre-commit-config.yaml`, `ruff.toml`, `mypy.ini`, `pyproject.toml` for tooling.

## 8. Non-Goals for Agents
- Do **not** attempt to fully rewrite `unified_gui_layout.py` in one PR; extract incrementally.
- Do **not** add new heavyweight dependencies without discussion.
- Avoid global state/singletons—prefer dependency injection as in `automation.py`.

---
For unclear or missing patterns, propose a diff for this file. Maintainers will clarify and refine.
Questions or missing patterns? Provide a diff proposal; maintainers can clarify to refine these instructions.
