import os

import pytest

HIL_ENABLED = os.environ.get("AMP_HIL") == "1"

pytestmark = pytest.mark.skipif(not HIL_ENABLED, reason="Hardware-in-loop tests disabled (set AMP_HIL=1 to enable)")

def test_hil_placeholder():
    # Placeholder for future real hardware interaction test (LabJack, FY, Tek)
    # This ensures CI remains green without hardware while providing a gate for local runs.
    assert HIL_ENABLED in (True, False)
