"""Internal Qt helper for lazy, headless-safe access.

Provides a single function `require_qt()` that attempts to import the Qt
widgets we rely on and returns a namespace-like simple object with the
symbols. If Qt is unavailable, returns None so callers can skip.
"""
from __future__ import annotations

from types import SimpleNamespace


def require_qt():  # pragma: no cover - thin import wrapper
    """Attempt to import Qt widgets from PySide6, falling back to PyQt5.

    Returns a SimpleNamespace of required classes or None if neither binding
    is available. This avoids import-time crashes in headless test runs.
    """
    binding = None
    try:  # Prefer PySide6
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QProgressBar,
            QPushButton,
            QSpinBox,
            QTabWidget,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
        binding = 'PySide6'
    except Exception:
        try:  # Fallback to PyQt5
            from PyQt5.QtCore import Qt, QTimer
            from PyQt5.QtWidgets import (
                QCheckBox,
                QComboBox,
                QHBoxLayout,
                QLabel,
                QLineEdit,
                QProgressBar,
                QPushButton,
                QSpinBox,
                QTabWidget,
                QTextEdit,
                QVBoxLayout,
                QWidget,
            )
            binding = 'PyQt5'
        except Exception:
            return None
    return SimpleNamespace(
        QWidget=QWidget,
        QVBoxLayout=QVBoxLayout,
        QHBoxLayout=QHBoxLayout,
        QLabel=QLabel,
        QComboBox=QComboBox,
        QLineEdit=QLineEdit,
        QPushButton=QPushButton,
        QTextEdit=QTextEdit,
        QTabWidget=QTabWidget,
        QProgressBar=QProgressBar,
        QCheckBox=QCheckBox,
        QSpinBox=QSpinBox,
        Qt=Qt,
        QTimer=QTimer,
        __binding__=binding,
    )
