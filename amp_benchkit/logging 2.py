"""Central logging utility for amp_benchkit.

Provides a get_logger() helper and setup_logging() to configure root handlers.
GUI and CLI can route textual output through this for consistency.
"""

from __future__ import annotations

import logging
import os
import pathlib
import sys
from logging.handlers import RotatingFileHandler

_DEFAULT_FORMAT = "[%(levelname).1s %(asctime)s] %(message)s"

_logger = logging.getLogger("amp_benchkit")

_def_handler: logging.Handler | None = None
_file_handler: logging.Handler | None = None


def _log_dir():
    base = (
        os.environ.get("XDG_STATE_HOME")
        or os.environ.get("XDG_CACHE_HOME")
        or os.path.expanduser("~/.cache")
    )
    p = pathlib.Path(base) / "amp-benchkit"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    return p


def setup_logging(
    verbose: bool = False,
    stream=None,
    file_logging: bool = True,
    max_bytes: int = 256_000,
    backups: int = 3,
):
    global _def_handler, _file_handler
    lvl = logging.DEBUG if verbose else logging.INFO
    _logger.setLevel(lvl)
    if _def_handler is not None:
        _logger.removeHandler(_def_handler)
    h = logging.StreamHandler(stream or sys.stderr)
    h.setFormatter(logging.Formatter(_DEFAULT_FORMAT, datefmt="%H:%M:%S"))
    h.setLevel(lvl)
    _logger.addHandler(h)
    _def_handler = h
    # Setup rotating file handler
    if file_logging:
        logdir = _log_dir()
        if logdir is not None:
            logfile = logdir / "benchkit.log"
            try:
                fh = RotatingFileHandler(logfile, maxBytes=max_bytes, backupCount=backups)
                fh.setFormatter(logging.Formatter(_DEFAULT_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
                fh.setLevel(lvl)
                if _file_handler is not None:
                    _logger.removeHandler(_file_handler)
                _logger.addHandler(fh)
                _file_handler = fh
            except Exception:
                pass
    _logger.debug("Logging initialized (verbose=%s)", verbose)
    return _logger


def get_logger():
    return _logger
