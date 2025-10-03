"""Stub logging module providing setup_logging/get_logger."""
from __future__ import annotations
import logging as _logging

_logger = None

def setup_logging(verbose: bool = False):
    global _logger
    level = _logging.DEBUG if verbose else _logging.INFO
    _logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')
    _logger = _logging.getLogger('amp_benchkit')


def get_logger():  # returns global logger
    global _logger
    if _logger is None:
        setup_logging(False)
    return _logger
