"""Example: generate a log-spaced sweep list and print it formatted.

Demonstrates programmatic use of automation.build_freq_points (same backend
as the CLI freq-gen/sweep subcommands) and optional THD calculation when
NumPy is present.
"""
from __future__ import annotations
import math
from amp_benchkit.automation import build_freq_points
from amp_benchkit.dsp import thd_fft  # dispatcher (may be stub)

try:
    import numpy as np  # optional
except Exception:  # pragma: no cover
    np = None  # type: ignore


def main():
    freqs = build_freq_points(20, 20000, points=13, mode='log')
    print("Frequencies (Hz):")
    for f in freqs:
        print(f"  {f:.6f}")
    if np is not None:
        # Synthesize a single-tone waveform and compute THD (should be ~0)
        fs = 50_000.0
        f0 = 1000.0
        n = 4096
        t = np.arange(n)/fs
        v = np.sin(2*math.pi*f0*t)
        thd, f_est, fund = thd_fft(t, v, f0=f0)
        print(
            f"Example THD single-tone ~ {thd:.6f} (f0_est={f_est:.1f}Hz, fund_amp={fund:.3f})")
    else:
        thd, f_est, fund = thd_fft([0.0, 1.0, -0.5], 48000.0)
        print(
            f"Stub THD path active (ratio={thd}, f0_est={f_est}, fund_amp={fund})")


if __name__ == '__main__':  # pragma: no cover
    main()
