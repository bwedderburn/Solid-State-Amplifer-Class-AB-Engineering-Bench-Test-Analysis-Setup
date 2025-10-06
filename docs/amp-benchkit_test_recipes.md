# Amp Bench Test Methods — CF, Tone-Bursts, and IMD (FY32xx + TDS2024B + U3-HV)

**Purpose:** Ready-to-use methods for realistic amplifier testing beyond pure sine waves.

---

## 1) Crest-Factor (CF) Methods
**CF (dB) = 20·log10(Vpeak/VRMS)**. Music has higher CF than a sine → peaky signals with lower average heating at the same peak.

**Why:** Load the amp like music (peaky) instead of continuous-sine (space heater).

**Pink-Noise @ CF ≈ 12 dB — Procedure**
1. Source: pink noise (DAW/file or generator). Add a limiter so peaks sit just under clip.
2. Calibrate: Observe output across the dummy load; raise input until **peaks ~1–2% below clipping**.
3. Run 60–120 s:
   - Scope: log Vpeak, VRMS over time.
   - LabJack: log heatsink temp, rails (2–5 Hz).
4. Note: For equal peaks, **P_avg / P_sine ≈ 10^(−CF/10)** → at 12 dB ≈ **6.3%** of sine heating.

**Pass/Observe:** No clipping, stable rails, reasonable thermal rise, no limiter pumping.

---

## 2) Tone-Bursts (Dynamic Headroom)
**Why:** Exposes transient capability, supply sag, protection behavior.

**Recipe:** 1 kHz sine, **20 ms ON / 480 ms OFF** (duty ≈ 4%).
- Generator: burst or gated output.
- Scope: EXT TRIG from generator TTL; set **trigger hold-off ≈ 500 ms**.

**Steps:**
1. Raise burst level to first sign of clipping, then back off 1–2%.
2. Measure within one 20 ms window: **first-cycle vs. last-cycle amplitude** → droop (dB).
3. Correlate with rail recovery via LabJack logs.

**Pass/Observe:** Small droop (<0.5 dB), clean burst envelope, full recovery before next burst.

---

## 3) IMD (Intermodulation Distortion)
Reveals nonlinearity differently from THD.

### 3.1 SMPTE (60 Hz + 7 kHz, 4:1)
- Setup: 60 Hz large, 7 kHz at **−12 dB** relative (amplitude ratio 4:1).
- Measure: On FFT, check **7 kHz tone** and **±60 Hz sidebands** (6.94 kHz, 7.06 kHz…).
- Procedure: Drive to a representative level (e.g., ~½ rated sine); compute sideband sum relative to 7 kHz. Be consistent with your formula.

**Good:** Sidebands low (e.g., −60 dBc or better, device-dependent).

### 3.2 CCIF (19 kHz + 20 kHz, equal)
- Setup: equal-level 19 & 20 kHz.
- Measure: **1 kHz difference product**, plus **18/21 kHz** products, etc.
- Procedure: Peaks just under clip; FFT the output; report products relative to the two carriers.

**Good:** Small 1 kHz spur and low adjacent products.

---

## 4) Instrument Notes
**FY32xx:** Prefer burst mode for tone-bursts; otherwise gate. Avoid tee-loading; use 10× probe for the input tap.
**TDS2024B:** EXT TRIG from FY TTL; AC coupling to sanity-check symmetry, then DC for absolute levels. For binary pulls: `DATA:WIDTH 1`, `DATA:ENC RPB`, `CURVE?`.
**LabJack U3-HV:** Log rails, heatsink, ambient, and optional load temp at ~2–5 Hz.

---

## 5) Suggested Minimal Test Matrix
1. **Sine 1 kHz:** sweep to clip; then 20 Hz–20 kHz sweeps at 1/8, 1/3, and just-under-clip.
2. **Tone-burst 1 kHz:** 20 ms/500 ms; record peak droop and rail recovery.
3. **Pink-noise CF 12 dB:** peaks just-under-clip; 2 min temp/rail logging.
4. **IMD:** SMPTE and CCIF at mid and near-max clean levels.

---

## 6) Data to Save Per Run
- Metadata (amp/load/date), stimulus settings, Vpeak/VRMS/crest-factor, droop (dB), rail min/recov time, temps, FFT markers (spur levels).

---

### Appendix — Quick FY/Tek Commands (reference)
- TDS2024B capture: `DATA:WIDTH 1` → `DATA:ENC RPB` → `CURVE?` (binary) → parse.
- EXT TRIG: Connect FY TTL → Scope EXT TRIG; set **hold-off** near burst period.

---

© 2025 Amp-Benchkit notes. Keep methods consistent for apples-to-apples comparisons.
