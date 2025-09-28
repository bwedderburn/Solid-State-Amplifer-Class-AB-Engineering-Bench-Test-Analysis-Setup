#!/usr/bin/env bash
# install_exodriver_alpine.sh
# Purpose: Reproducibly build and install LabJack Exodriver (liblabjackusb) on Alpine (musl) or glibc Linux
# without permanently modifying a vendored exodriver clone. Safe to re-run.
#
# Usage:
#   ./scripts/install_exodriver_alpine.sh            # clone into ./exodriver if missing
#   EXO_DIR=/custom/path ./scripts/install_exodriver_alpine.sh
#
# Behaviour:
#  - Installs build deps (apk or apt) if available
#  - Builds liblabjackusb from source
#  - Installs udev rule (if Linux + udev present)
#  - Provides guidance for musl (no ldconfig)
set -euo pipefail

EXO_DIR=${EXO_DIR:-exodriver}
REPO_URL=${REPO_URL:-https://github.com/labjack/exodriver.git}
RULES_FILE=90-labjack.rules
SUPPORT_EMAIL="support@labjack.com"

log(){ printf "[exodriver-install] %s\n" "$*"; }
warn(){ printf "[exodriver-install][WARN] %s\n" "$*" >&2; }
fail(){ printf "[exodriver-install][ERROR] %s\n" "$*" >&2; exit 1; }

need_cmd(){ command -v "$1" >/dev/null 2>&1 || fail "Required command '$1' not found"; }

# Detect package manager
PKG=""; if command -v apk >/dev/null 2>&1; then PKG=apk; elif command -v apt-get >/dev/null 2>&1; then PKG=apt; fi

if [ -z "$PKG" ]; then
  warn "No supported package manager detected (apk/apt). Skipping dependency installation."
else
  case $PKG in
    apk)
      log "Installing build dependencies via apk";
      sudo apk add --no-cache build-base libusb-dev bash git || warn "apk dependency install failed" ;;
    apt)
      log "Installing build dependencies via apt";
      sudo apt-get update -y && sudo apt-get install -y build-essential libusb-1.0-0-dev git || warn "apt dependency install failed" ;;
  esac
fi

# Clone if missing
if [ ! -d "$EXO_DIR/.git" ]; then
  log "Cloning exodriver into $EXO_DIR";
  git clone --depth 1 "$REPO_URL" "$EXO_DIR" || fail "Clone failed";
else
  log "Using existing exodriver directory: $EXO_DIR";
fi

cd "$EXO_DIR"

# Build library
if [ -d liblabjackusb ]; then
  log "Building liblabjackusb";
  (cd liblabjackusb && make clean && make ) || fail "Build failed";
  log "Installing liblabjackusb (requires sudo)";
  (cd liblabjackusb && sudo make install ) || fail "Install failed";
else
  fail "liblabjackusb directory not found in exodriver repo"
fi

UNAME_S=$(uname -s)
if [ "$UNAME_S" = "Darwin" ]; then
  log "macOS detected: skipping udev rules";
  exit 0
fi

if [ "$UNAME_S" = "Linux" ]; then
  # udev rule installation
  if [ -f "$RULES_FILE" ]; then
    TARGET_DIR="";
    for d in /lib/udev/rules.d /etc/udev/rules.d; do
      if [ -d "$d" ]; then TARGET_DIR=$d; break; fi
    done
    if [ -n "$TARGET_DIR" ]; then
      log "Installing $RULES_FILE to $TARGET_DIR (sudo)";
      sudo cp -f "$RULES_FILE" "$TARGET_DIR/" || warn "Could not copy rule";
      if command -v udevadm >/dev/null 2>&1; then
        if udevadm control --reload-rules 2>/dev/null; then
          log "udev rules reloaded";
        else
          warn "udevadm reload failed; you may need to reconnect device or reboot";
        fi
      else
        warn "udevadm not found; reconnect device or reboot to apply rules";
      fi
    else
      warn "No udev rules directory found; skipping rule install";
    fi
  else
    warn "Rules file $RULES_FILE not found; skipping"
  fi
fi

# Dynamic linker considerations (musl vs glibc)
if command -v ldconfig >/dev/null 2>&1; then
  if sudo ldconfig 2>/dev/null; then
    log "Ran ldconfig to update linker cache";
  else
    warn "ldconfig failed; continuing"
  fi
else
  warn "ldconfig not present (likely musl). If Python cannot locate liblabjackusb, export:"
  echo '    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH'
fi

log "Exodriver install complete. Test with: python -c 'import u3; print("u3 OK")'"
