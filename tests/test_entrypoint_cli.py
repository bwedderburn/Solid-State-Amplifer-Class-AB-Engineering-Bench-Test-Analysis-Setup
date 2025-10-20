import math
import sys

from amp_benchkit import cli


def test_cli_sweep_invoke(monkeypatch, capsys):
    # Provide arguments to generate a small linear sweep
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "amp-benchkit",
            "sweep",
            "--start",
            "1",
            "--stop",
            "2",
            "--points",
            "2",
            "--mode",
            "linear",
        ],
    )
    try:
        rc = cli.main()
        # If legacy main returned instead of exiting, rc should be 0
        assert rc == 0
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ["1", "2"]


def test_cli_error_exit(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["amp-benchkit", "sweep", "--start", "1", "--stop", "2", "--points", "1"]
    )
    try:
        cli.main()
        # If no SystemExit, treat as failure because underlying main uses sys.exit
        raise AssertionError("Expected SystemExit for invalid points")
    except SystemExit as e:
        assert e.code != 0


def test_cli_knee_sweep(monkeypatch, capsys):
    called = []

    def fake_knee_sweep(**kwargs):
        called.append(kwargs["visa_resource"])
        return {
            "rows": [
                (20.0, 0.25, 0.5, -6.0),
                (1000.0, 0.70, 1.40, 0.0),
                (20000.0, 0.40, 0.80, -3.5),
            ],
            "knees": (35.0, 18000.0, 1.40, 20.0 * math.log10(1.40)),
            "ref_db": 20.0 * math.log10(1.40),
            "target_db": 20.0 * math.log10(1.40) - 3.0,
            "csv_path": None,
        }

    monkeypatch.setattr("unified_gui_layout.knee_sweep", fake_knee_sweep)

    try:
        rc = cli.main(["knee-sweep"])
    except SystemExit as e:
        rc = e.code

    assert rc == 0
    assert len(called) == 1
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert any("Knees @" in line for line in out_lines)
    assert any("delta" in line for line in out_lines)


def test_cli_fft_capture(monkeypatch, capsys):
    captured = {"freqs": [1000.0, 2000.0], "values": [-3.0, -6.0], "x_unit": "Hz", "y_unit": "dB"}

    def fake_fft(**kwargs):
        captured["source"] = kwargs["source"]
        return captured

    monkeypatch.setattr("unified_gui_layout.scope_capture_fft_trace", fake_fft)

    try:
        rc = cli.main(["fft-capture", "--output", "-", "--top", "1"])
    except SystemExit as e:
        rc = e.code

    assert rc == 0
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert any("Top 1 bins" in line for line in out_lines)
    assert any("1000.00 Hz" in line for line in out_lines)
