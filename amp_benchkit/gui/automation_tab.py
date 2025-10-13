"""Automation / Sweep tab builder extracted from monolith.

Attaches widgets as attributes to the provided gui object for existing
methods (run_sweep_scope_fixed, run_audio_kpis, stop_sweep_scope).
"""

from __future__ import annotations

from typing import Any

from ..fy import FY_PROTOCOLS
from ._qt import require_qt


def build_automation_tab(gui: Any) -> object | None:
    qt = require_qt()
    if qt is None:
        return None
    QWidget = qt.QWidget
    QVBoxLayout = qt.QVBoxLayout
    QHBoxLayout = qt.QHBoxLayout
    QGroupBox = qt.QGroupBox
    QLabel = qt.QLabel
    QComboBox = qt.QComboBox
    QLineEdit = qt.QLineEdit
    QPushButton = qt.QPushButton
    QCheckBox = qt.QCheckBox
    QProgressBar = qt.QProgressBar
    QTextEdit = qt.QTextEdit
    w = QWidget()
    L = QVBoxLayout(w)
    # Top row: channel + metric selection
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
    r.addWidget(QLabel("Start Hz"))
    gui.auto_start = QLineEdit("100")
    r.addWidget(gui.auto_start)
    r.addWidget(QLabel("Stop Hz"))
    gui.auto_stop = QLineEdit("10000")
    r.addWidget(gui.auto_stop)
    r.addWidget(QLabel("Step Hz"))
    gui.auto_step = QLineEdit("100")
    r.addWidget(gui.auto_step)
    r.addWidget(QLabel("Amp Vpp"))
    gui.auto_amp = QLineEdit("0.25")
    r.addWidget(gui.auto_amp)
    r.addWidget(QLabel("Dwell ms"))
    gui.auto_dwell = QLineEdit("500")
    r.addWidget(gui.auto_dwell)
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
    # U3 orchestration row
    r4 = QHBoxLayout()
    r4.addWidget(QLabel("U3 Pulse Pin:"))
    gui.auto_u3_line = QComboBox()
    gui.auto_u3_line.addItems(
        ["None"]
        + [f"FIO{i}" for i in range(8)]
        + [f"EIO{i}" for i in range(8)]
        + [f"CIO{i}" for i in range(4)]
    )
    r4.addWidget(gui.auto_u3_line)
    r4.addWidget(QLabel("Width ms"))
    gui.auto_u3_pwidth = QLineEdit("10")
    gui.auto_u3_pwidth.setMaximumWidth(80)
    r4.addWidget(gui.auto_u3_pwidth)
    gui.auto_use_ext = QCheckBox("Use EXT Trigger")
    r4.addWidget(gui.auto_use_ext)
    r4.addWidget(QLabel("Slope"))
    gui.auto_ext_slope = QComboBox()
    gui.auto_ext_slope.addItems(["Rise", "Fall"])
    r4.addWidget(gui.auto_ext_slope)
    r4.addWidget(QLabel("Level V"))
    gui.auto_ext_level = QLineEdit("")
    gui.auto_ext_level.setMaximumWidth(80)
    r4.addWidget(gui.auto_ext_level)
    r4.addWidget(QLabel("Pre-arm ms"))
    gui.auto_ext_pre_ms = QLineEdit("5")
    gui.auto_ext_pre_ms.setMaximumWidth(80)
    r4.addWidget(gui.auto_ext_pre_ms)
    L.addLayout(r4)
    # U3 auto-config
    r4b = QHBoxLayout()
    gui.auto_u3_autocfg = QCheckBox("Auto-config U3 for run")
    gui.auto_u3_autocfg.setChecked(True)
    r4b.addWidget(gui.auto_u3_autocfg)
    r4b.addWidget(QLabel("Base"))
    gui.auto_u3_base = QComboBox()
    gui.auto_u3_base.addItems(["Keep Current", "Factory First"])
    r4b.addWidget(gui.auto_u3_base)
    L.addLayout(r4b)
    # Math
    r5 = QHBoxLayout()
    gui.auto_use_math = QCheckBox("Use MATH (CH1-CH2)")
    r5.addWidget(gui.auto_use_math)
    r5.addWidget(QLabel("Order"))
    gui.auto_math_order = QComboBox()
    gui.auto_math_order.addItems(["CH1-CH2", "CH2-CH1"])
    r5.addWidget(gui.auto_math_order)
    L.addLayout(r5)

    # Live testing group
    live_box = QGroupBox("Live Testing Functions")
    live_layout = QVBoxLayout(live_box)

    row = QHBoxLayout()
    row.addWidget(QLabel("Start Hz"))
    gui.live_thd_start = QLineEdit("20")
    gui.live_thd_start.setMaximumWidth(100)
    row.addWidget(gui.live_thd_start)
    row.addWidget(QLabel("Stop Hz"))
    gui.live_thd_stop = QLineEdit("20000")
    gui.live_thd_stop.setMaximumWidth(100)
    row.addWidget(gui.live_thd_stop)
    row.addWidget(QLabel("Points"))
    gui.live_thd_points = qt.QSpinBox()
    gui.live_thd_points.setRange(3, 999)
    gui.live_thd_points.setValue(61)
    row.addWidget(gui.live_thd_points)
    live_layout.addLayout(row)

    row = QHBoxLayout()
    row.addWidget(QLabel("Amp Vpp"))
    gui.live_thd_amp = QLineEdit("0.5")
    gui.live_thd_amp.setMaximumWidth(80)
    row.addWidget(gui.live_thd_amp)
    row.addWidget(QLabel("Dwell s"))
    gui.live_thd_dwell = QLineEdit("0.5")
    gui.live_thd_dwell.setMaximumWidth(80)
    row.addWidget(gui.live_thd_dwell)
    row.addWidget(QLabel("Scope CH"))
    gui.live_thd_scope = QComboBox()
    gui.live_thd_scope.addItems(["1", "2", "3", "4"])
    row.addWidget(gui.live_thd_scope)
    row.addWidget(QLabel("Math order"))
    gui.live_thd_math_order = QComboBox()
    gui.live_thd_math_order.addItems(["CH1-CH2", "CH2-CH1"])
    row.addWidget(gui.live_thd_math_order)
    gui.live_thd_use_math = QCheckBox("Use MATH")
    row.addWidget(gui.live_thd_use_math)
    live_layout.addLayout(row)

    row = QHBoxLayout()
    gui.live_thd_keep_spikes = QCheckBox("Keep raw spikes")
    row.addWidget(gui.live_thd_keep_spikes)
    row.addWidget(QLabel("Filter window"))
    gui.live_thd_filter_window = qt.QSpinBox()
    gui.live_thd_filter_window.setRange(1, 10)
    gui.live_thd_filter_window.setValue(2)
    row.addWidget(gui.live_thd_filter_window)
    row.addWidget(QLabel("Factor"))
    gui.live_thd_filter_factor = QLineEdit("2.0")
    gui.live_thd_filter_factor.setMaximumWidth(80)
    row.addWidget(gui.live_thd_filter_factor)
    row.addWidget(QLabel("Min %"))
    gui.live_thd_filter_min = QLineEdit("2.0")
    gui.live_thd_filter_min.setMaximumWidth(80)
    row.addWidget(gui.live_thd_filter_min)
    live_layout.addLayout(row)

    row = QHBoxLayout()
    row.addWidget(QLabel("Output"))
    gui.live_thd_output = QLineEdit("results/thd_sweep.csv")
    row.addWidget(gui.live_thd_output)
    live_layout.addLayout(row)

    gui.live_thd_summary = QTextEdit()
    gui.live_thd_summary.setReadOnly(True)
    live_layout.addWidget(gui.live_thd_summary)

    row = QHBoxLayout()
    gui.live_thd_run = QPushButton("Run THD Sweep")
    gui.live_thd_run.clicked.connect(gui.run_live_thd_sweep)
    row.addWidget(gui.live_thd_run)
    live_layout.addLayout(row)

    L.addWidget(live_box)
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
    # Progress + log
    gui.auto_prog = QProgressBar()
    L.addWidget(gui.auto_prog)
    gui.auto_log = QTextEdit()
    gui.auto_log.setReadOnly(True)
    L.addWidget(gui.auto_log)
    return w
