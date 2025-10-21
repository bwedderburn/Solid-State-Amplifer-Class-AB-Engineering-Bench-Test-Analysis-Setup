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
  --output results/thd_0p3_auto_gold.csv \
  --timestamp

Or use the scripted wrapper (auto-detect Tek/FY + scaling):

```bash
python3 scripts/run_thd_sweep.py \
  --amp-vpp 0.5 \
  --start 20 --stop 20000 --points 61 \
  --scope-auto-scale CH1=12 \
  --apply-gold-calibration --cal-target-vpp 0.5 \
  --timestamp
```
```

- Tune the gain map (`CHn=value`) to match your probe ratios / stage gain.
- Keep results under `results/` (e.g. `results/kenwood/baseline_auto_gold/`) so future HIL runs can compare against the same artefacts.

Document anomalies in `CHANGELOG.md` or new issues.

### -3 dB knee sweep

Use the new headless bandwidth helper when validating amplifier bandwidth or matching against golden references:

```bash
python unified_gui_layout.py knee-sweep \
  --amp-vpp 1.0 \
  --output results/knee_sweep.csv \
  --apply-gold-calibration \
  --knee-drop-db 3.0 \
  --smoothing median --smooth-window 5 \
  --timestamp
```

- Adjust `--knee-drop-db` for other thresholds (e.g. -1 dB noise floor checks).
- `--smoothing` / `--allow-non-monotonic` help tame non-linear response curves before interpolation.
- CLI output includes Vrms/PkPk columns plus the relative dB delta that should be cross-checked against published specs.

### FFT snapshot (Tek math trace)

When you need a quick look at harmonic distribution or the measurement noise floor, capture the on-scope FFT trace:

```bash
amp-benchkit fft-capture \
  --source CH1 \
  --window hanning \
  --scale db \
  --output results/fft_trace.csv \
  --top 12
```

- Pass `--fy-freq` / `--fy-amp` to re-arm the FY source ahead of the grab (falls back to auto-detecting the FY port).
- Use `--smoothing none` or custom scripts on the CSV to cross-validate against the analyzer’s THD readings.
- The CLI prints the strongest bins in human-readable form while the CSV retains the full spectrum for post-processing.
- Append `--timestamp` when you want to keep every capture instead of overwriting the previous CSV.

To automate multiple FFT grabs across the audio band, use the sweep helper (handles FY tuning and FFT center/span per point, restoring defaults afterward):

```bash
amp-benchkit fft-sweep \
  --start 100 \
  --stop 5000 \
  --points 10 \
  --amp-vpp 0.5 \
  --fft-span 250 \
  --fft-zoom 10 \
  --output-dir results/fft_sweep \
  --timestamp
```

To automate multiple FFT grabs across the audio band, use the sweep helper:

```bash
amp-benchkit fft-sweep \
  --start 100 \
  --stop 5000 \
  --points 10 \
  --amp-vpp 0.5 \
  --fft-span 500 \
  --output-dir results/fft_sweep \
  --timestamp
```

- The command adjusts the FY generator for each point, repoints the FFT center to the current frequency, then saves timestamped CSV traces.
- Tweak `--fft-span` or `--fft-zoom` so the scope’s FFT window matches your manual configuration.

### Offline THD comparison

After capturing both a THD sweep and an FFT trace, reconcile them with the helper script:

```bash
python scripts/fft_thd_compare.py \
  --thd results/thd_sweep.csv \
  --fft results/fft_trace.csv \
  --auto-fundamental \
  --window 200 \
  --harmonics 8
```

- Swap `--auto-fundamental` for `--fundamental 1000` if the FFT is already zoomed to 1 kHz.
- Tighten `--window` when the FFT resolution is high to avoid picking up adjacent bins.
- The script surfaces the harmonic peaks and delta so scope FFT, THD sweep, and analyzer readings can be compared offline.

For bulk FFT sweep runs, generate a consolidated report:

```bash
python scripts/fft_vs_thd_summary.py \
  --fft-dir results/fft_sweep \
  --thd results/thd_sweep.csv \
  --window 50 \
  --harmonics 8
```

This writes `fft_thd_summary.csv` and prints per-frequency deltas so you can confirm the FFT captures align with the THD sweep.

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
