"""DSP / signal analysis helpers for amp_benchkit.

Functions were extracted from the legacy monolithic GUI module.
Public (provisional) API:
  vrms(v) -> float
  vpp(v) -> float
  thd_fft(t, v, f0=None, nharm=10, window='hann') -> (thd, f0_est, fund_amp)
  find_knees(freqs, amps, ref_mode='max', ref_hz=1000.0, drop_db=3.0) -> (f_lo, f_hi, ref_amp, ref_db)
  snr_db(t, v, f0=None, nharm=5, window='hann') -> float
  noise_floor_db(t, v, f0=None, nharm=5, window='hann') -> float
"""
from __future__ import annotations
import numpy as np

__all__ = [
    'vrms','vpp','thd_fft','find_knees','snr_db','noise_floor_db'
]

def _np_array(x):
    return x if isinstance(x, np.ndarray) else np.asarray(x)

def vrms(v):
    v = _np_array(v)
    return float(np.sqrt(np.mean(np.square(v.astype(float))))) if v.size else float('nan')

def vpp(v):
    v = _np_array(v)
    return float((np.max(v) - np.min(v))) if v.size else float('nan')

def thd_fft(t, v, f0=None, nharm=10, window='hann'):
    t = _np_array(t).astype(float); v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return float('nan'), float('nan'), float('nan')
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        span = t[-1] - t[0]
        dt = span/(n-1) if span>0 else 1e-6
    fs = 1.0/dt
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    else:
        w = np.ones(n)
    v_win = v * w
    Y = np.fft.rfft(v_win)
    f = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(Y)
    if f0 is None or f0 <= 0:
        idx = int(np.argmax(mag[1:])) + 1
    else:
        idx = int(np.argmin(np.abs(f - float(f0))))
        if idx <= 0:
            idx = int(np.argmax(mag[1:])) + 1
    fund_amp = float(mag[idx])
    if fund_amp <= 0:
        return float('nan'), float(f[idx]), float(0.0)
    s2 = 0.0
    for k in range(2, max(2,int(nharm))+1):
        target = k * f[idx]
        if target > f[-1]:
            break
        hk = int(np.argmin(np.abs(f - target)))
        if hk <= 0 or hk >= mag.size:
            continue
        s2 += float(mag[hk])**2
    thd = float(np.sqrt(s2) / fund_amp)
    return thd, float(f[idx]), fund_amp

def find_knees(freqs, amps, ref_mode='max', ref_hz=1000.0, drop_db=3.0):
    f = _np_array(freqs).astype(float); a = _np_array(amps).astype(float)
    if f.size != a.size or f.size < 2:
        return float('nan'), float('nan'), float('nan'), float('nan')
    if ref_mode == 'freq':
        idx = int(np.argmin(np.abs(f - float(ref_hz))))
    else:
        idx = int(np.argmax(a))
    ref_amp = float(a[idx]) if a[idx] > 0 else float('nan')
    if not np.isfinite(ref_amp) or ref_amp <= 0:
        return float('nan'), float('nan'), float('nan'), float('nan')
    ref_db = 20.0*np.log10(ref_amp)
    target_db = ref_db - float(drop_db)
    adB = 20.0*np.log10(np.maximum(a, 1e-18))
    f_lo = float('nan'); f_hi = float('nan')
    prev_f = f[0]; prev_db = adB[0]
    for i in range(1, idx+1):
        cur_f = f[i]; cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (prev_db <= target_db and cur_db >= target_db):
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_lo = float(prev_f + frac*(cur_f - prev_f))
            else:
                f_lo = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    prev_f = f[idx]; prev_db = adB[idx]
    for i in range(idx+1, f.size):
        cur_f = f[i]; cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (prev_db <= target_db and cur_db >= target_db):
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_hi = float(prev_f + frac*(cur_f - prev_f))
            else:
                f_hi = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    return f_lo, f_hi, ref_amp, ref_db


