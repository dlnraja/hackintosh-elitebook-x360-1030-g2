#!/usr/bin/env python3
"""Assemble an OpenCore EFI for the HP EliteBook x360 1030 G2.

The script downloads pinned official releases, compiles the ACPI sources in
acpi/, and writes a config.plist derived from that OpenCore version's
Sample.plist. SMBIOS values stay placeholders unless user/smbios.json exists,
and that file is never written into config/config.plist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
DOWNLOADS = CACHE / "downloads"
EXTRACTED = CACHE / "src"
DIST = ROOT / "dist"
EFI = DIST / "EFI"
KEXTS = EFI / "OC" / "Kexts"
CHECKSUMS = ROOT / "scripts" / "checksums.sha256"
TEMPLATE = ROOT / "config" / "config.plist"

USER_AGENT = "elitebook-x360-1030-g2-efi-build"


def load_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for raw in (ROOT / "versions.env").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        versions[key.strip()] = value.strip()
    return versions


def load_checksums() -> dict[str, str]:
    if not CHECKSUMS.exists():
        return {}
    found: dict[str, str] = {}
    for raw in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, name = line.split(None, 1)
        found[name] = digest
    return found


def save_checksums(found: dict[str, str]) -> None:
    lines = [
        "# SHA-256 of the upstream archives downloaded by scripts/efi_build.py.",
        "# Regenerate with: python3 scripts/efi_build.py build --write-checksums",
        "",
    ]
    for name in sorted(found):
        lines.append(f"{found[name]}  {name}")
    lines.append("")
    CHECKSUMS.write_text("\n".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=180, context=context) as response:
                with temporary.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
            temporary.replace(dest)
            return
        except Exception as error:  # noqa: BLE001 - retry network failures
            last_error = error
            if temporary.exists():
                temporary.unlink()
            time.sleep(2 ** attempt)
    raise SystemExit(f"download failed for {url}: {last_error}")


def ensure_archive(url: str, filename: str, checksums: dict[str, str], freeze: bool) -> Path:
    dest = DOWNLOADS / filename
    if not dest.exists() or dest.stat().st_size == 0:
        print(f"download {filename}")
        download(url, dest)
    else:
        print(f"cached   {filename}")
    digest = sha256_file(dest)
    known = checksums.get(filename)
    if known and known != digest:
        print(f"checksum changed, retrying {filename}")
        dest.unlink()
        download(url, dest)
        digest = sha256_file(dest)
        if digest != known:
            raise SystemExit(f"checksum mismatch for {filename}: {digest} != {known}")
    if freeze:
        checksums[filename] = digest
    elif CHECKSUMS.exists() and known is None:
        raise SystemExit(
            f"{filename} has no entry in scripts/checksums.sha256. "
            "Run with --write-checksums after reviewing the archive."
        )
    return dest


def safe_extract(archive: Path, dest: Path) -> None:
    if dest.exists():
        return
    dest.mkdir(parents=True)
    root = dest.resolve()
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            name = info.filename
            if name.startswith("/") or ".." in Path(name).parts:
                raise SystemExit(f"unsafe path in {archive.name}: {name}")
            target = (root / name).resolve()
            if root != target and root not in target.parents:
                raise SystemExit(f"zip slip in {archive.name}: {name}")
        package.extractall(root)


def github(repo: str, tag: str, asset: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset}"


def find_top_kexts(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in root.rglob("*.kext"):
        if not (path / "Contents" / "Info.plist").is_file():
            continue
        nested = False
        for parent in path.parents:
            if parent == root:
                break
            if (parent / "Contents" / "Info.plist").is_file() and parent.name.endswith(".kext"):
                nested = True
                break
        if nested:
            continue
        found[path.name[:-5]] = path
    return found


def copy_kexts(source: Path, names: set[str], required: set[str], rename: dict[str, str] | None = None) -> None:
    available = find_top_kexts(source)
    rename = rename or {}
    for name in sorted(names):
        if name not in available:
            if name in required:
                raise SystemExit(f"missing {name}.kext in {source}. Found: {sorted(available)}")
            continue
        target_name = rename.get(name, name)
        destination = KEXTS / f"{target_name}.kext"
        if destination.exists():
            raise SystemExit(f"duplicate kext {target_name}")
        shutil.copytree(available[name], destination)


def compile_acpi() -> None:
    compiler = shutil.which("iasl")
    if not compiler:
        raise SystemExit("iasl is not installed. Install acpica-tools (Linux), brew install acpica (macOS), or the ACPICA tools (Windows).")
    acpi_out = EFI / "OC" / "ACPI"
    acpi_out.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "acpi").glob("*.dsl")):
        print(f"iasl     {source.name}")
        result = subprocess.run(
            [compiler, "-ve", "-p", str(acpi_out / source.stem), str(source)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or "Compilation successful" not in result.stdout + result.stderr:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(f"iasl failed for {source.name}")
        if "0 Errors, 0 Warnings" not in result.stdout + result.stderr:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(f"iasl reported warnings for {source.name}")


def find_x64(root: Path, tail: str) -> Path:
    hits = []
    suffix = "/X64/" + tail
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        normal = path.as_posix()
        if "/IA32/" in normal:
            continue
        if normal.endswith(suffix):
            hits.append(path)
    if len(hits) != 1:
        raise SystemExit(f"expected one X64 file ending in {suffix}, found {hits}")
    return hits[0]


def load_info(kext: Path) -> dict:
    with (kext / "Contents" / "Info.plist").open("rb") as handle:
        return plistlib.load(handle)


def executable_path(kext: Path) -> str:
    info = load_info(kext)
    name = info.get("CFBundleExecutable")
    if not name:
        return ""
    relative = f"Contents/MacOS/{name}"
    if not (kext / relative).is_file():
        raise SystemExit(f"{kext.name} declares {name} but the binary is missing")
    return relative


def parent_kext(path: Path) -> str | None:
    for candidate in path.parents:
        if candidate.name.endswith(".kext") and candidate != path:
            return candidate.name[:-5]
    return None


PLUGIN_ALLOW = {
    "VirtualSMC": {"SMCProcessor", "SMCBatteryManager"},
    "VoodooPS2Controller": {"VoodooPS2Keyboard"},
    "VoodooI2C": {"VoodooGPIO", "VoodooInput", "VoodooI2CHID", "VoodooI2CServices"},
}

ORDER = [
    "Lilu",
    "VirtualSMC",
    "SMCProcessor",
    "ECEnabler",
    "SMCBatteryManager",
    "WhateverGreen",
    "AppleALC",
    "RestrictEvents",
    "NVMeFix",
    "HibernationFixup",
    "BrightnessKeys",
    "VoodooPS2Controller",
    "VoodooPS2Keyboard",
    "VoodooGPIO",
    "VoodooInput",
    "VoodooI2CServices",
    "VoodooI2C",
    "VoodooI2CHID",
    "VoodooI2CSynaptics",
    "VoodooI2CELAN",
    "VoodooI2CAtmelMXT",
    "IntelBluetoothFirmware",
    "IntelBTPatcher",
    "BlueToolFixup",
    "AirportItlwm_Sequoia",
    "AirportItlwm_Tahoe",
    "AirportItlwm_Sonoma140",
    "AirportItlwm_Sonoma144",
    "AirportItlwm_Ventura",
    "itlwm",
    "RealtekCardReaderFriend",
    "RealtekCardReader",
    "USBToolBox",
    "UTBMap",
    "CPUFriend",
    "CPUFriendDataProvider",
]


def kernel_bounds(name: str, wifi: str) -> tuple[str, str, bool]:
    """Return MinKernel, MaxKernel, Enabled for a top-level kext name."""
    sequoia = ("24.2.0", "24.99.99")
    tahoe = ("25.0.0", "25.99.99")
    sonoma140 = ("23.0.0", "23.3.99")
    sonoma144 = ("23.4.0", "23.99.99")
    ventura = ("22.0.0", "22.99.99")
    table = {
        "sequoia": {
            "AirportItlwm_Sequoia": (*sequoia, True),
            "AirportItlwm_Tahoe": (*tahoe, True),
            "itlwm": ("", "", False),
        },
        "itlwm": {
            "AirportItlwm_Sequoia": (*sequoia, False),
            "AirportItlwm_Tahoe": (*tahoe, False),
            "itlwm": ("", "", True),
        },
        "sonoma": {
            "AirportItlwm_Sonoma140": (*sonoma140, True),
            "AirportItlwm_Sonoma144": (*sonoma144, True),
            "itlwm": ("", "", False),
        },
        "ventura": {
            "AirportItlwm_Ventura": (*ventura, True),
            "itlwm": ("", "", False),
        },
        "all": {
            "AirportItlwm_Sequoia": (*sequoia, True),
            "AirportItlwm_Tahoe": (*tahoe, True),
            "AirportItlwm_Sonoma140": (*sonoma140, True),
            "AirportItlwm_Sonoma144": (*sonoma144, True),
            "AirportItlwm_Ventura": (*ventura, True),
            "itlwm": ("", "", False),
        },
    }
    chosen = table[wifi]
    if name in chosen:
        return chosen[name]
    return ("", "", True)


DISABLED_NAMES = {
    "VoodooI2CSynaptics",
    "VoodooI2CELAN",
    "VoodooI2CAtmelMXT",
    "VoodooI2CFTE",
    "VoodooPS2Mouse",
    "VoodooPS2Trackpad",
    "SMCSuperIO",
    "SMCLightSensor",
    "SMCDellSensors",
    "IntelBluetoothInjector",
}


def kext_enabled(path: Path, wifi: str, extras: set[str]) -> bool:
    name = path.name[:-5]
    parent = parent_kext(path)
    top = parent or name
    if name in DISABLED_NAMES:
        return False
    if name in {"USBToolBox", "UTBMap"}:
        return "UTBMap" in extras
    if name in {"CPUFriend", "CPUFriendDataProvider"}:
        return "CPUFriendDataProvider" in extras
    if parent and parent in PLUGIN_ALLOW and name not in PLUGIN_ALLOW[parent]:
        return False
    _min, _max, enabled = kernel_bounds(top, wifi)
    if top.startswith("AirportItlwm") or top == "itlwm":
        return enabled
    return True


def kext_comment(name: str, versions: dict[str, str]) -> str:
    labels = {
        "Lilu": versions["LILU_VERSION"],
        "VirtualSMC": versions["VIRTUALSMC_VERSION"],
        "SMCProcessor": versions["VIRTUALSMC_VERSION"],
        "SMCBatteryManager": versions["VIRTUALSMC_VERSION"],
        "WhateverGreen": versions["WHATEVERGREEN_VERSION"],
        "AppleALC": versions["APPLEALC_VERSION"],
        "RestrictEvents": versions["RESTRICTEVENTS_VERSION"],
        "NVMeFix": versions["NVMEFIX_VERSION"],
        "HibernationFixup": versions["HIBERNATIONFIXUP_VERSION"],
        "BrightnessKeys": versions["BRIGHTNESSKEYS_VERSION"],
        "ECEnabler": versions["ECENABLER_VERSION"],
        "VoodooPS2Controller": versions["VOODOOPS2_VERSION"],
        "VoodooPS2Keyboard": versions["VOODOOPS2_VERSION"],
        "VoodooI2C": versions["VOODOOI2C_VERSION"],
        "VoodooGPIO": versions["VOODOOI2C_VERSION"],
        "VoodooInput": versions["VOODOOI2C_VERSION"],
        "VoodooI2CHID": versions["VOODOOI2C_VERSION"],
        "VoodooI2CSynaptics": versions["VOODOOI2C_VERSION"],
        "VoodooI2CELAN": versions["VOODOOI2C_VERSION"],
        "VoodooI2CServices": versions["VOODOOI2C_VERSION"],
        "IntelBluetoothFirmware": versions["INTEL_BT_VERSION"],
        "IntelBTPatcher": versions["INTEL_BT_VERSION"],
        "BlueToolFixup": versions["BRCMPATCHRAM_VERSION"],
        "itlwm": versions["ITLWM_VERSION"],
        "RealtekCardReader": versions["REALTEK_CARDREADER_VERSION"],
        "RealtekCardReaderFriend": versions["REALTEK_CARDREADER_FRIEND_VERSION"],
        "USBToolBox": versions["USBTOOLBOX_VERSION"],
        "CPUFriend": versions["CPUFRIEND_VERSION"],
        "AirportItlwm_Sequoia": versions["AIRPORT_FORK_TAG"] + " Sequoia",
        "AirportItlwm_Tahoe": versions["AIRPORT_FORK_TAG"] + " Tahoe",
        "AirportItlwm_Sonoma140": versions["ITLWM_VERSION"] + " Sonoma 14.0-14.3",
        "AirportItlwm_Sonoma144": versions["ITLWM_VERSION"] + " Sonoma 14.4+",
        "AirportItlwm_Ventura": versions["ITLWM_VERSION"] + " Ventura",
    }
    version = labels.get(name, "user supplied")
    return f"{name} {version}"


def collect_kext_entries(template: dict, versions: dict[str, str], wifi: str, extras: set[str]) -> list[dict]:
    paths = [path for path in KEXTS.rglob("*.kext") if (path / "Contents" / "Info.plist").is_file()]

    def sort_key(path: Path) -> tuple:
        name = path.name[:-5]
        index = ORDER.index(name) if name in ORDER else 800
        return (index, path.as_posix())

    entries = []
    for path in sorted(paths, key=sort_key):
        name = path.name[:-5]
        parent = parent_kext(path)
        top = parent or name
        minimum, maximum, _enabled = kernel_bounds(top, wifi)
        entry = dict(template)
        entry.update(
            {
                "Arch": "Any",
                "BundlePath": path.relative_to(KEXTS).as_posix(),
                "Comment": kext_comment(name, versions),
                "Enabled": kext_enabled(path, wifi, extras),
                "ExecutablePath": executable_path(path),
                "MaxKernel": maximum,
                "MinKernel": minimum,
                "PlistPath": "Contents/Info.plist",
            }
        )
        entries.append(entry)
    return ensure_parent_first(entries)


def ensure_parent_first(entries: list[dict]) -> list[dict]:
    """A plugin has to be listed after the kext that contains it."""
    ordered = list(entries)
    for _ in range(len(ordered) + 1):
        for index, entry in enumerate(ordered):
            bundle = entry["BundlePath"]
            marker = "/Contents/PlugIns/"
            if marker not in bundle:
                continue
            parent = bundle.split(marker)[0]
            parent_index = next(item for item, row in enumerate(ordered) if row["BundlePath"] == parent)
            if parent_index > index:
                moved = ordered.pop(index)
                parent_index = next(item for item, row in enumerate(ordered) if row["BundlePath"] == parent)
                ordered.insert(parent_index + 1, moved)
                break
        else:
            return ordered
    raise SystemExit("could not put kext plugins after their parents")


def strip_hash_keys(value):
    if isinstance(value, dict):
        return {key: strip_hash_keys(item) for key, item in value.items() if not str(key).startswith("#")}
    if isinstance(value, list):
        return [strip_hash_keys(item) for item in value]
    return value


def same_keys(reference: dict, candidate: dict, where: str) -> None:
    extra = set(candidate) - set(reference)
    missing = set(reference) - set(candidate)
    if extra or missing:
        raise SystemExit(f"{where}: extra keys {sorted(extra)} missing keys {sorted(missing)}")


def build_config(opencore: Path, versions: dict[str, str], wifi: str, alcid: int, extras: set[str]) -> dict:
    sample_hits = [path for path in opencore.rglob("Sample.plist") if "Docs" in path.parts]
    if len(sample_hits) != 1:
        raise SystemExit(f"Sample.plist not found uniquely in {opencore}")
    with sample_hits[0].open("rb") as handle:
        config = strip_hash_keys(plistlib.load(handle))

    acpi_template = config["ACPI"]["Add"][0]
    patch_template = config["ACPI"]["Patch"][0]
    ssdt_rows = [
        ("SSDT-PLUG.aml", True, "XCPM plugin-type"),
        ("SSDT-EC.aml", True, "Fake EC for AppleBusPower, Darwin only"),
        ("SSDT-USBX.aml", True, "USB power properties"),
        ("SSDT-PNLF.aml", True, "Backlight device, Kaby Lake profile"),
        ("SSDT-GPIO.aml", True, "GPIO pin enable for I2C"),
        ("SSDT-XOSI.aml", False, "Optional Windows _OSI shim, off by default"),
    ]
    config["ACPI"]["Add"] = []
    for filename, enabled, comment in ssdt_rows:
        row = dict(acpi_template)
        row.update({"Path": filename, "Enabled": enabled, "Comment": comment})
        same_keys(acpi_template, row, filename)
        config["ACPI"]["Add"].append(row)
    config["ACPI"]["Delete"] = []
    osi = dict(patch_template)
    osi.update(
        {
            "Comment": "Rename _OSI to XOSI. Enable only together with SSDT-XOSI.",
            "Enabled": False,
            "Count": 0,
            "Limit": 0,
            "Skip": 0,
            "Find": bytes.fromhex("5f4f5349"),
            "Replace": bytes.fromhex("584f5349"),
            "Mask": b"",
            "ReplaceMask": b"",
            "OemTableId": b"",
            "TableSignature": b"",
            "TableLength": 0,
            "Base": "",
            "BaseSkip": 0,
        }
    )
    same_keys(patch_template, osi, "OSI patch")
    config["ACPI"]["Patch"] = [osi]

    platform = bytes.fromhex(versions["IG_PLATFORM_ID"])
    if len(platform) != 4:
        raise SystemExit("IG_PLATFORM_ID must be 8 hex digits")
    config["DeviceProperties"]["Add"] = {
        "PciRoot(0x0)/Pci(0x2,0x0)": {"AAPL,ig-platform-id": platform}
    }
    config["DeviceProperties"]["Delete"] = {}

    kernel_template = config["Kernel"]["Add"][0]
    config["Kernel"]["Add"] = collect_kext_entries(kernel_template, versions, wifi, extras)
    for entry in config["Kernel"]["Add"]:
        same_keys(kernel_template, entry, entry["BundlePath"])
    quirks = config["Kernel"]["Quirks"]
    quirks["AppleXcpmCfgLock"] = True
    quirks["DisableIoMapper"] = True
    quirks["LapicKernelPanic"] = True
    quirks["PanicNoKextDump"] = True
    quirks["PowerTimeoutKernelPanic"] = True
    quirks["XhciPortLimit"] = False

    security = config["Misc"]["Security"]
    security["AllowSetDefault"] = True
    security["ScanPolicy"] = 0
    security["SecureBootModel"] = "Disabled"
    security["Vault"] = "Optional"
    security["DmgLoading"] = "Signed"
    debug = config["Misc"]["Debug"]
    debug["AppleDebug"] = False
    debug["ApplePanic"] = True
    debug["DisableWatchDog"] = True
    debug["Target"] = 0
    config["Misc"]["Boot"]["Timeout"] = 5
    config["Misc"]["Boot"]["HideAuxiliary"] = True
    config["Misc"]["Boot"]["ShowPicker"] = True
    config["Misc"]["Boot"]["PickerMode"] = "Builtin"

    tool_template = config["Misc"]["Tools"][0]
    tools = [
        ("OpenShell.efi", "UEFI Shell", "OpenShell:UEFIShell:Shell", "Hidden until space is pressed"),
        ("ControlMsrE2.efi", "CFG Lock", "Auto", "Read MSR 0xE2. Auxiliary."),
    ]
    config["Misc"]["Tools"] = []
    for path, name, flavour, comment in tools:
        row = dict(tool_template)
        row.update(
            {
                "Arguments": "",
                "Auxiliary": True,
                "Comment": comment,
                "Enabled": True,
                "Flavour": flavour,
                "FullNvramAccess": False,
                "Name": name,
                "Path": path,
                "RealPath": False,
                "TextMode": False,
            }
        )
        same_keys(tool_template, row, path)
        config["Misc"]["Tools"].append(row)

    nvram = config["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    nvram["boot-args"] = f"-v debug=0x100 keepsyms=1 alcid={alcid} revpatch=sbvmm"
    # en-US:0. Kept as data so it matches the Sample.plist type.
    nvram["prev-lang:kbd"] = bytes.fromhex("656e2d55533a30")
    nvram["csr-active-config"] = b"\x00\x00\x00\x00"
    nvram["run-efi-updater"] = "No"
    delete_boot = config["NVRAM"]["Delete"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    for key in ("boot-args", "prev-lang:kbd", "csr-active-config"):
        if key not in delete_boot:
            delete_boot.append(key)

    generic = config["PlatformInfo"]["Generic"]
    generic["SystemProductName"] = versions["SMBIOS_PRODUCT"]
    generic["SystemSerialNumber"] = "CHANGE_ME_SERIAL"
    generic["MLB"] = "CHANGE_ME_MLB17CH"
    generic["SystemUUID"] = "00000000-0000-0000-0000-000000000000"
    generic["ROM"] = b"\x00\x00\x00\x00\x00\x00"
    generic["SystemMemoryStatus"] = "Soldered"
    generic["SpoofVendor"] = True
    config["PlatformInfo"]["Automatic"] = True
    config["PlatformInfo"]["UpdateSMBIOSMode"] = "Create"
    config["PlatformInfo"]["CustomMemory"] = False

    config["UEFI"]["ConnectDrivers"] = True
    config["UEFI"]["Quirks"]["ReleaseUsbOwnership"] = True
    config["UEFI"]["Quirks"]["UnblockFsConnect"] = True
    driver_template = {
        "Arguments": "",
        "Comment": "",
        "Enabled": True,
        "HideVerbose": False,
        "LoadEarly": False,
        "Path": "OpenRuntime.efi",
    }
    # Prefer the sample's own driver dictionary so a new OpenCore key is kept.
    if config["UEFI"]["Drivers"]:
        driver_template = config["UEFI"]["Drivers"][0]
    driver_rows = [
        ("OpenRuntime.efi", True, False, "Runtime services"),
        ("OpenHfsPlus.efi", True, False, "HFS+ filesystem"),
        ("ResetNvramEntry.efi", True, False, "Picker entry: reset NVRAM"),
        ("ToggleSipEntry.efi", True, False, "Picker entry: toggle SIP"),
    ]
    config["UEFI"]["Drivers"] = []
    for path, enabled, early, comment in driver_rows:
        row = dict(driver_template)
        row.update({"Path": path, "Enabled": enabled, "LoadEarly": early, "Comment": comment, "Arguments": ""})
        same_keys(driver_template, row, path)
        config["UEFI"]["Drivers"].append(row)
    return config


def write_plist(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump(data, handle, sort_keys=False, fmt=plistlib.FMT_XML)


def inject_smbios(config: dict, payload: dict) -> None:
    required = ("SystemSerialNumber", "MLB", "SystemUUID", "ROM")
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise SystemExit(f"user/smbios.json is missing {missing}")
    serial = str(payload["SystemSerialNumber"])
    board = str(payload["MLB"])
    if "CHANGE_ME" in serial or "CHANGE_ME" in board:
        raise SystemExit("user/smbios.json still contains placeholders")
    rom = bytes.fromhex(str(payload["ROM"]))
    if len(rom) != 6:
        raise SystemExit("ROM must be 6 bytes of hex")
    uuid.UUID(str(payload["SystemUUID"]))
    generic = config["PlatformInfo"]["Generic"]
    generic["SystemSerialNumber"] = serial
    generic["MLB"] = board
    generic["SystemUUID"] = str(payload["SystemUUID"])
    generic["ROM"] = rom


def lint_config(config: dict, versions: dict[str, str], wifi: str, alcid: int) -> None:
    generic = config["PlatformInfo"]["Generic"]
    if not str(generic["SystemSerialNumber"]).startswith("CHANGE_ME"):
        raise SystemExit("template serial is not a placeholder")
    if not str(generic["MLB"]).startswith("CHANGE_ME"):
        raise SystemExit("template board serial is not a placeholder")
    if generic["SystemUUID"] != "00000000-0000-0000-0000-000000000000":
        raise SystemExit("template UUID is not the nil placeholder")
    if generic["ROM"] != b"\x00\x00\x00\x00\x00\x00":
        raise SystemExit("template ROM is not the zero placeholder")
    if generic["SystemProductName"] != "MacBookPro14,1":
        raise SystemExit("SMBIOS product changed")
    quirks = config["Kernel"]["Quirks"]
    expected_quirks = {
        "AppleXcpmCfgLock": True,
        "DisableIoMapper": True,
        "LapicKernelPanic": True,
        "PanicNoKextDump": True,
        "PowerTimeoutKernelPanic": True,
        "XhciPortLimit": False,
    }
    for key, value in expected_quirks.items():
        if quirks[key] != value:
            raise SystemExit(f"Kernel/Quirks/{key} is {quirks[key]!r}, expected {value!r}")
    if config["UEFI"]["Quirks"]["UnblockFsConnect"] is not True:
        raise SystemExit("UnblockFsConnect must be true on HP firmware")
    if config["UEFI"]["Quirks"]["ReleaseUsbOwnership"] is not True:
        raise SystemExit("ReleaseUsbOwnership must be true")
    security = config["Misc"]["Security"]
    if security["SecureBootModel"] != "Disabled" or security["Vault"] != "Optional" or security["ScanPolicy"] != 0:
        raise SystemExit("security defaults drifted")
    drivers = {row["Path"]: row for row in config["UEFI"]["Drivers"]}
    if "HfsPlus.efi" in drivers or "OpenHfsPlus.efi" not in drivers:
        raise SystemExit("filesystem driver selection is wrong")
    if drivers["OpenRuntime.efi"]["LoadEarly"]:
        raise SystemExit("OpenCore 1.0.8 Sample.plist leaves OpenRuntime LoadEarly false")
    for tool in config["Misc"]["Tools"]:
        if not tool["Flavour"]:
            raise SystemExit(f"{tool['Path']} needs a Flavour (ocvalidate rejects an empty one)")
    boot_args = config["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"]
    for token in ("revpatch=sbvmm", "debug=0x100", "keepsyms=1", f"alcid={alcid}"):
        if token not in boot_args:
            raise SystemExit(f"boot-args missing {token}: {boot_args}")
    enabled = [row["BundlePath"] for row in config["Kernel"]["Add"] if row["Enabled"]]
    if any("IntelBluetoothInjector" in path for path in enabled):
        raise SystemExit("IntelBluetoothInjector must not be enabled")
    airport = [path for path in enabled if "AirportItlwm" in path]
    itlwm = [path for path in enabled if path.endswith("itlwm.kext") or path == "itlwm.kext"]
    if airport and itlwm:
        raise SystemExit("AirportItlwm and itlwm are both enabled")
    if wifi == "sequoia" and not any("AirportItlwm_Sequoia" in path for path in airport):
        raise SystemExit("Sequoia AirportItlwm is not enabled")
    if wifi == "itlwm" and not itlwm:
        raise SystemExit("itlwm mode did not enable itlwm.kext")
    ranges = []
    for row in config["Kernel"]["Add"]:
        if row["Enabled"] and row["MinKernel"] and row["MaxKernel"] and "PlugIns" not in row["BundlePath"]:
            ranges.append((row["BundlePath"], row["MinKernel"], row["MaxKernel"]))
    for left in range(len(ranges)):
        for right in range(left + 1, len(ranges)):
            a0, a1 = ranges[left][1], ranges[left][2]
            b0, b1 = ranges[right][1], ranges[right][2]
            if a0 <= b1 and b0 <= a1:
                raise SystemExit(f"kernel ranges overlap: {ranges[left]} and {ranges[right]}")
    ssdt = {row["Path"]: row["Enabled"] for row in config["ACPI"]["Add"]}
    if ssdt.get("SSDT-XOSI.aml") is not False:
        raise SystemExit("SSDT-XOSI must ship disabled")
    if config["ACPI"]["Patch"][0]["Enabled"] is not False:
        raise SystemExit("OSI rename must ship disabled")
    platform = config["DeviceProperties"]["Add"]["PciRoot(0x0)/Pci(0x2,0x0)"]["AAPL,ig-platform-id"]
    if platform != bytes.fromhex(versions["IG_PLATFORM_ID"]):
        raise SystemExit("ig-platform-id mismatch")


def can_execute(path: Path) -> bool:
    try:
        subprocess.run([str(path)], capture_output=True, text=True, check=False)
    except OSError:
        return False
    return True


def run_ocvalidate(opencore: Path, config_path: Path, required: bool) -> None:
    candidates = list(opencore.rglob("ocvalidate"))
    candidates = [path for path in candidates if path.is_file() and not path.name.endswith(".exe")]
    runnable = next((path for path in candidates if os.access(path, os.X_OK) and can_execute(path)), None)
    if runnable is None:
        message = "ocvalidate from the OpenCore release is not runnable on this OS"
        if required:
            raise SystemExit(message)
        print(f"skip     {message}")
        return
    print(f"validate {runnable}")
    result = subprocess.run([str(runnable), str(config_path)], text=True, capture_output=True, check=False)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    combined = result.stdout + result.stderr
    if result.returncode != 0 or "No issues found" not in combined:
        raise SystemExit(f"ocvalidate failed with status {result.returncode}")


def copy_firmware(opencore: Path) -> None:
    boot = EFI / "BOOT"
    oc = EFI / "OC"
    drivers = oc / "Drivers"
    tools = oc / "Tools"
    for directory in (boot, drivers, tools, KEXTS):
        directory.mkdir(parents=True, exist_ok=True)
    mapping = {
        "EFI/BOOT/BOOTx64.efi": boot / "BOOTx64.efi",
        "EFI/OC/OpenCore.efi": oc / "OpenCore.efi",
        "EFI/OC/Drivers/OpenRuntime.efi": drivers / "OpenRuntime.efi",
        "EFI/OC/Drivers/OpenHfsPlus.efi": drivers / "OpenHfsPlus.efi",
        "EFI/OC/Drivers/ResetNvramEntry.efi": drivers / "ResetNvramEntry.efi",
        "EFI/OC/Drivers/ToggleSipEntry.efi": drivers / "ToggleSipEntry.efi",
        "EFI/OC/Tools/OpenShell.efi": tools / "OpenShell.efi",
        "EFI/OC/Tools/ControlMsrE2.efi": tools / "ControlMsrE2.efi",
    }
    for tail, target in mapping.items():
        shutil.copy2(find_x64(opencore, tail), target)


def archives_for(versions: dict[str, str], wifi: str, with_cpufriend: bool) -> list[tuple[str, str, set[str], set[str], dict[str, str]]]:
    """Return url, filename, copy-names, required-names, rename map."""
    v = versions
    rows = [
        (github("acidanthera/OpenCorePkg", v["OPENCORE_VERSION"], f"OpenCore-{v['OPENCORE_VERSION']}-RELEASE.zip"),
         f"OpenCore-{v['OPENCORE_VERSION']}-RELEASE.zip", set(), set(), {}),
        (github("acidanthera/Lilu", v["LILU_VERSION"], f"Lilu-{v['LILU_VERSION']}-RELEASE.zip"),
         f"Lilu-{v['LILU_VERSION']}-RELEASE.zip", {"Lilu"}, {"Lilu"}, {}),
        (github("acidanthera/VirtualSMC", v["VIRTUALSMC_VERSION"], f"VirtualSMC-{v['VIRTUALSMC_VERSION']}-RELEASE.zip"),
         f"VirtualSMC-{v['VIRTUALSMC_VERSION']}-RELEASE.zip",
         {"VirtualSMC", "SMCProcessor", "SMCBatteryManager"},
         {"VirtualSMC", "SMCProcessor", "SMCBatteryManager"}, {}),
        (github("acidanthera/WhateverGreen", v["WHATEVERGREEN_VERSION"], f"WhateverGreen-{v['WHATEVERGREEN_VERSION']}-RELEASE.zip"),
         f"WhateverGreen-{v['WHATEVERGREEN_VERSION']}-RELEASE.zip", {"WhateverGreen"}, {"WhateverGreen"}, {}),
        (github("acidanthera/AppleALC", v["APPLEALC_VERSION"], f"AppleALC-{v['APPLEALC_VERSION']}-RELEASE.zip"),
         f"AppleALC-{v['APPLEALC_VERSION']}-RELEASE.zip", {"AppleALC"}, {"AppleALC"}, {}),
        (github("acidanthera/RestrictEvents", v["RESTRICTEVENTS_VERSION"], f"RestrictEvents-{v['RESTRICTEVENTS_VERSION']}-RELEASE.zip"),
         f"RestrictEvents-{v['RESTRICTEVENTS_VERSION']}-RELEASE.zip", {"RestrictEvents"}, {"RestrictEvents"}, {}),
        (github("acidanthera/NVMeFix", v["NVMEFIX_VERSION"], f"NVMeFix-{v['NVMEFIX_VERSION']}-RELEASE.zip"),
         f"NVMeFix-{v['NVMEFIX_VERSION']}-RELEASE.zip", {"NVMeFix"}, {"NVMeFix"}, {}),
        (github("acidanthera/HibernationFixup", v["HIBERNATIONFIXUP_VERSION"], f"HibernationFixup-{v['HIBERNATIONFIXUP_VERSION']}-RELEASE.zip"),
         f"HibernationFixup-{v['HIBERNATIONFIXUP_VERSION']}-RELEASE.zip", {"HibernationFixup"}, {"HibernationFixup"}, {}),
        (github("acidanthera/BrightnessKeys", v["BRIGHTNESSKEYS_VERSION"], f"BrightnessKeys-{v['BRIGHTNESSKEYS_VERSION']}-RELEASE.zip"),
         f"BrightnessKeys-{v['BRIGHTNESSKEYS_VERSION']}-RELEASE.zip", {"BrightnessKeys"}, {"BrightnessKeys"}, {}),
        (github("1Revenger1/ECEnabler", v["ECENABLER_VERSION"], f"ECEnabler-{v['ECENABLER_VERSION']}-RELEASE.zip"),
         f"ECEnabler-{v['ECENABLER_VERSION']}-RELEASE.zip", {"ECEnabler"}, {"ECEnabler"}, {}),
        (github("acidanthera/VoodooPS2", v["VOODOOPS2_VERSION"], f"VoodooPS2Controller-{v['VOODOOPS2_VERSION']}-RELEASE.zip"),
         f"VoodooPS2Controller-{v['VOODOOPS2_VERSION']}-RELEASE.zip", {"VoodooPS2Controller"}, {"VoodooPS2Controller"}, {}),
        (github("VoodooI2C/VoodooI2C", "v" + v["VOODOOI2C_VERSION"].lstrip("v"), f"VoodooI2C-{v['VOODOOI2C_VERSION']}-RELEASE.zip"),
         f"VoodooI2C-{v['VOODOOI2C_VERSION']}-RELEASE.zip",
         {"VoodooI2C", "VoodooGPIO", "VoodooInput", "VoodooI2CHID", "VoodooI2CSynaptics", "VoodooI2CELAN", "VoodooI2CAtmelMXT", "VoodooI2CFTE"},
         {"VoodooI2C"}, {}),
        (github("OpenIntelWireless/IntelBluetoothFirmware", "v" + v["INTEL_BT_VERSION"].lstrip("v"), f"IntelBluetooth-v{v['INTEL_BT_VERSION'].lstrip('v')}.zip"),
         f"IntelBluetooth-v{v['INTEL_BT_VERSION'].lstrip('v')}.zip",
         {"IntelBluetoothFirmware", "IntelBTPatcher"}, {"IntelBluetoothFirmware", "IntelBTPatcher"}, {}),
        (github("acidanthera/BrcmPatchRAM", v["BRCMPATCHRAM_VERSION"], f"BrcmPatchRAM-{v['BRCMPATCHRAM_VERSION']}-RELEASE.zip"),
         f"BrcmPatchRAM-{v['BRCMPATCHRAM_VERSION']}-RELEASE.zip", {"BlueToolFixup"}, {"BlueToolFixup"}, {}),
        (github("OpenIntelWireless/itlwm", "v" + v["ITLWM_VERSION"].lstrip("v"), f"itlwm_v{v['ITLWM_VERSION']}_stable.kext.zip"),
         f"itlwm_v{v['ITLWM_VERSION']}_stable.kext.zip", {"itlwm"}, {"itlwm"}, {}),
        (github("0xFireWolf/RealtekCardReader", "v" + v["REALTEK_CARDREADER_VERSION"].lstrip("v"),
                f"RealtekCardReader_{v['REALTEK_CARDREADER_VERSION']}_006a845_RELEASE.zip"),
         f"RealtekCardReader_{v['REALTEK_CARDREADER_VERSION']}_006a845_RELEASE.zip",
         {"RealtekCardReader"}, {"RealtekCardReader"}, {}),
        (github("0xFireWolf/RealtekCardReaderFriend", "v" + v["REALTEK_CARDREADER_FRIEND_VERSION"].lstrip("v"),
                f"RealtekCardReaderFriend_{v['REALTEK_CARDREADER_FRIEND_VERSION']}_e1e3301_RELEASE.zip"),
         f"RealtekCardReaderFriend_{v['REALTEK_CARDREADER_FRIEND_VERSION']}_e1e3301_RELEASE.zip",
         {"RealtekCardReaderFriend"}, {"RealtekCardReaderFriend"}, {}),
        (github("USBToolBox/kext", v["USBTOOLBOX_VERSION"], f"USBToolBox-{v['USBTOOLBOX_VERSION']}-RELEASE.zip"),
         f"USBToolBox-{v['USBTOOLBOX_VERSION']}-RELEASE.zip", {"USBToolBox"}, {"USBToolBox"}, {}),
        (github("laobamac/itlwm", v["AIRPORT_FORK_TAG"], v["AIRPORT_SEQUOIA_ASSET"]),
         v["AIRPORT_SEQUOIA_ASSET"], {"AirportItlwm"}, {"AirportItlwm"}, {"AirportItlwm": "AirportItlwm_Sequoia"}),
        (github("laobamac/itlwm", v["AIRPORT_FORK_TAG"], v["AIRPORT_TAHOE_ASSET"]),
         v["AIRPORT_TAHOE_ASSET"], {"AirportItlwm"}, {"AirportItlwm"}, {"AirportItlwm": "AirportItlwm_Tahoe"}),
    ]
    if wifi in {"sonoma", "all"}:
        tag = "v" + v["ITLWM_VERSION"].lstrip("v")
        rows.append((github("OpenIntelWireless/itlwm", tag, f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Sonoma14.0.kext.zip"),
                     f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Sonoma14.0.kext.zip",
                     {"AirportItlwm"}, {"AirportItlwm"}, {"AirportItlwm": "AirportItlwm_Sonoma140"}))
        rows.append((github("OpenIntelWireless/itlwm", tag, f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Sonoma14.4.kext.zip"),
                     f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Sonoma14.4.kext.zip",
                     {"AirportItlwm"}, {"AirportItlwm"}, {"AirportItlwm": "AirportItlwm_Sonoma144"}))
    if wifi in {"ventura", "all"}:
        tag = "v" + v["ITLWM_VERSION"].lstrip("v")
        rows.append((github("OpenIntelWireless/itlwm", tag, f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Ventura.kext.zip"),
                     f"AirportItlwm_v{v['ITLWM_VERSION']}_stable_Ventura.kext.zip",
                     {"AirportItlwm"}, {"AirportItlwm"}, {"AirportItlwm": "AirportItlwm_Ventura"}))
    if with_cpufriend:
        rows.append((github("acidanthera/CPUFriend", v["CPUFRIEND_VERSION"], f"CPUFriend-{v['CPUFRIEND_VERSION']}-RELEASE.zip"),
                     f"CPUFriend-{v['CPUFRIEND_VERSION']}-RELEASE.zip", {"CPUFriend"}, {"CPUFriend"}, {}))
    if wifi == "itlwm":
        # Keep the Airport kexts available but the config leaves them disabled.
        return rows
    if wifi == "sonoma":
        return [row for row in rows if "Tahoe" not in row[1] and "Sequoia" not in row[1]]
    if wifi == "ventura":
        return [row for row in rows if "Tahoe" not in row[1] and "Sequoia" not in row[1] and "Sonoma" not in row[1]]
    return rows


def macserial_binary(opencore: Path) -> Path:
    names = []
    if sys.platform.startswith("linux"):
        names.append("macserial.linux")
    elif sys.platform == "win32":
        names.append("macserial.exe")
    names.append("macserial")
    for name in names:
        hits = [path for path in opencore.rglob(name) if path.is_file()]
        for hit in hits:
            if can_execute(hit):
                return hit
    raise SystemExit("no runnable macserial binary in the OpenCore utilities")


def command_smbios(versions: dict[str, str], checksums: dict[str, str], freeze: bool) -> None:
    url = github("acidanthera/OpenCorePkg", versions["OPENCORE_VERSION"], f"OpenCore-{versions['OPENCORE_VERSION']}-RELEASE.zip")
    filename = f"OpenCore-{versions['OPENCORE_VERSION']}-RELEASE.zip"
    archive = ensure_archive(url, filename, checksums, freeze)
    if freeze:
        save_checksums(checksums)
    extract = EXTRACTED / "OpenCore"
    safe_extract(archive, extract)
    binary = macserial_binary(extract)
    model = versions["SMBIOS_PRODUCT"]
    result = subprocess.run([str(binary), "-m", model, "-n", "1"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit("macserial failed")
    line = ""
    for candidate in result.stdout.splitlines():
        if "|" in candidate and not candidate.lower().startswith("warning"):
            line = candidate.strip()
    if "|" not in line:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("could not parse macserial output")
    serial, board = [part.strip() for part in line.split("|", 1)]
    payload = {
        "SystemProductName": model,
        "SystemSerialNumber": serial,
        "MLB": board,
        "SystemUUID": str(uuid.uuid4()).upper(),
        "ROM": os.urandom(6).hex(),
    }
    destination = ROOT / "user" / "smbios.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")
    print("This file is gitignored. Do not commit it or post the values.")
    print("Check the serial on Apple's coverage page. It should be rejected as not found.")
    print("Rebuild the EFI so dist/EFI picks the values up. config/config.plist stays a placeholder.")


def command_build(args: argparse.Namespace, versions: dict[str, str], checksums: dict[str, str]) -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    EFI.mkdir(parents=True)
    KEXTS.mkdir(parents=True)
    rows = archives_for(versions, args.wifi, args.with_cpufriend or (ROOT / "user" / "CPUFriendDataProvider.kext").is_dir())
    extracts: list[tuple[Path, set[str], set[str], dict[str, str]]] = []
    opencore_extract = EXTRACTED / "OpenCore"
    for url, filename, names, required, rename in rows:
        archive = ensure_archive(url, filename, checksums, args.write_checksums)
        folder = EXTRACTED / Path(filename).stem
        if filename.startswith("OpenCore-"):
            folder = opencore_extract
        safe_extract(archive, folder)
        extracts.append((folder, names, required, rename))
    if args.write_checksums:
        save_checksums(checksums)
        print(f"wrote {CHECKSUMS}")
    copy_firmware(opencore_extract)
    compile_acpi()
    for folder, names, required, rename in extracts:
        if not names:
            continue
        copy_kexts(folder, names, required, rename)
    extras: set[str] = set()
    user_map = ROOT / "user" / "UTBMap.kext"
    if user_map.is_dir():
        shutil.copytree(user_map, KEXTS / "UTBMap.kext")
        extras.add("UTBMap")
        print("copied  user/UTBMap.kext and enabled USBToolBox")
    provider = ROOT / "user" / "CPUFriendDataProvider.kext"
    if provider.is_dir():
        shutil.copytree(provider, KEXTS / "CPUFriendDataProvider.kext")
        extras.add("CPUFriendDataProvider")
        print("copied  CPUFriendDataProvider.kext")
    if not any(path.name == "VoodooI2CHID.kext" for path in KEXTS.rglob("VoodooI2CHID.kext")):
        raise SystemExit("VoodooI2CHID.kext was not found inside the VoodooI2C release")
    config = build_config(opencore_extract, versions, args.wifi, args.alcid, extras)
    lint_config(config, versions, args.wifi, args.alcid)
    write_plist(TEMPLATE, config)
    dist_config = EFI / "OC" / "config.plist"
    smbios_file = ROOT / "user" / "smbios.json"
    if smbios_file.exists():
        injected = json.loads(json.dumps(config, default=lambda item: list(item) if isinstance(item, bytes) else item))
        # Re-load from the template so binary fields stay bytes.
        with TEMPLATE.open("rb") as handle:
            injected = plistlib.load(handle)
        inject_smbios(injected, json.loads(smbios_file.read_text(encoding="utf-8")))
        write_plist(dist_config, injected)
        print("injected user/smbios.json into dist only")
    else:
        write_plist(dist_config, config)
    notes = ROOT / "THIRD-PARTY-NOTICES.md"
    shutil.copy2(notes, DIST / "THIRD-PARTY-NOTICES.md")
    info = DIST / "VERSIONS.txt"
    info.write_text(
        "\n".join(
            [
                "HP EliteBook x360 1030 G2 OpenCore EFI",
                f"wifi mode: {args.wifi}",
                f"OpenCore: {versions['OPENCORE_VERSION']}",
                f"SMBIOS placeholder product: {versions['SMBIOS_PRODUCT']}",
                "Serials in config/config.plist are placeholders.",
                "See the repository README for what was tested and what was not.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    run_ocvalidate(opencore_extract, dist_config, args.require_ocvalidate)
    archive_path = DIST / "EliteBook-x360-1030-G2-OpenCore.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in DIST.rglob("*"):
            if path == archive_path or not path.is_file():
                continue
            package.write(path, path.relative_to(DIST).as_posix())
    enabled = [row["BundlePath"] for row in config["Kernel"]["Add"] if row["Enabled"]]
    disabled = [row["BundlePath"] for row in config["Kernel"]["Add"] if not row["Enabled"]]
    print(f"enabled kexts: {len(enabled)}")
    for name in enabled:
        print(f"  + {name}")
    print(f"disabled kexts: {len(disabled)}")
    for name in disabled:
        print(f"  - {name}")
    print(f"zip      {archive_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the EliteBook x360 1030 G2 OpenCore EFI")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="download pinned releases and assemble dist/EFI")
    build.add_argument("--wifi", choices=("sequoia", "tahoe", "itlwm", "sonoma", "ventura", "all"), default="sequoia")
    build.add_argument("--with-cpufriend", action="store_true")
    build.add_argument("--require-ocvalidate", action="store_true")
    build.add_argument("--write-checksums", action="store_true")
    build.add_argument("--alcid", type=int, default=None)
    smbios = sub.add_parser("smbios", help="write user/smbios.json with macserial")
    smbios.add_argument("--write-checksums", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    versions = load_versions()
    checksums = load_checksums()
    if args.command == "smbios":
        command_smbios(versions, checksums, args.write_checksums)
        return
    if args.alcid is None:
        args.alcid = int(versions["DEFAULT_ALCID"])
    if args.wifi == "tahoe":
        # Same archives as Sequoia. The Tahoe kext is already kernel-gated.
        args.wifi = "sequoia"
        print("wifi mode tahoe uses the Sequoia package; AirportItlwm_Tahoe loads only on Darwin 25")
    command_build(args, versions, checksums)


if __name__ == "__main__":
    main()
