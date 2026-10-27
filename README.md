# HP EliteBook x360 1030 G2 — OpenCore

A small, reproducible OpenCore setup for the 2017 HP EliteBook x360 1030 G2 (Kaby Lake). The scripts download pinned releases, compile the ACPI sources in this repo, and assemble `dist/EFI`. No prebuilt OpenCore or kext binaries are committed.

This tree has **not** been booted on a 1030 G2. Anything about graphics, Wi-Fi, sleep, audio, USB, or input is a reading of public docs and other people's reports, or it is explicitly untested. The compatibility table below is the place to look before assuming a feature works.

macOS is licensed for Apple hardware. You are responsible for how you use it.

[Guide en français](README.fr.md)

## Which macOS to install

**Install macOS Sequoia 15.2 or newer.** That is the newest release that still has a documented, relatively short path for this CPU.

Why Sequoia, and not Tahoe:

- Dortania's Kaby Lake laptop page still points this class of machine at the `MacBookPro14,1` SMBIOS (13-inch, dual-core, 15 W, no Touch ID). Apple dropped that model in Sonoma. OpenCore Legacy Patcher's model list still includes it and marks the graphics as native. The OCLP post-install page, as fetched on 2026-10-26, lists Intel GPUs that need a Sequoia root patch only through Skylake. Kaby Lake is not on that list. A root patch may therefore be unnecessary. That has not been confirmed by booting this laptop.
- OCLP 2.5.1 (19 September 2026) is the current stable release and supports Sequoia. OCLP 3.0.0-rc.3 (8 October 2026) is a prerelease for macOS Tahoe. Dortania's Tahoe page lists only four SMBIOS families as natively supported, all newer than Kaby Lake, and it says AppleHDA has been removed, so AppleALC cannot drive a Conexant codec on Tahoe. Issue [#1167](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1167) tracks what is still unfinished. Issue [#1183](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1183) says the project is staying on Tahoe and has no plan for macOS 27.
- Official OpenIntelWireless `AirportItlwm` 2.3.0 stops at Sonoma. The Sequoia and Tahoe Airport builds in the default EFI come from [laobamac/itlwm](https://github.com/laobamac/itlwm) `v2.4.0-alpha` (commit `738d4c6`, 11 October 2026). That release says hardware validation is still required. The Sequoia kext is for Darwin 24.2 and later (macOS 15.2+). Official `itlwm.kext` 2.3.0 is included and **disabled**. It uses the HeliPort app instead of the Wi-Fi menu, and its own release notes stop at Sonoma.

A MacRumors post around 25 October 2026 claims HD 620/630 can boot Tahoe 26.7.1 without a root patch on a different EliteBook. That is not a test of the 1030 G2 and it is not an OCLP guarantee. Treat Tahoe as an experiment: the Tahoe Airport kext is already in the EFI and loads only on Darwin 25, analog audio should be assumed broken, and `-ibtcompatbeta` is **not** in the default boot arguments (Dortania says to add it for Intel Bluetooth on macOS 26).

## Hardware this EFI is aimed at

From HP QuickSpecs for the EliteBook x360 1030 G2, worldwide document c05275190, DA 15726, version 17 (4 June 2019), plus the EMEA datasheet and the Japanese HP product page where they name the wireless card:

| Item | HP's description |
| --- | --- |
| CPU | i5-7200U, i5-7300U, or i7-7600U. All are dual-core Kaby Lake with HD Graphics 620. |
| Memory | Soldered DDR4-2133, 4 / 8 / 16 GB. Not user-replaceable. |
| Display | 13.3-inch FHD or UHD touch, or FHD with HP Sure View. The UHD panel is untested with this framebuffer. |
| Wireless | Intel 802.11ac 2x2 with Bluetooth 4.2. The EMEA sheet and the Japanese page name the Intel Wireless-AC 8265. OpenIntelWireless lists that card by name. |
| Ports | 1 USB-C with Thunderbolt, 2 USB 3.1 Gen 1 (one charging), HDMI 1.4, barrel power, headset jack, external micro-SIM, microSD, smart-card reader. |
| Audio | Bang & Olufsen, four speakers, dual microphones. The codec vendor is **not** in the QuickSpecs. |
| Pointing | Glass clickpad. HP does not name Synaptics, ELAN, or Alps. |
| Other | 720p webcam plus IR camera, fingerprint sensor, optional Wacom HP Active Pen, optional WWAN and NFC. |

Some GitHub READMEs for this chassis say LPDDR3, two USB-C ports, or an AlpsAlpine V8 clickpad. Those details disagree with the QuickSpecs (one USB-C, DDR4) or are simply not in them (clickpad vendor). Count the ports on your own machine.

## What was checked, and what was not

| Claim | State |
| --- | --- |
| OpenCore 1.0.8 Sample.plist is the schema for `config/config.plist` | Done in the builder |
| ACPI sources compile with iasl, 0 warnings | Done locally with iasl 20230628 |
| Download URLs match the GitHub releases listed in `versions.env`, hashes in `scripts/checksums.sha256` | Done by the builder |
| Placeholder serial / MLB / UUID / ROM, never a generated serial in git | Enforced by the builder |
| `ocvalidate` from OpenCore 1.0.8 | The builder runs `ocvalidate.linux` on Linux and the Mach-O `ocvalidate` on macOS. Both GitHub Actions jobs pass `--require-ocvalidate`. A local run on 2026-10-26 reported no issues. |
| The laptop boots, sleeps, charges, or drives the panel | **Not tested** |
| Wi-Fi, Bluetooth, audio, trackpad, touchscreen, pen, microSD, Thunderbolt, webcam, battery percentage | **Not tested** |

### Community reports (not retested here)

| Topic | What other people wrote | Where |
| --- | --- | --- |
| Sequoia on an i5-7200U 1030 G2 | Success post. First write-up says everything except AirDrop, touchscreen disabled in BIOS, Wi-Fi "with ITLWM". | [r/hackintosh_life](https://www.reddit.com/r/hackintosh_life/comments/1p1dctt/success_hp_elitebook_x360_1030_g2_on_macos_sequoia/), [r/hackintosh](https://www.reddit.com/r/hackintosh/comments/1p8b01q/success_hp_elitebook_x360_1030_g2_on_macos_sequoia/) |
| Same author's EFI | Claims Sequoia, Wi-Fi with Handoff and AirPlay, Bluetooth after sleep, speakers, trackpad gestures, USB-C, microSD or SD, battery, sleep. Fingerprint unsupported. Touchscreen is listed both as working and as not tested. SMBIOS they tell you to use is `MacBookPro16,2`, which this repo does **not** use. | [Fudo7sei/HP-Elitebook-1030-G2-X360-Hackingtosh-EFI](https://github.com/Fudo7sei/HP-Elitebook-1030-G2-X360-Hackingtosh-EFI) |
| Earlier attempt | Sequoia install rebooted in a loop with `MacBookPro15,2` after a working Ventura EFI on `MacBookPro14,1`. | [Olarila thread](https://olarila.com/topic/44175-hp-elitebook-x360-1030-g2-possible-to-install-sequoia-on-it/) |
| Ventura / Sonoma EFI | `MacBookPro14,1`, audio layout 21, Alps V8, Intel 8265. AirDrop called out as needing a Broadcom card. Fingerprint called unsupported. | [RealSameerAlSahab/HP-Elitebook-X360-1030-G2-Hackingtosh-EFI](https://github.com/realsameeralsahab/hp-elitebook-x360-1030-g2-hackingtosh-efi) |
| Audio layout | AppleALC's CX8200 layouts are 3, 15, 21, 23, and 80. Layout 21 was added for an HP Spectre, layout 23 for a ProBook 440 G5. Neither note mentions the 1030 G2. | [AppleALC CX8200](https://github.com/acidanthera/AppleALC/blob/master/Resources/CX8200/Info.plist) |

Related machines, **not** drop-in EFIs: the x360 1030 G3 and the EliteBook 830 G4/G5 are Whiskey Lake or different boards. See [EliaAmir/hackintosh-elitebook-x360-1030-g3](https://github.com/EliaAmir/hackintosh-elitebook-x360-1030-g3), [yingw/HP-Elitebook-X360-1030-G3-Hackintosh](https://github.com/yingw/HP-Elitebook-X360-1030-G3-Hackintosh), [BourneKoloh/HP-Elitebook-x360-OC-EFI](https://github.com/BourneKoloh/HP-Elitebook-x360-OC-EFI), [jkaninda/Hackintosh-HP-EliteBook-830-G5-OC-Ventura](https://github.com/jkaninda/Hackintosh-HP-EliteBook-830-G5-OC-Ventura), [ebuyzone/Hackintosh-HP-Elitebook-830-G5](https://github.com/ebuyzone/Hackintosh-HP-Elitebook-830-G5), [nguyenthienhoan/HP-EliteBook-830-G5-OpenCore](https://github.com/nguyenthienhoan/HP-EliteBook-830-G5-OpenCore). No maintained 830 G4 tree turned up in this pass.

Fingerprint: every 1030 G2 report found for this model says it does not work, and this EFI has no kext for it. Still not retested here.

## Build the EFI

You need Python 3, `iasl` (package `acpica-tools`, or `brew install acpica`), and `curl` via Python's standard library. The build needs network access the first time. Archives land in `cache/` and are checked against `scripts/checksums.sha256`.

Linux or macOS:

```bash
bash scripts/build-efi.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-efi.ps1
```

Useful flags, passed through to `scripts/efi_build.py build`:

| Flag | Effect |
| --- | --- |
| `--wifi sequoia` | Default. Sequoia AirportItlwm enabled on Darwin 24.2–24.99, Tahoe AirportItlwm enabled on Darwin 25, `itlwm.kext` present but off. |
| `--wifi itlwm` | Official `itlwm` 2.3.0 on, both Airport kexts off. Install [HeliPort](https://github.com/OpenIntelWireless/HeliPort) after macOS is up. Recovery will not have a Wi-Fi menu. |
| `--wifi sonoma` | Official AirportItlwm 2.3.0 Sonoma 14.0 and 14.4 builds, kernel-gated. |
| `--wifi ventura` | Official AirportItlwm 2.3.0 Ventura build. |
| `--wifi all` | All of the above Airport variants, still only one range active per boot. `itlwm` stays off. |
| `--alcid 23` | Starting layout id. Default is 21, which is only a community starting point. |
| `--with-cpufriend` | Also download CPUFriend 1.3.0. It stays disabled until `user/CPUFriendDataProvider.kext` exists. |

The zip is `dist/EliteBook-x360-1030-G2-OpenCore.zip`. Copy the `EFI` folder inside it to the EFI partition of the installer USB. `config/config.plist` in git is the placeholder template. The file under `dist/EFI/OC/` is the one you boot.

Do not enable `itlwm.kext` and any `AirportItlwm*.kext` at the same time. OpenIntelWireless warns that this breaks both.

### Versions

| Piece | Version |
| --- | --- |
| OpenCore | 1.0.8 |
| Lilu | 1.7.2 |
| VirtualSMC | 1.3.8 |
| WhateverGreen | 1.7.1 |
| AppleALC | 1.9.8 |
| RestrictEvents | 1.1.6 |
| NVMeFix | 1.1.3 |
| HibernationFixup | 1.5.4 |
| BrightnessKeys | 1.0.3 |
| VoodooPS2 | 2.3.7 (keyboard plugin enabled; mouse, trackpad, and its VoodooInput present but disabled) |
| VoodooI2C | 2.9.1 (HID satellite on; Synaptics, ELAN, Atmel, FTE present and off) |
| ECEnabler | 1.0.6 |
| IntelBluetoothFirmware | 2.4.0, plus BlueToolFixup from BrcmPatchRAM 2.7.2 |
| itlwm / official AirportItlwm | 2.3.0 |
| laobamac AirportItlwm | v2.4.0-alpha Sequoia and Tahoe |
| RealtekCardReader + Friend | 0.9.7 and 1.0.4 |
| USBToolBox kext | 1.2.0, disabled until you add a map |
| CPUFriend | 1.3.0, only when requested |
| OCLP, if you need it | 2.5.1 for Sequoia. 3.0.0-rc.3 is Tahoe-only and prerelease. |

`IntelBluetoothInjector.kext` is intentionally not copied. OpenIntelWireless wants `IntelBluetoothFirmware` + `IntelBTPatcher` + `BlueToolFixup` on modern macOS, not the injector.

The 8265's Bluetooth USB id on the OpenIntelWireless compatibility page is one of `0x8087:0x0a2a`, `0x0a2b`, and the other ids in that table. This repo has not read the id from a 1030 G2. Confirm it in Windows Device Manager if Bluetooth never enumerates.

## SMBIOS

The product name is `MacBookPro14,1`. Dortania uses it for this CPU class. `RestrictEvents` is enabled with `revpatch=sbvmm`, which that kext's README describes as the way to get system updates for an unsupported board-id on macOS 11.3 and newer. `SecureBootModel` is `Disabled` because Dortania's notes for updates on macOS 14.4 and newer say to disable it when `sbvmm` is in use. Whether that combination actually boots the Sequoia installer on this laptop is **untested**.

Generate an identity on the machine you build from. This uses `macserial` from the OpenCore 1.0.8 utilities (the same tool [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) downloads):

```bash
bash scripts/generate-smbios.sh
bash scripts/build-efi.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generate-smbios.ps1
powershell -ExecutionPolicy Bypass -File scripts\build-efi.ps1
```

`user/smbios.json` is gitignored. Check the serial on Apple's coverage page. You want the "not found" result, not a real Mac's record. Do not commit the file, do not paste it into an issue, and do not reuse someone else's serial.

`ROM` is six random bytes. After installation you can replace it with the 8265's MAC address if iMessage setup asks you to. iMessage itself is untested.

## BIOS

HP uses **F10** for setup and **F9** for the boot menu. Menu names move between BIOS revisions. Match the intent; do not hunt for a menu this guide invents.

From Dortania's Kaby Lake laptop page, applied to a business HP firmware that hides many of those knobs:

- Turn **off** Secure Boot, Legacy / CSM, and Fast Boot.
- Turn **off** TPM / Intel Platform Trust and Intel SGX if you see them.
- Leave VT-x **on**. Turn VT-d **off**, or leave it on: `DisableIoMapper` is already set.
- If a video-memory or DVMT entry exists, set it to **64 MB or more**. Community 1030 G2 notes say the option is there and that 64 MB is the value they use. The QuickSpecs do not document the menu. If you cannot find it and you get a graphics panic, see Troubleshooting for the stolen-memory properties. They are not enabled by default.
- There is usually **no CFG Lock switch**. `AppleXcpmCfgLock` is on for that reason. `ControlMsrE2.efi` is in the picker (press space) if you want to read MSR 0xE2.
- Keep wireless and, if you want to test it, the touchscreen enabled.
- For the first install, set Thunderbolt security to the option that does not block USB-C devices. Dortania suggests disabling Thunderbolt entirely if the installer hangs, then turning it back on later. This EFI has **no** Thunderbolt hotplug SSDT. USB-C data may work without one. Thunderbolt devices and the HP dock are untested.
- `UnblockFsConnect` and `LapicKernelPanic` are on because Dortania calls those out for HP.

Community BIOS lists (Fudo7sei, RealSameerAlSahab) also mention disabling HP Smart Card power saving and leaving Fast Charge either way. Those switches were not confirmed against an HP manual for this model. Skip them if you do not see them.

## USB installer from Windows

Do this only after the EFI exists. Map USB **before** you install if you can. `XhciPortLimit` is off because it is unreliable from macOS 11.3 onward, and Sequoia is far past that. With more than 15 ports on one controller, the installer stick can disappear on the second reboot. This machine's port count has not been mapped.

### Map USB (recommended first)

1. On Windows, download the USBToolBox **tool** from [USBToolBox/tool](https://github.com/USBToolBox/tool). The kext pin in this repo is 1.2.0; the Windows tool is a separate repository and is not bundled.
2. Run it, select the xHCI controller, and export `UTBMap.kext`.
3. Put that bundle at `user/UTBMap.kext` and run the build again. The builder then enables `USBToolBox.kext` and the map.

### Recovery image (Dortania's Windows method)

Use `macrecovery.py` from the OpenCore 1.0.8 zip the build already cached at `cache/src/OpenCore/Utilities/macrecovery/`, or from a fresh [OpenCore 1.0.8](https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8) download.

```bat
py macrecovery.py -b Mac-937A206F2EE63C01 -m 00000000000000000 -os default download
```

In that OpenCore release, `boards.json` labels `Mac-937A206F2EE63C01` as **15.8**. That board id is only for downloading a recovery image. It is not the SMBIOS this EFI uses. Read the script's output. If the version is 15.x, continue. If it is 26.x, you downloaded Tahoe; stop and use gibMacOS to pick Sequoia instead. `-os latest` is more likely to follow Apple's newest catalog, so leave it at `default`.

Format a USB drive as FAT32 (Disk Management, or Rufus with a non-bootable large-FAT32 filesystem if the stick is bigger than 32 GB). Create `com.apple.recovery.boot` on it and copy both the `.dmg` and the `.chunklist`. Copy `dist/EFI` to the root of the same stick so you have `EFI` and `com.apple.recovery.boot` side by side.

The recovery installer downloads the rest of macOS. `AirportItlwm` can use the Wi-Fi menu in Recovery. `itlwm` cannot, unless you have USB Ethernet or a phone tether.

### Full offline installer (gibMacOS)

1. Clone [corpnewt/gibMacOS](https://github.com/corpnewt/gibMacOS) and run `gibMacOS.bat`.
2. Choose a **Sequoia 15.2 or newer** entry, not Tahoe.
3. Build the installer with the script gibMacOS prints (`MakeInstall.bat` / the BuildmacOSInstall command, depending on the revision you cloned).
4. Mount the installer USB's EFI partition and copy `dist/EFI` onto it.

## Install

1. F9, pick the USB drive.
2. OpenCore's text picker appears. Press space if you need Reset NVRAM, Toggle SIP, the shell, or the CFG-lock tool.
3. Boot the installer. The screen stays verbose (`-v`) on purpose.
4. Disk Utility: erase the target as APFS, GUID partition map. Disconnect Windows only if you meant to.
5. Install, and let it reboot from the USB each time until the internal volume boots on its own.
6. Mount the internal EFI (OpenCore's `MountEFI` is not bundled; `diskutil` on macOS or Disk Management on Windows both work) and copy the same `EFI` folder onto it. Keep the USB EFI until the internal one has booted twice.

Graphics may be slow or stuck at a low resolution until the display stack settles. Do not "fix" that by switching the SMBIOS to `MacBookPro16,2` during the install. That is what the Fudo7sei EFI asks for. This repo stays on `MacBookPro14,1` so the board-id matches the Kaby Lake Mac that OCLP knows. Switching SMBIOS is untested here and can make a patcher skip the Kaby Lake path.

## Post-install

### Graphics and OCLP

Boot once and open About This Mac. If the GPU reports a normal framebuffer memory size and the menu bar is translucent, leave OCLP alone.

If the UI is in software rendering, download **OCLP 2.5.1** from the [Dortania releases](https://github.com/dortania/OpenCore-Legacy-Patcher/releases/tag/2.5.1) and run Post-Install Root Patch. OCLP's own page may tell you this model does not need a graphics patch. Believe the app. If it does patch, it will also tell you how it wants SIP set. Our `csr-active-config` is `00000000` (SIP on). Change it only to the value OCLP shows you, then rebuild or edit the booted config and reset NVRAM. Root patches are wiped by macOS updates and have to be applied again. That behavior is described in OCLP's post-install page and has not been exercised here.

Do not install OCLP 3.0.0-rc.3 unless you are testing Tahoe and you have a backup.

### Audio

`alcid=21` is the default boot argument. It is the layout id community EFIs for this laptop mention, and it is also a CX8200 layout AppleALC wrote for a different HP. If you get no sound:

1. Confirm the codec in Windows (device manager, or a codec dump). If it is not Conexant CX8200, stop guessing from this list.
2. If it is CX8200, try `alcid=23`, then `15`, `3`, and `80`, one at a time, with an NVRAM reset between tries.
3. On Tahoe, stop. AppleHDA is gone, so AppleALC will not bring the speakers back. Dortania's alternatives are a root patch that restores AppleHDA, or VoodooHDA at lower quality. Neither is wired into this EFI, and neither is tested.

### Wi-Fi version switch

The default EFI already kernel-gates Sequoia and Tahoe AirportItlwm. Booting the other OS does not require a rebuild. To use official `itlwm` instead:

```bash
bash scripts/build-efi.sh --wifi itlwm
```

Then install HeliPort. AirDrop on the 8265 is reported as missing by both the first Reddit write-up and the RealSameer README. The Fudo7sei README later mentions Handoff and AirPlay. This repo has not checked any of those.

### USB map, if you skipped it

The same USBToolBox steps as above. Hackintool on macOS is the other common path; this guide does not walk through it because the Windows map is the one Dortania recommends once `XhciPortLimit` is off.

### CPUFriend

Optional. Native XCPM plus `SSDT-PLUG` is the Dortania baseline for Kaby Lake, and it is what this EFI ships. A CPUFriend data provider can tune the power profile further. It is not included, because a frequency vector copied from another machine would be a guess.

1. Install [CPUFriendFriend](https://github.com/corpnewt/CPUFriendFriend) on the booted system.
2. Generate a data-provider kext for `MacBookPro14,1`.
3. Place it at `user/CPUFriendDataProvider.kext`.
4. Run `bash scripts/build-efi.sh --with-cpufriend` and copy the new EFI.

### Trackpad, touchscreen, pen

`VoodooI2CHID` is the enabled satellite because it covers a lot of HID-over-I2C pads, including some Alps and ELAN devices. `VoodooI2CSynaptics` and `VoodooI2CELAN` are in the EFI and disabled. Enable one of them only after you disable HID, and only after you know the vendor from Windows. The PS/2 mouse and trackpad plugins are present and disabled so they do not fight I2C. The keyboard plugin stays enabled.

`SSDT-GPIO` turns on `GPEN` / `SBRG` and clears `GPHD` when those objects exist. It is a generic Kaby Lake pattern, not a dump of this board. If the pad stays dead, disable `SSDT-GPIO`, enable `SSDT-XOSI` **and** the `_OSI` to `XOSI` rename together, and reboot. `XOSI` answers yes to `Darwin` so the other SSDTs keep their macOS checks. Leave the rename off unless you need it: OpenCore also applies it when Windows is booted from OpenCore.

The touchscreen and the optional pen are untested. One community README lists the touchscreen as working and as not tested in the same document. HP describes the pen as an optional Wacom part.

### Battery, brightness, card reader

`ECEnabler` plus `SMCBatteryManager` is the usual way to read an embedded controller that uses fields wider than a byte, without a hand-written battery SSDT. `SSDT-EC` adds a fake `ACID0001` device so AppleBusPower has something named EC, and it does not claim the real `PNP0C09` device. If the boot log says `AE_ALREADY_EXISTS` for `EC`, disable `SSDT-EC` only.

`SSDT-PNLF` publishes a backlight device with `_UID` 16, WhateverGreen's Skylake/Kaby Lake profile. `BrightnessKeys` is on for the F-keys. Both are untested. The QuickSpecs list F2/F3 as brightness and F5–F7 as volume.

`RealtekCardReader` and `RealtekCardReaderFriend` are on because the slot is described as Realtek in community notes and in the request for this repo. HP's QuickSpecs only say "microSD". If the PCI id is not one the kext supports, the reader will just stay empty. Check the id before filing a bug against the kext.

## Troubleshooting

| What you see | What to try first |
| --- | --- |
| Kernel panic mentioning LAPIC | `LapicKernelPanic` should already be true. If you turned it off, turn it back on. |
| Picker shows no internal disk | `UnblockFsConnect` and `ScanPolicy` 0 are already set. Reset NVRAM from the picker. |
| `OCB: LoadImage failed - Security violation` | `SecureBootModel` should already be `Disabled`. Secure Boot in the BIOS must also be off. |
| Reboot loop right after the picker | Boot in verbose and read the last lines. On 11.3+ a bad or missing USB map does this. `XhciPortLimit` will not save you on Sequoia. |
| Black screen or a panic before the desktop, and DVMT cannot be set | Add, under `PciRoot(0x0)/Pci(0x2,0x0)`, `framebuffer-patch-enable` = `01000000`, `framebuffer-stolenmem` = `00003001`, `framebuffer-fbmem` = `00009000`. Dortania documents these for 32 MB stolen memory. Remove them if 64 MB already works. |
| Image, but no acceleration | Try platform id `00001659` in place of `00001B59` (Dortania's alternate for HD 620). Then try OCLP 2.5.1. Do not stack connector patches "just in case". |
| HDMI hangs when a display is plugged in | Dortania's Kaby Lake laptop page has two connector patches (con1/con2). Apply one set at a time. HDMI on this chassis is untested, so do not enable them pre-emptively. |
| No audio | See the audio section. On Tahoe, AppleALC cannot win. |
| Wi-Fi missing on Sequoia 15.0 or 15.1 | The laobamac Sequoia kext starts at 15.2. Update macOS or switch to `--wifi itlwm`. |
| Wi-Fi missing on Tahoe | Confirm `AirportItlwm_Tahoe` is the kext that loaded, and read laobamac's notes: alpha, WPA3-only and AirDrop not supported. |
| Bluetooth missing on Tahoe | Add the boot argument `-ibtcompatbeta`. Do not add it on Sequoia until you know you need it. |
| Trackpad dead | Vendor check, then the HID / Synaptics / ELAN switch, then GPIO versus XOSI. |
| CMOS resets or the machine falls into safe mode after shutdown | Set `DisableRtcChecksum` to true. It ships false. |
| Windows misbehaves when started from OpenCore | The SSDTs are gated on Darwin. The `_OSI` rename is not. Keep that rename disabled. |

## Layout

```
acpi/                 SSDT sources. The builder compiles them.
config/config.plist   Placeholder template generated from Sample.plist.
scripts/efi_build.py  Downloader, compiler, and config writer.
scripts/build-efi.sh  Linux and macOS entry point.
scripts/build-efi.ps1 Windows entry point.
scripts/generate-smbios.sh / .ps1
scripts/checksums.sha256
versions.env
user/                 Gitignored SMBIOS file and optional kext drop-ins.
dist/                 Build output, not committed.
```

## Sources

Rewritten from these pages. Nothing below is copied in bulk.

- HP QuickSpecs, EliteBook x360 1030 G2, c05275190, DA 15726, version 17, 4 June 2019, and the [EMEA datasheet](https://ck-group.lu/wp-content/uploads/2018/03/Documentation-anglais-elitebook-X360-1030-G2.pdf) which names the 8265 and the three CPUs. The [Japanese HP page](https://jp.ext.hp.com/notebooks/business/elitebook_x360_merit/) also names the 8265.
- [Dortania, Laptop Kaby Lake](https://dortania.github.io/OpenCore-Install-Guide/config-laptop.plist/kaby-lake.html) for SMBIOS, quirks, platform id `00001B59`, SSDT list, and the HP `LapicKernelPanic` / `UnblockFsConnect` reminders.
- [Dortania, Windows installer](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/windows-install.html) and OpenCore 1.0.8 `Utilities/macrecovery`.
- [Dortania, embedded controller](https://dortania.github.io/Getting-Started-With-ACPI/Universal/ec-fix.html) and the OpenCore `SSDT-EC-USBX` / `SSDT-PLUG` samples.
- [Dortania, macOS Tahoe notes](https://dortania.github.io/OpenCore-Install-Guide/extras/tahoe.html) for AppleHDA removal, the native SMBIOS list, and `-ibtcompatbeta`.
- [OCLP supported models](https://dortania.github.io/OpenCore-Legacy-Patcher/MODELS.html), [Sonoma drop](https://dortania.github.io/OpenCore-Legacy-Patcher/SONOMA-DROP.html), [Sequoia drop](https://dortania.github.io/OpenCore-Legacy-Patcher/SEQUOIA-DROP.html), and [post-install](https://dortania.github.io/OpenCore-Legacy-Patcher/POST-INSTALL.html).
- [RestrictEvents README](https://github.com/acidanthera/RestrictEvents/blob/master/README.md) for `revpatch=sbvmm`.
- [OpenIntelWireless itlwm compatibility](https://openintelwireless.github.io/itlwm/Compat.html) and [Bluetooth compatibility](https://openintelwireless.github.io/IntelBluetoothFirmware/Compat.html).
- [laobamac/itlwm](https://github.com/laobamac/itlwm) for the Sequoia and Tahoe Airport builds, and [5T33Z0's AirportItlwm Sequoia note](https://github.com/5T33Z0/OCLP4Hackintosh/blob/main/Enable_Features/AirportItllwm_Sequoia.md) for the explanation of why the official kext stopped at Sonoma.
- Community 1030 G2 reports linked in the table above. Their EFI binaries and README text are not reused.

## License

MIT for this repository's own files. See `LICENSE` and `THIRD-PARTY-NOTICES.md` before you redistribute a built zip. VoodooPS2 is APSL-2.0. itlwm, the laobamac fork, and BrcmPatchRAM's BlueToolFixup are GPL-2.0. VoodooI2C and IntelBluetoothFirmware are GPL-3.0. ECEnabler and the USBToolBox kext had no license file on 2026-10-26.
