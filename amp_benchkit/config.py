"""Simple JSON config persistence for amp_benchkit.

Stores small user preferences like last used FY port, protocol, scope resource.
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
from typing import Any

CONFIG_DIR = pathlib.Path(os.path.expanduser('~/.config/amp-benchkit'))
CONFIG_PATH = CONFIG_DIR / 'config.json'
_lock = threading.Lock()
_DEFAULT = {
    "fy_port": "",
    "fy_protocol": "FY ASCII 9600",
    "scope_resource": "",
}

_cached: dict[str, Any] | None = None

def load_config() -> dict[str, Any]:
    global _cached
    with _lock:
        if _cached is not None:
            return dict(_cached)
        try:
            if CONFIG_PATH.exists():
                with CONFIG_PATH.open('r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
        except Exception:
            data = {}
        # merge defaults
        cfg = dict(_DEFAULT); cfg.update({k:v for k,v in data.items() if isinstance(k,str)})
        _cached = cfg
        return dict(cfg)

def save_config(cfg: dict[str, Any]):
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = dict(_DEFAULT); data.update(cfg or {})
        with CONFIG_PATH.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        global _cached
        _cached = dict(data)

def update_config(**kwargs):
    cfg = load_config(); cfg.update(kwargs); save_config(cfg)
