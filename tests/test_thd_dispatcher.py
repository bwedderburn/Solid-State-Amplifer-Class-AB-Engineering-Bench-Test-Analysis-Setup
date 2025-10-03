import math

from amp_benchkit.dsp import thd_fft as stub_thd_fft
import unified_gui_layout as ugl


def test_thd_dispatcher_stub_path():
    """Calling unified thd_fft with (samples, fs_hz) should invoke stub implementation."""
    samples = [0.0, 1.0, -0.5, 0.25]
    thd, f0_est, fund_amp = ugl.thd_fft(samples, 48000.0)
    # Stub returns 0.0 THD and fixed 1000Hz fundamental with max amplitude
    assert thd == 0.0
    assert f0_est == 1000.0
    assert fund_amp == max(abs(x) for x in samples)


def test_thd_dispatcher_waveform_path():
    """Calling unified thd_fft with (t, v) arrays should use scope FFT path and approximate known THD."""
    try:
        import numpy as np  # optional path
    except Exception:  # pragma: no cover
        np = None
    if np is None:
        # Environment without numpy: fallback will behave like stub; skip assertion
        return
    fs = 50_000.0
    f0 = 1000.0
    n = 4096
    t = np.arange(n) / fs
    # Add 10% 2nd harmonic -> expected THD ~0.1 within a tolerance due to windowing
    v = np.sin(2 * math.pi * f0 * t) + 0.1 * np.sin(2 * math.pi * 2 * f0 * t)
    thd, f0_est, fund_amp = ugl.thd_fft(t, v, f0=f0, nharm=5, window='hann')
    assert abs(thd - 0.1) < 0.035
    assert abs(f0_est - f0) < 5.0  # within a few Hz
    assert fund_amp > 0.0


def test_thd_short_waveform_nan():
    """Very short waveform (n<16) should produce NaNs in advanced path."""
    try:
        import numpy as np
    except Exception:
        np = None
    if np is None:
        return
    t = np.linspace(0, 1e-3, 8)
    v = np.sin(2 * math.pi * 1000 * t)
    thd, f_est, fund_amp = ugl.thd_fft(t, v)
    # Dispatcher chooses advanced path, which returns NaNs for insufficient length
    assert math.isnan(thd) and math.isnan(f_est) and math.isnan(fund_amp)
