"""Qt import helper stub.
Returns None for require_qt() if Qt libs not installed, matching optional behavior.
"""
from __future__ import annotations
import os
import sys

def require_qt():  # pragma: no cover - trivial
    try:  # Attempt minimal import
        # Ensure headless friendly platform if not already specified
        if sys.platform == 'darwin':
            # 'minimal' tends to be more stable than 'offscreen' on headless macOS runners
            os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
            os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")
        else:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6 import QtWidgets, QtCore
        class QtWrapper:
            QWidget = QtWidgets.QWidget
            QTabWidget = QtWidgets.QTabWidget
            QVBoxLayout = QtWidgets.QVBoxLayout
            QHBoxLayout = QtWidgets.QHBoxLayout
            QLabel = QtWidgets.QLabel
            QCheckBox = QtWidgets.QCheckBox
            QSpinBox = QtWidgets.QSpinBox
            QPushButton = QtWidgets.QPushButton
            QTextEdit = QtWidgets.QTextEdit
            QLineEdit = QtWidgets.QLineEdit
            QComboBox = QtWidgets.QComboBox
            Qt = QtCore.Qt
            QTimer = QtCore.QTimer
        return QtWrapper
    except Exception:
        return None
