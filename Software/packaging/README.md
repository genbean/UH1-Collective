# Packaging

Builds a HeliSR release for Windows: an installer and a portable zip, each with HeliSR Configurator, Qt, avrdude, the firmware and the licences.

| File | What it is |
|---|---|
| `build-release.ps1` | Builds everything below into `output\` (working files in `work\`; both folders are git-ignored) |
| `HeliSRConfigurator.iss` | The Inno Setup script (based on FreeJoyConfiguratorQt's) |
| `README.txt` | The quick start that ships next to the app |
| `THIRD-PARTY-NOTICES.txt` | Licences and sources of everything in the package |
| `licenses\LGPL-3.0.txt` | Qt's licence (the other licence files are copied from the repo, avrdude and MinGW at build time) |

## Building

Needs the Arduino IDE 2.x (for the firmware), Qt 6 with MinGW (see `..\configurator\README.md`) and [Inno Setup 6](https://jrsoftware.org/isinfo.php). Then:

```powershell
cd Software\packaging
.\build-release.ps1
```

It takes under a minute and produces, for version *x.y.z* (from `configurator\src\version.h`):

- `HeliSR-Configurator-x.y.z-Setup.exe`: per-user install, no admin rights needed (an admin can choose all users), Start-menu entry, uninstaller;
- `HeliSR-Configurator-x.y.z-portable.zip`: the same files, run from any folder;
- `HeliSR-Configurator-x.y.z-SHA256SUMS.txt`.

Options: `-QtDir`, `-MinGWDir`, `-AvrdudeDir` and `-InnoDir` if the tools aren't in their usual places; `-SkipFirmware` reuses the last firmware build; `-SkipInstaller` makes only the zip.

What goes in:

| Part | From |
|---|---|
| `HeliSRConfigurator.exe` | a clean release build of `..\configurator` |
| Qt DLLs and plugins, MinGW runtime | `windeployqt` (no translations, no software OpenGL, no network plugins) |
| `firmware\HeliSR_16MHz.hex` | `..\firmware\build.ps1` (5 V / 16 MHz Pro Micro, no USB serial port) |
| `avrdude\` | the Arduino IDE's avrdude (8.0.0-arduino1): one exe needing only Windows' own DLLs, its config and licence |
| `profiles\` | the example profiles from `..\profiles` (the app copies them to `Documents\HeliSR\configs\examples`) |
| `licenses\`, notices, `README.txt`, `NOTICE.md` | this folder and the repo |

The app looks for the firmware and avrdude at exactly these paths next to itself.

## Release checklist

1. **Versions.** `configurator\src\version.h` (the app); `HSR_FIRMWARE_VERSION` in `firmware\HeliSR\src\shared\helisr_config.h` (the firmware); `HSR_CONFIG_VERSION` there too whenever the settings layout or the defaults change; `HSR_PROTOCOL_VERSION` in `helisr_protocol.h` whenever the USB commands change.
2. **Tests.** `firmware\test\host\run-host-tests.ps1`; `HeliSRConfigurator --ui-test 200` and `--ui-test-file` on the example profiles; with a board connected, `--roundtrip` and `--ui-device-test`. If the factory settings changed, remake the example profiles (see `..\docs\development.md`).
3. **Build.** `.\build-release.ps1`.
4. **Try the installer**, from PowerShell, with a board connected:
   ```powershell
   $d = "$env:TEMP\hsr-install"
   Start-Process output\HeliSR-Configurator-x.y.z-Setup.exe '/VERYSILENT', '/CURRENTUSER', "/DIR=`"$d`"" -Wait
   $env:PATH = 'C:\Windows\System32;C:\Windows'      # no Qt or MinGW on the PATH
   & "$d\HeliSRConfigurator.exe" --info | Out-Host
   & "$d\HeliSRConfigurator.exe" --flash "$d\firmware\HeliSR_16MHz.hex" | Out-Host
   Start-Process "$d\unins000.exe" '/VERYSILENT' -Wait
   ```
5. **GitHub release.** Tag `vX.Y.Z`, then attach:
   - the installer, the zip and the SHA256SUMS file;
   - `work\stage\firmware\HeliSR_16MHz.hex`, for people who flash with other tools;
   - **avrdude's source**, which its GPL-2 licence requires next to the binary: avrdude v8.0 (`https://github.com/avrdudes/avrdude/archive/refs/tags/v8.0.zip`) and the Arduino build scripts (`https://github.com/arduino/avrdude-packing`, release 8.0.0-arduino1). If a different avrdude is bundled, attach that version's source instead.

The installer isn't code-signed, so Windows SmartScreen shows "Windows protected your PC" the first time; **More info → Run anyway** continues. The release notes and the user guide should say so.
