# Release v0.3.1

## Highlights
- Added console entry points `amp-benchkit` and `amp-benchkit-gui`, plus a new `sweep` CLI subcommand for generating linear or logarithmic frequency lists.
- Bundled `results/sweep_scope.csv` and documented headless automation so users can demo sweeps without hardware on hand.
- Hardened FY generator channel-2 sweep handling to validate command sequences and frequency inputs.
- Toughened LabJack U3 helpers so they no-op cleanly when the device or driver is missing, keeping pytest runs green on non-hardware machines.
- Rebuilt the Docker image on top of `python:3.11-slim`, guaranteeing PySide6 wheels install cleanly and always copying the `patches/` directory.

## Upgrade Notes
- Install or upgrade via `pip install amp-benchkit` (or rebuild the Docker image) to pick up the new console scripts and curated sample data.
- If you depend on the Docker workflow, rebuild locally to pick up the new base image and dependency layout.

## Documentation
- README now includes sweep CLI examples and automation tips.
- See `CHANGELOG.md` for the full list of changes.
