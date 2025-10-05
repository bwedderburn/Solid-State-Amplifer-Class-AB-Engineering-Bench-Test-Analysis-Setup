# Minimal container for amp-benchkit unified GUI + LabJack Exodriver
# Multi-stage could be added later; kept single stage for clarity.
FROM alpine:latest

# Ensure all packages are up-to-date
RUN apk update && apk upgrade --no-cache

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv

# System deps
RUN apk add --no-cache python3 py3-pip python3-dev build-base libusb-dev git bash \
    && python3 -m venv $VIRTUAL_ENV \
    && ln -s $VIRTUAL_ENV/bin/python /usr/local/bin/python \
    && ln -s $VIRTUAL_ENV/bin/pip /usr/local/bin/pip

# Copy project
WORKDIR /app
COPY unified_gui_layout.py ./
COPY scripts/ ./scripts/
COPY patches/ ./patches/ || true

# Install Python deps (explicit list; could move to requirements.txt later)
RUN pip install --upgrade pip \
    && pip install pyvisa pyserial PySide6 PyQt5 LabJackPython numpy matplotlib

# Build & install Exodriver via wrapper (will clone inside /app)
RUN chmod +x scripts/install_exodriver_alpine.sh \
    && ./scripts/install_exodriver_alpine.sh || true

# Optional LD path export (runtime) for musl systems if dynamic linker doesn't find lib
ENV LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}

# Default command prints help
CMD ["python", "unified_gui_layout.py", "selftest"]
