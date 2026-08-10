# 07 · SMBIOS & iCloud — the 60-second guide

## Why you must generate your own

`PlatformInfo > Generic` in the shipped `config.plist` contains the values used
to build and test this machine. They are **not** meant to be shared:

- If the serial belongs to a real Mac, using it can lock out that owner's
  Apple-ID / iMessage.
- If everyone copies it, Apple's servers see one serial logging in from many
  places → services break for all of them.
- Apple may flag the account for fraud. This is the single most common cause
  of "iMessage won't activate" in the whole Hackintosh community.

**Rule: install, then regenerate, then (optionally) wipe the original.**

## Do it in 60 seconds

You need [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) (Python + Windows).

```powershell
python GenSMBIOS.command
# option 1 → Generate SMBIOS → type: MacBookPro15,2
```

Output (example):
```
MLB:    C02XXXXXXXXXJXXXX
Serial: C02XXXXXXXXX
SmUUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

Edit `EFI/OC/config.plist` (ProperTree) under `PlatformInfo → Generic`:

| Key | Set to |
|---|---|
| `SystemProductName` | `MacBookPro15,2` (unchanged) |
| `MLB` | your MLB |
| `SystemSerialNumber` | your Serial |
| `SystemUUID` | your SmUUID |
| `ROM` | `00:00:00:00:00:00` (auto-derived) or your LAN MAC |

Save, reboot, done. New identity applies from the next boot.

> Prefer to start clean? `python scripts/scrub_smbios.py` writes a copy of the
> config with all SMBIOS fields replaced by placeholders, so no original value
> leaks into a screenshot, a PR or a pastebin.

## Verify

```
system_profiler SPHardwareDataType | grep -i "serial\|model"
```

You should see **your** serial and `MacBookPro15,2`. If you see the repo's
serial, you forgot a step.

## iMessage / FaceTime checklist

1. Fresh SMBIOS (above), **unique** — never a value you've seen in a guide.
2. `csr-active-config` — leave at the shipped value unless you know why.
3. Signed in with a valid Apple-ID, network up.
4. If activation fails immediately after a change: sign out of iMessage on all
   devices, reboot, sign back in.
5. Don't call Apple support about it. 😄

## What the CI checks

`.github/workflows/validate.yml` validates the config structure on every push.
It **warns** when the SMBIOS looks like a real (non-placeholder) value — the
intent is to keep real serials out of the public history.

---

Back to the [README](../README.md)
