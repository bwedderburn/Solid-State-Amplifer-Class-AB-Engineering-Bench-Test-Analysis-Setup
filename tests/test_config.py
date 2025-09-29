import importlib
import json
from pathlib import Path

import pytest


def test_config_roundtrip(tmp_path):
    # Import config module and redirect paths to temporary directory
    import amp_benchkit.config as cfg

    cfg.CONFIG_DIR = tmp_path / "conf"
    cfg.CONFIG_PATH = cfg.CONFIG_DIR / "config.json"
    cfg._cached = None  # reset cache

    # Initial load should create defaults (file absent)
    data1 = cfg.load_config()
    assert data1["fy_protocol"] == "FY ASCII 9600"
    assert cfg.CONFIG_PATH.exists() is False  # load does not write automatically

    # Save with an override
    data1["fy_port"] = "ttyUSB_TEST"
    cfg.save_config(data1)
    assert cfg.CONFIG_PATH.exists()

    # Reload and ensure persistence
    cfg._cached = None
    data2 = cfg.load_config()
    assert data2["fy_port"] == "ttyUSB_TEST"
    assert data2["fy_protocol"] == "FY ASCII 9600"  # default preserved

    # update_config convenience
    cfg.update_config(scope_resource="USB::TEST")
    cfg._cached = None
    data3 = cfg.load_config()
    assert data3["scope_resource"].startswith("USB::TEST")


def test_config_corrupt_file(tmp_path):
    import amp_benchkit.config as cfg

    cfg.CONFIG_DIR = tmp_path / "conf"
    cfg.CONFIG_PATH = cfg.CONFIG_DIR / "config.json"
    cfg.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Write corrupt JSON
    cfg.CONFIG_PATH.write_text("{garbage", encoding="utf-8")
    cfg._cached = None
    data = cfg.load_config()
    # Should fall back to defaults gracefully
    assert data["fy_protocol"] == "FY ASCII 9600"
    # Save after corruption should overwrite with valid JSON
    cfg.save_config(data)
    json.loads(cfg.CONFIG_PATH.read_text(encoding="utf-8"))  # no exception


def test_u3_disabled_graceful(monkeypatch):
    # Simulate environment with no U3 support and ensure helper no-ops without error.
    import amp_benchkit.deps as deps
    monkeypatch.setattr(deps, "HAVE_U3", False, raising=False)
    # Reload main module so its cached constant reflects False
    import unified_gui_layout as main_mod
    importlib.reload(main_mod)
    # Calling u3_set_line should not raise even though U3 disabled
    main_mod.u3_set_line("FIO3", 1)
