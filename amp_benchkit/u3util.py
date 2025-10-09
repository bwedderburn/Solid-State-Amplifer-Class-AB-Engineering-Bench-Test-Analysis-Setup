"""LabJack U3 helper utilities.

Separates device opening and convenience wrappers from the monolithic GUI file.
USB functionality depends on Exodriver / liblabjackusb. Fail gracefully when absent.
"""

from __future__ import annotations

from .deps import HAVE_U3, U3_ERR, _u3

__all__ = [
    "have_u3",
    "open_u3_safely",
    "U3_ERR",
    "u3_open",
]


def have_u3():
    return HAVE_U3 and _u3 is not None


def open_u3_safely():
    if not have_u3():
        raise RuntimeError(f"LabJack U3 library unavailable: {U3_ERR}")
    return _u3.U3()


# ---- Wrappers used by extracted GUI tabs (mirroring legacy monolith helpers)
def u3_open():  # simple alias maintaining previous naming
    return open_u3_safely()
