import os
import json
from amp_benchkit.config import load_config, update_config

def test_persistence_round_trip(tmp_path, monkeypatch):
    # Force config path into temp dir by monkeypatching module global if present
    from amp_benchkit import config as cfgmod
    cfg_file = tmp_path / 'config.json'
    if hasattr(cfgmod, 'CONFIG_PATH'):
        monkeypatch.setattr(cfgmod, 'CONFIG_PATH', str(cfg_file), raising=False)
    # Start with empty
    data = load_config()
    assert isinstance(data, dict)
    update_config(results_dir='rt_results', thd_resource='USB::INSTR', thd_refresh='750')
    data2 = load_config()
    assert data2.get('results_dir') == 'rt_results'
    assert data2.get('thd_resource') == 'USB::INSTR'
    assert data2.get('thd_refresh') == '750'
