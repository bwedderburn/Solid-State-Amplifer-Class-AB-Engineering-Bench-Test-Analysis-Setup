# Development Workflow

## Coding Standards

- Target Python 3.10+ with type hints on public APIs.
- Formatting: `black` (line length 100) and `ruff`. Both run via `pre-commit`.
- Naming:
  - Modules/functions: `snake_case`
  - Qt widgets/classes: `CamelCase`
  - Constants/env keys: `SCREAMING_SNAKE_CASE`

Run the linters before committing:

```bash
pre-commit run --all-files
```

## Testing

- Unit tests live in `tests/`, mirroring the `amp_benchkit/` package layout.
- Common command:

  ```bash
  AMPBENCHKIT_FAKE_HW=1 python -m pytest -q
  ```

- Hardware-dependent tests auto-skip when devices are offline.
- Add golden CSV/JSON fixtures beside tests when validating capture pipelines.

## Virtual Environment Helpers

The repository ships with a bootstrap script for Python 3.12:

```bash
scripts/bootstrap-venv312.sh
```

Adjust script versions as needed and commit updates so the team can reproduce your environment.

## Commit & PR Guidelines

- Use imperative commit subjects (e.g., “Add scope simulator hooks”).
- Before pushing run:
  ```bash
  pre-commit run --all-files
  python -m pytest -q
  ```
- Update `CHANGELOG.md` for user-visible changes and attach screenshots/artifacts for GUI updates.

## Local Documentation Preview

To work on this documentation locally:

```bash
pip install .[docs]
mkdocs serve
```

Open <http://127.0.0.1:8000> in your browser for live reload during edits.
