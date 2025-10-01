# Unified GUI Layout (Lite + U3)
![selftest](https://github.com/bwedderburn/amp-benchkit/actions/workflows/selftest.yml/badge.svg) ![coverage](https://img.shields.io/badge/coverage-pending-lightgrey)

Cross-platform control panel for:
- FeelTech FY3200S function generator (dual-channel)
- Tektronix TDS2024B oscilloscope (VISA)
- LabJack U3/U3-HV DAQ (AIN/DIO, timers, watchdog)

## Features
- FY: per-channel setup, frequency sweeps; auto-baud fallback.
- Scope: capture raw bytes, calibrated CSV, quick PNG plots.
- U3: Read/Stream and **Config Defaults** tabs modeled after LJControlPanel.
- Automation: frequency sweep with single shared FY port/protocol override.
- Built-in `selftest` for protocol formatting and sanity checks.

## THD Calculation Dispatcher
The unified `thd_fft` exposed at the top level (imported via `unified_gui_layout`) performs dual-dispatch:

1. Advanced waveform mode: `thd_fft(t_array, v_array, f0=..., nharm=..., window='hann')`
   - `t_array`: time samples (seconds)
   - `v_array`: voltage samples (volts)
   - Returns `(thd_ratio, f0_est_hz, fundamental_bin_amplitude)`
   - Uses an FFT with windowing and harmonic bin summation. Requires at least 16 samples; shorter inputs yield NaNs.
2. Stub/sample mode: `thd_fft(samples, fs_hz)`
   - `samples`: arbitrary iterable of amplitudes
   - `fs_hz`: sample rate (ignored in stub)
   - Returns `(0.0, 1000.0, max_abs_sample)` — minimal placeholder for environments without NumPy.

Detection heuristic: if both first two arguments have `__len__` and NumPy is available, the advanced path is attempted; otherwise the stub path executes. This keeps CLI / lightweight environments working while enabling richer GUI / analysis when NumPy is installed.

The advanced waveform FFT + harmonic extraction lives in `amp_benchkit.dsp_ext` (imported only if present). This keeps the monolithic bridge lean and preserves stub behavior for minimal installs.

### Example
```python
import math
import unified_gui_layout as ugl

# Stub path (no NumPy arrays provided or NumPy not installed)
thd, f_est, a0 = ugl.thd_fft([0.0, 1.0, -0.5], 48000.0)
print(thd, f_est, a0)  # 0.0 1000.0 1.0

# Advanced path (requires NumPy)
try:
    import numpy as np
    fs = 50_000.0
    f0 = 1000.0
    n = 4096
    t = np.arange(n)/fs
    v = np.sin(2*math.pi*f0*t) + 0.1*np.sin(2*math.pi*2*f0*t)
    thd, f_est, a0 = ugl.thd_fft(t, v, f0=f0)
    print(thd, f_est, a0)
except ImportError:
    pass
```

## Installation Extras

Base installation keeps dependencies minimal. Enable optional capabilities:

- GUI tabs (Qt): `pip install "amp-benchkit[gui]"`
- Advanced FFT THD / numeric helpers: `pip install "amp-benchkit[dsp]"`
- Serial / VISA / LabJack hardware stacks: `pip install "amp-benchkit[serial,visa,labjack]"`
- Everything developers typically need: `pip install "amp-benchkit[gui,dsp,serial,visa,labjack,test]"`

If NumPy is absent, `thd_fft` falls back to a stub (always 0 THD) while remaining features continue to work.

### Release Helper
Use the helper script to bump versions:

```bash
chmod +x scripts/release.sh
./scripts/release.sh 0.3.3 --tag
git push && git push --tags
```

### CLI Helper: THD Mode
To see whether the advanced FFT THD implementation is active (NumPy installed) or the stub fallback is in use:

```bash
python unified_gui_layout.py thd-mode
```
Outputs either `advanced` or `stub`.

### New Structured CLI Utilities

Frequency list generation with machine-readable output:

```bash
python unified_gui_layout.py freq-gen --start 20 --stop 20000 --points 31 --mode log --format json
```
Outputs compact JSON: `{ "start": 20.0, "stop": 20000.0, "points": 31, "mode": "log", "frequencies": [...] }`

Or CSV (one float per line) for shell pipelines:

```bash
python unified_gui_layout.py freq-gen --start 20 --stop 20000 --points 31 --mode log --format csv
```

Waveform THD from a time,volts CSV file (header optional):

```bash
python unified_gui_layout.py thd-json capture.csv --f0 1000 --nharm 8 --window hann
```
Returns JSON containing `thd`, `f0_est`, `fund_amp`, and a harmonic table (when the `dsp` extra is installed). Short or invalid inputs produce NaN fields while still succeeding with exit code 0 for script robustness.

### Real-Time THD GUI Tab

The GUI now includes an optional "THD" tab (shown when Qt & `dsp` extra are installed) providing:

- Live THD % readout (default 1 Hz refresh) from either:
    - Tektronix scope capture (best-effort via VISA), or
    - Synthetic dual-tone (1 kHz + small 2nd harmonic) fallback when hardware not present.
- Adjustable harmonic count and refresh interval (ms).
- Export button writing a `results/harmonics.csv` table: `k,freq_hz,mag`.

If advanced DSP is unavailable, the tab displays a stub notice instead of failing.

### Real-Time THD Tab Enhancements (Unreleased)
The THD tab now:
- Uses a background capture thread (reduces UI jitter).
- Adds a Show Spectrum button (saves `results/spectrum.png`).
- Persists resource / f0 / harmonic count / refresh interval between runs.

If `matplotlib` is not installed the Spectrum button reports the missing dependency gracefully.

### Spectrum CLI Command (Unreleased)
A new `spectrum` subcommand exports a magnitude spectrum plot (PNG) from either:
- A CSV file with `time,volts`
- A synthetic sine (when `--file` omitted) with parameters `--f0`, `--fs`, `--points`

It respects a configurable output directory via either `--outdir` or the persisted `results_dir` in the config (defaults to `results/`). Example:

```
python unified_gui_layout.py spectrum --f0 1000 --points 4096 --fs 48000 --outdir results --output spectrum.png
```

If `matplotlib` is missing the command exits with a clear diagnostic.

### Persistent Results Directory
Using the THD tab or config utilities you can set `results_dir` which both the GUI spectrum export and CLI `spectrum` command will use when `--outdir` is not specified.
