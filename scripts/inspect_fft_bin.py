#!/usr/bin/env python3
"""Spot-check a single FFT capture CSV.

Usage:
    python scripts/inspect_fft_bin.py path/to/fft.csv --drive 20 --show 12
"""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Iterable, Sequence
from pathlib import Path


def load_fft(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header_read = False
        for row in reader:
            if not header_read:
                header_read = True
                continue
            if len(row) < 2:
                continue
            try:
                freq = float(str(row[0]).replace('"', ""))
                value = float(str(row[1]).replace('"', ""))
            except ValueError:
                continue
            rows.append((freq, value))
    return rows


def nearest_bin(
    rows: Sequence[tuple[float, float]], target_hz: float
) -> tuple[float, float] | None:
    if not rows:
        return None
    best = min(rows, key=lambda item: abs(item[0] - target_hz))
    return best


def top_bins(
    rows: Iterable[tuple[float, float]],
    *,
    limit: int,
    magnitude: bool,
) -> list[tuple[float, float]]:
    ranking = sorted(rows, key=lambda item: (abs(item[1]) if magnitude else item[1]), reverse=True)
    return ranking[:limit]


def describe(
    fft_rows: Sequence[tuple[float, float]],
    *,
    drive_hz: float | None,
    show: int,
    magnitude: bool,
) -> None:
    if not fft_rows:
        print("FFT appears empty.")
        return
    print(f"Loaded {len(fft_rows)} bins: {fft_rows[0][0]:.3f} Hz → {fft_rows[-1][0]:.3f} Hz")
    ranking = top_bins(fft_rows, limit=show, magnitude=magnitude)
    mode_label = "abs amplitude" if magnitude else "amplitude"
    print(f"Top {len(ranking)} bins (sorted by {mode_label}):")
    for freq, value in ranking:
        print(f"  {freq:12.4f} Hz -> {value:10.4f} dB")
    if drive_hz is not None:
        closest = nearest_bin(fft_rows, drive_hz)
        if closest:
            delta = closest[0] - drive_hz
            print(
                "\nClosest to drive "
                f"{drive_hz:.4f} Hz -> {closest[0]:.4f} Hz "
                f"({delta:+.4f} Hz), {closest[1]:.4f} dB"
            )
        else:
            print("\nDrive analysis unavailable (no bins loaded).")
    noise_floor = percentile((abs(v) for _, v in fft_rows), percentage=50.0)
    print(f"\nNoise floor estimate (median abs amplitude): {noise_floor:.4f} dB")


def percentile(values: Iterable[float], *, percentage: float) -> float:
    data = sorted(values)
    if not data:
        return math.nan
    idx = (percentage / 100.0) * (len(data) - 1)
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return data[int(idx)]
    weight = idx - lower
    return data[lower] * (1 - weight) + data[upper] * weight


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a single FFT capture CSV.")
    parser.add_argument("fft_csv", type=Path, help="Path to fft_*.csv captured by live sweep.")
    parser.add_argument(
        "--drive",
        type=float,
        default=None,
        help="Expected drive frequency (Hz) for nearest-bin highlighting.",
    )
    parser.add_argument(
        "--show",
        type=int,
        default=8,
        help="Number of dominant bins to display.",
    )
    parser.add_argument(
        "--magnitude",
        action="store_true",
        help="Sort peaks by absolute amplitude instead of raw value.",
    )
    args = parser.parse_args()

    rows = load_fft(args.fft_csv)
    describe(rows, drive_hz=args.drive, show=max(1, args.show), magnitude=args.magnitude)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
