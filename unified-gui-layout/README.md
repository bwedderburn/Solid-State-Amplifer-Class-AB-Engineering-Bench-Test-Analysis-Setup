# Unified GUI Layout (Lite + U3)

Cross-platform control panel for:
- FeelTech FY3200S function generator (dual-channel)
- Tektronix TDS2024B oscilloscope (VISA)
- LabJack U3/U3-HV DAQ (AIN/DIO, timers, watchdog)

## Features
- FY: per-channel setup, frequency sweeps; auto-baud fallback.
- Scope: capture raw bytes, calibrated CSV, quick PNG plots.
- U3: Read/Stream and **Config Defaults** tabs modeled after LJControlPanel.
- Automation: frequency sweep with single shared FY port/protocol override.
- Built-in `selftest` for protocol formatting and sanity checks.
