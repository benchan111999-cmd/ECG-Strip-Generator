# Rendering and calibration

## Current status

Rendering is not implemented in Milestone 0. No physical calibration claim is made.

## Planned renderer

Milestone 1 will implement deterministic Matplotlib rendering for one, two, and
twelve recorded leads using non-clinical fixtures, explicit timing, lead labels,
grid, and calibration pulse. Default speed/gain: 25 mm/s and 10 mm/mV.

## Verification requirements

PDF geometry must be checked numerically, followed by manual print measurement
at 100% scale with fit-to-page disabled before calibrated release. PNG is for
screen display and must not claim physical millimetre accuracy.

## Deferred appearance effects

ECG-Image-Kit remains optional and outside core milestones. It must never change
waveforms, timing, lead identity, or calibration.
