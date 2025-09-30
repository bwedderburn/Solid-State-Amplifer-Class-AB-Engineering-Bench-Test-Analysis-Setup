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
- Add new CLI subcommands by extracting logic to a new module, then wiring into `unified_gui_layout.py` (see `argparse`).
- Frequency sweeps: Use `automation.build_freq_points` (6-decimal rounding, inclusive endpoints). Tests assert tight tolerances.

## 3. Dependency & Environment Handling
- Always feature-detect using flags from `deps.py` (e.g., `HAVE_QT`, `HAVE_PYVISA`).
- GUI must run headless: guard all Qt usage; force `matplotlib.use('Agg')` at top.
- LabJack/Exodriver is optional; tests must not hard-fail if USB is absent. Wrap hardware access in try/except.

## 4. Conventions & Patterns
- **Logging**: Use `amp_benchkit.logging.get_logger()`. Enable DEBUG with `--verbose`. Avoid `print()` except for CLI output.
- **Config**: Use `amp_benchkit.config.update_config(...)`/`load_config()`. Never write ad-hoc files; config persists under `~/.config/amp-benchkit/`.
- **DSP return shapes**: Always return Python floats or tuples. THD returns `(thd_ratio, f0_est, fund_amp)`.
- **Fail soft**: Instrument operations must catch/log individual frequency failures but continue sweeps.
- **Testing**: Use `pytest` (see `tests/`). New features require at least one targeted test unless purely internal. Coverage gate: 70% (CI).
- **Pre-commit**: Enable with `pre-commit install`. Blocks large binaries/venvs and runs ruff/mypy.

## 5. GUI Tab Extraction
- New tabs: Add `build_<name>_tab(ctx) -> QWidget` in `amp_benchkit/gui/`. Wire into `unified_gui_layout.UnifiedGUI.__init__` using `tabs.addTab(builder(...), "Label")`.
- Use `deps.fixed_font()` and feature flags. Avoid blocking calls in GUI thread.

## 6. Build, Test, and Release
- Use `make` targets: `make selftest`, `make gui`, `make lint`, `make type`, `make test`, `make coverage`.
- Manual: `ruff check .`, `mypy .`, `pytest -q`.
- Release: Update `pyproject.toml` and `CHANGELOG.md`, tag, build, and push. See README for full steps.

## 7. Non-Goals for Agents
- Do **not** attempt to fully rewrite `unified_gui_layout.py` in one PR; extract incrementally.
- Do **not** add new heavyweight dependencies without discussion.
- Avoid global state/singletons—prefer dependency injection as in `automation.py`.

---
For unclear or missing patterns, propose a diff for this file. Maintainers will clarify and refine.
Questions or missing patterns? Provide a diff proposal; maintainers can clarify to refine these instructions.
