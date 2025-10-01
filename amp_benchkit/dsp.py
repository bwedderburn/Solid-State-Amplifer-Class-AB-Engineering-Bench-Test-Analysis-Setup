"""Stub DSP helpers."""
from __future__ import annotations
from typing import Tuple
import math

def thd_fft(samples, fs_hz: float) -> Tuple[float, float, float]:  # simplistic placeholder
    try:
        n = len(samples)
        if n == 0:
            return float('nan'), float('nan'), float('nan')
        # Very naive fundamental estimate: max abs sample as amplitude (placeholder)
        fund_amp = max(abs(x) for x in samples)
        thd_ratio = 0.0  # not computed in stub
        return thd_ratio, 1000.0, fund_amp
    except Exception:
        return float('nan'), float('nan'), float('nan')
