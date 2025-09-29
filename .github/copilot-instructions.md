# Copilot / AI Agent Project Instructions

Concise, project‑specific guidance to make productive, safe changes. Focus on these patterns; avoid generic boilerplate.

## 1. Architecture Snapshot
- Legacy monolithic entry: `unified_gui_layout.py` (still ~1300 lines) orchestrates CLI + multi‑tab GUI. New code should prefer extracted modules.
- Modularized helpers (preferred touch points):
  - `amp_benchkit.deps`: optional dependency + Qt binding detection (never re‑import heavy libs redundantly). Gate GUI logic via `HAVE_QT`.
  - `amp_benchkit.fy`, `amp_benchkit.tek`, `amp_benchkit.u3util`, `amp_benchkit.u3config`: instrument abstraction layers (FY function gen SCPI‑like serial, Tektronix VISA, LabJack U3).
  - `amp_benchkit.dsp`: numerical signal KPIs (RMS, PkPk, THD FFT, bandwidth knees). Always return floats, `nan` on invalid input.
  - `amp_benchkit.automation`: sweep orchestration (headless); inject instrument functions (DI friendly, used by GUI + tests).
  - `amp_benchkit.gui/*.py`: progressively extracted tab builders (generator, scope, DAQ, automation, diagnostics). Future tabs should mimic this pattern: a pure function returning a QWidget given shared context.
- Public (provisional) API enumerated in README; do not break signatures without bumping minor version.

## 2. CLI / Entry Points
- Console scripts (`amp-benchkit`, `amp-benchkit-gui`) map to `amp_benchkit.cli:main` / `main_gui`, which delegate to legacy `unified_gui_layout.main()`.
- Add new subcommands by editing `unified_gui_layout.py` argument parsing (search for `argparse`) BUT prefer extracting logic into a new small module first, then calling from legacy.
- Headless sweeps (frequency list output) rely on `automation.build_freq_points`; preserve 6‑decimal rounding and inclusive endpoints.

## 3. Dependency & Environment Handling
- Always feature‑detect using flags from `deps.py` (e.g. `HAVE_QT`, `HAVE_PYVISA`) before importing / executing hardware code. Provide graceful fallback (return, or raise ImportError with INSTALL_HINTS message for CLI paths).
- GUI must run headless tests: any Qt usage is guarded; matplotlib forced to Agg early (`matplotlib.use('Agg')`). Keep this at top if editing.
- LabJack driver (Exodriver) is optional; tests skip hardware assumptions. Never hard‑fail CI if USB absent—wrap in try/except.

## 4. Conventions & Patterns
- Rounding: frequency point generation rounds to 6 decimals; tests assert tight tolerances. Maintain this when adding modes (e.g., future JSON output).
- Logging: use `amp_benchkit.logging.get_logger()`; DEBUG enabled via top‑level `--verbose`. Avoid `print()` except for deliberate CLI stdout data (e.g., sweep numerical list).
- Config: use `amp_benchkit.config.update_config(...)` / `load_config()`; never write ad‑hoc files in cwd except intended outputs under `results/`.
- Return shapes: DSP functions return `float` or tuple of primitives; THD returns `(thd_ratio, f0_est, fund_amp)`. Keep numpy → Python float conversions explicit (`float(...)`).
- Fail soft: instrument operations catch and log individual frequency failures but continue the sweep (`automation.sweep_*`). Preserve that resilience.

## 5. Testing Expectations
- Pytest suite (`tests/`) exercises CLI sweep, entry point delegation, DSP math, automation helpers, and tab builders (import safety). New features require at least one targeted test unless purely internal refactor.
- Coverage gate: 70% (CI). Keep added code testable headless: inject dependencies instead of hard imports (follow patterns in `automation.py`).
- For command output tests, mimic existing style: capture stdout lines, compare numeric invariants not exact formatting beyond what's stable.

## 6. Adding Instrument Features
- Extend existing module (e.g., `fy.py`) with pure functions; raise custom exceptions (`FYError`, `TekError`) already defined—re‑use them. Update README public API list if becoming user‑facing.
- For new SCPI / serial commands: centralize string building (pattern in `build_fy_cmds`) to keep formatting consistent for tests/logging.

## 7. GUI Tab Additions
- New tab builder: `def build_<name>_tab(ctx) -> QWidget:` placed in `amp_benchkit/gui/`. Minimal side effects; rely on `deps.fixed_font()` and flags. Wire into main window in `unified_gui_layout.UnifiedGUI.__init__` using existing `tabs.addTab(builder(...), "Label")` pattern.
- Avoid blocking calls in GUI thread (use small timers or background threads if future long operations needed).

## 8. Release & Versioning
- Version in `pyproject.toml`. For release automation, README outlines manual steps (update changelog, tag). Keep semantic: incompatible API changes → minor bump, internal refactors → patch.

## 9. Safe Change Checklist (Apply Before PR)
1. Run: `make test` (or `pytest -q`).
2. Run: `ruff check .` (autofix trivial issues first if desired).
3. Optional: `mypy amp_benchkit` (ensure no new type regressions).
4. If touching sweep logic, re‑run `tests/test_cli_sweep.py` locally.
5. Update README only if user‑visible behavior changes (CLI params, public API).

## 10. Non‑Goals For Agents
- Do NOT attempt to fully rewrite `unified_gui_layout.py` in one PR; incremental extraction only.
- Do NOT introduce new heavyweight dependencies without discussion.
- Avoid adding global state or singleton patterns—prefer injected callables like existing automation functions.

---
Questions or missing patterns? Provide a diff proposal; maintainers can clarify to refine these instructions.
