"""Extended DSP utilities.

Advanced waveform-based THD calculation and harmonic analysis extracted from
legacy monolithic file. Keeps compatibility with existing dispatcher by
providing `thd_fft_waveform` which mirrors prior signature.
"""
from __future__ import annotations
from typing import Tuple, List, Dict
import math

try:  # optional
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

__all__ = ["thd_fft_waveform", "harmonic_table"]


def _np_array(x):
    if np is None:
        raise RuntimeError("NumPy not available for advanced DSP")
    return x if isinstance(x, np.ndarray) else np.asarray(x)


def harmonic_table(t, v, f0=None, nharm: int = 10, window: str = "hann") -> List[Dict[str, float]]:
    """Return list of harmonic components with frequency and magnitude.
    Each entry: {"k": harmonic_index, "freq_hz": float, "mag": float}
    """
    if np is None:
        return []
    t = _np_array(t).astype(float)
    v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return []
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        span = t[-1] - t[0]
        dt = span/(n-1) if span > 0 else 1e-6
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    else:
        w = np.ones(n)
    Y = np.fft.rfft(v*w)
    f = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(Y)
    # Fundamental detection
    if f0 is None or f0 <= 0:
        idx = int(np.argmax(mag[1:])) + 1
    else:
        idx = int(np.argmin(np.abs(f - float(f0))))
        if idx <= 0:
            idx = int(np.argmax(mag[1:])) + 1
    base_f = float(f[idx])
    out: List[Dict[str, float]] = []
    for k in range(1, max(2, nharm)+1):
        target = k * base_f
        if target > f[-1]:
            break
        hk = int(np.argmin(np.abs(f - target)))
        out.append({"k": k, "freq_hz": float(f[hk]), "mag": float(mag[hk])})
    return out


def thd_fft_waveform(t, v, f0=None, nharm: int = 10, window: str = 'hann') -> Tuple[float, float, float]:
    """Compute THD ratio and return (thd_ratio, f0_est, fundamental_amplitude)."""
    if np is None:
        return float('nan'), float('nan'), float('nan')
    table = harmonic_table(t, v, f0=f0, nharm=nharm, window=window)
    if not table:
        return float('nan'), float('nan'), float('nan')
    fund = table[0]
    fund_amp = fund["mag"]
    if fund_amp <= 0:
        return float('nan'), fund["freq_hz"], 0.0
    s2 = 0.0
    for entry in table[1:]:
        s2 += entry["mag"]**2
    thd = math.sqrt(s2)/fund_amp if s2 > 0 else 0.0
    return thd, fund["freq_hz"], fund_amp
