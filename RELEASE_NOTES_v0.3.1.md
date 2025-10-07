# Release v0.3.1

## Highlights
- Adds console scripts (`amp-benchkit`, `amp-benchkit-gui`) and a new `sweep` CLI subcommand for generating linear or logarithmic frequency lists.
- Bundles an example sweep dataset (`results/sweep_scope.csv`) and documents headless automation usage in the README.
- Improves FY generator sweep handling for channel 2 and strengthens LabJack U3 helpers for environments without attached hardware.
- Rebuilds the Docker image on top of `python:3.11-slim`, ensuring PySide6 wheels install cleanly and patches are copied consistently.

## Upgrade Notes
- Install the package (`pip install amp-benchkit`) to gain access to the new console entry points; the legacy `python unified_gui_layout.py` path remains but is considered deprecated.
- For Docker users, rebuild images to pick up the new base and dependency layout.

## Changelog Summary
See `CHANGELOG.md` for the structured list of additions, changes, and fixes included in this release.
