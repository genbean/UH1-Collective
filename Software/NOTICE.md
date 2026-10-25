# Notices

HeliSR (the firmware in `firmware/` and HeliSR Configurator in `configurator/`) is free software under the **GNU General Public License v3 or later**; see [LICENSE](LICENSE). It is a modified version of FreeJoy and is not made or supported by the FreeJoy team.

## Based on FreeJoy

- **FreeJoy firmware**, https://github.com/FreeJoy-Team/FreeJoy
  - Version 1.7.3b1, commit `fc697108124f9ffc4ca3f3b1c6bdb2f21f94d52d` (2026-04-19).
  - Copyright (C) 2020 Yury Vostrenkov and contributors. GPL-3.0.
- **FreeJoy Configurator (FreeJoyConfiguratorQt)**, https://github.com/FreeJoy-Team/FreeJoyConfiguratorQt
  - Commit `a3997defc781de3b2225408a4f1d32fb32d39e7d` (2026-02-27), for firmware 1.7.3.
  - Copyright Reksotiv and contributors (FreeJoy Team). GPL-3.0.

Thanks to the FreeJoy team for publishing their work under a free licence.

## Changes from FreeJoy

**2026-10-24**
- `configurator/`: a copy of FreeJoyConfiguratorQt at the commit above (adapted in phase 4, below).
- `firmware/`: new firmware for the ATmega32U4 Pro Micro on the HeliSR Rev 3.0 board, replacing FreeJoy's STM32F103 code.
  - **The settings layout** (`firmware/HeliSR/src/shared/helisr_config.h`) is derived from FreeJoy's `common_types.h`:
    - limits cut to the Pro Micro: 64 buttons, 11 spare pins, 9 analog sources;
    - sensor, RGB-LED and shift-register configuration removed;
    - a 3-position-switch centre button type added;
    - packed so the firmware and the configurator share one definition.
  - **The settings channel** (`firmware/HeliSR/src/protocol.cpp`, `shared/helisr_protocol.h`) is modelled on FreeJoy's `usb_endp.c`. It uses its own commands, a checksum on writes, and EEPROM storage.
  - **New code written for the Pro Micro:** USB, the board drivers, settings storage and the processing loop.

**2026-10-24 (phase 2)**
- `firmware/HeliSR/src/buttons.cpp`: ported from FreeJoy's `buttons.c`, `axis_to_buttons.c` and `encoders.c`.
- `firmware/HeliSR/src/axes.cpp`: ported from `analog.c`.
- `firmware/HeliSR/src/leds.cpp`: ported from `leds.c` and the PWM part of `periphery.c`.
- What changed in the port:
  - single-pass button processing, 16-bit timestamps, integer maths, and tables in flash;
  - sensors, matrices, fast encoders and RGB removed;
  - a `SWITCH_CENTER` button type added;
  - several FreeJoy bugs fixed (listed in each file's header).

**2026-10-24 (phase 3)**
- Behaviour brought in line with FreeJoy's after comparing against its original code: the processing order, unused axes, the offset wrap, sequential start-up, the prescaler and trim order, and FreeJoy's float resolution step.
- `HSR_FREEJOY_EXACT` (test builds only) restores FreeJoy's behaviour where HeliSR fixes its bugs: stuck delayed buttons, the lower trim limit, and the dead-band overflow.
- `firmware/test/host/`: a PC test program. `freejoy/fj_bridge.c` drives FreeJoy's original source files (taken from a FreeJoy checkout at build time, not copied into this project) for the comparison.

**2026-10-25 (phase 4): FreeJoyConfiguratorQt becomes HeliSR Configurator**
- Renamed (window, program `HeliSRConfigurator.exe`, project `HeliSRConfigurator.pro`, settings folder `Documents\HeliSR`), with a new icon. FreeJoy's logo files, screenshots and wiki links are removed; the About box credits FreeJoyConfiguratorQt.
- **Settings and protocol:** `common_types.h` and `common_defines.h` now include the firmware's `shared/helisr_config.h` and `helisr_protocol.h`, and the factory settings come from the new `shared/helisr_defaults.h` (the firmware's `settings_defaults()` moved there unchanged). `hiddevice.cpp` is rewritten for HeliSR's command/reply protocol (INFO, READ, WRITE + COMMIT with a checksum, PARAMS, BOOTLOADER); `reportconverter.*` and `stm_main.*` are removed.
- **Pages:** the Blue Pill / Controller Lite pin page (`widgets/pins/`) is replaced by a new Board page (`widgets/board/`, with an AS5600 programming helper). The shift-register page, RGB LEDs (`widgets/led_rgb/`, `widgets/color/`), host-controlled LEDs, the fast encoder and the I2C sensor options are removed. Buttons pick their input by name and gain the Switch center type; LEDs and PWM follow the spare pins; limits follow the firmware (64 buttons, 8 encoders, 11 LEDs). FreeJoy's shift-state indicators are fixed (shifts 2-5 never cleared), as is a read past the end of a 26-character device name.
- **Flashing:** the STM32 flasher (`firmwareupdater.*`, `flasher.ui`) is replaced by `avrflasher.*`, which uses the Pro Micro's bootloader and avrdude.
- **New:** profile files for HeliSR settings (`configtofile.cpp` rewritten), a command-line mode (`cli.cpp`) and a page round-trip test (`uitest.cpp`).

**2026-10-25 (phase 5)**
- FreeJoyConfiguratorQt's Inno Setup script moved to `packaging/HeliSRConfigurator.iss` and rewritten for HeliSR: its own AppId, per-user install, the bundled firmware and avrdude.
- `packaging/build-release.ps1` (new) builds the release; `packaging/licenses/LGPL-3.0.txt` is the FSF's text, unmodified.

## Third-party components

- **Arduino AVR core** (the firmware is built on it), https://github.com/arduino/ArduinoCore-avr. LGPL-2.1 or later. `usb_helisr.cpp` follows its HID library's descriptor handling.
- **Qt** (the configurator's GUI toolkit), https://www.qt.io. Used under the LGPL-3.0. The installer ships Qt's own DLLs, unmodified, with the LGPL text (`packaging/licenses/LGPL-3.0.txt`).
- **HIDAPI** (`configurator/src/*/hidapi.c`), Copyright 2009 Alan Ott, Signal 11 Software. Used under the GPL-3.0, one of its three licence options.
- **avrdude** (run by the configurator to flash the Pro Micro), https://github.com/avrdudes/avrdude. GPL-2.0 or later. The installer bundles the Arduino build 8.0.0-arduino1, unmodified, with its licence; it is a separate program, run as one. Its source is attached to each release (see `packaging/README.md`).
- **MinGW-w64 GCC runtime** (`libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libwinpthread-1.dll`, shipped by the installer). GPL-3.0 with the GCC Runtime Library Exception, and MIT/ZPL for winpthreads.

## Names

"FreeJoy" is the FreeJoy team's project name. This fork is called HeliSR so it isn't mistaken for an official FreeJoy release.
