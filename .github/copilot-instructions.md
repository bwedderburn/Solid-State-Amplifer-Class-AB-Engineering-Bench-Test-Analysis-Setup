# AI Agent Instructions for Amp Benchkit

## Project Overview
This is a cross-platform test and measurement application for audio amplifier benchmarking, built around a single Python file (`unified_gui_layout.py`) that provides GUI and CLI interfaces for controlling:

- **FeelTech FY3200S** dual-channel function generator via serial
- **Tektronix TDS2024B** oscilloscope via VISA/USB 
- **LabJack U3/U3-HV** DAQ device for digital I/O, analog inputs, and automation triggers

The application enables automated frequency response sweeps, THD analysis, and audio performance characterization through coordinated instrument control.

## Architecture & Key Patterns

### Monolithic Design Philosophy
- **Single file architecture**: All functionality consolidated in `unified_gui_layout.py` (~2000+ lines)
- **Optional dependencies**: Graceful degradation when hardware drivers unavailable (pyvisa, pyserial, LabJackPython, Qt)
- **Fallback mechanisms**: Auto-detection of Qt binding (PySide6 → PyQt5), serial port scanning, baud rate fallbacks

### Hardware Abstraction Layers
```python
# FY3200S: Command formatting with strict length limits (15 chars)
def _fy_cmds(freq_hz, amp_vpp, off_v, wave, duty=None, ch=1):
    # Returns list of formatted commands like ["bf100000000", "ba2.00"]

# Tektronix: IEEE-488 block data parsing
def _decode_ieee_block(raw: bytes) -> bytes:
    # Handles "#3100<data>" format from scope CURVE? queries

# LabJack: U3-specific feedback system abstraction
def u3_set_line(line: str, state: int):
    # Maps "FIO3", "EIO1" to global I/O numbers (0-7, 8-15, 16-19)
```

### Error Handling Pattern
- **Best-effort operations**: Hardware commands wrapped in try/except with graceful fallbacks
- **Multiple protocol attempts**: Serial commands try different baud/EOL combinations automatically
- **Resource cleanup**: Context managers and explicit close() calls in finally blocks

## Critical Development Workflows

### Testing & Validation
```bash
# Primary validation method - no hardware required
python3 unified_gui_layout.py selftest

# Hardware diagnostics when instruments available  
python3 unified_gui_layout.py diag

# GUI launch (requires Qt installation)
python3 unified_gui_layout.py --gui
```

### Code Formatting
```bash
# Uses Black with specific configuration from pyproject.toml
black .  # 100-char line length, Python 3.10+

# CI validation
black --check .
```

## Hardware-Specific Conventions

### FY3200S Function Generator
- **Centi-Hz encoding**: 1000 Hz → `bf100000000` (frequency × 100, 9-digit zero-padded)
- **Amplitude precision**: 0.01V steps, clamped to 0.00-99.99V
- **Duty cycle**: 0.1% precision, encoded as integer tenths (12.3% → `bd123`)
- **Protocol variants**: FY ASCII (9600 baud, LF) vs Auto (115200 baud, CRLF)

### Tektronix Scope Integration  
- **IEEE block format**: Scope returns `#<digits><length><data>` for waveform queries
- **Calibration chain**: Raw bytes → (data-offset) × scale + zero → calibrated volts
- **Multi-model support**: Best-effort commands for different TDS series models
- **External triggering**: Automated single-shot acquisition with EXT trigger support

### LabJack U3 Orchestration
- **Global I/O mapping**: FIO0-7 (0-7), EIO0-7 (8-15), CIO0-3 (16-19) 
- **Config persistence**: `setDefaults()` saves current state as power-on configuration
- **Test Panel concept**: 1Hz runtime loop for interactive I/O control without persistence
- **Feedback system**: Batch operations via `getFeedback()` for efficiency

## Integration Patterns

### Automated Sweep Workflows
The automation system coordinates all three instruments:
1. **U3 auto-configuration**: Apply DAQ settings based on UI selections
2. **FY frequency stepping**: Shared port/protocol across channels  
3. **Scope triggering**: Optional EXT trigger from U3 pulse lines
4. **KPI computation**: THD via FFT, frequency response, knee detection

### Cross-Instrument Synchronization
```python
# Typical automation sequence
u3_autoconfig_runtime(base='factory', pulse_line='FIO3')  # Configure DAQ
fy_apply(freq_hz=1000, amp_vpp=2.0, ch=1, port=auto_port) # Set generator
scope_set_trigger_ext(slope='Rise', level=1.5)            # Configure trigger
scope_arm_single()                                        # Arm acquisition
u3_pulse_line('FIO3', width_ms=10)                       # Trigger pulse
scope_wait_single_complete(timeout_s=3.0)                # Wait for capture
t, v = scope_capture_calibrated(ch=1)                    # Get waveform
```

## Key Files & Directories

- **`unified_gui_layout.py`**: Main application - all GUI tabs, instrument drivers, automation
- **`requirements.txt`**: Core dependencies (numpy, matplotlib, pyvisa, pyserial, PySide6, LabJackPython) 
- **`pyproject.toml`**: Black formatter config (100-char line, Python 3.10+)
- **`.github/workflows/selftest.yml`**: CI across Ubuntu/macOS, Python 3.10/3.11
- **`results/`**: Auto-created output directory for CSV data, PNG plots, analysis results

## Common Pitfalls & Guidelines

### Hardware Dependencies
- Always check `HAVE_*` flags before calling hardware functions
- Provide install hints via `INSTALL_HINTS` dict when dependencies missing
- Use `find_fy_port()` for automatic serial port detection (prefers USB-serial adapters)

### GUI Architecture  
- Qt binding abstraction allows PySide6/PyQt5 compatibility
- Fixed-width fonts preferred for test panel hex displays
- Progress bars and `QApplication.processEvents()` for long operations

### Measurement Accuracy
- **Calibrated captures essential**: Use `scope_capture_calibrated()` not raw bytes for analysis
- **Windowing for THD**: Hann window reduces spectral leakage in FFT analysis  
- **Settling times**: Respect `dwell` parameters for generator/scope synchronization

When modifying this codebase, maintain the single-file architecture, preserve graceful degradation for missing hardware, and ensure selftest passes before commits.