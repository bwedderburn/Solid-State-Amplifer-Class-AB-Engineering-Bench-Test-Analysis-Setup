"""LabJack U3 helper utilities.

Separates device opening and convenience wrappers from the monolithic GUI file.
USB functionality depends on Exodriver / liblabjackusb. Fail gracefully when absent.
"""
from __future__ import annotations
from .deps import HAVE_U3, _u3, U3_ERR
import time
from typing import List

__all__ = [
    'have_u3','open_u3_safely','U3_ERR',
    'u3_open','u3_read_ain','u3_set_dir','u3_set_line','u3_read_multi'
]

def have_u3():
    return HAVE_U3 and _u3 is not None

def open_u3_safely():
    if not have_u3():
        raise RuntimeError(f"LabJack U3 library unavailable: {U3_ERR}")
    return _u3.U3()


# ---- Wrappers used by extracted GUI tabs (mirroring legacy monolith helpers)
def u3_open():  # simple alias maintaining previous naming
    return open_u3_safely()

def u3_read_ain(ch: int) -> float:
    d = None
    try:
        d = u3_open()
        return float(d.getAIN(int(ch)))
    finally:
        try:
            if d: d.close()
        except Exception:
            pass

def u3_set_dir(line: str, direction: int):
    d = None
    try:
        d = u3_open()
        # Map line name to global index
        ln = line.upper()
        base = 0
        if ln.startswith('FIO'): base = 0
        elif ln.startswith('EIO'): base = 8
        elif ln.startswith('CIO'): base = 16
        idx = base + int(ln[3:])
        d.setDOState(idx, int(bool(direction)))  # setDOState also sets direction
    finally:
        try:
            if d: d.close()
        except Exception:
            pass

def u3_set_line(line: str, state: int):
    d = None
    try:
        d = u3_open()
        ln = line.upper()
        base = 0
        if ln.startswith('FIO'): base = 0
        elif ln.startswith('EIO'): base = 8
        elif ln.startswith('CIO'): base = 16
        idx = base + int(ln[3:])
        d.setDOState(idx, 1 if state else 0)
    finally:
        try:
            if d: d.close()
        except Exception:
            pass

def u3_read_multi(chs: List[int], samples: int = 1, delay_s: float = 0.0):
    out = []
    for _ in range(samples):
        row = []
        for ch in chs:
            try:
                row.append(u3_read_ain(int(ch)))
            except Exception:
                row.append(float('nan'))
        out.append(row)
        if delay_s > 0:
            time.sleep(delay_s)
    return out
