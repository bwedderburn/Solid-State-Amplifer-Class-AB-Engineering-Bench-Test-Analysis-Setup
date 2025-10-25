# AGENTS.md — amp-benchkit

**Repository**: `bwedderburn/amp-benchkit`
**Working dir**: `~/Documents/GitHub/amp-benchkit`
**Primary tool**: OpenAI Codex CLI (≥ 0.46.0) — this file guides Codex behavior, permissions, and playbooks.

## 0) What this project is
Automated audio amplifier bench testing across generator → scope → DAQ with both **CLI** and **Qt GUI** paths. Targets: FY3200S generator (serial), Tektronix TDS2024B scope (VISA/USBTMC), LabJack U3‑HV (USB/Ethernet). Runs with **fake hardware** for CI/review.

## 1) Current layout (authoritative)
```
amp_benchkit/            # package (drivers, dsp, gui helpers, utils)
tests/                   # pytest suite (fake-hw by default; hardware marked)
docs/                    # MkDocs site (optional)
unified_gui_layout.py    # GUI/headless entrypoint (supports `gui`, `selftest`)
requirements*.txt
.pre-commit-config.yaml
pyproject.toml
```
> Codex: discover modules at runtime; do not assume a flat script repo.

## 2) Quickstart (for humans *and* Codex)
```bash
# environment
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install .[gui]
# optional developer extras
pip install .[dev,test] || true

# pre-commit (format/lint/types)
pip install pre-commit && pre-commit install
pre-commit run --all-files --show-diff-on-failure

# headless smoke
python unified_gui_layout.py selftest

# launch GUI on desktop
python unified_gui_layout.py gui
```

## 3) Agents (roles Codex can assume)
- **Conductor** — coordinates tasks, keeps docs/CHANGELOG aligned.
- **Core Engineer** — implements package modules with type hints & tests.
- **Instrumentation Engineer** — FY3200S + TDS2024B control & capture flows.
- **DAQ Engineer** — U3‑HV sampling/scaling; skips cleanly when absent.
- **GUI Engineer** — PySide6/PyQt5 panes (Generator, Scope, DAQ, Sweep, Diag).
- **QA** — pytest fixtures, fake-hw mode, artifacts (CSV/JSON/PNG).
- **Release Engineer** — version, tags, changelog, release notes.

**Done criteria (all roles):** tests green (or skipped in fake-hw), hooks pass, docs updated, GUI & CLI smoke succeed.

## 4) Approvals profiles
Use `/approvals` to toggle. Defaults are cautious; switch to **bench-full** for local power.

### safe-defaults
- ✅ Edit files in repo, run Python/pytest, install pip deps in **.venv**, run pre-commit, local git add/commit/branch.
- ❓ Ask before: `git push`, network downloads, modifying shell rc files.
- ❌ No `brew`/system installs, no `sudo`, no writes outside repo.

### bench-full
- ✅ All of safe-defaults plus `git push --tags`, create GitHub releases, and `brew install` of required tools **when explicitly listed**.
- ❓ Always ask before `sudo` or touching files outside the repo.

**Approval request template Codex must use:**
```bash
# Plan
brew install --cask ni-visa
# Reason: enable stable VISA backend for Tektronix TDS2024B on macOS
# Fallback: use pyvisa-py (limited features)
```

## 5) Standard playbooks
### A) Dev env + hooks
```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install .[gui]
pip install .[dev,test] || true
pre-commit install
pre-commit run --all-files --show-diff-on-failure
```
### B) Run tests
```bash
# fake-hw default; mark real hardware tests with -m hardware
pytest -q
pytest -q -m "hardware"   # only when instruments are present
```
### C) GUI / headless
```bash
python unified_gui_layout.py gui
python unified_gui_layout.py selftest
```
### D) Release cadence (manual unless approved)
- Bump version in `pyproject.toml` (and package `__init__` if present).
- Update `CHANGELOG.md`.
- Tag `vX.Y.Z`, push branch + tags, create GitHub Release with artifacts.

## 6) Quality gates (must be true before “done”)
- `pre-commit run --all-files` passes (format/lint/types/end-of-file/trailing-ws).
- `pytest -q` green in fake-hw mode; hardware tests either green or marked/ignored.
- CLI `selftest` exits 0; GUI opens without crash and handles missing hardware.
- Docs/README updated for user-visible changes.

## 7) Common pitfalls & remedies
- **Exodriver/LabJack** missing → install `liblabjackusb` (macOS pkg or from LabJack). If absent, DAQ tests skip.
- **VISA backend** absent → prefer NI‑VISA; otherwise use `pyvisa-py` (USBTMC) and allow manual VISA string override.
- **Qt not found** → `pip install PySide6`.
- **Serial ambiguity (FY3200S)** → expose port picker in GUI and support `--port`/`FY_PORT`.

## 8) Configuration (env vars Codex may use)
- `AMPBENCHKIT_FAKE_HW=1` — force simulators (scope/gen/daq).
- `AMPBENCHKIT_SESSION_DIR=/path/to/results` — capture output root.
- `FY_PORT=/dev/tty.usbserial-*` — override FY3200S serial.
- `VISA_RESOURCE=USB0::0x0699::...::INSTR` — override Tek scope.
- `U3_CONNECTION=ethernet|usb` — force U3 path if needed.

## 9) Codex session bootstrap
Run in repo root:
```
/init
/model gpt-5-codex high
/approvals            # choose safe-defaults or bench-full
/status
```
To execute bulk repo maintenance, prefer a single cohesive plan, then `/review` the diff before commit.

## 10) Roadmap prompts Codex can take on
- Add scope screenshot saving (PNG) & bundle CSV/JSON/PNG per session.
- Implement crest‑factor‑controlled pink noise + leveling.
- Add tone‑burst sequencer & peak capture.
- Expand fake-hw backends + fixtures for CI determinism.
- Provide `benchkit` / `benchkit-gui` console scripts under `pyproject.toml`.
