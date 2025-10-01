"""THD / Analysis tab.

Provides a real-time (timer-driven) THD readout. It attempts to:
1. Capture calibrated scope waveform if VISA + instrument available (best-effort).
2. Otherwise fall back to synthetic waveform generation for demonstrative purposes.

Design Principles (per contributor guide):
- No blocking I/O in constructor; all hardware access inside timer callback.
- Graceful degradation: if advanced DSP not available, shows 'stub'.
- Avoid hard failures if pyvisa / numpy missing; display status text instead.
"""
from __future__ import annotations
from typing import Any, Optional, Tuple
import math
import time
import threading
import queue

from ..deps import HAVE_PYVISA, HAVE_QT
from ..logging import get_logger
try:  # config persistence
    from ..config import load_config, update_config  # type: ignore
except Exception:  # pragma: no cover
    def load_config():  # type: ignore
        return {}

    def update_config(**kv):  # type: ignore
        return None

try:  # optional advanced DSP
    from .. import dsp_ext  # type: ignore
except Exception:  # pragma: no cover
    dsp_ext = None  # type: ignore

try:  # lightweight array fallback
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

from ._qt import require_qt

log = get_logger()


def _synthetic_wave(fs=50_000.0, f0=1000.0, n=2048):
    if np is None:
        # Return simple Python lists
        t = [i / fs for i in range(n)]
        v = [math.sin(2 * math.pi * f0 * ti) + 0.05 *
             math.sin(2 * math.pi * 2 * f0 * ti) for ti in t]
        return t, v
    t = np.arange(n) / fs
    v = np.sin(2 * math.pi * f0 * t) + 0.05 * np.sin(2 * math.pi * 2 * f0 * t)
    return t, v


