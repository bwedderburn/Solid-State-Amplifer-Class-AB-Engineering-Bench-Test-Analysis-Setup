import subprocess
import sys
import json
import os

PY = sys.executable


def run_cli(*args: str) -> str:
    out = subprocess.check_output(
        [PY, 'unified_gui_layout.py', *args], text=True)
    return out.strip()


def test_cli_thd_mode_outputs_mode():
    mode = run_cli('thd-mode')
    assert mode in {"advanced", "stub"}
    # If advanced, importing numpy should succeed
    if mode == 'advanced':
        import importlib
        numpy_spec = importlib.util.find_spec('numpy')
        assert numpy_spec is not None
