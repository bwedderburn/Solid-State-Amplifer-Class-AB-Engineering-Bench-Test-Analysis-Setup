"""LabJack U3 configuration and digital I/O helpers.

Split out from unified_gui_layout for reuse and easier testing.
"""
from __future__ import annotations
import time
from .deps import HAVE_U3, _u3, INSTALL_HINTS
from .u3util import open_u3_safely as u3_open

__all__ = [
    'u3_read_ain','u3_read_multi','u3_set_line','u3_set_dir','u3_pulse_line','u3_autoconfigure_for_automation'
]

def u3_read_ain(ch=0):
    ch = int(ch)
    if ch < 0 or ch > 3:
        raise ValueError("Only AIN0–AIN3 are supported")
    d = u3_open()
    try:
        return d.getAIN(ch)
    finally:
        try: d.close()
        except Exception: pass

def u3_read_multi(ch_list, samples=1, delay_s=0.0):
    chs = [int(c) for c in ch_list if 0 <= int(c) <= 3]
    if not chs: chs = [0]
    d = u3_open(); vals = []
    try:
        for _ in range(max(1,int(samples))):
            row = [d.getAIN(c) for c in chs]; vals.append(row)
            if delay_s > 0: time.sleep(delay_s)
        return vals
    finally:
        try: d.close()
        except Exception: pass

def _global_index(line: str):
    line = (line or '').strip().upper()
    if not line or line == 'NONE':
        return None
    try:
        idx_local = int(line[3:])
    except Exception:
        return None
    base = 0
    if line.startswith('FIO'): base = 0
    elif line.startswith('EIO'): base = 8
    elif line.startswith('CIO'): base = 16
    return base + idx_local

def u3_set_line(line: str, state: int):
    if not HAVE_U3: return
    gi = _global_index(line)
    if gi is None: return
    d = u3_open()
    try:
        st = 1 if state else 0
        try:
            d.getFeedback(_u3.BitStateWrite(gi, st))
        except Exception:
            try: d.setDOState(gi, st)
            except Exception: pass
    finally:
        try: d.close()
        except Exception: pass

def u3_pulse_line(line: str, width_ms: float = 5.0, level: int = 1):
    if not HAVE_U3: return
    try:
        u3_set_line(line, level)
        time.sleep(max(0.0, float(width_ms)/1000.0))
    finally:
        u3_set_line(line, 0 if level else 1)

def u3_set_dir(line: str, direction: int):
    if not HAVE_U3: return
    gi = _global_index(line)
    if gi is None: return
    d = u3_open()
    try:
        try:
            d.getFeedback(_u3.BitDirWrite(gi, 1 if direction else 0))
        except Exception:
            # Fallback: try PortDirWrite by masking
            try:
                idx_local = gi % 8
                base = gi - idx_local
                mask = 1 << idx_local
                if base == 0:
                    d.getFeedback(_u3.PortDirWrite(Direction=[0,0,0], WriteMask=[mask,0,0]))
                elif base == 8:
                    d.getFeedback(_u3.PortDirWrite(Direction=[0,0,0], WriteMask=[0,mask,0]))
                else:
                    d.getFeedback(_u3.PortDirWrite(Direction=[0,0,0], WriteMask=[0,0,mask]))
            except Exception:
                pass
    finally:
        try: d.close()
        except Exception: pass

def u3_autoconfigure_for_automation(pulse_line: str, base: str = 'current'):
    if not HAVE_U3: return
    d=None
    try:
        d = u3_open()
        if isinstance(base, str) and base.lower().startswith('factory'):
            try: d.setToFactoryDefaults()
            except Exception: pass
        if isinstance(base, str) and base.lower().startswith('factory'):
            try: d.configIO(FIOAnalog=0x0F)
            except Exception:
                try: d.configU3(FIOAnalog=0x0F)
                except Exception: pass
    finally:
        try:
            if d: d.close()
        except Exception: pass
    try:
        if pulse_line and pulse_line.strip().lower() != 'none':
            u3_set_dir(pulse_line, 1)
    except Exception:
        pass
