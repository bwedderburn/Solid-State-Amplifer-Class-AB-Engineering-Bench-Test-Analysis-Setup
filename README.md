# Unified GUI Layout (Lite + U3)
![selftest](https://github.com/bwedderburn/amp-benchkit/actions/workflows/selftest.yml/badge.svg)

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

### CLI Helper: THD Mode
To see whether the advanced FFT THD implementation is active (NumPy installed) or the stub fallback is in use:

```bash
python unified_gui_layout.py thd-mode
```
Outputs either `advanced` or `stub`.
