import numpy as np

from amp_benchkit.dsp import find_knees, thd_fft, vpp, vrms


def test_vrms_vpp():
    v = np.array([-1.0, 1.0])
    assert abs(vpp(v) - 2.0) < 1e-9
    # RMS of +/-1 square-ish two-point vector -> sqrt(mean([1,1])) = 1
    assert abs(vrms(v) - 1.0) < 1e-9


def test_thd_fft_basic():
    fs = 10000.0
    f0 = 500.0
    N = 2048
    t = np.arange(N) / fs
    sig = np.sin(2 * np.pi * f0 * t) + 0.05 * np.sin(2 * np.pi * 2 * f0 * t)
    thd, f_est, fund = thd_fft(t, sig, f0=f0, nharm=5)
    assert abs(f_est - f0) < f0 * 0.02
    assert 0.03 < thd < 0.08  # rough bounds around 0.05


def test_find_knees():
    freqs = np.array([10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000], dtype=float)
    amps = np.array([1, 1, 1, 1, 1, 1, 1, 0.7, 0.4, 0.2], dtype=float)
    f_lo, f_hi, ref_amp, ref_db = find_knees(freqs, amps, ref_mode="max", drop_db=3.0)
    assert np.isfinite(f_hi) and f_hi > 1000


def test_legacy_wrappers_removed():
    import unified_gui_layout as legacy

    # Deprecated wrappers were removed after modularization cleanup.
    assert not hasattr(legacy, "vrms") and not hasattr(legacy, "vpp")
