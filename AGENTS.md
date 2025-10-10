# Repository Guidelines

This blended guide pairs a concise contributor checklist with the historical Codex playbook used to orchestrate automation. Start with the quick guide for day-to-day development, and refer to the preserved playbook when running Codex CLI sessions or onboarding new collaborators.

## Quick Contributor Guide
### Project Structure & Module Organization
Core Python package lives under `amp_benchkit/` for instrument drivers, automation flows, and shared GUI widgets; keep quick-launch scripts such as `unified_gui_layout.py` at the repo root for smoke checks. Place developer utilities in `scripts/`, persistent captures in `results/`, and documentation updates in `docs/` or `ROADMAP.md`. Mirror the package layout inside `tests/` to simplify discovery.

### Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create and enter the repo-local virtual environment.
- `pip install -e .[dev,test,gui]` — install runtime dependencies along with linting, typing, and GUI extras.
- `make deps` — bootstrap dependencies through the consolidated make target.
- `pytest -q` — run the unit suite; export `AMPBENCHKIT_FAKE_HW=1` when hardware is offline.
- `make gui` or `python unified_gui_layout.py gui` — launch the Qt interface for manual verification.

### Coding Style & Naming Conventions
Target Python 3.10+ with typed public APIs. Keep commits hook-clean by running `black` (configured for 100-character lines) and `ruff` through `pre-commit`. Use `snake_case` for functions and modules, `CamelCase` for Qt widgets and drivers, and uppercase constants for configuration keys. Document hardware assumptions inline when behavior deviates from lab defaults.

### Testing Guidelines
Name pytest modules `test_<module>.py`, store shared fixtures in `tests/fixtures/`, and skip hardware-dependent tests automatically when devices are absent. Exercise simulator paths with `AMPBENCHKIT_FAKE_HW=1`, maintain coverage across signal generation, instrument I/O, and GUI command paths, and keep golden CSV/JSON artifacts next to tests when validating capture pipelines.

### Commit & Pull Request Guidelines
Write imperative, present-tense commit subjects (for example, "Add scope simulator hooks"), keep bodies concise, and run `pre-commit run --all-files` plus `pytest -q` before pushing. Pull requests should link related issues, summarize user-facing changes, and attach screenshots or captured artifacts for GUI or plotting updates. Capture release-impacting notes in `CHANGELOG.md` inside the same PR.

### Security & Configuration Tips
Never commit device serial numbers or lab credentials. Override discovery via environment variables such as `FY_PORT`, `VISA_RESOURCE`, and `AMPBENCHKIT_SESSION_DIR` when scripting. Record new hardware setup steps in `EXODRIVER.md` or `SECURITY.md`, and surface missing dependencies (VISA backends, Exodriver) with actionable error messages.

## AGENTS.md — amp-benchkit (v0.3.6)

**Purpose**
This file tells OpenAI Codex CLI how to work on this repository end‑to‑end: what the project is, which “agents” (roles) exist, what they’re allowed to do without asking, and the standard playbooks for running, testing, and releasing the bench kit.

**Repository**: `bwedderburn/amp-benchkit`
**Local working dir**: `~/Documents/GitHub/amp-benchkit` (zsh shells: one for GUI tests, one for Codex CLI)
**Primary audience**: Codex CLI (v0.45.0 or later) operating as an assistant in your local shell.
**Hardware targets**: FY3200S/FY3224S signal generator (serial), Tektronix TDS2024B oscilloscope (USB/VISA), LabJack U3‑HV DAQ (USB; Exodriver).
**Software stack**: Python 3.10+; PySide6/PyQt5, PyVISA, pyserial, LabJackPython, numpy, matplotlib; pre‑commit/black for dev.

---

### 0) Getting Codex CLI ready in this repo

From `~/Documents/GitHub/amp-benchkit` run:

```
# Start Codex CLI in repo root
codex

# In Codex, initialize this file (one time or after edits)
/init

# (Optional) Pick a model & reasoning level
/model gpt-5-codex high

# Review what Codex is allowed to do
/approvals

# Verify current session
/status
```

