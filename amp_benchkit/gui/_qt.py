"""Qt import helper stub.
Returns None for require_qt() if Qt libs not installed, matching optional behavior.
"""
from __future__ import annotations

def require_qt():  # pragma: no cover - trivial
    try:  # Attempt minimal import
        from PySide6 import QtWidgets, QtCore
        class QTWrap:
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
        return QTWrap
    except Exception:
        return None
