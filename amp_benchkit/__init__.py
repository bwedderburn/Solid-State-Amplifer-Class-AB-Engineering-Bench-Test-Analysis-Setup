"""amp_benchkit package

Lightweight namespace for instrumentation + GUI helpers.
The version constant is used by setuptools dynamic metadata in pyproject.

Merged histories: we retain the dynamic version style (tests enforce simple
numeric semver) and optionally expose a subset of dependency flags if present
in the lightweight `deps` module. Advanced DSP helpers are re-exported when
`dsp_ext` is available.
"""

__all__ = ["__version__"]

# Optional re-exports (older remote branch expected these symbols). We guard
# to avoid raising if stub deps module lacks attributes.
try:  # pragma: no cover - defensive
    from . import deps as _deps  # type: ignore
    for _name in [
        "HAVE_PYVISA",
        "HAVE_SERIAL",
        "HAVE_QT",
        "HAVE_U3",
        "dep_msg",
    ]:
        if hasattr(_deps, _name):  # only export if defined
            globals()[_name] = getattr(_deps, _name)
            __all__.append(_name)
except Exception:
    pass

# Re-export advanced DSP API if available
try:  # pragma: no cover
    from .dsp_ext import thd_fft_waveform, harmonic_table  # type: ignore
    __all__.extend(["thd_fft_waveform", "harmonic_table"])
except Exception:  # pragma: no cover
    pass

# Version (must remain simple semver: enforced by tests)
__version__ = "0.3.5"

