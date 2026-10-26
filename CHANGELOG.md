# Changelog

## 0.1.0 - 2026-10-26

First public snapshot of a from-scratch OpenCore configuration for the HP EliteBook x360 1030 G2.

- Builder pins OpenCore 1.0.8 and the kext releases listed in `versions.env`, checks `scripts/checksums.sha256`, compiles the ACPI sources, and writes `dist/EFI`.
- Default Wi-Fi selection is laobamac `AirportItlwm` v2.4.0-alpha for Sequoia (Darwin 24.2 through 24.99) and Tahoe (Darwin 25), with official `itlwm` 2.3.0 present and disabled. `--wifi itlwm`, `sonoma`, `ventura`, and `all` switch that selection.
- SMBIOS product is `MacBookPro14,1`. Serial, board serial, UUID, and ROM in `config/config.plist` are placeholders. `scripts/generate-smbios.sh` and `scripts/generate-smbios.ps1` fill `user/smbios.json` with OpenCore's `macserial` and never write that file back into the template.
- GitHub Actions assembles the EFI on Linux and runs `ocvalidate` from the pinned OpenCore release on macOS.

No boot on this chassis is claimed. See the compatibility table in `README.md`.
