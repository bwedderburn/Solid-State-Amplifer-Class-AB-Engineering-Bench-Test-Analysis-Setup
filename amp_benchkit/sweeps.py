"""Reusable sweep routines for headless instrumentation runs."""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable
from pathlib import Path

from .automation import build_freq_points, sweep_audio_kpis
from .dsp import thd_fft, vpp, vrms
from .fy import fy_apply
from .tek import (
    scope_arm_single,
    scope_capture_calibrated,
    scope_configure_math_subtract,
    scope_resume_run,
    scope_wait_single_complete,
)


def thd_math_sweep(
    *,
    visa_resource: str,
    fy_port: str | None,
    amp_vpp: float = 0.5,
    start_hz: float = 20.0,
    stop_hz: float = 20000.0,
    points: int = 61,
    dwell_s: float = 0.15,
    math_order: str = "CH1-CH2",
    output: Path | None = None,
) -> tuple[list[tuple[float, float, float, float]], Path | None]:
    """Run a THD sweep using the scope math channel (CH1-CH2).

    Returns the raw rows and optional CSV output path if ``output`` was provided.
    """
    if points < 2:
        raise ValueError("points must be >= 2")
    if not math.isfinite(amp_vpp) or amp_vpp <= 0:
        raise ValueError("amp_vpp must be > 0")
    if not math.isfinite(dwell_s) or dwell_s < 0:
        raise ValueError("dwell_s must be >= 0")

    freqs = build_freq_points(start=start_hz, stop=stop_hz, points=points, mode="log")

    result = sweep_audio_kpis(
        freqs,
        channel=1,
        scope_channel=1,
        amp_vpp=amp_vpp,
        dwell_s=dwell_s,
        fy_apply=lambda **kw: fy_apply(port=fy_port, proto="FY ASCII 9600", **kw),
        scope_capture_calibrated=lambda res, ch: scope_capture_calibrated(
            visa_resource, timeout_ms=15000, ch=ch
        ),
        dsp_vrms=vrms,
        dsp_vpp=vpp,
        dsp_thd_fft=lambda t, v, f0: thd_fft(t, v, f0=f0, nharm=10, window="hann"),
        do_thd=True,
        use_math=True,
        math_order=math_order,
        scope_configure_math_subtract=lambda res, order: scope_configure_math_subtract(
            visa_resource, order
        ),
        scope_arm_single=lambda res: scope_arm_single(visa_resource),
        scope_wait_single_complete=lambda res, timeout_s: scope_wait_single_complete(
            visa_resource, timeout_s=timeout_s
        ),
        scope_resource=visa_resource,
    )

    rows: list[tuple[float, float, float, float]] = [
        (freq, vr, pk, thd_percent) for freq, vr, pk, _thd_ratio, thd_percent in result["rows"]
    ]

    out_path: Path | None = None
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["freq_hz", "vrms", "pkpk", "thd_percent"])
            writer.writerows(rows)

    scope_resume_run(visa_resource)
    return rows, out_path


def format_thd_rows(rows: Iterable[tuple[float, float, float, float]]) -> list[str]:
    """Return human readable strings for THD sweep rows."""
    formatted: list[str] = []
    for freq, _vr, _pk, thd_percent in rows:
        if math.isnan(thd_percent):
            formatted.append(f"{freq:8.2f} Hz → THD NaN")
        else:
            formatted.append(f"{freq:8.2f} Hz → THD {thd_percent:6.3f}%")
    return formatted
