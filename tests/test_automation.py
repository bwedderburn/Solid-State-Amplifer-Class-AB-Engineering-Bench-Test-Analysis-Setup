import math

from amp_benchkit.automation import build_freq_list, sweep_audio_kpis, sweep_scope_fixed


def test_build_freq_list_basic():
    freqs = build_freq_list(100, 300, 100)
    assert freqs == [100,200,300]


def test_sweep_scope_fixed_minimal(monkeypatch):
    # Inject fakes
    calls = []
    def fake_fy_apply(**kw):
        calls.append(kw['freq_hz'])
    def fake_scope_measure(src, metric):
        # return simple function of src for determinism
        return 1.23 if metric=='RMS' else 4.56
    out = sweep_scope_fixed(
        freqs=[100,200],
        channel=1,
        scope_channel=1,
        amp_vpp=2.0,
        dwell_s=0.0,
        metric='RMS',
        fy_apply=fake_fy_apply,
        scope_measure=fake_scope_measure,
    )
    assert len(out) == 2
    assert calls == [100,200]
    assert out[0][1] == 1.23


def test_sweep_audio_kpis_basic(monkeypatch):
    freqs = [100,200]
    def fake_fy_apply(**kw):
        pass
    # Provide a simple 1 kHz sine capture irrespective of freq to exercise DSP path
    import numpy as np
    fs = 10000.0; f0 = 100.0; N = 1024
    t = np.arange(N)/fs
    sig = 0.5 * np.sin(2*math.pi*f0*t)
    def fake_capture(res, ch):
        return t, sig
    def vrms(v):
        import numpy as np
        return float(np.sqrt((np.array(v)**2).mean()))
    def vpp(v):
        return float(max(v)-min(v))
    def thd_fft(t, v, f):
        # Return fake THD ratio 0.1
        return 0.1, f, None
    def find_knees(freqs, amps, ref_mode, ref_hz, drop_db):
        return freqs[0], freqs[-1], max(amps), 0.0
    res = sweep_audio_kpis(
        freqs,
        channel=1,
        scope_channel=1,
        amp_vpp=2.0,
        dwell_s=0.0,
        fy_apply=fake_fy_apply,
        scope_capture_calibrated=fake_capture,
        dsp_vrms=vrms,
        dsp_vpp=vpp,
        dsp_thd_fft=thd_fft,
        dsp_find_knees=find_knees,
        do_thd=True,
        do_knees=True,
    )
    rows = res['rows']
    assert len(rows) == 2
    assert res['knees'][0] == 100 and res['knees'][1] == 200
    # Vrms of 0.5 * sin should be ~0.3535
    assert abs(rows[0][1] - 0.3535) < 0.02
