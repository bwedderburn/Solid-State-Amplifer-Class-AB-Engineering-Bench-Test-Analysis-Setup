import math

import pytest

from amp_benchkit.dsp import find_knees
from amp_benchkit.sweeps import (
    _clean_amplitudes,
    _monotonic_envelope,
    _reference_index,
    _smooth_series,
    thd_sweep,
)


def _stub_sweep_audio_kpis(freqs, *, fy_apply, amp_vpp, **kwargs):
    rows = []
    for f in freqs:
        fy_apply(
            freq_hz=f,
            amp_vpp=amp_vpp,
            wave="Sine",
            off_v=0.0,
            duty=None,
            ch=1,
        )
        rows.append((f, 1.0, 2.0, 0.01, 1.0))
    return {"rows": rows}


@pytest.fixture(autouse=True)
def _patch_scope(monkeypatch):
    monkeypatch.setattr("amp_benchkit.sweeps.scope_resume_run", lambda *a, **k: None)
    monkeypatch.setattr("amp_benchkit.sweeps.scope_configure_timebase", lambda *a, **k: None)
    monkeypatch.setattr(
        "amp_benchkit.sweeps.scope_capture_calibrated", lambda *a, **k: ([0.0], [0.0])
    )
    monkeypatch.setattr("amp_benchkit.sweeps.scope_arm_single", lambda *a, **k: None)
    monkeypatch.setattr("amp_benchkit.sweeps.scope_wait_single_complete", lambda *a, **k: True)
    monkeypatch.setattr("amp_benchkit.sweeps.scope_configure_math_subtract", lambda *a, **k: None)


