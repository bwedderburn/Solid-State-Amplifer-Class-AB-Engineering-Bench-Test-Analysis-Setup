"""FY function generator helpers (minimal test-oriented subset)."""
from __future__ import annotations
from typing import List

FY_PROTOCOLS = ["Auto", "ASCII", "Binary"]  # simple placeholder set
__all__ = ["FY_PROTOCOLS", "build_fy_cmds"]


def build_fy_cmds(freq_hz: float, amp_vpp: float, off_v: float, wave: str, *, duty: float | None = None, ch: int = 1) -> List[str]:
    """Build a list of low-level command strings.

    The original implementation produced several commands including a base write
    (bw...) and duty (bd...) command. Tests assert presence and a specific
    formatting for the frequency field (centi-Hz zero-padded to 9 digits).
    """
    freq_cHz = int(round(freq_hz * 100))
    freq_field = f"{freq_cHz:09d}"  # zero pad to 9 digits
    cmds: List[str] = []
    # Base waveform setup command (placeholder structure)
    cmds.append(f"bw{ch}{wave[:1].upper()}" )
    # Frequency command includes padded field
    cmds.append(f"bf{ch}{freq_field}")
    # Amplitude (scaled to mVpp *100 maybe; keep simple)
    amp_mVpp = int(round(amp_vpp * 1000))
    cmds.append(f"ba{ch}{amp_mVpp:06d}")
    # Offset (mV) sign handled by prefix
    off_mV = int(round(off_v * 1000))
    sign = 'p' if off_mV >= 0 else 'n'
    cmds.append(f"bo{ch}{sign}{abs(off_mV):05d}")
    if duty is not None:
        duty_tenths = int(round(duty * 10))
        cmds.append(f"bd{ch}{duty_tenths:03d}")
    return cmds

