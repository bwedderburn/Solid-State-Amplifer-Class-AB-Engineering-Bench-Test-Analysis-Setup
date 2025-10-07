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
    QTextEdit = qt.QTextEdit
    QPushButton = qt.QPushButton
    w = QWidget()
    L = QVBoxLayout(w)
    gui.diag = QTextEdit()
    gui.diag.setReadOnly(True)
    L.addWidget(gui.diag)
    b = QPushButton("Run Diagnostics")
    b.clicked.connect(gui.run_diag)
    L.addWidget(b)
    return w
