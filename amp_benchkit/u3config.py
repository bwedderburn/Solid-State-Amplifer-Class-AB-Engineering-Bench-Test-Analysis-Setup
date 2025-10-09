"""LabJack U3 configuration and digital I/O helpers.

This module provides the canonical implementations for U3 I/O operations:
- Analog input reading (:func:`u3_read_ain`, :func:`u3_read_multi`)
- Digital line control (:func:`u3_set_line`, :func:`u3_set_dir`)
- Pulse generation (:func:`u3_pulse_line`)
- Device configuration (:func:`u3_autoconfigure_for_automation`)

These functions use advanced LabJack APIs (getFeedback, BitStateWrite, etc.)
with appropriate fallbacks for robustness.

For low-level device opening, see :mod:`amp_benchkit.u3util`.

Split out from unified_gui_layout for reuse and easier testing.
"""

from __future__ import annotations

import time
from contextlib import suppress

from . import deps as _deps
from .u3util import open_u3_safely as u3_open

__all__ = [
    "u3_read_ain",
    "u3_read_multi",
    "u3_set_line",
    "u3_set_dir",
    "u3_pulse_line",
    "u3_autoconfigure_for_automation",
]


def _have_u3() -> bool:
    return bool(getattr(_deps, "HAVE_U3", False) and getattr(_deps, "_u3", None))


def _u3_mod():
    return getattr(_deps, "_u3", None)


def u3_read_ain(ch=0):
    ch = int(ch)
    if ch < 0 or ch > 3:
        raise ValueError("Only AIN0–AIN3 are supported")
    d = u3_open()
    try:
        return d.getAIN(ch)
    finally:
        with suppress(Exception):
            d.close()


def u3_read_multi(ch_list, samples=1, delay_s=0.0):
    chs = [int(c) for c in ch_list if 0 <= int(c) <= 3]
    if not chs:
        chs = [0]
    d = u3_open()
    vals = []
    try:
        for _ in range(max(1, int(samples))):
            row = [d.getAIN(c) for c in chs]
            vals.append(row)
            if delay_s > 0:
                time.sleep(delay_s)
        return vals
    finally:
        with suppress(Exception):
            d.close()


def _global_index(line: str):
    line = (line or "").strip().upper()
    if not line or line == "NONE":
        return None
    try:
        idx_local = int(line[3:])
    except Exception:
        return None
    base = 0
    if line.startswith("FIO"):
        base = 0
    elif line.startswith("EIO"):
        base = 8
    elif line.startswith("CIO"):
        base = 16
    return base + idx_local


def u3_set_line(line: str, state: int):
    if not _have_u3():
        return
    lj = _u3_mod()
    if lj is None:
        return
    gi = _global_index(line)
    if gi is None:
        return
    d = u3_open()
    try:
        st = 1 if state else 0
        try:
            d.getFeedback(lj.BitStateWrite(gi, st))
        except Exception:
            with suppress(Exception):
                d.setDOState(gi, st)
    finally:
        with suppress(Exception):
            d.close()


def u3_pulse_line(line: str, width_ms: float = 5.0, level: int = 1):
    if not _have_u3():
        return
    try:
        u3_set_line(line, level)
        time.sleep(max(0.0, float(width_ms) / 1000.0))
    finally:
        u3_set_line(line, 0 if level else 1)


def u3_set_dir(line: str, direction: int):
    if not _have_u3():
        return
    lj = _u3_mod()
    if lj is None:
        return
    gi = _global_index(line)
    if gi is None:
        return
    d = u3_open()
    try:
        try:
            d.getFeedback(lj.BitDirWrite(gi, 1 if direction else 0))
        except Exception:
            # Fallback: try PortDirWrite by masking
            with suppress(Exception):
                idx_local = gi % 8
                base = gi - idx_local
                mask = 1 << idx_local
                if base == 0:
                    d.getFeedback(lj.PortDirWrite(Direction=[0, 0, 0], WriteMask=[mask, 0, 0]))
                elif base == 8:
                    d.getFeedback(lj.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, mask, 0]))
                else:
                    d.getFeedback(lj.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, 0, mask]))
    finally:
        with suppress(Exception):
            d.close()


def u3_autoconfigure_for_automation(pulse_line: str, base: str = "current"):
    if not _have_u3():
        return
    d = None
    try:
        d = u3_open()
        if isinstance(base, str) and base.lower().startswith("factory"):
            with suppress(Exception):
                d.setToFactoryDefaults()
        if isinstance(base, str) and base.lower().startswith("factory"):
            try:
                d.configIO(FIOAnalog=0x0F)
            except Exception:
                with suppress(Exception):
                    d.configU3(FIOAnalog=0x0F)
    finally:
        with suppress(Exception):
            if d:
                d.close()
    if pulse_line and pulse_line.strip().lower() != "none":
        with suppress(Exception):
            u3_set_dir(pulse_line, 1)
