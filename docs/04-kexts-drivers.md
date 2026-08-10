# 04 · Kexts & drivers — what, why, and how to update safely

## Kexts (in `EFI/OC/Kexts/`, load order)

| # | Kext | Version (shipped) | What it does | Required? |
|---|---|---|---|---|
| 1 | **Lilu** | 1.7.3 | Patching foundation; every Acidanthera kext depends on it | ✅ |
| 2 | **AppleALC** | 1.9.8 | Onboard audio (ALC3247, `layout-id 3`) | ✅ |
| 3 | **RealtekRTL8111** | 2.4.2 | Wired GbE (RTL8111HSH) | ✅ |
| 4 | **RestrictEvents** | 1.1.7 | Feature-flag control; `revpatch=sbvmm` enables OTA updates | ✅ |
| 5 | **VirtualSMC** | 1.3.8 | Fake SMC — macOS won't boot without it | ✅ |
| 6 | **SMCProcessor** | 1.3.8 | CPU temperature/frequency sensors | ✅ |
| 7 | **SMCSuperIO** | 1.3.8 | Fan/Super-IO sensors | ✅ |
| 8 | **USBToolBox** | 1.2.0 | USB mapping runtime | ✅ |
| 9 | **WhateverGreen** | 1.7.1 | All iGPU fixes (framebuffer, connectors, VRAM) | ✅ |
| 10 | **UTBMap** | 1.1 | **Your machine's USB port map** (generated, data-only) | ✅ |
| 11 | **RT2870USBWirelessDriver** | (Ralink) | MT7601 USB Wi-Fi dongle | ⚠️ only if you use this dongle |

### UTBMap — the part you must not copy blindly

`UTBMap.kext` is a *generated* map of **this machine's** USB ports. If you have
the same model it will very likely match (camera/mic ports are the same on the
i5/i3 variants), but if you ever get "no USB on that port", re-generate it:

1. Boot with **USBToolBox + UTBMap removed** and `XhciPortLimit` temporarily
   enabled, or use the Windows [USBToolBox](https://github.com/USBToolBox/tool)
   app.
2. Plug a USB 2.0 and USB 3.0 device into **every** port (including a Bluetooth
   dongle to find the internal BT port).
3. Save the map → `UTBMap.kext`.

See the USB section of [docs/05](05-debugging-journey.md) for why the internal
ports matter on this machine.

## Drivers (in `EFI/OC/Drivers/`)

| Driver | Purpose |
|---|---|
| `HfsPlus.efi` | HFS+ / APFS volume support (from OpenCore's own build). |
| `OpenRuntime.efi` | OpenCore runtime services — **required**. |
| `ResetNvramEntry.efi` | Adds "Reset NVRAM" to the picker — your best friend when experimenting. |

> `OpenShell.efi` is intentionally not shipped; add it to `EFI/OC/Tools/` if you
> want a UEFI shell for debugging.

## ACPI tables (in `EFI/OC/ACPI/`)

`SSDT-EC`, `SSDT-PLUG`, `SSDT-SBUS`, `SSDT-MCHC`, `SSDT-USBX`, `SSDT-RTCAWAC` —
see [docs/03](03-configuration.md) for what each one does. These are standard
Dortania "Gathering files" SSDTs (plus the HP RTC bits).

## Updating safely (OpenCore, kexts, drivers)

The golden rule: **update components, keep the configuration.**

1. Download the new kext/driver from its upstream release page
   (links below) — never from random mirrors.
2. Replace the `.kext`/`.efi` inside `EFI/` (keep the folder structure).
3. **Do not** re-run a generic OpenCore "config builder" over your config —
   the iGPU block in `DeviceProperties` and the boot-args in `NVRAM` are
   machine-specific and would be lost.
4. Validate:
   ```powershell
   python scripts/validate_efi.py EFI/OC/config.plist
   ```
5. Reboot. Keep the previous EFI backed up (the old config + `OpenCore.efi`
   on a USB) until the new combo has booted twice.

## Upstream sources

- OpenCore: https://github.com/acidanthera/OpenCorePkg
- Lilu / WhateverGreen / AppleALC / VirtualSMC / RestrictEvents:
  https://github.com/acidanthera
- RealtekRTL8111: https://github.com/Mieze/RTL8111_driver_for_mac_OS
- USBToolBox: https://github.com/USBToolBox/kext
- Wireless USB (RT2870/MT7601): https://github.com/chris1111/Wireless-USB-Adapter

---

Next: **[05-debugging-journey.md](05-debugging-journey.md)** — the story · or back to the [README](../README.md)
