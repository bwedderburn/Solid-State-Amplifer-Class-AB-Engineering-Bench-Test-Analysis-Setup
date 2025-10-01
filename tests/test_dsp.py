import numpy as np
import warnings

from amp_benchkit.dsp import vrms, vpp, thd_fft, find_knees, snr_db, noise_floor_db


def test_vrms_vpp():
    v = np.array([ -1.0, 1.0 ])
    assert abs(vpp(v) - 2.0) < 1e-9
    # RMS of +/-1 square-ish two-point vector -> sqrt(mean([1,1])) = 1
    assert abs(vrms(v) - 1.0) < 1e-9


def test_thd_fft_basic():
    fs = 10000.0; f0 = 500.0; N = 2048
    t = np.arange(N)/fs
    sig = np.sin(2*np.pi*f0*t) + 0.05*np.sin(2*np.pi*2*f0*t)
    thd, f_est, fund = thd_fft(t, sig, f0=f0, nharm=5)
    assert abs(f_est - f0) < f0*0.02
    assert 0.03 < thd < 0.08  # rough bounds around 0.05


def test_find_knees():
    freqs = np.array([10,20,50,100,200,500,1000,2000,5000,10000], dtype=float)
    amps = np.array([1,1,1,1,1,1,1,0.7,0.4,0.2], dtype=float)
    f_lo, f_hi, ref_amp, ref_db = find_knees(freqs, amps, ref_mode='max', drop_db=3.0)
    assert np.isfinite(f_hi) and f_hi > 1000


def test_legacy_wrappers_removed():
    import unified_gui_layout as legacy
    # Deprecated wrappers were removed after modularization cleanup.
    assert not hasattr(legacy, 'vrms') and not hasattr(legacy, 'vpp')


def test_snr_db():
    """Test SNR calculation with synthetic sine + noise."""
    fs = 10000.0
    f0 = 1000.0
    N = 4096
    t = np.arange(N) / fs
    
    # Sine + white noise (known SNR)
    np.random.seed(42)
    signal_amp = 1.0
    noise_amp = 0.1
    sig_clean = signal_amp * np.sin(2 * np.pi * f0 * t)
    noise = noise_amp * np.random.randn(N)
    sig_noisy = sig_clean + noise
    
    snr_measured = snr_db(t, sig_noisy, f0=f0, nharm=5, window='hann')
    # With windowing and FFT bin effects, SNR will be higher than time-domain calculation
    # Verify it's in a reasonable range and properly computed
    assert 20.0 < snr_measured < 50.0, f"Expected SNR in range 20-50 dB, got {snr_measured:.2f} dB"
    
    # Test with higher noise
    noise_amp = 0.3
    noise = noise_amp * np.random.randn(N)
    sig_noisy2 = sig_clean + noise
    snr_measured2 = snr_db(t, sig_noisy2, f0=f0, nharm=5, window='hann')
    # Higher noise should give lower SNR
    assert snr_measured2 < snr_measured, "Higher noise should give lower SNR"


def test_noise_floor_db():
    """Test noise floor calculation with synthetic signals."""
    fs = 10000.0
    f0 = 1000.0
    N = 4096
    t = np.arange(N) / fs
    
    # Sine + white noise
    np.random.seed(42)
    noise_amp = 0.05
    sig_clean = np.sin(2 * np.pi * f0 * t)
    noise = noise_amp * np.random.randn(N)
    sig_noisy = sig_clean + noise
    
    nf_noisy = noise_floor_db(t, sig_noisy, f0=f0, nharm=5, window='hann')
    # Noise floor should be finite
    assert np.isfinite(nf_noisy), f"Noise floor should be finite, got {nf_noisy}"
    
    # Test that higher noise gives higher noise floor
    noise_amp2 = 0.1
    noise2 = noise_amp2 * np.random.randn(N)
    sig_noisy2 = sig_clean + noise2
    nf_noisy2 = noise_floor_db(t, sig_noisy2, f0=f0, nharm=5, window='hann')
    assert nf_noisy2 > nf_noisy, "Higher noise amplitude should give higher noise floor"
