import pytest


def test_force_fail():
    pytest.fail("Intentional failure to trigger Codex Auto-Fix.")
