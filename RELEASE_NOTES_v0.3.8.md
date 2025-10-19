# Release Notes — v0.3.8

## Highlights
- **Automatic scope scaling**: `thd-math-sweep` can now drive Tektronix volts/div for each channel using `--scope-auto-scale ...` flags, preventing math-trace clipping during amplitude sweeps. Settings are restored after each run and failures log clear warnings.
- **Baseline artefact packaging**: CLI helpers generate merged summaries and plots comparing raw vs gold-calibrated THD for 0.2–0.5 Vpp Kenwood sweeps; a new README segment documents how to archive them under `results/`.

## CLI Changes
- `thd-math-sweep` / `scripts/thd_math_sweep.py` accept:
  - `--scope-auto-scale CH1=13,CH3=1` map (channel -> expected Vpp gain).
  - `--scope-auto-scale-margin`, `--scope-auto-scale-min`, `--scope-auto-scale-divs` for headroom and display tuning.
- The README now includes a full command example mixing auto-scaling with `--apply-gold-calibration` for bridged amplifier testing.

## Internal / Testing
- Added `scope_read_vertical_scale` / `scope_set_vertical_scale` helpers and threaded them through `sweep_audio_kpis` with preservation of original scope state.
- New pytest coverage (`tests/test_sweeps.py`) ensures volts/div adjustments occur per sweep point and reset afterwards.

Upgrade with `pip install -U amp-benchkit==0.3.8` and consult the updated documentation section "Automatic Scope Scaling" for usage tips.
