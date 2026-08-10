# 06 · Troubleshooting

> Rule 0 of this repo's debugging method: **one layer at a time, logs over
> guesses, keep a fallback EFI.** If you're stuck, attach the evidence listed
> in the [issue template](../.github/ISSUE_TEMPLATE/bug_report.yml) — a bug
> report without a verbose log is a story, not a bug report.

## Black screen / no display

| Situation | Likely cause | Action |
|---|---|---|
| Black screen after OpenCore logo | Panel not in the connector map | Confirm you're on `0x59160000` + `-igfxonln=1`. Add `-igfxdbg` to boot-args and read the connector logs. |
| Works in VESA mode (`-igfxvesa`) but nothing else | Framebuffer mismatch | Compare `device-id` (`0x5916`) with `AAPL,ig-platform-id`; see [docs/05 §3](05-debugging-journey.md). |
| Black screen only on cold boot, fine on restart | DVMT/framebuffer timing | Try `framebuffer-fbmem=9MB`/`stolenmem=19MB` (already set) and test `-igfxblr` (backlight register) if the panel is LED. |
| **7 MB VRAM** in System Information | `framebuffer-unifiedmem` missing | Must be `0x80000000` (2048 MB) — see [docs/03](03-configuration.md). |

## Boot stalls / kernel panics

- **Always boot verbose once** to capture the failing stage: add `-v` to
  `boot-args`, boot, note the **last line** before the hang/panic.
- `keepsyms=1` is already set — the panic shows symbol names, not just
  addresses.
- Common this-machine stops:
  - `IOConsoleUsers: gIOScreenLockState` → graphics stage (see above)
  - `VM Swap Subsystem is ON` → usually fine, wait
  - `hpms`/ACPI errors → check the RTC patch is still enabled (`ACPI > Patch`)
- **Recovery boots but installer fails**: network layer — see
  [docs/05 §2](05-debugging-journey.md).

## USB — a port, or the camera, doesn't work

The shipped `UTBMap.kext` matches this model (internal camera/mic ports
included). If something is missing:

1. Confirm the port **itself** is alive: `System Information → USB`,
   or `ioreg -p IOUSB -w0`.
2. If the port is missing entirely → re-generate the map
   ([docs/04](04-kexts-drivers.md) → "UTBMap — the part you must not copy blindly").
3. Do **not** re-enable `XhciPortLimit` — broken since macOS 11.3.

## Audio

- No output at all → confirm `layout-id 3` on `Pci(0x1f,0x3)` and that
  AppleALC is loaded (`kextstat | grep AppleALC`).
- Internal speaker works, jack doesn't (or vice-versa) → try layouts 13 / 28
  for this codec family, keeping everything else unchanged (one layer at a time).
- No audio device in the picker for boot chime — expected: `AudioSupport=false`
  (see "Known limitations").

## Wi-Fi

- Internal RTL8821CE **cannot** work — no driver exists. Use the MT7601 USB
  dongle (shipped kext) or swap in a Broadcom card.
- Dongle not detected → check `RT2870USBWirelessDriver.kext` is in
  `Kernel > Add` (it is) and that the USB port it sits in is in the map.

## Updates (OTA) and boot-args after updates

- OTA updates are enabled via `revpatch=sbvmm` + `SecureBootModel=Disabled`.
- After a major update, kexts may need refresh (esp. Lilu + WhateverGreen +
  AppleALC). Re-run `scripts/validate_efi.py` after updating kexts.

## Reset NVRAM — your reset button

In the OpenCore picker choose **Reset NVRAM** (shipped via
`ResetNvramEntry.efi`) whenever a boot-arg experiment leaves you in a bad state,
or when switching between config iterations. This machine's RTC patch survives
NVRAM resets (that's the point of the ACPI-level fix).

## Collecting evidence (for issues)

Minimal set that makes a bug report actionable:

```
# 1. OpenCore version (add Tools/OpenShell or use the picker):
#    run "opencore-version" from the UEFI shell, or read the EFI log

# 2. Verbose boot log — boot with -v and photograph the LAST screen lines

# 3. OpenCore log file (already enabled: Misc > Debug > Target=3)
#    → /EFI/OC/ (OpenCore log is written to the EFI volume)

# 4. Hardware identity:
ioreg -lw0 | grep -i "model\|board-id"     # SMBIOS in use
system_profiler SPUSBDataType              # USB topology
system_profiler SPAudioDataType            # audio codecs
kextstat | grep -v com.apple               # third-party kexts loaded

# 5. SMBIOS scrubbed — never share serials in screenshots
```

---

Next: **[07-smbios-icloud.md](07-smbios-icloud.md)** · or back to the [README](../README.md)
