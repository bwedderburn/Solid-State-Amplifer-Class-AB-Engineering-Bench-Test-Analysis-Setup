# GitHub Copilot Instructions for amp-benchkit

This document provides guidelines for GitHub Copilot when working with the amp-benchkit repository. For comprehensive documentation, see `AGENTS.md`, `CONTRIBUTING.md`, and `SECURITY.md`.

## Project Overview

amp-benchkit is a Python-based toolkit for automating amplifier bench measurements with a Qt GUI for manual control. It interfaces with FeelTech signal generators, Tektronix oscilloscopes, and LabJack DAQ devices, with simulator modes for development without physical hardware.

## Project Structure

- **Core modules**: `amp_benchkit/` contains drivers, automation flows, and shared widgets
- **Tests**: Mirror the `amp_benchkit/` structure in `tests/` for easy discovery
- **Scripts**: Quick-launch scripts like `unified_gui_layout.py` at repository root
- **Utilities**: Developer utilities in `scripts/`
- **Results**: Persistent captures in `results/`
- **Documentation**: Updates in `docs/` or `ROADMAP.md`

## Build, Test, and Development Commands

### Environment Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev,test,gui]
```

### Testing
```bash
# Run all tests (use AMPBENCHKIT_FAKE_HW=1 when hardware is offline)
AMPBENCHKIT_FAKE_HW=1 pytest -q

# Run specific test
pytest tests/test_dsp.py::test_thd_fft
```

### Linting and Formatting
```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
black .

# Run all pre-commit hooks
pre-commit run --all-files
```

### Type Checking
```bash
mypy amp_benchkit
```

### GUI and Selftest
```bash
# Launch GUI
make gui
# OR
python unified_gui_layout.py gui --gui

# Run headless selftest
python unified_gui_layout.py selftest
```

## Coding Style and Naming Conventions

### Language and Type Hints
- Target **Python 3.10+** with typed public APIs
- Add type hints to all public functions and methods
- Use `from __future__ import annotations` for forward references

### Formatting
- **Line length**: 100 characters (black configuration)
- Run `black` and `ruff` via `pre-commit` before committing
- Consistent style enforced through pre-commit hooks

### Naming Conventions
- **Functions and modules**: `snake_case`
- **Qt widgets and driver classes**: `CamelCase`
- **Constants and environment variables**: `SCREAMING_SNAKE_CASE`
- **Private functions/methods**: Prefix with single underscore `_function_name`

### Documentation
- Document hardware assumptions inline when behavior diverges from lab defaults
- Use docstrings for public functions following existing patterns
- Keep comments concise and meaningful

## Testing Guidelines

### Test Organization
- Name test modules `test_<module>.py`
- Place shared fixtures under `tests/fixtures/`
- Mirror the `amp_benchkit/` directory structure

### Hardware Testing
- Skip hardware-dependent tests automatically when devices are absent
- Use `AMPBENCHKIT_FAKE_HW=1` to exercise simulator paths
- Add deterministic synthetic data for DSP tests

### Test Coverage
- Maintain coverage across:
  - Signal generation
  - Instrument I/O
  - GUI command flows
- Keep golden CSV/JSON artifacts next to tests when validating capture pipelines
- Add tests for new public functions or bug fixes

## Commit and Pull Request Conventions

### Commit Messages
Use **imperative, present-tense** commit subjects:
- ✅ `feat: add automation orchestration module`
- ✅ `fix: handle empty IEEE block response gracefully`
- ✅ `docs: expand README with TestPyPI instructions`
- ✅ `refactor: extract scope math helper`
- ❌ `Added new feature`
- ❌ `Fixed bug`

### Pre-Push Checklist
```bash
pre-commit run --all-files
pytest -q
```

### Pull Request Requirements
- Link related issues
- Summarize user-facing changes
- Attach screenshots or captured artifacts for GUI or plotting updates
- Record release-impacting notes in `CHANGELOG.md` within the same PR
- Ensure CI checks pass before requesting review

### Commit Practices
- Keep commit bodies concise
- Avoid very large omnibus commits
- Separate refactoring from feature additions when possible

## Security and Configuration

### Security Rules
- **NEVER** commit device serial numbers or lab credentials
- **NEVER** commit secrets into source code
- **NEVER** include passwords or API keys
- Use environment variables for sensitive configuration

### Environment Variables
Override discovery and configuration via:
- `FY_PORT` - FeelTech signal generator port
- `VISA_RESOURCE` - VISA resource identifier
- `AMPBENCHKIT_SESSION_DIR` - Session directory for captures
- `AMPBENCHKIT_FAKE_HW` - Enable simulator mode (set to `1`)

### Hardware Setup
- Document new hardware setup steps in `EXODRIVER.md` or `SECURITY.md`
- Surface missing dependencies (VISA backends, Exodriver) with actionable error messages
- Validate all external input using appropriate validators

### Security Vulnerability Reporting
- Do NOT open public issues for security vulnerabilities
- Use GitHub's Private Vulnerability Reporting feature
- See `SECURITY.md` for detailed reporting instructions

## Dependencies and Package Management

### Core Dependencies
- **PyVISA**: Instrument communication
- **pyserial**: Serial port access
- **LabJackPython**: LabJack U3 DAQ interface
- **Qt (PySide6/PyQt6)**: GUI framework
- **NumPy/SciPy**: Signal processing
- **pytest**: Testing framework

### Installing Dependencies
```bash
pip install -e .[dev,test,gui,docs,publish]
```

### Adding New Dependencies
- Add to `pyproject.toml` under appropriate extra groups
- Update `requirements.txt` if needed
- Document any system-level dependencies in README or setup docs
- Prefer existing libraries; only add new ones if absolutely necessary

## Pre-Commit Hooks

### Installed Hooks
- Style/hygiene: trailing whitespace, end-of-file newline, mixed line endings, merge conflict markers
- Lint & format: `ruff` (with autofix), `ruff-format`, and `black`
- Types: `mypy` (best-effort, non-blocking)
- Safeguards: Block staging of:
  - Virtual environment / `site-packages` content
  - Binary blobs >5MB

### Setup
```bash
pip install pre-commit
pre-commit install
```

### Why Safeguards?
Earlier repository history accidentally included a full `.venv/` directory with large Qt binaries, bloating the repository. Pre-commit hooks prevent recurrence.

## Public API Stability

The following APIs are considered **stable (Beta)**:

### Drivers
- `amp_benchkit.fy.FYGenerator` and methods
- `amp_benchkit.tek.TekScope` and methods
- `amp_benchkit.u3config.u3_read_ain()`

### Configuration
- `amp_benchkit.logging.setup_logging(verbose=False, file_logging=True)`
- `amp_benchkit.config.load_config()` / `save_config(cfg)` / `update_config(**kv)`

### DSP/Analysis
- `amp_benchkit.dsp.vrms(v)`
- `amp_benchkit.dsp.vpp(v)`
- `amp_benchkit.dsp.thd_fft(t, v, f0=None, nharm=10, window='hann')`
- `amp_benchkit.dsp.find_knees(freqs, amps, ref_mode='max', ref_hz=1000.0, drop_db=3.0)`

### Exceptions
- `amp_benchkit.fy.FYError`, `FYTimeoutError`
- `amp_benchkit.tek.TekError`, `TekTimeoutError`

**Items not listed should be treated as internal and subject to change.**

## Common Patterns and Best Practices

### Error Handling
```python
from amp_benchkit.fy import FYError, FYTimeoutError
from amp_benchkit.tek import TekError, TekTimeoutError

