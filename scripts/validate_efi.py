#!/usr/bin/env python3
"""
validate_efi.py — sanity-check an OpenCore EFI against its config.plist.

Checks:
  1. config.plist parses as a plist and has all required top-level sections.
  2. Every ACPI table listed in ACPI > Add exists in ACPI/.
  3. Every kext listed in Kernel > Add exists in Kexts/ and has Info.plist.
  4. Every driver listed in UEFI > Drivers exists in Drivers/.
  5. The iGPU block is present and decodes to the known-good framebuffer.
  6. Warnings (not failures): real-looking SMBIOS values, diagnostic boot-args.

Usage:
    python scripts/validate_efi.py [config.plist] [--strict]

Exit code 0 = pass (warnings allowed unless --strict), 1 = fail.
Runs on Windows/macOS/Linux with only the Python standard library.
"""

import argparse
import base64
import os
import plistlib
import re
import sys

REQUIRED_SECTIONS = (
    "ACPI", "Booter", "DeviceProperties", "Kernel", "Misc",
    "NVRAM", "PlatformInfo", "UEFI",
)

GOOD_IG_PLATFORM_ID = b"\x00\x00\x16\x59"  # 0x59160000 (KBL-R UHD 620)
GOOD_DEVICE_ID = b"\x16\x59\x00\x00"       # 0x5916
UNIFIEDMEM_TARGET = 0x80000000             # 2048 MB

PLACEHOLDER_SERIAL = re.compile(r"^0+$|^[XxOo]{6,}$")
REAL_SERIAL_HINT = re.compile(r"^(C0[0-9]|C02|C07|FVF|C02[A-Z0-9])", re.I)


def b2int(data: bytes) -> int:
    return int.from_bytes(data, "little")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", default="EFI/OC/config.plist")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    args = parser.parse_args()

    # config lives at <repo>/EFI/OC/config.plist -> repo root is 3 levels up
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(args.config))))
    efi_oc = os.path.join(root, "EFI", "OC")
    cfg_path = os.path.abspath(args.config)

    errors, warnings = [], []

    # 1 — parse + required sections
    if not os.path.isfile(cfg_path):
        errors.append(f"config not found: {cfg_path}")
        return report(errors, warnings, strict=args.strict)

    with open(cfg_path, "rb") as fh:
        try:
            cfg = plistlib.load(fh)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"config.plist is not a valid plist: {exc}")
            return report(errors, warnings, strict=args.strict)

    for section in REQUIRED_SECTIONS:
        if section not in cfg:
            errors.append(f"missing top-level section: {section}")

    # 2 — ACPI tables
    acpi_dir = os.path.join(efi_oc, "ACPI")
    for entry in cfg.get("ACPI", {}).get("Add", []):
        path = entry.get("Path", "")
        if entry.get("Enabled", True) and not os.path.isfile(os.path.join(acpi_dir, path)):
            errors.append(f"ACPI table missing: ACPI/{path}")

    # 3 — kexts
    kext_dir = os.path.join(efi_oc, "Kexts")
    for entry in cfg.get("Kernel", {}).get("Add", []):
        path = entry.get("BundlePath", "")
        if not entry.get("Enabled", True):
            continue
        if not os.path.isdir(os.path.join(kext_dir, path)):
            errors.append(f"kext missing: Kexts/{path}")
        elif not os.path.isfile(os.path.join(kext_dir, path, "Contents", "Info.plist")):
            errors.append(f"kext has no Info.plist: Kexts/{path}")

    # 4 — drivers
    drivers_dir = os.path.join(efi_oc, "Drivers")
    for entry in cfg.get("UEFI", {}).get("Drivers", []):
        path = entry.get("Path", "")
        if entry.get("Enabled", True) and not os.path.isfile(os.path.join(drivers_dir, path)):
            errors.append(f"driver missing: Drivers/{path}")

    # 5 — iGPU block
    dev_add = cfg.get("DeviceProperties", {}).get("Add", {})
    igpu = dev_add.get("PciRoot(0x0)/Pci(0x2,0x0)")
    if not igpu:
        errors.append("DeviceProperties: missing PciRoot(0x0)/Pci(0x2,0x0) (iGPU) block")
    else:
        pid = igpu.get("AAPL,ig-platform-id")
        if pid == GOOD_IG_PLATFORM_ID:
            print("iGPU: framebuffer 0x59160000 (KBL-R UHD 620)  OK")
        else:
            got = f"0x{b2int(pid):08x}" if pid else "MISSING"
            errors.append(f"iGPU: AAPL,ig-platform-id = {got} (expected 0x59160000)")
        if b2int(igpu.get("framebuffer-unifiedmem", b"\x00\x00\x00\x00")) != UNIFIEDMEM_TARGET:
            errors.append("iGPU: framebuffer-unifiedmem != 2048 MB (black-screen fix missing)")
        did = igpu.get("device-id")
        if did and did != GOOD_DEVICE_ID:
            warnings.append(f"iGPU: device-id = 0x{b2int(did):04x} (shipped config uses 0x5916)")

    # 6 — SMBIOS hygiene (warning only)
    generic = cfg.get("PlatformInfo", {}).get("Generic", {})
    serial = str(generic.get("SystemSerialNumber", ""))
    mlb = str(generic.get("MLB", ""))
    if serial and not PLACEHOLDER_SERIAL.search(serial) and REAL_SERIAL_HINT.search(serial):
        warnings.append(
            "SMBIOS: SystemSerialNumber looks like a real serial. Generate your own "
            "with GenSMBIOS before installing/sharing (docs/07-smbios-icloud.md)."
        )
    if len(mlb) > 8 and not PLACEHOLDER_SERIAL.search(mlb):
        warnings.append(
            "SMBIOS: MLB looks like a real value. Scrub with scripts/scrub_smbios.py "
            "if you plan to redistribute."
        )

    # 7 — diagnostic scaffolding check (warning only)
    boot_args = cfg.get("NVRAM", {}).get("Add", {}) \
        .get("7C436110-AB2A-4BBB-A880-FE41995C9F82", {}).get("boot-args", "")
    for bad in ("-igfxvesa", "debug=0x100"):
        if bad in boot_args:
            warnings.append(f"boot-args contain diagnostic scaffolding: {bad}")
    print(f"boot-args: {boot_args}")

    return report(errors, warnings, strict=args.strict)


def report(errors, warnings, strict: bool) -> int:
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR:   {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    if errors:
        return 1
    if warnings and strict:
        print("Failing due to --strict.")
        return 1
    print("Validation passed." if not errors else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
