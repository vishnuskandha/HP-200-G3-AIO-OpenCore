#!/usr/bin/env python3
"""
scrub_smbios.py — strip SMBIOS identity from config.plist for safe sharing.

Writes a new file next to the original (config.plist.scrubbed) with all
PlatformInfo > Generic identity fields replaced by placeholders, so no real
serial/MLB/UUID/ROM ever ends up in a screenshot, a pull request or a pastebin.

Usage:
    python scripts/scrub_smbios.py [config.plist] [--inplace]

The scrubbed config still boots (macOS shows a generic identity), but you
should generate real values with GenSMBIOS before daily use:
    https://github.com/corpnewt/GenSMBIOS   (MacBookPro15,2)
See docs/07-smbios-icloud.md for the full guide.
"""

import argparse
import os
import plistlib
import shutil
import sys

PLACEHOLDERS = {
    "MLB": "00000000000000000",
    "SystemSerialNumber": "000000000000",
    "SystemUUID": "00000000-0000-0000-0000-000000000000",
    "ROM": b"\x00\x00\x00\x00\x00\x00",
    "HwTarget": "0",
}

FIELDS = ("MLB", "SystemSerialNumber", "SystemUUID", "ROM")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", default="EFI/OC/config.plist")
    parser.add_argument("--inplace", action="store_true",
                        help="overwrite the original file instead of writing a copy")
    args = parser.parse_args()

    src = os.path.abspath(args.config)
    if not os.path.isfile(src):
        print(f"config not found: {src}")
        return 1

    with open(src, "rb") as fh:
        cfg = plistlib.load(fh)

    generic = cfg.get("PlatformInfo", {}).get("Generic", {})
    changed = []
    for field in FIELDS:
        if field in generic:
            old = generic[field]
            if isinstance(old, bytes) or old != PLACEHOLDERS[field]:
                generic[field] = PLACEHOLDERS[field]
                changed.append(field)

    if not changed:
        print("No real-looking SMBIOS values found — nothing to scrub.")
        return 0

    dst = src if args.inplace else src + ".scrubbed"
    with open(dst, "wb") as fh:
        plistlib.dump(cfg, fh, sort_keys=False)
    print(f"Scrubbed {', '.join(changed)} -> {dst}")
    print("Fill in your own values (GenSMBIOS, MacBookPro15,2) before installing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
