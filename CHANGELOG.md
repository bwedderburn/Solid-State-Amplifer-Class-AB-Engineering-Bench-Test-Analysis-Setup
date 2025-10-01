# Changelog

All notable changes to this project will be documented in this file.

Format: Based on *Keep a Changelog* and follows semantic versioning where practical.

## [Unreleased]
### Added
- Async capture thread for real-time THD tab updates.
- Spectrum export feature in THD tab, allowing data export in various formats.
- Persistent THD settings, retaining user preferences across sessions.

### Changed
- (none yet)

### Fixed
- (none yet)

### Notes / Follow-ups
- (none yet)

## [0.3.3] - 2025-10-01
### Added
- CI coverage reporting artifacts (coverage XML per Python version).
- Automated publish workflow (`publish.yml`) for tag-based PyPI release (token required).
- Multi-OS distribution build & smoke test job.
- All-extras install job ensuring dependency compatibility.
- Optional Codecov upload + enforced 70% minimum coverage threshold.
- Extracted advanced waveform FFT + harmonic analysis into `amp_benchkit.dsp_ext` (optional import) to reduce monolith size.
- `freq-gen` CLI subcommand producing JSON or CSV frequency lists (structured alternative to `sweep`).
- `thd-json` CLI subcommand computing THD + harmonic table from time,volts CSV input.
- Real-time GUI THD tab with synthetic fallback waveform and optional scope capture.
- THD tab controls: adjustable refresh interval & harmonic count, export harmonics CSV button.

### Changed
- `unified_gui_layout.thd_fft` now delegates to `dsp_ext.thd_fft_waveform` when available (behavior preserved; stub fallback unaffected).

### Fixed
- Graceful handling for short or invalid THD waveform inputs in CLI JSON path.

### Notes / Follow-ups
- Consider promoting `dsp_ext` APIs into documented public surface in next minor release.
- Potential future: integrate mini spectrum plot in THD tab.

## [0.3.2] - 2025-10-01
### Added
- THD dual-dispatch (`thd_fft`) with advanced FFT path (requires `dsp` extra / NumPy) and lightweight stub fallback.
- Optional `dsp` extra to avoid forcing NumPy for minimal installs.
- `thd-mode` CLI subcommand to report whether advanced or stub THD path is active.

### Changed
- Moved NumPy from core dependency list into optional extras (`dsp`, `test`).

### Fixed
- Added CI job to ensure stub THD mode works without NumPy.

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

[Unreleased]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.3...HEAD
[0.3.3]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.2...0.3.3
[0.3.2]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.1...0.3.2
[0.3.1]: https://github.com/bwedderburn/amp-benchkit/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/bwedderburn/amp-benchkit/releases/tag/0.3.0
