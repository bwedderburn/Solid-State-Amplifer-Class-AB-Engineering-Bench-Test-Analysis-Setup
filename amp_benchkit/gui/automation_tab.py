"""Automation / Sweep tab builder extracted from monolith.

Attaches widgets as attributes to the provided gui object for existing
methods (run_sweep_scope_fixed, run_audio_kpis, stop_sweep_scope).
"""
from __future__ import annotations

from ..fy import FY_PROTOCOLS  # type: ignore
from ._qt import require_qt
from typing import Any, Optional


def build_automation_tab(gui: Any) -> Optional[object]:
    qt = require_qt()
    if qt is None:
        return None
    QWidget = qt.QWidget
    QVBoxLayout = qt.QVBoxLayout
    QHBoxLayout = qt.QHBoxLayout
    QLabel = qt.QLabel
    QComboBox = qt.QComboBox
    QLineEdit = qt.QLineEdit
    QPushButton = qt.QPushButton
    QCheckBox = qt.QCheckBox
    QTextEdit = qt.QTextEdit

    w = QWidget()
    L = QVBoxLayout(w)

    # Top row
    r = QHBoxLayout()
    r.addWidget(QLabel("FY Channel:"))
    gui.auto_ch = QComboBox()
    gui.auto_ch.addItems(["1", "2"])
    r.addWidget(gui.auto_ch)
    r.addWidget(QLabel("Scope CH:"))
    gui.auto_scope_ch = QComboBox()
    gui.auto_scope_ch.addItems(["1", "2", "3", "4"])
    r.addWidget(gui.auto_scope_ch)
    r.addWidget(QLabel("Metric:"))
    gui.auto_metric = QComboBox()
    gui.auto_metric.addItems(["RMS", "PK2PK"])
    r.addWidget(gui.auto_metric)
    L.addLayout(r)

    # Override row
    r2 = QHBoxLayout()
    r2.addWidget(QLabel("FY Port (override):"))
    gui.auto_port = QLineEdit("")
    r2.addWidget(gui.auto_port)
    if not hasattr(gui, 'scan_serial_into'):
        setattr(gui, 'scan_serial_into', lambda *_a, **_k: None)
    scan = QPushButton("Scan")
    scan.clicked.connect(lambda: gui.scan_serial_into(gui.auto_port))
    r2.addWidget(scan)
    r2.addWidget(QLabel("Protocol:"))
    gui.auto_proto = QComboBox()
    gui.auto_proto.addItems(FY_PROTOCOLS)
    r2.addWidget(gui.auto_proto)
    L.addLayout(r2)

    # Sweep parameters
    r = QHBoxLayout()
    for label, attr, default in [
        ("Start Hz", 'auto_start', "100"),
        ("Stop Hz", 'auto_stop', "10000"),
        ("Step Hz", 'auto_step', "100"),
        ("Amp Vpp", 'auto_amp', "2.0"),
        ("Dwell ms", 'auto_dwell', "500"),
    ]:
        r.addWidget(QLabel(label))
        line = QLineEdit(default)
        setattr(gui, attr, line)
        r.addWidget(line)
    L.addLayout(r)

    # KPI options
    r3 = QHBoxLayout()
    gui.auto_do_thd = QCheckBox("THD (FFT)")
    r3.addWidget(gui.auto_do_thd)
    gui.auto_do_knees = QCheckBox("Find Knees")
    r3.addWidget(gui.auto_do_knees)
    r3.addWidget(QLabel("Drop dB"))
    gui.auto_knee_db = QLineEdit("3.0")
    gui.auto_knee_db.setMaximumWidth(80)
    r3.addWidget(gui.auto_knee_db)
    r3.addWidget(QLabel("Ref"))
    gui.auto_ref_mode = QComboBox()
    gui.auto_ref_mode.addItems(["Max", "1kHz"])
    r3.addWidget(gui.auto_ref_mode)
    gui.auto_ref_hz = QLineEdit("1000")
    gui.auto_ref_hz.setMaximumWidth(100)
    r3.addWidget(gui.auto_ref_hz)
    L.addLayout(r3)

    # U3 stub row (minimal for tests)
    r4 = QHBoxLayout()
    r4.addWidget(QLabel("U3 Pulse Pin:"))
    gui.auto_u3_line = QComboBox()
    gui.auto_u3_line.addItems(["None"])
    r4.addWidget(gui.auto_u3_line)
    L.addLayout(r4)

    # Math options
    r5 = QHBoxLayout()
    gui.auto_use_math = QCheckBox("Use MATH (CH1-CH2)")
    r5.addWidget(gui.auto_use_math)
    r5.addWidget(QLabel("Order"))
    gui.auto_math_order = QComboBox()
    gui.auto_math_order.addItems(["CH1-CH2", "CH2-CH1"])
    r5.addWidget(gui.auto_math_order)
    L.addLayout(r5)

    # Safe fallbacks for run handlers
    for handler in ["run_sweep_scope_fixed", "run_audio_kpis", "stop_sweep_scope"]:
        if not hasattr(gui, handler):
            setattr(gui, handler, lambda *_a, **_k: None)

    # Action buttons
    r = QHBoxLayout()
    b = QPushButton("Run Sweep")
    b.clicked.connect(gui.run_sweep_scope_fixed)
    r.addWidget(b)
    kb = QPushButton("Run KPIs")
    kb.clicked.connect(gui.run_audio_kpis)
    r.addWidget(kb)
    sb = QPushButton("Stop")
    sb.clicked.connect(gui.stop_sweep_scope)
    r.addWidget(sb)
    L.addLayout(r)

    # Progress + log placeholders
    gui.auto_prog = QTextEdit()
    gui.auto_prog.setReadOnly(True)
    L.addWidget(gui.auto_prog)
    gui.auto_log = QTextEdit()
    gui.auto_log.setReadOnly(True)
    L.addWidget(gui.auto_log)
    return w
