"""Stub automation module.

Provides build_freq_points for CLI usage.
"""
from __future__ import annotations
from typing import List


def build_freq_points(start: float, stop: float, points: int, mode: str = "linear") -> List[float]:
    if points <= 1:
        return [round(start, 6)]
    if mode == "log":
        import math
        if start <= 0 or stop <= 0:
            raise ValueError("Log sweep requires positive start/stop")
        ln_s = math.log(start)
        ln_e = math.log(stop)
        vals = [round((math.e ** (ln_s + (ln_e - ln_s) * i / (points - 1))), 6)
                for i in range(points)]
    else:
        step = (stop - start) / (points - 1)
        vals = [round(start + step * i, 6) for i in range(points)]
    # Ensure exact endpoints rounding at 6 decimals
    vals[0] = round(start, 6)
    vals[-1] = round(stop, 6)
    return vals
