"""Plot THD sweep CSV files on a log-frequency chart.

Usage:

    python scripts/plot_thd_sweep.py results/thd_*Vpp_*.csv \
        --output results/thd_plot.png

Each CSV is expected to have the columns ``freq_hz`` and ``thd_percent``
as produced by ``thd-sweep`` or ``batch_thd_sweep``.  The script draws
one curve per file, labels them by basename (or ``--labels``), and saves
the figure (PNG by default).  If you provide more labels than files,
extras are ignored; if fewer, remaining curves fall back to basenames.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def load(path: Path) -> tuple[list[float], list[float]]:
    freqs: list[float] = []
    thd: list[float] = []
    with path.open() as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        if "freq_hz" not in fieldnames or "thd_percent" not in fieldnames:
            raise ValueError(f"{path} missing freq_hz/thd_percent columns")
        for row in reader:
            freqs.append(float(row["freq_hz"]))
            thd.append(float(row["thd_percent"]))
    return freqs, thd


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plot THD sweep CSV files.")
    p.add_argument("files", nargs="+", help="One or more thd_sweep CSV files.")
    p.add_argument("--labels", nargs="*", help="Optional legend labels (override basenames).")
    p.add_argument(
        "--output",
        default="thd_plot.png",
        help="Output image file (default thd_plot.png).",
    )
    p.add_argument("--title", default="THD vs Frequency", help="Figure title.")
    p.add_argument(
        "--ylim",
        nargs=2,
        type=float,
        default=None,
        help="Optional y-axis limits (percent).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    files = [Path(f) for f in args.files]
    raw_labels = args.labels
    labels = list(raw_labels) if raw_labels is not None else []

    plt.figure(figsize=(10, 6))
    for idx, path in enumerate(files):
        freqs, thd = load(path)
        label = labels[idx] if idx < len(labels) else path.stem
        plt.semilogx(freqs, thd, marker="o", markersize=3, linewidth=1.2, label=label)

    plt.grid(True, which="both", linestyle=":", linewidth=0.6)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("THD (%)")
    plt.title(args.title)
    plt.legend()
    if args.ylim:
        plt.ylim(args.ylim)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Saved plot: {output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
