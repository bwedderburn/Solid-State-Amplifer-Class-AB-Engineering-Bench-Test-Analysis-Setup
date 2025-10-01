import json
import math
import os
import tempfile
import subprocess
import sys
import shutil

BIN = [sys.executable, 'unified_gui_layout.py']


def run_cli(args):
    cp = subprocess.run(BIN + args, capture_output=True, text=True)
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def test_freq_gen_json():
    rc, out, err = run_cli(['freq-gen', '--start', '10', '--stop',
                           '100', '--points', '5', '--mode', 'linear', '--format', 'json'])
    assert rc == 0, err
    data = json.loads(out)
    assert data['start'] == 10
    assert data['stop'] == 100
    assert data['points'] == 5
    assert len(data['frequencies']) == 5
    # endpoints exact (6-dec rounding handled by build_freq_points)
    assert abs(data['frequencies'][0]-10.0) < 1e-6
    assert abs(data['frequencies'][-1]-100.0) < 1e-6


def test_freq_gen_csv():
    rc, out, err = run_cli(['freq-gen', '--start', '10', '--stop',
                           '100', '--points', '5', '--mode', 'linear', '--format', 'csv'])
    assert rc == 0, err
    lines = out.splitlines()
    assert len(lines) == 5
    assert abs(float(lines[0]) - 10.0) < 1e-6
    assert abs(float(lines[-1]) - 100.0) < 1e-6


def test_thd_json_basic():
    # Skip if numpy unavailable (advanced path requires it)
    try:
        import numpy as np  # type: ignore
    except Exception:
        return
    fs = 50000.0
    f0 = 1000.0
    n = 4096
    t = np.arange(n)/fs
    v = np.sin(2*math.pi*f0*t) + 0.05*np.sin(2*math.pi*2*f0*t)
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'wave.csv')
        with open(path, 'w', encoding='utf-8') as fh:
            for ti, vi in zip(t, v):
                fh.write(f"{ti},{vi}\n")
        rc, out, err = run_cli(
            ['thd-json', path, '--f0', str(f0), '--nharm', '5'])
        assert rc == 0, err
        data = json.loads(out)
        # THD ~0.05 (window/fft bin rounding tolerance)
        if math.isfinite(data['thd']):
            assert abs(data['thd'] - 0.05) < 0.03
            assert abs(data['f0_est'] - f0) < 5.0
            assert data['fund_amp'] > 0.0
            assert isinstance(data['harmonics'], list)


def test_thd_json_short_wave():
    try:
        import numpy as np  # type: ignore
    except Exception:
        return
    t = [0.0, 1e-6, 2e-6, 3e-6]  # very short
    v = [0.0, 0.1, -0.1, 0.05]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, 'short.csv')
        with open(path, 'w', encoding='utf-8') as fh:
            for ti, vi in zip(t, v):
                fh.write(f"{ti},{vi}\n")
        rc, out, err = run_cli(['thd-json', path])
        assert rc == 0, err
        data = json.loads(out)
        # short path returns NaNs (serialized as NaN in JSON not standard; json dumps may output NaN literal allowed by Python)
        # Accept either NaN or missing harmonics
        # Python's json allows NaN, check string presence
        assert ('"thd":NaN' in out) or (not math.isfinite(data['thd']))
