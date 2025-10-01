"""Automation / Sweep tab builder extracted from monolith.

Attaches widgets as attributes to the provided gui object for existing
methods (run_sweep_scope_fixed, run_audio_kpis, stop_sweep_scope).
"""
from __future__ import annotations

from typing import Any

from ..fy import FY_PROTOCOLS  # type: ignore
from ._qt import require_qt


def build_automation_tab(gui: Any) -> object | None:
    qt = require_qt()
    if qt is None:
        return None
    QWidget=qt.QWidget; QVBoxLayout=qt.QVBoxLayout; QHBoxLayout=qt.QHBoxLayout
    QLabel=qt.QLabel; QComboBox=qt.QComboBox; QLineEdit=qt.QLineEdit; QPushButton=qt.QPushButton
    QCheckBox=qt.QCheckBox; QProgressBar=qt.QProgressBar; QTextEdit=qt.QTextEdit
    w = QWidget(); L = QVBoxLayout(w)
    # Top row: channel + metric selection
    r = QHBoxLayout(); r.addWidget(QLabel("FY Channel:")); gui.auto_ch = QComboBox(); gui.auto_ch.addItems(["1","2"]); r.addWidget(gui.auto_ch)
    r.addWidget(QLabel("Scope CH:")); gui.auto_scope_ch = QComboBox(); gui.auto_scope_ch.addItems(["1","2","3","4"]); r.addWidget(gui.auto_scope_ch)
    r.addWidget(QLabel("Metric:")); gui.auto_metric = QComboBox(); gui.auto_metric.addItems(["RMS","PK2PK"]); r.addWidget(gui.auto_metric); L.addLayout(r)
    # Override row
    r2 = QHBoxLayout(); r2.addWidget(QLabel("FY Port (override):")); gui.auto_port = QLineEdit(""); r2.addWidget(gui.auto_port)
    scan = QPushButton("Scan"); scan.clicked.connect(lambda: gui.scan_serial_into(gui.auto_port)); r2.addWidget(scan)
    r2.addWidget(QLabel("Protocol:")); gui.auto_proto = QComboBox(); gui.auto_proto.addItems(FY_PROTOCOLS); r2.addWidget(gui.auto_proto)
    L.addLayout(r2)
    # Sweep parameters
    r = QHBoxLayout(); r.addWidget(QLabel("Start Hz")); gui.auto_start = QLineEdit("100"); r.addWidget(gui.auto_start)
    r.addWidget(QLabel("Stop Hz")); gui.auto_stop = QLineEdit("10000"); r.addWidget(gui.auto_stop)
    r.addWidget(QLabel("Step Hz")); gui.auto_step = QLineEdit("100"); r.addWidget(gui.auto_step)
    r.addWidget(QLabel("Amp Vpp")); gui.auto_amp = QLineEdit("2.0"); r.addWidget(gui.auto_amp)
    r.addWidget(QLabel("Dwell ms")); gui.auto_dwell = QLineEdit("500"); r.addWidget(gui.auto_dwell); L.addLayout(r)
    # KPI options
    r3 = QHBoxLayout(); gui.auto_do_thd = QCheckBox("THD (FFT)"); r3.addWidget(gui.auto_do_thd)
    gui.auto_do_knees = QCheckBox("Find Knees"); r3.addWidget(gui.auto_do_knees)
    r3.addWidget(QLabel("Drop dB")); gui.auto_knee_db = QLineEdit("3.0"); gui.auto_knee_db.setMaximumWidth(80); r3.addWidget(gui.auto_knee_db)
    r3.addWidget(QLabel("Ref")); gui.auto_ref_mode = QComboBox(); gui.auto_ref_mode.addItems(["Max","1kHz"]); r3.addWidget(gui.auto_ref_mode)
    gui.auto_ref_hz = QLineEdit("1000"); gui.auto_ref_hz.setMaximumWidth(100); r3.addWidget(gui.auto_ref_hz)
    L.addLayout(r3)
    # U3 orchestration row
    r4 = QHBoxLayout(); r4.addWidget(QLabel("U3 Pulse Pin:")); gui.auto_u3_line = QComboBox(); gui.auto_u3_line.addItems(["None"]+[f"FIO{i}" for i in range(8)]+[f"EIO{i}" for i in range(8)]+[f"CIO{i}" for i in range(4)])
    r4.addWidget(gui.auto_u3_line); r4.addWidget(QLabel("Width ms")); gui.auto_u3_pwidth = QLineEdit("10"); gui.auto_u3_pwidth.setMaximumWidth(80); r4.addWidget(gui.auto_u3_pwidth)
    gui.auto_use_ext = QCheckBox("Use EXT Trigger"); r4.addWidget(gui.auto_use_ext)
    r4.addWidget(QLabel("Slope")); gui.auto_ext_slope = QComboBox(); gui.auto_ext_slope.addItems(["Rise","Fall"]); r4.addWidget(gui.auto_ext_slope)
    r4.addWidget(QLabel("Level V")); gui.auto_ext_level = QLineEdit(""); gui.auto_ext_level.setMaximumWidth(80); r4.addWidget(gui.auto_ext_level)
    r4.addWidget(QLabel("Pre-arm ms")); gui.auto_ext_pre_ms = QLineEdit("5"); gui.auto_ext_pre_ms.setMaximumWidth(80); r4.addWidget(gui.auto_ext_pre_ms)
    L.addLayout(r4)
    # U3 auto-config
    r4b = QHBoxLayout(); gui.auto_u3_autocfg = QCheckBox("Auto-config U3 for run"); gui.auto_u3_autocfg.setChecked(True); r4b.addWidget(gui.auto_u3_autocfg)
    r4b.addWidget(QLabel("Base")); gui.auto_u3_base = QComboBox(); gui.auto_u3_base.addItems(["Keep Current","Factory First"]); r4b.addWidget(gui.auto_u3_base)
    L.addLayout(r4b)
    # Math
    r5 = QHBoxLayout(); gui.auto_use_math = QCheckBox("Use MATH (CH1-CH2)"); r5.addWidget(gui.auto_use_math)
    r5.addWidget(QLabel("Order")); gui.auto_math_order = QComboBox(); gui.auto_math_order.addItems(["CH1-CH2","CH2-CH1"]); r5.addWidget(gui.auto_math_order)
    L.addLayout(r5)
    # Action buttons
    r = QHBoxLayout(); b = QPushButton("Run Sweep"); b.clicked.connect(gui.run_sweep_scope_fixed); r.addWidget(b)
    kb = QPushButton("Run KPIs"); kb.clicked.connect(gui.run_audio_kpis); r.addWidget(kb)
    sb = QPushButton("Stop"); sb.clicked.connect(gui.stop_sweep_scope); r.addWidget(sb); L.addLayout(r)
    # Progress + log
    gui.auto_prog = QProgressBar(); L.addWidget(gui.auto_prog)
    gui.auto_log = QTextEdit(); gui.auto_log.setReadOnly(True); L.addWidget(gui.auto_log)
    return w
