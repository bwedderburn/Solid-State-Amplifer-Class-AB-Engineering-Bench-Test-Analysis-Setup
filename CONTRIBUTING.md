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
