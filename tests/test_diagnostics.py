"""Tests for amp_benchkit.diagnostics module.

Validates that diagnostics collection works correctly, especially
when optional dependencies like pyvisa are missing.
"""


def test_collect_diagnostics_basic():
    """Verify basic diagnostics collection works."""
    from amp_benchkit.diagnostics import collect_diagnostics

    result = collect_diagnostics()
    assert isinstance(result, str)
    assert len(result) > 0
    assert "[Environment]" in result
    assert "[Dependencies]" in result
    assert "[Connectivity]" in result
    assert "[Hardware]" in result


def test_connectivity_section_handles_none_pyvisa(monkeypatch):
    """Verify _connectivity_section handles None _pyvisa gracefully.

    This test specifically validates the fix for the mypy type error
    where _pyvisa could be None but was accessed unconditionally.
    """
    import amp_benchkit.diagnostics as diag_mod

    # Simulate pyvisa being None (not installed)
    monkeypatch.setattr(diag_mod, "_pyvisa", None)
    monkeypatch.setattr(diag_mod, "HAVE_PYVISA", False)

    # This should not raise AttributeError
    title, lines = diag_mod._connectivity_section()

    assert title == "[Connectivity]"
    assert isinstance(lines, list)
    # When pyvisa is None, visa_lines should be empty and display "(none)"
    assert any("VISA resources:" in line for line in lines)


def test_connectivity_section_with_pyvisa_available(monkeypatch):
    """Verify _connectivity_section works when pyvisa is available."""
    import amp_benchkit.diagnostics as diag_mod

    # Only run this test if pyvisa is actually available
    if diag_mod._pyvisa is None:
        import pytest

        pytest.skip("pyvisa not available in this environment")

    # Ensure flags are set correctly
    monkeypatch.setattr(diag_mod, "HAVE_PYVISA", True)

    # This should not raise any errors
    title, lines = diag_mod._connectivity_section()

    assert title == "[Connectivity]"
    assert isinstance(lines, list)
    assert any("VISA resources:" in line for line in lines)


def test_diagnostics_selective_sections():
    """Verify individual sections can be toggled on/off."""
    from amp_benchkit.diagnostics import collect_diagnostics

    # Only environment
    result = collect_diagnostics(
        include_environment=True,
        include_dependencies=False,
        include_connectivity=False,
        include_hardware=False,
    )
    assert "[Environment]" in result
    assert "[Dependencies]" not in result
    assert "[Connectivity]" not in result
    assert "[Hardware]" not in result

    # Only connectivity
    result = collect_diagnostics(
        include_environment=False,
        include_dependencies=False,
        include_connectivity=True,
        include_hardware=False,
    )
    assert "[Environment]" not in result
    assert "[Dependencies]" not in result
    assert "[Connectivity]" in result
    assert "[Hardware]" not in result
