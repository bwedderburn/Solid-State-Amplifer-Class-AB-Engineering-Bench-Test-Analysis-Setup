# Contributing Guide

Thanks for your interest in improving `amp-benchkit`! This document outlines how to get set up,
make changes, and propose them for inclusion.

## Table of Contents
- [Development Environment](#development-environment)
- [Workflow](#workflow)
- [Commit & PR Conventions](#commit--pr-conventions)
- [Testing](#testing)
- [Linting & Formatting](#linting--formatting)
- [Type Checking](#type-checking)
- [Release Process](#release-process)
- [Pre-Commit Hooks](#pre-commit-hooks)
- [Issue Reporting](#issue-reporting)
- [Security](#security)
- [Code of Conduct](#code-of-conduct)

## Development Environment

1. Clone the repository:
```bash
git clone https://github.com/your-org-or-user/amp-benchkit.git
cd amp-benchkit
```
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```
3. Install dependencies (core + dev extras):
```bash
pip install --upgrade pip
pip install -e .[dev,test,publish,gui]
```
4. (Optional) Install Exodriver (LabJack USB) if you have hardware:
```bash
./scripts/install_exodriver_alpine.sh
```

## Workflow

We use a standard GitHub fork & pull request model or feature branches within the main repo.

Typical flow:
1. Create a descriptive branch: `feat/automation-api`, `fix/tek-timeout`, etc.
2. Make your changes with small, logically separated commits.
3. Ensure tests, lint, and type checks pass locally (`make ci-local` planned) before opening a PR.
4. Open a Pull Request with a clear description and link any related issues.
5. Respond to review feedback; rebase / squash if requested.
6. A maintainer will merge once approvals and checks are green.

## Commit & PR Conventions

Use concise, imperative tense commit messages:
- `feat: add automation orchestration module`
- `fix: handle empty IEEE block response gracefully`
- `docs: expand README with TestPyPI instructions`
- `refactor: extract scope math helper`

Avoid very large omnibus commits. If you refactor + add a feature, consider separate commits.

## Testing

We use `pytest`. Fast-running tests include DSP functions, IEEE block parsing, config IO, and GUI tab smoke builds (Qt dependency skipped if missing).

Run all tests:
```bash
pytest -q
```
Run a subset:
```bash
pytest tests/test_dsp.py::test_thd_fft
```
Add tests for new public functions or bug fixes. Prefer deterministic synthetic data for DSP tests.

## Linting & Formatting

We use `ruff` for linting (and light autofix) plus Black-compatible style (enforced via ruff's formatting evolution if enabled later).

Manual run:
```bash
ruff check .
```
Autofix:
```bash
ruff check . --fix
```
(Formatting target to be added or integrated with `make format`).

## Type Checking

`mypy` is configured. Run:
```bash
mypy .
```
Incrementally add type hints—focus on stable public modules (`fy.py`, `tek.py`, `dsp.py`, `automation.py`).

## Release Process

1. Update `CHANGELOG.md` and bump version in `pyproject.toml`.
2. Run tests + build locally: `python -m build`.
3. Tag: `git tag vX.Y.Z` and push: `git push origin vX.Y.Z`.
4. GitHub Actions will build & (if configured) upload to PyPI.
5. Draft Release notes on GitHub (can copy from changelog).
6. Post-release: bump to `X.Y.(Z+1).dev0` if continuing development.

Release Candidates (TestPyPI): create a tag like `v0.3.0-rc1` (workflow forthcoming) to publish to TestPyPI.

## Pre-Commit Hooks

We use [pre-commit](https://pre-commit.com) to catch issues early and prevent oversized / unintended files from entering history.

Install once after setting up your virtualenv:
```bash
pip install pre-commit
pre-commit install
```
This installs a Git hook that runs automatically on `git commit`.

Included hooks:
* Style / hygiene: trailing whitespace, end-of-file newline, mixed line endings, merge conflict markers.
* Lint & format: `ruff` (with autofix) + `ruff-format` and `black` for consistent style.
* Types: `mypy` (best-effort; non-blocking refinement encouraged).
* Safeguards: block staging of virtual environment / `site-packages` content and binary blobs >5MB.

Manual run over all files:
```bash
pre-commit run --all-files
```

### Why these safeguards?
Earlier history accidentally included a full `.venv/` directory (large Qt binaries), bloating the repository and triggering GitHub rejection. We performed a history rewrite to remove it. These hooks make a recurrence very unlikely.

If you truly need to add a large artifact, prefer:
1. Generating it in CI at build/test time, or
2. Using Git LFS (only after discussion), or
3. Publishing it as a release attachment / external asset.

### Updating Hooks
After editing `.pre-commit-config.yaml` run:
```bash
pre-commit autoupdate
```
Commit the resulting version bumps in a single `chore(deps): update pre-commit hook revs` commit.

## Signed Commits (GPG)

We encourage (and may enforce) GPG-signed commits for provenance. To enable signing with the
project maintainer's pattern:

1. Generate (or use) an OpenPGP key matching an email on your GitHub account:
	```bash
	gpg --full-generate-key
	gpg --list-secret-keys --keyid-format=long
	```
2. Tell Git which key to use and enable signing:
	```bash
	git config --global user.signingkey <YOUR_KEY_ID>
	git config --global commit.gpgsign true
	```
3. Ensure a working TTY for pinentry (add to shell init):
	```bash
	export GPG_TTY=$(tty)
	```
4. Export your public key and add it at GitHub Settings → SSH and GPG keys:
	```bash
	gpg --armor --export <YOUR_KEY_ID>
	```
5. Make a test commit and verify it shows "Verified" on GitHub.

If working in a headless environment and pinentry fails, add `allow-loopback-pinentry` to
`~/.gnupg/gpg-agent.conf` and restart the agent:
```bash
echo allow-loopback-pinentry >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```

Historical commits are not retroactively re-signed to avoid disruptive history rewrites.
Only new commits need to be signed unless a security advisory states otherwise.

## Issue Reporting

When filing an issue, include:
- Environment (OS, Python version)
- Steps to reproduce (minimal code, if possible)
- Expected vs actual behavior
- Hardware context (FY model, Tek scope model, LabJack presence)

Label suggestions: `bug`, `enhancement`, `question`, `hardware`, `dsp`, `gui`.

## Security

If you discover a potential security issue (e.g., unsafe file handling, injection vector), please DO NOT open a public issue first. Instead, contact the maintainers privately (see README contact section once added). We'll coordinate a fix and disclosure if relevant.

## Code of Conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful and inclusive.

---
Thanks again for contributing! Thoughtful issues, tests, and reviews are all valuable contributions—even small doc fixes help.
