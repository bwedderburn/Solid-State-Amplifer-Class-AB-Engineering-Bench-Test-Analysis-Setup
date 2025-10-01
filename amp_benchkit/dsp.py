"""Stub DSP helpers."""
from __future__ import annotations
from typing import Tuple


# simplistic placeholder
def thd_fft(samples, fs_hz: float) -> Tuple[float, float, float]:
    """Very small placeholder: returns 0 THD and max sample amplitude.

    Parameters
    ----------
    samples : sequence
        Time-domain samples.
    fs_hz : float
        Sample rate in Hz (unused in stub).
    """
    try:
        if not samples:
            return float('nan'), float('nan'), float('nan')
        fund_amp = max(abs(float(x)) for x in samples)
        return 0.0, 1000.0, fund_amp
    except Exception:
        return float('nan'), float('nan'), float('nan')