def build_thd_tab(gui: Any) -> Optional[Any]:
    qt = require_qt()
    if qt is None:
        return None
    QWidget = qt.QWidget
    QVBoxLayout = qt.QVBoxLayout
    QHBoxLayout = qt.QHBoxLayout
    QLabel = qt.QLabel
    QPushButton = qt.QPushButton
    QLineEdit = qt.QLineEdit
    QTimer = qt.QTimer
    Qt = qt.Qt  # noqa: N816

    w = QWidget()
    L = QVBoxLayout(w)
    row = QHBoxLayout()
    row.addWidget(QLabel("Resource (VISA):"))
    gui.thd_scope_res = QLineEdit("USB::INSTR")
    gui.thd_scope_res.setMaximumWidth(200)
    row.addWidget(gui.thd_scope_res)
    row.addWidget(QLabel("f0 hint (Hz):"))
    gui.thd_f0 = QLineEdit("1000")
    gui.thd_f0.setMaximumWidth(100)
    row.addWidget(gui.thd_f0)
    row.addWidget(QLabel("Harmonics:"))
    gui.thd_nharm = QLineEdit("8")
    gui.thd_nharm.setMaximumWidth(60)
    row.addWidget(gui.thd_nharm)
    row.addWidget(QLabel("Refresh ms:"))
    gui.thd_refresh = QLineEdit("1000")
    gui.thd_refresh.setMaximumWidth(70)
    row.addWidget(gui.thd_refresh)
    L.addLayout(row)

    gui.thd_status = QLabel("Idle")
    L.addWidget(gui.thd_status)
    gui.thd_value = QLabel("THD: —")
    font = gui.thd_value.font()
    try:
        font.setPointSize(font.pointSize() + 2)
        gui.thd_value.setFont(font)
    except Exception:
        pass
    L.addWidget(gui.thd_value)

    btn_row = QHBoxLayout()
    gui.thd_start = QPushButton("Start")
    gui.thd_stop = QPushButton("Stop")
    gui.thd_export = QPushButton("Export Harmonics")
    gui.thd_spectrum = QPushButton("Show Spectrum")
    btn_row.addWidget(gui.thd_start)
    btn_row.addWidget(gui.thd_stop)
    btn_row.addWidget(gui.thd_export)
    btn_row.addWidget(gui.thd_spectrum)
    L.addLayout(btn_row)

    gui.thd_last_update = 0.0
    gui.thd_timer = QTimer()
    gui.thd_timer.setInterval(1000)  # 1 Hz refresh
    gui.thd_last_wave: Optional[Tuple[Any, Any]] = None
    gui.thd_capture_queue: "queue.Queue[Tuple[Any, Any]]" = queue.Queue(
        maxsize=1)
    gui.thd_capture_thread: Optional[threading.Thread] = None
    gui.thd_capture_stop = threading.Event()

    # Load persisted settings if present
    try:
        _cfg = load_config() or {}
        if 'thd_resource' in _cfg:
            gui.thd_scope_res.setText(str(_cfg['thd_resource']))
        if 'thd_f0' in _cfg:
            gui.thd_f0.setText(str(_cfg['thd_f0']))
        if 'thd_nharm' in _cfg:
            gui.thd_nharm.setText(str(_cfg['thd_nharm']))
        if 'thd_refresh' in _cfg:
            gui.thd_refresh.setText(str(_cfg['thd_refresh']))
    except Exception:  # pragma: no cover
        pass

    def _direct_capture():  # best-effort scope capture (blocking)
        if not HAVE_PYVISA or np is None:
            return _synthetic_wave()
        try:
            from unified_gui_layout import scope_capture_calibrated  # type: ignore
            t, v = scope_capture_calibrated(
                resource=gui.thd_scope_res.text().strip() or "USB::INSTR", ch=1)
            if len(t) < 16:
                return _synthetic_wave()
            return t, v
        except Exception as e:  # pragma: no cover
            log.debug("Scope capture fallback: %s", e)
            return _synthetic_wave()

    def _capture_worker():  # thread loop
        while not gui.thd_capture_stop.is_set():
            wave = _direct_capture()
            try:
                # replace old sample if queue full
                if gui.thd_capture_queue.full():
                    try:
                        gui.thd_capture_queue.get_nowait()
                    except Exception:
                        pass
                gui.thd_capture_queue.put_nowait(wave)
            except Exception:
                pass
            # Sleep a fraction of GUI refresh interval to avoid over-sampling
            time.sleep(max(0.1, gui.thd_timer.interval()/1000.0 * 0.5))

    def _compute_thd():
        f0_hint = None
        try:
            val = float(gui.thd_f0.text().strip())
            if val > 0:
                f0_hint = val
        except Exception:
            pass
        try:
            nharm = max(2, int(gui.thd_nharm.text().strip()))
        except Exception:
            nharm = 8
        if dsp_ext is None or np is None:
            gui.thd_value.setText("THD: stub (install dsp extra)")
            return
        # Pull latest waveform from queue or perform direct capture if none yet
        try:
            t, v = gui.thd_capture_queue.get_nowait()
        except Exception:
            t, v = _direct_capture()
        gui.thd_last_wave = (t, v)
        try:
            thd, f0_est, fund = dsp_ext.thd_fft_waveform(
                t, v, f0=f0_hint, nharm=nharm)
            if thd == thd:  # not NaN
                gui.thd_value.setText(
                    f"THD: {thd*100:.2f}%  f0={f0_est:.1f}Hz  fund={fund:.3f}")
            else:
                gui.thd_value.setText("THD: n/a")
        except Exception as e:  # pragma: no cover
            gui.thd_value.setText(f"THD error: {e}")
        return f0_hint, nharm, t, v

    def _tick():
        _compute_thd()
        gui.thd_status.setText(time.strftime("Last update %H:%M:%S"))

    gui.thd_timer.timeout.connect(_tick)  # type: ignore[attr-defined]

    def _start():
        if not gui.thd_timer.isActive():  # type: ignore[attr-defined]
            # Update interval from field
            try:
                iv = int(gui.thd_refresh.text().strip())
                if iv < 100:
                    iv = 100
                gui.thd_timer.setInterval(iv)
            except Exception:
                pass
            # Persist settings
            try:
                update_config(
                    thd_resource=gui.thd_scope_res.text().strip(),
                    thd_f0=gui.thd_f0.text().strip(),
                    thd_nharm=gui.thd_nharm.text().strip(),
                    thd_refresh=gui.thd_refresh.text().strip(),
                )
            except Exception:  # pragma: no cover
                pass
            # Start capture thread if not running
            if gui.thd_capture_thread is None or not gui.thd_capture_thread.is_alive():
                gui.thd_capture_stop.clear()
                gui.thd_capture_thread = threading.Thread(
                    target=_capture_worker, daemon=True)
                gui.thd_capture_thread.start()
            gui.thd_timer.start()
            _tick()

    def _stop():
        try:
            gui.thd_timer.stop()
        except Exception:
            pass
        try:
            gui.thd_capture_stop.set()
        except Exception:
            pass
        # join thread briefly
        try:
            if gui.thd_capture_thread and gui.thd_capture_thread.is_alive():
                gui.thd_capture_thread.join(timeout=0.5)
        except Exception:  # pragma: no cover
            pass

    gui.thd_start.clicked.connect(_start)
    gui.thd_stop.clicked.connect(_stop)

    def _export():
        if dsp_ext is None or np is None:
            gui.thd_status.setText("Export requires dsp extra")
            return
        try:
            f0_hint, nharm, t, v = _compute_thd()
            # Use estimated f0 for harmonic table if valid
            thd_txt = gui.thd_value.text()
            # crude parse to get f0_est
            f0_est = None
            if 'f0=' in thd_txt:
                try:
                    f0_est = float(thd_txt.split('f0=')[1].split('Hz')[0])
                except Exception:
                    pass
            table = dsp_ext.harmonic_table(
                t, v, f0=f0_est or f0_hint, nharm=nharm)
            # Write simple CSV
            import os
            os.makedirs('results', exist_ok=True)
            path = 'results/harmonics.csv'
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write('k,freq_hz,mag\n')
                for row in table:
                    fh.write(f"{row['k']},{row['freq_hz']},{row['mag']}\n")
            gui.thd_status.setText(f"Harmonics exported -> {path}")
        except Exception as e:  # pragma: no cover
            gui.thd_status.setText(f"Export error: {e}")

    gui.thd_export.clicked.connect(_export)

    def _show_spectrum():
        if np is None or dsp_ext is None:
            gui.thd_status.setText("Spectrum requires dsp + numpy")
            return
        if gui.thd_last_wave is None:
            gui.thd_status.setText("No waveform yet")
            return
        t, v = gui.thd_last_wave
        try:
            import numpy as _n  # type: ignore
            try:
                import matplotlib.pyplot as plt  # type: ignore
            except Exception as e:  # pragma: no cover
                gui.thd_status.setText(f"matplotlib missing: {e}")
                return
            # Compute magnitude spectrum
            arr_t = _n.asarray(t, dtype=float)
            arr_v = _n.asarray(v, dtype=float)
            dt = _n.median(_n.diff(arr_t)) if arr_t.size > 1 else 1.0
            freqs = _n.fft.rfftfreq(arr_v.size, d=dt)
            mags = _n.abs(_n.fft.rfft(arr_v))
            plt.figure()
            plt.semilogx(freqs + 1e-12, 20*_n.log10(_n.maximum(mags, 1e-18)))
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magnitude (dB)')
            plt.title('Waveform Spectrum')
            plt.grid(True, which='both', ls=':')
            import os
            try:
                cfg = load_config()
            except Exception:
                cfg = {}
            out_dir = cfg.get('results_dir', 'results')
            os.makedirs(out_dir, exist_ok=True)
            out = os.path.join(out_dir, 'spectrum.png')
            plt.savefig(out, bbox_inches='tight')
            plt.close()
            gui.thd_status.setText(f"Spectrum saved -> {out}")
        except Exception as e:  # pragma: no cover
            gui.thd_status.setText(f"Spectrum error: {e}")

    gui.thd_spectrum.clicked.connect(_show_spectrum)

    return w


__all__ = ["build_thd_tab"]
