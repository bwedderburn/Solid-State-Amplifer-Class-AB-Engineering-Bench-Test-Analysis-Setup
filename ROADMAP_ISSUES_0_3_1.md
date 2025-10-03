# 0.3.1 Cycle Candidate Issues

This document summarizes proposals to convert into GitHub issues. Each section can become an issue with the body text copied verbatim.

---
## SNR & Noise Floor Metrics
**Type**: Feature
**Rationale**: Extend KPI set beyond THD and bandwidth knees for broader audio characterization.
**Scope**:
- Implement `snr_db(signal, noise)` helper (time-domain segmentation or FFT-based bin exclusion approach) in `dsp.py` or new `metrics.py`.
- Add `noise_floor_db` function (average of non-fundamental, non-harmonic bins inside analyzed band).
- Integrate into `sweep_audio_kpis` returning additional fields when enabled.
- Configurable window & number of discarded harmonic bins.
**Acceptance**:
- Unit tests with synthetic sine + added white noise verifying SNR within ±0.5 dB.
- CLI / automation example updated.
- Documentation section in README + changelog entry.
**Risks**: Window leakage influencing noise floor; decide on default (Hann).

## Coverage Threshold Introduction
**Type**: Quality
**Rationale**: Prevent regression in test coverage while still allowing incremental improvement.
**Scope**:
- Add `--cov-fail-under=70` to CI test job initially.
- Print coverage summary artifact and possibly badge later.
- Add a CONTRIBUTING note: raise threshold when comfortably above value for two consecutive releases.
**Acceptance**:
- CI fails if coverage dips below threshold.
- README “Development” section references threshold.
**Risks**: Flaky tests or platform-differing coverage; mitigate by avoiding brittle timing tests.

## Sweep CLI Wrapper
**Type**: Feature (User Experience)
**Rationale**: Provide a headless, script-friendly interface without writing Python.
**Scope**:
- `amp-benchkit sweep --start 20 --stop 20000 --points 25 --mode log` prints frequencies (later: run acquisition pipeline).
- Reuse `build_freq_list` from automation.
- Add integration test verifying output count & boundaries.
**Acceptance**:
- Running command yields correct count, inclusive boundaries.
- Help text lists arguments and defaults.
**Risks**: Future expansion (instrument selection) may require subparser redesign.

## Stricter Typing Phase 1
**Type**: Quality
**Rationale**: Catch errors earlier & prep for more contributors.
**Scope**:
- Enable mypy disallow untyped defs in `dsp.py` and `automation.py`.
- Add type annotations for public APIs lacking them.
**Acceptance**:
- CI mypy step passes with stricter config.
**Risks**: Temporary churn; keep changes scoped.
