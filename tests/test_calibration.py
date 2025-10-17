from amp_benchkit.calibration import CalibrationCurve, load_calibration_curve


def test_load_calibration_curve():
    curve = load_calibration_curve()
    assert isinstance(curve, CalibrationCurve)
    assert curve.freqs[0] == 20.0
    assert curve.freqs[-1] == 20000.0
    ratio = curve.ratio_at(1000.0)
    assert 0.99 < ratio < 1.02
    corrected = curve.apply(1000.0, 1.0)
    assert abs(corrected - (1.0 / ratio)) < 1e-6
