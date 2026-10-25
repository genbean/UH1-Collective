# HeliSR Configurator user guide

HeliSR Configurator sets up the HeliSR firmware on a Pro Micro. Nothing you change is sent to the board until you click **Write config to Device**.

- [The left-hand panel](#the-left-hand-panel)
- [Board](#board)
- [Button Config](#button-config)
- [Axes Config](#axes-config) and [Axes Curves](#axes-curves)
- [Encoders](#encoders)
- [LED/PWM](#ledpwm)
- [Advanced Settings](#advanced-settings)
- [Several boards on one PC](#several-boards-on-one-pc)
- [Command line](#command-line)

## The left-hand panel

| Control | What it does |
|---|---|
| Device list | Every HeliSR board plugged in, by name and serial number (for example `HeliSR (HSR30AABCC1)`). The app works with the one shown. |
| Status | Green with the firmware version: connected. Red: no board. Yellow: the board's firmware doesn't match this version of the app; update it (see [Flashing](flashing.md)). |
| **Read config from Device** | Loads the board's settings into the pages. |
| **Write config to Device** | Sends the pages' settings to the board. The board checks them, saves them and restarts, and the app reconnects. Windows sees the new name and layout straight away. |
| Profile list, ⚙ | Profiles in `Documents\HeliSR\configs`. Picking one loads it into the pages (not onto the board). ⚙ chooses another folder. |
| **Load config from file** / **Save config to file** | Open or save a profile anywhere. The examples that come with the app are in the `examples` folder. See [Profiles](profiles.md). |
| **Reset All** | Puts the factory settings in the pages: IN1–IN16 as buttons 1–16, AX1–AX4 as X, Y, Z, Rx. |
| **Show debug** | A log of what the app is doing, for troubleshooting. |
| Help (the globe) | Opens this documentation on GitHub. |

## Board

The board's fixed inputs, what the spare Pro Micro pins do, and the AS5600 helper.

**IN1–IN16** are the 16 switch inputs, physical inputs 1–16 on the Button Config page. **AX1–AX4** are the 4 analog inputs; the bars show their live readings (0–4092). AX1 and AX4 have the PROG1 and PROG4 buttons for AS5600 sensors.

**Spare Pro Micro pins.** The board leaves 11 Pro Micro pins unused: TX, RX, 4, 5, 6, 7, 8, 9, 10, 14 and 16. They aren't broken out, so using one means soldering a wire to the Pro Micro. Each can be:

| Setting | What it does | Pins |
|---|---|---|
| Not used | Nothing (the default) | all |
| Button to GND | A switch from the pin to GND, using the pin's internal pull-up. It becomes a physical input (number 17 for TX ... 27 for pin 16) | all |
| Button to VCC | A switch from the pin to VCC. **Needs a 10 kΩ resistor from the pin to GND** | all |
| Axis analog | An extra analog input, offered as an axis source | 4, 6, 8, 9, 10 |
| LED | An on/off output for an LED (with its resistor), set up on the LED/PWM page | all |
| LED PWM | A dimmable output (backlighting), set up on the LED/PWM page | 5, 6, 9, 10 |

**Summary** adds it all up. Axis ranges (buttons from axes) share 37 physical inputs; if the axes ask for more, the app won't write the settings until you remove some.

**AS5600 programming helper:** see the [AS5600 guide](as5600.md).

## Button Config

The firmware has **64 logical buttons**: the buttons a game sees. Each one is fed by a **physical input** and has a **function** (type).

**Physical buttons** (left) shows every physical input, lit while it's on: IN1–IN16, any spare pins set as buttons (labelled with the pin, like `TX`), and the axis ranges (`X1` is the first range of the X axis; see [Axes Config](#axes-config)). With **Automatically set physical button when pressed** ticked, click a logical button's input box and then press a switch: the box picks that input.

**Logical buttons** (right), one row each:

| Column | Meaning |
|---|---|
| № | The logical button's number |
| Physical | The input that drives it, by name (IN5, Pin TX, X range 2), or `-` for none |
| Disable | Keeps the button out of the game's view (it still works for shifts, LEDs and axis buttons) |
| Invert | On while the input is **off** |
| Function | What the button does: see below |
| Shift | Which shift layer it belongs to: see [Shifts](#shifts) |
| Delay timer | Waits this long (Timer 1–3) after the input turns on before acting |
| Press timer | How long the button stays on, at least (default 100 ms); the length of a pulse |

**Button numbers in games.** Games see only the buttons that are reported, numbered in order. A logical button with no input, a disabled one, or a hat direction doesn't take a number. Logical buttons 1–16 with nothing disabled are game buttons 1–16.

### Functions

| Function | What the game sees |
|---|---|
| Button normal | On while the input is on |
| Button toggle | Each press turns it on, the next press off (a latching button) |
| Toggle switch ON/OFF | A short press (the press timer) each time the switch changes, either way. For games that expect a key press per flip of a switch |
| Toggle switch ON | A short press when the switch turns on |
| Toggle switch OFF | A short press when the switch turns off |
| **Switch center** | On while this input **and the next one** are both off. On an ON-OFF-ON switch wired to IN5 and IN6, a Switch center button on IN5 gives the middle position its own button. (New in HeliSR) |
| POV1–POV4 Up / Right / Down / Left | A direction of hat switch 1–4. Hats with any direction assigned appear in the game as hats, in order; their directions don't count as buttons |
| POV1 / POV2 Center | On while that hat is centred |
| Encoder A / Encoder B | One of the two signal lines of a rotary encoder. The first Encoder A button pairs with the first Encoder B button, and so on (up to 8 encoders). A turns on for a click one way, B for a click the other way. See [Encoders](#encoders) |
| Radio button 1–4 | A group: pressing any button of the group turns it on and the others in its group off, and it stays on |
| Sequential toggle | Several logical buttons on the **same** input: each press moves on to the next one, which stays on |
| Sequential button | The same, but the current one is on only while the input is held |

### Shifts

**Shift 1–5** (top) each name a logical button. While that button is on, its shift layer is active:

- a logical button on **shift *k*** works only while shift *k* is active;
- a logical button with **no shift** (`-`) works only while **no** shift is active.

So one input can do two jobs. For example, IN16 as shift 1, IN2 as button 2 with no shift, and IN2 again as button 21 on shift 1: IN2 alone presses button 2; IN16 + IN2 presses button 21.

### Timer settings

| Setting | Meaning |
|---|---|
| Timer 1–3 | Three durations for the Delay and Press timer columns |
| Debounce timer | How long an input must be steady before a change counts (default 20 ms). Raise it if a switch double-triggers |
| Axes to buttons timer | The same for axis ranges (default 50 ms) |
| Encoder press timer | How long an encoder click's button stays on (default 20 ms) |

## Axes Config

The firmware reports up to **8 axes**: X, Y, Z, Rx, Ry, Rz, Slider 1, Slider 2. Each has a panel.

| Control | Meaning |
|---|---|
| Output | Report this axis to games. Untick it for axes you don't use, so a floating input can't jitter |
| Inverted | Reverse the axis |
| Axis source | Where the axis comes from: **AX1–AX4**, a spare pin set to Axis analog, **Encoder** (the encoder chosen in the extended settings), or **None** |
| Out / Raw bars | The axis as games see it, and the source's raw value |
| Calibrate | Click, move the control through its whole range, then click **Stop && Save**: the minimum and maximum are set from what it saw |
| Set Center / Center | For self-centring controls: set the centre to the current position. Without Center, the centre is half-way |
| Reset calibration | The full range again |
| Buttons from axes | Splits the axis into up to 12 ranges, each a physical input (an axis range) on the Button Config page: detents, a throttle cutoff, a gear lever. Drag the markers to set where each range starts and ends |

**Show extended settings:**

| Setting | Meaning |
|---|---|
| Filter | Smoothing, off or level 1–7. Higher is smoother but slower |
| Deadband / Dynamic deadband | A dead zone around the centre (centred axes), or one that follows a still control so it doesn't jitter |
| Resolution | Bits of resolution reported (1–16) |
| Offset | Moves the wrap-around point of a 360° sensor (in 15° steps). An AS5600 programmed with its PROG button doesn't need it |
| Encoder | With the source set to Encoder: which encoder (as numbered on the Encoders page) |
| Function / Function axis | Combine with another axis: **Plus** adds it, **Minus** subtracts it, **Equal** copies it. Always on, or only while a Function enable button is held |
| Button 1–3 | Logical buttons that act on the axis. **Up / Down** (buttons 1 and 3) move it in steps of the full range ÷ **Step div**; holding repeats after half a second. With the source None, this makes an axis driven by buttons, such as trim from a hat. **Reset** returns the steps to zero. **Center** makes the current position the centre. **Prescale enable** scales the axis to **Prescaler %** while held (with no such button, Prescaler % always applies; 100 % changes nothing). **Function enable** turns the function on while held |

## Axes Curves

An 11-point response curve for each axis: drag the points, or pick a preset. Hold Ctrl (or click the Ctrl button) to select several axes and change their curves together.

## Encoders

Up to **8 rotary encoders**, each on two inputs set to Encoder A and Encoder B on the Button Config page. The page shows each encoder's inputs and its type:

- **Encoder 1x:** one press per full cycle of the encoder's two signals. Right for most detented encoders (EC11 and similar), where one click is one cycle.
- **Encoder 2x / 4x:** two or four presses per cycle, for encoders that click more often than their cycle.

If one click gives two presses, choose 1x; if it takes two clicks to get one press, choose 2x.

## LED/PWM

**On/off LEDs** (right): one row for each spare pin set to **LED** on the Board page.

| Column | Meaning |
|---|---|
| Pin | The spare pin; it lights green while the LED is on |
| Logical button | The LED follows this logical button (with its Invert setting) |
| Function | Normal, or Inverted (lit while the button is off) |
| Timer | Steady (`-`), or blinking with Timer 1–4 (set at the bottom) while on |

**PWM outputs** (left): pins 5, 6, 9 and 10, when set to **LED PWM** on the Board page. Each has a brightness (duty cycle, 0–100 %), or follows an axis when **Connected to axis** is ticked, scaled by that brightness.

The Pro Micro's pins can drive about 20 mA each: an LED with a resistor is fine, but a strip of backlight LEDs needs a transistor.

## Advanced Settings

| Setting | Meaning |
|---|---|
| Device USB name | What Windows and games call the board (up to 26 characters, plain ASCII) |
| VID / PID | The USB vendor and product IDs. Give each HeliSR board on one PC its own PID (see below) |
| USB exchange period | How often the board reports to the PC (default 5 ms) |
| Remove name | Clears Windows' remembered name for this VID/PID. Windows sometimes keeps showing an old name after a rename; this fixes it |
| Firmware | Updates the firmware, or puts it on a new Pro Micro: see [Flashing](flashing.md) |
| Languages, theme, font size | The app's own look. Russian, Chinese and German translations come from FreeJoy's app; text that's new in HeliSR shows in English |

## Several boards on one PC

Each HeliSR board has its own serial number, so Windows keeps them apart. Give each a different **Device USB name** and **PID** (for example 9206, 9207, 9208): Windows remembers names by VID/PID, and games tell controllers apart by them. Pick the board to work on in the device list.

## Command line

The app also runs without its window, for backups or scripts. Run it from a command prompt in its folder:

```
HeliSRConfigurator --info                       firmware version and board details
HeliSRConfigurator --read  my-setup.cfg         save the board's settings to a profile
HeliSRConfigurator --write my-setup.cfg         write a profile to the board
HeliSRConfigurator --write-defaults             put the factory settings on the board
HeliSRConfigurator --params 5                   show the live readings for 5 seconds
HeliSRConfigurator --flash firmware\HeliSR_16MHz.hex                  update the firmware
HeliSRConfigurator --flash-new firmware\HeliSR_16MHz.hex [--port COM5]   flash a new Pro Micro
HeliSRConfigurator --save-defaults new.cfg      save the factory settings as a profile (no board needed)
```

Add `--device 2` to use the second board in the list.
