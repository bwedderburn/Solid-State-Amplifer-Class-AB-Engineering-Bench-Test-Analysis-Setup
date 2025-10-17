"""DAQ (U3) tab builder extracted from monolithic GUI.

The builder attaches all created widgets as attributes on the passed `gui` object
(for compatibility with existing action/handler methods) and returns a QTabWidget
containing the three sub-tabs: Read/Stream, Config Defaults, Test Panel.
"""

from __future__ import annotations

from typing import Any

# NOTE: We intentionally avoid importing PySide6 at module import time so that
# headless test environments (no libEGL) can still import this module. The
# actual Qt classes are imported inside the builder. Reuse helpers lazily to
# avoid pulling heavy dependencies when the GUI is not in use.
from ..deps import fixed_font
from ._qt import require_qt


def build_daq_tab(gui: Any) -> object | None:
    qt = require_qt()
    if qt is None:
        return None
    QWidget = qt.QWidget
    QTabWidget = qt.QTabWidget
    QVBoxLayout = qt.QVBoxLayout
    QHBoxLayout = qt.QHBoxLayout
    QGridLayout = qt.QGridLayout
    QLabel = qt.QLabel
    QCheckBox = qt.QCheckBox
    QSpinBox = qt.QSpinBox
    QPushButton = qt.QPushButton
    QTextEdit = qt.QTextEdit
    QLineEdit = qt.QLineEdit
    QComboBox = qt.QComboBox
    Qt = qt.Qt
    # Provide no-op fallbacks for handler methods if the host GUI object does not
    # supply them (allows lightweight dummies in tests / partial embedding).
    _expected_handlers = [
        "read_daq_once",
        "read_daq_multi",
        "u3_write_factory",
        "u3_write_values",
        "u3_read_current",
        "apply_port_dir",
        "apply_port_state",
        "apply_all_ports",
        "load_masks_from_device",
        "fill_masks_from_checks",
        "reset_counter",
        "start_test_panel",
        "stop_test_panel",
    ]
    for _name in _expected_handlers:
        if not hasattr(gui, _name):
            setattr(gui, _name, lambda *a, **k: None)
    """Build the DAQ page (U3) with its sub-tabs and wire attributes onto `gui`.

    Returns the top-level QTabWidget that should be inserted into the main tab widget.
    """
    daq = QTabWidget()
    gui.daq_tabs = daq  # maintain attribute parity

    # --- Read/Stream tab
    gui.daq_rw = QWidget()
    L = QVBoxLayout(gui.daq_rw)

    # Detect U3 capabilities (hardware rev / HV) if gui exposes helper.
    caps_fn = getattr(gui, "_u3_capabilities", None)
    caps = caps_fn() if callable(caps_fn) else {}

    def _to_float(val):
        try:
            return float(val)
        except Exception:
            return None

    hw_version = _to_float(caps.get("hardware_version"))
    hw_is_130 = hw_version is not None and hw_version >= 1.30 - 1e-6
    is_hv = bool(caps.get("is_hv"))

    chan_wrap = QVBoxLayout()
    chan_wrap.addWidget(QLabel("Channels (AIN0–AIN15):"))
    chan_grid = QGridLayout()
    gui.chan_boxes = []
    for idx in range(16):
        cb = QCheckBox(f"AIN{idx}")
        if idx < 4:
            cb.setChecked(True)
            if is_hv:
                cb.setToolTip("AIN0–AIN3 fixed analog on U3-HV (datasheet §2.5)")
        gui.chan_boxes.append(cb)
        chan_grid.addWidget(cb, idx // 8, idx % 8)
    chan_wrap.addLayout(chan_grid)
    L.addLayout(chan_wrap)

    rr = QHBoxLayout()
    rr.addWidget(QLabel("Samples:"))
    gui.daq_nsamp = QSpinBox()
    gui.daq_nsamp.setRange(1, 10000)
    gui.daq_nsamp.setValue(1)
    rr.addWidget(gui.daq_nsamp)
    rr.addWidget(QLabel("Delay (ms):"))
    gui.daq_delay = QSpinBox()
    gui.daq_delay.setRange(0, 1000)
    gui.daq_delay.setValue(0)
    rr.addWidget(gui.daq_delay)
    rr.addWidget(QLabel("ResIdx:"))
    gui.daq_res = QSpinBox()
    gui.daq_res.setRange(0, 8)
    gui.daq_res.setValue(0)
    rr.addWidget(gui.daq_res)
    L.addLayout(rr)

    br = QHBoxLayout()
    b1 = QPushButton("Read Selected")
    b1.clicked.connect(gui.read_daq_once)
    br.addWidget(b1)
    b2 = QPushButton("Read Loop ×N")
    b2.clicked.connect(gui.read_daq_multi)
    br.addWidget(b2)
    L.addLayout(br)

    gui.daq_log = QTextEdit()
    gui.daq_log.setReadOnly(True)
    L.addWidget(gui.daq_log)

    daq.addTab(gui.daq_rw, "Read/Stream")

    # --- Config Defaults tab
    gui.daq_cw = QWidget()
    C = QVBoxLayout(gui.daq_cw)

    # Analog Input checkbox row
    C.addWidget(QLabel("FIO Analog Inputs (checked = Analog mode)"))
    fio_ai = QGridLayout()
    gui.ai_checks_fio = []
    for idx in range(8):
        cb = QCheckBox(f"AIN{idx}")
        default = idx < 4
        cb.setChecked(default)
        if is_hv and idx < 4:
            cb.setEnabled(False)
            cb.setToolTip("Fixed analog on U3-HV (AIN0–AIN3)")
        gui.ai_checks_fio.append(cb)
        fio_ai.addWidget(cb, idx // 4, idx % 4)
    C.addLayout(fio_ai)
    gui.ai_checks = gui.ai_checks_fio  # backward compatibility

    C.addWidget(QLabel("EIO Analog Inputs (checked = Analog mode)"))
    eio_ai = QGridLayout()
    gui.ai_checks_eio = []
    for idx in range(8):
        cb = QCheckBox(f"AIN{8 + idx}")
        gui.ai_checks_eio.append(cb)
        eio_ai.addWidget(cb, idx // 4, idx % 4)
    C.addLayout(eio_ai)

    def grid_dio(lbl: str, count: int):
        box = QVBoxLayout()
        box.addWidget(QLabel(lbl + " Direction (checked = Output)"))
        lay = QHBoxLayout()
        items = []
        for i in range(count):
            cb = QCheckBox(str(i))
            lay.addWidget(cb)
            items.append(cb)
        box.addLayout(lay)
        box2 = QVBoxLayout()
        box2.addWidget(QLabel(lbl + " State (checked = High)"))
        lay2 = QHBoxLayout()
        items2 = []
        for i in range(count):
            cb = QCheckBox(str(i))
            lay2.addWidget(cb)
            items2.append(cb)
        box2.addLayout(lay2)
        return box, items, box2, items2

    sec, gui.fio_dir_box, sec2, gui.fio_state_box = grid_dio("FIO", 8)
    C.addLayout(sec)
    C.addLayout(sec2)
    sec, gui.eio_dir_box, sec2, gui.eio_state_box = grid_dio("EIO", 8)
    C.addLayout(sec)
    C.addLayout(sec2)
    sec, gui.cio_dir_box, sec2, gui.cio_state_box = grid_dio("CIO", 4)
    C.addLayout(sec)
    C.addLayout(sec2)

    # Timers/Counters
    tc = QHBoxLayout()
    gui.t_pin = QSpinBox()
    if hw_is_130:
        gui.t_pin.setRange(4, 8)
        gui.t_pin.setValue(max(4, gui.t_pin.value()))
        gui.t_pin.setToolTip("Hardware 1.30+: timers/counters start at FIO4 (datasheet §5.2)")
    else:
        gui.t_pin.setRange(0, 16)
    gui.t_num = QSpinBox()
    gui.t_num.setRange(0, 6)
    gui.t_clkbase = QComboBox()
    gui.t_clkbase.addItems(["4MHz", "48MHz", "750kHz"])
    gui.t_div = QSpinBox()
    gui.t_div.setRange(0, 255)
    for lbl, wid in [
        ("PinOffset", gui.t_pin),
        ("#Timers", gui.t_num),
        ("TimerClockBase", gui.t_clkbase),
        ("Divisor", gui.t_div),
    ]:
        col = QVBoxLayout()
        lab = QLabel(lbl)
        lab.setAlignment(Qt.AlignHCenter)
        col.addWidget(lab)
        col.addWidget(wid)
        tc.addLayout(col)
    gui.counter0 = QCheckBox("Counter0 Enable")
    gui.counter1 = QCheckBox("Counter1 Enable")
    tc.addWidget(gui.counter0)
    tc.addWidget(gui.counter1)
    C.addWidget(QLabel("Timer/Counter"))
    C.addLayout(tc)

    # DAC outputs
    dac = QHBoxLayout()
    gui.dac0 = QLineEdit("0.0")
    gui.dac1 = QLineEdit("0.0")
    for lbl, w in [("DAC0 (V)", gui.dac0), ("DAC1 (V)", gui.dac1)]:
        col = QVBoxLayout()
        lab = QLabel(lbl)
        lab.setAlignment(Qt.AlignHCenter)
        col.addWidget(lab)
        col.addWidget(w)
        dac.addLayout(col)
    C.addLayout(dac)

    # Watchdog
    wd = QHBoxLayout()
    gui.wd_en = QCheckBox("Enable Watchdog")
    gui.wd_to = QLineEdit("100")
    gui.wd_reset = QCheckBox("Reset on Timeout")
    wd.addWidget(gui.wd_en)
    col = QVBoxLayout()
    lab = QLabel("Timeout sec")
    lab.setAlignment(Qt.AlignHCenter)
    col.addWidget(lab)
    col.addWidget(gui.wd_to)
    wd.addLayout(col)
    wd.addWidget(gui.wd_reset)
    gui.wd_line = QComboBox()
    gui.wd_line.addItems(
        ["None"]
        + [f"FIO{i}" for i in range(8)]
        + [f"EIO{i}" for i in range(8)]
        + [f"CIO{i}" for i in range(4)]
    )
    gui.wd_state = QComboBox()
    gui.wd_state.addItems(["Low", "High"])
    wd.addWidget(QLabel("Set DIO:"))
    wd.addWidget(gui.wd_line)
    wd.addWidget(gui.wd_state)
    C.addLayout(wd)

    # Backward-compat flags
    bc = QHBoxLayout()
    gui.bc_disable_tc_offset = QCheckBox("Disable Timer/Counter Offset Errors")
    gui.bc_force_dac8 = QCheckBox("Force 8-bit DAC Mode")
    bc.addWidget(gui.bc_disable_tc_offset)
    bc.addWidget(gui.bc_force_dac8)
    C.addLayout(bc)

    # Buttons
    btns = QHBoxLayout()
    rf = QPushButton("Write Factory Values")
    rf.clicked.connect(gui.u3_write_factory)
    rv = QPushButton("Write Values")
    rv.clicked.connect(gui.u3_write_values)
    rc = QPushButton("Read Current")
    rc.clicked.connect(gui.u3_read_current)
    for b in (rf, rv, rc):
        btns.addWidget(b)
    C.addLayout(btns)

    gui.cfg_log = QTextEdit()
    gui.cfg_log.setReadOnly(True)
    C.addWidget(gui.cfg_log)

    daq.addTab(gui.daq_cw, "Config Defaults")

    # --- Test Panel tab
    gui.daq_test = QWidget()
    T = QVBoxLayout(gui.daq_test)
    T.addWidget(QLabel("U3 Test Panel (runtime, non-persistent). Writes/reads ~1 Hz."))

    ain_row = QVBoxLayout()
    ain_row.addWidget(QLabel("AIN readings:"))
    ain_grid = QGridLayout()
    gui.test_ain_lbls = []
    for idx in range(16):
        label = QLabel(f"AIN{idx}")
        label.setAlignment(Qt.AlignHCenter)
        row = (idx // 8) * 2
        col = idx % 8
        ain_grid.addWidget(label, row, col)
        lbl = QLineEdit("—")
        lbl.setReadOnly(True)
        lbl.setMaximumWidth(90)
        gui.test_ain_lbls.append(lbl)
        ain_grid.addWidget(lbl, row + 1, col)
    ain_row.addLayout(ain_grid)
    T.addLayout(ain_row)

    def grid_test(lbl: str, count: int):
        box = QVBoxLayout()
        box.addWidget(QLabel(lbl + " (Dir/State/Readback)"))
        dir_row = QHBoxLayout()
        state_row = QHBoxLayout()
        rb_row = QHBoxLayout()
        dirs = []
        states = []
        rbs = []
        for i in range(count):
            dcb = QCheckBox(str(i))
            scb = QCheckBox(str(i))
            rcb = QCheckBox(str(i))
            rcb.setEnabled(False)
            dir_row.addWidget(dcb)
            state_row.addWidget(scb)
            rb_row.addWidget(rcb)
            dirs.append(dcb)
            states.append(scb)
            rbs.append(rcb)
        box.addWidget(QLabel("Direction (✓=Output)"))
        box.addLayout(dir_row)
        box.addWidget(QLabel("State (✓=High)"))
        box.addLayout(state_row)
        box.addWidget(QLabel("Readback (input/output actual)"))
        box.addLayout(rb_row)
        return box, dirs, states, rbs

    row_io = QHBoxLayout()
    sec, gui.test_fio_dir, gui.test_fio_state, gui.test_fio_rb = grid_test("FIO0-7", 8)
    row_io.addLayout(sec)
    sec2, gui.test_eio_dir, gui.test_eio_state, gui.test_eio_rb = grid_test("EIO0-7", 8)
    row_io.addLayout(sec2)
    sec3, gui.test_cio_dir, gui.test_cio_state, gui.test_cio_rb = grid_test("CIO0-3", 4)
    row_io.addLayout(sec3)
    T.addLayout(row_io)

    _ff = fixed_font()

    pm = QHBoxLayout()
    pm.addWidget(QLabel("Dir FIO"))
    gui.test_dir_fio = QLineEdit("0x00 (00000000)")
    gui.test_dir_fio.setReadOnly(True)
    gui.test_dir_fio.setMaximumWidth(140)
    pm.addWidget(gui.test_dir_fio)
    pm.addWidget(QLabel("EIO"))
    gui.test_dir_eio = QLineEdit("0x00 (00000000)")
    gui.test_dir_eio.setReadOnly(True)
    gui.test_dir_eio.setMaximumWidth(140)
    pm.addWidget(gui.test_dir_eio)
    pm.addWidget(QLabel("CIO"))
    gui.test_dir_cio = QLineEdit("0x00 (00000000)")
    gui.test_dir_cio.setReadOnly(True)
    gui.test_dir_cio.setMaximumWidth(140)
    pm.addWidget(gui.test_dir_cio)
    for fld in (gui.test_dir_fio, gui.test_dir_eio, gui.test_dir_cio):
        try:
            if _ff:
                fld.setFont(_ff)
        except Exception:
            pass
    T.addLayout(pm)

    pm2 = QHBoxLayout()
    pm2.addWidget(QLabel("State FIO"))
    gui.test_st_fio = QLineEdit("0x00 (00000000)")
    gui.test_st_fio.setReadOnly(True)
    gui.test_st_fio.setMaximumWidth(140)
    pm2.addWidget(gui.test_st_fio)
    pm2.addWidget(QLabel("EIO"))
    gui.test_st_eio = QLineEdit("0x00 (00000000)")
    gui.test_st_eio.setReadOnly(True)
    gui.test_st_eio.setMaximumWidth(140)
    pm2.addWidget(gui.test_st_eio)
    pm2.addWidget(QLabel("CIO"))
    gui.test_st_cio = QLineEdit("0x00 (00000000)")
    gui.test_st_cio.setReadOnly(True)
    gui.test_st_cio.setMaximumWidth(140)
    pm2.addWidget(gui.test_st_cio)
    for fld in (gui.test_st_fio, gui.test_st_eio, gui.test_st_cio):
        try:
            if _ff:
                fld.setFont(_ff)
        except Exception:
            pass
    T.addLayout(pm2)

    wrd = QHBoxLayout()
    wrd.addWidget(QLabel("Set Dir FIO"))
    gui.test_wdir_fio = QLineEdit("0x00")
    gui.test_wdir_fio.setMaximumWidth(100)
    wrd.addWidget(gui.test_wdir_fio)
    bdF = QPushButton("Apply")
    bdF.clicked.connect(lambda: gui.apply_port_dir("FIO"))
    wrd.addWidget(bdF)
    wrd.addWidget(QLabel("EIO"))
    gui.test_wdir_eio = QLineEdit("0x00")
    gui.test_wdir_eio.setMaximumWidth(100)
    wrd.addWidget(gui.test_wdir_eio)
    bdE = QPushButton("Apply")
    bdE.clicked.connect(lambda: gui.apply_port_dir("EIO"))
    wrd.addWidget(bdE)
    wrd.addWidget(QLabel("CIO"))
    gui.test_wdir_cio = QLineEdit("0x00")
    gui.test_wdir_cio.setMaximumWidth(100)
    wrd.addWidget(gui.test_wdir_cio)
    bdC = QPushButton("Apply")
    bdC.clicked.connect(lambda: gui.apply_port_dir("CIO"))
    wrd.addWidget(bdC)
    T.addLayout(wrd)

    wrs = QHBoxLayout()
    wrs.addWidget(QLabel("Set State FIO"))
    gui.test_wst_fio = QLineEdit("0x00")
    gui.test_wst_fio.setMaximumWidth(100)
    wrs.addWidget(gui.test_wst_fio)
    bsF = QPushButton("Apply")
    bsF.clicked.connect(lambda: gui.apply_port_state("FIO"))
    wrs.addWidget(bsF)
    wrs.addWidget(QLabel("EIO"))
    gui.test_wst_eio = QLineEdit("0x00")
    gui.test_wst_eio.setMaximumWidth(100)
    wrs.addWidget(gui.test_wst_eio)
    bsE = QPushButton("Apply")
    bsE.clicked.connect(lambda: gui.apply_port_state("EIO"))
    wrs.addWidget(bsE)
    wrs.addWidget(QLabel("CIO"))
    gui.test_wst_cio = QLineEdit("0x00")
    gui.test_wst_cio.setMaximumWidth(100)
    wrs.addWidget(gui.test_wst_cio)
    bsC = QPushButton("Apply")
    bsC.clicked.connect(lambda: gui.apply_port_state("CIO"))
    wrs.addWidget(bsC)
    T.addLayout(wrs)

    allr = QHBoxLayout()
    ball = QPushButton("Apply All (Dir+State)")
    ball.clicked.connect(gui.apply_all_ports)
    allr.addWidget(ball)
    bread = QPushButton("Read Masks from Device")
    bread.clicked.connect(gui.load_masks_from_device)
    allr.addWidget(bread)
    bfill = QPushButton("Masks ← Checkboxes")
    bfill.clicked.connect(gui.fill_masks_from_checks)
    allr.addWidget(bfill)
    T.addLayout(allr)

    ctrs = QHBoxLayout()
    ctrs.addWidget(QLabel("Counter0"))
    gui.test_c0 = QLineEdit("0")
    gui.test_c0.setReadOnly(True)
    gui.test_c0.setMaximumWidth(120)
    ctrs.addWidget(gui.test_c0)
    c0r = QPushButton("Reset C0")
    c0r.clicked.connect(lambda: gui.reset_counter(0))
    ctrs.addWidget(c0r)
    ctrs.addWidget(QLabel("Counter1"))
    gui.test_c1 = QLineEdit("0")
    gui.test_c1.setReadOnly(True)
    gui.test_c1.setMaximumWidth(120)
    ctrs.addWidget(gui.test_c1)
    c1r = QPushButton("Reset C1")
    c1r.clicked.connect(lambda: gui.reset_counter(1))
    ctrs.addWidget(c1r)
    T.addLayout(ctrs)

    dacr = QHBoxLayout()
    dacr.addWidget(QLabel("DAC0 (V)"))
    gui.test_dac0 = QLineEdit("0.0")
    gui.test_dac0.setMaximumWidth(100)
    dacr.addWidget(gui.test_dac0)
    dacr.addWidget(QLabel("DAC1 (V)"))
    gui.test_dac1 = QLineEdit("0.0")
    gui.test_dac1.setMaximumWidth(100)
    dacr.addWidget(gui.test_dac1)
    T.addLayout(dacr)

    ctr = QHBoxLayout()
    gui.test_factory = QCheckBox("Factory on Start")
    gui.test_factory.setChecked(True)
    ctr.addWidget(gui.test_factory)
    bstart = QPushButton("Start Panel")
    bstart.clicked.connect(gui.start_test_panel)
    ctr.addWidget(bstart)
    bstop = QPushButton("Stop Panel")
    bstop.clicked.connect(gui.stop_test_panel)
    ctr.addWidget(bstop)
    T.addLayout(ctr)

    sts = QHBoxLayout()
    sts.addWidget(QLabel("Last Error"))
    gui.test_last = QLineEdit("")
    gui.test_last.setReadOnly(True)
    sts.addWidget(gui.test_last)
    T.addLayout(sts)
    T.addWidget(QLabel("Error History"))
    gui.test_hist = QTextEdit()
    gui.test_hist.setReadOnly(True)
    gui.test_hist.setMaximumHeight(120)
    T.addWidget(gui.test_hist)
    gui.test_log = QTextEdit()
    gui.test_log.setReadOnly(True)
    T.addWidget(gui.test_log)

    daq.addTab(gui.daq_test, "Test Panel")

    # keep all pages alive
    gui._daq_keepalive = (gui.daq_rw, gui.daq_cw, gui.daq_test)

    return daq
