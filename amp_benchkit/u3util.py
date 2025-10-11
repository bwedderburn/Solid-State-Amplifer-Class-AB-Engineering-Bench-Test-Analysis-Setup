"""LabJack U3 device connection utilities.

Provides low-level device opening and availability checking.
For I/O operations (reading analog inputs, setting digital lines, etc.),
use :mod:`amp_benchkit.u3config` instead.

USB functionality depends on Exodriver / liblabjackusb. Fail gracefully when absent.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager

from .deps import HAVE_U3, U3_ERR, _u3

__all__ = [
    "have_u3",
    "open_u3_safely",
    "U3_ERR",
    "u3_open",
]


def have_u3():
    return HAVE_U3 and _u3 is not None


@contextmanager
def _suppress_libusb_noise():
    """Hide noisy libusb warnings emitted during U3 enumeration.

    LabJack's Exodriver emits `LIBUSB_ERROR_NOT_FOUND` on some hosts even when the
    device opens successfully. We temporarily redirect the C stderr file descriptor
    to `/dev/null` so the message does not confuse users. Any real failures will
    still raise Python exceptions once stderr is restored.
    """

    if os.name != "posix":
        yield
        return
    try:
        err_fd = sys.stderr.fileno()
    except (AttributeError, OSError, ValueError):
        yield
        return

    saved_fd = os.dup(err_fd)
    try:
        with open(os.devnull, "w") as devnull:
            os.dup2(devnull.fileno(), err_fd)
        yield
    finally:
        os.dup2(saved_fd, err_fd)
        os.close(saved_fd)


def open_u3_safely():
    if not have_u3():
        raise RuntimeError(f"LabJack U3 library unavailable: {U3_ERR}")
    with _suppress_libusb_noise():
        try:
            return _u3.U3(firstFound=True)
        except Exception as exc:
            # Retry using explicit two-step open in case autoOpen fails.
            try:
                dev = _u3.U3(autoOpen=False)
                dev.open(firstFound=True)
                return dev
            except Exception:
                raise RuntimeError(f"LabJack U3 open failed: {exc}") from exc


# ---- Wrappers used by extracted GUI tabs (mirroring legacy monolith helpers)
def u3_open():  # simple alias maintaining previous naming
    return open_u3_safely()