> Tip: You can re‑run `/init` anytime after you update AGENTS.md to reload instructions.

---

### 1) Project overview (what Codex should optimize for)

- A reliable, repeatable amplifier test bench that **automates**: configure generator → trigger/capture scope → read/log DAQ → save CSV/JSON/PNG → optional GUI control.
- Tests beyond sine: crest‑factor‑controlled pink noise, tone‑bursts, multitone/IMD, small‑signal square checks.
- Works **headless (CLI)** and with a **Qt GUI** on macOS.
- Clean developer UX: virtualenv, `requirements.txt` + `requirements-dev.txt`, `pre-commit`, `black`, simple `pytest` tests.
- Safe hardware bring‑up: detect devices; degrade gracefully (skip tests) when hardware is missing.

---

### 2) Directory & key files (evolving)

> This repo is evolving; Codex should auto‑discover modules and tests on each run. Common elements include:

- `unified_gui_layout.py` (or `*_lite.py`): Qt GUI entrypoint (PySide6/PyQt5 fallback).
- `fy_control_gui.py`, `fy_3200_s_binary_gui.py`: FY3200S serial control utilities and GUI elements.
- `tds2024b_multichannel_capture.py`: Tektronix TDS2024B capture helpers (VISA/USB).
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`
- `docs/` and `tests/` (if present) – Codex should create/maintain missing ones as needed.
- `examples/` – sample scripts & data (Codex can add more for new features).

Codex may propose a future split such as:
```
src/benchkit/   # core library (visa.py, fy.py, u3.py, gui.py, io.py, signals.py, config.py)
bin/            # entrypoints: benchkit, benchkit-gui
tests/          # pytest-based tests
docs/
```

---

### 3) Environment setup & health checks

### Python & dependencies
```
# Prefer a venv in the repo
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt  # dev only
```

### macOS (common issues)
- **Qt not available** → `pip install PySide6` (already in requirements).
- **LabJack U3 Exodriver missing** → install `liblabjackusb` (macOS package or from LabJack).
- **VISA** → Ensure a backend (NI-VISA or pyvisa‑py). For NI-VISA on macOS, install the official package; otherwise pyvisa‑py can do USBTMC for many Tek scopes.

### Optional “fake hardware” switch
Codex may set this if hardware is disconnected (so tests still pass):
```
export AMPBENCHKIT_FAKE_HW=1
```

---

### 4) Agents (roles), goals, file scopes & done criteria

> Codex runs as a *team*. Each agent below is a hat Codex can wear. Codex can switch hats as needed.
> All agents must keep code formatted (`black`) and add/update tests when changing behavior.

### A) **Conductor / Orchestrator**
- **Goal**: Plan tasks, keep repo coherent, maintain docs & changelog, keep CI green.
- **Edits**: `AGENTS.md`, `README.md`, `CHANGELOG.md`, repo‑level scripts, release notes.
- **Done**: Plan executed, docs updated, CI & pre-commit pass, version bumped when appropriate.

### B) **Python Core Engineer**
- **Goal**: Implement/clean core modules (I/O, signal generation helpers, config, session logging).
- **Edits**: `src/*` or current flat modules; adds interfaces with type hints & tests.
- **Done**: Unit tests green; examples run; backward‑compatible unless major release.

### C) **Instrumentation Engineer (Scope & Generator)**
- **Goal**: Tek TDS2024B + FY3200S control; burst/trigger recipes; screenshot capture; VISA resource scanning.
- **Edits**: `tds2024b_*.py`, `fy_*.py`, `signals.py`.
- **Done**: Can detect devices, run a burst capture, save CSV+PNG; skip gracefully when devices absent.

### D) **DAQ Engineer (LabJack U3‑HV)**
- **Goal**: Multi‑channel logging (rails, temps), calibration/scaling; watchdog status.
- **Edits**: `u3_*.py`, `daq.py`.
- **Done**: Sampling works with real U3‑HV; simulated with `AMPBENCHKIT_FAKE_HW=1`.

### E) **GUI Engineer (Qt)**
- **Goal**: PySide6/PyQt5 GUI panes (Generator, Scope, DAQ, Automation/Sweep, Diagnostics).
- **Edits**: `unified_gui_layout*.py`, `gui.py`.
- **Done**: GUI launches on macOS; ports/visa scan; minimal “Run test” workflow OK; headless paths unaffected.

### F) **QA / Tests**
- **Goal**: pytest + fixtures for real/fake hardware; golden CSV/JSON; PNG hash similarity where feasible.
- **Edits**: `tests/`.
- **Done**: `pytest -q` green locally; pre‑commit hooks pass; example runs reproducible.

### G) **Release Engineer**
- **Goal**: versioning, tagging, changelog, GitHub releases; artifact bundle (CSV/JSON/PNG/meta).
- **Edits**: `pyproject.toml`, `CHANGELOG.md`, `.github/workflows/*` (if any).
- **Done**: Version bump, tag pushed, release notes generated; artifacts downloadable.

---

### 5) Command approvals (what Codex may do without asking)

> You control this via `/approvals`. Below are **recommended defaults** for this repo.
> If you want “full throttle,” switch to **Profile: bench‑full** (all checks = YES) then run `/approvals` and toggle accordingly.

### Profile: safe‑defaults (recommended when experimenting)
| Category | Allow | Notes |
|---|---|---|
| **Edit files inside repo** | ✅ | Create/modify/delete within repo; no writes outside unless approved. |
| **Run Python in venv** | ✅ | `python`, `pytest`, small scripts. |
| **Install Python deps in venv** | ✅ | `pip install -r requirements*.txt`; pin versions. |
| **Formatting & hooks** | ✅ | `black`, `pre-commit run --all-files`. |
| **Read system info** | ✅ | `system_profiler`, `python -V`, `pip list` (non-privileged). |
| **Git (local)** | ✅ | `git add/commit`, create branches; ask before force operations. |
| **Git (remote)** | ❓ | Ask before `git push`, PRs, tagging. |
| **Brew/system installs** | ❌ | Ask before `brew install`, any `sudo`. |
| **File operations outside repo** | ❌ | Ask first. |
| **Network ops (curl/wget)** | ❓ | Ask before downloading tools/data. |
| **Destructive ops** | ❌ | Never run `rm -rf` outside repo, disk format, killall, etc. |

### Profile: bench‑full (max capability for local workstation)
Toggle these to ✅ in `/approvals` when you explicitly want Codex to have full power:
- Git push, create PRs/tags/releases
- `brew install` system dependencies (e.g., NI‑VISA, libusb, jq)
- Download helper tools/data (e.g., test WAV/PNG fixtures)
- Modify shell rc files *only when asked* (zsh) – default is still **ask first**
- Long‑running jobs (captures/bursts); ok to run generators & scope sessions

> **Safety rail**: Even in **bench‑full**, Codex must ask before: `sudo` commands, writing outside the repo in sensitive locations, or deleting user data.


---

### 6) Standard playbooks

### A) Create/refresh local dev environment
```
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files --show-diff-on-failure
```

### B) Run GUI locally (macOS)
```
source .venv/bin/activate
python unified_gui_layout.py gui
# or the lite variant if present:
python unified_gui_layout_lite.py --gui
```

### C) Quick CLI capture (headless)
```
source .venv/bin/activate
python -m benchkit.run --freqs 100,1000,10000 --amp-vpp 2.0 --wave sine \
  --u3-channels 0,1 --save results/
# If no hardware present:
AMPBENCHKIT_FAKE_HW=1 python -m benchkit.run --demo
```

### D) Tests
```
source .venv/bin/activate
pytest -q
pre-commit run --all-files --show-diff-on-failure
black . --check
```

### E) Version bump & release (manual unless you enable bench‑full)
```
# Update version strings & CHANGELOG.md
git switch -c release/v0.3.7
# edit pyproject.toml / __init__.py / CHANGELOG.md
pre-commit run --all-files
git add -A && git commit -m "Bump to v0.3.7"
git tag v0.3.7
git push --set-upstream origin release/v0.3.7 --tags
# (optional) create GitHub Release with artifacts
```

---

### 7) Quality gates (Codex must satisfy before saying “done”)

- All modified files pass `black` and `pre-commit`.
- New/changed behavior is covered by at least one pytest.
- No regressions: `pytest -q` is green locally (fake mode acceptable if hardware is absent).
- CLI & GUI both still start (smoke test); GUI does not crash on missing hardware.
- Docs updated: `README.md` sections and/or `CHANGELOG.md` for user‑visible changes.
- When adding features: provide a runnable example under `examples/` and a test fixture (CSV/JSON/PNG).

---

### 8) Known pitfalls & how Codex should react

- **Exodriver not found** (LabJack U3): print a clear hint to install `liblabjackusb`; in tests, skip U3 tests unless `--with-u3` is set or device is detected.
- **Qt missing**: advise `pip install PySide6`; GUI must handle absence gracefully.
- **NI‑VISA not installed**: fall back to `pyvisa‑py` if available; list USBTMC resources; allow manual VISA string override in settings or env var.
- **Serial port ambiguity (FY3200S)**: provide a selector in GUI and `--port` CLI override.

---

### 9) Configuration & environment variables (Codex may add more)

- `AMPBENCHKIT_FAKE_HW=1` → enable simulators for scope/gen/DAQ.
- `AMPBENCHKIT_SESSION_DIR=...` → where to store captures/results.
- `FY_PORT=/dev/tty.usbserial-*` → manual override for FY3200S.
- `VISA_RESOURCE=USB0::0x0699::0x0363::...::INSTR` → manual override for Tek scope.
- `U3_CONNECTION=ethernet|usb` → if you want to force Ethernet (when Exodriver is missing).

---

### 10) Style & conventions

- Python ≥ 3.10, type hints encouraged.
- Formatting: `black` with line length 100 (see `pyproject.toml`).
- Avoid hard‑coding macOS paths; prefer env vars and discovery helpers.
- Tests should be deterministic; skip when hardware absent or put in “fake” mode.

---

### 11) Roadmap prompts Codex can use to grow the repo (future‑proofing)

- “Add scope screenshot saving (PNG) per test point and bundle CSV/JSON+PNG into a session folder.”
- “Implement crest‑factor‑controlled pink noise playback and leveling routine.”
- “Add tone‑burst sequencer with peak capture and timing markers.”
- “Integrate LabJack multi‑channel logging (rails & temps) with per‑channel scaling config.”
- “Expose Automation/Sweep pane in GUI tied to the CLI recipes.”
- “Write driver install notes for macOS (Exodriver, VISA backends).”
- “Add `benchkit`/`benchkit-gui` console scripts and package layout under `src/`.”

---

### 12) How Codex should ask for approval (when needed)

When an action is outside **safe‑defaults**, Codex should present:
- The **exact command(s)** it intends to run (single code block).
- A **one‑line reason** why it’s needed.
- Any **fallback** if declined.

Example:
```
# Plan to install NI-VISA for Tek VISA support
brew install --cask ni-visa
# Reason: Enable stable USBTMC for TDS2024B on macOS
# Fallback: use pyvisa-py; only limited features may work
```

---

### 13) Session quickstart for you

1. Open two zsh terminals in `~/Documents/GitHub/amp-benchkit`: one for GUI testing, one for Codex.
2. In the Codex terminal, run `codex` then `/init`, then `/approvals` and pick **safe‑defaults** or **bench‑full**.
3. Tell Codex what you want (e.g., “Write tests for `fy_3200_s_binary_gui.py` serial parser” or “Add a Scope screenshot feature and a `--save-png` flag”).
4. Use `/review` to inspect changes before committing.
5. Run the GUI/CLI and tests from the other terminal as you iterate.

---

_This AGENTS.md is intentionally future‑proof: Codex should extend roles, config, tests, and scripts as the project grows, and may propose a `src/` package layout once the codebase stabilizes._
