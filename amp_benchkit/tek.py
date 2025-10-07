"""Tektronix scope helper functions.

Encapsulates SCPI setup and waveform capture logic used by the unified GUI.
Requires pyvisa to be available.
"""

from __future__ import annotations

from contextlib import suppress

import numpy as np

from .deps import HAVE_PYVISA, INSTALL_HINTS, _pyvisa

TEK_RSRC_DEFAULT = "USB0::0x0699::0x036A::C100563::INSTR"


class TekError(Exception):
    """Base exception for Tektronix scope operations."""


class TekTimeoutError(TekError):
    """Raised when a scope operation times out."""


__all__ = [
    "TEK_RSRC_DEFAULT",
    "tek_setup_channel",
    "tek_capture_block",
    "read_curve_block",
    "parse_ieee_block",
    "scope_set_trigger_ext",
    "scope_arm_single",
    "scope_wait_single_complete",
    "scope_configure_math_subtract",
    "scope_capture_calibrated",
    "scope_screenshot",
    "TekError",
    "TekTimeoutError",
]


def _need_pyvisa():  # internal guard
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")


def tek_setup_channel(sc, ch=1):
    sc.write("HEADER OFF")
    try:
        sc.write(f"DATA:SOURCE CH{ch}")
        sc.write("DATa:ENCdg RIBinary;WIDth 1")
        sc.write("DATA:START 1")
        sc.write("HORIZONTAL:RECORDLENGTH 10000")
        sc.write("ACQUIRE:STOPAFTER SEQUENCE")
        sc.write("ACQUIRE:STATE RUN")
    except Exception:
        pass


def parse_ieee_block(block: bytes):
    # Accept either raw numeric list (no #) or IEEE block (#4....)
    if not block:
        return np.array([])
    if block[:1] != b"#":
        try:
            txt = block.decode().strip()
            if txt and txt[0].isdigit():
                parts = [int(x) for x in txt.split(",") if x]
                return np.array(parts)
        except Exception:
            return np.array([])
        return np.array([])
    if len(block) < 2:
        return np.array([])
    n_dig = int(chr(block[1]))
    header = 2 + n_dig
    if len(block) < header:
        return np.array([])
    n_bytes = int(block[2 : 2 + n_dig])
    data = block[header : header + n_bytes]
    return np.frombuffer(data, dtype=np.int8)


def read_curve_block(sc):
    sc.write("CURVE?")
    block = sc.read_raw()
    return block


def tek_capture_block(resource, ch=1):
    _need_pyvisa()
    try:
        rm = _pyvisa.ResourceManager()
        sc = rm.open_resource(resource)
    except Exception as e:
        raise TekError(f"Failed to open scope resource '{resource}': {e}") from e
    try:
        tek_setup_channel(sc, ch)
        block = read_curve_block(sc)
        # Acquire scaling info
        try:
            ymult = float(sc.query("WFMPRE:YMULT?"))
            yoff = float(sc.query("WFMPRE:YOFF?"))
            yzero = float(sc.query("WFMPRE:YZERO?"))
            xincr = float(sc.query("WFMPRE:XINCR?"))
        except Exception:
            ymult = yoff = yzero = xincr = 1.0
        raw = parse_ieee_block(block)
        volts = (raw - yoff) * ymult + yzero
        t = np.arange(len(volts)) * xincr
        return t, volts, raw
    finally:
        with suppress(Exception):
            sc.close()


def scope_set_trigger_ext(resource=TEK_RSRC_DEFAULT, slope="RISE", level=None):
    _need_pyvisa()
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        s = str(slope).upper()
        s = "FALL" if s.startswith("F") else "RISE"
        cmds = [
            "TRIGger:MAIn:EDGE:SOURce EXT",
            "TRIGger:EDGE:SOURce EXT",
        ]
        for c in cmds:
            with suppress(Exception):
                sc.write(c)
        for c in (f"TRIGger:MAIn:EDGE:SLOPe {s}", f"TRIGger:EDGE:SLOPe {s}"):
            with suppress(Exception):
                sc.write(c)
        if level is not None:
            try:
                lv = float(level)
                for c in (
                    f"TRIGger:LEVel:EXTernal {lv}",
                    f"TRIGger:MAIn:LEVel:EXTernal {lv}",
                ):
                    with suppress(Exception):
                        sc.write(c)
            except Exception:
                pass
    finally:
        with suppress(Exception):
            sc.close()


def scope_arm_single(resource=TEK_RSRC_DEFAULT):
    _need_pyvisa()
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        for c in ("ACQuire:STOPAfter SEQuence", "ACQuire:STATE RUN"):
            with suppress(Exception):
                sc.write(c)
    finally:
        with suppress(Exception):
            sc.close()


def scope_wait_single_complete(resource=TEK_RSRC_DEFAULT, timeout_s=3.0, poll_ms=50):
    if not HAVE_PYVISA:
        return False
    try:
        rm = _pyvisa.ResourceManager()
        sc = rm.open_resource(resource)
    except Exception:
        return False
    import time as _t

    try:
        deadline = _t.time() + float(timeout_s)
        while _t.time() < deadline:
            with suppress(Exception):
                st = sc.query("ACQuire:STATE?").strip()
                if st in ("0", "STOP", "STOPPED"):
                    return True
                if st not in ("1", "RUN", "RUNNING"):
                    ts = sc.query("TRIGger:STATE?").strip().upper()
                    if ts in ("TRIGGERED", "STOP", "SAVE"):
                        return True
            _t.sleep(max(0.0, float(poll_ms) / 1000.0))
    finally:
        with suppress(Exception):
            sc.close()
    return False


def scope_configure_math_subtract(resource=TEK_RSRC_DEFAULT, order="CH1-CH2"):
    _need_pyvisa()
    order = (order or "CH1-CH2").upper()
    if order not in ("CH1-CH2", "CH2-CH1"):
        order = "CH1-CH2"
    a, b = order.split("-")
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
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
            with suppress(Exception):
                sc.write(c)
    finally:
        with suppress(Exception):
            sc.close()


def scope_capture_calibrated(resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1):
    _need_pyvisa()
    import numpy as _np

    try:
        rm = _pyvisa.ResourceManager()
        sc = rm.open_resource(resource)
    except Exception as e:
        raise TekError(f"Failed to open scope resource '{resource}': {e}") from e
    try:
        sc.timeout = int(timeout_ms)
        sc.chunk_size = max(getattr(sc, "chunk_size", 20480), 1048576)
        tek_setup_channel(sc, ch)
        ymult = float(sc.query("WFMPRE:YMULT?"))
        yzero = float(sc.query("WFMPRE:YZERO?"))
        yoff = float(sc.query("WFMPRE:YOFF?"))
        xincr = float(sc.query("WFMPRE:XINCR?"))
        block = read_curve_block(sc)
        data = _np.frombuffer(parse_ieee_block(block), dtype=_np.int8)
        volts = (data - yoff) * ymult + yzero
        t = _np.arange(data.size) * xincr
        return t.tolist(), volts.tolist()
    finally:
        with suppress(Exception):
            sc.close()


def scope_screenshot(
    filename="results/scope.png", resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1
):
    _need_pyvisa()
    import os

    import matplotlib.pyplot as _plt

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    t, v = scope_capture_calibrated(resource, timeout_ms, ch=ch)
    _plt.figure()
    _plt.plot(t, v)
    _plt.xlabel("Time (s)")
    _plt.ylabel("Voltage (V)")
    _plt.title(f"Scope CH{ch} Waveform")
    _plt.grid(True)
    _plt.savefig(filename, bbox_inches="tight")
    _plt.close()
    return filename
