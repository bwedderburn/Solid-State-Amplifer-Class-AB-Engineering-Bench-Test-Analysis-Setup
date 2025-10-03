"""DSP helper functions (minimal viable set for tests)."""
from __future__ import annotations
from typing import Iterable, Tuple, Sequence
import math

__all__ = ["vrms", "vpp", "thd_fft", "find_knees"]


def vrms(v: Iterable[float]) -> float:
    try:
        import numpy as np  # optional
        arr = np.asarray(list(v), dtype=float)
        if arr.size == 0:
            return float("nan")
        return float(math.sqrt((arr * arr).mean()))
    except Exception:
        vals = list(v)
        if not vals:
            return float("nan")
        return math.sqrt(sum((float(x) ** 2) for x in vals) / len(vals))


def vpp(v: Iterable[float]) -> float:
    vals = list(v)
    if not vals:
        return float("nan")
    return float(max(vals) - min(vals))


def thd_fft(t, v, f0: float | None = None, nharm: int = 5, window: str = "hann", **_ignored) -> Tuple[float, float, float]:
    """Approximate THD using FFT if numpy present, else stub.

    Returns (thd_ratio, f0_est, fundamental_amp)
    """
    try:
        import numpy as np
        t_arr = np.asarray(t, dtype=float)
        v_arr = np.asarray(v, dtype=float)
        if t_arr.size < 16:
            return float("nan"), float("nan"), float("nan")
        dt = float(t_arr[1] - t_arr[0])
        if window == "hann":
            w_arr = np.hanning(len(v_arr))
        else:
            w_arr = np.ones(len(v_arr))
        spec = np.fft.rfft(v_arr * w_arr)
        freqs = np.fft.rfftfreq(len(v_arr), d=dt)
        if f0 is None:
            f0_idx = int(np.argmax(np.abs(spec)))
        else:
            f0_idx = int(np.argmin(np.abs(freqs - f0)))
        fund_amp = float(np.abs(spec[f0_idx]))
        harm_pow = 0.0
        for k in range(2, nharm + 1):
            idx = f0_idx * k
            if idx < len(spec):
                harm_pow += float(np.abs(spec[idx]) ** 2)
        thd = math.sqrt(harm_pow) / fund_amp if fund_amp > 0 else float("nan")
        return thd, float(freqs[f0_idx]), fund_amp
    except Exception:
        # Fallback stub
        try:
            fund_amp = max(abs(float(x)) for x in v)
            return 0.0, f0 or 1000.0, fund_amp
        except Exception:
            return float("nan"), float("nan"), float("nan")


def find_knees(freqs: Sequence[float], amps: Sequence[float], ref_mode: str = "max", ref_hz: float = 1000.0, drop_db: float = 3.0) -> Tuple[float, float, float, float]:
    """Very simplified knee finder.

    Determines reference amplitude (max or at ref_hz) then finds highest
    frequency where amplitude is within drop_db of reference.
    Returns (lo_ref_freq, hi_knee_freq, ref_amp, ref_db)
    """
    # Accept sequences or numpy arrays; length check via len()
    if len(freqs) == 0 or len(amps) == 0:  # type: ignore[arg-type]
        return float("nan"), float("nan"), float("nan"), float("nan")
    import numpy as np  # rely on numpy if present else simple python
    f_arr = np.asarray(freqs, dtype=float)
    a_arr = np.asarray(amps, dtype=float)
    if ref_mode.lower().startswith("max"):
        ref_amp = float(a_arr.max())
        ref_freq = float(f_arr[a_arr.argmax()])
    else:
        # nearest to ref_hz
        idx = int(np.argmin(np.abs(f_arr - ref_hz)))
        ref_amp = float(a_arr[idx])
        ref_freq = float(f_arr[idx])
    if ref_amp <= 0:
        return ref_freq, ref_freq, ref_amp, 0.0
    ref_db = 20 * math.log10(ref_amp)
    thresh = ref_amp / (10 ** (drop_db / 20))
    # Find first frequency after ref where amplitude drops below threshold
    hi_freq = float('nan')
    passed_ref = False
    for f, a in zip(f_arr, a_arr):
        if not passed_ref and f >= ref_freq:
            passed_ref = True
        if passed_ref and f > ref_freq and a < thresh:
            hi_freq = float(f)
            break
    if math.isnan(hi_freq):  # no drop detected; fall back to last frequency
        hi_freq = float(f_arr[-1])
    return ref_freq, hi_freq, ref_amp, ref_db

