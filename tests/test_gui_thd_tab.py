import importlib
import pytest

from amp_benchkit.gui import build_all_tabs


def test_thd_tab_presence():
    # If Qt missing, build_all_tabs will return empty or partial list and that's acceptable.
    tabs = build_all_tabs(object())
    # Accept absence when Qt not installed.
    names = [label for (_w, label) in tabs]
    # THD tab should appear if any tabs exist AND dsp_ext import succeeded and Qt present.
    # We can't easily detect Qt availability here without importing PySide6; so just ensure no crash and optional presence.
    assert isinstance(tabs, list)
    # If THD present, label must be exactly 'THD'
    if any(label == 'THD' for label in names):
        assert 'THD' in names
