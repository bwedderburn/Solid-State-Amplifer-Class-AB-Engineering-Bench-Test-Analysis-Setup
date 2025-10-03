import importlib
import sys


def test_daq_optional_import_guard(monkeypatch):
    # Simulate absence of LabJackPython by ensuring 'u3' import raises ImportError
    if 'u3' in sys.modules:
        del sys.modules['u3']
    class DummyFinder:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'u3':
                raise ImportError('Simulated missing u3')
            return None
    sys.meta_path.insert(0, DummyFinder())
    try:
        mod = importlib.import_module('amp_benchkit.gui.daq_tab')
        # Access the internal placeholder variable to ensure import succeeded
        assert hasattr(mod, '_u3')
        # The guard sets _u3 to None when import fails
        assert getattr(mod, '_u3') is None
    finally:
        # Remove our finder to avoid side effects on other tests
        sys.meta_path = [mp for mp in sys.meta_path if not isinstance(mp, DummyFinder)]
