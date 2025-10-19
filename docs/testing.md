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

### Tektronix auto-scaling checks

When validating sweeps at multiple amplitudes, prefer the new auto-scaling flags so the
Tek math trace does not clip between runs:

```bash
python unified_gui_layout.py thd-math-sweep \
  --math --math-order CH1-CH3 \
  --amp-vpp 0.3 \
  --scope-auto-scale CH1=13,CH3=1 \
  --scope-auto-scale-margin 0.8 \
  --apply-gold-calibration --cal-target-vpp 0.3 \
  --output results/thd_0p3_auto_gold.csv
```

- Tune the gain map (`CHn=value`) to match your probe ratios / stage gain.
- Keep results under `results/` (e.g. `results/kenwood/baseline_auto_gold/`) so future HIL runs can compare against the same artefacts.

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