try:
    # Instrument operation
    pass
except FYTimeoutError:
    # Handle timeout specifically
    pass
except FYError as e:
    # Handle general FY errors
    logger.error(f"FY error: {e}")
```

### Logging
```python
from amp_benchkit.logging import setup_logging
import logging

setup_logging(verbose=True, file_logging=True)
logger = logging.getLogger(__name__)
logger.info("Operation started")
```

### Configuration
```python
from amp_benchkit.config import load_config, save_config, update_config

cfg = load_config()
update_config(key="value")
save_config(cfg)
```

### Hardware Simulation
```python
import os
os.environ['AMPBENCHKIT_FAKE_HW'] = '1'
# Now hardware operations will use simulators
```

## GUI Development

### Qt Imports
Use lazy Qt imports via the helper:
```python
from amp_benchkit.gui.qt_helper import QtWidgets, QtCore
```

### Widget Naming
- Use `CamelCase` for Qt widget classes
- Follow existing tab structure in `amp_benchkit/gui/`

### GUI Testing
- Provide simulator fallbacks for all hardware operations
- Test GUI components with `AMPBENCHKIT_FAKE_HW=1`

## Release Process

1. Update `CHANGELOG.md` and bump version in `pyproject.toml`
2. Run tests and build locally: `python -m build`
3. Tag: `git tag vX.Y.Z` and push: `git push origin vX.Y.Z`
4. GitHub Actions builds and (if configured) uploads to PyPI
5. Draft Release notes on GitHub
6. Post-release: bump to `X.Y.(Z+1).dev0` for continued development

## Additional Resources

- **Contributing Guide**: See `CONTRIBUTING.md`
- **Code of Conduct**: See `CODE_OF_CONDUCT.md`
- **Security Policy**: See `SECURITY.md`
- **Agent Guidelines**: See `AGENTS.md`
- **Documentation**: <https://bwedderburn.github.io/amp-benchkit/>
- **Repository**: <https://github.com/bwedderburn/amp-benchkit>

## Quick Reference

### File a Bug
Include: OS, Python version, steps to reproduce, expected vs actual behavior, hardware context

### Supported Versions
- 0.3.x: Active support ✅
- 0.2.x: Critical fixes only ⚠️
- <0.2.0: Not supported ❌

### Code Style Quick Check
```bash
black . && ruff check . --fix && mypy amp_benchkit
```

### Full CI Check
```bash
pre-commit run --all-files && pytest -q
```
