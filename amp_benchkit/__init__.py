"""amp_benchkit package

Lightweight namespace for instrumentation + GUI helpers.
The version constant is used by setuptools dynamic metadata in pyproject.
"""

__all__ = [
    "__version__",
]

# Re-export advanced DSP API if available
try:
    from .dsp_ext import thd_fft_waveform, harmonic_table  # type: ignore
    __all__.extend(["thd_fft_waveform", "harmonic_table"])
except Exception:  # pragma: no cover
    pass

# Version bump (must remain simple semver: enforced by tests)
__version__ = "0.3.5"
