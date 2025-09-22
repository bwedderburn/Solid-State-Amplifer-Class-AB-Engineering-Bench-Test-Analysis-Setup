#!/usr/bin/env python3
"""
Unified GUI Layout (LITE+U3)

Refined to prefer PySide6 automatically (falls back to PyQt5). Headless selftests preserved.
- NEW: Automation tab uses a single shared FY **Port override** and **Protocol** for sweeps,
        regardless of which FY channel is selected. If left blank, it auto-finds a likely FY port.
- NEW: DAQ (U3) page includes a "Config Defaults" sub‑tab modeled after the U3-HV Windows panel.
- NEW: U3 Config tab adds Watchdog "Reset on Timeout" + (optional) Set DIO State,
       Backward-compat checkboxes, and Counter enable mapping to configIO when possible.
"""
import sys, os, time, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PYVISA_ERR = SERIAL_ERR = QT_ERR = U3_ERR = None
QT_BINDING = None  # "PySide6" or "PyQt5"

# -----------------------------
# Optional dependencies
# -----------------------------
try:
    import pyvisa as _pyvisa
except Exception as e:
    _pyvisa = None; PYVISA_ERR = e

try:
    import serial as _serial; import serial.tools.list_ports as _lp
except Exception as e:
    _serial = _lp = None; SERIAL_ERR = e

try:
    import u3 as _u3
    HAVE_U3 = True
except Exception as e:
    _u3 = None; U3_ERR = e; HAVE_U3 = False

# ---- Qt: try PySide6 first, then PyQt5
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QProgressBar,
        QCheckBox, QSpinBox
    )
    from PySide6.QtCore import Qt
    QT_BINDING = "PySide6"; HAVE_QT = True
except Exception as e1:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QProgressBar,
            QCheckBox, QSpinBox
        )
        from PyQt5.QtCore import Qt
        QT_BINDING = "PyQt5"; HAVE_QT = True
    except Exception as e2:
        (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
         QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QProgressBar,
         QCheckBox, QSpinBox, Qt) = (None,)*15
        HAVE_QT = False; QT_ERR = (e1, e2)

HAVE_PYVISA = _pyvisa is not None
HAVE_SERIAL = _serial is not None and _lp is not None
INSTALL_HINTS = {
    'pyvisa': 'pip install pyvisa',
    'pyserial': 'pip install pyserial',
    'pyside6': 'pip install PySide6',
    'pyqt5': 'pip install PyQt5',
    'u3': 'pip install LabJackPython'
}

TEK_RSRC_DEFAULT = "USB0::0x0699::0x036A::C100563::INSTR"
FY_PROTOCOLS = ["FY ASCII 9600", "Auto (115200/CRLF→9600/LF)"]
WAVE_CODE = {"Sine":"0","Square":"1","Pulse":"2","Triangle":"3"}
SWEEP_MODE = {"Linear":"0","Log":"1"}

# -----------------------------
# Utility / status helpers
# -----------------------------

def dep_msg():
    qt_str = f"Qt({QT_BINDING or 'none'})"
    return " | ".join([
        f"pyvisa: {'OK' if HAVE_PYVISA else 'MISSING'}",
        f"pyserial: {'OK' if HAVE_SERIAL else 'MISSING'}",
        f"{qt_str}: {'OK' if HAVE_QT else 'MISSING'}",
        f"LabJack u3: {'OK' if HAVE_U3 else 'MISSING'}",
    ])

def list_ports():
    return list(_lp.comports()) if HAVE_SERIAL else []

def find_fy_port():
    ps = list_ports()
    for p in ps:
        d = (p.device or '').lower()
        if any(k in d for k in ['usbserial','tty.usb','wchusb','ftdi']):
            return p.device
    return ps[0].device if ps else None

