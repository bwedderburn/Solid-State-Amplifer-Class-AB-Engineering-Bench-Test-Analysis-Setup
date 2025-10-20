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
    "scope_capture_fft_trace",
    "scope_configure_timebase",
    "scope_read_timebase",
    "scope_resume_run",
    "scope_read_vertical_scale",
    "scope_set_vertical_scale",
    "scope_screenshot",
    "TekError",
    "TekTimeoutError",
]


def _need_pyvisa():  # internal guard
    if not HAVE_PYVISA:
        raise ImportError(f"pyvisa not available. {INSTALL_HINTS['pyvisa']}")


def _resolve_source(ch) -> str:
    """Normalize Tektronix DATA:SOURCE values."""
    if isinstance(ch, str):
        value = ch.strip().upper()
        if not value:
            return "CH1"
        if value in {"MATH", "REF1", "REF2", "REF3", "REF4"}:
            return value
        if value.startswith("CH") and value[2:].isdigit():
            return f"CH{int(value[2:])}"
        if value.isdigit():
            return f"CH{int(value)}"
        return "CH1"
    try:
        num = int(ch)
    except Exception:
        return "CH1"
    return f"CH{num}"


def tek_setup_channel(sc, ch=1):
    sc.write("HEADER OFF")
    source = _resolve_source(ch)
    try:
        sc.write(f"DATA:SOURCE {source}")
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


def scope_read_timebase(resource=TEK_RSRC_DEFAULT):
    """Return current horizontal scale in seconds/div (None on failure)."""
    if not HAVE_PYVISA:
        return None
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        try:
            return float(sc.query("HORizontal:MAIn:SCAle?"))
        except Exception:
            return None
    finally:
        with suppress(Exception):
            sc.close()


def scope_configure_timebase(resource=TEK_RSRC_DEFAULT, seconds_per_div=None):
    """Adjust horizontal scale (seconds per division)."""
    if not HAVE_PYVISA or seconds_per_div is None:
        return
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        with suppress(Exception):
            sc.write("HORizontal:MODE MAIn")
        sc.write(f"HORizontal:MAIn:SCAle {float(seconds_per_div)}")
    finally:
        with suppress(Exception):
            sc.close()


def scope_resume_run(resource=TEK_RSRC_DEFAULT):
    """Return the scope to continuous acquisition (RUN) mode."""
    if not HAVE_PYVISA:
        return
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        for cmd in ("ACQuire:STOPAfter RUNSTop", "ACQuire:STATE RUN"):
            with suppress(Exception):
                sc.write(cmd)
    finally:
        with suppress(Exception):
            sc.close()


def scope_read_vertical_scale(resource=TEK_RSRC_DEFAULT, ch=1):
    """Return current vertical scale (V/div) for the requested channel."""
    if not HAVE_PYVISA:
        return None
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        src = _resolve_source(ch)
        if src == "MATH":
            return float(sc.query("MATH:VERTICAL:SCALE?"))
        return float(sc.query(f"{src}:SCALE?"))
    except Exception:
        return None
    finally:
        with suppress(Exception):
            sc.close()


def scope_set_vertical_scale(resource=TEK_RSRC_DEFAULT, ch=1, volts_per_div=1.0):
    """Set vertical scale (V/div) for the requested channel."""
    if not HAVE_PYVISA:
        return
    rm = _pyvisa.ResourceManager()
    sc = rm.open_resource(resource)
    try:
        src = _resolve_source(ch)
        value = max(1e-6, float(volts_per_div))
        cmd = "MATH:VERTICAL:SCALE" if src == "MATH" else f"{src}:SCALE"
        sc.write(f"{cmd} {value}")
    finally:
        with suppress(Exception):
            sc.close()


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
    """Capture a calibrated waveform for the requested source.

    Supports integer channels (1-4) or source names like 'MATH'.
    """
    _need_pyvisa()
    import numpy as _np

    try:
        rm = _pyvisa.ResourceManager()
        sc = rm.open_resource(resource)
    except Exception as e:
        raise TekError(f"Failed to open scope resource '{resource}': {e}") from e
    try:
        try:
            sc.timeout = int(float(timeout_ms))
        except Exception:
            sc.timeout = 15000
        sc.chunk_size = max(getattr(sc, "chunk_size", 20480), 1048576)
        tek_setup_channel(sc, ch)
        ymult = float(sc.query("WFMPRE:YMULT?"))
        yzero = float(sc.query("WFMPRE:YZERO?"))
        yoff = float(sc.query("WFMPRE:YOFF?"))
        xincr = float(sc.query("WFMPRE:XINCR?"))
        try:
            xzero = float(sc.query("WFMPRE:XZERO?"))
        except Exception:
            xzero = 0.0
        block = read_curve_block(sc)
        data = _np.frombuffer(parse_ieee_block(block), dtype=_np.int8)
        volts = (data - yoff) * ymult + yzero
        t = xzero + _np.arange(data.size) * xincr
        return t.tolist(), volts.tolist()
    finally:
        with suppress(Exception):
            sc.close()


