# Testing Matrix

Use this checklist to ensure changes are validated across supported workflows.

## Unit & Integration Tests

- `python -m pytest -q` (with `AMPBENCHKIT_FAKE_HW=1` for simulator mode).
- Focus areas:
  - Signal generation helpers (`amp_benchkit.fy`, `signals.py`)
  - Scope capture and math subtraction (`amp_benchkit.tek`)
  - GUI builder smoke tests (`tests/test_gui_builders.py`)
  - Automation sweeps (`tests/test_automation.py`)

## GUI Smoke Tests

1. `python unified_gui_layout.py gui`
2. Verify generator, scope, and DAQ tabs load without hardware.
3. Run the “Run Test” or sweep actions using fake hardware.

## Hardware-in-the-Loop (HIL)

For release qualification (v0.3.6 baseline):

```bash
export AMP_HIL=1
pytest -q -rs
```

Exercise scope/generator fixtures individually for failures, e.g.:

```bash
pytest tests/test_gui_builders.py -k scope
```

Document anomalies in `CHANGELOG.md` or new issues.

## Continuous Integration

GitHub Actions run:
- `CI` workflow (matrix Python versions, coverage)
- `pre-commit` (lint/type checks)
- `docs` (MkDocs build, see workflow details)

Monitor failures with:

```bash
gh run list --status failure --branch main
```

Follow up on red runs before merging feature branches.
