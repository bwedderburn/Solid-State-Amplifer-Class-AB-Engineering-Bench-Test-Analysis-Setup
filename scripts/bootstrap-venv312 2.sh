#!/usr/bin/env bash
set -euo pipefail

PY_VERSION="${PY_VERSION:-3.12.4}"
VENV_NAME="${VENV_NAME:-.venv312}"

if ! command -v pyenv >/dev/null 2>&1; then
  echo "pyenv is required. Install it (e.g. 'brew install pyenv') and re-run." >&2
  exit 1
fi

echo "[bootstrap] Ensuring Python ${PY_VERSION} is available via pyenv..."
pyenv install --skip-existing "${PY_VERSION}"

echo "[bootstrap] Setting local Python version..."
pyenv local "${PY_VERSION}"

if [[ -d "${VENV_NAME}" ]]; then
  echo "[bootstrap] Removing existing virtualenv ${VENV_NAME}..."
  rm -rf "${VENV_NAME}"
fi

echo "[bootstrap] Creating virtualenv ${VENV_NAME}..."
python -m venv "${VENV_NAME}"

echo "[bootstrap] Installing project dependencies (including GUI extras)..."
(
  # shellcheck disable=SC1090
  source "${VENV_NAME}/bin/activate"
  pip install --upgrade pip
  pip install -e ".[dev,test,gui]"
  python - <<'PY'
import sys
try:
    from PyQt5.QtWidgets import QApplication
    QApplication(sys.argv)
    print("[bootstrap] Qt (PyQt5) initialisation succeeded.")
except Exception as exc:
    print("[bootstrap] WARNING: Qt initialisation failed:", exc)
PY
)

cat <<EOF

[bootstrap] Done.
Activate the environment with:
  source ${VENV_NAME}/bin/activate

Launch the GUI with:
  python unified_gui_layout.py gui

Run full hardware tests with:
  AMP_HIL=1 pytest -q -rs
EOF
