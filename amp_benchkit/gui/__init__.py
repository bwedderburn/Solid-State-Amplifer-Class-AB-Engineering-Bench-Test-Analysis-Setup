"""GUI tab builders aggregator.

Each build_<name>_tab(gui) should return a QWidget (or None if unavailable).
A convenience build_all_tabs() returns an iterable of (widget, label) tuples
for the main window to add.
"""
from __future__ import annotations
from typing import List, Tuple, Any
from ._qt import require_qt
from .gen_tab import build_generator_tab  # type: ignore
from .scope_tab import build_scope_tab  # type: ignore
from .daq_tab import build_daq_tab  # type: ignore
from .automation_tab import build_automation_tab  # type: ignore
from .diag_tab import build_diagnostics_tab  # type: ignore

# Import individual tab builders lazily inside build_all_tabs to avoid side-effects on import.


def build_all_tabs(gui: Any) -> List[Tuple[Any, str]]:
    tabs: List[Tuple[Any, str]] = []
    qt = require_qt()
    if qt is None:
        return tabs
    # DAQ tab (optional if builder import fails)
    try:  # pragma: no cover
        from .daq_tab import build_daq_tab  # type: ignore
        w = build_daq_tab(gui)
        if w is not None:
            tabs.append((w, "DAQ"))
    except Exception:
        pass
    # THD / Analysis tab will be appended by future additions if present
    try:  # pragma: no cover
        from .thd_tab import build_thd_tab  # type: ignore
        w = build_thd_tab(gui)
        if w is not None:
            tabs.append((w, "THD"))
    except Exception:
        pass
    return tabs


__all__ = [
    "build_all_tabs",
    "build_generator_tab",
    "build_scope_tab",
    "build_daq_tab",
    "build_automation_tab",
    "build_diagnostics_tab",
]
