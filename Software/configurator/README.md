# HeliSR Configurator

The setup app for the HeliSR firmware: a Pro Micro (ATmega32U4) on a HeliSR Rev 3.0 or Rev 4.0 board, used in any collective, throttle, button box or panel. It is a fork of [FreeJoyConfiguratorQt](https://github.com/FreeJoy-Team/FreeJoyConfiguratorQt) by the FreeJoy team, licensed under the GPL-3; see [../NOTICE.md](../NOTICE.md). It only talks to HeliSR firmware, not to FreeJoy devices.

## Pages

| Page | What it sets |
|---|---|
| **Board** | Which board (it follows the connected one), its fixed inputs (IN1–IN16 and AX1–AX4, with live AX readings; on Rev 4.0 each AS5600's state, and A2/A3), what each spare Pro Micro pin does (button, analog axis, LED, PWM), a summary of the setup, and the AS5600 helper: PROG1/PROG4 programming on Rev 3.0, start/stop and I²C clock over I²C on Rev 4.0 |
| **Button Config** | 64 logical buttons, each fed by a physical input chosen by name (IN5, Pin TX, X range 2 ...). FreeJoy's button types, plus **Switch center** (on while an input and the next one are both off). 5 shift layers, timers, debounce |
| **Axes Config** | 8 axes (X–Slider 2) from AX1–AX4, analog spare pins, or an encoder; calibration, filtering, dead band, functions, axis-to-button ranges |
| **Axes Curves** | 11-point curves |
| **Encoders** | 8 encoders on button inputs, 1x/2x/4x |
| **LED/PWM** | On/off LEDs on spare pins, following a logical button; PWM on pins 5, 6, 9, 10, fixed or following an axis |
| **Advanced Settings** | USB name, VID/PID and report rate; **firmware flashing** (the connected board over USB, or a Pro Micro without HeliSR firmware); language and theme |

Profiles (`.cfg`) save a whole setup to a file, in `Documents\HeliSR\configs` by default. The app copies the example profiles from `profiles\` next to it into `Documents\HeliSR\configs\examples`. The user documentation is in [`../docs`](../docs).

## Flashing

The app restarts a HeliSR board into the Pro Micro's bootloader over USB, finds the bootloader's serial port and runs **avrdude**. A Pro Micro without HeliSR firmware gets a 1200-baud "touch" on its serial port (an Arduino sketch's port), or you double-tap its RST pin when asked.

avrdude is looked for in `avrdude\` next to the app (the installer puts it there), then in the Arduino IDE's packages, then on the PATH. The release firmware is looked for in `firmware\HeliSR_Rev3.0_16MHz.hex` and `firmware\HeliSR_Rev4.0_16MHz.hex` next to the app; any other `.hex` can be picked by hand. Before flashing, the app reads the board tag in the `.hex` (`firmwarefile.cpp`) and asks before anything that could put Rev 4.0 firmware on a Rev 3.0 board.

## Command line

The same program also runs without its window:

```
HeliSRConfigurator --info                       firmware, settings version, board health
HeliSRConfigurator --read  my-setup.cfg         save the board's settings to a profile
HeliSRConfigurator --write my-setup.cfg         write a profile to the board
HeliSRConfigurator --write-defaults             factory settings
HeliSRConfigurator --params 5                   live readings for 5 seconds
HeliSRConfigurator --flash HeliSR_Rev3.0_16MHz.hex     update the connected board's firmware
HeliSRConfigurator --flash-new HeliSR_Rev3.0_16MHz.hex [--port COM5]   a Pro Micro without HeliSR firmware
HeliSRConfigurator --hex-info HeliSR_Rev4.0_16MHz.hex  which board a firmware file is for
HeliSRConfigurator --sensors 5                  Rev 4.0: the AS5600s' state and angles
HeliSRConfigurator --save-defaults new.cfg      the factory settings as a profile (no board needed)
```

`--flash` and `--flash-new` refuse a file that may not suit the board; `--board 3.0` or `--board 4.0` says which board the Pro Micro is on.

Add `--device 2` to pick the second of several boards. Development tests:

```
HeliSRConfigurator --roundtrip                  write, read back and compare, then restore (needs a board)
HeliSRConfigurator --ui-test 200 [--seed n] [--board 4.0]   random settings through every page and back
HeliSRConfigurator --ui-test-file a.cfg b.cfg   profiles through every page and back
HeliSRConfigurator --ui-device-test             the window's Write and Read buttons with a board
HeliSRConfigurator --sensor-roundtrip           Rev 4.0: the AS5600 settings saved, read back, kept through a restart, restored
HeliSRConfigurator --ui-screenshot board.png [--board 4.0]   a picture of the Board page
```

## Building

Windows, with Qt 6 and MinGW (Qt 5.15 should also work). The project was built with Qt 6.8.3 `win64_mingw` and MinGW 13.1, installed with [aqtinstall](https://github.com/miurahr/aqtinstall), no Qt account needed:

```
pip install aqtinstall
aqt install-qt windows desktop 6.8.3 win64_mingw -O C:\Qt
aqt install-tool windows desktop tools_mingw1310 qt.tools.win64_mingw1310 -O C:\Qt
```

Then, with `C:\Qt\6.8.3\mingw_64\bin` and `C:\Qt\Tools\mingw1310_64\bin` on the PATH:

```
cd Software\configurator
mkdir build
cd build
qmake ..\HeliSRConfigurator.pro CONFIG+=release
mingw32-make -j8
```

The program is `build\src\release\HeliSRConfigurator.exe`. The settings layout and USB protocol come straight from the firmware's `firmware/HeliSR/src/shared/` headers, so the app and the firmware always agree. To run it from the build folder, keep Qt's `bin` on the PATH; for the installer and portable zip (Qt, avrdude and the firmware bundled), see [../packaging/README.md](../packaging/README.md).

The Linux and macOS code paths from FreeJoyConfiguratorQt are kept, but only Windows has been built and tested.