def test_thd_sweep_restores_generator(monkeypatch, tmp_path):
    calls = []

    def fake_fy_apply(*, freq_hz, amp_vpp, wave, off_v, duty, ch, port=None, proto=None):
        calls.append(
            {
                "freq_hz": freq_hz,
                "amp_vpp": amp_vpp,
                "port": port,
                "proto": proto,
            }
        )
        return ["ok"]

    monkeypatch.setattr("amp_benchkit.sweeps.fy_apply", fake_fy_apply)

    rows, out_path, suppressed = thd_sweep(
        visa_resource="FAKE::SCOPE",
        fy_port="FAKE::GEN",
        fy_proto="FY ASCII 9600",
        amp_vpp=0.5,
        scope_channel=1,
        start_hz=100.0,
        stop_hz=200.0,
        points=3,
        dwell_s=0.0,
        use_math=False,
        output=None,
        filter_spikes=False,
        post_freq_hz=1234.0,
        post_seconds_per_div=None,
    )

    assert rows
    assert out_path is None
    assert suppressed == []
    assert len(calls) == 4  # 3 sweep points + 1 restore
    assert math.isclose(calls[-1]["freq_hz"], 1234.0, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(calls[-1]["amp_vpp"], 0.5, rel_tol=0, abs_tol=1e-9)
    assert calls[-1]["port"] == "FAKE::GEN"
    assert calls[-1]["proto"] == "FY ASCII 9600"


def test_thd_sweep_logs_when_reset_fails(monkeypatch, caplog):
    def flaky_fy_apply(*, freq_hz, amp_vpp, wave, off_v, duty, ch, port=None, proto=None):
        if freq_hz == 1000.0:
            raise RuntimeError("link lost")
        return ["ok"]

    monkeypatch.setattr("amp_benchkit.sweeps.fy_apply", flaky_fy_apply)
    monkeypatch.setattr("amp_benchkit.sweeps.sweep_audio_kpis", _stub_sweep_audio_kpis)

    with caplog.at_level("WARNING", logger="amp_benchkit.sweeps"):
        thd_sweep(
            visa_resource="FAKE::SCOPE",
            fy_port="FAKE::GEN",
            fy_proto="FY ASCII 9600",
            amp_vpp=0.5,
            scope_channel=1,
            start_hz=100.0,
            stop_hz=200.0,
            points=3,
            dwell_s=0.0,
            use_math=False,
            output=None,
            filter_spikes=False,
            post_freq_hz=1000.0,
            post_seconds_per_div=None,
        )
    assert any("FY reset to 1000.0 Hz failed" in rec.message for rec in caplog.records)


def test_thd_sweep_auto_scale(monkeypatch):
    calls = []

    def fake_fy_apply(*, freq_hz, amp_vpp, wave, off_v, duty, ch, port=None, proto=None):
        calls.append((freq_hz, amp_vpp))
        return ["ok"]

    set_calls = []
    read_calls = []

    def fake_set(resource, channel, volts_per_div):
        set_calls.append((resource, channel, volts_per_div))

    def fake_read(resource, channel):
        read_calls.append((resource, channel))
        return 0.05

    monkeypatch.setattr("amp_benchkit.sweeps.fy_apply", fake_fy_apply)
    monkeypatch.setattr("amp_benchkit.sweeps.scope_set_vertical_scale", fake_set)
    monkeypatch.setattr("amp_benchkit.sweeps.scope_read_vertical_scale", fake_read)

    thd_sweep(
        visa_resource="FAKE::SCOPE",
        fy_port="FAKE::GEN",
        fy_proto="FY ASCII 9600",
        amp_vpp=0.5,
        scope_channel=1,
        start_hz=100.0,
        stop_hz=200.0,
        points=3,
        dwell_s=0.0,
        use_math=False,
        output=None,
        filter_spikes=False,
        post_seconds_per_div=None,
        scope_scale_map={"CH1": 10.0},
        scope_scale_margin=1.0,
        scope_scale_min=0.01,
        scope_scale_divs=8.0,
    )

    # 3 sweep points -> 3 scale adjustments, plus one restore
    assert len(calls) == 4  # includes post-sweep restore @ 1 kHz
    assert math.isclose(calls[-1][0], 1000.0, abs_tol=1e-6)
    assert len([c for c in set_calls if c[2] != 0.05]) == 3
    assert math.isclose(set_calls[0][2], 0.5 * 10.0 / 8.0, rel_tol=1e-9)
    assert set_calls[-1][2] == 0.05
    assert read_calls  # ensure original scale was queried


def test_knee_sweep_basic(monkeypatch, tmp_path):
    # Fabricated, slightly non-linear amplitude profile with ripple around the passband.
    freqs = [20.0, 40.0, 80.0, 160.0, 320.0, 640.0, 1280.0, 2560.0, 5120.0, 10240.0, 20480.0]
    pkpk = [0.32, 0.55, 0.88, 0.70, 1.08, 1.12, 1.09, 1.01, 0.68, 0.45, 0.28]

    def fake_build_freq_points(*args, **kwargs):
        return list(freqs)

    def fake_fy_apply(*, freq_hz, amp_vpp, wave, off_v, duty, ch, port=None, proto=None):
        fy_calls.append(freq_hz)
        return ["ok"]

    def fake_sweep_audio_kpis(
        freq_list,
        *,
        dsp_find_knees,
        do_knees,
        knee_drop_db=3.0,
        knee_ref_mode="max",
        knee_ref_hz=1000.0,
        **kwargs,
    ):
        assert list(freq_list) == freqs
        fy_apply_fn = kwargs.get("fy_apply")
        amp_setting = kwargs.get("amp_vpp", 1.0)
        channel = kwargs.get("channel", 1)
        if fy_apply_fn:
            for f in freq_list:
                fy_apply_fn(
                    freq_hz=f,
                    amp_vpp=amp_setting,
                    wave="Sine",
                    off_v=0.0,
                    duty=None,
                    ch=channel,
                )
        rows = []
        for f, pk in zip(freq_list, pkpk, strict=False):
            vr = pk / (2.0 * math.sqrt(2.0))
            rows.append((f, vr, pk, float("nan"), float("nan")))
        knees = None
        if do_knees:
            knees = dsp_find_knees(
                list(freq_list),
                [row[2] for row in rows],
                knee_ref_mode,
                knee_ref_hz,
                knee_drop_db,
            )
        return {"rows": rows, "knees": knees}

    fy_calls: list[float] = []
    monkeypatch.setattr("amp_benchkit.sweeps.build_freq_points", fake_build_freq_points)
    monkeypatch.setattr("amp_benchkit.sweeps.fy_apply", fake_fy_apply)
    monkeypatch.setattr("amp_benchkit.sweeps.sweep_audio_kpis", fake_sweep_audio_kpis)

    from amp_benchkit.sweeps import knee_sweep

    result = knee_sweep(
        visa_resource="FAKE::SCOPE",
        fy_port="FAKE::GEN",
        amp_vpp=1.0,
        scope_channel=1,
        start_hz=20.0,
        stop_hz=20000.0,
        points=len(freqs),
        dwell_s=0.0,
        output=tmp_path / "knees.csv",
    )

    knees = result["knees"]
    assert knees is not None
    f_lo, f_hi, ref_amp, ref_db = knees
    cleaned = _clean_amplitudes(pkpk)
    smoothed = _smooth_series(cleaned, 5, "median")
    ref_idx = _reference_index(freqs, smoothed, "max", 1000.0)
    processed = _monotonic_envelope(smoothed, ref_idx)
    expected_knees = find_knees(freqs, processed, "max", 1000.0, 3.0)
    assert all(math.isfinite(x) for x in expected_knees)
    for got, exp in zip(knees, expected_knees, strict=False):
        assert math.isclose(got, exp, rel_tol=0, abs_tol=1e-6)

    rows = result["rows"]
    assert len(rows) == len(freqs)
    # Δ dB near reference should be close to 0
    mid_row = rows[6]
    assert math.isclose(mid_row[3], 0.0, abs_tol=0.1)

    csv_path = result["csv_path"]
    assert csv_path and csv_path.exists()
    content = csv_path.read_text().splitlines()
    assert content[0] == "freq_hz,vrms,pkpk,rel_db"
    assert len(content) == len(freqs) + 1

    # Sweep points + post-run 1 kHz reset
    assert len(fy_calls) == len(freqs) + 1
    assert math.isclose(fy_calls[-1], 1000.0, abs_tol=1e-6)
