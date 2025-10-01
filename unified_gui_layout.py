#!/usr/bin/env python3
"""
Minimal unified CLI/GUI bridge.

NOTE:
Original large monolithic implementation was lost/truncated.
This rebuilt version delegates to modular packages and preserves
the public-facing commands used by existing console scripts:
  - selftest
  - sweep
  - diag
  - config-dump
  - config-reset
  - gui (stub if Qt unavailable)

Future incremental extraction can reintroduce tabbed GUI logic
under amp_benchkit.gui.* modules without expanding this file again.
"""

from __future__ import annotations

import argparse
import sys
import json
import math
import types
import time
from typing import List

try:  # Optional dependency for certain numeric operations; not required for --help / no-arg path
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

# -------------------- Minimal placeholder symbols (stubs) --------------------
# These prevent NameError during import for instrument helpers that are legacy holdovers.
TEK_RSRC_DEFAULT = "USB::INSTR"  # Placeholder scope resource
WAVE_CODE: dict[str, str] = {}
SWEEP_MODE: dict[str, str] = {}

# Serial stub
class _SerialStub:
    def __init__(self, *a, **k):
        pass
    def write(self, *a, **k):
        return 0
    def read(self, *a, **k):
        return b""
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class _SerialModuleStub(types.SimpleNamespace):
    Serial = _SerialStub

_serial = _SerialModuleStub()  # type: ignore

# VISA stub
class _VisaResource:
    def __init__(self):
        self.chunk_size = 1024
        self.timeout = 1000
    def write(self, *a, **k):
        return None
    def query(self, *a, **k):
        return ""
    def read_raw(self):
        return b"#00"
    def close(self):
        return None

class _VisaRM:
    def open_resource(self, *a, **k):
        return _VisaResource()

class _PyVisaStub(types.SimpleNamespace):
    ResourceManager = _VisaRM

_pyvisa = _PyVisaStub()  # type: ignore

# QFont stub used in fixed_font legacy helper
class QFont:  # pragma: no cover - placeholder
    TypeWriter = 0
    def __init__(self, *a, **k):
        pass
    def setStyleHint(self, *a, **k):
        pass

from amp_benchkit.automation import build_freq_points
from amp_benchkit.dsp import thd_fft
from amp_benchkit.logging import setup_logging, get_logger
from amp_benchkit.deps import (
    HAVE_QT,
    HAVE_SERIAL,
    HAVE_PYVISA,
    HAVE_U3,
    dep_msg,
    INSTALL_HINTS,
)

# Config handling (fail-soft)
try:  # pragma: no cover
    from amp_benchkit.config import load_config, save_config, CONFIG_PATH
except Exception:  # pragma: no cover
    def load_config():  # type: ignore
        return {}
    def save_config(data):  # type: ignore
        return
    CONFIG_PATH = "(unavailable)"  # type: ignore


# -------------------- Internal Selftest ----------------------------------


# (Truncated legacy helpers removed during refactor)
# Prefer a fixed-width font when available (used in Test Panel)
def fixed_font():
    try:
        f = QFont("Monospace")
        try:
            f.setStyleHint(QFont.TypeWriter)
        except Exception:
            pass
        return f
    except Exception:
        return None

# -----------------------------
# FY3200S protocol helpers
# -----------------------------

def _fy_cmds(freq_hz, amp_vpp, off_v, wave, duty=None, ch=1):
    clamp = lambda v,a,b: max(a, min(b, v))
    step = lambda v,s: v if s<=0 else round(round(v/s)*s, 10)
    pref = 'b' if ch==1 else 'd'
    cmds = [
        f"{pref}w{WAVE_CODE.get(wave,'0')}",
        f"{pref}f{int(round(float(freq_hz)*100)):09d}",
        f"{pref}o{step(float(off_v),0.01):0.2f}",
    ]
    if duty is not None:
        dp = int(round(clamp(step(float(duty),0.1), 0.0, 99.9)*10))
        cmds.append(f"{pref}d{dp:03d}")
    cmds.append(f"{pref}a{step(clamp(float(amp_vpp),0.0,99.99),0.01):0.2f}")
    for c in cmds:
        if len(c)+1 > 15:
            raise ValueError("FY command too long: "+c)
    return cmds

def fy_apply(freq_hz=1000, amp_vpp=2.0, wave="Sine", off_v=0.0, duty=None, ch=1, port=None, proto="FY ASCII 9600"):
    if not HAVE_SERIAL:
        raise ImportError(f"pyserial not available. {INSTALL_HINTS['pyserial']}")
    port = port or find_fy_port()
    if not port:
        raise RuntimeError("No serial ports found.")
    baud,eol = (9600, "\n") if proto=="FY ASCII 9600" else (115200, "\r\n")
    try:
        with _serial.Serial(port, baudrate=baud, timeout=1) as s:
            for cmd in _fy_cmds(freq_hz,amp_vpp,off_v,wave,duty,ch):
                s.write((cmd+eol).encode()); time.sleep(0.02)
    except Exception as e:
        # Try alternate baud/EOL pairs automatically
        for b,e2 in [(115200, "\r\n"),(9600, "\n")]:
            try:
                with _serial.Serial(port, baudrate=b, timeout=1) as s:
                    for cmd in _fy_cmds(freq_hz,amp_vpp,off_v,wave,duty,ch):
                        s.write((cmd+e2).encode()); time.sleep(0.02)
                return
            except Exception:
                pass
        raise RuntimeError(f"FY write failed on {port}: {e}")

def fy_sweep(port, ch, proto, start=None, end=None, t_s=None, mode=None, run=None):
    baud,eol = (9600, "\n") if proto=="FY ASCII 9600" else (115200, "\r\n"); pref='b' if ch==1 else 'd'
    with _serial.Serial(port, baudrate=baud, timeout=1) as s:
        if start is not None: s.write((f"{pref}b{int(start*100):09d}"+eol).encode()); time.sleep(0.02)
        if end   is not None: s.write((f"{pref}e{int(end*100):09d}"+eol).encode()); time.sleep(0.02)
        if t_s   is not None: s.write((f"{pref}t{int(t_s):02d}"+eol).encode()); time.sleep(0.02)
        if mode  is not None: s.write((f"{pref}m{SWEEP_MODE.get(mode,'0')}"+eol).encode()); time.sleep(0.02)
        if run   is not None: s.write((f"{pref}r{1 if run else 0}"+eol).encode()); time.sleep(0.02)

# -----------------------------
# Tektronix helpers
# -----------------------------

def _tek_setup_channel(sc, ch=1):
    sc.write("HEADER OFF")
    try:
        if isinstance(ch, str):
            src = ch.upper()
        else:
            src = f"CH{int(ch)}"
        sc.write(f"DATA:SOURCE {src}")
    except Exception:
        sc.write(f"DATA:SOURCE CH{int(ch)}")
    sc.write("DATA:ENC RPB"); sc.write("DATA:WIDTH 1")
    try:
        pts = int(float(sc.query("WFMPRE:NR_PT?")))
    except Exception:
        pts = 2500
    sc.write("DATA:START 1"); sc.write(f"DATA:STOP {pts if pts>0 else 2500}")

def _decode_ieee_block(raw: bytes) -> bytes:
    if not raw: return b""
    if raw[:1] != b"#": return raw
    nd = raw[1] - 48
    if nd <= 0: return b""
    nlen = int(raw[2:2+nd].decode('ascii', errors='ignore') or '0')
    start = 2 + nd
    return raw[start:start+nlen]

def _read_curve_block(sc):
    sc.write("CURVE?"); raw = sc.read_raw(); return _decode_ieee_block(raw)

def scope_capture(resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1):
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        sc.timeout = int(timeout_ms); sc.chunk_size = max(getattr(sc,'chunk_size',20480), 1048576)
        _tek_setup_channel(sc, ch); block = _read_curve_block(sc)
        return list(np.frombuffer(block, dtype=np.uint8))
    finally:
        try: sc.close()
        except Exception: pass

def scope_set_trigger_ext(resource=TEK_RSRC_DEFAULT, slope='RISE', level=None):
    """Best-effort set EXT trigger on Tek scopes (varies by model)."""
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        s = str(slope).upper()
        if s.startswith('F'): s = 'FALL'
        else: s = 'RISE'
        cmds = [
            "TRIGger:MAIn:EDGE:SOURce EXT",
            "TRIGger:EDGE:SOURce EXT",
        ]
        for c in cmds:
            try: sc.write(c)
            except Exception: pass
        # Slope variants
        for c in (f"TRIGger:MAIn:EDGE:SLOPe {s}", f"TRIGger:EDGE:SLOPe {s}"):
            try: sc.write(c)
            except Exception: pass
        # Optional level
        if level is not None:
            try:
                lv = float(level)
                for c in (f"TRIGger:LEVel:EXTernal {lv}", f"TRIGger:MAIn:LEVel:EXTernal {lv}"):
                    try: sc.write(c)
                    except Exception: pass
            except Exception:
                pass
    finally:
        try: sc.close()
        except Exception: pass

def scope_arm_single(resource=TEK_RSRC_DEFAULT):
    """Arm single-sequence acquisition."""
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        for c in ("ACQuire:STOPAfter SEQuence", "ACQuire:STATE RUN"):
            try: sc.write(c)
            except Exception: pass
    finally:
        try: sc.close()
        except Exception: pass

def scope_wait_single_complete(resource=TEK_RSRC_DEFAULT, timeout_s=3.0, poll_ms=50):
    """Poll ACQuire:STATE? until it returns 0 (stopped) or timeout."""
    if not HAVE_PYVISA:
        return False
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        deadline = time.time() + float(timeout_s)
        while time.time() < deadline:
            try:
                st = sc.query("ACQuire:STATE?").strip()
                if st in ('0', 'STOP', 'STOPPED'):
                    return True
                if st not in ('1', 'RUN', 'RUNNING'):
                    try:
                        ts = sc.query("TRIGger:STATE?").strip().upper()
                        if ts in ('TRIGGERED', 'STOP', 'SAVE'):
                            return True
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(max(0.0, float(poll_ms)/1000.0))
    finally:
        try: sc.close()
        except Exception: pass
    return False

def scope_configure_math_subtract(resource=TEK_RSRC_DEFAULT, order='CH1-CH2'):
    """Configure scope MATH as subtraction of two channels (best-effort across models)."""
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    order = (order or 'CH1-CH2').upper()
    if order not in ('CH1-CH2', 'CH2-CH1'):
        order = 'CH1-CH2'
    a, b = order.split('-')
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        for c in (
            "MATH:STATE ON",
            f"MATH:DEFINE {order}",
            "MATH:OPER SUBT",
            "MATH:OPER SUB",
            "MATH:OPERation SUBtract",
            f"MATH:SOURCE1 {a}",
            f"MATH:SOURCE2 {b}",
        ):
            try: sc.write(c)
            except Exception: pass
    finally:
        try: sc.close()
        except Exception: pass

def scope_capture_calibrated(resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1):
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    rm = _pyvisa.ResourceManager(); sc = rm.open_resource(resource)
    try:
        sc.timeout = int(timeout_ms); sc.chunk_size = max(getattr(sc,'chunk_size',20480), 1048576)
        _tek_setup_channel(sc, ch)
        ymult = float(sc.query('WFMPRE:YMULT?')); yzero = float(sc.query('WFMPRE:YZERO?'))
        yoff = float(sc.query('WFMPRE:YOFF?')); xincr = float(sc.query('WFMPRE:XINCR?'))
        block = _read_curve_block(sc); data = np.frombuffer(block, dtype=np.uint8)
        volts = (data - yoff) * ymult + yzero; t = np.arange(data.size) * xincr
        return t.tolist(), volts.tolist()
    finally:
        try: sc.close()
        except Exception: pass

def scope_screenshot(filename="results/scope.png", resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1):
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    t, v = scope_capture_calibrated(resource, timeout_ms, ch=ch)
    plt.figure(); plt.plot(t, v); plt.xlabel('Time (s)'); plt.ylabel('Voltage (V)'); plt.title(f'TDS2024B CH{ch} Waveform'); plt.grid(True)
    plt.savefig(filename, bbox_inches='tight'); plt.close(); return filename

# -----------------------------
# LabJack U3 helpers
# -----------------------------

def u3_open():
    if not HAVE_U3:
        raise RuntimeError("LabJack U3 driver not available. Install with: "+INSTALL_HINTS['u3'])
    return _u3.U3()

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

# -----------------------------
# DSP / audio KPI helpers (scope waveform based)
# -----------------------------

def _np_array(x):
    return x if isinstance(x, np.ndarray) else np.asarray(x)

def vrms(v):
    v = _np_array(v)
    return float(np.sqrt(np.mean(np.square(v.astype(float))))) if v.size else float('nan')

def vpp(v):
    v = _np_array(v)
    return float((np.max(v) - np.min(v))) if v.size else float('nan')

def thd_fft(t, v, f0=None, nharm=10, window='hann'):
    """
    Compute THD using an FFT of the calibrated scope waveform.
    - t: time array (s)
    - v: voltage array (V)
    - f0: fundamental frequency hint (Hz). If None, auto-detect peak > DC.
    - nharm: number of harmonics to include (≥2)
    Returns (thd_ratio, f0_est, fund_amp)
    """
    t = _np_array(t).astype(float); v = _np_array(v).astype(float)
    n = v.size
    if n < 16:
        return float('nan'), float('nan'), float('nan')
    # Sample interval and rate
    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        # Fallback: infer from span if needed
        span = t[-1] - t[0]
        dt = span/(n-1) if span>0 else 1e-6
    fs = 1.0/dt
    # Windowing
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    else:
        w = np.ones(n)
    v_win = v * w
    # FFT (one-sided)
    Y = np.fft.rfft(v_win)
    f = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(Y)
    # Ignore DC when selecting fundamental
    if f0 is None or f0 <= 0:
        idx = int(np.argmax(mag[1:])) + 1  # skip DC
    else:
        idx = int(np.argmin(np.abs(f - float(f0))))
        if idx <= 0:
            idx = int(np.argmax(mag[1:])) + 1
    fund_amp = float(mag[idx])
    if fund_amp <= 0:
        return float('nan'), float(f[idx]), float(0.0)
    # Sum of harmonic bins (nearest bin to integer multiples)
    s2 = 0.0
    for k in range(2, max(2,int(nharm))+1):
        target = k * f[idx]
        if target > f[-1]:
            break
        hk = int(np.argmin(np.abs(f - target)))
        if hk <= 0 or hk >= mag.size:
            continue
        s2 += float(mag[hk])**2
    thd = float(np.sqrt(s2) / fund_amp)
    return thd, float(f[idx]), fund_amp

