# Release v0.3.0

> Automation module extraction, packaging polish, CI pipelines, and history cleanup groundwork.

## Highlights
- New `automation.py` module providing headless frequency sweep + KPI (THD, bandwidth knees) orchestration.
- Modular GUI extraction continued: tabs separated under `amp_benchkit.gui` (generator, scope, DAQ, diagnostics, automation).
- Dependency detection + Qt binding abstraction (`deps.py`, `_qt` helper) consolidates optional import logic.
- Added comprehensive DSP helpers (`dsp.py`) and tests.

## Packaging & Metadata
- `pyproject.toml` now includes project URLs, classifiers, license (MIT SPDX), citation file (`CITATION.cff`).
- Added optional extras: `gui`, `dev`, `test`, `publish`.
- Console scripts: `amp-benchkit`, `amp-benchkit-gui`.

## CI / Automation
- GitHub Actions: build + test workflow (Python 3.11/3.12), Exodriver build check, PyPI publish workflow, TestPyPI RC workflow.
- Added release version tagging guidance and dev version bump convention.

## Quality & Tooling
- Introduced pre-commit (post 0.3.0 release adoption) with ruff, black, mypy, large file & virtualenv guards.
- Makefile targets (planned/initial) for env, deps, selftest, GUI.
- Logging subsystem centralizes structured output to console and rotating file.

## Testing
- Expanded pytest suite: 15 passing tests, 2 skipped (hardware-dependent / optional GUI cases).
- Coverage for: DSP calculations (THD, RMS, Vpp, knee detection), IEEE block parsing, config persistence, GUI tab builders smoke tests.

## Instrument Support
- FY32xx function generator: command builders, sweep control, baud/EOL auto-fallback.
- Tektronix TDS Series scope helpers: waveform capture (raw + calibrated), trigger, math channel subtraction, screenshot plotting.
- LabJack U3 utilities: safe open, configuration helpers, watchdog / counter mapping (partial), diagnostic scripts.

## Automation Features
- Frequency list builder (log/linear) with deterministic float handling.
- Sweep capture & KPI evaluation with dependency injection for testability.
- THD FFT and bandwidth knee calculations integrated into automation pipeline.

## Documentation
- README expanded with usage, exodriver strategy, health checks.
- CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, CITATION added.
- Exodriver patching approach documented (`patches/`).

## History Cleanup Note
Earlier repository history inadvertently contained a committed `.venv/` including large Qt binaries (>100MB). A history rewrite removed these artifacts. Contributors who cloned before the cleanup must reclone or hard reset:
```bash
git fetch origin
git reset --hard origin/main
```
Pre-commit hooks now guard against recurrence.

## Upgrade Notes
- Update your local clone if you see large binary blobs or force-push divergence.
- Reinstall extras to access new automation functions: `pip install -e .[gui,test,dev]`.
- Console scripts now wrap `unified_gui_layout:main`; direct script invocation still supported.

## Roadmap (Post 0.3.0)
- Remaining GUI tab refinements & layout polishing.
- Additional automation metrics (SNR, IMD, noise floor).
- Hardware-in-loop optional CI stage (gated / manual trigger).
- REST / WebSocket bridge for remote orchestration.
- Type hint expansion, mypy stricter config, coverage reporting.

## Changelog Summary
Refer to `CHANGELOG.md` for granular commit-level entries. Key categories:
- feat: automation module, GUI tab modularization
- build/meta: packaging, extras, project URLs
- ci: publish pipeline, TestPyPI RC, exodriver checks
- docs: community & usage docs
- chore/refactor: dependency abstraction, logging, config persistence

---
Published as GitHub Release v0.3.0.