def snr_db(t, v, f0=None, nharm=5, window='hann'):
    """Calculate Signal-to-Noise Ratio in dB using FFT-based bin exclusion.
    
    Parameters
    ----------
    t : array-like
        Time vector in seconds.
    v : array-like
        Voltage/signal values.
    f0 : float, optional
        Fundamental frequency in Hz. If None, the peak in FFT is used.
    nharm : int, optional
        Number of harmonics to exclude from noise calculation (default: 5).
    window : str, optional
        Window function: 'hann', 'hamming', or 'none' (default: 'hann').
        
    Returns
    -------
    float
        SNR in dB. Returns nan if signal is too short or invalid.
        
    Notes
    -----
    SNR is computed as 20*log10(signal_rms / noise_rms), where:
    - signal_rms is the RMS of the fundamental frequency bin
    - noise_rms is the RMS of all bins excluding DC, fundamental, and harmonics
    """
    t = _np_array(t).astype(float)
    v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return float('nan')
    
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        span = t[-1] - t[0]
        dt = span/(n-1) if span>0 else 1e-6
    
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    else:
        w = np.ones(n)
    
    v_win = v * w
    Y = np.fft.rfft(v_win)
    f = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(Y)
    
    # Find fundamental
    if f0 is None or f0 <= 0:
        idx = int(np.argmax(mag[1:])) + 1
    else:
        idx = int(np.argmin(np.abs(f - float(f0))))
        if idx <= 0:
            idx = int(np.argmax(mag[1:])) + 1
    
    fund_amp = float(mag[idx])
    if fund_amp <= 0:
        return float('nan')
    
    # Create mask for noise bins (exclude DC, fundamental, and harmonics)
    noise_mask = np.ones(mag.size, dtype=bool)
    noise_mask[0] = False  # Exclude DC
    noise_mask[idx] = False  # Exclude fundamental
    
    # Exclude harmonics
    for k in range(2, max(2, int(nharm))+1):
        target = k * f[idx]
        if target > f[-1]:
            break
        hk = int(np.argmin(np.abs(f - target)))
        if 0 < hk < mag.size:
            noise_mask[hk] = False
    
    # Calculate noise RMS from remaining bins
    noise_bins = mag[noise_mask]
    if noise_bins.size == 0:
        return float('nan')
    
    noise_rms = float(np.sqrt(np.mean(noise_bins**2)))
    if noise_rms <= 0:
        return float('inf')
    
    snr = 20.0 * np.log10(fund_amp / noise_rms)
    return float(snr)


def noise_floor_db(t, v, f0=None, nharm=5, window='hann'):
    """Calculate noise floor in dB relative to 1V RMS.
    
    Parameters
    ----------
    t : array-like
        Time vector in seconds.
    v : array-like
        Voltage/signal values.
    f0 : float, optional
        Fundamental frequency in Hz. If None, the peak in FFT is used.
    nharm : int, optional
        Number of harmonics to exclude from noise calculation (default: 5).
    window : str, optional
        Window function: 'hann', 'hamming', or 'none' (default: 'hann').
        
    Returns
    -------
    float
        Noise floor in dBV (dB relative to 1V RMS). Returns nan if invalid.
        
    Notes
    -----
    Noise floor is computed as 20*log10(noise_rms), where noise_rms is the
    RMS of all FFT bins excluding DC, fundamental, and harmonics.
    """
    t = _np_array(t).astype(float)
    v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return float('nan')
    
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        span = t[-1] - t[0]
        dt = span/(n-1) if span>0 else 1e-6
    
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    else:
        w = np.ones(n)
    
    v_win = v * w
    Y = np.fft.rfft(v_win)
    f = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(Y)
    
    # Find fundamental
    if f0 is None or f0 <= 0:
        idx = int(np.argmax(mag[1:])) + 1
    else:
        idx = int(np.argmin(np.abs(f - float(f0))))
        if idx <= 0:
            idx = int(np.argmax(mag[1:])) + 1
    
    # Create mask for noise bins (exclude DC, fundamental, and harmonics)
    noise_mask = np.ones(mag.size, dtype=bool)
    noise_mask[0] = False  # Exclude DC
    noise_mask[idx] = False  # Exclude fundamental
    
    # Exclude harmonics
    for k in range(2, max(2, int(nharm))+1):
        target = k * f[idx]
        if target > f[-1]:
            break
        hk = int(np.argmin(np.abs(f - target)))
        if 0 < hk < mag.size:
            noise_mask[hk] = False
    
    # Calculate noise RMS from remaining bins
    noise_bins = mag[noise_mask]
    if noise_bins.size == 0:
        return float('nan')
    
    noise_rms = float(np.sqrt(np.mean(noise_bins**2)))
    if noise_rms <= 0:
        return float('-inf')
    
    noise_floor = 20.0 * np.log10(noise_rms)
    return float(noise_floor)

