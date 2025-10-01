# 0.3.3 Roadmap (Draft)

Target Themes:
- DSP modularization
- GUI tab extraction & cleanup
- Instrument abstraction stability

## Proposed Issues
1. Extract advanced THD + helper functions from `unified_gui_layout.py` into `amp_benchkit.dsp` (maintain dispatcher shim).
2. Add harmonic amplitude table output to THD calculation (behind flag or separate API).
3. Implement cached frequency sweep profiles (avoid recompute of identical point sets).
4. Introduce structured logging contexts (per sweep / capture) for easier post-run analysis.
5. Add Codecov badge hooked to real coverage once token configured.
6. Add Windows smoke test for minimal headless usage (already partly covered by dist job; expand functional tests).
7. Provide example Jupyter notebook (optional) demonstrating automated sweep + analysis.
8. Add CLI command `freq-gen` to output generated frequency list as JSON or CSV.
9. Replace in-file Qt widget building with modular `amp_benchkit.gui.*` imports for each tab (progressive extraction).
10. Optional: Provide `--thd-json` to emit structured THD results in automation mode.

## Stretch
- Plug-in system for additional instrument drivers.
- Async acquisition pipeline (capture + processing concurrency).

## Deferred / Evaluate Later
- Waveform synthesis library for arbitrary generator profiles.
- gRPC or HTTP microservice wrapper around core automation.
