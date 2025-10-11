import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "unified_gui_layout.py")


def run(args):
    cmd = [sys.executable, SCRIPT] + args
    out = subprocess.check_output(cmd, text=True)
    return out.strip().splitlines()


def test_linear_sweep():
    lines = run(["sweep", "--start", "10", "--stop", "100", "--points", "5", "--mode", "linear"])
    floats = list(map(float, lines))
    assert floats[0] == 10
    assert floats[-1] == 100
    # Expect evenly spaced: 10, 32.5, 55, 77.5, 100
    diffs = [b - a for a, b in zip(floats, floats[1:], strict=False)]
    # All diffs equal within tiny tolerance
    assert max(diffs) - min(diffs) < 1e-6


def test_log_sweep():
    lines = run(["sweep", "--start", "10", "--stop", "1000", "--points", "4", "--mode", "log"])
    floats = list(map(float, lines))
    assert floats[0] == 10
    assert floats[-1] == 1000
    # Geometric progression ratio
    r1 = floats[1] / floats[0]
    r2 = floats[2] / floats[1]
    r3 = floats[3] / floats[2]
    # Allow small numeric drift due to rounding to 6 decimals
    assert abs(r1 - r2) < 1e-6
    assert abs(r2 - r3) < 1e-6


def test_invalid_points():
    # Points <2 should raise (from automation.build_freq_list)
    proc = subprocess.run(
        [sys.executable, SCRIPT, "sweep", "--start", "10", "--stop", "100", "--points", "1"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "error" in proc.stderr.lower() or "points" in proc.stderr.lower()