def scope_capture_fft_trace(
    resource=TEK_RSRC_DEFAULT,
    source=1,
    *,
    window="HANNING",
    scale="DB",
    timeout_ms=15000,
):
    """Capture the Tek FFT (math) trace as frequency/amplitude arrays.

    Parameters
    ----------
    resource : str
        VISA resource identifier for the scope.
    source : int | str
        Base channel feeding the FFT (e.g. 1, "CH2").
    window : str
        FFT window. Accepted values: rectangular, hanning, hamming, blackman.
    scale : str
        FFT vertical scale. Accepted values: linear, db.
    timeout_ms : int
        VISA timeout for the transfer.

    Returns
    -------
    dict
        {"freqs": [...], "values": [...], "x_unit": "Hz", "y_unit": "dB" or "V"}.
    """

    _need_pyvisa()
    import numpy as _np

    window_map = {
        "RECT": "RECTANGULAR",
        "RECTANGULAR": "RECTANGULAR",
        "RECTANGLE": "RECTANGULAR",
        "HANN": "HANNING",
        "HANNING": "HANNING",
        "HAMM": "HAMMING",
        "HAMMING": "HAMMING",
        "BLACK": "BLACKMAN",
        "BLACKMAN": "BLACKMAN",
    }
    scale_map = {
        "LIN": "LINEAR",
        "LINEAR": "LINEAR",
        "DB": "DB",
        "DBM": "DB",
        "DECIBEL": "DB",
    }
    src = _resolve_source(source)
    win_key = window.upper().strip()
    scl_key = scale.upper().strip()
    win_cmd = window_map.get(win_key, window_map.get(win_key.rstrip("G"), "HANNING"))
    if win_cmd not in window_map.values():
        raise TekError(f"Unsupported FFT window '{window}'")
    scale_cmd = scale_map.get(scl_key)
    if scale_cmd is None:
        raise TekError(f"Unsupported FFT scale '{scale}'")

    try:
        rm = _pyvisa.ResourceManager()
        sc = rm.open_resource(resource)
    except Exception as e:
        raise TekError(f"Failed to open scope resource '{resource}': {e}") from e
    try:
        try:
            sc.timeout = int(float(timeout_ms))
        except Exception:
            sc.timeout = 15000
        sc.chunk_size = max(getattr(sc, "chunk_size", 20480), 1048576)
        sc.write("HEADER OFF")
        # Configure FFT math trace
        with suppress(Exception):
            sc.write("MATH:DEFINE FFT")
        with suppress(Exception):
            sc.write(f"MATH:SOURCE1 {src}")
        with suppress(Exception):
            sc.write(f"MATH:SOUrce {src}")
        with suppress(Exception):
            sc.write(f"MATH:FFT:SOURCE {src}")
        with suppress(Exception):
            sc.write(f"MATH:FFT:WINDOW {win_cmd}")
        with suppress(Exception):
            sc.write(f"MATH:FFT:SCALE {scale_cmd}")
        with suppress(Exception):
            sc.write("MATH:FFT:STATE ON")
        sc.write("DATA:SOURCE MATH")
        sc.write("DATa:ENCdg RIBinary;WIDth 1")
        sc.write("DATA:START 1")
        sc.write("ACQUIRE:STOPAFTER SEQUENCE")
        sc.write("ACQUIRE:STATE RUN")
        ymult = float(sc.query("WFMPRE:YMULT?"))
        yzero = float(sc.query("WFMPRE:YZERO?"))
        yoff = float(sc.query("WFMPRE:YOFF?"))
        xincr = float(sc.query("WFMPRE:XINCR?"))
        try:
            xzero = float(sc.query("WFMPRE:XZERO?"))
        except Exception:
            xzero = 0.0
        try:
            xunit = sc.query("WFMPRE:XUNIT?").strip()
        except Exception:
            xunit = "Hz"
        try:
            yunit = sc.query("WFMPRE:YUNIT?").strip()
        except Exception:
            yunit = "dB" if scale_cmd == "DB" else "V"
        block = read_curve_block(sc)
        raw = parse_ieee_block(block)
        data = raw.astype(_np.float64, copy=False)
        values = (data - yoff) * ymult + yzero
        freqs = xzero + _np.arange(values.size) * xincr
        return {
            "freqs": freqs.tolist(),
            "values": values.tolist(),
            "x_unit": xunit or "Hz",
            "y_unit": yunit or ("dB" if scale_cmd == "DB" else "V"),
        }
    finally:
        with suppress(Exception):
            sc.write("MATH:FFT:STATE OFF")
        with suppress(Exception):
            sc.close()


def scope_screenshot(
    filename="results/scope.png", resource=TEK_RSRC_DEFAULT, timeout_ms=15000, ch=1
):
    _need_pyvisa()
    import os

    import matplotlib.pyplot as _plt

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    src_label = _resolve_source(ch)
    t, v = scope_capture_calibrated(resource, timeout_ms, ch=ch)
    _plt.figure()
    _plt.plot(t, v)
    _plt.xlabel("Time (s)")
    _plt.ylabel("Voltage (V)")
    _plt.title(f"Scope {src_label} Waveform")
    _plt.grid(True)
    _plt.savefig(filename, bbox_inches="tight")
    _plt.close()
    return filename
