# Third-party notices

The files written in this repository (scripts, ACPI sources, documentation, and the generated `config/config.plist` template) are under the MIT license in `LICENSE`.

That MIT license does not cover macOS, and it does not cover the OpenCore, kext, or utility binaries the build downloads. Those stay under the license of the project that published them. `scripts/efi_build.py` downloads the pinned Git tag or release asset and does not relicense it. The CI artifact is a convenience aggregate of those unmodified archives plus this repo's ACPI and config. It is not a single combined work under MIT.

Checked on 2026-10-26:

| Project | Pinned release | License reported by the project |
| --- | --- | --- |
| [acidanthera/OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) | 1.0.8 | BSD-3-Clause |
| [acidanthera/Lilu](https://github.com/acidanthera/Lilu) | 1.7.2 | BSD-3-Clause |
| [acidanthera/VirtualSMC](https://github.com/acidanthera/VirtualSMC) | 1.3.8 | BSD-3-Clause |
| [acidanthera/WhateverGreen](https://github.com/acidanthera/WhateverGreen) | 1.7.1 | BSD-3-Clause |
| [acidanthera/AppleALC](https://github.com/acidanthera/AppleALC) | 1.9.8 | BSD-3-Clause |
| [acidanthera/RestrictEvents](https://github.com/acidanthera/RestrictEvents) | 1.1.6 | BSD-3-Clause |
| [acidanthera/HibernationFixup](https://github.com/acidanthera/HibernationFixup) | 1.5.4 | BSD-3-Clause |
| [acidanthera/BrightnessKeys](https://github.com/acidanthera/BrightnessKeys) | 1.0.3 | BSD-3-Clause |
| [acidanthera/CPUFriend](https://github.com/acidanthera/CPUFriend) | 1.3.0 | BSD-3-Clause |
| [acidanthera/NVMeFix](https://github.com/acidanthera/NVMeFix) | 1.1.3 | BSD license in `LICENSE.txt` |
| [acidanthera/VoodooPS2](https://github.com/acidanthera/VoodooPS2) | 2.3.7 | Apple Public Source License 2.0 (`LICENSE.md`) |
| [acidanthera/BrcmPatchRAM](https://github.com/acidanthera/BrcmPatchRAM) | 2.7.2 | GPL-2.0. Only `BlueToolFixup.kext` is copied. |
| [VoodooI2C/VoodooI2C](https://github.com/VoodooI2C/VoodooI2C) | 2.9.1 | GPL-3.0 |
| [OpenIntelWireless/itlwm](https://github.com/OpenIntelWireless/itlwm) | 2.3.0 | GPL-2.0 |
| [laobamac/itlwm](https://github.com/laobamac/itlwm) | v2.4.0-alpha (`738d4c6`) | GPL-2.0. Sequoia and Tahoe `AirportItlwm` builds. |
| [OpenIntelWireless/IntelBluetoothFirmware](https://github.com/OpenIntelWireless/IntelBluetoothFirmware) | 2.4.0 | GPL-3.0 |
| [OpenIntelWireless/HeliPort](https://github.com/OpenIntelWireless/HeliPort) | not bundled | BSD-3-Clause. Used only with `itlwm.kext`. |
| [0xFireWolf/RealtekCardReader](https://github.com/0xFireWolf/RealtekCardReader) | 0.9.7 | BSD-3-Clause, included inside the kext |
| [0xFireWolf/RealtekCardReaderFriend](https://github.com/0xFireWolf/RealtekCardReaderFriend) | 1.0.4 | BSD-3-Clause, included inside the kext |
| [1Revenger1/ECEnabler](https://github.com/1Revenger1/ECEnabler) | 1.0.6 | No `LICENSE` file in the repository on this date. The release is downloaded as published. Remove `ECEnabler.kext` from the EFI if you cannot accept that. |
| [USBToolBox/kext](https://github.com/USBToolBox/kext) | 1.2.0 | No `LICENSE` file in the repository on this date. The kext is disabled unless you add your own map. |
| [corpnewt/GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) | not bundled | MIT. The SMBIOS script calls OpenCore's `macserial` directly, which is what GenSMBIOS downloads. |
| [corpnewt/gibMacOS](https://github.com/corpnewt/gibMacOS) | not bundled | MIT |
| [corpnewt/CPUFriendFriend](https://github.com/corpnewt/CPUFriendFriend) | not bundled | MIT |
| [dortania/OpenCore-Legacy-Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) | 2.5.1 stable, 3.0.0-rc.3 prerelease | BSD-style `LICENSE.txt`. Not bundled. |

GPL source for the binaries is the Git tag named above. The SHA-256 of each downloaded archive is in `scripts/checksums.sha256`.

OpenCore's `Docs/AcpiSamples/Source/SSDT-PLUG.dsl` and `SSDT-EC-USBX.dsl` (BSD-3-Clause) describe the CPU plugin-type injection and the USB power values `0x13EC` / `0x0834` used by the ACPI sources here. The `.dsl` files in `acpi/` are rewritten for this repository. The RehabMan `SSDT-PNLF` register program is GPL-2.0 and is not included. WhateverGreen's Skylake/Kaby Lake backlight profile is referenced only by `_UID` 16.