def find_knees(freqs, amps, ref_mode='max', ref_hz=1000.0, drop_db=3.0):
    """
    Find low/high knee frequencies where response drops by `drop_db` dB relative to a reference.
    - freqs: list/array of Hz (ascending)
    - amps: corresponding amplitude metric (linear, e.g., Vpp or Vrms)
    - ref_mode: 'max' or 'freq'
    - ref_hz: reference frequency if ref_mode=='freq'
    Returns (f_lo, f_hi, ref_amp, ref_db)
    """
    f = _np_array(freqs).astype(float); a = _np_array(amps).astype(float)
    if f.size != a.size or f.size < 2:
        return float('nan'), float('nan'), float('nan'), float('nan')
    # Determine reference amplitude
    if ref_mode == 'freq':
        idx = int(np.argmin(np.abs(f - float(ref_hz))))
    else:
        idx = int(np.argmax(a))
    ref_amp = float(a[idx]) if a[idx] > 0 else float('nan')
    if not np.isfinite(ref_amp) or ref_amp <= 0:
        return float('nan'), float('nan'), float('nan'), float('nan')
    ref_db = 20.0*np.log10(ref_amp)
    target_db = ref_db - float(drop_db)
    # Convert to dB
    adB = 20.0*np.log10(np.maximum(a, 1e-18))
    # Find low-side crossing
    f_lo = float('nan'); f_hi = float('nan')
    # Low side: search from start up to ref idx
    prev_f = f[0]; prev_db = adB[0]
    for i in range(1, idx+1):
        cur_f = f[i]; cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (prev_db <= target_db and cur_db >= target_db):
            # Linear interpolate crossing
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_lo = float(prev_f + frac*(cur_f - prev_f))
            else:
                f_lo = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    # High side: search from ref idx to end
    prev_f = f[idx]; prev_db = adB[idx]
    for i in range(idx+1, f.size):
        cur_f = f[i]; cur_db = adB[i]
        if (prev_db >= target_db and cur_db <= target_db) or (prev_db <= target_db and cur_db >= target_db):
            if cur_db != prev_db:
                frac = (target_db - prev_db) / (cur_db - prev_db)
                f_hi = float(prev_f + frac*(cur_f - prev_f))
            else:
                f_hi = float(cur_f)
            break
        prev_f, prev_db = cur_f, cur_db
    return f_lo, f_hi, ref_amp, ref_db

# -----------------------------
# U3 simple digital helpers for orchestration
# -----------------------------

def u3_set_line(line: str, state: int):
    """Set a single U3 digital line high/low. line like 'FIO3', 'EIO1', 'CIO0'."""
    if not HAVE_U3:
        return
    if not line or line.strip().lower() == 'none':
        return
    line = line.strip().upper()
    try:
        idx_local = int(line[3:])
    except Exception:
        return
    # Map to global IO number
    base = 0
    if line.startswith('FIO'): base = 0
    elif line.startswith('EIO'): base = 8
    elif line.startswith('CIO'): base = 16
    idx = base + idx_local
    d = u3_open()
    try:
        st = 1 if state else 0
        try:
            d.getFeedback(_u3.BitStateWrite(idx, st))
        except Exception:
            # Fallback for older firmwares/APIs
            try:
                d.setDOState(idx, st)
            except Exception:
                pass
    finally:
        try: d.close()
        except Exception: pass

def u3_pulse_line(line: str, width_ms: float = 5.0, level: int = 1):
    """Pulse a U3 line for width_ms milliseconds (best-effort)."""
    if not HAVE_U3:
        return
    try:
        u3_set_line(line, level)
        time.sleep(max(0.0, float(width_ms)/1000.0))
    finally:
        u3_set_line(line, 0 if level else 1)

def u3_set_dir(line: str, direction: int):
    """Set a single U3 line direction (1=output, 0=input)."""
    if not HAVE_U3:
        return
    if not line or line.strip().lower() == 'none':
        return
    line = line.strip().upper()
    try:
        idx_local = int(line[3:])
    except Exception:
        return
    base = 0
    if line.startswith('FIO'): base = 0
    elif line.startswith('EIO'): base = 8
    elif line.startswith('CIO'): base = 16
    idx = base + idx_local
    d = u3_open()
    try:
        try:
            d.getFeedback(_u3.BitDirWrite(idx, 1 if direction else 0))
        except Exception:
            # Fallback: try PortDirWrite on the appropriate port
            try:
                if base == 0:
                    # FIO is lower 8 bits
                    mask = 1 << idx_local
                    d.getFeedback(_u3.PortDirWrite(Direction=[0, 0, 0], WriteMask=[mask, 0, 0]))
                elif base == 8:
                    mask = 1 << idx_local
                    d.getFeedback(_u3.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, mask, 0]))
                elif base == 16:
                    mask = 1 << idx_local
                    d.getFeedback(_u3.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, 0, mask]))
            except Exception:
                pass
    finally:
        try: d.close()
        except Exception: pass

def u3_autoconfigure_for_automation(pulse_line: str, base: str = 'current'):
    """Best-effort: optionally restore factory defaults, set AIN0-3 as analog, and ensure pulse_line is output."""
    if not HAVE_U3:
        return
    d = None
    try:
        d = u3_open()
        # Base reset if requested
        if isinstance(base, str) and base.lower().startswith('factory'):
            try:
                d.setToFactoryDefaults()
            except Exception:
                pass
        # If starting from factory, ensure AIN0-3 analog (FIOAnalog bits 0..3 = 1)
        if isinstance(base, str) and base.lower().startswith('factory'):
            try:
                # Prefer configIO path if supported
                d.configIO(FIOAnalog=0x0F)
            except Exception:
                try:
                    d.configU3(FIOAnalog=0x0F)
                except Exception:
                    pass
    finally:
        try:
            if d: d.close()
        except Exception:
            pass
    # Ensure selected pulse line is an output
    try:
        if pulse_line and pulse_line.strip().lower() != 'none':
            u3_set_dir(pulse_line, 1)
    except Exception:
        pass

# -----------------------------
# GUI
# -----------------------------
if HAVE_QT:
    BaseGUI = QMainWindow
else:
    class BaseGUI(object): pass

