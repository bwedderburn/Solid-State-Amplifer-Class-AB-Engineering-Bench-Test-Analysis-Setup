#!/usr/bin/env python3
"""Lightweight LabJack U3 USB / environment diagnostic.

Goals:
- Import u3 module, report version.
- Attempt to open a U3 (non-destructive) with conservative timeout.
- Distinguish between: library missing, driver missing (liblabjackusb), no device
  present, permission error.
- Exit codes:
    0 success (device opened)
    1 python module missing
    2 driver (shared library) load failure
    3 no device detected / open failed
    4 permission / OS level denial
"""

from __future__ import annotations

import sys

EXIT_MOD_MISSING = 1
EXIT_DRIVER_FAIL = 2
EXIT_NO_DEVICE = 3
EXIT_PERM = 4


def main():
    try:
        import u3  # type: ignore
    except Exception as e:
        print(f"ERROR: Failed to import LabJackPython 'u3': {e}")
        print("Hint: pip install LabJackPython")
        return EXIT_MOD_MISSING

    print(f"u3 module import OK (version attr: {getattr(u3, '__version__', 'n/a')})")

    # Try opening a device. Use a short timeout if supported.
    try:
        try:
            d = u3.U3()  # Default open
        except Exception as e_first:
            # Some environments require specifying firstFound; fall back.
            try:
                d = u3.U3(firstFound=True)
            except Exception:
                raise e_first from None
    except Exception as e:
        msg = str(e).lower()
        if "liblabjackusb" in msg or "exodriver" in msg:
            print("ERROR: Exodriver (liblabjackusb) not loaded.")
            print(" - Ensure library installed (scripts/install_exodriver_alpine.sh)")
            print(" - Possibly set: export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH")
            return EXIT_DRIVER_FAIL
        if "permission" in msg or "denied" in msg:
            print("ERROR: Permission denied opening device.")
            print(" - On Linux add udev rules then replug device.")
            return EXIT_PERM
        print(f"No device opened: {e}")
        return EXIT_NO_DEVICE

    # If we got here, device opened
    try:
        info = d.configU3() if hasattr(d, "configU3") else {}
    except Exception:
        info = {}
    print("Device open SUCCESS")
    if info:
        print("Basic configU3 info keys:", list(info.keys()))
    d.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    rc = main()
    sys.exit(rc)
