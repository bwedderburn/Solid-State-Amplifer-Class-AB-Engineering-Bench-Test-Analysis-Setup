import os
import subprocess
import sys
import math

BIN = [sys.executable, 'unified_gui_layout.py']


def run_cli(args):
    cp = subprocess.run(BIN + args, capture_output=True, text=True)
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def test_spectrum_synthetic(tmp_path):
    # Skip if numpy missing
    try:
        import numpy  # noqa: F401
    except Exception:
        return
    d = tmp_path / 'out'
    rc, out, err = run_cli(['spectrum', '--outdir', str(d), '--output',
                           'spec.png', '--f0', '1234', '--fs', '48000', '--points', '2048'])
    assert rc == 0, err
    png_path = out.strip()
    assert os.path.exists(png_path)
    assert png_path.endswith('spec.png')
    # Basic sanity: file non-empty
    assert os.path.getsize(png_path) > 0
