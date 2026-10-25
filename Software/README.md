# HeliSR software

Firmware and a configuration app for a **Pro Micro (ATmega32U4) on a HeliSR Rev 3.0 board**. They work in any collective, throttle, button box or panel. This is a fork of [FreeJoy](https://github.com/FreeJoy-Team/FreeJoy), licensed under the GPL-3; see [NOTICE.md](NOTICE.md).

**Status: under construction.** Phases 0-3 of [PLAN.md](PLAN.md) are done. The firmware has FreeJoy's button, axis, encoder and LED features. Its logic is tested on the PC, matches FreeJoy's own code exactly on random settings, and gives identical results on a Pro Micro. It hasn't been tested on a HeliSR board yet, and the configurator isn't adapted yet.

| Folder | What's in it |
|---|---|
| `firmware/HeliSR/` | The firmware, an Arduino sketch |
| `firmware/HeliSR/src/shared/` | The settings layout and USB protocol, shared with the configurator |
| `firmware/build.ps1` | Builds the firmware (see below) |
| `firmware/test/` | Development test tools for a Pro Micro: the settings channel and joystick (`hsr-usb-test.ps1`), flashing through the bootloader command (`hsr-flash-via-bootloader.ps1`), a logic test (`hsr-logic-test.ps1`), and the lockstep replay of the PC tests (`hsr-lockstep.ps1`, needs `build.ps1 -Test`). Shared helpers are in `hsr-usb-lib.ps1`. |
| `firmware/test/host/` | The PC tests: the firmware's logic compiled for the PC, the scenario tests, and the comparison with FreeJoy's own code (`run-host-tests.ps1`) |
| `configurator/` | HeliSR Configurator, forked from FreeJoyConfiguratorQt (not modified yet) |

## Building the firmware

You need the Arduino IDE 2.x, with "Arduino AVR Boards" installed (it comes with the IDE). Then, in PowerShell:

```powershell
cd Software\firmware
.\build.ps1             # 5 V / 16 MHz Pro Micro
.\build.ps1 -Mhz8       # 3.3 V / 8 MHz Pro Micro
.\build.ps1 -Serial     # also include the Arduino USB serial port (for development)
```

The `.hex` files land in `firmware\build\<variant>\`.

## What the board reports with no settings

- IN1–IN16 are buttons 1–16.
- AX1, AX2, AX3 and AX4 are the X, Y, Z and Rx axes.
- The device is called "HeliSR".

## Testing

On the PC (needs MinGW-w64 g++, for example Qt's: `aqt install-tool windows desktop tools_mingw1310 qt.tools.win64_mingw1310`):

```powershell
cd Software\firmware\test\host
.\run-host-tests.ps1                               # scenario tests of the firmware's logic
.\run-host-tests.ps1 -FreeJoy <FreeJoy checkout>   # also compare with FreeJoy's own code
```

On a Pro Micro, the same scenarios in lockstep with the PC:

```powershell
cd Software\firmware
.\build.ps1 -Test                                  # then flash build\noserial-test\HeliSR.ino.hex
cd test
.\host\run-host-tests.ps1 -Trace host\build\trace.txt -Random 10
.\hsr-lockstep.ps1 -Trace host\build\trace.txt
```

Flash the normal build afterwards: the test firmware ignores the board's inputs once a lockstep run has started.
