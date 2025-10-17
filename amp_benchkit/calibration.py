"""Calibration helpers for compensating measurement path loss/gain."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from importlib import resources


@dataclass(frozen=True)
class CalibrationCurve:
    """Frequency→ratio lookup with log-spaced interpolation."""

    freqs: tuple[float, ...]
    ratios: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.freqs) != len(self.ratios):
            raise ValueError("frequency and ratio arrays must be the same length")
        if len(self.freqs) < 2:
            raise ValueError("calibration requires at least two points")
        if any(f <= 0 for f in self.freqs):
            raise ValueError("frequencies must be > 0")

    def ratio_at(self, freq_hz: float) -> float:
        """Return the calibration ratio at `freq_hz` using log-frequency interpolation."""

        freq = float(freq_hz)
        if freq <= self.freqs[0]:
            return self.ratios[0]
        if freq >= self.freqs[-1]:
            return self.ratios[-1]
        # Binary search
        lo = 0
        hi = len(self.freqs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.freqs[mid] <= freq:
                lo = mid
            else:
                hi = mid
        f1, f2 = self.freqs[lo], self.freqs[hi]
        r1, r2 = self.ratios[lo], self.ratios[hi]
        if math.isclose(f1, f2):
            return r1
        log_f = math.log(freq)
        w = (log_f - math.log(f1)) / (math.log(f2) - math.log(f1))
        return r1 + (r2 - r1) * w

    def apply(self, freq_hz: float, amplitude: float) -> float:
        """Return amplitude corrected for path gain (divide by ratio)."""

        ratio = self.ratio_at(freq_hz)
        if ratio <= 0:
            return float("nan")
        return float(amplitude) / ratio

    def apply_array(self, freqs: Iterable[float], amplitudes: Iterable[float]) -> list[float]:
        return [self.apply(f, a) for f, a in zip(freqs, amplitudes, strict=False)]


@cache
def load_calibration_curve(name: str = "gold_reference") -> CalibrationCurve:
    """Load a packaged calibration curve."""

    package = "amp_benchkit.calibration_data"
    filename = f"{name}.json"
    data = json.loads(resources.files(package).joinpath(filename).read_text())
    freqs = tuple(float(f) for f in data["frequencies"])
    ratios = tuple(float(r) for r in data["ratio"])
    return CalibrationCurve(freqs=freqs, ratios=ratios)
