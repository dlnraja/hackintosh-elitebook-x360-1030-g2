#!/usr/bin/env bash
# Download the pinned OpenCore and kext releases and assemble dist/EFI.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi
if ! command -v iasl >/dev/null 2>&1; then
  echo "iasl is required. Debian/Ubuntu: sudo apt-get install acpica-tools. macOS: brew install acpica." >&2
  exit 1
fi
exec python3 scripts/efi_build.py build "$@"
