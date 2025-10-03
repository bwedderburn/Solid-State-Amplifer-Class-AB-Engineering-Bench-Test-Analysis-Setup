# Release Notes – amp-benchkit v0.3.5

Tag: `v0.3.5`
Date: 2025-10-01

## Highlights
- Real-time THD tab now uses an async capture thread (smoother UI, reduced blocking).
- Added persistent THD settings (resource, f0, harmonics, refresh interval) via JSON config.
- Introduced CLI `spectrum` command for rapid magnitude spectrum PNG export (supports synthetic or CSV input).
- GUI THD tab gains Spectrum export button using shared `results_dir` path.
- Advanced DSP API (`thd_fft_waveform`, `harmonic_table`) publicly re-exported.

## Added
- `spectrum` CLI subcommand.
- `results_dir` config key recognized by GUI and CLI.
- Persistence test & spectrum test to ensure stable behavior.

## Changed
- Capture thread in THD tab now properly joins on stop.
- Packaging: explicit setuptools package discovery excluding vendor driver sources.

## Fixed
- Config path monkeypatching robust when tests override `CONFIG_PATH` as a string.

## Compatibility
- Python >=3.10.
- Optional extras: `[dsp]` for NumPy FFT path, `[gui]` for Qt tabs, `[labjack]` for hardware.

## Installation
```bash
pip install amp-benchkit==0.3.5
# or with recommended extras
pip install "amp-benchkit[gui,dsp]"  # add others as needed
```

## Quick Usage
```bash
# Frequency list
python unified_gui_layout.py freq-gen --start 100 --stop 10k --points 7 --mode log --format json
# THD mode (advanced vs stub)
python unified_gui_layout.py thd-mode
# Spectrum (synthetic sine 1 kHz)
python unified_gui_layout.py spectrum --f0 1000 --points 4096 --fs 48000 --outdir results
```

## Next (Planned)
- Optional inline/live spectrum preview in GUI.
- Peak picking & CSV spectrum export.
- Additional window options for spectrum CLI (matching THD analysis windows).

---
Generated as part of automated release preparation.
