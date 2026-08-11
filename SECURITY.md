# Security Policy

## Supported Versions

Only the latest commit on the `main` branch is actively supported. Security
fixes are backported to the latest tagged release when one exists.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately through GitHub's Private Vulnerability Reporting:

<https://github.com/vishnuskandha/HP-200-G3-AIO-OpenCore/security/advisories/new>

When reporting, please include:

- The affected component and commit/version
- A description of the vulnerability and its impact
- Steps to reproduce, if possible
- Any suggested remediation, if you have one

You should receive an acknowledgement within 5 business days, and a status
update (accepted, mitigated, or declined) once the report has been triaged.

## Security Notes

- **SMBIOS / identifiers:** the committed `EFI/OC/config.plist` contains this
  machine's SMBIOS values. If you plan to redistribute or share this EFI,
  regenerate your own SMBIOS with GenSMBIOS (see
  [docs/07-smbios-icloud.md](docs/07-smbios-icloud.md)) or strip it with
  [scripts/scrub_smbios.py](scripts/scrub_smbios.py). Never commit real serial
  numbers, MLB values, or UUIDs — CI warns when they look real.
- **macOS licensing:** macOS is Apple-licensed software intended for Apple
  hardware. This repository is not affiliated with Apple; ensure you comply
  with Apple's software license agreement.
- **Untested changes:** this EFI is a working, boot-tested configuration.
  Untested bootloader or SSDT changes can prevent booting; validate changes on
  equivalent hardware before shipping.
- The CI workflow runs `scripts/validate_efi.py` and confirms the working tree
  is untouched after validation.
