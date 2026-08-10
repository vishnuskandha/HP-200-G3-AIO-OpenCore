# 01 · Hardware — the HP 200 G3 All-in-One

> Source: [HP 200 G3 All-in-One PC specifications](https://support.hp.com/us-en/document/c05950812)
> (product numbers 3VA37EA / 3VA38EA family).

Every component below was verified on the machine used to build this EFI.
The "macOS mapping" column explains *why* the EFI is configured the way it is —
this is the important part for anyone adapting this build.

## Spec sheet

| Component | Spec | macOS mapping |
|---|---|---|
| **CPU** | Intel Core **i5-8250U** — Kaby Lake-R, 4C/8T, 1.6–3.4 GHz, 6 MB L3 | Native; `SSDT-PLUG.aml` enables `_PMS` → native XCPM power management. i3-8130U variant works the same. |
| **iGPU** | Intel **UHD Graphics 620** (PCI `0x5916`) | **The whole story of this repo.** See [docs/05](05-debugging-journey.md). Patched to `framebuffer 0x59160000` + 2048 MB unifiedmem. |
| **Display** | 21.5″ FHD (1920×1080) anti-glare, WLED, internal eDP | Internal panel driven by the patched framebuffer. **This AIO model has no external DP-in port** — the panel must be brought online by `-igfxonln=1`. |
| **RAM** | 4 GB DDR4-2133 (2× SODIMM, up to 16 GB) | Native. |
| **Storage** | 1× 3.5″ SATA (HDD/SSD) + 1× M.2 2280 SATA + SATA DVD-RW | Native (SATA controller needs no extra kext). |
| **Audio** | Realtek **ALC3247** codec (ALC256 family), internal speaker, headphone/mic combo, rear line-in/out | AppleALC with **`layout-id 3`** — the tested layout for this codec. |
| **LAN** | Realtek **RTL8111HSH-CG** GbE (RJ-45) | `RealtekRTL8111.kext` (2.4.2) |
| **WLAN (onboard)** | Realtek **RTL8821CE** 802.11ac M.2 | ❌ **No macOS driver exists.** Replaced functionally by a USB dongle (below). |
| **Wi-Fi (used)** | MediaTek **MT7601** USB dongle (802.11n) | `RT2870USBWirelessDriver.kext` (Wi-Fi only — no BT/AirDrop). |
| **Camera** | 1 MP HD webcam, 720p@30, dual-array mic | Internal **USB** device — only works if the USB map keeps its port enabled (see `docs/05`). |
| **USB** | Rear: 2× USB 2.0, 2× USB 3.1 Gen1 · Bottom: 3-in-1 SD reader | Custom map (`USBToolBox` + `UTBMap`) with internal ports included. |
| **HDMI-out** | 1× HDMI 1.4b (rear) | Connected to the iGPU — second display; untested in this build. |
| **Power** | 65 W external adapter | — |
| **TPM / Security** | TPM 2.0, lock slot | Disable Secure Boot in BIOS; TPM is irrelevant for macOS. |

## Why the "all-in-one" part matters

Two things make an AIO different from a laptop or desktop hackintosh:

1. **The panel is fixed to the machine.** There is no "just plug in a monitor".
   If the framebuffer's connector map doesn't match the panel's eDP path, you get
   a black screen — which is exactly what happened, and exactly what
   `0x59160000` + the igfx boot-args fixed.
2. **Internal peripherals sit on the internal USB controller.** The webcam,
   microphone and (on some SKUs) the Bluetooth adapter enumerate as USB devices
   with ports that look "unused" from outside. A naive USB map that only covers
   external ports silently kills the camera — see the USB section in
   [docs/05](05-debugging-journey.md).

## Variants of this machine

- **i5-8250U** (3VA38EA) — what this EFI was built on
- **i3-8130U** (3VA37EA) — same UHD 620, same framebuffer setup; the EFI should
  work as-is (please confirm in Issues if you tested it)
- The **200 G3** desktop/mini and **ProOne 400 G3** are *different* machines —
  this EFI is for the all-in-one.

## Firmware facts used by this EFI

- BIOS uses an **AWAC** (Always-On-Artwork) clock — handled by
  `SSDT-RTCAWAC.aml` + the `_STA → XSTA` renames.
- HP boards historically trigger a **"005 — Real Time Clock Power Loss"** POST
  error when macOS writes the RTC in a way HP doesn't expect. Patched in
  `ACPI > Patch` ("Fix HP Real-Time Clock Power Loss (005) Post Error") and by
  `DisableRtcChecksum` + `rtc-blacklist` in NVRAM.

---

Next: **[02-installation.md](02-installation.md)** · or back to the [README](../README.md)
