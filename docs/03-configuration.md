# 03 · config.plist — what every section does

> This file documents the shipped `EFI/OC/config.plist`. Values below are the
> ones actually in the repo — nothing here is theoretical.
>
> Structure reference: the official [Dortania configuration guide](https://dortania.github.io/OpenCore-Install-Guide/config-laptop.plist/kaby-lake.html)
> for Kaby Lake laptops (this machine behaves like one).

## Top-level sections

| Section | Role in this build |
|---|---|
| `ACPI` | SSDTs + firmware ACPI patches |
| `Booter` | boot.efi patching and memory quirks |
| `DeviceProperties` | **the iGPU and audio fixes live here** |
| `Kernel` | kext loading order, kernel quirks |
| `Misc` | picker, debug logging, security |
| `NVRAM` | boot-args, csr-active-config, RTC blacklist |
| `PlatformInfo` | SMBIOS identity (MacBookPro15,2) |
| `UEFI` | UEFI drivers, console, input, APFS |

---

## ACPI

**Added tables** (all enabled, `ACPI > Add`):

| SSDT | Purpose |
|---|---|
| `SSDT-EC.aml` | Fake Embedded Controller (USBX/EC0). |
| `SSDT-PLUG.aml` | Enables `_PMS` on the CPU PR scope → native XCPM power management. |
| `SSDT-SBUS.aml` | Fake SMBus (needed by some SMC plugins). |
| `SSDT-MCHC.aml` | Fake Memory Controller Hub. |
| `SSDT-USBX.aml` | USB power properties (with the EC rename below). |
| `SSDT-RTCAWAC.aml` | Shims the always-on AWAC clock into the RTC macOS expects. |

**Patches** (`ACPI > Patch`):

1. **AWAC `_STA` → `XSTA` rename** — pairs with `SSDT-RTCAWAC.aml`.
2. **EC0 `_STA` → `XSTA` rename** — pairs with `SSDT-EC.aml`; disables the
   firmware's own EC device so the SSDT's fake one is used.
3. **Fix HP Real-Time Clock Power Loss (005) POST Error** —
   `47 01 70 00 70 00 00 08` → `47 01 70 00 70 00 00 02`. HP boards flag the
   "005 Real Time Clock Power Loss" error at POST when macOS re-initializes the
   RTC. This patch (plus `DisableRtcChecksum` and the `rtc-blacklist` NVRAM
   variable) suppresses it.

**Quirks**: `ResetLogoStatus=true` (clean logo/firmware state after macOS restarts).

---

## Booter

- **Quirks that matter here:**
  - `AvoidRuntimeDefrag`, `SetupVirtualMap`, `ProvideCustomSlide`,
    `EnableWriteUnprotector`, `FixupAppleEfiImages` — the standard set for
    OEM UEFI firmware.
  - `EnableSafeModeSlide=true` — safe mode boots correctly.
- The "macOS → hacOS" patch is present but **disabled** — it's a diagnostic
  trick, not part of a production config (this repo practices what the
  debugging doc preaches: no scaffolding in the final EFI).

---

## DeviceProperties — the two most important blocks

```xml
PciRoot(0x0)/Pci(0x2,0x0)        ← the iGPU (UHD 620)
    AAPL,ig-platform-id     00001659  → framebuffer 0x59160000
    device-id              16590000  → 0x5916 (Kaby Lake-R UHD 620)
    framebuffer-patch-enable    1
    framebuffer-stolenmem  0x01300000 → 19 MB stolen memory
    framebuffer-fbmem      0x00900000 → 9 MB framebuffer memory
    framebuffer-unifiedmem 0x80000000 → 2048 MB VRAM  ← the black-screen fix
```

| Property | Value | Why |
|---|---|---|
| `AAPL,ig-platform-id` | `0x59160000` | KBL-R UHD 620 framebuffer (3 connectors, eDP-capable). **Not** `0x59120000` — that one is for plain Kaby Lake and produces the 7 MB VRAM black screen. |
| `device-id` | `0x5916` | Spoofs/confirms the real PCI id so the framebuffer matches. |
| `framebuffer-stolenmem` | 19 MB | Fits the 32 MB DVMT pre-alloc common on this board. |
| `framebuffer-fbmem` | 9 MB | Standard for this framebuffer. |
| `framebuffer-unifiedmem` | **2048 MB** | Allocates full VRAM — without it macOS reports 7 MB and acceleration never engages. |

```xml
PciRoot(0x0)/Pci(0x1f,0x3)       ← HD Audio (ALC3247)
    layout-id  3
```

`layout-id 3` is the AppleALC layout tested working for the ALC256-family
(ALC3247) codec on this machine — internal speaker + headphone/mic combo jack.

---

## Kernel

**Kext load order** (the order in `Kernel > Add` matters — dependencies first):

1. `Lilu.kext` — the patching foundation everything else depends on
2. `AppleALC.kext` — audio
3. `RealtekRTL8111.kext` — wired LAN
4. `RestrictEvents.kext` — feature flags (`revpatch=sbvmm` for OTA updates)
5. `VirtualSMC.kext` — fake SMC
6. `SMCProcessor.kext` — CPU sensor keys
7. `SMCSuperIO.kext` — Super I/O sensors
8. `USBToolBox.kext` — USB mapping runtime
9. `WhateverGreen.kext` — graphics patching (iGPU fixes)
10. `UTBMap.kext` — the generated USB port map (data only)
11. `RT2870USBWirelessDriver.kext` — MT7601 USB Wi-Fi

**Quirks that matter:**

| Quirk | Value | Why |
|---|---|---|
| `AppleXcpmCfgLock` | true | Board has no CFG-Lock unlock option in BIOS. |
| `DisableIoMapper` | true | No VT-d support needed; avoids DMAR issues. |
| `DisableLinkeditJettison` | true | Required for Lilu-based kexts on modern macOS. |
| `DisableRtcChecksum` | true | HP RTC protection (see ACPI section). |
| `LapicKernelPanic` | true | HP/Intel OEM lapic quirks. |
| `PanicNoKextDump`, `PowerTimeoutKernelPanic` | true | Nicer panics, no kext dump noise. |
| `XhciPortLimit` | false | **Correct** — USB mapping (UTBMap) replaces this obsolete limit patch (broken since macOS 11.3). |

---

## Misc

- **Boot**: picker visible, 5 s timeout, `PickerAttributes=17` (modern picker).
- **Debug**: `Target=3` (console + file log), `DisplayLevel=0x80000002`,
  `DisableWatchDog=true` — verbose-friendly but quiet by default.
- **Security**: `SecureBootModel=Disabled`, `Vault=Optional`,
  `DmgLoading=Signed`, `BlacklistAppleUpdate=true` (no surprise update packages),
  `ExposeSensitiveData=6`.

---

## NVRAM

`7C436110-AB2A-4BBB-A880-FE41995C9F82` (boot-args):

```
keepsyms=1 -igfxonln=1 -igfxfw=2 -igfxrps ipc_control_port_options=0
```

| Arg | Meaning |
|---|---|
| `keepsyms=1` | Keep kernel symbols for panics (harmless to leave). |
| `-igfxonln=1` | WhateverGreen: force **all connectors online** — required so the internal panel comes up. |
| `-igfxfw=2` | WhateverGreen: aggressive Intel **firmware (GuC/HuC) loading** for the iGPU. |
| `-igfxrps` | WhateverGreen: enable iGPU **RPS control** (correct P-states → smooth UI). |
| `ipc_control_port_options=0` | Sequoia-era stability fix (avoids a known IOPCIFamily/IOKit panic path). |

Other keys:
- `csr-active-config = 0xA030000` — **SIP partially disabled** (for kext
  loading under `SecureBootModel=Disabled`). This is the community-standard
  value, not a security hole: re-enable fully (`0x00000000`) if you use
  `SecureBootModel` with vaulting.
- `revpatch=sbvmm` (UUID `4D1FDA02-…`) — lets macOS OTA updates run with
  `SecureBootModel=Disabled`.
- `rtc-blacklist` (empty data) — pairs with `DisableRtcChecksum` for HP RTC.
- `prev-lang:kbd` — deliberately unset (boots in system language).

---

## PlatformInfo

- `SystemProductName = MacBookPro15,2` — the 13″ 2018–2019 MacBook Pro;
  matches an 8th-gen UHD 620 machine.
- `Automatic = true` → MLB/SN/UUID/ROM are used as-is from `Generic`.
- `UpdateSMBIOSMode = Custom`, `SpoofVendor = true` (don't fake the vendor
  string — display the real one).
- **You must regenerate MLB/Serial/SystemUUID/ROM** — see
  [docs/07](07-smbios-icloud.md).

---

## UEFI

- **Drivers**: `HfsPlus.efi` (APFS/HFS volumes), `OpenRuntime.efi` (required
  runtime), `ResetNvramEntry.efi` (NVRAM reset tool in the picker).
- **APFS**: `EnableJumpstart=true` (boot APFS volumes), `MinDate/MinVersion=-1`
  (accept any Sequoia-era APFS).
- **Input**: `KeySupport=true` (keyboard in picker on non-Apple firmware),
  `PointerSupport=false`.
- **Output**: `ProvideConsoleGop=true`, `Resolution=Max`, `TextRenderer=BuiltinGraphics`.
- **Quirks**: `RequestBootVarRouting=true` (protect boot variables from macOS),
  `ReleaseUsbOwnership=true`, `UnblockFsConnect=true`, `EnableVectorAcceleration=true`.

---

Next: **[04-kexts-drivers.md](04-kexts-drivers.md)** · or back to the [README](../README.md)
