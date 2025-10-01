"""Stub config persistence."""
from __future__ import annotations
import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / '.config' / 'amp-benchkit' / 'config.json'
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

_cache = None


def load_config():
    global _cache
    if _cache is not None:
        return _cache
    # Support tests monkeypatching CONFIG_PATH to a string
    path = CONFIG_PATH if isinstance(CONFIG_PATH, Path) else Path(str(CONFIG_PATH))
    if path.exists():
        try:
            _cache = json.loads(path.read_text())
        except Exception:
            _cache = {}
    else:
        _cache = {}
    return _cache


def save_config(data):
    path = CONFIG_PATH if isinstance(CONFIG_PATH, Path) else Path(str(CONFIG_PATH))
    if not path.parent.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    path.write_text(json.dumps(data, indent=2))


def update_config(**kv):
    cfg = load_config()
    cfg.update(kv)
    save_config(cfg)
