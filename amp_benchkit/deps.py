"""Stub dependency detection module."""
from __future__ import annotations

HAVE_QT = False
HAVE_SERIAL = False
HAVE_PYVISA = False
HAVE_U3 = False

INSTALL_HINTS = {
    'pyserial': 'pip install pyserial',
    'pyvisa': 'pip install pyvisa',
    'LabJackPython': 'pip install LabJackPython',
    'qt': "pip install 'amp-benchkit[gui]'",
}

def dep_msg() -> str:
    return "Optional dependencies not installed (stub)."

def fixed_font():  # used by daq_tab
    return None
