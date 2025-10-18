import math

import pytest

from amp_benchkit.sweeps import thd_sweep


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
