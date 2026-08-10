# 02 · Installation

> ⚠️ **Read [07-smbios-icloud.md](07-smbios-icloud.md) first.** You must not
> install with this repo's SMBIOS values — generate your own.

## What you need

| Item | Notes |
|---|---|
| HP 200 G3 AIO | obviously 🙂 |
| USB stick, **8 GB+** | will be wiped |
| macOS Sequoia installer | via [gibMacOS](https://github.com/corpnewt/gibMacOS) (recommended) or a Mac |
| A second computer (Windows/macOS/Linux) | to create the USB stick |
| [ProperTree](https://github.com/corpnewt/ProperTree) | plist editor |
| [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) | SMBIOS generation |
| This repo | `EFI/` folder |

## Step 1 — BIOS settings (HP 200 G3)

Boot the machine, press **F10** to enter BIOS Setup.

1. **Security → Secure Boot Configuration → Legacy Support Enable and Secure Boot Disable**
   (or just disable Secure Boot if present).
2. **Advanced → Boot Options → UEFI Boot Order** — make sure UEFI USB is listed
   and UEFI mode is active (not Legacy/CSM).
3. **Advanced → Port Options** — keep **USB** and **XHCI** enabled.
4. Check **Advanced → Power Management** — nothing required, but note the HP
   "005 RTC" error is handled by the EFI itself (see [docs/01](01-hardware.md)).
5. **Save and Exit.**

> If the machine previously ran Windows, you may also want to disable
> **Fast Boot** / **Windows 10 Fast Startup** (BIOS level) and fully shut down
> before switching operating systems.

## Step 2 — Create the installer USB

**On Windows (recommended path):**

1. Use [gibMacOS](https://github.com/corpnewt/gibMacOS) to download the Sequoia
   **Recovery** (recommended — small) or full installer:
   ```powershell
   python gibMacOS.command
   # option 1: download a build, then option "Full Installer" if desired
   ```
2. Format the USB stick (FAT32, GUID partition map) — easiest with
   [Rufus](https://rufus.ie) or diskpart.
3. Restore the recovery image to the stick (gibMacOS has a built-in
   `MakeInstall.py` / `BuildmacOSInstallApp.command` flow, or use
   [macrecovery](https://github.com/acidanthera/OpenCorePkg/tree/master/Utilities/macrecovery)
   output written to the stick).

**On a Mac:**

```bash
# download Sequoia installer from the App Store, then:
sudo /Applications/Install\ macOS\ Sequoia.app/Contents/Resources/createinstallmedia --volume /Volumes/USB --nointeraction
```

## Step 3 — Generate SMBIOS (mandatory)

```powershell
python GenSMBIOS.command
# option 1: Generate SMBIOS
# type "MacBookPro15,2"
```

You get three lines: `MLB`, `Serial`, `SystemUUID`. Open
`EFI/OC/config.plist` in ProperTree and edit:

```
PlatformInfo → Generic →
    SystemProductName     = MacBookPro15,2   (keep)
    MLB                   = <your MLB>
    SystemSerialNumber    = <your Serial>
    SystemUUID            = <your UUID>
    ROM                   = <leave, or your LAN MAC>
```

> Prefer a blank config? Run `scripts/scrub_smbios.py` first, then fill in
> your values. See [docs/07](07-smbios-icloud.md) for the full rationale.

## Step 4 — Copy the EFI

1. Mount the USB's EFI partition (on Windows: `mountvol` / DiskGenius; on macOS:
   `diskutil mount EFI` — the stick is FAT32 so just open it).
2. Copy this repository's **`EFI/`** folder to the root of the USB's EFI
   partition. Result:

   ```
   <USB EFI>/EFI/BOOT/BOOTx64.efi
   <USB EFI>/EFI/OC/...
   ```

3. Eject the stick safely.

## Step 5 — Install

1. Plug the stick into the AIO, power on, press **F9** → choose the USB drive.
2. OpenCore picker appears → choose **macOS Installer** (or the recovery entry).
3. If the picker shows an APFS volume instead, use **Reset NVRAM** first.
4. Use **Disk Utility** during install to format the internal disk as **APFS**
   (GUID scheme).
5. Install. The machine reboots several times — keep the USB in until the
   installer announces the disk as bootable.

## Step 6 — Post-install

1. Boot **from the internal disk** through the USB picker, then after you reach
   the desktop:
   - Mount the internal EFI partition and copy the `EFI/` folder there so the
     machine boots without the USB.
   - Optional: enable OpenCore as a boot option in the BIOS/UEFI menu.
2. Sanity check with the repo scripts:
   ```powershell
   python scripts/validate_efi.py EFI/OC/config.plist
   ```
3. Sign in to iMessage/FaceTime — see [docs/07](07-smbios-icloud.md) for the
   "it works only with a fresh SMBIOS" rule.
4. Enable **recovery boot** check — see [docs/06](06-troubleshooting.md)
   (Recovery needs the network; the Ethernet or the Wi-Fi dongle both work).

## Keeping the EFI up to date

Do **not** blindly replace the whole folder with a new OpenCore release.
Follow [docs/04-kexts-drivers.md](04-kexts-drivers.md): update the components,
keep the config, re-validate.

---

Next: **[03-configuration.md](03-configuration.md)** · or back to the [README](../README.md)
