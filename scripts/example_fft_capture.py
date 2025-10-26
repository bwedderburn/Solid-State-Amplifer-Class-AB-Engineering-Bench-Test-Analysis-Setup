#!/usr/bin/env python3
"""Example: Capture FFT with proper vertical scaling for TDS 2024B.

This script demonstrates how to use the enhanced FFT capture functions
with proper vertical scale and position configuration for accurate
FFT measurements on the Tektronix TDS 2024B oscilloscope.

Usage:
    python scripts/example_fft_capture.py --visa-resource USB0::0x0699::0x036A::C100563::INSTR

The script shows how to:
1. Read current FFT vertical parameters
2. Configure FFT with custom vertical scale and position
3. Capture FFT data with proper scaling
4. Save results to CSV and plot
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

# Ensure repository root on sys.path when running from a checkout.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amp_benchkit.tek import (
    scope_capture_fft_trace,
    scope_read_fft_vertical_params,
)


def main() -> int:
    """Main function for FFT capture example."""
    parser = argparse.ArgumentParser(description="Capture FFT with proper vertical scaling")
    parser.add_argument(
        "--visa-resource",
        default=os.environ.get("VISA_RESOURCE", "USB0::0x0699::0x036A::C100563::INSTR"),
        help="Tektronix VISA resource string",
    )
    parser.add_argument(
        "--source",
        type=int,
        default=1,
        help="Source channel for FFT (1-4)",
    )
    parser.add_argument(
        "--window",
        default="HANNING",
        choices=["RECTANGULAR", "HANNING", "HAMMING", "BLACKMAN", "FLATTOP"],
        help="FFT window function",
    )
    parser.add_argument(
        "--scale",
        default="DB",
        choices=["LINEAR", "DB"],
        help="FFT vertical scale (LINEAR or DB)",
    )
    parser.add_argument(
        "--vertical-scale",
        type=float,
        default=10.0,
        help="Vertical scale in units/div (e.g., 10 for 10dB/div in DB mode)",
    )
    parser.add_argument(
        "--vertical-position",
        type=float,
        default=0.0,
        help="Vertical position in divisions (-5.0 to +5.0)",
    )
    parser.add_argument(
        "--output",
        default="results/fft_capture.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate and save a plot of the FFT",
    )

    args = parser.parse_args()

    print(f"Connecting to scope: {args.visa_resource}")
    print(f"Source channel: CH{args.source}")
    print(f"Window: {args.window}")
    print(f"Scale: {args.scale}")
    print(f"Vertical scale: {args.vertical_scale} units/div")
    print(f"Vertical position: {args.vertical_position} div")

    # Read current FFT vertical parameters
    print("\nReading current FFT vertical parameters...")
    current_params = scope_read_fft_vertical_params(args.visa_resource)
    if current_params:
        print(f"  Current scale: {current_params.get('scale')} units/div")
        print(f"  Current position: {current_params.get('position')} div")
    else:
        print("  Unable to read current parameters")

    # Capture FFT with specified vertical scale and position
    print(f"\nCapturing FFT trace with {args.vertical_scale} units/div...")
    try:
        result = scope_capture_fft_trace(
            resource=args.visa_resource,
            source=args.source,
            window=args.window,
            scale=args.scale,
            vertical_scale=args.vertical_scale,
            vertical_position=args.vertical_position,
        )

        freqs = result["freqs"]
        values = result["values"]
        x_unit = result["x_unit"]
        y_unit = result["y_unit"]

        print(f"Captured {len(freqs)} points")
        print(f"Frequency range: {freqs[0]:.2f} to {freqs[-1]:.2f} {x_unit}")
        print(f"Amplitude unit: {y_unit}")

        # Save to CSV
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([f"Frequency ({x_unit})", f"Amplitude ({y_unit})"])
            for freq, val in zip(freqs, values, strict=False):
                writer.writerow([freq, val])
        print(f"\nSaved FFT data to: {args.output}")

        # Generate plot if requested
        if args.plot:
            try:
                import matplotlib.pyplot as plt

                plt.figure(figsize=(10, 6))
                plt.plot(freqs, values)
                plt.xlabel(f"Frequency ({x_unit})")
                plt.ylabel(f"Amplitude ({y_unit})")
                plt.title(f"FFT - CH{args.source} - {args.window} window - {args.scale} scale")
                plt.grid(True, alpha=0.3)

                plot_path = args.output.replace(".csv", ".png")
                plt.savefig(plot_path, dpi=150, bbox_inches="tight")
                print(f"Saved plot to: {plot_path}")
                plt.close()
            except ImportError:
                print("matplotlib not available, skipping plot generation")

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
