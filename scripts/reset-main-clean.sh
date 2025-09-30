#!/usr/bin/env bash
#
# Fully resync local 'main' branch to 'origin/main' and remove ALL
# local-only commits, uncommitted changes, untracked files, and ignored files.
#
# Creates a timestamped backup branch before doing anything destructive.
#
# USE WITH CAUTION.
#
# What you lose:
#   - Local commits not on origin/main
#   - Uncommitted changes
#   - Untracked files and directories
#   - Ignored files (node_modules, build outputs, caches, etc.)
#
# Recovery path:
#   - Checkout the created backup branch and cherry-pick what you need.
#
# Optional DRY RUN:
#   ./reset-main-clean.sh --dry-run
#
# Force (skip confirmations):
#   ./reset-main-clean.sh --yes
#
set -euo pipefail

COLOR_RED="$(tput setaf 1 || true)"
COLOR_YELLOW="$(tput setaf 3 || true)"
COLOR_GREEN="$(tput setaf 2 || true)"
COLOR_RESET="$(tput sgr0 || true)"

confirm=yes
dry_run=no

for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=yes ;;
    --yes|-y) confirm=no ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

echo "${COLOR_YELLOW}>>> Verifying repository...${COLOR_RESET}"

# Ensure we're inside a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "${COLOR_RED}Not inside a Git repository. Aborting.${COLOR_RESET}" >&2
  exit 1
fi

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "main" ]]; then
  echo "${COLOR_YELLOW}Current branch is '${current_branch}', switching to 'main'...${COLOR_RESET}"
  if git show-ref --verify --quiet refs/heads/main; then
    [[ "$dry_run" == yes ]] || git checkout main
  else
    echo "${COLOR_RED}Local branch 'main' does not exist. Aborting.${COLOR_RESET}" >&2
    exit 1
  fi
fi

echo "${COLOR_YELLOW}>>> Fetching origin...${COLOR_RESET}"
[[ "$dry_run" == yes ]] || git fetch origin

if ! git show-ref --verify --quiet refs/remotes/origin/main; then
  echo "${COLOR_RED}Remote branch origin/main not found. Aborting.${COLOR_RESET}" >&2
  exit 1
fi

echo "${COLOR_YELLOW}>>> Local-only commits (if any):${COLOR_RESET}"
git log --oneline origin/main..main || true

echo

echo "${COLOR_YELLOW}>>> Pending working tree changes:${COLOR_RESET}"
git status --short || true
echo

echo "${COLOR_YELLOW}>>> Preview of files that would be removed by 'git clean -fdx':${COLOR_RESET}"
git clean -fdx -n || true
echo

backup_branch="backup/$(date +%Y%m%d-%H%M)-main-pre-reset"
echo "${COLOR_YELLOW}Planned backup branch: ${COLOR_GREEN}${backup_branch}${COLOR_RESET}"

if [[ "$dry_run" == yes ]]; then
  echo
  echo "${COLOR_GREEN}DRY RUN complete. No changes made.${COLOR_RESET}"
  echo "To execute for real: $0 --yes"
  exit 0
fi

if [[ "$confirm" == yes ]]; then
  echo
  read -r -p "Proceed with HARD RESET and FULL CLEAN? Type 'RESET' to continue: " answer
  if [[ "$answer" != "RESET" ]]; then
    echo "${COLOR_RED}Aborted by user.${COLOR_RESET}"
    exit 1
  fi
fi

echo "${COLOR_YELLOW}>>> Creating backup branch at current HEAD...${COLOR_RESET}"
git branch "$backup_branch"

echo "${COLOR_YELLOW}>>> Hard resetting 'main' to 'origin/main'...${COLOR_RESET}"
git reset --hard origin/main

echo "${COLOR_YELLOW}>>> Performing full clean (untracked + ignored)...${COLOR_RESET}"
git clean -fdx

echo "${COLOR_GREEN}>>> Done.${COLOR_RESET}"
echo "Backup branch: ${backup_branch}"
echo

echo "Quick recovery example:"
echo "  git checkout ${backup_branch}"
echo "  # inspect, cherry-pick specific commits back if needed"
echo
git status
echo
echo "${COLOR_GREEN}Recent commits on main:${COLOR_RESET}"
git log -n 5 --oneline
