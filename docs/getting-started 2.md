# Quickstart

Follow these steps to get amp-benchkit running locally, with or without connected hardware.

## 1. Clone the Repository

```bash
git clone https://github.com/bwedderburn/amp-benchkit.git
cd amp-benchkit
```

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Install Dependencies

For daily development (CLI, tests, GUI) install the editable package with extras:

```bash
pip install -e .[dev,test,gui]
```

To build documentation locally:

```bash
pip install .[docs]
```

## 4. Run the Automated Tests

Enable fake hardware for environments without lab instruments:

```bash
export AMPBENCHKIT_FAKE_HW=1
python -m pytest -q
```

## 5. Launch the GUI

```bash
python unified_gui_layout.py gui
```

If Qt bindings are missing, reinstall the GUI extra (`pip install .[gui]`) or run the CLI recipes defined in the README.

## Next Steps

- Follow the [Hardware Setup](hardware-setup.md) guide when you have physical instruments.
- Review the [Development Workflow](development.md) for coding standards, linting, and commit conventions.
