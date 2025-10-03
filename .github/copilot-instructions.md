## Amp BenchKit – AI Contributor Guide (Concise)
Focused, codebase-specific rules so an agent can make safe, high‑leverage changes quickly. Prefer incremental extraction over large rewrites.

### 1. Architecture Snapshot
Monolith bridge: `unified_gui_layout.py` = thin CLI/GUI dispatcher (argparse + small selftests). Real logic lives in modular packages under `amp_benchkit/`.
Core modules:
* `deps.py` – Detect optional deps (Qt, pyvisa, pyserial, LabJack). Use feature flags (`HAVE_QT`, `HAVE_PYVISA`, etc.) before any hardware/GUI call. Provide user-facing hints via `INSTALL_HINTS` / `dep_msg()`.
* `automation.py` – Pure(ish) orchestration: builds frequency lists (`build_freq_points`), sweeps (`sweep_scope_fixed`, `sweep_audio_kpis`) using dependency-injected callables. Maintain “fail soft”: log and continue on per‑frequency errors.
* `dsp.py` – Deterministic numeric helpers. Always return Python floats (or tuple) and `nan` on invalid input. THD signature: `(thd_ratio, f0_est, fund_amp)`.
* Instruments: `fy.py`, `tek.py`, `u3util.py`, `u3config.py` – Keep side effects localized; reuse custom exceptions (e.g. `FYError`, `TekError`).
* GUI tabs (`amp_benchkit/gui/*.py`) – Each `build_<name>_tab(gui)` returns a ready `QWidget`, attaches widget refs onto the passed controller object, and performs zero I/O or long blocking work during build.

### 2. Public Surface & Stability
Treat only functions enumerated in README “Public API” + console scripts (`amp-benchkit`, `amp-benchkit-gui`) as stable. Do not rename or change signatures without a minor version bump. New functionality: add beside existing modules—do not expand the monolith.

### 3. CLI / Sweep Rules
Add subcommands by editing `unified_gui_layout.build_parser()` minimally; delegate real work to a new module. Frequency generation must use `automation.build_freq_points` (6‑dec inclusive endpoints; tests enforce exact rounding). Output for sweeps = one raw float per line (no extra formatting) to preserve scriptability.

### 4. Patterns & Conventions
Config: Use `config.load_config() / update_config()` only; never write ad‑hoc files. Logging: always obtain a logger via `logging.get_logger()` after `setup_logging()`. Avoid `print()` except intentional CLI stdout (e.g. sweep list). Keep GUI-safe by lazy importing Qt inside handlers (see `_cmd_gui`).
Numerics: Vector ops use NumPy; guard small sample / invalid inputs with graceful `nan`. Don’t add silent unit conversions—use Hz, seconds, volts consistently.
Dependency gating: Wrap optional hardware access in try/except; never cause test failures if hardware missing. Use feature flags before imports that might load drivers.

### 5. Testing & Quality
Add or update at least one pytest when changing logic in `automation.py`, `dsp.py`, or instrument helpers. Emulate patterns in `tests/test_automation.py` & `test_dsp.py` (pure functions; deterministic tolerances). Maintain rounding expectations (6 decimals). Coverage target ≈70%; keep new code side‑effect light and injectable for mocking.

### 6. GUI Additions
New tab: create `amp_benchkit/gui/<name>_tab.py` with `build_<name>_tab(gui)`; import only through a lazy aggregator (or future `build_all_tabs`). Don’t block the UI thread (no sleeps, hardware probes) during build—inject actions via buttons/callbacks. Use `deps.fixed_font()` where monospace helpful. Always degrade gracefully if `HAVE_QT` is False.

### 7. Non‑Goals / Cautions
Do not: (a) rewrite `unified_gui_layout.py` wholesale, (b) introduce heavy new deps (seek maintainer approval), (c) introduce global singletons beyond existing config cache, or (d) hard‑fail on absent hardware. Prefer small, reviewable diffs.

### 8. Quick Examples
Add CLI subcommand (outline only): add parser → `sp = sub.add_parser("mycmd"); sp.set_defaults(func=_cmd_mycmd)`; implement `_cmd_mycmd(args)` in the same file delegating to `amp_benchkit.my_module.run(...)`.
Add sweep logic: new function in `automation.py` should accept injected instrument callables; return simple Python types (lists, tuples, dict) for easy serialization.

If something seems ambiguous, open a PR updating this file with a targeted clarification rather than guessing.
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
- Do **not** assume hardware is present; always use feature detection and graceful degradation.
- Do **not** modify core instrument APIs without checking Public API stability guarantees.

---
For unclear or missing patterns, propose a diff for this file. Maintainers will clarify and refine.
Questions or missing patterns? Provide a diff proposal; maintainers can clarify to refine these instructions.
