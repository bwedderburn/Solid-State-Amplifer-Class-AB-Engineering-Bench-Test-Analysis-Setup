"""GUI tab construction helpers.

Extracted tabs:
- Generator: ``build_generator_tab``
- Scope: ``build_scope_tab``
- DAQ (U3): ``build_daq_tab``
- Automation / Sweep: ``build_automation_tab``
- Diagnostics: ``build_diagnostics_tab``

Pending extraction (planned): Automation/Sweep, Diagnostics.
"""
from .automation_tab import build_automation_tab  # noqa: F401
from .daq_tab import build_daq_tab  # noqa: F401
from .diag_tab import build_diagnostics_tab  # noqa: F401
from .gen_tab import build_generator_tab  # noqa: F401
from .scope_tab import build_scope_tab  # noqa: F401

__all__ = [
	'build_generator_tab','build_scope_tab','build_daq_tab',
	'build_automation_tab','build_diagnostics_tab','build_all_tabs'
]

def build_all_tabs(gui):
	"""Convenience helper: build all known tabs and return a dict.

	Any tab returning None (due to missing Qt) will appear with value None.
	Keys: generator, scope, daq, automation, diagnostics
	"""
	return {
		'generator': build_generator_tab(gui),
		'scope': build_scope_tab(gui),
		'daq': build_daq_tab(gui),
		'automation': build_automation_tab(gui),
		'diagnostics': build_diagnostics_tab(gui),
	}
