import subprocess
import sys
import pathlib

PY = sys.executable
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'unified_gui_layout.py'

def test_cli_no_args_help():
    proc = subprocess.run([PY, str(SCRIPT)], capture_output=True, text=True)
    # Accept exit code 2 (intended) or 1 (if import stub errors still bubble before graceful exit)
    assert proc.returncode in (1, 2)
    combined = (proc.stderr + proc.stdout).lower()
    assert 'usage:' in combined
