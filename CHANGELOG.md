# Changelog

All notable changes to this project will be documented in this file.

Format: Based on *Keep a Changelog* and follows semantic versioning where practical.

## [Unreleased]
### Added
- THD dual-dispatch (`thd_fft`) with advanced FFT path (requires `dsp` extra / NumPy) and lightweight stub fallback.
- Optional `dsp` extra to avoid forcing NumPy for minimal installs.
- `thd-mode` CLI subcommand to report whether advanced or stub THD path is active.

### Changed
- Moved NumPy from core dependency list into optional extras (`dsp`, `test`).

### Fixed
- (placeholder)

### Notes / Follow-ups
- Consider extracting waveform DSP helpers from `unified_gui_layout.py` into `amp_benchkit.dsp` proper (keeping backward compatibility).

## [0.3.1] - 2025-10-01
### Added
- Concise AI contributor guide (`.github/copilot-instructions.md`) summarizing architecture, dependency gating, testing patterns.
- Graceful no-argument CLI behavior: running `python unified_gui_layout.py` now prints help instead of an argparse error.
- Gated (optional) LabJack U3 import in `amp_benchkit/gui/daq_tab.py` to avoid import failures when `LabJackPython` is absent.
- Repository-level `.gitignore` to filter virtualenv, build, cache, and coverage artifacts.
- Vendor `exodriver/install` script (plus its own .gitignore) for reproducible local driver setup.

### Changed
- Resolved legacy merge remnants in `unified_gui_layout.py`; rely on modular `amp_benchkit` package functions for sweeps and DSP.

### Fixed
- Prevents hard import errors in GUI tests/environments without LabJack hardware or driver.

### Notes / Follow-ups
- Add tests for new no-arg help path and optional U3 import guard.
- Consider extracting remaining legacy logic in `unified_gui_layout.py` into smaller modules.
- Integrate lint/type checks (ruff/mypy) in CI once environment standardization is done.

## [0.3.0] - 2025-09-??
### Added
- (Backfill placeholder) Initial modular extraction groundwork; previous history reconstructed from repository.

[Unreleased]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.1...HEAD
[0.3.1]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/bwedderburn/amp-benchkit/releases/tag/0.3.0
