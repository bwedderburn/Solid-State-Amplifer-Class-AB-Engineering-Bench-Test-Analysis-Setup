"""Compare THD from sweep CSV vs FFT spectrum capture."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def _load_fft(path: Path) -> tuple[list[float], list[float], str, str]:
    freqs: list[float] = []
    values: list[float] = []
    with path.open() as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                freqs.append(float(row[0]))
                values.append(float(row[1]))
            except ValueError:
                continue

    def _norm(unit: str) -> str:
        unit = unit.split("_", 1)[-1] if "_" in unit else unit
        return unit.strip().strip('"').strip().lower()

    x_unit = _norm(header[0]) if header else "hz"
    y_unit = _norm(header[1]) if header else "db"
    return freqs, values, x_unit, y_unit


def _load_thd(path: Path) -> dict[float, float]:
    rows: dict[float, float] = {}
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                freq = float(row["freq_hz"])
                thd = float(row.get("thd_percent", "nan"))
            except (KeyError, ValueError):
                continue
            rows[freq] = thd
    return rows


def _db_to_linear(value: float, scale: str) -> float:
    scale_norm = scale.lower()
    if scale_norm.startswith("db"):
        return 10 ** (value / 20.0)
    return value


def _find_band(freqs: list[float], values: list[float], target: float, window: float) -> float:
    best = float("-inf")
    for f, val in zip(freqs, values, strict=False):
        if abs(f - target) <= window and val > best:
            best = val
    if not math.isfinite(best):
        return float("nan")
    return best


def compute_fft_thd(
    freqs: list[float],
    values: list[float],
    *,
    scale: str,
    fundamental_hz: float,
    harmonics: int,
    window: float,
) -> tuple[float, list[tuple[int, float]]]:
    amps: list[tuple[int, float]] = []
    for k in range(1, harmonics + 1):
        target = k * fundamental_hz
        peak = _find_band(freqs, values, target, window)
        amps.append((k, peak))
    if not amps or not math.isfinite(amps[0][1]):
        return float("nan"), amps
    # Convert to linear amplitude
    fund = _db_to_linear(amps[0][1], scale)
    if fund <= 0:
        return float("nan"), amps
    energy = 0.0
    for _harm, value in amps[1:]:
        if not math.isfinite(value):
            continue
        amp = _db_to_linear(value, scale)
        energy += amp * amp
    thd_ratio = math.sqrt(energy) / fund
    return thd_ratio * 100.0, amps


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare THD sweep results with FFT-derived THD.")
    p.add_argument("--fft", required=True, type=Path, help="FFT CSV from fft-capture command.")
    p.add_argument("--thd", required=True, type=Path, help="THD sweep CSV (freq,thd_percent).")
    p.add_argument(
        "--fundamental",
        type=float,
        default=None,
        help="Fundamental frequency in Hz (omit to auto-detect strongest bin).",
    )
    p.add_argument(
        "--window",
        type=float,
        default=5.0,
        help="Half-width search window around each harmonic (Hz).",
    )
    p.add_argument(
        "--harmonics",
        type=int,
        default=8,
        help="Number of harmonics to include when computing FFT THD (default: 8).",
    )
    p.add_argument(
        "--auto-fundamental",
        action="store_true",
        help="Override --fundamental by auto-selecting the strongest FFT bin.",
    )
    args = p.parse_args(argv)

    freqs, values, x_unit, y_unit = _load_fft(args.fft)
    if not freqs or not values:
        print("FFT file is empty or invalid.")
        return 1
    x_unit_label = x_unit.upper()
    y_unit_label = "dB" if y_unit == "db" else y_unit
    fundamental_opt = args.fundamental

    if args.auto_fundamental or fundamental_opt is None:
        peak_idx = max(
            range(len(values)),
            key=lambda i: values[i],
        )
        fundamental_opt = freqs[peak_idx]
        print(f"Auto-detected fundamental: {fundamental_opt:.2f} {x_unit_label}")
    if fundamental_opt is None:
        print("Fundamental frequency not provided and auto-detect failed.")
        return 1
    if not math.isfinite(fundamental_opt):
        print("Fundamental frequency is not finite.")
        return 1
    fundamental = float(fundamental_opt)
    thd_rows = _load_thd(args.thd)
    fft_thd, amps = compute_fft_thd(
        freqs,
        values,
        scale=y_unit,
        fundamental_hz=fundamental,
        harmonics=max(1, args.harmonics),
        window=max(args.window, 0.5),
    )

    # Find sweep THD near the requested frequency
    best_freq_opt = min(thd_rows, key=lambda f: abs(f - fundamental), default=None)
    sweep_thd_opt = thd_rows.get(best_freq_opt) if best_freq_opt is not None else None

    print(f"FFT-derived THD: {fft_thd:.3f}% ({fundamental:.2f} Hz fundamental)")
    if sweep_thd_opt is not None and math.isfinite(sweep_thd_opt):
        delta = fft_thd - sweep_thd_opt
        print(f"Sweep THD @ {best_freq_opt:.2f} Hz: {sweep_thd_opt:.3f}% (Δ {delta:+.3f} %)")
    else:
        print("Sweep THD unavailable near fundamental.")

    print("\nHarmonic bins used (k, peak amplitude):")
    for k, value in amps:
        label = f"{value:.3f} {y_unit_label}" if math.isfinite(value) else "NaN"
        print(f"  {k:2d} × {fundamental:.2f} {x_unit_label} → {label}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
