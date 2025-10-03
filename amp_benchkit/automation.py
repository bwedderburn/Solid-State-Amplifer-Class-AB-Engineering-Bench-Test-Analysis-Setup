"""Automation helpers.

Minimal reconstruction of previously available public functions expected
by tests: build_freq_list (legacy name), sweep_scope_fixed, sweep_audio_kpis.
Functions are intentionally lightweight and dependency-injected so tests can
provide fakes (no hardware I/O here).
"""
from __future__ import annotations
from typing import List, Iterable, Callable, Sequence, Tuple, Dict, Any
import math

__all__ = [
    "build_freq_points", "build_freq_list", "sweep_scope_fixed", "sweep_audio_kpis"
]


def build_freq_points(start: float, stop: float, points: int, mode: str = "linear") -> List[float]:
    """Return a list of frequencies rounded to 6 decimals inclusive of endpoints.

    Deterministic rounding enforced for test reproducibility.
    """
    if points <= 1:
        raise ValueError("points must be >= 2")
    if mode.lower().startswith("log"):
        if start <= 0 or stop <= 0:
            raise ValueError("Log sweep requires positive start/stop")
        ln_s = math.log(start)
        ln_e = math.log(stop)
        vals = [math.exp(ln_s + (ln_e - ln_s) * i / (points - 1)) for i in range(points)]
    else:
        step = (stop - start) / (points - 1)
        vals = [start + step * i for i in range(points)]
    # Round to 6 decimals; fix endpoints exactly
    out = [round(v, 6) for v in vals]
    out[0] = round(start, 6)
    out[-1] = round(stop, 6)
    return out


def build_freq_list(start: float, stop: float, step: float) -> List[int]:
    """Legacy helper: inclusive integer frequency list used by tests.

    Mirrors earlier behavior: produce ints (not floats).
    """
    if step <= 0:
        raise ValueError("step must be > 0")
    n = int(round((stop - start) / step))
    vals = [int(start + i * step) for i in range(n + 1)]
    if vals[-1] != int(stop):
        vals.append(int(stop))
    return vals


def sweep_scope_fixed(
    *,
    freqs: Sequence[float],
    channel: int,
    scope_channel: int,
    amp_vpp: float,
    dwell_s: float,
    metric: str,
    fy_apply: Callable[..., Any],
    scope_measure: Callable[[int, str], float],
) -> List[Tuple[float, float]]:
    """Iterate frequencies applying generator settings and measuring scope metric.

    Parameters are injected so tests can supply fakes. Returns list of (freq, value).
    Fail-soft: exceptions per-frequency yield (freq, nan).
    """
    out: List[Tuple[float, float]] = []
    for f in freqs:
        try:
            fy_apply(freq_hz=f, amp_vpp=amp_vpp, ch=channel)
            val = scope_measure(scope_channel, metric)
        except Exception:  # pragma: no cover - defensive
            val = float("nan")
        out.append((f, val))
    return out


def sweep_audio_kpis(
    freqs: Sequence[float],
    *,
    channel: int,
    scope_channel: int,
    amp_vpp: float,
    dwell_s: float,
    fy_apply: Callable[..., Any],
    scope_capture_calibrated: Callable[[int, int], Tuple[Iterable[float], Iterable[float]]],
    dsp_vrms: Callable[[Iterable[float]], float],
    dsp_vpp: Callable[[Iterable[float]], float],
    dsp_thd_fft: Callable[[Iterable[float], Iterable[float], float], Tuple[float, float, Any]],
    dsp_find_knees: Callable[[Sequence[float], Sequence[float], str, float, float], Tuple[float, float, float, float]],
    do_thd: bool = False,
    do_knees: bool = False,
    ref_mode: str | None = None,
    ref_hz: float | None = None,
    drop_db: float = 3.0,
) -> Dict[str, Any]:
    """Compute audio KPIs over frequencies.

    Returns dict with 'rows' and optional 'knees'. Each row: (freq, vrms, vpp, thd?).
    """
    rows: List[Tuple[float, float, float, float | None]] = []
    vrms_vals: List[float] = []
    for f in freqs:
        try:
            fy_apply(freq_hz=f, amp_vpp=amp_vpp, ch=channel)
            t, v = scope_capture_calibrated(scope_channel, 1)  # dummy signature (resource mocked)
            vr = dsp_vrms(v)
            pp = dsp_vpp(v)
            vrms_vals.append(vr)
            thd_ratio: float | None = None
            if do_thd:
                thd_ratio, _f_est, _ = dsp_thd_fft(t, v, f)
        except Exception:  # pragma: no cover
            vr = pp = float("nan")
            thd_ratio = float("nan") if do_thd else None
        rows.append((f, vr, pp, thd_ratio))
    result: Dict[str, Any] = {"rows": rows}
    if do_knees and vrms_vals:
        # Provide knees over raw vrms values; ref_mode normalized
        ref_mode_eff = (ref_mode or "max").lower()
        k = dsp_find_knees(list(freqs), vrms_vals, ref_mode_eff, ref_hz or 1000.0, drop_db)
        result["knees"] = k
    return result

