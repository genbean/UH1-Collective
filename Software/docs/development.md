# Development

How the HeliSR software is put together, built and tested. [`PLAN.md`](../PLAN.md) has the design decisions and what each phase found; [`NOTICE.md`](../NOTICE.md) lists the changes from FreeJoy.

## Folders

| Folder | What's in it |
|---|---|
| `firmware/HeliSR/` | The firmware, an Arduino sketch |
| `firmware/HeliSR/src/shared/` | The settings layout (`helisr_config.h`), factory settings (`helisr_defaults.h`) and USB protocol (`helisr_protocol.h`), compiled into both the firmware and the configurator |
| `firmware/build.ps1` | Builds the firmware |
| `firmware/test/` | Test tools for a Pro Micro: the settings channel and joystick (`hsr-usb-test.ps1`), flashing through the bootloader command (`hsr-flash-via-bootloader.ps1`), a logic test (`hsr-logic-test.ps1`), and the lockstep replay of the PC tests (`hsr-lockstep.ps1`). Shared helpers are in `hsr-usb-lib.ps1` |
| `firmware/test/host/` | The PC tests: the firmware's logic compiled for the PC, the scenario tests, and the comparison with FreeJoy's own code |
| `configurator/` | HeliSR Configurator, forked from FreeJoyConfiguratorQt. See [its README](../configurator/README.md) |
| `profiles/` | The example profiles and the script that makes them |
| `packaging/` | The release build, installer script and release checklist. See [its README](../packaging/README.md) |
| `docs/` | These pages |

## Building the firmware

You need the Arduino IDE 2.x, with "Arduino AVR Boards" installed (it comes with the IDE). Then, in PowerShell:

```powershell
cd Software\firmware
.\build.ps1             # the release build: 5 V / 16 MHz Pro Micro, no USB serial port
.\build.ps1 -Serial     # with the Arduino USB serial port, so the Arduino IDE can upload without a double tap
.\build.ps1 -Port COM5  # build and upload
```

The `.hex` lands in `firmware\build\<variant>\HeliSR.ino.hex`. Only the 5 V / 16 MHz Pro Micro is supported.

The build uses the Arduino IDE's own `arduino-cli` and the Arduino AVR core 1.8.8 (`arduino:avr:leonardo`). The firmware registers its own USB functions (a joystick and a settings channel) through the core's PluggableUSB, so the core itself is unmodified.

## Building the configurator

Qt 6 with MinGW, then `qmake` and `mingw32-make`: see [configurator/README.md](../configurator/README.md#building).

## Building a release

`packaging\build-release.ps1` builds the firmware and the configurator, and packs them with Qt, avrdude, the example profiles and the licences into `HeliSR-Configurator-x.y.z-Setup.exe` and a portable zip. See [packaging/README.md](../packaging/README.md), which also has the release checklist.

## How the app and the firmware talk

The board is a USB composite device: a joystick that games read, and a vendor-defined HID collection (usage page 0xFF00) that only the configurator uses. Each settings packet is 64 bytes: report ID, command, index, status and 60 bytes of data, and the board answers every command. INFO comes first; the app refuses a board whose protocol version, settings version or settings size differs from its own. Settings go over in 60-byte chunks (READ / WRITE), then COMMIT with a CRC-16; the board saves them to EEPROM and restarts so Windows sees the new name and layout. `helisr_protocol.h` has the details.

## Testing

**Firmware logic on the PC** (needs MinGW-w64 g++, for example Qt's: `aqt install-tool windows desktop tools_mingw1310 qt.tools.win64_mingw1310`):

```powershell
cd Software\firmware\test\host
.\run-host-tests.ps1                               # 192 scenario checks of the firmware's logic
.\run-host-tests.ps1 -FreeJoy <FreeJoy checkout>   # also compare with FreeJoy's own code on random settings
```

**The same scenarios on a Pro Micro**, in lockstep with the PC:

```powershell
cd Software\firmware
.\build.ps1 -Test                                  # then flash build\noserial-test\HeliSR.ino.hex
cd test
.\host\run-host-tests.ps1 -Trace host\build\trace.txt -Random 10
.\hsr-lockstep.ps1 -Trace host\build\trace.txt
```

Flash the normal build afterwards: the test firmware ignores the board's inputs once a lockstep run has started.

**The configurator:**

```
HeliSRConfigurator --ui-test 200                  random settings through every page and back (no board needed)
HeliSRConfigurator --ui-test-file a.cfg b.cfg     profiles through every page and back
HeliSRConfigurator --roundtrip                    write, read back and compare, then restore (needs a board)
HeliSRConfigurator --ui-device-test               the same through the window's Write and Read buttons
```

Run them after any change to the configurator or the shared headers.

## Example profiles

```powershell
cd Software\profiles
python make_profiles.py
```

It starts from `Default (16 buttons, 4 axes).cfg`. If the firmware's factory settings change, remake that first with `HeliSRConfigurator --save-defaults "Default (16 buttons, 4 axes).cfg"`.