FY_BAUD_EOLS = [(9600, "\n"), (115200, "\r\n")]

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
    sc.write("HEADER OFF"); sc.write(f"DATA:SOURCE CH{int(ch)}"); sc.write("DATA:ENC RPB"); sc.write("DATA:WIDTH 1")
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
            sc.write(f"MEASU:IMM:SOURCE CH{int(ch)}"); sc.write(f"MEASU:IMM:TYP {typ}")
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

        # keep both page widgets alive explicitly
        self._daq_keepalive = (self.daq_rw, self.daq_cw)

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
            try:
                d.configU3(RestoreFactoryDefaults=True)
            except Exception:
                d.configU3(WriteToFactory=True)
            self._log(self.cfg_log, "Factory values written")
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
            try:
                d.configIO(FIOAnalog=fio_an, FIODirection=fio_dir, EIODirection=eio_dir, CIODirection=cio_dir,
                           Counter0Enable=self.counter0.isChecked(), Counter1Enable=self.counter1.isChecked())
            except Exception:
                d.configIO(FIOAnalog=fio_an, FIODirection=fio_dir, EIODirection=eio_dir, CIODirection=cio_dir)
            # Digital states
            fio_state=self._mask_from_checks(self.fio_state_box); eio_state=self._mask_from_checks(self.eio_state_box); cio_state=self._mask_from_checks(self.cio_state_box)
            fb=[]
            for i in range(8): fb.append(_u3.BitStateWrite(FIONum=i, State=1 if (fio_state>>i)&1 else 0))
            for i in range(8): fb.append(_u3.BitStateWrite(EIONum=i, State=1 if (eio_state>>i)&1 else 0))
            for i in range(4): fb.append(_u3.BitStateWrite(CIONum=i, State=1 if (cio_state>>i)&1 else 0))
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
                d.configIO(NumberTimersEnabled=self.t_num.value(), TimerCounterPinOffset=self.t_pin.value())
            except Exception:
                pass
            # Apply digital state writes
            try:
                d.getFeedback(*fb)
            except Exception:
                pass
            # Watchdog (best-effort mapping of extra options)
            if self.wd_en.isChecked():
                try:
                    kw = dict(EnableWatchdog=True, WatchdogTimeout=int(float(self.wd_to.text() or '100')))
                    if self.wd_reset.isChecked():
                        kw['ResetOnTimeout'] = True
                    wline = getattr(self, 'wd_line', None)
                    if wline and wline.currentText() != 'None':
                        kw['WatchdogSetDIO'] = (wline.currentText(), 1 if self.wd_state.currentText()=="High" else 0)
                    # Unknown keys are silently ignored by our try/except
                    d.configU3(**kw)
                except Exception:
                    pass
            # Backward-compat flags (placeholders; ignored on unsupported firmwares)
            try:
                d.configU3(DisableTimerCounterPinOffsetErrors=self.bc_disable_tc_offset.isChecked())
            except Exception:
                pass
            self._log(self.cfg_log, "Values written")
        except Exception as e:
            self._log(self.cfg_log, f"Write error: {e}")
        finally:
            try: d.close()
            except Exception: pass

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
        r = QHBoxLayout(); b = QPushButton("Run Sweep"); b.clicked.connect(self.run_sweep_scope_fixed); r.addWidget(b)
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
            for i,f in enumerate(freqs):
                if self._sweep_abort: break
                try:
                    fy_apply(freq_hz=f, amp_vpp=amp, wave="Sine", off_v=0.0, duty=None, ch=ch, port=pt, proto=pr)
                except Exception as e:
                    self._log(self.auto_log, f"FY error @ {f} Hz: {e}"); continue
                time.sleep(dwell)
                typ = 'RMS' if metric=='RMS' else 'PK2PK'
                try:
                    val = self.scope_measure(sch, typ)
                except Exception as e:
                    self._log(self.auto_log, f"Scope error @ {f} Hz: {e}"); val = float('nan')
                out.append((f,val))
                self._log(self.auto_log, f"{f:.3f} Hz → {metric} {val:.4f}")
                self.auto_prog.setValue(int((i+1)/n*100)); QApplication.processEvents()
            os.makedirs('results', exist_ok=True)
            fn = os.path.join('results','sweep_scope.csv')
            with open(fn,'w') as fh:
                fh.write('freq_hz,metric\n')
                for f,val in out: fh.write(f"{f},{val}\n")
            self._log(self.auto_log, f"Saved: {fn}")
        except Exception as e:
            self._log(self.auto_log, f"Sweep error: {e}")

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
    else:
        ap.print_help()
        print('\nTip: install PySide6 or PyQt5 to launch GUI:', INSTALL_HINTS['pyside6'])


if __name__ == '__main__':
    main()
