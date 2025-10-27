#!/usr/bin/env python3
"""Combine low/high FFT passes into a single stitched trace per frequency."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


class FFTTrace(NamedTuple):
    freq_token: str
    rows: list[tuple[float, float]]
    source: Path


@dataclass
class StitchConfig:
    blend_hz: float
    prefer_high: bool


def parse_fft_file(path: Path) -> FFTTrace:
    token = path.stem.replace("fft_low_", "").replace("fft_high_", "")
    rows: list[tuple[float, float]] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = True
        for row in reader:
            if header:
                header = False
                continue
            if len(row) < 2:
                continue
            try:
                freq = float(str(row[0]).replace('"', ""))
                value = float(str(row[1]).replace('"', ""))
            except ValueError:
                continue
            rows.append((freq, value))
    return FFTTrace(freq_token=token, rows=rows, source=path)


def stitch_pair(
    low: FFTTrace | None,
    high: FFTTrace | None,
    *,
    cfg: StitchConfig,
) -> list[tuple[float, float]]:
    candidates: list[tuple[float, float]] = []
    if low:
        low_rows = [(f, v) for f, v in low.rows if f <= cfg.blend_hz]
        candidates.extend(low_rows)
    if high:
        high_rows = [(f, v) for f, v in high.rows if f > cfg.blend_hz]
        candidates.extend(high_rows)
    if not candidates and low:
        candidates = low.rows.copy()
    if not candidates and high:
        candidates = high.rows.copy()
    return sorted(candidates, key=lambda item: item[0])


def collect_pairs(root: Path) -> dict[str, dict[str, FFTTrace]]:
    grouped: dict[str, dict[str, FFTTrace]] = defaultdict(dict)
    for path in root.glob("fft_*.csv"):
        name = path.name
        if name.startswith("fft_low_"):
            trace = parse_fft_file(path)
            grouped[trace.freq_token]["low"] = trace
        elif name.startswith("fft_high_"):
            trace = parse_fft_file(path)
            grouped[trace.freq_token]["high"] = trace
        elif name.startswith("fft_"):
            trace = parse_fft_file(path)
            grouped[trace.freq_token]["unknown"] = trace
    return grouped


def write_trace(path: Path, rows: Sequence[tuple[float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["freq_hz", "amplitude_db"])
        writer.writerows(rows)


def summarize(
    stitched: dict[str, list[tuple[float, float]]],
    summary_path: Path,
) -> None:
    with summary_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["token", "min_freq_hz", "max_freq_hz", "points"])
        for token, rows in sorted(stitched.items()):
            if rows:
                writer.writerow([token, rows[0][0], rows[-1][0], len(rows)])
            else:
                writer.writerow([token, math.nan, math.nan, 0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Stitch low/high FFT pass CSVs.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/fft_live"),
        help="Directory containing fft_low_*.csv / fft_high_*.csv files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/fft_live/stitched"),
        help="Directory to write stitched traces.",
    )
    parser.add_argument(
        "--blend-hz",
        type=float,
        default=60.0,
        help="Frequency cutoff (Hz): <= uses low pass, > uses high pass.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Optional CSV summary path (defaults to output/fft_stitched_summary.csv).",
    )
    args = parser.parse_args()

    pairs = collect_pairs(args.input)
    cfg = StitchConfig(blend_hz=max(0.0, args.blend_hz), prefer_high=True)
    stitched: dict[str, list[tuple[float, float]]] = {}
    for token, traces in sorted(pairs.items()):
        low_trace = traces.get("low")
        high_trace = traces.get("high") or traces.get("unknown")
        combined = stitch_pair(low_trace, high_trace, cfg=cfg)
        stitched[token] = combined
        if combined:
            output_name = f"fft_{token}.csv"
            write_trace(args.output / output_name, combined)
            print(f"Stitched {token}: {len(combined)} points")
        else:
            print(f"Skipped {token}: no data available")

    summary_path = args.summary or (args.output / "fft_stitched_summary.csv")
    summarize(stitched, summary_path)
    print(f"\nSummary written to: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
