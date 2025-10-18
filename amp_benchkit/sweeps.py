"""Reusable sweep routines for headless instrumentation runs."""

from __future__ import annotations

import csv
import logging
import math
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path
from statistics import median

from .automation import build_freq_points, sweep_audio_kpis
from .calibration import CalibrationCurve
from .dsp import thd_fft, vpp, vrms
from .fy import fy_apply
from .tek import (
    scope_arm_single,
    scope_capture_calibrated,
    scope_configure_math_subtract,
    scope_configure_timebase,
    scope_resume_run,
    scope_wait_single_complete,
)


def _filter_spikes(
    rows: list[tuple[float, float, float, float]],
    *,
    window: int,
    factor: float,
    min_percent: float,
):
    suppressed: list[tuple[float, float, float]] = []
    filtered: list[tuple[float, float, float, float]] = []
    total = len(rows)
    for idx, (freq, vr, pk, thd_percent) in enumerate(rows):
        neighbors = [
            rows[j][3]
            for j in range(max(0, idx - window), min(total, idx + window + 1))
            if j != idx and math.isfinite(rows[j][3])
        ]
        if not neighbors or not math.isfinite(thd_percent):
            filtered.append((freq, vr, pk, thd_percent))
            continue
        baseline = median(neighbors)
        threshold = max(min_percent, baseline * factor)
        if thd_percent > threshold:
            suppressed.append((freq, thd_percent, baseline))
            filtered.append((freq, vr, pk, float(baseline)))
        else:
            filtered.append((freq, vr, pk, thd_percent))
    return filtered, suppressed


def thd_sweep(
    *,
    visa_resource: str,
    fy_port: str | None,
    amp_vpp: float = 0.5,
    calibrate_to_vpp: float | None = None,
    fy_proto: str = "FY ASCII 9600",
    scope_channel: int = 1,
    start_hz: float = 20.0,
    stop_hz: float = 20000.0,
    points: int = 61,
    dwell_s: float = 0.15,
    use_math: bool = False,
    math_order: str = "CH1-CH2",
    output: Path | None = None,
    post_freq_hz: float = 1000.0,
    post_seconds_per_div: float | None = 1e-4,
    filter_spikes: bool = True,
    filter_window: int = 2,
    filter_factor: float = 2.0,
    filter_min_percent: float = 2.0,
    calibration_curve: CalibrationCurve | None = None,
) -> tuple[
    list[tuple[float, float, float, float]],
    Path | None,
    list[tuple[float, float, float]],
]:
    """Run a THD sweep capturing either a single scope channel or the math trace.

    Returns the processed rows, optional CSV path, and a list describing any
    spike suppressions ``[(freq_hz, original_thd, replacement_thd), ...]`` when
    filtering is enabled.
    """
    if points < 2:
        raise ValueError("points must be >= 2")
    if not math.isfinite(amp_vpp) or amp_vpp <= 0:
        raise ValueError("amp_vpp must be > 0")
    if not math.isfinite(dwell_s) or dwell_s < 0:
        raise ValueError("dwell_s must be >= 0")

    log = logging.getLogger("amp_benchkit.sweeps")
    freqs = build_freq_points(start=start_hz, stop=stop_hz, points=points, mode="log")

    def _capture(_resource, ch):
        target = math_order if use_math else ch
        return scope_capture_calibrated(visa_resource, timeout_ms=15000, ch=target)

    if calibrate_to_vpp is not None and calibration_curve is None:
        raise ValueError("calibrate_to_vpp requires calibration_curve")

    amplitude_calibration = calibration_curve.apply if calibration_curve else None

    amp_vpp_strategy = None
    if calibrate_to_vpp is not None and calibration_curve is not None:
        target = float(calibrate_to_vpp)

        def _amp_strategy(freq: float) -> float:
            ratio = calibration_curve.ratio_at(freq)
            if ratio <= 0:
                return target
            return target / ratio

        amp_vpp_strategy = _amp_strategy

    sweep_amp = float(calibrate_to_vpp) if calibrate_to_vpp is not None else amp_vpp

    def _fy_apply(**kw):
        return fy_apply(port=fy_port, proto=fy_proto, **kw)

    result = sweep_audio_kpis(
        freqs,
        channel=1,
        scope_channel=scope_channel,
        amp_vpp=sweep_amp,
        dwell_s=dwell_s,
        fy_apply=_fy_apply,
        scope_capture_calibrated=_capture,
        dsp_vrms=vrms,
        dsp_vpp=vpp,
        dsp_thd_fft=lambda t, v, f0: thd_fft(t, v, f0=f0, nharm=10, window="hann"),
        do_thd=True,
        use_math=use_math,
        math_order=math_order,
        cycles_per_capture=10.0,
        scope_configure_math_subtract=(
            (lambda res, order: scope_configure_math_subtract(visa_resource, order))
            if use_math
            else None
        ),
        scope_arm_single=lambda res: scope_arm_single(visa_resource),
        scope_wait_single_complete=lambda res, timeout_s: scope_wait_single_complete(
            visa_resource, timeout_s=timeout_s
        ),
        scope_resource=visa_resource,
        amplitude_calibration=amplitude_calibration,
        amp_vpp_strategy=amp_vpp_strategy,
    )

    rows: list[tuple[float, float, float, float]] = []
    corrected_full_rows: list[tuple[float, float, float, float, float]] = []
    for freq, vr, pk, thd_ratio, thd_percent in result["rows"]:
        if calibration_curve:
            if math.isfinite(vr):
                vr = calibration_curve.apply(freq, vr)
            if math.isfinite(pk):
                pk = calibration_curve.apply(freq, pk)
        rows.append((freq, vr, pk, thd_percent))
        corrected_full_rows.append((freq, vr, pk, thd_ratio, thd_percent))
    if calibration_curve:
        result["rows"] = corrected_full_rows

    suppressed: list[tuple[float, float, float]] = []
    if filter_spikes and rows:
        rows, suppressed = _filter_spikes(
            rows,
            window=filter_window,
            factor=filter_factor,
            min_percent=filter_min_percent,
        )

    out_path: Path | None = None
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["freq_hz", "vrms", "pkpk", "thd_percent"])
            writer.writerows(rows)

    scope_resume_run(visa_resource)
    # Restore predictable idle state (1 kHz tone, fast timebase) for quick follow-up work.
    try:  # pragma: no cover - hardware-specific
        _fy_apply(
            freq_hz=post_freq_hz,
            amp_vpp=amp_vpp,
            wave="Sine",
            off_v=0.0,
            duty=None,
            ch=1,
        )
    except Exception as exc:  # pragma: no cover - hardware-specific
        log.warning(
            "FY reset to %.1f Hz failed (amp %.2f Vpp, port=%s, proto=%s): %s",
            post_freq_hz,
            amp_vpp,
            fy_port or "<auto>",
            fy_proto,
            exc,
        )
    if post_seconds_per_div is not None:
        with suppress(Exception):  # pragma: no cover - hardware-specific
            scope_configure_timebase(visa_resource, post_seconds_per_div)
    return rows, out_path, suppressed


def format_thd_rows(rows: Iterable[tuple[float, float, float, float]]) -> list[str]:
    """Return human readable strings for THD sweep rows."""
    formatted: list[str] = []
    for freq, _vr, _pk, thd_percent in rows:
        if math.isnan(thd_percent):
            formatted.append(f"{freq:8.2f} Hz → THD NaN")
        else:
            formatted.append(f"{freq:8.2f} Hz → THD {thd_percent:6.3f}%")
    return formatted
