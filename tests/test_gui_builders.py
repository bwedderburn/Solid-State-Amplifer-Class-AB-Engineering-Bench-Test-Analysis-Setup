import os
import sys

import pytest

# Attempt to import Qt binding only when available; skip otherwise.
try:
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover - headless / missing Qt
    QApplication = None  # type: ignore

from amp_benchkit.gui import (
    build_automation_tab,
    build_daq_tab,
    build_diagnostics_tab,
    build_generator_tab,
    build_scope_tab,
)


class DummyGUI:
    def _log(self, tgt, msg):
        pass
    # Stubs for methods referenced by tabs
    def apply_gen_side(self, side): pass
    def start_sweep_side(self, side): pass
    def stop_sweep_side(self, side): pass
    def scan_serial_into(self, target): pass
    def run_sweep_scope_fixed(self): pass
    def run_audio_kpis(self): pass
    def stop_sweep_scope(self): pass
    def run_diag(self): pass
    def read_daq_once(self): pass
    def read_daq_multi(self): pass

@pytest.mark.skipif(QApplication is None, reason="Qt not available")
def test_build_all_tabs():
    # Use offscreen platform if possible
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QApplication.instance() or QApplication(sys.argv)
    gui = DummyGUI()
    tabs = [
        build_generator_tab(gui),
        build_scope_tab(gui),
        build_daq_tab(gui),
        build_automation_tab(gui),
        build_diagnostics_tab(gui)
    ]
    # Ensure each returned a widget (not None)
    assert all(t is not None for t in tabs)
