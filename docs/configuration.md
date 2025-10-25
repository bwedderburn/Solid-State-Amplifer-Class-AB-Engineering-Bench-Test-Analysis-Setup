# Configuration & Environment

## Core Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `AMPBENCHKIT_FAKE_HW` | Enable simulator paths for scope/generator/DAQ | `0` (real hardware) |
| `AMPBENCHKIT_SESSION_DIR` | Directory to store captures/results | `results/` |
| `FY_PORT` | Override FeelTech serial port discovery | auto-detect |
| `VISA_RESOURCE` | Override Tektronix VISA resource string | auto-detect |
| `U3_CONNECTION` | Force LabJack connection type (`usb` or `ethernet`) | `usb` |
| `AMP_HIL` | Flag to enable hardware-in-loop pytest suite | unset |

Set variables per session (macOS/Linux):

```bash
export AMPBENCHKIT_FAKE_HW=1
export FY_PORT=/dev/tty.usbserial-XYZ
```

## Session Output

- Local experiment artifacts live under `results/` (now ignored by Git).
- To keep a clean history, store shareable captures in versioned directories (e.g., `results/v0.3.6/`).

## Logging

- The automation workflow accepts a `logger` callable to aggregate messages.
- The GUI surfaces instrument logs in the Diagnostics tab; persist to disk via session directory configuration.

## Updating Dependencies

- Runtime pins are managed in `pyproject.toml` and `requirements.txt`.
- Use `pip install -e .[dev,test,gui]` to update your environment.
- Docs tooling lives under the `docs` optional extra (`pip install .[docs]`).

## Secrets

Never commit credentials, instrument serial numbers, or lab IPs. Use environment variables or `.env` files excluded via `.gitignore`.
