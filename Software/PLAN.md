# Plan: a FreeJoy fork for the Pro Micro + HeliSR

Status: **draft for review, 2026-10-24.** Nothing has been built or downloaded yet.

## Goal

A general-purpose game-controller firmware and configuration app for **any Pro Micro on a HeliSR Rev 3.0 board**, in any collective, throttle, button box or panel. It isn't tied to the UH-1. Both are forked once from FreeJoy v1.7.3, published together in this project's GitHub repo under GPL-3, and never need FreeJoy's updates.

- Inputs keep the board's generic names: **IN1–IN16** and **AX1–AX4**.
- The UH-1 collective becomes just one example **profile file** that users can load.
- Out of the box, with no app: inputs 1–16 are buttons 1–16, and AX1–AX4 are axes.

## What the hardware can and can't do

**HeliSR Rev 3.0 + Pro Micro (ATmega32U4):**

| Resource | Available | Notes |
|---|---|---|
| Digital inputs | 16 (IN1–IN16, two 74HC165s) | 10 k pull-ups, switch to GND. The chain can't be extended (U1's SER is grounded). |
| Analog inputs | 4 (AX1–AX4 = A3–A0) | 10-bit ADC, oversampled to 12 bits. AX1 and AX4 have the PROG buttons for AS5600 one-time programming. |
| Spare Pro Micro pins | 11, **not broken out on the board** (TX, RX, 4, 5, 6, 7, 8, 9, 10, 14, 16) | Reachable only by soldering wires to the Pro Micro's pins. Five are analog-capable (4, 6, 8, 9, 10) and four do PWM (5, 6, 9, 10). See decision 2. |
| Flash / RAM / EEPROM | 28 KB / 2.5 KB / 1 KB | The real limits on the port (see Risks). |
| I²C, SPI | Not usable | I²C pins (2, 3) drive the shift registers. SCK (15) is their clock. |

