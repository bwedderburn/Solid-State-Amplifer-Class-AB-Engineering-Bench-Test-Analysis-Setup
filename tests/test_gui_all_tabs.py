import os
import sys

import pytest

try:
    from PySide6.QtWidgets import (
        QApplication,  # prefer PySide6; fallback attempted inside builder helper
    )
except Exception:
    try:
        from PyQt5.QtWidgets import QApplication  # type: ignore
    except Exception:
        QApplication = None  # type: ignore

from amp_benchkit.gui import build_all_tabs


class DummyGUI:
    def _log(self, tgt, msg): pass
    scope_res = ''
    # Generator stubs
    def apply_gen_side(self, side): pass
    def start_sweep_side(self, side): pass
    def stop_sweep_side(self, side): pass
    def scan_serial_into(self, target): pass
    def list_visa(self): pass
    def capture_scope(self): pass
    def save_shot(self): pass
    def save_csv(self): pass
    # Automation stubs
    def run_sweep_scope_fixed(self): pass
    def run_audio_kpis(self): pass
    def stop_sweep_scope(self): pass
    # Diagnostics
    def run_diag(self): pass
    # DAQ
    def read_daq_once(self): pass
    def read_daq_multi(self): pass

@pytest.mark.skipif(QApplication is None, reason="Qt not available")
def test_build_all_tabs():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QApplication.instance() or QApplication(sys.argv)
    gui = DummyGUI()
    tabs = build_all_tabs(gui)
    assert set(tabs.keys()) == { 'generator','scope','daq','automation','diagnostics' }
    # All should be non-None if Qt present
    assert all(v is not None for v in tabs.values())
