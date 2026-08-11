# Contributing to HP 200 G3 AIO OpenCore

Thanks for your interest! Bug reports, documentation, framebuffer tweaks,
kext/driver updates, and hardware reports are all welcome.

## Important: this is a real machine's EFI

The `EFI/` directory is a working OpenCore package that boots a real machine.
`config.plist` and the SSDTs are tuned to this specific HP 200 G3 All-in-One.

- **Do not blindly merge EFI changes** that you cannot boot-test on equivalent
  hardware. Untested bootloader changes can brick a hackintosh.
- Always describe the hardware context (CPU, iGPU, board) in your PR.
- Run the validator before opening a PR:

  ```bash
  python3 scripts/validate_efi.py EFI/OC/config.plist --strict
  ```

  The same check runs in CI (`.github/workflows/validate.yml`) on every push
  and pull request that touches `EFI/**` or `scripts/**`.

## Privacy: SMBIOS values

The committed `config.plist` contains this machine's SMBIOS values. They are
used to boot the author's hardware.

- **Never commit a real serial number, MLB, or UUID.** CI warns when values
  look real.
- Before sharing screenshots or a config, regenerate your own SMBIOS with
  GenSMBIOS (see [docs/07-smbios-icloud.md](docs/07-smbios-icloud.md)) or scrub
  with [scripts/scrub_smbios.py](scripts/scrub_smbios.py).
- The repository must stay distributable, so placeholder SMBIOS is preferred in
  any commit that would otherwise add real identifiers.

## Workflow

1. Read the docs first — especially `03-configuration.md` and `04-kexts-drivers.md`.
2. Create a branch: `git checkout -b fix/your-change`.
3. Make your change and add a note in the relevant doc if behavior changes.
4. Run the validator and keep it green.
5. Open a pull request and explain what changed, on what hardware, and how it
   was tested (verbose log, `ioreg`, OpenCore version).

## Reporting bugs

Use the issue template in `.github/ISSUE_TEMPLATE/bug_report.yml`. Helpful
reports include:

- OpenCore version and build (`opencore-version.efi` output)
- Verbose boot log (`-v` boot-arg)
- `ioreg` output for the affected device
- What you changed since the last working state

## Security issues

Do **not** report security issues in public issues. See
[SECURITY.md](SECURITY.md) for the private reporting process.

## License

Repository content (docs, config, scripts) is MIT — see [LICENSE](LICENSE).
Redistributed OpenCore components (kexts, drivers, tools) remain under their
own licenses; do not remove their license/version metadata when updating.
