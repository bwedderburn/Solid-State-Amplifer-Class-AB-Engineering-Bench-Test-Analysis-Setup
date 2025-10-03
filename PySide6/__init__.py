# Minimal PySide6 stub for headless test avoidance
from .QtWidgets import (
    QApplication,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSpinBox,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QComboBox,
)


class QtCore:
    class Qt:
        AlignHCenter = 0x0004

    class QTimer:
        pass


__all__ = [
    'QApplication',
    'QWidget',
    'QTabWidget',
    'QVBoxLayout',
    'QHBoxLayout',
    'QLabel',
    'QCheckBox',
    'QSpinBox',
    'QPushButton',
    'QTextEdit',
    'QLineEdit',
    'QComboBox',
    'QtCore',
]
