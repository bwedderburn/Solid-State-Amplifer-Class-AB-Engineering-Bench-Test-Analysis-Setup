#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <new-version> [--tag]" >&2
  exit 1
fi
NEW_VERSION="$1"
TAG=${2:-}

INIT_FILE="amp_benchkit/__init__.py"
if ! grep -q '__version__' "$INIT_FILE"; then
  echo "Could not locate __version__ in $INIT_FILE" >&2
  exit 2
fi

# Update version in-place
awk -v ver="$NEW_VERSION" 'BEGIN{updated=0} {if($0 ~ /__version__ =/){print "__version__ = \"" ver "\"  # Single-source version"; updated=1} else print} END{if(!updated) exit 3}' "$INIT_FILE" > "$INIT_FILE.tmp"
mv "$INIT_FILE.tmp" "$INIT_FILE"

git add "$INIT_FILE"
git commit -m "chore: bump version to $NEW_VERSION"

if [[ "$TAG" == "--tag" ]]; then
  git tag -a "v$NEW_VERSION" -m "Release $NEW_VERSION"
  echo "Created tag v$NEW_VERSION (push with: git push --tags)"
fi

echo "Version bumped to $NEW_VERSION"
