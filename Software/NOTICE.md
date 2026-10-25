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
- `configurator/`: a copy of FreeJoyConfiguratorQt at the commit above. It has not been modified yet.
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

## Third-party components

- **Arduino AVR core** (the firmware is built on it), https://github.com/arduino/ArduinoCore-avr. LGPL-2.1 or later. `usb_helisr.cpp` follows its HID library's descriptor handling.
- **Qt** (the configurator's GUI toolkit), https://www.qt.io. Used under the LGPL-3.0. Installers ship Qt's own DLLs, unmodified, with Qt's licence.
- **HIDAPI** (`configurator/src/*/hidapi.c`), Copyright 2009 Alan Ott, Signal 11 Software. Used under the GPL-3.0, one of its three licence options.
- **`configurator/src/widgets/color/colorcells.cpp`**, Copyright (C) 2016 The Qt Company Ltd. LGPL-3.0 or GPL-2.0+/GPL-3.0.
- **avrdude** (to be bundled with the configurator for flashing), https://github.com/avrdudes/avrdude. GPL-2.0 or later. It is shipped as a separate program.

## Names

"FreeJoy" is the FreeJoy team's project name. This fork is called HeliSR so it isn't mistaken for an official FreeJoy release.
