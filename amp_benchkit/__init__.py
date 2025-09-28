"""amp_benchkit package

Initial refactor step: host shared dependency detection and helper utilities
previously embedded in the monolithic unified_gui_layout.py.
"""
from .deps import (
    HAVE_PYVISA, HAVE_SERIAL, HAVE_QT, HAVE_U3,
    QT_BINDING, QT_ERR, PYVISA_ERR, SERIAL_ERR, U3_ERR,
    dep_msg, list_ports, find_fy_port,
)

__all__ = [
    'HAVE_PYVISA','HAVE_SERIAL','HAVE_QT','HAVE_U3','QT_BINDING','QT_ERR','PYVISA_ERR',
    'SERIAL_ERR','U3_ERR','dep_msg','list_ports','find_fy_port','__version__'
]

# Synchronized with pyproject.toml version
__version__ = '0.2.0'
