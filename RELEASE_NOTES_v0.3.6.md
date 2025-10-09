# amp-benchkit 0.3.6

## Highlights
- Fixes Tektronix capture routing so math/differential sweeps use the requested source channel instead of falling back to CH1.
- Normalises Tek scope source names (e.g. `MATH`, numeric strings) across setup, capture, and screenshots, preventing `ValueError` when using automation with math traces.
- Adds minor packaging cleanups and refreshed test/build artifacts for the release.

## Artifacts
- `dist/amp_benchkit-0.3.6.tar.gz`
- `dist/amp_benchkit-0.3.6-py3-none-any.whl`

## Checks
- `python3 -m pytest`
- `python3 -m build --no-isolation`

