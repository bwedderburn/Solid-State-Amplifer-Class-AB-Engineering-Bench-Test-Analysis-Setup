# Minimal container for amp-benchkit unified GUI + LabJack Exodriver
# Multi-stage could be added later; kept single stage for clarity.
FROM python:3.11-slim

# Ensure all packages are up-to-date and install build deps
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3-venv \
        python3-dev \
        build-essential \
        libusb-1.0-0-dev \
        git \
        bash \
        sudo \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Create isolated Python environment inside the image
RUN python3 -m venv $VIRTUAL_ENV

# Copy project
WORKDIR /app
COPY unified_gui_layout.py ./
COPY scripts/ ./scripts/
COPY patches/ ./patches/

# Install Python deps (explicit list; mirrors requirements/runtime.txt)
RUN $VIRTUAL_ENV/bin/pip install --upgrade pip \
    && $VIRTUAL_ENV/bin/pip install pyvisa pyserial PySide6 PyQt5 LabJackPython numpy matplotlib

# Build & install Exodriver via wrapper (will clone inside /app)
RUN chmod +x scripts/install_exodriver_alpine.sh \
    && ./scripts/install_exodriver_alpine.sh || true

# Ensure runtime linker finds liblabjackusb without manual export
ENV LD_LIBRARY_PATH=/usr/local/lib

# Default command prints help
CMD ["python", "unified_gui_layout.py", "selftest"]
