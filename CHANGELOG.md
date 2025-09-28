Changelog
=========

All notable changes to this project will be documented in this file. The format is
Keep a Changelog, and this project adheres to Semantic Versioning (SemVer) starting
with 0.x pre‑release phases.

## [0.3.0] - 2025-09-28
### Added
- New `amp_benchkit.automation` module exposing headless sweep helpers (`build_freq_list`, `sweep_scope_fixed`, `sweep_audio_kpis`).
- Unit tests for automation orchestration (freq list, sweep KPI path, THD/knees logic injection).
- Community documents: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`.
- TestPyPI release candidate workflow (`.github/workflows/testpypi.yml`) for tags like `v0.3.0-rc1`.
- README badges (CI, License, Python versions, PyPI) and Development section (lint/format/type instructions).

### Changed
- `unified_gui_layout.py` now delegates sweep/KPI methods to the automation module; original behavior preserved.
- Improved internal separation between GUI widgets and orchestration logic for easier scripting reuse.

### Fixed
- Resolved ambiguous truthiness check on NumPy arrays when computing KPI metrics (explicit length check in automation module).

### Internal / Tooling
- Expanded test count (now covers automation flows without hardware by dependency injection).
- Added release candidate publishing path distinct from stable PyPI tags.

## [0.2.0] - 2025-09-28
### Added
- Completed extraction of all GUI tabs into `amp_benchkit.gui` (`generator`, `scope`, `daq`, `automation`, `diagnostics`).
- Added LabJack U3 helper parity functions (`u3_read_multi`, etc.) to `u3util` for modular tabs.
- Introduced lazy (in-function) Qt imports across tab builders for headless test resilience.

### Changed
- Centralized `FY_PROTOCOLS` in `amp_benchkit.fy` and updated generator and automation tabs to reference it.
- Refactored `unified_gui_layout.py` to delegate all tab construction to builder functions.

### Removed
- Deprecated DSP wrapper functions (`vrms`, `vpp`, `thd_fft`, `find_knees`) from `unified_gui_layout.py`; users should import from `amp_benchkit.dsp` directly.

### Fixed
- Eliminated headless Qt import errors (`libEGL.so.1` issues) by moving PySide6 imports inside builder functions.

### Internal / Tooling
- Updated tests to import DSP functions from `amp_benchkit.dsp` directly (no deprecation warnings remain).
- Roadmap docs (`DEV_GUI_MODULARIZATION.md`) updated to reflect completed modularization milestone.

## [0.1.2] - 2025-09-??
### Added
- Initial extraction of generator, scope, and DAQ tabs; logging subsystem; config persistence; CI workflows; DSP module.

## [0.1.1] - 2025-09-??
### Added
- Early modularization (deps, instruments) and test scaffolding.

## [0.1.0] - 2025-09-??
### Added
- Initial monolithic `unified_gui_layout.py` with multi‑tab GUI and instrumentation helpers.

---

Unreleased changes will accumulate here until the next tagged version.
# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [0.1.1] - 2025-09-28
## [0.1.2] - 2025-09-28
### Added
- Extracted DSP functions into `amp_benchkit.dsp` module (vrms, vpp, thd_fft, find_knees).
- DSP unit tests and deprecation tests.
- Release workflow (`release.yml`) for tag-based PyPI publishing.

### Changed
- Added deprecation wrappers in `unified_gui_layout` emitting `DeprecationWarning` for migrated DSP functions.

### Added
- GitHub Actions CI (Python 3.11/3.12) with coverage, lint, type-check steps.
- Rotating file logging under XDG cache/state directory.
- Hardware-in-loop (HIL) test scaffold (env gated via `AMP_HIL=1`).
- Public API section in README.
- Makefile targets: lint, format, test, coverage, type.
- Custom exceptions (`FYError`, `FYTimeoutError`, `TekError`, `TekTimeoutError`).

### Changed
- Refined error handling for FY serial and Tek VISA operations.
- Added test extra in `pyproject.toml` and bumped version to 0.1.1.

## [0.1.0] - 2025-09-28
### Added
- Initial modularization (deps, fy, tek, u3util, u3config) extracted from monolith.
- Logging subsystem and JSON config persistence.
- Core pytest suite and config tests.
