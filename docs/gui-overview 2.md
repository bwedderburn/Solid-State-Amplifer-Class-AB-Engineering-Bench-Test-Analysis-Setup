# GUI Layout Overview

The Qt interface (PySide6/PyQt5) mirrors the automation modules and organizes controls into dedicated tabs.

## Generator Tab

- Configure FY3200S waveform, amplitude, offset, and channel routing.
- Supports loading presets and issuing burst sequences.
- Displays connection status and last command acknowledgement.

## Scope Tab

- Select Tektronix TDS2024B channels or the MATH trace.
- Configure trigger settings (edge slope, level) and acquisition timebase.
- Capture snapshots or stream data into the automation pipeline.

## DAQ Tab

- Monitor LabJack U3-HV analog/digital inputs.
- Fire digital pulses to coordinate with external triggers.
- Auto-configure device on connect when `u3_autoconfig` is enabled.

## Automation Tab

- Run predefined sweeps (frequency response, THD, crest-factor checks).
- Displays progress updates and logs instrumentation errors.
- Generates CSV/JSON outputs into the configured session directory.

## Diagnostics Tab

- Shows consolidated log messages from all drivers.
- Includes VISA/U3 discovery helpers for troubleshooting.

## Launching the GUI

```bash
python unified_gui_layout.py gui
```

Run with `AMPBENCHKIT_FAKE_HW=1` to exercise the UI without hardware. All tabs should load using simulator backends; the testing guide explains expectation for HIL verification.
