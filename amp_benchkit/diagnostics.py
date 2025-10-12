"""Diagnostics helpers for amp-benchkit.

Collects environment, dependency, and hardware status information so the GUI
and CLI can surface consistent, structured diagnostics. Designed to be safe in
environments without hardware attached; hardware probes are optional.
"""

from __future__ import annotations

import datetime as _dt
import os
import platform
import sys
from contextlib import suppress
from typing import Any, Iterable

from . import __version__
from .deps import (
    HAVE_PYVISA,
    HAVE_QT,
    HAVE_SERIAL,
    HAVE_U3,
    INSTALL_HINTS,
    QT_BINDING,
    _lp,
    _pyvisa,
    _serial,
    _u3,
    dep_msg,
    find_fy_port,
    list_ports,
)
from .u3config import u3_read_ain
from .u3util import have_u3, open_u3_safely

DiagSections = list[tuple[str, list[str]]]


def _clean_lines(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line is None:
            continue
        text = str(line).rstrip()
        if not text:
            continue
        out.append(text)
    return out or ["(none)"]


def _format_sections(sections: DiagSections) -> str:
    blocks: list[str] = []
    for title, lines in sections:
        blocks.append(title)
        for line in _clean_lines(lines):
            blocks.append(f"  {line}")
        blocks.append("")  # blank line between sections
    return "\n".join(blocks).strip()


def _env_section(context: dict[str, Any] | None = None) -> tuple[str, list[str]]:
    env_keys = [
        "AMPBENCHKIT_FAKE_HW",
        "AMP_HIL",
        "FY_PORT",
        "VISA_RESOURCE",
        "AMPBENCHKIT_SESSION_DIR",
    ]
    env_lines = [
        f"Timestamp: {_dt.datetime.now().isoformat(timespec='seconds')}",
        f"amp-benchkit: {__version__}",
        f"Python: {sys.version.split()[0]} ({sys.executable})",
        f"Platform: {platform.platform()}",
        f"CWD: {os.getcwd()}",
        f"Qt Binding: {QT_BINDING or 'Unavailable'} (HAVE_QT={HAVE_QT})",
    ]
    env_lines.append("Environment flags:")
    for key in env_keys:
        env_lines.append(f"  {key}={os.environ.get(key, '<unset>')}")
    if context:
        env_lines.append("Context:")
        for k, v in context.items():
            env_lines.append(f"  {k}: {v}")
    return ("[Environment]", env_lines)


def _dependency_section() -> tuple[str, list[str]]:
    lines = [dep_msg()]
    if HAVE_PYVISA:
        lines.append(f"pyvisa version: {getattr(_pyvisa, '__version__', 'unknown')}")
    else:
        lines.append(f"pyvisa missing → {INSTALL_HINTS['pyvisa']}")

    if HAVE_SERIAL:
        lines.append(f"pyserial version: {getattr(_serial, '__version__', 'unknown')}")
    else:
        lines.append(f"pyserial missing → {INSTALL_HINTS['pyserial']}")

    if HAVE_U3 and _u3 is not None:
        lines.append(f"LabJackPython version: {getattr(_u3, '__version__', 'unknown')}")
    else:
        lines.append(f"LabJackPython missing → {INSTALL_HINTS['u3']}")

    return ("[Dependencies]", lines)


def _connectivity_section() -> tuple[str, list[str]]:
    lines: list[str] = []
    serial_lines: list[str] = []
    if HAVE_SERIAL:
        for port in list_ports():
            serial_lines.append(
                f"{port.device} ({getattr(port, 'description', 'unknown').strip() or 'unknown'})"
            )
    lines.append("Serial ports:")
    lines.extend(f"  {entry}" for entry in (serial_lines or ["(none)"]))

    visa_lines: list[str] = []
   if HAVE_PYVISA and _pyvisa is not None:
    try:
        rm = _pyvisa.ResourceManager()
        visa_lines = list(rm.list_resources())
    except Exception as exc:
        visa_lines = [f"VISA error: {exc}"]
else:
    visa_lines = ["pyvisa is not available"]
    lines.append("VISA resources:")
    lines.extend(f"  {entry}" for entry in (visa_lines or ["(none)"]))

    fy_guess = find_fy_port()
    lines.append(f"FY auto-detected port: {fy_guess or '(unavailable)'}")
    return ("[Connectivity]", lines)


def _hardware_section() -> tuple[str, list[str]]:
    lines: list[str] = []
    if not have_u3():
        lines.append(f"LabJack U3 unavailable → {INSTALL_HINTS['u3']}")
        return ("[Hardware]", lines)

    try:
        dev = open_u3_safely()
    except Exception as exc:
        lines.append(f"Failed to open U3 device: {exc}")
        return ("[Hardware]", lines)

    try:
        info = {}
        with suppress(Exception):
            info = dev.configU3()
        serial = info.get("SerialNumber", getattr(dev, "serialNumber", None))
        hw_version = info.get("HardwareVersion", getattr(dev, "hardwareVersion", None))
        fw_version = info.get("FirmwareVersion", getattr(dev, "firmwareVersion", None))
        lines.append(f"U3 Serial: {serial}")
        lines.append(f"U3 Hardware Version: {hw_version}")
        lines.append(f"U3 Firmware Version: {fw_version}")
        with suppress(Exception):
            lines.append(f"U3 AIN0: {u3_read_ain(0):.4f} V")
        with suppress(Exception):
            lines.append(f"U3 Temperature Sensor: {u3_read_ain(14):.4f} V")
    finally:
        with suppress(Exception):
            dev.close()
    return ("[Hardware]", lines)


def collect_diagnostics(
    *,
    include_environment: bool = True,
    include_dependencies: bool = True,
    include_connectivity: bool = True,
    include_hardware: bool = True,
    context: dict[str, Any] | None = None,
) -> str:
    """Collect diagnostics information.

    Parameters mirror checkboxes in the GUI; each section can be toggled.
    """

    sections: DiagSections = []
    if include_environment:
        sections.append(_env_section(context=context))
    if include_dependencies:
        sections.append(_dependency_section())
    if include_connectivity:
        sections.append(_connectivity_section())
    if include_hardware:
        sections.append(_hardware_section())
    return _format_sections(sections)
