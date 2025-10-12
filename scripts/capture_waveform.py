"""Capture a single waveform from the Tektronix scope and dump CSV samples.

This helper configures the FY3200S generator, waits for the signal to settle,
captures either a scope channel or the MATH subtraction trace, and writes the
time/voltage pairs to ``results/waveform_<freq>.csv`` by default.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure repository root on sys.path when running from a checkout.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amp_benchkit.dsp import thd_fft, vpp, vrms  # noqa: E402
from amp_benchkit.fy import fy_apply  # noqa: E402
from amp_benchkit.sweeps import format_thd_rows  # noqa: E402
from amp_benchkit.tek import (  # noqa: E402
    scope_arm_single,
    scope_capture_calibrated,
    scope_configure_math_subtract,
    scope_resume_run,
    scope_wait_single_complete,
)


def capture_waveform(
    *,
    visa_resource: str,
    fy_port: str | None,
    freq_hz: float,
    amp_vpp: float,
    dwell_s: float,
    channel: int,
    use_math: bool,
    math_order: str,
    output: Path,
) -> Path:
    fy_apply(
        port=fy_port,
        proto="FY ASCII 9600",
        freq_hz=freq_hz,
        amp_vpp=amp_vpp,
        wave="Sine",
        off_v=0.0,
        duty=None,
        ch=1,
    )

    if use_math:
        scope_configure_math_subtract(visa_resource, math_order)

    scope_arm_single(visa_resource)
    time.sleep(max(dwell_s, 0.1))
    scope_wait_single_complete(visa_resource, timeout_s=max(1.0, dwell_s + 1.0))

    source = math_order if use_math else channel
    t, v = scope_capture_calibrated(visa_resource, timeout_ms=15000, ch=source)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as fh:
        fh.write("time_s,volts\n")
        for ts, vs in zip(t, v, strict=False):
            fh.write(f"{ts},{vs}\n")

    rms = vrms(v)
    peak = vpp(v)
    thd_ratio, f_est, _ = thd_fft(t, v, f0=freq_hz, nharm=10, window="hann")
    thd_row = format_thd_rows([(freq_hz, rms, peak, thd_ratio * 100.0)])[0]
    print(f"Captured {len(v)} samples @ {freq_hz} Hz")
    thd_pct = thd_ratio * 100.0
    print(f"Vrms {rms:.4f} V, Vpp {peak:.4f} V")
    print(f"THD estimate {thd_pct:.3f}% (f_est {f_est:.2f} Hz)")
    print(thd_row)
    print("Saved:", output)

    scope_resume_run(visa_resource)
    return output


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture a single waveform snapshot to CSV.")
    ap.add_argument("frequency", type=float, help="Generator frequency in Hz.")
    ap.add_argument(
        "--visa-resource",
        default=os.environ.get("VISA_RESOURCE", "USB0::0x0699::0x036A::C100563::INSTR"),
        help="Tektronix VISA resource string.",
    )
    ap.add_argument(
        "--fy-port",
        default=os.environ.get("FY_PORT"),
        help="FY3200S serial port (auto-detect if omitted).",
    )
    ap.add_argument(
        "--amp-vpp",
        type=float,
        default=float(os.environ.get("AMP_VPP", "0.5")),
        help="Generator amplitude (Vpp).",
    )
    ap.add_argument(
        "--dwell",
        type=float,
        default=0.3,
        help="Settle time before capture (seconds).",
    )
    ap.add_argument(
        "--channel",
        type=int,
        default=1,
        help="Scope channel to capture (ignored when --math is set).",
    )
    ap.add_argument(
        "--math",
        action="store_true",
        help="Capture the scope MATH trace instead of a single channel.",
    )
    ap.add_argument(
        "--math-order",
        default="CH1-CH2",
        help="Math subtraction order (used only with --math).",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination CSV path (default results/waveform_<freq>.csv).",
    )
    args = ap.parse_args()

    out_path = (
        args.output if args.output else Path("results") / f"waveform_{int(args.frequency)}Hz.csv"
    )

    capture_waveform(
        visa_resource=args.visa_resource,
        fy_port=args.fy_port,
        freq_hz=args.frequency,
        amp_vpp=args.amp_vpp,
        dwell_s=args.dwell,
        channel=args.channel,
        use_math=args.math,
        math_order=args.math_order,
        output=out_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
