"""Headless THD sweep with Tektronix TDS2024B (single-ended or math).

This script mirrors the manual heredoc used earlier and saves a CSV
with Vrms, Vpp, and THD% across a 20 Hz to 20 kHz logarithmic sweep.
It assumes:
  - FY3200S generator connected over serial (FY_PORT env var or auto-detect).
  - Tektronix scope reachable via VISA resource (VISA_RESOURCE env var).
  - CH1 monitors the DUT output by default. Use ``--math`` for CH1-CH2 subtraction.

Example usage (macOS with pyvisa-py and libusb-package):
    PYUSB_LIBRARY=\"/path/to/libusb_package/libusb-1.0.dylib\" \\
    FY_PORT=/dev/cu.usbserial-XXXX \\
    VISA_RESOURCE=USB0::0x0699::0x036A::SERIAL::INSTR \\
    python scripts/thd_math_sweep.py

Add `sudo` if macOS blocks USBTMC access. The same sweep is also
available via the packaged CLI: `amp-benchkit thd-math-sweep`.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

# Ensure repository root on sys.path when running from a checkout.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amp_benchkit.sweeps import format_thd_rows, thd_sweep  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sweep THD using Tektronix scope capture (single-ended or math)."
    )
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
        help="Generator amplitude in Vpp.",
    )
    ap.add_argument(
        "--start-hz",
        type=float,
        default=20.0,
        help="Sweep start frequency.",
    )
    ap.add_argument(
        "--stop-hz",
        type=float,
        default=20000.0,
        help="Sweep stop frequency.",
    )
    ap.add_argument(
        "--points",
        type=int,
        default=61,
        help="Number of logarithmic sweep points.",
    )
    ap.add_argument(
        "--dwell",
        type=float,
        default=0.15,
        help="Dwell time per frequency (seconds). Use 0.3+ for LF stability.",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("results/thd_sweep.csv"),
        help="Destination CSV path.",
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
        help="MATH subtraction order (used only when --math is set).",
    )
    args = ap.parse_args()

    if args.points < 2:
        raise ValueError("points must be >= 2")
    if not math.isfinite(args.amp_vpp) or args.amp_vpp <= 0:
        raise ValueError("amp_vpp must be > 0")
    if not math.isfinite(args.dwell) or args.dwell < 0:
        raise ValueError("dwell must be >= 0")

    rows, out_path = thd_sweep(
        visa_resource=args.visa_resource,
        fy_port=args.fy_port,
        amp_vpp=args.amp_vpp,
        scope_channel=args.channel,
        start_hz=args.start_hz,
        stop_hz=args.stop_hz,
        points=args.points,
        dwell_s=args.dwell,
        use_math=args.math,
        math_order=args.math_order,
        output=args.output,
    )
    if out_path:
        print("Saved:", out_path)
    for line in format_thd_rows(rows):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
