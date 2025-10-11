# Exodriver Handling in amp-benchkit

The upstream LabJack Exodriver repository previously appeared as a stray gitlink in this repository (an accidentally committed submodule reference without a `.gitmodules` entry). That caused the entire driver history/clone state to be ambiguous and prevented clean cloning in some contexts.

## Current Strategy

We now vendor a *minimal* source snapshot of only the pieces needed for local builds in constrained environments:

Included:
- `exodriver/liblabjackusb/` (C sources + Makefile, NO compiled objects / shared libs)
- `exodriver/90-labjack.rules` (udev rule)
- `exodriver/install.sh` (upstream helper)
- `exodriver/INSTALL.*` (docs)
- Representative `examples/` sources (no build artefacts)

Removed / Excluded:
- Git metadata (`exodriver/.git` removed)
- All compiled objects (`*.o`) and shared libraries (`liblabjackusb.so*`)
- Any transient build products

## Rationale

1. Deterministic local build path for users without network access (air‑gapped labs)
2. Avoid shipping binaries to keep repository lightweight and auditable
3. Preserve upstream licensing and attribution – see `exodriver/README`

## If You Need the Full Upstream Repo

Clone directly instead of relying on the vendored snapshot:
```bash
git clone https://github.com/labjack/exodriver.git
```
Then run its normal build/install procedure, or our convenience script pointing at your clone:
```bash
EXO_DIR=/path/to/exodriver ./scripts/install_exodriver_alpine.sh
```

## Updating the Vendored Snapshot

1. Remove current directory (keep during review):
   ```bash
   rm -rf exodriver.new && git clone --depth 1 https://github.com/labjack/exodriver.git exodriver.new
   ```
2. Copy desired subset (sources, examples, rules) over existing `exodriver/`.
3. Delete any compiled artefacts (find & remove `*.o`, `liblabjackusb.so*`).
4. Commit with message: `chore(exodriver): refresh snapshot <upstream-sha>` including the upstream commit hash.
5. Update this file with the new upstream SHA.

Current upstream base commit: (fill in on next refresh).

## License

Refer to upstream licensing terms in `exodriver/README`. This project does not modify the license of the vendored code.

## Security / Integrity Note

Because this is a snapshot, verify integrity when updating by comparing diffs to the upstream commit. Avoid partial edits to C sources except for clearly documented patches.
