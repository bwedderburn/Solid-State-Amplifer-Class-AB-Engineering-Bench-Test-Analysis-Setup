"""DSP / signal analysis helpers for amp_benchkit.

Functions were extracted from the legacy monolithic GUI module.
Public (provisional) API:
  vrms(v) -> float
  vpp(v) -> float
  thd_fft(t, v, f0=None, nharm=10, window='hann') -> (thd, f0_est, fund_amp)
  find_knees(freqs, amps, ref_mode='max', ref_hz=1000.0, drop_db=3.0)
      -> (f_lo, f_hi, ref_amp, ref_db)
"""

from __future__ import annotations

import numpy as np

__all__ = ["vrms", "vpp", "thd_fft", "find_knees"]


def _np_array(x):
    return x if isinstance(x, np.ndarray) else np.asarray(x)


def vrms(v):
    v = _np_array(v)
    return float(np.sqrt(np.mean(np.square(v.astype(float))))) if v.size else float("nan")


def vpp(v):
    v = _np_array(v)
    return float(np.max(v) - np.min(v)) if v.size else float("nan")


def thd_fft(t, v, f0=None, nharm=10, window="hann"):
    t = _np_array(t).astype(float)
    v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return float("nan"), float("nan"), float("nan")
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        span = t[-1] - t[0]
        dt = span / (n - 1) if span > 0 else 1e-6
    v_centered = v - np.mean(v)
    if f0 is None or f0 <= 0:
        if window == "hann":
            w = np.hanning(n)
        elif window == "hamming":
            w = np.hamming(n)
        else:
            w = np.ones(n)
        spectrum = np.fft.rfft(v_centered * w)
        freqs = np.fft.rfftfreq(n, d=dt)
        idx = int(np.argmax(np.abs(spectrum[1:])) + 1)
        f_est = float(freqs[idx])
    else:
        f_est = float(f0)

    omega = 2.0 * np.pi * f_est
    basis = np.column_stack([np.sin(omega * t), np.cos(omega * t), np.ones_like(t)])
    coeffs, *_ = np.linalg.lstsq(basis, v, rcond=None)
    sin_c, cos_c, offset = coeffs
    amp_peak = float(np.hypot(sin_c, cos_c))
    if not np.isfinite(amp_peak) or amp_peak <= 0:
        return float("nan"), f_est, float("nan")

    fundamental = sin_c * np.sin(omega * t) + cos_c * np.cos(omega * t) + offset
    residual = v - fundamental
    residual -= np.mean(residual)

    fundamental_rms = amp_peak / np.sqrt(2.0)
    harmonic_energy = 0.0
    max_harm = max(2, int(nharm))
    for k in range(2, max_harm + 1):
        omega_k = omega * k
        basis_k = np.column_stack([np.sin(omega_k * t), np.cos(omega_k * t)])
        coeffs_k, *_ = np.linalg.lstsq(basis_k, residual, rcond=None)
        amp_k = np.hypot(coeffs_k[0], coeffs_k[1])
        harmonic_energy += (amp_k / np.sqrt(2.0)) ** 2
        residual -= coeffs_k[0] * np.sin(omega_k * t) + coeffs_k[1] * np.cos(omega_k * t)

    thd_ratio = (
        float(np.sqrt(harmonic_energy) / fundamental_rms) if fundamental_rms > 0 else float("nan")
    )
    return thd_ratio, f_est, amp_peak


def find_knees(freqs, amps, ref_mode="max", ref_hz=1000.0, drop_db=3.0):
    f = _np_array(freqs).astype(float)
    a = _np_array(amps).astype(float)
    if f.size != a.size or f.size < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    idx = int(np.argmin(np.abs(f - float(ref_hz)))) if ref_mode == "freq" else int(np.argmax(a))
    ref_amp = float(a[idx]) if a[idx] > 0 else float("nan")
    if not np.isfinite(ref_amp) or ref_amp <= 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    ref_db = 20.0 * np.log10(ref_amp)
    target_db = ref_db - float(drop_db)
    adB = 20.0 * np.log10(np.maximum(a, 1e-18))
    f_lo = float("nan")
    f_hi = float("nan")
    prev_f = f[0]
    prev_db = adB[0]
    for i in range(1, idx + 1):
        cur_f = f[i]
        cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (
            prev_db <= target_db and cur_db >= target_db
        ):
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_lo = float(prev_f + frac * (cur_f - prev_f))
            else:
                f_lo = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    prev_f = f[idx]
    prev_db = adB[idx]
    for i in range(idx + 1, f.size):
        cur_f = f[i]
        cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (
            prev_db <= target_db and cur_db >= target_db
        ):
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_hi = float(prev_f + frac * (cur_f - prev_f))
            else:
                f_hi = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    return f_lo, f_hi, ref_amp, ref_db
