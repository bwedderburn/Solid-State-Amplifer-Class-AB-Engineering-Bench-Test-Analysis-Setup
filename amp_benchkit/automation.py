"""Automation orchestration helpers.

This module provides headless (non-GUI) functions that implement the
core logic previously embedded inside the UnifiedGUI class methods
`run_sweep_scope_fixed` and `run_audio_kpis`.

Design goals:
- Decouple hardware/measurement orchestration from GUI widget access.
- Allow reuse in CLI / scripting contexts.
- Keep side-effects (file writes, logging) injectable.

Public functions:
- sweep_scope_fixed(...): perform a frequency sweep recording a chosen metric.
- sweep_audio_kpis(...): perform a frequency sweep computing Vrms / PkPk / THD and knees.

Both functions accept callables for instrument operations so they can
be monkey‑patched or replaced in tests.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from typing import Any

Number = float

# Type aliases for dependency injection
FyApplyFn = Callable[..., Any]
ScopeMeasureFn = Callable[[Any, str], float]
ScopeCaptureFn = Callable[..., tuple[Sequence[float], Sequence[float]]]
DspVrmsFn = Callable[[Sequence[float]], float]
DspVppFn = Callable[[Sequence[float]], float]
ThdFn = Callable[
    [Sequence[float], Sequence[float], float], tuple[float, float, Any]
]  # (thd_ratio, f_est, spectrum)
FindKneesFn = Callable[
    [Sequence[float], Sequence[float], str, float, float], tuple[float, float, float, float]
]


class SweepAbort(Exception):
    """Raised internally to signal a user abort."""


def build_freq_list(start: Number, stop: Number, step: Number) -> list[Number]:
    if step <= 0:
        raise ValueError("step must be > 0")
    freqs: list[Number] = []
    f = start
    # Inclusive stop with small epsilon
    while f <= stop + 1e-9:
        freqs.append(round(f, 6))
        f += step
    return freqs


def build_freq_points(
    *, start: Number, stop: Number, points: int, mode: str = "log"
) -> list[Number]:
    """Build a list of frequency points.

    Parameters
    ----------
    start, stop : Number
        Sweep endpoints (inclusive).
    points : int
        Number of points >= 2.
    mode : str
        'log' for logarithmic (geometric) spacing, 'linear' for uniform spacing.
    """
    if points < 2:
        raise ValueError("points must be >= 2")
    if start <= 0 or stop <= 0:
        raise ValueError("start/stop must be > 0")
    if stop < start:
        raise ValueError("stop must be >= start")
    mode = mode.lower()
    if mode not in ("log", "linear"):
        raise ValueError("mode must be 'log' or 'linear'")
    if mode == "linear":
        step = (stop - start) / (points - 1)
        return [round(start + i * step, 6) for i in range(points)]
    # log
    r = (stop / start) ** (1 / (points - 1))
    out = [start * (r**i) for i in range(points)]
    return [round(x, 6) for x in out]


def sweep_scope_fixed(
    freqs: Sequence[Number],
    channel: int,
    scope_channel: int,
    amp_vpp: Number,
    dwell_s: Number,
    metric: str,
    *,
    fy_apply: FyApplyFn,
    scope_measure: ScopeMeasureFn,
    scope_configure_math_subtract: Callable[[Any, str], Any] | None = None,
    scope_set_trigger_ext: Callable[[Any, str, float | None], Any] | None = None,
    scope_arm_single: Callable[[Any], Any] | None = None,
    scope_wait_single_complete: Callable[[Any, float], bool] | None = None,
    use_math: bool = False,
    math_order: str = "CH1-CH2",
    use_ext: bool = False,
    ext_slope: str = "Rise",
    ext_level: float | None = None,
    pre_ms: float = 5.0,
    scope_resource: Any = None,
    logger: Callable[[str], Any] = lambda s: None,
    progress: Callable[[int, int], Any] = lambda i, n: None,
    abort_flag: Callable[[], bool] = lambda: False,
    u3_autoconfig: Callable[[], Any] | None = None,
) -> list[tuple[Number, float]]:
    """Perform a simple scope measurement sweep.

    Returns list of (freq_hz, metric_value).
    """
    out: list[tuple[Number, float]] = []
    metric_key = "RMS" if metric.upper() == "RMS" else "PK2PK"
    if u3_autoconfig:
        try:
            u3_autoconfig()
        except Exception as e:
            logger(f"U3 auto-config warn: {e}")
    n = len(freqs)
    for i, f in enumerate(freqs):
        if abort_flag():
            break
        try:
            try:
                fy_apply(
                    freq_hz=f,
                    amp_vpp=amp_vpp,
                    wave="Sine",
                    off_v=0.0,
                    duty=None,
                    ch=channel,
                )
            except Exception as e:
                logger(f"FY error @ {f} Hz: {e}")
                continue
            time.sleep(max(0.0, dwell_s))
            if use_math and scope_configure_math_subtract:
                try:
                    scope_configure_math_subtract(scope_resource, math_order)
                except Exception as e:
                    logger(f"MATH config error: {e}")
            if (
                use_ext
                and scope_set_trigger_ext
                and scope_arm_single
                and scope_wait_single_complete
            ):
                try:
                    scope_set_trigger_ext(scope_resource, ext_slope, ext_level)
                    scope_arm_single(scope_resource)
                    if pre_ms > 0:
                        time.sleep(pre_ms / 1000.0)
                    scope_wait_single_complete(scope_resource, max(1.0, dwell_s * 2 + 0.5))
                except Exception as e:
                    logger(f"EXT trig wait error: {e}")
            try:
                src = "MATH" if use_math else scope_channel
                val = scope_measure(src, metric_key)
            except Exception as e:
                logger(f"Scope error @ {f} Hz: {e}")
                val = float("nan")
            out.append((f, val))
            src_label = "MATH" if use_math else f"CH{scope_channel}"
            logger(f"{f:.3f} Hz → {metric_key} {val:.4f} ({src_label})")
        finally:
            progress(i + 1, n)
    return out


def sweep_audio_kpis(
    freqs: Sequence[Number],
    channel: int,
    scope_channel: int,
    amp_vpp: Number,
    dwell_s: Number,
    *,
    fy_apply: FyApplyFn,
    scope_capture_calibrated: ScopeCaptureFn,
    dsp_vrms: DspVrmsFn,
    dsp_vpp: DspVppFn,
    dsp_thd_fft: (
        Callable[[Sequence[float], Sequence[float], float], tuple[float, float, Any]] | None
    ) = None,
    dsp_find_knees: FindKneesFn | None = None,
    do_thd: bool = False,
    do_knees: bool = False,
    knee_drop_db: float = 3.0,
    knee_ref_mode: str = "Max",
    knee_ref_hz: float = 1000.0,
    use_math: bool = False,
    math_order: str = "CH1-CH2",
    use_ext: bool = False,
    ext_slope: str = "Rise",
    ext_level: float | None = None,
    pre_ms: float = 5.0,
    pulse_line: str = "None",
    pulse_ms: float = 0.0,
    u3_pulse_line: Callable[[str, float, int], Any] | None = None,
    scope_set_trigger_ext: Callable[[Any, str, float | None], Any] | None = None,
    scope_arm_single: Callable[[Any], Any] | None = None,
    scope_wait_single_complete: Callable[[Any, float], bool] | None = None,
    scope_configure_math_subtract: Callable[[Any, str], Any] | None = None,
    scope_resource: Any = None,
    logger: Callable[[str], Any] = lambda s: None,
    progress: Callable[[int, int], Any] = lambda i, n: None,
    abort_flag: Callable[[], bool] = lambda: False,
    u3_autoconfig: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Perform audio KPI sweep.

    Returns dict with keys:
      rows: List[(freq, vrms, pkpk, thd_ratio, thd_percent)]
      knees: Optional[(f_lo, f_hi, ref_amp, ref_db)]
    """
    if u3_autoconfig:
        try:
            u3_autoconfig()
        except Exception as e:
            logger(f"U3 auto-config warn: {e}")
    n = len(freqs)
    rows = []
    for i, f in enumerate(freqs):
        if abort_flag():
            break
        try:
            try:
                fy_apply(
                    freq_hz=f,
                    amp_vpp=amp_vpp,
                    wave="Sine",
                    off_v=0.0,
                    duty=None,
                    ch=channel,
                )
            except Exception as e:
                logger(f"FY error @ {f} Hz: {e}")
                continue
            # EXT / U3 pulse orchestration
            try:
                if use_ext and scope_set_trigger_ext:
                    scope_set_trigger_ext(scope_resource, ext_slope, ext_level)
                if scope_arm_single:
                    scope_arm_single(scope_resource)
                if pre_ms > 0:
                    time.sleep(pre_ms / 1000.0)
                if u3_pulse_line and pulse_line and pulse_line != "None" and pulse_ms > 0.0:
                    u3_pulse_line(pulse_line, pulse_ms, 1)
            except Exception as e:
                logger(f"U3/EXT trig error: {e}")
            # Wait for capture or dwell
            done = False
            if scope_wait_single_complete:
                try:
                    timeout = max(1.0, dwell_s * 4 + 1.0)
                    done = scope_wait_single_complete(scope_resource, timeout)
                except Exception:
                    done = False
            if not done and dwell_s > 0:
                time.sleep(dwell_s or 0.2)
            if use_math and scope_configure_math_subtract:
                try:
                    scope_configure_math_subtract(scope_resource, math_order)
                except Exception as e:
                    logger(f"MATH config error: {e}")
            # Capture
            try:
                src = "MATH" if use_math else scope_channel
                t, v = scope_capture_calibrated(scope_resource, ch=src)
            except Exception as e:
                logger(f"Scope capture error @ {f} Hz: {e}")
                t = []
                v = []
            have_samples = False
            try:
                have_samples = len(v) > 0  # works for lists or numpy arrays
            except Exception:
                have_samples = False
            vr = dsp_vrms(v) if have_samples else float("nan")
            pp = dsp_vpp(v) if have_samples else float("nan")
            thd_ratio = float("nan")
            thd_percent = float("nan")
            if do_thd and dsp_thd_fft and have_samples:
                try:
                    thd_ratio, f_est, _ = dsp_thd_fft(t, v, f)
                    thd_percent = (
                        float(thd_ratio * 100.0) if math.isfinite(thd_ratio) else float("nan")
                    )
                except Exception as e:
                    logger(f"THD calc error @ {f} Hz: {e}")
            rows.append((f, vr, pp, thd_ratio, thd_percent))
            msg = f"{f:.3f} Hz → Vrms {vr:.4f} V, PkPk {pp:.4f} V"
            if math.isfinite(thd_percent):
                msg += f", THD {thd_percent:.3f}%"
            logger(msg)
        finally:
            progress(i + 1, n)
    knees = None
    if do_knees and dsp_find_knees and rows:
        try:
            freqs2 = [r[0] for r in rows]
            amps = [r[2] for r in rows]
            f_lo, f_hi, ref_amp, ref_db = dsp_find_knees(
                freqs2,
                amps,
                "freq" if knee_ref_mode.lower().startswith("1k") else "max",
                knee_ref_hz,
                knee_drop_db,
            )
            knees = (f_lo, f_hi, ref_amp, ref_db)
            logger(
                f"Knees @ -{knee_drop_db:.2f} dB (ref {knee_ref_mode}): "
                f"low≈{f_lo:.2f} Hz, high≈{f_hi:.2f} Hz "
                f"(ref_amp={ref_amp:.4f} V, ref_dB={ref_db:.2f} dB)"
            )
        except Exception as e:
            logger(f"Knee calc error: {e}")
    return {"rows": rows, "knees": knees}
