# Plan: a FreeJoy fork for the Pro Micro + HeliSR

Status, 2026-10-25: **phases 0-5 and 7 are done**; phase 6 waits for the built boards. See [Phase 1 results](#phase-1-results), [Phase 2 results](#phase-2-results), [Phase 3 results](#phase-3-results), [Phase 4 results](#phase-4-results), [Phase 5 results](#phase-5-results) and [Phase 7 results](#phase-7-results). Everything has run on a bare Pro Micro; nothing has run on a HeliSR board yet.

2026-10-27: **HeliSR Rev 4.0 support** added, with its own firmware build: see [Rev 4.0 support](#rev-40-support). No Rev 4.0 board exists yet, so it is tested on the PC and through the app's pages only.

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
| I²C, SPI | Not usable | I²C pins (2, 3) drive the shift registers. SCK (15) is their clock. (Rev 4.0 moves the shift registers and reads AS5600s over I²C: [Rev 4.0 support](#rev-40-support).) |

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

**Other Pro Micros:** only the 5 V / 16 MHz Pro Micro is supported (decision 4, 2026-10-25). The RP2040 Pro Micro is a different chip and is out of scope, but the firmware's hardware layer is kept separate so a port stays possible.

## How it fits together

- **One shared settings definition** (`firmware/HeliSR/src/shared/helisr_config.h`, plus `helisr_protocol.h`) is compiled into both the firmware and the app. It sits inside the sketch so the Arduino IDE can still build the sketch on its own; the configurator includes it by relative path. Compile-time checks on its size and field positions, for both the AVR and the PC, stop the two from ever disagreeing.
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
4. **5 V / 16 MHz Pro Micro only (2026-10-25).** The 3.3 V / 8 MHz build was dropped: you don't need it, the wrong build leaves a board without USB until it's reflashed, and an AS5600 at 3.3 V needs different module preparation from the board README's.

## Phase 1 results

All builds are clean (no warnings in HeliSR code) with arduino-cli and Arduino AVR core 1.8.8.

**The firmware foundation**, built and working end to end in software:
- the USB module: joystick plus settings channel, a joystick layout built from the settings, and the USB name, IDs and serial number from EEPROM;
- the shift-register and interrupt-driven ADC drivers, and the spare pins;
- EEPROM settings with a checksum;
- the settings protocol, including read, write, commit, defaults, live data and bootloader entry;
- simple button and axis processing.

| Build | Flash (of 28,672) | RAM (of 2,560) |
|---|---|---|
| 16 MHz, no USB serial (release default) | 11,044 B (38 %) | 1,146 B (44 %) |
| 16 MHz, with USB serial | 11,844 B (41 %) | 1,256 B (49 %) |
| 8 MHz, no USB serial | 11,044 B (38 %) | 1,146 B (44 %) |

The settings block is 652 bytes, the biggest single RAM user. It fits in EEPROM with 362 bytes to spare.

**FreeJoy's feature code compiled for the AVR as it is** (64 buttons, 8 axes, 8 encoders), to see what phase 2 costs:

| Module | Code | RAM |
|---|---|---|
| buttons.c | ~5.2 KB | ~740 B (button state: 5 B × 64 physical + 5 B × 64 logical) |
| analog.c | ~9.9 KB | ~1,300 B (filter buffers 320, sensors 304, coefficient tables 280 in RAM, dead-band 128, axis buttons 120) |
| axis_to_buttons.c | ~0.8 KB | – |
| encoders.c | ~2.2 KB | 96 B |
| **Total** | **~18.2 KB** | **~2.1 KB** |

Taken as is, that doesn't fit: about 29 KB of flash and about 3.3 KB of RAM. The cuts below bring it to an estimated **~24–25 KB flash (85–90 %) and ~2.1–2.2 KB RAM**, leaving roughly 3–4 KB of flash and 350–450 B for the stack.

**Verdict: go,** with these porting rules for phase 2:
1. **Drop what the HeliSR can't use.** That means FreeJoy's sensor paths (TLE, MCP, MLX, ADS1115, I²C AS5600, AS5048), its STM32 ADC/DMA setup (`AxesInit` is 1.8 KB), matrices and hardware-timer encoders. This saves about 4 KB.
2. **No floating point.** `ShapeFunc` and the dead-band code use `float`, which pulls in the soft-float library (about 1–2 KB). Use integer maths.
3. **16-bit `int`.** FreeJoy assumes a 32-bit int, so every intermediate wider than int16 must be an explicit `int32_t`. The phase 1 compile already caught this in the axis constants. Even int32 has limits: the full-range calibration product overflows it (found on hardware), so keep FreeJoy's half-range `map3` structure.
4. **Constant tables go in `PROGMEM`** (filter coefficients, encoder tables): about 300 B of RAM.
5. **Smaller state.**
   - Button timestamps: `uint16_t` milliseconds, not `int32_t`, which saves about 250 B.
   - Only the 27 real digital inputs keep debounce state.
   - Filter buffers sized to what is actually used.
6. **Measure after each module.** Spare levers if needed:
   - leave out the USB serial port (already the release default);
   - cut the encoder count;
   - cut the logical buttons from 64 to 48;
   - cut the output axes from 8 to 6.

   Each lever is documented if it's used.

**The spare pins fit** (buttons, analog, LEDs, PWM): their code is in the foundation already, and costs a few hundred bytes.

### Tested on a bare Pro Micro, 2026-10-24

The board was the user's OSOYOO USB-C clone. It came with a factory sketch enumerating as an Arduino Micro (2341:8037), and its bootloader enumerates as 2341:0037. There was no HeliSR board, so the inputs were floating. The tools are in `firmware/test/`:
- `hsr-usb-test.ps1` talks to the settings channel and the joystick through Windows' own HID and joystick APIs.
- `hsr-flash-via-bootloader.ps1` flashes the way the configurator will.

| Check | Result |
|---|---|
| First flash over the factory sketch's serial port | ✅ |
| Enumeration | ✅ 1B4F:9206, v1.00, manufacturer and product "HeliSR", serial `HSR30AABCC1` from the unique ID. Composite device: a "HID-compliant game controller" and a "HID-compliant vendor-defined device" (plus COM port in the serial build) |
| Joystick layout | ✅ 4 axes and 16 buttons (11-byte report); Windows' joystick API agrees |
| Joystick data | ✅ raw reports and the joystick API match the live data |
| INFO, READ, PARAMS | ✅ |
| WRITE + COMMIT (rename to "HeliSR Test Box") | ✅ CRC checked, saved (2.2 s when every byte changes), watchdog restart, new name enumerated, "settings from EEPROM" = 1, unique ID kept |
| COMMIT with a wrong CRC | ✅ refused with ERR_CRC, nothing saved |
| DEFAULTS + COMMIT | ✅ |
| ADC sampling | ✅ floating AX pins read 0; a test build with pull-ups (`-DHSR_TEST_AX_PULLUPS`) read 4087–4088 |
| Bootloader entry over the settings channel, then flashing with avrdude | ✅ bootloader port after ~1.25 s; 11,168 B written and verified in 1.6 s. Works from the release build (no serial port) too |
| Settings survive a reflash | ✅ (avrdude `-D` doesn't erase EEPROM) |

**Bugs found and fixed while testing:**
- Reports were sent only on change, so a program opening the joystick later saw nothing. Reports now go out every exchange period, as FreeJoy does, and GET_REPORT for the joystick input report is answered.
- **Calibration overflow:** `(v − min) × 65534` exceeds int32 when the range is full width, so full-scale input came out as minimum. Fixed with clamping plus uint32. FreeJoy avoids this by mapping each half around the centre (`map3`), and the port must keep that.

**Still to check on a real HeliSR:** the shift-register inputs, AS5600 or pot axes, the spare pins, and ADC noise with real sensors.

## Phase 2 results

FreeJoy's button, axis, axis-to-button, encoder and LED logic is ported (`buttons.cpp`, `axes.cpp`, `leds.cpp`), following the porting rules. Each file's header lists its changes from FreeJoy.

**Design changes:**
- **One pass over the logical buttons** in place of FreeJoy's physical x logical double loop, which would be 4,096 iterations per scan on the AVR. The behaviour is the same.
- **Timestamps and maths:** 16-bit timestamps, integer maths only, and constant tables in flash.
- **Shared report rules:** `hsr_button_reported()`, `hsr_reported_buttons()` and `hsr_pov_mask()` live in `helisr_config.h`, so the USB descriptor, the report and the configurator can't disagree. As in FreeJoy, POV direction buttons are reported only through their hat, and reported buttons are packed in order.
- **New `SWITCH_CENTER` type** (on while an input and the next are both off).

**FreeJoy bugs fixed in passing:**
- **Trim limit:** the lower trim limit (`MIN - value`, where FreeJoy wrote `value + MIN`).
- **Sequential buttons:** their start-up missed groups when there were three or more.
- **Encoder slots:** index -1 reads for unused encoder slots.
- **Dead band:** a dynamic-dead-band variance that could overflow.
- **Delayed buttons:** one whose delay ran out during a slow pass now still gets its press.

**Settings version 2.** Phase 1's defaults lacked fields phase 2 depends on (prescaler 100, LED timers, encoder mode), so the version was bumped. EEPROM saved by phase 1 is rejected and the defaults load.

| Build | Flash (of 28,672) | RAM (of 2,560) |
|---|---|---|
| 16 MHz, no USB serial (release) | 20,256 B (70 %) | 2,042 B (80 %) |
| 16 MHz, with USB serial (development) | 21,052 B (73 %) | 2,154 B (84 %) |
| 8 MHz, no USB serial | 20,256 B (70 %) | 2,042 B (80 %) |

Far below the 24-25 KB estimate, leaving about 8 KB of flash. RAM went from 2,166 to 2,042 B by moving tables to flash and sharing one packet buffer.

**Stack, measured on the Pro Micro.** Start-up paints the free RAM, and INFO reports the bytes the stack has never reached. Through enumeration, settings transfers, a save-and-restart and processing, that's **224-254 B never touched**: about 290 B used at peak, leaving about 225 B of margin in the release build. The development build has about 110 B less margin. Keep an eye on this if features are added.

**Longest processing pass:** 3.9 ms, which includes USB interrupts during enumeration.

### Found on hardware: an Arduino core bug

Every millisecond, the AVR core's start-of-frame interrupt calls `USB_Flush(CDC_TX)` with `CDC_TX` = endpoint 3. It does this even when the USB serial port is compiled out. In the release build, endpoint 3 was the settings channel's OUT endpoint, so any command waiting there for more than about 1 ms was thrown away. Phase 1 mostly got away with it because its loop was fast; phase 2's longer passes lost up to 75 % of commands.

Fixed by ordering the endpoints so endpoint 3 is the settings IN endpoint, where the flush is harmless, and by sending each joystick report in one `USB_Send` call. The workaround is documented in `usb_helisr.cpp`. After the fix: 200/200 commands answered at about 4.7 ms each, 0 dropped. INFO now also reports commands received, replies dropped and the longest pass, for diagnosis.

### Tested on the Pro Micro (`firmware/test/hsr-logic-test.ps1`)

The test uses settings that drive features from inputs present on a bare board. It checks the report byte for byte and the exact read-back, then restores the factory settings. All checks passed:
- inverted button, and the `SWITCH_CENTER` button;
- axis-to-button ranges, also driving a hat;
- inverted axis, curve point, and the "equal" axis function;
- descriptor layout: 16 buttons, 4 axes, 1 hat, a 12-byte report;
- Windows' joystick API agreeing with all of it;
- PWM and single-LED outputs run without fault (not observable without hardware).

**Not yet exercised on hardware** (they need real switches, or the PC tests in phase 3): toggle and pulse types, delay and press timers, radio and sequential buttons, shift layers, encoders, trim and centre buttons, filters, dynamic dead band and spare-pin inputs.

**Behaviour to document for users:** while the configurator reads or writes settings, the joystick pauses for 2 s (as in FreeJoy).

## Phase 3 results

The firmware's own logic files (`buttons.cpp`, `axes.cpp`, `leds.cpp`, `pipeline.cpp`, `joy_layout.cpp`, `settings.cpp`) are compiled, unchanged, into a PC test program (`firmware/test/host/`) and driven one millisecond per pass. Three layers of checking:

1. **Scenario tests:** 192 checks, one scenario per feature, with timings derived from FreeJoy's rules. They're built with GCC's undefined-behaviour checks in trap mode, so a signed overflow stops the test.
2. **Comparison with FreeJoy's own code:** FreeJoy's `buttons.c`, `encoders.c`, `axis_to_buttons.c` and `analog.c` are compiled for the PC, unmodified (the build needs a FreeJoy checkout), and run in lockstep with HeliSR on random settings and random inputs. **2,000 of 2,000 random setups were identical**: about six million passes in which logical buttons, physical inputs, reported buttons, hats, shift state and all 8 axes matched on every pass. The default run is 400 setups.
3. **The same scenarios on the Pro Micro:** the test firmware (`build.ps1 -Test`) adds two commands that run one pass with inputs and time from the PC. `hsr-lockstep.ps1` replays the PC's trace. **56 of 56 scenarios (58,979 passes, including 10 random setups) were identical on the AVR and the PC**, which covers 16-bit `int` arithmetic and avr-libc's float.

**What the comparison found in the port** (all fixed, so the port now behaves as FreeJoy does):
- **Processing order:** logical buttons are processed in FreeJoy's order (by physical input, shifted mappings first), worked out once at start-up. Order matters where buttons share state: hat bits, radio and sequential groups.
- **Unused axes:** an axis with no source still runs through calibration and reports a constant, as in FreeJoy. Only axes nothing can observe are skipped.
- **Offset wrap:** the magnet-offset wrap uses FreeJoy's 4095, not 4096.
- **Sequential toggles:** their start-up ignores buttons with no input.
- **Axis buttons:** the prescaler sees the previous pass's button states, and trim takes at most one step up and one down per pass (FreeJoy's order and if/else chain).
- **Resolution:** the resolution step keeps FreeJoy's float calculation. An integer version differed by a count now and then, which a prescaler or axis-to-button boundary could magnify. It costs about 1 KB of flash.

**FreeJoy bugs found, kept fixed in HeliSR, each with a test that fails on FreeJoy's behaviour:**
- **Stuck delay:** a button with a delay timer that isn't processed during its press window (its input's shift layer is off) stays in DELAY for good in FreeJoy, and never responds again.
- **Trim at the bottom:** FreeJoy stores `value + MIN` as the lower trim limit, so the axis jumps back up.
- **Dynamic dead band:** FreeJoy's 32-bit variance sum wraps, and it freezes a moving axis for a few passes after a jump.
- **Also found:** reads of `buttons[-1]` for unused encoder slots, and `raw_buttons_data[-1]` for encoder inputs with no input assigned. The comparison's random settings avoid those cases.

`HSR_FREEJOY_EXACT`, used only in the comparison build, brings these bugs back so the comparison can demand identical results.

**Stack.** The phase 3 changes first pushed the peak to about 355 B, leaving only 96 B free. Four changes brought it back:
- 16-bit axis values between stages;
- interface descriptors sent from a 9-byte buffer inside the USB interrupt;
- the report built in place, with no copies;
- one function per settings command.

With them, `out_axis_data` went too. Measured on the Pro Micro: **237-257 B never used** in the release build, and 217 B in the test firmware through the whole lockstep run.

| Build | Flash (of 28,672) | RAM (of 2,560) |
|---|---|---|
| 16 MHz, no USB serial (release) | 21,398 B (74 %) | 2,093 B (81 %) |
| Test firmware | 21,916 B (76 %) | 2,094 B (81 %) |

**Toolchain:** MinGW-w64 g++ 13.1 from Qt's mirror, installed with aqtinstall to `%USERPROFILE%\Qt\Tools\mingw1310_64`. The same toolchain builds the configurator in phase 4.

**Still to check on a real HeliSR:** the shift-register inputs, real sensors, the spare pins, and ADC noise. All the logic itself has now been verified on the AVR.

## Phase 4 results

FreeJoyConfiguratorQt is now **HeliSR Configurator** (`configurator/`, see its README). Built with Qt 6.8.3 and MinGW 13.1 (aqtinstall, in `%USERPROFILE%\Qt`), no warnings.

**What changed:**
- **Rebrand:** name, program, settings folder (`Documents\HeliSR`), a new helicopter icon, and an About box that credits FreeJoyConfiguratorQt. FreeJoy's logos and wiki links are gone; the help button opens this project's `Software` folder on GitHub.
- **One settings definition:** the app compiles the firmware's `shared/helisr_config.h` and `helisr_protocol.h`, and the new `shared/helisr_defaults.h`, which holds the factory settings both sides load. Moving them there left the firmware byte-for-byte the same size (21,398 B flash, 2,093 B RAM) and all 192 PC checks still pass.
- **USB:** finds HeliSR boards by manufacturer "HeliSR" and the settings collection (usage page 0xFF00), lists them by name and serial, reads INFO first and refuses settings it doesn't understand (protocol, settings version and size must match), reads live data at about 100 per second, and writes with WRITE + COMMIT. After a write it waits for the board to restart and reconnects on its own.
- **Board page** (replaces FreeJoy's pin page): IN1-IN16 and AX1-AX4 with live AX readings, the 11 spare pins with only the functions each pin can do, and a summary. Spare-pin and axis-range changes rebuild the other pages' lists once.
- **AS5600 helper:** for AX1/PROG1 or AX4/PROG4. It walks through the datasheet's OUT-pin programming, sees each PROG press in the live reading (and presses shorter than the chip's 100 ms), checks the result (the output follows the sensor, or stays at 0 if the burn failed), and can apply the measured range as the calibration of the axes using that input.
- **Other pages:** buttons pick inputs by name (IN5, Pin TX, X range 2); Switch center added; 8 encoders numbered from 1, no fast encoder; LEDs per spare pin and PWM on pins 5/6/9/10; no I2C sensors, shift registers, RGB or host-controlled LEDs.
- **Flasher:** HeliSR's bootloader command, then the new serial port, then avrdude (`-c avr109 -b 57600 -D`, which keeps the EEPROM settings). A Pro Micro without HeliSR firmware gets a 1200-baud touch on a chosen port, or a double tap on RST. avrdude comes from `avrdude\` next to the app (phase 5 bundles it), else the Arduino IDE.
- **Profiles:** a HeliSR INI layout (spare pins by label, LEDs by pin), checked and clamped on load; FreeJoy profiles are refused with a message.
- **Command line:** `--info`, `--read`, `--write`, `--write-defaults`, `--params`, `--flash`, `--flash-new`, plus test commands.

**Tested on the Pro Micro (bare, release firmware):**

| Check | Result |
|---|---|
| Detection and INFO | ✅ "HeliSR (HSR30AABCC1)", firmware 1.0.0, 16 MHz, protocol 1, settings v2 (652 B) |
| Live data | ✅ 212 packets in 2 s |
| Read to a profile, write, read back, restore (`--roundtrip`) | ✅ byte-identical; the board restarted under its test name and back; 5.8 s |
| Flash over USB (`--flash`) | ✅ bootloader port COM4 found, written and verified, settings kept; 7.3 s |
| Every page: random settings in and back out (`--ui-test`) | ✅ 200 of 200 setups byte-identical (a deliberately broken LED mapping was caught on every LED) |
| The window's Write and Read buttons (`--ui-device-test`) | ✅ random settings written, board restarted and reconnected, read back identical, original restored |
| Screenshots of every page with a test profile | ✅ after one fix: axis sources were filled in after the axes read their settings |

**Not tested yet:** the AS5600 helper with a real AS5600 (needs the board and sensor, phase 6), flashing a Pro Micro without HeliSR firmware (`--flash-new`, the 1200-baud touch and double tap), several boards at once, and Linux/macOS builds. The Inno Setup script is still FreeJoy's (phase 5).

**Translations:** the Russian, Chinese and German files are kept; texts that didn't change are still translated, new and changed texts show in English.

## Phase 5 results

`packaging/build-release.ps1` builds a release in under a minute (see `packaging/README.md`):

| Output (1.0.0) | Size |
|---|---|
| `HeliSR-Configurator-1.0.0-Setup.exe` (Inno Setup 6) | 12.7 MB |
| `HeliSR-Configurator-1.0.0-portable.zip` | 14.9 MB |
| `HeliSR-Configurator-1.0.0-SHA256SUMS.txt` | |

**Contents** (37 MB installed):
- the app and Qt 6.8.3, from windeployqt: 4 Qt DLLs and 6 plugins, no translations, no software OpenGL, no network plugins;
- the MinGW runtime;
- `firmware\HeliSR_16MHz.hex` (21,398 B); an 8 MHz build was also shipped at first and then dropped (decision 4);
- `avrdude\`, the Arduino IDE's avrdude 8.0.0-arduino1: one 32-bit exe that needs only Windows' own DLLs;
- the licences (GPL-3, LGPL-3, GPL-2, the GCC runtime exception, winpthreads), `THIRD-PARTY-NOTICES.txt`, `NOTICE.md` and a quick-start `README.txt`.

**The installer:**
- per-user, no admin rights needed (an admin can choose all users);
- 64-bit Windows 10 or later;
- English, Russian and German;
- its own AppId;
- a GPL-3 licence page;
- a Start-menu entry, and an optional desktop icon.

**Tested** (silent install into a scratch folder, then the installed copy with only `C:\Windows` on the PATH, so no Qt or MinGW from this PC):

| Check | Result |
|---|---|
| Install and uninstall | ✅ exit 0. The uninstall removed the folder, the Start-menu shortcut and the uninstall registry entry |
| `--info` on the Pro Micro | ✅ |
| `--ui-test 50` (the window's pages, Qt plugins loading) | ✅ 50 of 50 |
| `--flash` with the bundled firmware | ✅ the bundled avrdude ran (not the Arduino IDE's copy), written and verified, settings kept |
| The window | ✅ it found the bundled firmware and picked the 16 MHz build to match the board |

**Stack, measured again:** the board's lowest unused stack is **208 B** once the app polls live data at 100 per second; it was 237-257 B in phase 3 with lighter USB traffic. More frequent USB interrupts land during the deepest processing pass. That still leaves about 200 B, but don't add stack-hungry features without measuring.

**Still open:**
- **avrdude source:** each GitHub release must carry avrdude's source next to the binary (GPL-2); the release checklist in `packaging/README.md` says what to attach.
- **Code signing:** the installer isn't signed, so SmartScreen warns the first time; the user guide (phase 7) should explain "More info → Run anyway".
- **Not tested:** flashing a factory-fresh Pro Micro (`--flash-new`).
- **No GitHub Actions workflow yet** (optional).

## Phase 7 results

Documentation for people building their own, without help:

| Page | What it covers |
|---|---|
| `README.md` | What HeliSR is, getting started, the documentation index, licence and credits |
| `docs/quick-start.md` | Install (including SmartScreen), first flash, checking it works (`joy.cpl`), wiring, first setup |
| `docs/user-guide.md` | Every page and setting, every button type (as the firmware actually behaves: timers, shifts, hats, encoders, radio and sequential buttons), axis buttons and functions, several boards, the command line |
| `docs/flashing.md` | How flashing works, new boards, updates, recovery with a double tap, troubleshooting, avrdude by hand |
| `docs/as5600.md` | OUT-pin programming, module preparation (R4, R1, DIR), wiring, the helper step by step, the UH-1's two sensors, troubleshooting |
| `docs/profiles.md` | Profiles, and the three examples with their button tables |
| `docs/development.md` | Folders, builds, how the app and firmware talk, all the tests, remaking the profiles |

The board README's "MMJoy2 setup" section is out of date, but that folder is frozen, so the docs say so instead of changing it.

**Example profiles** (`profiles/`, made by `make_profiles.py` from the factory-settings profile, which `--save-defaults` writes):
- **Default (16 buttons, 4 axes):** the factory settings.
- **UH-1 collective (HeliSR head):** the Huey head's controls from `Head/README.md`, with buttons for the middle positions of the ON-OFF-ON switches and for LDG LT OFF. The collective (AX1) is Z and the throttle (AX4) is Rz. Rev 4's throttle has no cutoff range, so the profile has no cutoff button (the first version wrongly had one, from the Rev 2 README). Named "UH-1 Collective".
- **Button box:** every button type, with two encoders, a hat and a shift layer.

The installer ships them, and the app copies them to `Documents\HeliSR\configs\examples` (an edited copy is left alone).

**Checked:**
- each profile goes through every page unchanged (`--ui-test-file`);
- on the Pro Micro, each was written, read back identical, and gave the layout Windows' joystick API reports:

  | Profile | Buttons | Axes | Hat |
  |---|---|---|---|
  | UH-1 | 16 | 2 | – |
  | Button box | 16 | 0 | 1 |
  | Default | 16 | 4 | – |

- the rebuilt installer installs the profiles, the first run copies them, and the uninstall is clean.

**Also in this phase:** only the 5 V / 16 MHz Pro Micro is supported now (decision 4). The release ships one firmware file, `HeliSR_16MHz.hex`.

**Still open:**
- **The old `Firmware/HeliCollective` sketch:** retired and removed from the repository.
- **The repository's top-level README** is only a title.
- **Not verified on hardware yet (phase 6):** the documented wiring and the AS5600 steps.

## Rev 4.0 support

2026-10-27. HeliSR Rev 4.0 (`PCB/HeliSR_Rev4.0`, designed, not ordered) reads four AS5600s over I²C through a PCA9546A switch instead of analog inputs, because the sensor cables are about 60 cm. Its shift registers' data and load lines move to pins 14 and A0. It gets its own firmware build (`build.ps1 -Board 4.0`), and the configurator supports both boards. Rev 3.0 boards behave as before.

**Decisions:**
- **One settings layout for both boards.** `dev_config_t`, its version (2) and the protocol version (1) are unchanged. So Rev 3.0's firmware, the settings saved on its boards and the profiles are untouched, and a profile works on either board. What differs is what the pins are (`hsr_spare_exists()`, `hsr_source_exists()` in `helisr_config.h`):
  - Rev 4.0 has no spare pin 9 (pin 14, the shift registers' data line there). The firmware never touches it whatever the settings say, and the app hides it.
  - Rev 4.0's A2 and A3 are analog sources 9 and 10, with no spare-pin setting: an axis that uses one turns it on. The live data carries them after the older fields (73 bytes instead of 69), so every field keeps its place; on Rev 3.0 they read 0, in bytes that were padding before.
- **The AS5600 settings belong to the board, not the profile:** the I²C clock (100, 50, 25 or 10 kHz) and each port's start and stop (ZPOS, MPOS), in their own EEPROM block (960-981), through two new commands (SENSOR_STATUS, SENSOR_CONFIG) that Rev 3.0 answers with ERR_COMMAND. Like Rev 3.0's burnt-in angles, they describe how a sensor is mounted, which a shared profile shouldn't carry. The helper saves them at once, without a restart. The firmware writes them to each sensor's volatile registers at start-up and never burns.
- **Which board a build is for** is set when it's built (`HSR_BOARD_REV`; the Arduino IDE builds Rev 3.0) and carried in flash as `hsr_build_tag_t`. INFO reads its board ID from the tag, which keeps the linker from dropping it. The app reads the tag from a `.hex` and:
  - flashes a file for the board the connected firmware is for;
  - asks before flashing the other board's file (the firmware could be on the wrong board, so it's a question, not a refusal), a Rev 4.0 file onto a Pro Micro without HeliSR firmware, or an untagged file;
  - on the command line, refuses those unless `--board` says which board the Pro Micro is on.
  The bundled files are `HeliSR_Rev3.0_16MHz.hex` and `HeliSR_Rev4.0_16MHz.hex` (they were `HeliSR_16MHz.hex`).
- **One port per pass, blocking,** with every TWI step time-limited (`i2c.cpp`): simple to check, and a pass grows by about 130 I²C clocks (1.3 ms at 100 kHz, 13 ms at 10 kHz; calculated). An interrupt-driven reader would keep passes short at the slow clocks, if they turn out to be needed.
- **Failures:** a port that fails keeps its last reading (0 until its first) and its state says why; its range is written again once it answers. Every third visit reads ZPOS and MPOS back, which catches a sensor that restarted without a failed transfer. A stuck bus is freed at once (/RESET pulse, 9 clocks, STOP), and the port that stuck it is left alone for 250 ms so the other ports carry on. A switch that doesn't answer is reset at most every 250 ms.
- **The app follows the board:** the pages show the connected board's (and remember it); without a board, the Board page chooses. A board ID the app doesn't know counts as incompatible.
- **Versions:** left at firmware 1.0.0 and app 1.0.0; bump them at the next release.
- **Not done:** the firmware doesn't check which board it's on. A Rev 4.0 build put on a Rev 3.0 board some other way (avrdude by hand, the Arduino IDE) still drives the contended pins. A possible guard, once a Rev 4.0 board can prove it doesn't misfire: before driving anything, check that pin 3 has Rev 4.0's 10 k pull-up (Rev 3.0's latch line has none), and stay passive if not.

**Builds** (no warnings in HeliSR code):

| Build | Flash (of 28,672) | RAM (of 2,560) |
|---|---|---|
| Rev 3.0, release | 21,450 B (74 %); was 21,398 | 2,093 B (81 %), unchanged |
| Rev 4.0, release | 24,188 B (84 %) | 2,174 B (84 %) |
| Rev 4.0, test (`-Test`) | 24,738 B | 2,175 B |
| Rev 4.0, USB serial (`-Serial`) | 24,978 B | 2,284 B |

Rev 4.0's extra 81 B of RAM are the sensors' state (40 B), their settings (18 B) and the two extra analog sources. Rev 3.0's lowest unused stack was 208 B under live data (phase 5), so Rev 4.0's should be about 125 B: thin but workable. Measure it once Rev 4.0 firmware runs (INFO's stack figure).

**Tested without a Rev 4.0 board:**

| Check | Result |
|---|---|
| Both builds, and Rev 4.0's `-Test` and `-Serial` | ✅ compile |
| PC tests (`run-host-tests.ps1`, now built as Rev 4.0) | ✅ 344 of 344: the 192 logic checks as before, and 152 new ones. `sensor_tests.cpp` runs `sensors.cpp` against a model of the PCA9546A with an AS5600 on each channel: each port on its own channel (AX1-AX4 → 2, 1, 3, 0) and never two at once; ZPOS before MPOS, 1 ms apart, high byte first, read back; nothing burnt; settings kept in EEPROM and written again at a restart; out-of-range settings refused with nothing changed; a damaged EEPROM block; the clock; a sensor unplugged and back, restarted silently, or refusing its range; the magnet states; the switch missing; a stuck bus; scaling to 0-4092. Also A2/A3 through the pipeline and the live data |
| What the model found | A stuck sensor took the other ports down while bus recoveries were rate-limited (the switch stayed connected to it). Fixed as above |
| `--ui-test 200` | ✅ 200 of 200 on Rev 3.0; 200 of 200 with `--board 4.0` |
| `--ui-test-file`, the 3 example profiles | ✅ unchanged on both boards |
| `--hex-info` | ✅ both builds identified; a build from before the tag reported as untagged; a non-hex file refused |
| `--flash-new` refusals (no device needed) | ✅ a Rev 4.0 file without `--board 4.0`, a file for the other board than `--board`, an untagged file, a non-hex file: each refused before anything is touched |
| `--ui-screenshot` of the Board page | Both boards look right; Rev 4.0 with made-up sensor readings (no device) |

**Found on the way, not Rev 4.0's:** `--ui-test 200` crashed on this PC, on the unchanged code too. FreeJoy's encoder page kept only 8 encoder inputs of each kind and read past its rows when a ninth existed for a moment, while settings load one button at a time. It now keeps full sorted lists (`encodersconfig.cpp`). Loading a profile with 8 encoders over another could have crashed the window the same way.

**On the Pro Micro:** not run yet (no Pro Micro was connected): Rev 3.0's `hsr-usb-test.ps1` checks, `--roundtrip`, `--ui-device-test` and `--flash`, and, on the bare Pro Micro only (never on a Rev 3.0 board), Rev 4.0 firmware's INFO, `--sensor-roundtrip`, `--sensors` (every port "no switch") and its stack figure.

**Not tested: waits for a Rev 4.0 board:**
- the shift registers on pins 14 and A0;
- everything on a real I²C bus: the TWI at each clock, the PCA9546A's channel selection and /RESET, the bus recovery, long cables and the pull-ups;
- the AS5600 as the firmware uses it: reading STATUS on through RAW ANGLE in one transfer, ZPOS and MPOS taking effect without a burn, the ANGLE output across the range, STATUS and AGC values with real magnets, and whether a chip burnt on Rev 3.0 takes a new range;
- the JTD write on a clone with JTAG on;
- A2 and A3 read by the ADC (the pipeline side is tested on the PC);
- the I²C helper with real sensors: Set start, Set stop, the direction it detects, the clock change, the board-page states;
- pass times and the stack at each clock;
- the flasher's dialogs in the window (the check behind them is the command line's, tested above).
