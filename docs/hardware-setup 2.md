# Hardware Setup

This guide covers recommended wiring and configuration for each supported instrument. When hardware is unavailable, enable simulator mode via `AMPBENCHKIT_FAKE_HW=1`.

## FeelTech FY3200S / FY3224S

- Connect the FY3200S to your host via USB-to-serial adapter.
- Let the application auto-detect the serial port, or override with `FY_PORT=/dev/tty.usbserial-XXXX`.
- Recommended default settings:
  - Waveform: sine
  - Channel: CH1
  - Voltage: 2 Vpp (adjust per DUT)
- The GUI exposes generator controls; CLI automation uses helper functions in `amp_benchkit.fy`.

## Tektronix TDS2024B Oscilloscope

- Connect over USB and ensure a VISA backend is installed (NI-VISA or `pyvisa-py`).
- Override discovery with `VISA_RESOURCE=USB0::...::INSTR` if multiple scopes are present.
- For external triggering:
  - Configure slope/level in automation via `use_ext`, `ext_slope`, and `ext_level`.
  - The GUI scope tab provides channel toggles and MATH subtraction helpers.

## LabJack U3-HV

- Install LabJack Exodriver (`liblabjackusb`) on macOS or Linux as described in `EXODRIVER.md`.
- Use USB for most setups; override connection with `U3_CONNECTION=ethernet` when required.
- The DAQ tab supports monitoring rails, temperatures, and digital pulses during sweeps.
- Simulator fallback returns deterministic values when `AMPBENCHKIT_FAKE_HW=1`.

## Session Directory

Set `AMPBENCHKIT_SESSION_DIR=/path/to/runs` to store captures (CSV/JSON/PNG). By default results are saved under `results/`, which is now `.gitignore`d for local experimentation.

## Safety Notes

- Never commit device serial numbers or lab credentials;-store them in environment variables.
- Document new lab setups in `EXODRIVER.md`, `SECURITY.md`, or the docs site so the team has a canonical reference.
