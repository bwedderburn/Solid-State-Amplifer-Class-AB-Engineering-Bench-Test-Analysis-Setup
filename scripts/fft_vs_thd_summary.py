"""Aggregate THD sweep data against a directory of FFT captures."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import TypedDict

from fft_thd_compare import _load_fft, _load_thd, compute_fft_thd


def _extract_freq(path: Path) -> float | None:
    match = re.search(r"fft_([0-9.]+)Hz", path.stem)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


class SummaryRow(TypedDict):
    fft_file: str
    center_hz: float
    fft_thd_percent: float
    sweep_freq_hz: float
    sweep_thd_percent: float
    delta_percent: float


def summarize(
    fft_files: list[Path],
    thd_map: dict[float, float],
    *,
    window: float,
    harmonics: int,
) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    for path in sorted(fft_files):
        center = _extract_freq(path)
        if center is None:
            continue
        freqs, values, _x_unit, y_unit = _load_fft(path)
        if not freqs or not values:
            continue
        fft_thd, _harmonics_list = compute_fft_thd(
            freqs,
            values,
            scale=y_unit,
            fundamental_hz=center,
            harmonics=harmonics,
            window=window,
        )
        nearest = min(thd_map, key=lambda f: abs(f - center), default=None)
        sweep_thd = float("nan") if nearest is None else thd_map.get(nearest, float("nan"))
        if math.isfinite(fft_thd) and math.isfinite(sweep_thd):
            delta = fft_thd - sweep_thd
        else:
            delta = float("nan")
        sweep_freq = float(nearest) if nearest is not None else float("nan")
        rows.append(
            {
                "fft_file": str(path),
                "center_hz": center,
                "fft_thd_percent": fft_thd,
                "sweep_freq_hz": sweep_freq,
                "sweep_thd_percent": sweep_thd,
                "delta_percent": delta,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Summarize FFT vs THD sweep results.")
    p.add_argument(
        "--fft-dir",
        required=True,
        type=Path,
        help="Directory containing fft sweep CSV files (fft_<freq>Hz_*.csv).",
    )
    p.add_argument("--thd", required=True, type=Path, help="THD sweep CSV.")
    p.add_argument("--window", type=float, default=50.0, help="Frequency window in Hz.")
    p.add_argument("--harmonics", type=int, default=8, help="Harmonics to include.")
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional summary CSV output (defaults to fft-summary.csv in fft-dir).",
    )
    args = p.parse_args(argv)

    fft_dir = args.fft_dir
    fft_files = sorted(fft_dir.glob("fft_*Hz_*.csv"))
    if not fft_files:
        print("No FFT files matched pattern fft_*Hz_*.csv in", fft_dir)
        return 1
    thd_rows = _load_thd(args.thd)
    rows = summarize(
        fft_files,
        thd_rows,
        window=max(args.window, 1.0),
        harmonics=max(args.harmonics, 1),
    )
    if not rows:
        print("No rows generated (check FFT files and THD data).")
        return 1

    output_path = args.output or (fft_dir / "fft_thd_summary.csv")
    with output_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "fft_file",
                "center_hz",
                "fft_thd_percent",
                "sweep_freq_hz",
                "sweep_thd_percent",
                "delta_percent",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print("Summary saved:", output_path)
    for row in rows:
        sweep_freq = row["sweep_freq_hz"]
        sweep_thd = row["sweep_thd_percent"]
        delta = row["delta_percent"]
        print(
            f"{row['center_hz']:8.2f} Hz → FFT THD {row['fft_thd_percent']:.3f}% | "
            f"Sweep {sweep_freq:.2f} Hz {sweep_thd:.3f}% (Δ {delta:.3f} %)"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
