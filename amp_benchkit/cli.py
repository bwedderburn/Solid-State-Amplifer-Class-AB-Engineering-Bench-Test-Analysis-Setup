"""Package console script entrypoints.

This thin wrapper allows us to keep the large legacy `unified_gui_layout.py`
module while providing stable import paths for console_scripts.

Public functions:
- main(): generic CLI/GUI combined entry (mirrors python unified_gui_layout.py)
- main_gui(): convenience alias (still needs --gui flag for GUI launch)
"""
from __future__ import annotations

import sys

# Re-export version for convenience
try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("amp-benchkit")  # type: ignore
except Exception:  # pragma: no cover - best effort
    __version__ = "0.0.0"


def main(argv: list[str] | None = None) -> int:
    """Entry point for `amp-benchkit` console script.

    Parameters
    ----------
    argv : list[str] | None
        If provided, used instead of sys.argv[1:]. This makes unit testing simpler.
    Returns
    -------
    int
        Exit code (0 success, non-zero error).
    """
    if argv is not None:
        # Temporarily patch sys.argv while delegating
        old = sys.argv
        sys.argv = [old[0]] + list(argv)
        try:
            from unified_gui_layout import main as _legacy_main
            return _legacy_main() or 0
        finally:
            sys.argv = old
    else:
        from unified_gui_layout import main as _legacy_main
        return _legacy_main() or 0


def main_gui() -> int:
    """Explicit GUI entry (still requires --gui flag for now)."""
    from unified_gui_layout import main as _legacy_main
    return _legacy_main() or 0

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
