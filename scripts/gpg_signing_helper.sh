#!/usr/bin/env bash
# gpg_signing_helper.sh
# Lightweight helper to:
#  - Detect existing GPG signing key config
#  - Show guidance for generating a new key
#  - Export public key snippet
#  - Sanity-check signing setup
#
# This script DOES NOT automatically generate keys (interactive security decision)
# and will not export secret keys unless explicitly requested with a flag.
#
# Usage:
#  ./scripts/gpg_signing_helper.sh                 # show status & guidance
#  ./scripts/gpg_signing_helper.sh --export-pub    # print public key for configured signing key
#  ./scripts/gpg_signing_helper.sh --export-secret # (danger) export armored secret key to stdout
#  ./scripts/gpg_signing_helper.sh --test-commit   # create an empty signed test commit
#
# Environment:
#  GPG_BIN (default: gpg)
set -euo pipefail

GPG_BIN=${GPG_BIN:-gpg}
COLOR_Y="\033[33m"; COLOR_G="\033[32m"; COLOR_R="\033[31m"; COLOR_N="\033[0m"

err() { echo -e "${COLOR_R}ERROR:${COLOR_N} $*" >&2; }
info() { echo -e "${COLOR_G}INFO:${COLOR_N} $*"; }
warn() { echo -e "${COLOR_Y}WARN:${COLOR_N} $*"; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

usage() {
  sed -n '1,35p' "$0"
}

if ! have_cmd "$GPG_BIN"; then
  err "GPG binary '$GPG_BIN' not found. Install gnupg first."; exit 1
fi

SIGN_KEY=$(git config --get user.signingkey || true)
AUTO_SIGN=$(git config --get commit.gpgsign || true)
GPG_PROG=$(git config --get gpg.program || true)

mode_export_pub=false
mode_export_secret=false
mode_test_commit=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --export-pub) mode_export_pub=true ; shift ;;
    --export-secret) mode_export_secret=true ; shift ;;
    --test-commit) mode_test_commit=true ; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown argument: $1"; usage; exit 1 ;;
  esac
done

echo "--- GPG Signing Helper ---"
if [[ -n "$SIGN_KEY" ]]; then
  info "Configured signing key: $SIGN_KEY"
else
  warn "No git signing key configured (git config user.signingkey)."
fi

if [[ "$AUTO_SIGN" == "true" ]]; then
  info "Automatic commit signing is ENABLED (commit.gpgsign=true)."
else
  warn "Automatic commit signing is NOT enabled. Enable with: git config --global commit.gpgsign true"
fi

if [[ -n "$GPG_PROG" ]]; then
  info "Git configured GPG program: $GPG_PROG"
fi

echo
info "Available secret keys:" || true
$GPG_BIN --list-secret-keys --keyid-format LONG || true

cat <<'EOT'

GUIDANCE (manual steps):
1. Generate key:   gpg --full-generate-key   (choose RSA 4096, expiration 1y)
2. List keys:      gpg --list-secret-keys --keyid-format LONG
3. Configure git:  git config --global user.signingkey <KEYID>
                   git config --global commit.gpgsign true
                   git config --global gpg.program gpg
4. Export public:  gpg --armor --export <KEYID>
5. Revoke cert:    gpg --output revoke-<KEYID>.asc --gen-revoke <KEYID>
6. Test commit:    git commit --allow-empty -m "chore: test signed commit"

NOTE: Never commit any file named like private-key-backup-*.asc or revoke-*.asc
EOT

if $mode_export_pub; then
  if [[ -z "$SIGN_KEY" ]]; then
    err "No signing key configured; set user.signingkey first."; exit 1
  fi
  info "Armored public key for $SIGN_KEY:"; echo
  $GPG_BIN --armor --export "$SIGN_KEY" || { err "Failed to export public key"; exit 1; }
fi

if $mode_export_secret; then
  warn "Exporting SECRET key (armored) to stdout. Protect carefully."
  if [[ -z "$SIGN_KEY" ]]; then
    err "No signing key configured; set user.signingkey first."; exit 1
  fi
  $GPG_BIN --armor --export-secret-keys "$SIGN_KEY"
fi

if $mode_test_commit; then
  if [[ -z "$SIGN_KEY" ]]; then
    err "No signing key configured; cannot test signing."; exit 1
  fi
  info "Creating empty signed test commit..."
  git commit --allow-empty -m "chore: test signed commit (helper)" || warn "Commit may have failed (no changes?)"
  git log --show-signature -1 || true
fi

info "Done."
