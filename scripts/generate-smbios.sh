#!/usr/bin/env bash
# Write user/smbios.json using the macserial binary shipped with the pinned OpenCore release.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi
exec python3 scripts/efi_build.py smbios "$@"
