# Unified GUI Layout (Lite + U3)

![selftest](https://github.com/bwedderburn/amp-benchkit/actions/workflows/selftest.yml/badge.svg) ![coverage](https://img.shields.io/badge/coverage-pending-lightgrey)

Cross-platform control panel for:

```markdown
# Unified GUI Layout (Lite + U3)
![selftest](https://github.com/bwedderburn/amp-benchkit/actions/workflows/selftest.yml/badge.svg) ![coverage](https://img.shields.io/badge/coverage-pending-lightgrey)

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

## THD Calculation Dispatcher
`thd_fft` (via `unified_gui_layout`) provides:
1. Waveform mode: `thd_fft(t_array, v_array, f0=..., nharm=..., window='hann')`
2. Stub mode: `thd_fft(samples, fs_hz)` returning a placeholder when advanced DSP unavailable.

Heuristic: if both first args are sequence-like and NumPy exists → advanced mode; else stub.

### Example
```python
import math, unified_gui_layout as ugl
```jsonc
# Unified GUI Layout (Lite + U3)

![selftest](https://github.com/bwedderburn/amp-benchkit/actions/workflows/selftest.yml/badge.svg) ![coverage](https://img.shields.io/badge/coverage-pending-lightgrey)

Cross-platform control panel for:
- FeelTech FY3200S function generator (dual-channel)
- Tektronix TDS2024B oscilloscope (VISA)
- LabJack U3/U3-HV DAQ (AIN/DIO, timers, watchdog)

## Features

- FY: per-channel setup, frequency sweeps; auto-baud fallback
- Scope: capture raw bytes, calibrated CSV, quick PNG plots
- U3: Read/Stream and **Config Defaults** tabs modeled after LJControlPanel
- Automation: frequency sweep with single shared FY port/protocol override
- Built-in `selftest` for protocol formatting and sanity checks

## THD Calculation Dispatcher

`thd_fft` (via `unified_gui_layout`) provides two modes:
1. Waveform mode: `thd_fft(t_array, v_array, f0=..., nharm=..., window='hann')`
2. Stub mode: `thd_fft(samples, fs_hz)` placeholder when advanced DSP unavailable.

Heuristic: if both first args are sequence-like and NumPy exists → advanced mode; else stub.

### Example

```python
import math, unified_gui_layout as ugl
thd, f_est, a0 = ugl.thd_fft([0.0, 1.0, -0.5], 48000.0)
print(thd, f_est, a0)
```

## Installation Extras

Install extras as needed:

- GUI: `pip install "amp-benchkit[gui]"`
- DSP: `pip install "amp-benchkit[dsp]"`
- Hardware stacks: `pip install "amp-benchkit[serial,visa,labjack]"`
- Full dev: `pip install "amp-benchkit[gui,dsp,serial,visa,labjack,test]"`

### Release Helper

```bash
chmod +x scripts/release.sh
./scripts/release.sh 0.3.3 --tag
git push && git push --tags
```

### CLI Snippets

```bash
python unified_gui_layout.py thd-mode
python unified_gui_layout.py freq-gen --start 20 --stop 20000 --points 31 --mode log --format json
python unified_gui_layout.py thd-json capture.csv --f0 1000 --nharm 8 --window hann
```

### Real-Time THD Tab (Optional)

Provides live THD %, spectrum export (if matplotlib present), harmonic table, persistence.

### Spectrum CLI (Unreleased)

```bash
python unified_gui_layout.py spectrum --f0 1000 --points 4096 --fs 48000 --outdir results --output spectrum.png
```

### Persistent Results Directory

Configure once; reused by spectrum and THD exports.

## Developer: CodeGPT MCP Integration

Expose BenchKit utilities to a local MCP server for the CodeGPT extension.

### 1. Client Config

File: `.codegpt/mcp_config.json`

```jsonc
{
  "mcpServers": {
    "ampBenchKitLocal": { "url": "http://localhost:5001", "auth": "CHANGE_ME_SECURE_TOKEN" }
  }
}
```

### 2. Minimal FastAPI Server (`tools/mcp_server.py`)

```python
from __future__ import annotations
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from amp_benchkit.automation import build_freq_points
import unified_gui_layout as ugl

TOKEN = os.environ.get("AMP_BENCHKIT_MCP_TOKEN", "")
app = FastAPI(title="Amp BenchKit MCP")

def _auth(tok):
    if TOKEN and tok != TOKEN:
        raise HTTPException(status_code=401, detail="bad token")

class FreqReq(BaseModel):
    start: float; stop: float; points: int; mode: str = "log"
@app.post('/freq-points')
def freq_points(r: FreqReq, authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"frequencies": build_freq_points(r.start, r.stop, r.points, r.mode)}

class THDReq(BaseModel):
    samples: list[float]; fs: float | None = None
@app.post('/thd')
def thd(r: THDReq, authorization: str | None = Header(default=None)):
    _auth(authorization)
    thd_ratio, f0_est, fund = ugl.thd_fft(r.samples, r.fs or 48000.0)
    return {"thd": thd_ratio, "f0_est": f0_est, "fund_amp": fund}

@app.get('/ping')
def ping(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"ok": True}
```

### 3. Run

```bash
pip install fastapi uvicorn
export AMP_BENCHKIT_MCP_TOKEN=your-long-random-token
python -m uvicorn tools.mcp_server:app --port 5001 --reload
```

### 4. Security

Use a long random token; add TLS & rate limiting before exposing externally.

### 5. Hardware Opt-In

```bash
export AMP_BENCHKIT_ENABLE_U3=1
```

Restart processes after enabling to attempt actual u3 import.

### 6. Future Endpoints

`/sweep`, `/spectrum`, `/config` (job-based for long tasks).

Contribution tip: add tests for new endpoints.