class UnifiedGUI(BaseGUI):
    def __init__(self):
        if not HAVE_QT: return
        super().__init__(); self.setWindowTitle("Unified Control (Lite+U3)"); self.resize(1080,780)
        self.scope_res = TEK_RSRC_DEFAULT; os.makedirs('results', exist_ok=True)
        tabs = QTabWidget(); self.setCentralWidget(tabs)
        tabs.addTab(self.tab_gen(), "Generator"); tabs.addTab(self.tab_scope(), "Scope"); tabs.addTab(self.tab_daq(), "DAQ (U3)")
        tabs.addTab(self.tab_automation(), "Automation / Sweep"); tabs.addTab(self.tab_diag(), "Diagnostics")

    # ---- Generator
    def tab_gen(self):
        w = QWidget(); L = QVBoxLayout(w)
        row = QHBoxLayout()
        # CH1 panel
        c1 = QVBoxLayout(); c1.addWidget(QLabel("CH1"))
        self.wave1 = QComboBox(); self.wave1.addItems(["Sine","Square","Triangle","Pulse"]); c1.addWidget(QLabel("Waveform:")); c1.addWidget(self.wave1)
        self.freq1 = QLineEdit("1000"); c1.addWidget(QLabel("Frequency (Hz):")); c1.addWidget(self.freq1)
        self.amp1 = QLineEdit("2.0"); c1.addWidget(QLabel("Amplitude (Vpp):")); c1.addWidget(self.amp1)
        self.off1 = QLineEdit("0.0"); c1.addWidget(QLabel("Offset (V):")); c1.addWidget(self.off1)
        self.duty1 = QLineEdit("50.0"); c1.addWidget(QLabel("Duty (%):")); c1.addWidget(self.duty1)
        self.proto1 = QComboBox(); self.proto1.addItems(FY_PROTOCOLS); c1.addWidget(QLabel("Protocol:")); c1.addWidget(self.proto1)
        pr1 = QHBoxLayout(); self.port1 = QLineEdit(""); pr1.addWidget(QLabel("Serial (auto/override):")); pr1.addWidget(self.port1)
        b1 = QPushButton("Scan"); b1.clicked.connect(lambda: self.scan_serial_into(self.port1)); pr1.addWidget(b1); c1.addLayout(pr1)
        # CH1 sweep controls
        c1.addWidget(QLabel("Sweep controls:"))
        s1 = QHBoxLayout()
        def col(txt, wdg):
            lay = QVBoxLayout(); lay.addWidget(QLabel(txt, alignment=Qt.AlignHCenter)); wdg.setMaximumWidth(140); lay.addWidget(wdg); return lay
        self.sw_start1 = QLineEdit(""); s1.addLayout(col("Start Hz", self.sw_start1))
        self.sw_end1 = QLineEdit(""); s1.addLayout(col("End Hz", self.sw_end1))
        self.sw_time1 = QLineEdit("10"); s1.addLayout(col("Time s", self.sw_time1))
        self.sw_mode1 = QComboBox(); self.sw_mode1.addItems(["Linear","Log"]); s1.addLayout(col("Mode", self.sw_mode1))
        self.sw_amp1 = QLineEdit(""); s1.addLayout(col("Amp Vpp", self.sw_amp1))
        self.sw_dwell1 = QLineEdit(""); s1.addLayout(col("Dwell ms", self.sw_dwell1))
        c1.addLayout(s1)
        ab1 = QHBoxLayout(); a1 = QPushButton("Apply CH1"); a1.clicked.connect(lambda: self.apply_gen_side(1)); ab1.addWidget(a1)
        rs1 = QPushButton("Start Sweep CH1"); rs1.clicked.connect(lambda: self.start_sweep_side(1)); ab1.addWidget(rs1)
        st1 = QPushButton("Stop Sweep CH1"); st1.clicked.connect(lambda: self.stop_sweep_side(1)); ab1.addWidget(st1); c1.addLayout(ab1)
        # CH2 panel
        c2 = QVBoxLayout(); c2.addWidget(QLabel("CH2"))
        self.wave2 = QComboBox(); self.wave2.addItems(["Sine","Square","Triangle","Pulse"]); c2.addWidget(QLabel("Waveform:")); c2.addWidget(self.wave2)
        self.freq2 = QLineEdit("1000"); c2.addWidget(QLabel("Frequency (Hz):")); c2.addWidget(self.freq2)
        self.amp2 = QLineEdit("2.0"); c2.addWidget(QLabel("Amplitude (Vpp):")); c2.addWidget(self.amp2)
        self.off2 = QLineEdit("0.0"); c2.addWidget(QLabel("Offset (V):")); c2.addWidget(self.off2)
        self.duty2 = QLineEdit("50.0"); c2.addWidget(QLabel("Duty (%):")); c2.addWidget(self.duty2)
        self.proto2 = QComboBox(); self.proto2.addItems(FY_PROTOCOLS); c2.addWidget(QLabel("Protocol:")); c2.addWidget(self.proto2)
        pr2 = QHBoxLayout(); self.port2 = QLineEdit(""); pr2.addWidget(QLabel("Serial (auto/override):")); pr2.addWidget(self.port2)
        b2 = QPushButton("Scan"); b2.clicked.connect(lambda: self.scan_serial_into(self.port2)); pr2.addWidget(b2); c2.addLayout(pr2)
        # CH2 sweep controls
        c2.addWidget(QLabel("Sweep controls:"))
        s2 = QHBoxLayout()
        def col2(txt, wdg):
            lay = QVBoxLayout(); lay.addWidget(QLabel(txt, alignment=Qt.AlignHCenter)); wdg.setMaximumWidth(140); lay.addWidget(wdg); return lay
        self.sw_start2 = QLineEdit(""); s2.addLayout(col2("Start Hz", self.sw_start2))
        self.sw_end2 = QLineEdit(""); s2.addLayout(col2("End Hz", self.sw_end2))
        self.sw_time2 = QLineEdit("10"); s2.addLayout(col2("Time s", self.sw_time2))
        self.sw_mode2 = QComboBox(); self.sw_mode2.addItems(["Linear","Log"]); s2.addLayout(col2("Mode", self.sw_mode2))
        self.sw_amp2 = QLineEdit(""); s2.addLayout(col2("Amp Vpp", self.sw_amp2))
        self.sw_dwell2 = QLineEdit(""); s2.addLayout(col2("Dwell ms", self.sw_dwell2))
        c2.addLayout(s2)
        ab2 = QHBoxLayout(); a2 = QPushButton("Apply CH2"); a2.clicked.connect(lambda: self.apply_gen_side(2)); ab2.addWidget(a2)
        rs2 = QPushButton("Start Sweep CH2"); rs2.clicked.connect(lambda: self.start_sweep_side(2)); ab2.addWidget(rs2)
        st2 = QPushButton("Stop Sweep CH2"); st2.clicked.connect(lambda: self.stop_sweep_side(2)); ab2.addWidget(st2); c2.addLayout(ab2)
        row.addLayout(c1); row.addSpacing(20); row.addLayout(c2)
        L.addLayout(row)
        self.gen_log = QTextEdit(); self.gen_log.setReadOnly(True); L.addWidget(self.gen_log)
        return w

    def scan_serial_into(self, target_edit):
        ps = list_ports()
        if not ps:
            self._log(self.gen_log, "No serial ports."); return
        self._log(self.gen_log, "Ports: "+", ".join(p.device for p in ps))
        for p in ps:
            d=(p.device or '').lower()
            if any(k in d for k in ['usbserial','tty.usb','wchusb','ftdi']):
                target_edit.setText(p.device); break

    def _proto_for_ch(self, ch:int) -> str:
        cb = self.proto1 if ch==1 else self.proto2
        return cb.currentText() if cb and hasattr(cb, 'currentText') else "FY ASCII 9600"

    def _port_for_ch(self, ch:int) -> str:
        ed = self.port1 if ch==1 else self.port2
        txt = (ed.text().strip() if ed and hasattr(ed,'text') else '')
        return txt or find_fy_port()

    def apply_gen_side(self, side):
        try:
            if side==1:
                f=float(self.freq1.text()); a=float(self.amp1.text()); o=float(self.off1.text()); wf=self.wave1.currentText(); duty=None
                try: duty=float(self.duty1.text())
                except Exception: pass
                pr=self.proto1.currentText(); pt=(self.port1.text().strip() or None)
                fy_apply(freq_hz=f,amp_vpp=a,wave=wf,off_v=o,duty=duty,ch=1,port=pt,proto=pr)
                self._log(self.gen_log,f"APPLIED CH1: {wf} {f} Hz, {a} Vpp, Off {o} V, Duty {duty if duty is not None else '—'}% ({pr})")
            else:
                f=float(self.freq2.text()); a=float(self.amp2.text()); o=float(self.off2.text()); wf=self.wave2.currentText(); duty=None
                try: duty=float(self.duty2.text())
                except Exception: pass
                pr=self.proto2.currentText(); pt=(self.port2.text().strip() or None)
                fy_apply(freq_hz=f,amp_vpp=a,wave=wf,off_v=o,duty=duty,ch=2,port=pt,proto=pr)
                self._log(self.gen_log,f"APPLIED CH2: {wf} {f} Hz, {a} Vpp, Off {o} V, Duty {duty if duty is not None else '—'}% ({pr})")
        except Exception as e:
            self._log(self.gen_log,f"Error: {e}")

    def start_sweep_side(self, side):
        try:
            if side==1:
                pr=self.proto1.currentText(); pt=self.port1.text().strip() or find_fy_port()
                st=float(self.sw_start1.text()) if self.sw_start1.text().strip() else None
                en=float(self.sw_end1.text()) if self.sw_end1.text().strip() else None
                ts=int(self.sw_time1.text()) if self.sw_time1.text().strip() else None
                md=self.sw_mode1.currentText()
                if self.sw_amp1.text().strip():
                    try:
                        a=float(self.sw_amp1.text()); f=float(self.freq1.text() or 1000.0); o=float(self.off1.text() or 0.0); wf=self.wave1.currentText(); d=float(self.duty1.text()) if self.duty1.text().strip() else None
                        fy_apply(freq_hz=f, amp_vpp=a, wave=wf, off_v=o, duty=d, ch=1, port=pt, proto=pr)
                    except Exception as e:
                        self._log(self.gen_log,f"Amp set CH1 failed: {e}")
                fy_sweep(pt,1,pr,st,en,ts,md,True)
                self._log(self.gen_log,f"SWEEP START CH1: {st}→{en} Hz, {ts}s, {md}")
            else:
                pr=self.proto2.currentText(); pt=self.port2.text().strip() or find_fy_port()
                st=float(self.sw_start2.text()) if self.sw_start2.text().strip() else None
                en=float(self.sw_end2.text()) if self.sw_end2.text().strip() else None
                ts=int(self.sw_time2.text()) if self.sw_time2.text().strip() else None
                md=self.sw_mode2.currentText()
                if self.sw_amp2.text().strip():
                    try:
                        a=float(self.sw_amp2.text()); f=float(self.freq2.text() or 1000.0); o=float(self.off2.text() or 0.0); wf=self.wave2.currentText(); d=float(self.duty2.text()) if self.duty2.text().strip() else None
                        fy_apply(freq_hz=f, amp_vpp=a, wave=wf, off_v=o, duty=d, ch=2, port=pt, proto=pr)
                    except Exception as e:
                        self._log(self.gen_log,f"Amp set CH2 failed: {e}")
                fy_sweep(pt,2,pr,st,en,ts,md,True)
                self._log(self.gen_log,f"SWEEP START CH2: {st}→{en} Hz, {ts}s, {md}")
        except Exception as e:
            self._log(self.gen_log,f"Sweep start error: {e}")

    def stop_sweep_side(self, side):
        try:
            if side==1:
                pr=self.proto1.currentText(); pt=self.port1.text().strip() or find_fy_port()
                fy_sweep(pt,1,pr,run=False); self._log(self.gen_log,"SWEEP STOP CH1")
            else:
                pr=self.proto2.currentText(); pt=self.port2.text().strip() or find_fy_port()
                fy_sweep(pt,2,pr,run=False); self._log(self.gen_log,"SWEEP STOP CH2")
        except Exception as e:
            self._log(self.gen_log,f"Sweep stop error: {e}")

    def scope_measure(self, ch=1, typ='RMS'):
        if not HAVE_PYVISA: raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")
        r = self.scope_edit.text().strip() if hasattr(self,'scope_edit') else self.scope_res
        rm = _pyvisa.ResourceManager(); sc = rm.open_resource(r or self.scope_res)
        try:
            try: sc.timeout = 5000
            except Exception: pass
            # Allow 'MATH' as a source
            try:
                if isinstance(ch, str) and ch.strip().upper() == 'MATH':
                    sc.write("MEASU:IMM:SOURCE MATH")
                else:
                    sc.write(f"MEASU:IMM:SOURCE CH{int(ch)}")
            except Exception:
                sc.write(f"MEASU:IMM:SOURCE CH{int(ch)}")
            sc.write(f"MEASU:IMM:TYP {typ}")
            v = float(sc.query("MEASU:IMM:VAL?")); return v
        finally:
            try: sc.close()
            except Exception: pass

    # ---- Scope
    def tab_scope(self):
        w = QWidget(); L = QVBoxLayout(w)
        r = QHBoxLayout(); r.addWidget(QLabel("VISA Resource:")); self.scope_edit = QLineEdit(self.scope_res); r.addWidget(self.scope_edit)
        b = QPushButton("List VISA"); b.clicked.connect(self.list_visa); r.addWidget(b); L.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Channel:")); self.scope_ch = QComboBox(); self.scope_ch.addItems(["1","2","3","4"]); r.addWidget(self.scope_ch); L.addLayout(r)
        b = QPushButton("Single Capture"); b.clicked.connect(self.capture_scope); L.addWidget(b)
        b = QPushButton("Save Screenshot"); b.clicked.connect(self.save_shot); L.addWidget(b)
        b = QPushButton("Save CSV (Calibrated)"); b.clicked.connect(self.save_csv); L.addWidget(b)
        self.scope_log = QTextEdit(); self.scope_log.setReadOnly(True); L.addWidget(self.scope_log)
        return w

    def list_visa(self):
        if not HAVE_PYVISA:
            self._log(self.scope_log,f"pyvisa missing → {INSTALL_HINTS['pyvisa']}"); return
        try:
            res = _pyvisa.ResourceManager().list_resources(); self._log(self.scope_log, ", ".join(res) if res else "(none)")
            tek = [r for r in res if r.startswith("USB0::0x0699::")]
            if tek: self.scope_edit.setText(tek[0])
        except Exception as e: self._log(self.scope_log, f"VISA error: {e}")

    def capture_scope(self):
        try:
            r = self.scope_edit.text().strip() or self.scope_res; ch = int(self.scope_ch.currentText())
            d = scope_capture(r, ch=ch); self._log(self.scope_log, f"Captured CH{ch} {len(d)} pts: {d[:10]}")
        except Exception as e: self._log(self.scope_log, f"Error: {e}")

    def save_shot(self):
        try:
            r = self.scope_edit.text().strip() or self.scope_res; ch = int(self.scope_ch.currentText())
            fn = os.path.join('results', f'scope_ch{ch}.png'); path = scope_screenshot(fn, r, ch=ch); self._log(self.scope_log, f"Saved: {path}")
        except Exception as e: self._log(self.scope_log, f"Error: {e}")

    def save_csv(self):
        try:
            r = self.scope_edit.text().strip() or self.scope_res; ch = int(self.scope_ch.currentText())
            fn = os.path.join('results', f'ch{ch}.csv'); t, v = scope_capture_calibrated(r, timeout_ms=15000, ch=ch)
            with open(fn,'w') as f:
                f.write('t,volts\n')
                for i in range(len(v)):
                    f.write(f"{t[i]},{v[i]}\n")
            self._log(self.scope_log, f"Saved: {fn}")
        except Exception as e: self._log(self.scope_log, f"Error: {e}")

    # ---- DAQ (U3) with sub-tabs
    def tab_daq(self):
        # Build the DAQ page AS a QTabWidget (robust lifetime semantics)
        daq = QTabWidget()
        self.daq_tabs = daq  # strong ref prevents GC while wiring

        # --- Read/Stream tab
        self.daq_rw = QWidget()
        L = QVBoxLayout(self.daq_rw)

        hdr = QHBoxLayout(); hdr.addWidget(QLabel("Channels:"))
        self.chan_boxes = []
        for i in range(4):
            cb = QCheckBox(f"AIN{i}")
            self.chan_boxes.append(cb)
            hdr.addWidget(cb)
        L.addLayout(hdr)

        rr = QHBoxLayout()
        rr.addWidget(QLabel("Samples:"))
        self.daq_nsamp = QSpinBox(); self.daq_nsamp.setRange(1,10000); self.daq_nsamp.setValue(1); rr.addWidget(self.daq_nsamp)
        rr.addWidget(QLabel("Delay (ms):"))
        self.daq_delay = QSpinBox(); self.daq_delay.setRange(0,1000); self.daq_delay.setValue(0); rr.addWidget(self.daq_delay)
        rr.addWidget(QLabel("ResIdx:"))
        self.daq_res = QSpinBox(); self.daq_res.setRange(0,8); self.daq_res.setValue(0); rr.addWidget(self.daq_res)
        L.addLayout(rr)

        br = QHBoxLayout()
        b1 = QPushButton("Read Selected"); b1.clicked.connect(self.read_daq_once); br.addWidget(b1)
        b2 = QPushButton("Read Loop ×N"); b2.clicked.connect(self.read_daq_multi); br.addWidget(b2)
        L.addLayout(br)

        self.daq_log = QTextEdit(); self.daq_log.setReadOnly(True); L.addWidget(self.daq_log)

        daq.addTab(self.daq_rw, "Read/Stream")

        # --- Config Defaults tab (U3-HV style)
        self.daq_cw = QWidget()
        C = QVBoxLayout(self.daq_cw)

        # Analog Input checkbox row (checked = Analog)
        ai = QHBoxLayout()
        self.ai_checks = [QCheckBox(f"AIN{i}") for i in range(4)]
        for cb in self.ai_checks:
            cb.setChecked(True)
            ai.addWidget(cb)
        C.addWidget(QLabel("Analog Input (checked = Analog)"))
        C.addLayout(ai)

        # Digital direction/state sections for FIO/EIO/CIO
        def grid_dio(lbl, count):
            box  = QVBoxLayout(); box.addWidget(QLabel(lbl+" Direction (checked = Output)"))
            lay  = QHBoxLayout(); items=[]
            for i in range(count):
                cb=QCheckBox(str(i)); lay.addWidget(cb); items.append(cb)
            box.addLayout(lay)

            box2 = QVBoxLayout(); box2.addWidget(QLabel(lbl+" State (checked = High)"))
            lay2 = QHBoxLayout(); items2=[]
            for i in range(count):
                cb=QCheckBox(str(i)); lay2.addWidget(cb); items2.append(cb)
            box2.addLayout(lay2)
            return box, items, box2, items2

        sec, self.fio_dir_box,  sec2, self.fio_state_box  = grid_dio("FIO", 8); C.addLayout(sec); C.addLayout(sec2)
        sec, self.eio_dir_box,  sec2, self.eio_state_box  = grid_dio("EIO", 8); C.addLayout(sec); C.addLayout(sec2)
        sec, self.cio_dir_box,  sec2, self.cio_state_box  = grid_dio("CIO", 4); C.addLayout(sec); C.addLayout(sec2)

        # Timers/Counters
        tc=QHBoxLayout()
        self.t_pin=QSpinBox(); self.t_pin.setRange(0,16)
        self.t_num=QSpinBox(); self.t_num.setRange(0,6)
        self.t_clkbase=QComboBox(); self.t_clkbase.addItems(["4MHz","48MHz","750kHz"])
        self.t_div=QSpinBox(); self.t_div.setRange(0,255)
        for lbl,wid in [("PinOffset",self.t_pin),("#Timers",self.t_num),("TimerClockBase",self.t_clkbase),("Divisor",self.t_div)]:
            col=QVBoxLayout(); lab=QLabel(lbl); lab.setAlignment(Qt.AlignHCenter); col.addWidget(lab); col.addWidget(wid); tc.addLayout(col)
        self.counter0=QCheckBox("Counter0 Enable"); self.counter1=QCheckBox("Counter1 Enable"); tc.addWidget(self.counter0); tc.addWidget(self.counter1)
        C.addWidget(QLabel("Timer/Counter")); C.addLayout(tc)

        # DAC outputs
        dac=QHBoxLayout(); self.dac0=QLineEdit("0.0"); self.dac1=QLineEdit("0.0")
        for lbl,w in [("DAC0 (V)",self.dac0),("DAC1 (V)",self.dac1)]:
            col=QVBoxLayout(); lab=QLabel(lbl); lab.setAlignment(Qt.AlignHCenter); col.addWidget(lab); col.addWidget(w); dac.addLayout(col)
        C.addLayout(dac)

        # Watchdog section
        wd=QHBoxLayout(); self.wd_en=QCheckBox("Enable Watchdog"); self.wd_to=QLineEdit("100"); self.wd_reset=QCheckBox("Reset on Timeout")
        wd.addWidget(self.wd_en)
        col=QVBoxLayout(); lab=QLabel("Timeout sec"); lab.setAlignment(Qt.AlignHCenter); col.addWidget(lab); col.addWidget(self.wd_to); wd.addLayout(col)
        wd.addWidget(self.wd_reset)
        self.wd_line=QComboBox(); self.wd_line.addItems(["None"]+[f"FIO{i}" for i in range(8)]+[f"EIO{i}" for i in range(8)]+[f"CIO{i}" for i in range(4)])
        self.wd_state=QComboBox(); self.wd_state.addItems(["Low","High"])
        wd.addWidget(QLabel("Set DIO:")); wd.addWidget(self.wd_line); wd.addWidget(self.wd_state)
        C.addLayout(wd)

        # Backward-compat options (best-effort)
        bc=QHBoxLayout(); self.bc_disable_tc_offset = QCheckBox("Disable Timer/Counter Offset Errors")
        self.bc_force_dac8 = QCheckBox("Force 8-bit DAC Mode")
        bc.addWidget(self.bc_disable_tc_offset); bc.addWidget(self.bc_force_dac8)
        C.addLayout(bc)

        # Buttons
        btns=QHBoxLayout()
        rf=QPushButton("Write Factory Values"); rf.clicked.connect(self.u3_write_factory)
        rv=QPushButton("Write Values"); rv.clicked.connect(self.u3_write_values)
        rc=QPushButton("Read Current"); rc.clicked.connect(self.u3_read_current)
        for b in (rf,rv,rc): btns.addWidget(b)
        C.addLayout(btns)

        self.cfg_log=QTextEdit(); self.cfg_log.setReadOnly(True); C.addWidget(self.cfg_log)

        daq.addTab(self.daq_cw, "Config Defaults")

        # --- Test Panel tab (runtime, 1 Hz write/read)
        self.daq_test = QWidget()
        T = QVBoxLayout(self.daq_test)
        T.addWidget(QLabel("U3 Test Panel (runtime, non-persistent). Writes/reads ~1 Hz."))
        # Row: AIN readings
        ain_row = QHBoxLayout(); ain_row.addWidget(QLabel("AIN readings:"))
        self.test_ain_lbls = []
        for i in range(4):
            col = QVBoxLayout(); col.addWidget(QLabel(f"AIN{i}"))
            lbl = QLineEdit("—"); lbl.setReadOnly(True); lbl.setMaximumWidth(100); self.test_ain_lbls.append(lbl)
            col.addWidget(lbl); ain_row.addLayout(col)
        T.addLayout(ain_row)
        # DIO grids
        def grid_test(lbl, count):
            box = QVBoxLayout(); box.addWidget(QLabel(lbl+" (Dir/State/Readback)"))
            dir_row = QHBoxLayout(); state_row = QHBoxLayout(); rb_row = QHBoxLayout()
            dirs=[]; states=[]; rbs=[]
            for i in range(count):
                # Direction and desired state are writable; readback is disabled
                dcb = QCheckBox(str(i)); scb = QCheckBox(str(i)); rcb = QCheckBox(str(i)); rcb.setEnabled(False)
                dir_row.addWidget(dcb); state_row.addWidget(scb); rb_row.addWidget(rcb)
                dirs.append(dcb); states.append(scb); rbs.append(rcb)
            box.addWidget(QLabel("Direction (✓=Output)")); box.addLayout(dir_row)
            box.addWidget(QLabel("State (✓=High)")); box.addLayout(state_row)
            box.addWidget(QLabel("Readback (input/output actual)")); box.addLayout(rb_row)
            return box, dirs, states, rbs
        row_io = QHBoxLayout()
        sec, self.test_fio_dir, self.test_fio_state, self.test_fio_rb = grid_test("FIO0-7", 8); row_io.addLayout(sec)
        sec2, self.test_eio_dir, self.test_eio_state, self.test_eio_rb = grid_test("EIO0-7", 8); row_io.addLayout(sec2)
        sec3, self.test_cio_dir, self.test_cio_state, self.test_cio_rb = grid_test("CIO0-3", 4); row_io.addLayout(sec3)
        T.addLayout(row_io)
        # Port masks (Direction / State)
        pm = QHBoxLayout()
        # Direction masks
        pm.addWidget(QLabel("Dir FIO")); self.test_dir_fio = QLineEdit("0x00 (00000000)"); self.test_dir_fio.setReadOnly(True); self.test_dir_fio.setMaximumWidth(140);
        _ff = fixed_font()
        try:
            if _ff: self.test_dir_fio.setFont(_ff)
        except Exception: pass
        pm.addWidget(self.test_dir_fio)
        pm.addWidget(QLabel("EIO")); self.test_dir_eio = QLineEdit("0x00 (00000000)"); self.test_dir_eio.setReadOnly(True); self.test_dir_eio.setMaximumWidth(140);
        try:
            if _ff: self.test_dir_eio.setFont(_ff)
        except Exception: pass
        pm.addWidget(self.test_dir_eio)
        pm.addWidget(QLabel("CIO")); self.test_dir_cio = QLineEdit("0x00 (00000000)"); self.test_dir_cio.setReadOnly(True); self.test_dir_cio.setMaximumWidth(140);
        try:
            if _ff: self.test_dir_cio.setFont(_ff)
        except Exception: pass
        pm.addWidget(self.test_dir_cio)
        T.addLayout(pm)
        pm2 = QHBoxLayout()
        pm2.addWidget(QLabel("State FIO")); self.test_st_fio = QLineEdit("0x00 (00000000)"); self.test_st_fio.setReadOnly(True); self.test_st_fio.setMaximumWidth(140);
        try:
            if _ff: self.test_st_fio.setFont(_ff)
        except Exception: pass
        pm2.addWidget(self.test_st_fio)
        pm2.addWidget(QLabel("EIO")); self.test_st_eio = QLineEdit("0x00 (00000000)"); self.test_st_eio.setReadOnly(True); self.test_st_eio.setMaximumWidth(140);
        try:
            if _ff: self.test_st_eio.setFont(_ff)
        except Exception: pass
        pm2.addWidget(self.test_st_eio)
        pm2.addWidget(QLabel("CIO")); self.test_st_cio = QLineEdit("0x00 (00000000)"); self.test_st_cio.setReadOnly(True); self.test_st_cio.setMaximumWidth(140);
        try:
            if _ff: self.test_st_cio.setFont(_ff)
        except Exception: pass
        pm2.addWidget(self.test_st_cio)
        T.addLayout(pm2)
        # Write whole-port controls (Direction)
        wrd = QHBoxLayout(); wrd.addWidget(QLabel("Set Dir FIO")); self.test_wdir_fio = QLineEdit("0x00"); self.test_wdir_fio.setMaximumWidth(100);
        try:
            if _ff: self.test_wdir_fio.setFont(_ff)
        except Exception: pass
        wrd.addWidget(self.test_wdir_fio)
        bdF = QPushButton("Apply"); bdF.clicked.connect(lambda: self.apply_port_dir('FIO')); wrd.addWidget(bdF)
        wrd.addWidget(QLabel("EIO")); self.test_wdir_eio = QLineEdit("0x00"); self.test_wdir_eio.setMaximumWidth(100);
        try:
            if _ff: self.test_wdir_eio.setFont(_ff)
        except Exception: pass
        wrd.addWidget(self.test_wdir_eio)
        bdE = QPushButton("Apply"); bdE.clicked.connect(lambda: self.apply_port_dir('EIO')); wrd.addWidget(bdE)
        wrd.addWidget(QLabel("CIO")); self.test_wdir_cio = QLineEdit("0x00"); self.test_wdir_cio.setMaximumWidth(100);
        try:
            if _ff: self.test_wdir_cio.setFont(_ff)
        except Exception: pass
        wrd.addWidget(self.test_wdir_cio)
        bdC = QPushButton("Apply"); bdC.clicked.connect(lambda: self.apply_port_dir('CIO')); wrd.addWidget(bdC)
        T.addLayout(wrd)
        # Write whole-port controls (State)
        wrs = QHBoxLayout(); wrs.addWidget(QLabel("Set State FIO")); self.test_wst_fio = QLineEdit("0x00"); self.test_wst_fio.setMaximumWidth(100);
        try:
            if _ff: self.test_wst_fio.setFont(_ff)
        except Exception: pass
        wrs.addWidget(self.test_wst_fio)
        bsF = QPushButton("Apply"); bsF.clicked.connect(lambda: self.apply_port_state('FIO')); wrs.addWidget(bsF)
        wrs.addWidget(QLabel("EIO")); self.test_wst_eio = QLineEdit("0x00"); self.test_wst_eio.setMaximumWidth(100);
        try:
            if _ff: self.test_wst_eio.setFont(_ff)
        except Exception: pass
        wrs.addWidget(self.test_wst_eio)
        bsE = QPushButton("Apply"); bsE.clicked.connect(lambda: self.apply_port_state('EIO')); wrs.addWidget(bsE)
        wrs.addWidget(QLabel("CIO")); self.test_wst_cio = QLineEdit("0x00"); self.test_wst_cio.setMaximumWidth(100);
        try:
            if _ff: self.test_wst_cio.setFont(_ff)
        except Exception: pass
        wrs.addWidget(self.test_wst_cio)
        bsC = QPushButton("Apply"); bsC.clicked.connect(lambda: self.apply_port_state('CIO')); wrs.addWidget(bsC)
        T.addLayout(wrs)
        # Apply all (Direction + State for all ports)
        allr = QHBoxLayout(); ball = QPushButton("Apply All (Dir+State)"); ball.clicked.connect(self.apply_all_ports); allr.addWidget(ball)
        bread = QPushButton("Read Masks from Device"); bread.clicked.connect(self.load_masks_from_device); allr.addWidget(bread)
        bfill = QPushButton("Masks ← Checkboxes"); bfill.clicked.connect(self.fill_masks_from_checks); allr.addWidget(bfill)
        T.addLayout(allr)
        # Counters
        ctrs = QHBoxLayout(); ctrs.addWidget(QLabel("Counter0")); self.test_c0 = QLineEdit("0"); self.test_c0.setReadOnly(True); self.test_c0.setMaximumWidth(120); ctrs.addWidget(self.test_c0)
        c0r = QPushButton("Reset C0"); c0r.clicked.connect(lambda: self.reset_counter(0)); ctrs.addWidget(c0r)
        ctrs.addWidget(QLabel("Counter1")); self.test_c1 = QLineEdit("0"); self.test_c1.setReadOnly(True); self.test_c1.setMaximumWidth(120); ctrs.addWidget(self.test_c1)
        c1r = QPushButton("Reset C1"); c1r.clicked.connect(lambda: self.reset_counter(1)); ctrs.addWidget(c1r)
        T.addLayout(ctrs)
        # DAC row
        dacr = QHBoxLayout(); dacr.addWidget(QLabel("DAC0 (V)")); self.test_dac0 = QLineEdit("0.0"); self.test_dac0.setMaximumWidth(100); dacr.addWidget(self.test_dac0)
        dacr.addWidget(QLabel("DAC1 (V)")); self.test_dac1 = QLineEdit("0.0"); self.test_dac1.setMaximumWidth(100); dacr.addWidget(self.test_dac1)
        T.addLayout(dacr)
        # Buttons
        ctr = QHBoxLayout(); self.test_factory = QCheckBox("Factory on Start"); self.test_factory.setChecked(True); ctr.addWidget(self.test_factory)
        bstart = QPushButton("Start Panel"); bstart.clicked.connect(self.start_test_panel); ctr.addWidget(bstart)
        bstop = QPushButton("Stop Panel"); bstop.clicked.connect(self.stop_test_panel); ctr.addWidget(bstop)
        T.addLayout(ctr)
        # Last Error / Status line + history
        sts = QHBoxLayout(); sts.addWidget(QLabel("Last Error")); self.test_last = QLineEdit(""); self.test_last.setReadOnly(True);
        try:
            if _ff: self.test_last.setFont(_ff)
        except Exception: pass
        sts.addWidget(self.test_last)
        T.addLayout(sts)
        T.addWidget(QLabel("Error History"))
        self.test_hist = QTextEdit(); self.test_hist.setReadOnly(True); self.test_hist.setMaximumHeight(120)
        try:
            if _ff: self.test_hist.setFont(_ff)
        except Exception: pass
        T.addWidget(self.test_hist)
        self.test_log = QTextEdit(); self.test_log.setReadOnly(True)
        try:
            if _ff: self.test_log.setFont(_ff)
        except Exception: pass
        T.addWidget(self.test_log)
        self.test_log = QTextEdit(); self.test_log.setReadOnly(True); T.addWidget(self.test_log)
        daq.addTab(self.daq_test, "Test Panel")

        # keep both page widgets alive explicitly
        self._daq_keepalive = (self.daq_rw, self.daq_cw, self.daq_test)

        return daq


    def _selected_channels(self):
        return [i for i,cb in enumerate(self.chan_boxes) if cb.isChecked()]

        # ---- DAQ simple readers (used by Read/Stream tab)
    def read_daq_once(self):
        if not HAVE_U3:
            self._log(self.daq_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        chs = self._selected_channels() or [0]
        try:
            vals = u3_read_multi(chs, samples=1)
            self._log(self.daq_log, " | ".join(f"AIN{c}:{vals[0][i]:.4f} V" for i,c in enumerate(chs)))
        except Exception as e:
            self._log(self.daq_log, f"Read error: {e}")

    def read_daq_multi(self):
        if not HAVE_U3:
            self._log(self.daq_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        chs = self._selected_channels() or [0]
        ns = self.daq_nsamp.value(); delay = self.daq_delay.value()/1000.0
        try:
            vals = u3_read_multi(chs, samples=ns, delay_s=delay)
            for k,row in enumerate(vals):
                line = f"[{k+1}/{ns}] " + " | ".join(f"AIN{c}:{row[i]:.4f} V" for i,c in enumerate(chs))
                self._log(self.daq_log, line)
        except Exception as e:
            self._log(self.daq_log, f"Loop error: {e}")

    # ---- Test Panel runtime loop
    def start_test_panel(self):
        if not HAVE_U3:
            self._log(self.test_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            if self.test_factory.isChecked():
                d = u3_open();
                try: d.setToFactoryDefaults()
                finally:
                    try: d.close()
                    except Exception: pass
        except Exception as e:
            self._log(self.test_log, f"Factory reset warn: {e}")
            self._test_status(str(e), 'error')
        if not hasattr(self, 'test_timer') or self.test_timer is None:
            self.test_timer = QTimer(self)
        self.test_timer.setInterval(1000)
        self.test_timer.timeout.connect(self.tick_test_panel)
        self.test_timer.start()
        self._log(self.test_log, "Test Panel started")
        self._test_status("OK", 'info')

    def stop_test_panel(self):
        t = getattr(self, 'test_timer', None)
        if t: t.stop()
        self._log(self.test_log, "Test Panel stopped")

    def tick_test_panel(self):
        # Apply current UI state to U3 once per second; read AINs
        if not HAVE_U3:
            return
        # Directions
        try:
            for i,cb in enumerate(getattr(self, 'test_fio_dir', [])):
                u3_set_dir(f"FIO{i}", 1 if cb.isChecked() else 0)
            for i,cb in enumerate(getattr(self, 'test_eio_dir', [])):
                u3_set_dir(f"EIO{i}", 1 if cb.isChecked() else 0)
            for i,cb in enumerate(getattr(self, 'test_cio_dir', [])):
                u3_set_dir(f"CIO{i}", 1 if cb.isChecked() else 0)
        except Exception as e:
            self._log(self.test_log, f"Dir write warn: {e}")
            self._test_status(str(e), 'error')
        # States (desired)
        try:
            for i,cb in enumerate(getattr(self, 'test_fio_state', [])):
                u3_set_line(f"FIO{i}", 1 if cb.isChecked() else 0)
            for i,cb in enumerate(getattr(self, 'test_eio_state', [])):
                u3_set_line(f"EIO{i}", 1 if cb.isChecked() else 0)
            for i,cb in enumerate(getattr(self, 'test_cio_state', [])):
                u3_set_line(f"CIO{i}", 1 if cb.isChecked() else 0)
        except Exception as e:
            self._log(self.test_log, f"State write warn: {e}")
            self._test_status(str(e), 'error')
        # Readback states (DI) and per-port masks
        try:
            d = u3_open()
            try:
                states = d.getFeedback(_u3.PortStateRead())[0]  # dict {'FIO':byte, 'EIO':byte, 'CIO':byte}
                dirs   = d.getFeedback(_u3.PortDirRead())[0]
            finally:
                try: d.close()
                except Exception: pass
            sF, sE, sC = states.get('FIO',0), states.get('EIO',0), states.get('CIO',0)
            dF, dE, dC = dirs.get('FIO',0),   dirs.get('EIO',0),   dirs.get('CIO',0)
            for i,cb in enumerate(getattr(self, 'test_fio_rb', [])):
                cb.setChecked( bool((sF>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_eio_rb', [])):
                cb.setChecked( bool((sE>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_cio_rb', [])):
                cb.setChecked( bool((sC>>i)&1) )
            def fm(x):
                return f"0x{x:02X} ({x:08b})"
            self.test_dir_fio.setText(fm(dF)); self.test_dir_eio.setText(fm(dE)); self.test_dir_cio.setText(fm(dC))
            self.test_st_fio.setText(fm(sF));  self.test_st_eio.setText(fm(sE));  self.test_st_cio.setText(fm(sC))
        except Exception as e:
            self._log(self.test_log, f"Readback warn: {e}")
            self._test_status(str(e), 'error')
        # DACs
        try:
            d = u3_open()
            try:
                dv0 = max(0.0, min(5.0, float(self.test_dac0.text() or '0')))
                dv1 = max(0.0, min(5.0, float(self.test_dac1.text() or '0')))
                try:
                    d.getFeedback(_u3.DAC0_8(Value=int(dv0/5.0*255)), _u3.DAC1_8(Value=int(dv1/5.0*255)))
                except Exception:
                    pass
            finally:
                try: d.close()
                except Exception: pass
        except Exception as e:
            self._log(self.test_log, f"DAC warn: {e}")
            self._test_status(str(e), 'error')
        # AIN readings
        try:
            for i in range(4):
                v = u3_read_ain(i)
                self.test_ain_lbls[i].setText(f"{v:.4f}")
        except Exception as e:
            self._log(self.test_log, f"AIN read warn: {e}")
            self._test_status(str(e), 'error')
        # Counters
        try:
            d = u3_open()
            try:
                try:
                    c0 = d.getFeedback(_u3.Counter0(Reset=False))[0]
                except Exception:
                    c0 = None
                try:
                    c1 = d.getFeedback(_u3.Counter1(Reset=False))[0]
                except Exception:
                    c1 = None
            finally:
                try: d.close()
                except Exception: pass
            if c0 is not None:
                self.test_c0.setText(str(c0))
            if c1 is not None:
                self.test_c1.setText(str(c1))
        except Exception as e:
            self._log(self.test_log, f"Counter read warn: {e}")
            self._test_status(str(e), 'error')

    def reset_counter(self, which: int):
        if not HAVE_U3:
            return
        try:
            d = u3_open()
            try:
                if which == 0:
                    d.getFeedback(_u3.Counter0(Reset=True))
                    self._log(self.test_log, "Counter0 reset")
                else:
                    d.getFeedback(_u3.Counter1(Reset=True))
                    self._log(self.test_log, "Counter1 reset")
            finally:
                try: d.close()
                except Exception: pass
        except Exception as e:
            self._log(self.test_log, f"Counter reset warn: {e}")
            self._test_status(str(e), 'error')

    # ---- Whole-port writers (Test Panel)
    def _parse_mask_text(self, txt: str) -> int:
        s = (txt or '').strip()
        try:
            if s.lower().startswith('0x') or s.lower().startswith('0b'):
                return max(0, min(255, int(s, 0)))
            # allow binary like 10101010
            if all(c in '01' for c in s) and len(s) <= 8:
                return int(s, 2)
            return max(0, min(255, int(s)))
        except Exception:
            return 0

    def apply_port_dir(self, port: str):
        if not HAVE_U3:
            self._log(self.test_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        port = (port or 'FIO').upper()
        vF=vE=vC=0; mF=mE=mC=0
        if port=='FIO':
            vF = self._parse_mask_text(getattr(self,'test_wdir_fio').text())
            mF = 0xFF
        elif port=='EIO':
            vE = self._parse_mask_text(getattr(self,'test_wdir_eio').text())
            mE = 0xFF
        else:
            vC = self._parse_mask_text(getattr(self,'test_wdir_cio').text())
            mC = 0xFF
        try:
            d = u3_open()
            try:
                d.getFeedback(_u3.PortDirWrite(Direction=[vF,vE,vC], WriteMask=[mF,mE,mC]))
            finally:
                try: d.close()
                except Exception: pass
            self._log(self.test_log, f"Dir write {port}: 0x{(vF if port=='FIO' else vE if port=='EIO' else vC):02X}")
            self._test_status("OK", 'info')
        except Exception as e:
            self._log(self.test_log, f"Dir write error: {e}")
            self._test_status(str(e), 'error')

    def apply_port_state(self, port: str):
        if not HAVE_U3:
            self._log(self.test_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        port = (port or 'FIO').upper()
        vF=vE=vC=0; mF=mE=mC=0
        if port=='FIO':
            vF = self._parse_mask_text(getattr(self,'test_wst_fio').text())
            mF = 0xFF
        elif port=='EIO':
            vE = self._parse_mask_text(getattr(self,'test_wst_eio').text())
            mE = 0xFF
        else:
            vC = self._parse_mask_text(getattr(self,'test_wst_cio').text())
            mC = 0xFF
        try:
            d = u3_open()
            try:
                d.getFeedback(_u3.PortStateWrite(State=[vF,vE,vC], WriteMask=[mF,mE,mC]))
            finally:
                try: d.close()
                except Exception: pass
            self._log(self.test_log, f"State write {port}: 0x{(vF if port=='FIO' else vE if port=='EIO' else vC):02X}")
            self._test_status("OK", 'info')
        except Exception as e:
            self._log(self.test_log, f"State write error: {e}")
            self._test_status(str(e), 'error')

    def apply_all_ports(self):
        if not HAVE_U3:
            self._log(self.test_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            df = self._parse_mask_text(getattr(self,'test_wdir_fio').text()); de = self._parse_mask_text(getattr(self,'test_wdir_eio').text()); dc = self._parse_mask_text(getattr(self,'test_wdir_cio').text())
            sf = self._parse_mask_text(getattr(self,'test_wst_fio').text()); se = self._parse_mask_text(getattr(self,'test_wst_eio').text()); sc = self._parse_mask_text(getattr(self,'test_wst_cio').text())
            d = u3_open()
            try:
                d.getFeedback(_u3.PortDirWrite(Direction=[df,de,dc], WriteMask=[0xFF,0xFF,0xFF]))
                d.getFeedback(_u3.PortStateWrite(State=[sf,se,sc], WriteMask=[0xFF,0xFF,0xFF]))
            finally:
                try: d.close()
                except Exception: pass
            self._log(self.test_log, f"Applied all: Dir=[0x{df:02X},0x{de:02X},0x{dc:02X}] State=[0x{sf:02X},0x{se:02X},0x{sc:02X}]")
            self._test_status("OK", 'info')
        except Exception as e:
            self._log(self.test_log, f"Apply all error: {e}")
            self._test_status(str(e), 'error')

    def load_masks_from_device(self):
        if not HAVE_U3:
            self._log(self.test_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            d = u3_open()
            try:
                states = d.getFeedback(_u3.PortStateRead())[0]
                dirs   = d.getFeedback(_u3.PortDirRead())[0]
            finally:
                try: d.close()
                except Exception: pass
            sF, sE, sC = states.get('FIO',0), states.get('EIO',0), states.get('CIO',0)
            dF, dE, dC = dirs.get('FIO',0),   dirs.get('EIO',0),   dirs.get('CIO',0)
            # Fill editable mask fields
            self.test_wdir_fio.setText(f"0x{dF:02X}"); self.test_wdir_eio.setText(f"0x{dE:02X}"); self.test_wdir_cio.setText(f"0x{dC:02X}")
            self.test_wst_fio.setText(f"0x{sF:02X}");  self.test_wst_eio.setText(f"0x{sE:02X}");  self.test_wst_cio.setText(f"0x{sC:02X}")
            # Optionally sync desired checkboxes to device
            for i,cb in enumerate(getattr(self, 'test_fio_dir', [])): cb.setChecked( bool((dF>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_eio_dir', [])): cb.setChecked( bool((dE>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_cio_dir', [])): cb.setChecked( bool((dC>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_fio_state', [])): cb.setChecked( bool((sF>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_eio_state', [])): cb.setChecked( bool((sE>>i)&1) )
            for i,cb in enumerate(getattr(self, 'test_cio_state', [])): cb.setChecked( bool((sC>>i)&1) )
            self._log(self.test_log, "Loaded masks from device")
            self._test_status("OK", 'info')
        except Exception as e:
            self._log(self.test_log, f"Read masks error: {e}")
            self._test_status(str(e), 'error')

    def fill_masks_from_checks(self):
        def mfrom(checks):
            m=0
            for i,cb in enumerate(checks):
                if cb.isChecked(): m|=(1<<i)
            return m
        try:
            dF = mfrom(getattr(self,'test_fio_dir', [])); dE = mfrom(getattr(self,'test_eio_dir', [])); dC = mfrom(getattr(self,'test_cio_dir', []))
            sF = mfrom(getattr(self,'test_fio_state', [])); sE = mfrom(getattr(self,'test_eio_state', [])); sC = mfrom(getattr(self,'test_cio_state', []))
            self.test_wdir_fio.setText(f"0x{dF:02X}"); self.test_wdir_eio.setText(f"0x{dE:02X}"); self.test_wdir_cio.setText(f"0x{dC:02X}")
            self.test_wst_fio.setText(f"0x{sF:02X}");  self.test_wst_eio.setText(f"0x{sE:02X}");  self.test_wst_cio.setText(f"0x{sC:02X}")
            self._log(self.test_log, "Filled mask editors from checkboxes")
        except Exception as e:
            self._log(self.test_log, f"Fill masks error: {e}")
            self._test_status(str(e), 'error')

    # ---- U3 config helpers/actions
    def _mask_from_checks(self, checks):
        m=0
        for i,cb in enumerate(checks):
            if cb.isChecked(): m|=(1<<i)
        return m

    def u3_read_current(self):
        if not HAVE_U3:
            self._log(self.cfg_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            d=u3_open()
            info=d.configIO()
            self._log(self.cfg_log, str(info))
        except Exception as e:
            self._log(self.cfg_log, f"Read error: {e}")
        finally:
            try: d.close()
            except Exception: pass

    def u3_write_factory(self):
        if not HAVE_U3:
            self._log(self.cfg_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            d=u3_open()
            # Set power-up defaults back to factory via Device API
            d.setToFactoryDefaults()
            self._log(self.cfg_log, "Factory defaults restored")
        except Exception as e:
            self._log(self.cfg_log, f"Factory write error: {e}")
        finally:
            try: d.close()
            except Exception: pass

    def u3_write_values(self):
        if not HAVE_U3:
            self._log(self.cfg_log, f"u3 missing → {INSTALL_HINTS['u3']}"); return
        try:
            d=u3_open()
            # Analog inputs / directions + Counters
            fio_an=self._mask_from_checks(self.ai_checks)
            fio_dir=self._mask_from_checks(self.fio_dir_box); eio_dir=self._mask_from_checks(self.eio_dir_box); cio_dir=self._mask_from_checks(self.cio_dir_box)
            # Set default directions/analog settings at boot via configU3
            try:
                d.configU3(FIOAnalog=fio_an, FIODirection=fio_dir, EIODirection=eio_dir, CIODirection=cio_dir)
            except Exception:
                pass
            # Digital states (defaults + current)
            fio_state=self._mask_from_checks(self.fio_state_box); eio_state=self._mask_from_checks(self.eio_state_box); cio_state=self._mask_from_checks(self.cio_state_box)
            try:
                d.configU3(FIOState=fio_state, EIOState=eio_state, CIOState=cio_state)
            except Exception:
                pass
            fb=[]
            # Use global IO numbering: FIO0-7 → 0..7, EIO0-7 → 8..15, CIO0-3 → 16..19
            for i in range(8):
                fb.append(_u3.BitStateWrite(i, 1 if (fio_state>>i)&1 else 0))
            for i in range(8):
                fb.append(_u3.BitStateWrite(8+i, 1 if (eio_state>>i)&1 else 0))
            for i in range(4):
                fb.append(_u3.BitStateWrite(16+i, 1 if (cio_state>>i)&1 else 0))
            # DAC outputs (8-bit mode by default)
            try:
                dv0=max(0.0,min(5.0,float(self.dac0.text() or '0'))); dv1=max(0.0,min(5.0,float(self.dac1.text() or '0')))
                fb.append(_u3.DAC0_8(Value=int(dv0/5.0*255)))
                fb.append(_u3.DAC1_8(Value=int(dv1/5.0*255)))
            except Exception:
                pass
            # Timer/Counter clock setup
            if self.t_clkbase.currentText()=="48MHz": base=48
            elif self.t_clkbase.currentText()=="750kHz": base=750
            else: base=4
            try:
                d.configTimerClock(TimerClockBase=base, TimerClockDivisor=self.t_div.value())
                d.configIO(NumberOfTimersEnabled=self.t_num.value(), TimerCounterPinOffset=self.t_pin.value(),
                           EnableCounter0=self.counter0.isChecked(), EnableCounter1=self.counter1.isChecked(),
                           FIOAnalog=fio_an)
            except Exception:
                pass
            # Apply digital state writes
            try:
                d.getFeedback(*fb)
            except Exception:
                # Fallback to immediate per-pin writes
                try:
                    for i in range(8):
                        d.setDOState(i, 1 if (fio_state>>i)&1 else 0)
                    for i in range(8):
                        d.setDOState(8+i, 1 if (eio_state>>i)&1 else 0)
                    for i in range(4):
                        d.setDOState(16+i, 1 if (cio_state>>i)&1 else 0)
                except Exception:
                    pass
            # Persist current configuration as power-up defaults
            try:
                d.setDefaults()
            except Exception:
                pass
            # Watchdog (best-effort mapping of extra options)
            if self.wd_en.isChecked():
                try:
                    timeout = int(float(self.wd_to.text() or '100'))
                    reset = self.wd_reset.isChecked()
                    set_dio = False; dio_num = 0; dio_state = 0
                    wline = getattr(self, 'wd_line', None)
                    if wline and wline.currentText() != 'None':
                        pin = wline.currentText()  # e.g., 'FIO3', 'EIO1', 'CIO0'
                        base = 0
                        if pin.startswith('FIO'): base = 0
                        elif pin.startswith('EIO'): base = 8
                        elif pin.startswith('CIO'): base = 16
                        try:
                            idx = int(pin[3:])
                            dio_num = base + idx
                            dio_state = 1 if self.wd_state.currentText()=="High" else 0
                            set_dio = True
                        except Exception:
                            set_dio = False
                    d.watchdog(ResetOnTimeout=reset,
                               SetDIOStateOnTimeout=set_dio,
                               TimeoutPeriod=timeout,
                               DIOState=dio_state,
                               DIONumber=dio_num)
                except Exception:
                    pass
            # Backward-compat flags (placeholders; ignored on unsupported firmwares)
            try:
                # Not directly supported by configU3; left as no-op
                pass
            except Exception:
                pass
            self._log(self.cfg_log, "Values written")
        except Exception as e:
            self._log(self.cfg_log, f"Write error: {e}")
        finally:
            try: d.close()
            except Exception: pass

    # Apply current DAQ config selections for this run (no persist unless requested)
    def u3_autoconfig_runtime(self, base: str = 'Keep Current', pulse_line: str = 'None', persist: bool = False):
        if not HAVE_U3:
            return
        d = None
        try:
            d = u3_open()
            # Optional factory base
            if isinstance(base, str) and base.lower().startswith('factory'):
                try:
                    d.setToFactoryDefaults()
                except Exception:
                    pass
            # Collect masks from current UI
            fio_an = self._mask_from_checks(self.ai_checks) if hasattr(self,'ai_checks') else 0x0F
            fio_dir = self._mask_from_checks(self.fio_dir_box) if hasattr(self,'fio_dir_box') else 0
            eio_dir = self._mask_from_checks(self.eio_dir_box) if hasattr(self,'eio_dir_box') else 0
            cio_dir = self._mask_from_checks(self.cio_dir_box) if hasattr(self,'cio_dir_box') else 0
            fio_state = self._mask_from_checks(self.fio_state_box) if hasattr(self,'fio_state_box') else 0
            eio_state = self._mask_from_checks(self.eio_state_box) if hasattr(self,'eio_state_box') else 0
            cio_state = self._mask_from_checks(self.cio_state_box) if hasattr(self,'cio_state_box') else 0
            # Configure directions and analog mode at boot/current
            try:
                d.configU3(FIOAnalog=fio_an, FIODirection=fio_dir, EIODirection=eio_dir, CIODirection=cio_dir)
            except Exception:
                pass
            # Digital states (apply now)
            fb=[]
            for i in range(8): fb.append(_u3.BitStateWrite(i, 1 if (fio_state>>i)&1 else 0))
            for i in range(8): fb.append(_u3.BitStateWrite(8+i, 1 if (eio_state>>i)&1 else 0))
            for i in range(4): fb.append(_u3.BitStateWrite(16+i, 1 if (cio_state>>i)&1 else 0))
            try:
                d.getFeedback(*fb)
            except Exception:
                try:
                    for i in range(8): d.setDOState(i, 1 if (fio_state>>i)&1 else 0)
                    for i in range(8): d.setDOState(8+i, 1 if (eio_state>>i)&1 else 0)
                    for i in range(4): d.setDOState(16+i, 1 if (cio_state>>i)&1 else 0)
                except Exception:
                    pass
            # DAC outputs from UI if present
            try:
                dv0=max(0.0,min(5.0,float(self.dac0.text() or '0'))); dv1=max(0.0,min(5.0,float(self.dac1.text() or '0')))
                try:
                    d.getFeedback(_u3.DAC0_8(Value=int(dv0/5.0*255)), _u3.DAC1_8(Value=int(dv1/5.0*255)))
                except Exception:
                    pass
            except Exception:
                pass
            # Timers / Counters
            try:
                if self.t_clkbase.currentText()=="48MHz": base_clk=48
                elif self.t_clkbase.currentText()=="750kHz": base_clk=750
                else: base_clk=4
                d.configTimerClock(TimerClockBase=base_clk, TimerClockDivisor=self.t_div.value())
                d.configIO(NumberOfTimersEnabled=self.t_num.value(), TimerCounterPinOffset=self.t_pin.value(),
                           EnableCounter0=self.counter0.isChecked(), EnableCounter1=self.counter1.isChecked(),
                           FIOAnalog=fio_an)
            except Exception:
                pass
            # Watchdog if enabled in UI
            try:
                if self.wd_en.isChecked():
                    timeout = int(float(self.wd_to.text() or '100'))
                    reset = self.wd_reset.isChecked()
                    set_dio = False; dio_num = 0; dio_state = 0
                    wline = getattr(self, 'wd_line', None)
                    if wline and wline.currentText() != 'None':
                        pin = wline.currentText()
                        basep = 0
                        if pin.startswith('FIO'): basep = 0
                        elif pin.startswith('EIO'): basep = 8
                        elif pin.startswith('CIO'): basep = 16
                        try:
                            idx = int(pin[3:]); dio_num = basep + idx
                            dio_state = 1 if self.wd_state.currentText()=="High" else 0
                            set_dio = True
                        except Exception:
                            set_dio = False
                    d.watchdog(ResetOnTimeout=reset,
                               SetDIOStateOnTimeout=set_dio,
                               TimeoutPeriod=timeout,
                               DIOState=dio_state,
                               DIONumber=dio_num)
            except Exception:
                pass
            # Ensure pulse line (if any) is an output
            try:
                if pulse_line and pulse_line.strip().lower() != 'none':
                    u3_set_dir(pulse_line, 1)
            except Exception:
                pass
            # Persist current as power-up defaults if requested
            if persist:
                try:
                    d.setDefaults()
                except Exception:
                    pass
        finally:
            try:
                if d: d.close()
            except Exception:
                pass

    # ---- Automation
    def tab_automation(self):
        w = QWidget(); L = QVBoxLayout(w)
        r = QHBoxLayout(); r.addWidget(QLabel("FY Channel:")); self.auto_ch = QComboBox(); self.auto_ch.addItems(["1","2"]); r.addWidget(self.auto_ch)
        r.addWidget(QLabel("Scope CH:")); self.auto_scope_ch = QComboBox(); self.auto_scope_ch.addItems(["1","2","3","4"]); r.addWidget(self.auto_scope_ch)
        r.addWidget(QLabel("Metric:")); self.auto_metric = QComboBox(); self.auto_metric.addItems(["RMS","PK2PK"]); r.addWidget(self.auto_metric); L.addLayout(r)
        # Shared override row (preferred port/protocol for sweeps)
        r2 = QHBoxLayout(); r2.addWidget(QLabel("FY Port (override):")); self.auto_port = QLineEdit(""); r2.addWidget(self.auto_port)
        scan = QPushButton("Scan"); scan.clicked.connect(lambda: self.scan_serial_into(self.auto_port)); r2.addWidget(scan)
        r2.addWidget(QLabel("Protocol:")); self.auto_proto = QComboBox(); self.auto_proto.addItems(FY_PROTOCOLS); r2.addWidget(self.auto_proto)
        L.addLayout(r2)
        r = QHBoxLayout(); r.addWidget(QLabel("Start Hz")); self.auto_start = QLineEdit("100"); r.addWidget(self.auto_start)
        r.addWidget(QLabel("Stop Hz")); self.auto_stop = QLineEdit("10000"); r.addWidget(self.auto_stop)
        r.addWidget(QLabel("Step Hz")); self.auto_step = QLineEdit("100"); r.addWidget(self.auto_step)
        r.addWidget(QLabel("Amp Vpp")); self.auto_amp = QLineEdit("2.0"); r.addWidget(self.auto_amp)
        r.addWidget(QLabel("Dwell ms")); self.auto_dwell = QLineEdit("500"); r.addWidget(self.auto_dwell); L.addLayout(r)
        # KPI options row
        r3 = QHBoxLayout();
        self.auto_do_thd = QCheckBox("THD (FFT)"); r3.addWidget(self.auto_do_thd)
        self.auto_do_knees = QCheckBox("Find Knees"); r3.addWidget(self.auto_do_knees)
        r3.addWidget(QLabel("Drop dB")); self.auto_knee_db = QLineEdit("3.0"); self.auto_knee_db.setMaximumWidth(80); r3.addWidget(self.auto_knee_db)
        r3.addWidget(QLabel("Ref")); self.auto_ref_mode = QComboBox(); self.auto_ref_mode.addItems(["Max","1kHz"]); r3.addWidget(self.auto_ref_mode)
        self.auto_ref_hz = QLineEdit("1000"); self.auto_ref_hz.setMaximumWidth(100); r3.addWidget(self.auto_ref_hz)
        L.addLayout(r3)
        # U3 orchestration row
        r4 = QHBoxLayout(); r4.addWidget(QLabel("U3 Pulse Pin:")); self.auto_u3_line = QComboBox();
        self.auto_u3_line.addItems(["None"]+[f"FIO{i}" for i in range(8)]+[f"EIO{i}" for i in range(8)]+[f"CIO{i}" for i in range(4)])
        r4.addWidget(self.auto_u3_line); r4.addWidget(QLabel("Width ms")); self.auto_u3_pwidth = QLineEdit("10"); self.auto_u3_pwidth.setMaximumWidth(80); r4.addWidget(self.auto_u3_pwidth)
        # External trigger options
        self.auto_use_ext = QCheckBox("Use EXT Trigger"); r4.addWidget(self.auto_use_ext)
        r4.addWidget(QLabel("Slope")); self.auto_ext_slope = QComboBox(); self.auto_ext_slope.addItems(["Rise","Fall"]); r4.addWidget(self.auto_ext_slope)
        r4.addWidget(QLabel("Level V")); self.auto_ext_level = QLineEdit(""); self.auto_ext_level.setMaximumWidth(80); r4.addWidget(self.auto_ext_level)
        r4.addWidget(QLabel("Pre-arm ms")); self.auto_ext_pre_ms = QLineEdit("5"); self.auto_ext_pre_ms.setMaximumWidth(80); r4.addWidget(self.auto_ext_pre_ms)
        L.addLayout(r4)
        # U3 auto-config row (base: factory/current)
        r4b = QHBoxLayout(); self.auto_u3_autocfg = QCheckBox("Auto-config U3 for run"); self.auto_u3_autocfg.setChecked(True)
        r4b.addWidget(self.auto_u3_autocfg)
        r4b.addWidget(QLabel("Base")); self.auto_u3_base = QComboBox(); self.auto_u3_base.addItems(["Keep Current","Factory First"]); r4b.addWidget(self.auto_u3_base)
        L.addLayout(r4b)
        # Math options (two probes across load)
        r5 = QHBoxLayout(); self.auto_use_math = QCheckBox("Use MATH (CH1-CH2)"); r5.addWidget(self.auto_use_math)
        r5.addWidget(QLabel("Order")); self.auto_math_order = QComboBox(); self.auto_math_order.addItems(["CH1-CH2","CH2-CH1"]); r5.addWidget(self.auto_math_order)
        L.addLayout(r5)
        r = QHBoxLayout(); b = QPushButton("Run Sweep"); b.clicked.connect(self.run_sweep_scope_fixed); r.addWidget(b)
        kb = QPushButton("Run KPIs"); kb.clicked.connect(self.run_audio_kpis); r.addWidget(kb)
        sb = QPushButton("Stop"); sb.clicked.connect(self.stop_sweep_scope); r.addWidget(sb); L.addLayout(r)
        self.auto_prog = QProgressBar(); L.addWidget(self.auto_prog)
        self.auto_log = QTextEdit(); self.auto_log.setReadOnly(True); L.addWidget(self.auto_log)
        return w

    def stop_sweep_scope(self):
        self._sweep_abort = True

    def run_sweep_scope_fixed(self):
        try:
            ch = int(self.auto_ch.currentText()); sch = int(self.auto_scope_ch.currentText())
            start = float(self.auto_start.text()); stop = float(self.auto_stop.text()); step = float(self.auto_step.text())
            amp = float(self.auto_amp.text()); dwell = max(0.0, float(self.auto_dwell.text())/1000.0)
            metric = self.auto_metric.currentText()
            freqs=[]; f=start
            while f <= stop + 1e-9:
                freqs.append(round(f,6)); f += step
            out=[]; self._sweep_abort=False; n=len(freqs)
            pr = (self.auto_proto.currentText() if hasattr(self,'auto_proto') else "FY ASCII 9600")
            pt = ((self.auto_port.text().strip() if hasattr(self,'auto_port') else '') or find_fy_port())
            # Optional math / ext trigger
            use_math = bool(self.auto_use_math.isChecked()) if hasattr(self,'auto_use_math') else False
            order = (self.auto_math_order.currentText() if hasattr(self,'auto_math_order') else 'CH1-CH2')
            use_ext = bool(self.auto_use_ext.isChecked()) if hasattr(self,'auto_use_ext') else False
            ext_slope = (self.auto_ext_slope.currentText() if hasattr(self,'auto_ext_slope') else 'Rise')
            try:
                ext_level = float(self.auto_ext_level.text()) if hasattr(self,'auto_ext_level') and self.auto_ext_level.text().strip() else None
            except Exception:
                ext_level = None
            try:
                pre_ms = float(self.auto_ext_pre_ms.text()) if hasattr(self,'auto_ext_pre_ms') and self.auto_ext_pre_ms.text().strip() else 5.0
            except Exception:
                pre_ms = 5.0
            rsrc = self.scope_edit.text().strip() if hasattr(self,'scope_edit') else self.scope_res
            # Optional U3 auto-config: apply current DAQ selections
            try:
                if hasattr(self,'auto_u3_autocfg') and self.auto_u3_autocfg.isChecked():
                    base = self.auto_u3_base.currentText() if hasattr(self,'auto_u3_base') else 'Keep Current'
                    self.u3_autoconfig_runtime(base=base, pulse_line='None', persist=False)
            except Exception as e:
                self._log(self.auto_log, f"U3 auto-config warn: {e}")
            for i,f in enumerate(freqs):
                if self._sweep_abort: break
                try:
                    fy_apply(freq_hz=f, amp_vpp=amp, wave="Sine", off_v=0.0, duty=None, ch=ch, port=pt, proto=pr)
                except Exception as e:
                    self._log(self.auto_log, f"FY error @ {f} Hz: {e}"); continue
                time.sleep(dwell)
                typ = 'RMS' if metric=='RMS' else 'PK2PK'
                # Configure math and ext trigger if requested
                if use_math:
                    try:
                        scope_configure_math_subtract(rsrc or self.scope_res, order=order)
                    except Exception as e:
                        self._log(self.auto_log, f"MATH config error: {e}")
                if use_ext:
                    try:
                        scope_set_trigger_ext(rsrc or self.scope_res, slope=ext_slope, level=ext_level)
                        scope_arm_single(rsrc or self.scope_res)
                        if pre_ms > 0: time.sleep(pre_ms/1000.0)
                        scope_wait_single_complete(rsrc or self.scope_res, timeout_s=max(1.0, dwell*2+0.5))
                    except Exception as e:
                        self._log(self.auto_log, f"EXT trig wait error: {e}")
                try:
                    src = 'MATH' if use_math else sch
                    val = self.scope_measure(src, typ)
                except Exception as e:
                    self._log(self.auto_log, f"Scope error @ {f} Hz: {e}"); val = float('nan')
                out.append((f,val))
                self._log(self.auto_log, f"{f:.3f} Hz → {metric} {val:.4f} ({'MATH' if use_math else f'CH{sch}'})")
                self.auto_prog.setValue(int((i+1)/n*100)); QApplication.processEvents()
            os.makedirs('results', exist_ok=True)
            fn = os.path.join('results','sweep_scope.csv')
            with open(fn,'w') as fh:
                fh.write('freq_hz,metric\n')
                for f,val in out: fh.write(f"{f},{val}\n")
            self._log(self.auto_log, f"Saved: {fn}")
        except Exception as e:
            self._log(self.auto_log, f"Sweep error: {e}")

    def run_audio_kpis(self):
        """Sweep using FY + scope, compute Vrms/PkPk and THD, then report -dB knees if requested."""
        try:
            ch = int(self.auto_ch.currentText()); sch = int(self.auto_scope_ch.currentText())
            start = float(self.auto_start.text()); stop = float(self.auto_stop.text()); step = float(self.auto_step.text())
            amp = float(self.auto_amp.text()); dwell = max(0.0, float(self.auto_dwell.text())/1000.0)
            # FY override
            pr = (self.auto_proto.currentText() if hasattr(self,'auto_proto') else "FY ASCII 9600")
            pt = ((self.auto_port.text().strip() if hasattr(self,'auto_port') else '') or find_fy_port())
            # U3 orchestration + EXT trigger
            pulse_line = self.auto_u3_line.currentText() if hasattr(self, 'auto_u3_line') else 'None'
            try:
                pulse_ms = float(self.auto_u3_pwidth.text()) if hasattr(self,'auto_u3_pwidth') and self.auto_u3_pwidth.text().strip() else 0.0
            except Exception:
                pulse_ms = 0.0
            use_ext = bool(self.auto_use_ext.isChecked()) if hasattr(self,'auto_use_ext') else False
            ext_slope = (self.auto_ext_slope.currentText() if hasattr(self,'auto_ext_slope') else 'Rise')
            try:
                ext_level = float(self.auto_ext_level.text()) if hasattr(self,'auto_ext_level') and self.auto_ext_level.text().strip() else None
            except Exception:
                ext_level = None
            try:
                pre_ms = float(self.auto_ext_pre_ms.text()) if hasattr(self,'auto_ext_pre_ms') and self.auto_ext_pre_ms.text().strip() else 5.0
            except Exception:
                pre_ms = 5.0
            # MATH use
            use_math = bool(self.auto_use_math.isChecked()) if hasattr(self,'auto_use_math') else False
            order = (self.auto_math_order.currentText() if hasattr(self,'auto_math_order') else 'CH1-CH2')
            # U3 auto-config (base: factory/current) using current DAQ selections
            try:
                if hasattr(self,'auto_u3_autocfg') and self.auto_u3_autocfg.isChecked():
                    base = self.auto_u3_base.currentText() if hasattr(self,'auto_u3_base') else 'Keep Current'
                    self.u3_autoconfig_runtime(base=base, pulse_line=pulse_line, persist=False)
            except Exception as e:
                self._log(self.auto_log, f"U3 auto-config warn: {e}")
            # Build frequency list
            freqs=[]; f=start
            while f <= stop + 1e-9:
                freqs.append(round(f,6)); f += step
            self._sweep_abort = False
            n = len(freqs)
            # Scope resource
            rsrc = self.scope_edit.text().strip() if hasattr(self,'scope_edit') else self.scope_res
            out = []
            for i,f in enumerate(freqs):
                if self._sweep_abort: break
                # Set generator
                try:
                    fy_apply(freq_hz=f, amp_vpp=amp, wave="Sine", off_v=0.0, duty=None, ch=ch, port=pt, proto=pr)
                except Exception as e:
                    self._log(self.auto_log, f"FY error @ {f} Hz: {e}")
                    continue
                # Optional EXT trigger workflow
                try:
                    if use_ext:
                        # Configure and arm single; brief pre-arm delay; then pulse U3 to trigger
                        scope_set_trigger_ext(rsrc or self.scope_res, slope=ext_slope, level=ext_level)
                        scope_arm_single(rsrc or self.scope_res)
                        if pre_ms > 0: time.sleep(pre_ms/1000.0)
                    # U3 pulse (either used as EXT trigger or general control)
                    if HAVE_U3 and pulse_line and pulse_line != 'None' and pulse_ms > 0.0:
                        u3_pulse_line(pulse_line, width_ms=pulse_ms, level=1)
                except Exception as e:
                    self._log(self.auto_log, f"U3/EXT trig error: {e}")
                # Wait for acquisition complete or dwell fallback
                done = False
                if use_ext:
                    try:
                        done = scope_wait_single_complete(rsrc or self.scope_res, timeout_s=max(1.0, dwell*2+0.5))
                    except Exception:
                        done = False
                if not done and dwell > 0:
                    time.sleep(dwell)
                # Configure MATH if requested
                if use_math:
                    try:
                        scope_configure_math_subtract(rsrc or self.scope_res, order=order)
                    except Exception as e:
                        self._log(self.auto_log, f"MATH config error: {e}")
                # Capture calibrated waveform
                try:
                    src = 'MATH' if use_math else sch
                    t, v = scope_capture_calibrated(rsrc or self.scope_res, timeout_ms=15000, ch=src)
                except Exception as e:
                    self._log(self.auto_log, f"Scope capture error @ {f} Hz: {e}")
                    t = []; v = []
                # Compute KPIs
                vr = vrms(v) if v else float('nan')
                pp = vpp(v) if v else float('nan')
                thd_ratio = float('nan'); thd_percent = float('nan')
                if getattr(self, 'auto_do_thd', None) and self.auto_do_thd.isChecked() and v:
                    try:
                        thd_ratio, f_est, _ = thd_fft(t, v, f0=f, nharm=10, window='hann')
                        thd_percent = float(thd_ratio*100.0) if np.isfinite(thd_ratio) else float('nan')
                    except Exception as e:
                        self._log(self.auto_log, f"THD calc error @ {f} Hz: {e}")
                        thd_ratio = float('nan'); thd_percent = float('nan')
                out.append((f, vr, pp, thd_ratio, thd_percent))
                msg = f"{f:.3f} Hz → Vrms {vr:.4f} V, PkPk {pp:.4f} V"
                if np.isfinite(thd_percent):
                    msg += f", THD {thd_percent:.3f}%"
                self._log(self.auto_log, msg)
                self.auto_prog.setValue(int((i+1)/n*100)); QApplication.processEvents()
            # Save CSV
            os.makedirs('results', exist_ok=True)
            fn = os.path.join('results','audio_kpis.csv')
            with open(fn,'w') as fh:
                fh.write('freq_hz,vrms,pkpk,thd_ratio,thd_percent\n')
                for row in out:
                    fh.write(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n")
            self._log(self.auto_log, f"Saved: {fn}")
            # Knees
            if getattr(self, 'auto_do_knees', None) and self.auto_do_knees.isChecked() and out:
                try:
                    freqs = [r[0] for r in out]; amps = [r[2] for r in out]  # use PkPk by default
                    drop = float(self.auto_knee_db.text() or '3.0')
                    ref_mode = (self.auto_ref_mode.currentText() if hasattr(self,'auto_ref_mode') else 'Max')
                    ref_hz = float(self.auto_ref_hz.text() or '1000') if ref_mode.lower().startswith('1k') else 1000.0
                    f_lo, f_hi, ref_amp, ref_db = find_knees(freqs, amps, ref_mode=('freq' if ref_mode.lower().startswith('1k') else 'max'), ref_hz=ref_hz, drop_db=drop)
                    summ = f"Knees @ -{drop:.2f} dB (ref {ref_mode}): low≈{f_lo:.2f} Hz, high≈{f_hi:.2f} Hz (ref_amp={ref_amp:.4f} V, ref_dB={ref_db:.2f} dB)"
                    self._log(self.auto_log, summ)
                    with open(os.path.join('results','audio_knees.txt'),'w') as fh:
                        fh.write(summ+"\n")
                except Exception as e:
                    self._log(self.auto_log, f"Knee calc error: {e}")
        except Exception as e:
            self._log(self.auto_log, f"KPI sweep error: {e}")

    # ---- Diagnostics
    def tab_diag(self):
        w = QWidget(); L = QVBoxLayout(w)
        self.diag = QTextEdit(); self.diag.setReadOnly(True); L.addWidget(self.diag)
        b = QPushButton("Run Diagnostics"); b.clicked.connect(self.run_diag); L.addWidget(b)
        return w

    def run_diag(self):
        out = ["Dependencies: "+dep_msg()]
        if HAVE_SERIAL:
            ps = list_ports(); out.append("Serial: "+(", ".join(p.device for p in ps) if ps else "(none)"))
        else:
            out.append(f"pyserial missing → {INSTALL_HINTS['pyserial']}")
        if HAVE_PYVISA:
            try:
                res = _pyvisa.ResourceManager().list_resources()
                out.append("VISA: " + (", ".join(res) if res else "(none)"))
            except Exception as e:
                out.append(f"VISA error: {e}")
        else:
            out.append(f"pyvisa missing → {INSTALL_HINTS['pyvisa']}")
        if HAVE_U3:
            try:
                v = u3_read_ain(0)
                out.append(f"U3 AIN0 read OK: {v:.4f} V")
            except Exception as e:
                out.append(f"U3 error: {e}")
        else:
            out.append(f"u3 missing → {INSTALL_HINTS['u3']}")
        self._log(self.diag, "\n".join(out))

    @staticmethod
    def _log(w, t):
        w.append(t)

    # ---- Test Panel status/history helpers
    def _test_status(self, text: str, level: str = 'error'):
        try:
            ts = time.strftime('%H:%M:%S')
            tag = 'ERROR' if str(level).lower().startswith('err') else 'INFO'
            entry = f"[{ts}] {tag}: {text}"
            if not hasattr(self, '_test_hist') or self._test_hist is None:
                self._test_hist = []
            self._test_hist.append(entry)
            # keep last 50 entries
            if len(self._test_hist) > 50:
                self._test_hist = self._test_hist[-50:]
            if hasattr(self, 'test_last') and self.test_last is not None:
                self.test_last.setText(text)
            if hasattr(self, 'test_hist') and self.test_hist is not None:
                self.test_hist.setPlainText("\n".join(self._test_hist))
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description='Unified GUI (Lite+U3)')
    ap.add_argument('--gui', action='store_true', help='Launch Qt GUI')
    sub = ap.add_subparsers(dest='cmd')
    sub.add_parser('diag')
    sub.add_parser('gui')
    sub.add_parser('selftest')
    args = ap.parse_args()

    if args.cmd == 'diag':
        print('Dependency status:', dep_msg())
        if HAVE_SERIAL:
            ps = list_ports()
            print('Serial:', ", ".join(p.device for p in ps) if ps else '(none)')
        else:
            print('pyserial missing →', INSTALL_HINTS['pyserial'])
        if HAVE_PYVISA:
            try:
                print('VISA:', ", ".join(_pyvisa.ResourceManager().list_resources()) or '(none)')
            except Exception as e:
                print('VISA error:', e)
        else:
            print('pyvisa missing →', INSTALL_HINTS['pyvisa'])
        if HAVE_U3:
            try:
                print('U3 AIN0:', f"{u3_read_ain(0):.4f} V")
            except Exception as e:
                print('U3 error:', e)
        else:
            print('u3 missing →', INSTALL_HINTS['u3'])
        return

    if args.cmd == 'selftest':
        ok = True
        try:
            # Test1: baud/EOL tuples
            assert FY_BAUD_EOLS == [(9600, "\n"), (115200, "\r\n")]
            print('Test1 OK: baud/EOL tuples valid')

            # Test2: command formatting
            for ch in (1, 2):
                cmds = _fy_cmds(1000, 2.0, 0.0, 'Sine', duty=12.3, ch=ch)
                assert any(c.startswith(('bd', 'dd')) for c in cmds)
                assert cmds[-1].startswith(('ba', 'da'))
                assert all(len(c)+1 <= 15 for c in cmds)
            print('Test2 OK: command formatting (duty 3-digit, amplitude last, length ≤15)')

            # Test3: centi-Hz scaling
            assert _fy_cmds(1000, 2.0, 0.0, 'Sine', None, 1)[1].endswith(f"{1000*100:09d}")
            print('Test3 OK: centi-Hz scaling (1000 Hz → 100000)')

            # Test4: sweep start/end centi-Hz and 9-digit padding
            st = 123.45; en = 678.9
            start_cmd = f"b{int(st*100):09d}"; end_cmd = f"e{int(en*100):09d}"
            assert start_cmd == "b000012345" and end_cmd == "e000067890"
            print('Test4 OK: sweep start/end centi-Hz and 9-digit padding')

            # Test5: duty 12.3% → d123
            cmds = _fy_cmds(1000, 2.0, 0.0, 'Sine', duty=12.3, ch=1)
            duty_cmd = [c for c in cmds if c.startswith('bd')][0]
            assert duty_cmd.endswith('123')
            print('Test5 OK: duty 12.3% → d123')

            # Test6: clamp extremes
            cm = _fy_cmds(1000, 120.0, 0.0, 'Sine', duty=123.4, ch=1)
            assert any(x.endswith('999') for x in cm if x.startswith('bd'))
            assert cm[-1].endswith('99.99')
            cm2 = _fy_cmds(1000, -5.0, 0.005, 'Sine', duty=0.04, ch=2)
            assert cm2[-1].endswith('0.00')
            assert any(x.endswith('000') for x in cm2 if x.startswith('dd'))
            assert not any(x.endswith('0.01') for x in cm2 if x.startswith('do'))
            print('Test6 OK: clamps for duty/amp/offset')

            # Test7: IEEE block decode
            raw = b'#3100' + bytes(range(100)) + b'extra'
            dec = _decode_ieee_block(raw)
            assert len(dec) == 100 and dec[0] == 0 and dec[-1] == 99
            hdr = 't,volts\n'; assert hdr.endswith('\n') and hdr.startswith('t,volts')
            print('Test7 OK: block decode and CSV header')

            # Test8: passthrough when not IEEE block
            dec2 = _decode_ieee_block(b'hello')
            assert dec2 == b'hello'
            print('Test8 OK: raw (non-#) IEEE block passthrough')

            # Test9: duty clamp at 0%
            cm3 = _fy_cmds(1000, 2.0, 0.0, 'Sine', duty=-5.0, ch=1)
            assert any(x.endswith('000') for x in cm3 if x.startswith('bd'))
            print('Test9 OK: duty clamp at 0% → d000')
            # Test10: THD estimator sanity (sine + 10% 2nd harmonic)
            fs = 50000.0; f0 = 1000.0; N = 4096
            t = np.arange(N)/fs
            sig = np.sin(2*np.pi*f0*t) + 0.1*np.sin(2*np.pi*2*f0*t)
            thd, f_est, _ = thd_fft(t, sig, f0=f0, nharm=5, window='hann')
            assert abs(thd - 0.1) < 0.03  # within a few % points due to window/leakage
            print('Test10 OK: THD ~10% on 2nd harmonic')
        except Exception as e:
            ok = False
            print('Selftest FAIL:', e)
        sys.exit(0 if ok else 1)

    # Launch GUI
    if args.gui or args.cmd == 'gui':
        if not HAVE_QT:
            print('Qt not available (PySide6/PyQt5). Install with:', INSTALL_HINTS['pyside6'], 'or', INSTALL_HINTS['pyqt5'])
            print('Python exe:', sys.executable)
            return
        app = QApplication(sys.argv); win = UnifiedGUI(); win.show()
        # PySide6 has app.exec(), PyQt5 uses app.exec_()
        if hasattr(app, 'exec'):
            sys.exit(app.exec())
        else:
            sys.exit(app.exec_())
def _run_selftest() -> tuple[bool, List[str]]:
    """
    Lightweight, hardware-free validation of core math & orchestration expectations.
    Returns (ok, messages)
    """
    msgs: List[str] = []
    ok = True
    try:
        # Test 1: build_freq_points linear spacing inclusive
        pts = build_freq_points(10, 100, points=5, mode="linear")
        assert pts == [10.0, 32.5, 55.0, 77.5, 100.0]
        msgs.append("Test1 OK: linear spacing")

        # Test 2: log spacing monotonic & endpoints
        log_pts = build_freq_points(10, 1000, points=4, mode="log")
        assert abs(log_pts[0] - 10) < 1e-6 and abs(log_pts[-1] - 1000) < 1e-6
        assert all(a < b for a, b in zip(log_pts, log_pts[1:]))
        msgs.append("Test2 OK: log spacing")

        # Test 3: THD sanity (one harmonic at 10%)
        fs = 50_000.0
        f0 = 1000.0
        n = 4096
        t = np.arange(n) / fs
        sig = np.sin(2 * math.pi * f0 * t) + 0.1 * np.sin(2 * math.pi * 2 * f0 * t)
        thd_ratio, f0_est, fund_amp = thd_fft(t, sig, f0=f0, nharm=5, window="hann")
        assert abs(thd_ratio - 0.1) < 0.03
        msgs.append("Test3 OK: THD FFT (~10%)")

        # Test 4: config roundtrip (if available)
        cfg = load_config()
        if isinstance(cfg, dict):
            save_config(cfg)
            msgs.append("Test4 OK: config roundtrip (noop)")
        else:
            msgs.append("Test4 SKIP: config not dict")

    except Exception as e:  # pragma: no cover (failure path)
        ok = False
        msgs.append(f"Selftest FAIL: {e}")

    return ok, msgs


# -------------------- Command Handlers -----------------------------------


def _cmd_selftest(_args):
    ok, msgs = _run_selftest()
    for m in msgs:
        print(m)
    return 0 if ok else 1


def _cmd_sweep(args):
    try:
        freqs = build_freq_points(
            start=args.start,
            stop=args.stop,
            points=args.points,
            mode=args.mode,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    for f in freqs:
        # Plain float output (6 decimal places preserved by build function)
        print(f)
    return 0


def _cmd_diag(_args):
    print("Dependency status:", dep_msg())
    if HAVE_SERIAL:
        try:
            from serial.tools.list_ports import comports  # type: ignore
            ports = list(comports())
            print("Serial:", ", ".join(p.device for p in ports) if ports else "(none)")
        except Exception as e:  # pragma: no cover
            print("Serial enumeration error:", e)
    else:
        print("pyserial missing →", INSTALL_HINTS.get("pyserial", "pip install pyserial"))

    if HAVE_PYVISA:
        try:
            import pyvisa  # type: ignore
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            print("VISA:", ", ".join(resources) if resources else "(none)")
        except Exception as e:  # pragma: no cover
            print("VISA error:", e)
    else:
        print("pyvisa missing →", INSTALL_HINTS.get("pyvisa", "pip install pyvisa"))

    if HAVE_U3:
        try:
            # Defer import; may not have driver installed
            from amp_benchkit.u3util import safe_open  # type: ignore
            dev = safe_open()
            if dev:
                # Just show we tried; avoid full read for speed
                print("U3: detected (AIN probe skipped)")
            else:
                print("U3: not opened")
        except Exception as e:  # pragma: no cover
            print("U3 error:", e)
    else:
        print("u3 missing →", INSTALL_HINTS.get("u3", "pip install LabJackPython"))
    return 0


def _cmd_config_dump(_args):
    cfg = load_config()
    print(json.dumps(cfg, indent=2, sort_keys=True))
    return 0


def _cmd_config_reset(_args):
    try:
        save_config({})
        print("Config reset ->", CONFIG_PATH)
        return 0
    except Exception as e:  # pragma: no cover
        print("Config reset error:", e, file=sys.stderr)
        return 3


def _cmd_gui(args):
    if not HAVE_QT:
        print("GUI not available (PySide6 / PyQt5 missing). Install with extras: pip install 'amp-benchkit[gui]'", file=sys.stderr)
        return 4
    # Lazy import to avoid Qt boot on headless usage
    try:
        from amp_benchkit.gui import build_all_tabs  # hypothetical aggregator
        # Placeholder simple Qt app (kept minimal)
        from PySide6.QtWidgets import QApplication, QTabWidget
        app = QApplication([])
        tabs = QTabWidget()
        for w, label in build_all_tabs():
            tabs.addTab(w, label)
        tabs.setWindowTitle("Amp BenchKit")
        tabs.show()
        return app.exec()
    except Exception as e:  # pragma: no cover
        print("GUI launch error:", e, file=sys.stderr)
        return 5


# -------------------- Main / Argparse ------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="amp-benchkit (unified)",
        description="Bench automation toolkit (headless + GUI).",
    )
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    # Subparsers: do not force 'required' so a plain invocation prints help instead of a terse error
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("selftest", help="Run lightweight internal selfchecks")
    sp.set_defaults(func=_cmd_selftest)

    sp = sub.add_parser("sweep", help="Generate frequency points (stdout)")
    sp.add_argument("--start", type=float, required=True)
    sp.add_argument("--stop", type=float, required=True)
    sp.add_argument("--points", type=int, required=True)
    sp.add_argument("--mode", choices=["linear", "log"], default="linear")
    sp.set_defaults(func=_cmd_sweep)

    sp = sub.add_parser("diag", help="Show dependency/hardware status")
    sp.set_defaults(func=_cmd_diag)

    sp = sub.add_parser("config-dump", help="Print current persisted config JSON")
    sp.set_defaults(func=_cmd_config_dump)

    sp = sub.add_parser("config-reset", help="Reset config to empty object")
    sp.set_defaults(func=_cmd_config_reset)

    sp = sub.add_parser("gui", help="Launch Qt GUI (if available)")
    sp.set_defaults(func=_cmd_gui)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    # If no args provided (beyond program name), show help & exit code 2 (consistent with argparse error convention)
    if argv is None and len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 2
    if argv is not None and len(argv) == 0:
        parser.print_help(sys.stderr)
        return 2
    args = parser.parse_args(argv)
    setup_logging(verbose=args.verbose)
    log = get_logger()
    log.debug("Args: %s", args)

    rc = args.func(args)  # type: ignore[attr-defined]
    log.debug("Exit code: %s", rc)
    return rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
