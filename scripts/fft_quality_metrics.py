#!/usr/bin/env python3
"""Evaluate FFT sweep quality from the summary CSV (optionally per-trace)."""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


class SweepRow(NamedTuple):
    test_freq: float
    drive_amp: float
    bin_freq: float
    bin_value: float
    bin_width: float
    csv_name: str


@dataclass
class QualityConfig:
    freq_tol_hz: float
    ref_db: float | None
    noise_window: int


def read_summary(path: Path) -> list[SweepRow]:
    rows: list[SweepRow] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header_map: dict[str, int] | None = None
        for row in reader:
            if not row:
                continue
            key = row[0].strip().lower()
            if header_map is None:
                if key != "test_freq_hz":
                    continue  # skip notes or unrelated rows
                header_map = {name.strip().lower(): idx for idx, name in enumerate(row)}
                continue
            if header_map is None:
                continue
            csv_idx = header_map.get("csv_path")
            if csv_idx is None or csv_idx >= len(row):
                continue
            try:
                test_freq = float(row[header_map.get("test_freq_hz", 0)])
            except ValueError:
                continue
            bin_freq_idx = header_map.get("bin_freq_hz", header_map.get("top_bin_hz"))
            bin_val_idx = header_map.get("bin_value_db", header_map.get("top_bin_value"))
            drive_amp_idx = header_map.get("drive_amp_db", bin_val_idx)
            try:
                drive_amp = float(row[drive_amp_idx]) if drive_amp_idx is not None else math.nan
            except (ValueError, TypeError, IndexError):
                drive_amp = math.nan
            try:
                bin_freq = float(row[bin_freq_idx]) if bin_freq_idx is not None else math.nan
            except (ValueError, TypeError, IndexError):
                bin_freq = math.nan
            try:
                bin_value = float(row[bin_val_idx]) if bin_val_idx is not None else drive_amp
            except (ValueError, TypeError, IndexError):
                bin_value = drive_amp
            bin_width_idx = header_map.get("bin_width_hz")
            try:
                bin_width = float(row[bin_width_idx]) if bin_width_idx is not None else math.nan
            except (ValueError, TypeError, IndexError):
                bin_width = math.nan
            rows.append(
                SweepRow(
                    test_freq=test_freq,
                    drive_amp=drive_amp,
                    bin_freq=bin_freq,
                    bin_value=bin_value,
                    bin_width=bin_width,
                    csv_name=row[csv_idx],
                )
            )
    return rows


def compute_noise_floor(trace_path: Path, window: int) -> float | None:
    try:
        with trace_path.open(newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            values = [float(r[1]) for r in reader if len(r) >= 2]
    except FileNotFoundError:
        return None
    except ValueError:
        return None
    if not values:
        return None
    trimmed = sorted(values, key=abs)
    window = max(1, min(window, len(trimmed)))
    sample = trimmed[:window]
    return sum(sample) / len(sample)


def analyze(
    rows: Sequence[SweepRow],
    *,
    data_dir: Path | None,
    cfg: QualityConfig,
) -> list[str]:
    issues: list[str] = []
    freq_deltas: list[float] = []
    levels: list[float] = []
    noise_stats: list[tuple[float, float]] = []
    for row in rows:
        delta = row.bin_freq - row.test_freq
        freq_deltas.append(delta)
        levels.append(row.drive_amp)
        half_bin = row.bin_width / 2 if row.bin_width and not math.isnan(row.bin_width) else 0.0
        threshold = max(cfg.freq_tol_hz, half_bin)
        if abs(delta) > threshold:
            issues.append(
                "Freq mismatch "
                f"{row.test_freq:.2f} Hz -> bin {row.bin_freq:.2f} Hz "
                f"({delta:+.3f} Hz) [file {row.csv_name}]"
            )
        if cfg.ref_db is not None and row.drive_amp < cfg.ref_db - 6.0:
            issues.append(
                "Low amplitude "
                f"{row.drive_amp:.2f} dB at {row.test_freq:.2f} Hz "
                f"(ref {cfg.ref_db:.2f} dB)"
            )
        if data_dir is not None:
            trace_path = data_dir / row.csv_name
            noise = compute_noise_floor(trace_path, cfg.noise_window)
            if noise is not None:
                noise_stats.append((row.test_freq, noise))
                if row.drive_amp is not None and noise > row.drive_amp - 20.0:
                    issues.append(
                        f"Elevated noise floor ({noise:.2f} dB) near {row.test_freq:.2f} Hz"
                    )
    summarize_results(freq_deltas, levels, noise_stats)
    return issues


def summarize_results(
    freq_deltas: Iterable[float],
    levels: Iterable[float],
    noise_stats: Iterable[tuple[float, float]],
) -> None:
    deltas = list(freq_deltas)
    amps = list(levels)
    print("\nSweep summary:")
    if deltas:
        print(
            "  Peak frequency delta: max "
            f"{max(deltas):+.4f} Hz, min {min(deltas):+.4f} Hz, "
            f"rms {rms(deltas):.4f} Hz"
        )
    if amps:
        print(f"  Peak amplitude: max {max(amps):.3f} dB, min {min(amps):.3f} dB")
    noise_list = list(noise_stats)
    if noise_list:
        worst = max(noise_list, key=lambda item: item[1])
        print(f"  Worst noise floor: {worst[1]:.3f} dB near {worst[0]:.2f} Hz")


def rms(values: Iterable[float]) -> float:
    data = list(values)
    if not data:
        return 0.0
    return math.sqrt(sum(v * v for v in data) / len(data))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate FFT sweep quality.")
    parser.add_argument(
        "--summary",
        type=Path,
        required=True,
        help="Path to fft_sweep_summary.csv emitted by live sweep.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing per-frequency FFT CSV captures (optional).",
    )
    parser.add_argument(
        "--freq-tolerance",
        type=float,
        default=0.5,
        help="Allowed peak frequency error in Hz.",
    )
    parser.add_argument(
        "--ref-db",
        type=float,
        default=None,
        help="Reference amplitude in dB (warn if peaks fall below ref-6dB).",
    )
    parser.add_argument(
        "--noise-window",
        type=int,
        default=64,
        help="Sample size for noise-floor estimate (smallest magnitudes).",
    )
    args = parser.parse_args()

    rows = read_summary(args.summary)
    if not rows:
        print("No sweep rows found in summary.")
        return 1

    cfg = QualityConfig(
        freq_tol_hz=max(0.0, args.freq_tolerance),
        ref_db=args.ref_db,
        noise_window=max(1, args.noise_window),
    )
    issues = analyze(rows, data_dir=args.data_dir, cfg=cfg)
    if issues:
        print("\nIssues detected:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nNo issues detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
