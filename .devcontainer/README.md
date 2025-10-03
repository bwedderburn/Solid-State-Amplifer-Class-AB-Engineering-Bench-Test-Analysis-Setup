# Devcontainer notes

- PySide6 GUI won’t render in Codespaces (no display), but `selftest` and non-GUI tasks run fine.
- VISA/U3 hardware isn’t present here; tests are designed to avoid hardware access by default.
- Run:
  - `python3 unified_gui_layout.py selftest`
  - `python3 unified_gui_layout.py --gui` (locally on your Mac, not in Codespaces)
