# GUI Modularization Plan

This document tracks the progressive extraction of GUI tab construction logic from
`unified_gui_layout.py` into `amp_benchkit.gui` submodules.

## Completed
- Generator tab -> `amp_benchkit.gui.gen_tab.build_generator_tab`
- Scope tab -> `amp_benchkit.gui.scope_tab.build_scope_tab`

## Completed (continued)
- DAQ (U3) tab -> `amp_benchkit.gui.daq_tab.build_daq_tab`

## Completed (continued)
- Automation / Sweep tab -> `amp_benchkit.gui.automation_tab.build_automation_tab`

## Completed (continued)
- Diagnostics tab -> `amp_benchkit.gui.diag_tab.build_diagnostics_tab`

All primary GUI tabs are now modular. Future improvements may include:
- Consolidating shared row-building patterns
- Optional pytest-qt smoke tests for each tab builder
- Removing deprecated DSP wrappers from `unified_gui_layout.py`

## Later Tabs
- Automation / Sweep tab -> `automation_tab.py`
- Diagnostics tab -> `diag_tab.py`

## Later Tabs
- DAQ (U3) tab -> `u3_tab.py`
- Automation / Sweep tab -> `automation_tab.py`
- Diagnostics tab -> `diag_tab.py`

Each extraction should keep side effects (attribute creation) explicit and avoid
introducing new dependencies inside helpers (reuse existing modules).

## Testing Approach
- Continue to rely on headless selftests / CLI for non-GUI logic.
- Potential future: lightweight Qt test harness using pytest-qt (optional extra).

## Open Considerations
- Central style/theming? Possibly a small utility once 2+ tabs extracted.
- Common helper for column layout repetition.
- Lazy instrument initialization to reduce startup latency.
