# 05 · The debugging journey — 7 MB VRAM to 2048 MB

> This is the engineering story behind the EFI: what broke, how it was
> diagnosed, and the exact fix. Written as a field note so the *method*
> transfers to other machines — not just the settings.

The machine arrived as a "compatibility problem disguised as an installation".
Following the installer never produced a working system, because the *boundary*
between firmware, boot configuration, kernel extensions, graphics and device
discovery had to be rebuilt by hand. The process that worked:

1. **Observe precisely** — record the last successful boot stage, device
   identity and visible symptom.
2. **Change one layer** — keep ACPI, kexts, device properties and boot-args
   logically separate.
3. **Preserve a fallback** — a known-bootable EFI is part of the recovery plan.
4. **Use logs over guesses** — verbose boot, `ioreg`, system reports.
5. **Remove diagnostic scaffolding** — temporary boot-args don't stay.

Every section below maps to the config that ships in this repo.

---

## 1 · Establishing a known baseline

Before changing anything, the hardware was inventoried (see
[docs/01](01-hardware.md)): CPU/iGPU generation, chipset, storage controller,
network devices, audio codec, USB controller + ports, and the AIO's display
path. That inventory decided the SMBIOS family, ACPI work, kext list and
framebuffer properties worth testing.

The EFI was kept **versioned in small iterations** — three snapshots survive
from that process and are summarized below as Config A/B/C. After every
meaningful change: record the boot stage, keep the fallback.

| Snapshot | State | iGPU platform-id | boot-args |
|---|---|---|---|
| Config A (early) | debugging, verbose | `0x59120000` | `-v debug=0x100 keepsyms=1` |
| Config B (mid) | display via VESA only | `0x59120000` | `-v debug=0x100 keepsyms=1 -igfxvesa` |
| **Config C (final)** | **fully working** | **`0x59160000`** | `keepsyms=1 -igfxonln=1 -igfxfw=2 -igfxrps ipc_control_port_options=0` |

---

## 2 · Recovery and networking: a network failure disguised as an installer failure

Early recovery attempts failed inconsistently. Because macOS Recovery depends on
remote resources, a connectivity problem looks exactly like a broken installer.

The diagnosis was decomposed instead of guessed at:

1. Is the interface **detected**? → `ifconfig`, network pane
2. Does a **route** exist? → `netstat -rn`
3. Does **name resolution** work independently? → `dig`, `nslookup`
4. Is the **recovery endpoint** reachable? → `curl` the recovery server
5. Only then retry the installer.

That sequence separated "boot configuration problem" from "network problem"
without rewriting EFI settings for a DNS issue. In the final machine, both
`RealtekRTL8111` (wired) and the MT7601 USB Wi-Fi work in Recovery.

---

## 3 · The black screen and UHD 620 — the main event

**Symptom:** black screen; `System Information → Graphics` showed
**Intel UHD 620 with only 7 MB of video memory**.

The device was *detected* but *not accelerated* — a framebuffer problem, not a
missing-kext problem. Debugging proceeded one layer at a time:

- platform/device properties (`DeviceProperties > Add`)
- framebuffer selection (`AAPL,ig-platform-id`)
- connector / display-path assumptions (the AIO panel!)
- diagnostic boot-args only
- WhateverGreen/Lilu compatibility
- log evidence at the point the display changed state

**The root cause:** this machine's iGPU reports PCI device-id **`0x5916`** —
Kaby Lake-**R** — but the config carried the plain Kaby Lake framebuffer
**`0x59120000`**. That mismatch leaves the panel's eDP connector off the active
connector list, so macOS initializes the GPU with a 7 MB stub framebuffer.

**The fix (three parts, all in the shipped config):**

| Change | In config | Effect |
|---|---|---|
| `AAPL,ig-platform-id = 0x59160000` | `DeviceProperties` | The KBL-R framebuffer whose connector map matches the panel. |
| `framebuffer-unifiedmem = 2048 MB` | `DeviceProperties` | Real VRAM allocation instead of the 7 MB stub. |
| `-igfxonln=1 -igfxfw=2 -igfxrps` | NVRAM boot-args | Force all connectors online; load Intel firmware; enable GPU RPS power states. |

After that change, acceleration initialized and UI behavior changed
immediately (smooth scrolling, hardware GL, proper resolution).

> **What if your panel still doesn't light up?** Add `-igfxdbg` for detailed
> connector logs and check the eDP index in the verbose output — on some panels
> a `framebuffer-patch` entry pinning the correct connector index is needed
> (see [docs/06](06-troubleshooting.md)).

---

## 4 · USB, camera and peripheral state — the hidden ports

Generic USB injection (`XhciPortLimit`) was used during discovery — it is a
debugging tool, not a finished configuration. The finished state is a real map:

- **USBToolBox** (runtime) + **UTBMap** (the generated map) replace the
  port-limit hack entirely.
- Every port's **connector type** was assigned: USB 2/3, internal, etc.

The AIO twist: **internal peripherals connect through the USB controller**.
The webcam, microphone and (if present) Bluetooth enumerate on USB ports that
look unused from the outside. A port that appears empty externally can still be
load-bearing internally — this is why `UTBMap.kext` keeps the internal ports
enabled and why the camera works.

**Regression order used:** core boot → graphics → USB → audio → sleep →
peripherals. Fixing everything at once would have made regressions impossible
to attribute.

---

## 5 · Audio, sleep and the HP RTC

- **Audio:** ALC3247 (ALC256 family) with AppleALC `layout-id 3` — tested on
  the internal speaker and the combo headphone jack.
- **Sleep:** tested only *after* the core path was stable (the debugging-order
  rule again). Report any regression in Issues with a full log.
- **HP RTC:** this family's firmware raises a **"005 — Real Time Clock Power
  Loss"** POST error when the RTC is touched the way macOS likes to. Fixed in
  three places: the ACPI `Fix HP Real-Time Clock Power Loss` patch,
  `Kernel > Quirks > DisableRtcChecksum`, and the `rtc-blacklist` NVRAM
  variable.

---

## 6 · What the final EFI does *not* contain

- ❌ no `-v` / `debug=0x100` / `-igfxvesa` — diagnostic scaffolding removed
- ❌ no `XhciPortLimit` — replaced by the real USB map
- ❌ no unused kexts, no disabled experiments
- ❌ no "macOS → hacOS" patch (present but disabled in `Booter > Patch`)

Every remaining value has a reason and a doc reference — the practical version
of "make every configuration change earn its place".

---

## The transferable lesson

The most useful part of this project has nothing to do with one operating
system: **complex failures become manageable when the system is decomposed into
layers, evidence is captured at each boundary, and changes are small enough to
explain.** Inventory the real environment, isolate the failing interface,
preserve recovery, and make every change earn its place. That method applies to
embedded devices, robotics, deployment pipelines and production systems.

---

Next: **[06-troubleshooting.md](06-troubleshooting.md)** · or back to the [README](../README.md)
