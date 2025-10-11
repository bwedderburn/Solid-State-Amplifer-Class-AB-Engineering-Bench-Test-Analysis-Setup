"""Diagnostics tab builder extracted from monolith.

Provides a simple text area and a button to invoke existing run_diag method.
Imports Qt lazily to remain headless-test friendly.
"""

from __future__ import annotations

from typing import Any

from ._qt import require_qt


def build_diagnostics_tab(gui: Any) -> object | None:
    qt = require_qt()
    if qt is None:
        return None
    QWidget = qt.QWidget
    QVBoxLayout = qt.QVBoxLayout
    QHBoxLayout = qt.QHBoxLayout
    QTextEdit = qt.QTextEdit
    QPushButton = qt.QPushButton
    QCheckBox = qt.QCheckBox
    QSizePolicy = getattr(qt, "QSizePolicy", None)
    w = QWidget()
    L = QVBoxLayout(w)
    # Options row
    opt_row = QHBoxLayout()
    gui.diag_include_env = QCheckBox("Environment")
    gui.diag_include_env.setChecked(True)
    opt_row.addWidget(gui.diag_include_env)
    gui.diag_include_deps = QCheckBox("Dependencies")
    gui.diag_include_deps.setChecked(True)
    opt_row.addWidget(gui.diag_include_deps)
    gui.diag_include_hw = QCheckBox("Hardware probes")
    gui.diag_include_hw.setChecked(True)
    opt_row.addWidget(gui.diag_include_hw)
    gui.diag_auto_clear = QCheckBox("Clear before capture")
    gui.diag_auto_clear.setChecked(False)
    opt_row.addWidget(gui.diag_auto_clear)
    opt_row.addStretch()
    L.addLayout(opt_row)
    # Button row
    btn_row = QHBoxLayout()
    run_btn = QPushButton("Run Diagnostics")
    run_btn.clicked.connect(gui.run_diag)
    btn_row.addWidget(run_btn)
    save_btn = QPushButton("Save Snapshot")
    save_btn.clicked.connect(lambda: getattr(gui, "save_diag_snapshot", lambda: None)())
    btn_row.addWidget(save_btn)
    copy_btn = QPushButton("Copy to Clipboard")
    copy_btn.clicked.connect(lambda: getattr(gui, "copy_diag_to_clipboard", lambda: None)())
    btn_row.addWidget(copy_btn)
    clear_btn = QPushButton("Clear Log")
    clear_btn.clicked.connect(lambda: getattr(gui, "clear_diag_log", lambda: None)())
    btn_row.addWidget(clear_btn)
    btn_row.addStretch()
    L.addLayout(btn_row)
    gui.diag = QTextEdit()
    gui.diag.setReadOnly(True)
    if QSizePolicy is not None:
        gui.diag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    L.addWidget(gui.diag)
    return w