**Firmware features (FreeJoy's, adapted):**
- **Buttons:** 64 logical buttons (FreeJoy has 128; the 32U4's RAM limits it). Each is fed by an input, an axis range or a shift.
  - Types: normal, inverted, latching toggle, toggle-switch pulse (on both edges, ON only, OFF only), radio buttons, sequential buttons.
  - POV hats: up to 4.
  - Encoders on any two inputs: hand-speed detented encoders, polled.
  - 5 shift layers, press and pulse timers, and adjustable debounce.
- **New in the fork:** a **3-position-switch centre** type, which is on while both of a switch's inputs are open. This gives every ON-OFF-ON toggle an OFF button. FreeJoy has no such type.
- **Axes:** 4 physical inputs to up to 8 HID axes (X, Y, Z, Rx, Ry, Rz, Slider 1, Slider 2). For each:
  - resolution;
  - manual or automatic calibration, with a centre;
  - 7 smoothing levels;
  - inversion;
  - centre and dynamic dead bands;
  - offset;
  - an 11-point curve;
  - combined-axis functions.
- **Axis → buttons:** up to 12 ranges per axis, for detents such as throttle cutoff or idle.
- **Buttons → axis:** for example trim from a hat, or a digital axis.
- **Device:**
  - a USB name set in the app;
  - a selectable USB product ID, so several boards can work on one PC;
  - settings kept in EEPROM, with a checksum and automatic defaults.

**Not possible on Rev 3.0** (left out of the app): matrices, more than 16 physical inputs, I²C or SPI sensors and ADCs (including digital AS5600 reading), and fast hardware encoders. LEDs, PWM and RGB are only possible on the spare pins (decision 2).

**Other Pro Micros:** the 3.3 V / 8 MHz Pro Micro gets its own .hex, which costs little. The RP2040 Pro Micro is a different chip and is out of scope, but the firmware's hardware layer is kept separate so a port stays possible.

## How it fits together

- **One shared settings definition** (`shared/config.h`) is compiled into both the firmware and the app. Compile-time checks on its size and field positions, for both the AVR and the PC, stop the two from ever disagreeing.
- **USB:**
  - A custom Arduino plug-in USB module provides the joystick, plus a settings channel with its own IN and OUT endpoints. The Arduino core's HID library ignores data sent to the device, so it can't be used for the settings channel.
  - The same module answers the device and string descriptor requests, so the name and product ID come from EEPROM without patching the Arduino core. This was checked in core 1.8.8.
- **Flashing from the app:**
  - the app sends "enter bootloader" over USB;
  - the firmware jumps to the Pro Micro's bootloader;
  - the app runs a bundled avrdude.

  Users never need the Arduino IDE. A brand-new Pro Micro still flashes the normal way, or with a double tap on RST.
- **Build:**
  - Firmware: arduino-cli, already on this PC.
  - App: Qt 5.15 or later with MinGW, not on this PC.
  - Installer: Inno Setup 6, already installed, and the configurator already ships a script for it.
  - A GitHub Actions workflow can rebuild everything on each release tag once the repo is public.

## Phases

0. **Set up the fork.**
   - Copy FreeJoy (firmware, local download) and FreeJoyConfiguratorQt (commit a3997de) into `Software/`, with the source commits recorded.
   - Rename the fork.
   - Add the GPL-3 license, a NOTICE crediting the FreeJoy team and listing changes, and third-party notices (Qt LGPL, hidapi, avrdude GPL-2+, Arduino core LGPL).
1. **Firmware foundation, measured first.** This is the go/no-go check for the 28 KB / 2.5 KB budget, before porting the features:
   - the USB module (joystick, settings channel, runtime name and PID, bootloader jump);
   - the shift-register and ADC drivers;
   - EEPROM settings storage.
2. **Port the features:** buttons (all types, shifts, timers, hats, encoders), axis processing, axis→buttons, buttons→axis, and the new centre type.
3. **Test the logic on the PC.** Build the button and axis code as a desktop program, then run scripted input sequences through it and check the outputs. This catches most bugs before any hardware exists.
4. **Configurator fork.**
   - Rebrand it, and make it detect our device.
   - Switch it to the shared settings header.
   - Replace the Blue Pill pin page with a **HeliSR board page** (IN1–16, AX1–4, plus spare pins if chosen).
   - Remove the STM32-only pages (sensors, external ADCs, RGB, shift-register setup), and add the centre type.
   - Add an **AS5600 helper** for PROG1 and PROG4, with a live reading to confirm the burn.
   - Add the flasher, and profile save and load.
   - Keep English. The existing German, Russian and Chinese translations are kept where the text didn't change.
5. **Build and package:** the app, windeployqt, an Inno Setup installer with avrdude bundled, both .hex files, and an optional GitHub Actions workflow.
6. **Test on hardware once the boards are built:**
   - every input, axis and button type;
   - settings surviving a power cycle;
   - flashing from the app;
   - two boards on one PC;
   - the Windows device name.
7. **Documentation for strangers:**
   - quick start, flashing and the AS5600 guide;
   - profile examples, including the UH-1 collective;
   - licences.

   Also decide whether the simple `HeliCollective` sketch is retired or kept as a minimal option.

## Risks

- **Memory.** FreeJoy's full settings block is 1,170 bytes, more than the 1 KB EEPROM, and its button state alone would take a quarter of the RAM. The fork cuts this to 64 logical buttons and 4 physical axes. Phase 1 measures the budget before the bulk of the work. Features that don't fit get cut and documented, not squeezed in fragilely.
- **The app's structure.** FreeJoy's app decides what to show from its pin page, so replacing that page touches the other pages. This is the largest part of phase 4.
- **USB IDs.** Arduino's own vendor ID shouldn't be used for a published device. pid.codes gives free product IDs to open-source hardware. **You** apply once the repo is public; until then the firmware uses SparkFun's Pro Micro IDs.
- **Windows name caching.** Windows remembers a device's name by vendor and product ID, which is one reason the product ID is selectable.
- **No hardware yet.** Phases 1–5 are checked by compiling and by the PC tests; the real verification is phase 6.

## Decisions (2026-10-24)

1. **Name: HeliSR.** The app is "HeliSR Configurator", and the firmware and default USB name are "HeliSR". Users can rename the device in the app.
2. **Spare Pro Micro pins: yes, if they fit.** That means direct buttons, extra analog axes, and LEDs / PWM backlight, with a Pro Micro pin page in the app. If phase 1 shows the flash is too tight, they're dropped and the docs say so.
3. **Qt download: approved.** At phase 4, install official Qt + MinGW binaries with aqtinstall (no Qt account needed), into a folder outside the project.
