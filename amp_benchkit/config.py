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
    if CONFIG_PATH.exists():
        try:
            _cache = json.loads(CONFIG_PATH.read_text())
        except Exception:
            _cache = {}
    else:
        _cache = {}
    return _cache


def save_config(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def update_config(**kv):
    cfg = load_config()
    cfg.update(kv)
    save_config(cfg)
