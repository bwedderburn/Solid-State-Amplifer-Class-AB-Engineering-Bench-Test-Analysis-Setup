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
