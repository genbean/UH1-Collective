# HeliSR software

Firmware and a setup app that turn a **Pro Micro on a HeliSR Rev 3.0 board** into a USB game controller. They aren't tied to this project's UH-1 collective: use them in any collective, throttle, button box or panel.

- **16 switch inputs** (IN1–IN16) and **4 analog inputs** (AX1–AX4) on the board, plus 11 spare Pro Micro pins for more buttons, analog axes, LEDs or PWM backlighting.
- **64 buttons, 8 axes, 4 hats** as Windows and games see them. Plain buttons, latching toggles, pulses for toggle switches, a button for the middle of ON-OFF-ON switches, radio and sequential buttons, 8 rotary encoders, and 5 shift layers.
- **Axes:** calibration, smoothing, dead bands, curves, combined axes, axes driven by buttons, and up to 12 button ranges per axis (detents, a throttle cutoff).
- **AS5600 sensors:** a helper for programming their range with the board's PROG buttons.
- **Works straight away:** with no setup, IN1–IN16 are buttons 1–16 and AX1–AX4 are four axes.
- **HeliSR Configurator** (Windows 10/11) reads and writes the settings, saves them as profiles, and flashes the firmware itself, with no Arduino IDE needed.

## Getting started

1. Download **HeliSR Configurator** from the [Releases](https://github.com/genbean/Heli-Collective/releases) page.
2. Follow the **[Quick start](docs/quick-start.md)**: install, flash the Pro Micro, check it works, set it up.

## Documentation

| Page | |
|---|---|
| [Quick start](docs/quick-start.md) | From a bare Pro Micro to a working controller |
| [User guide](docs/user-guide.md) | Every page and setting of HeliSR Configurator, and its command line |
| [Flashing](docs/flashing.md) | First flash, updates, recovery and troubleshooting |
| [AS5600 sensors](docs/as5600.md) | Preparing, wiring and programming AS5600 angle sensors |
| [Profiles](docs/profiles.md) | Saving setups, and the examples, including the **UH-1 collective** |
| [Development](docs/development.md) | Building the firmware, the app and a release; how they talk; tests |

The board itself (schematic, PCB, connectors) is documented in [`PCB/HeliSR_Rev3.0`](../PCB/HeliSR_Rev3.0/README.md). Its "MMJoy2 setup" section is out of date: this software replaces MMJoy2.

## What you need

- A HeliSR Rev 3.0 board with a **5 V / 16 MHz Pro Micro** (ATmega32U4; the SparkFun board or a clone). The 3.3 V / 8 MHz Pro Micro isn't supported.
- 64-bit Windows 10 or 11 for HeliSR Configurator. Once set up, the board works as a standard USB game controller on any system.

## Licence and credits

The HeliSR firmware and HeliSR Configurator are free software under the **GNU General Public License v3 or later** ([LICENSE](LICENSE)). They are modified versions of **[FreeJoy](https://github.com/FreeJoy-Team/FreeJoy)** and **[FreeJoyConfiguratorQt](https://github.com/FreeJoy-Team/FreeJoyConfiguratorQt)** by the FreeJoy team, ported to the Pro Micro and the HeliSR board. HeliSR isn't made or supported by the FreeJoy team. [NOTICE.md](NOTICE.md) lists the changes from FreeJoy and the third-party components; [`packaging/THIRD-PARTY-NOTICES.txt`](packaging/THIRD-PARTY-NOTICES.txt) covers what the installer ships (Qt, avrdude, the MinGW runtime).

## Status

The firmware and app are complete and tested on a bare Pro Micro:
- The firmware's logic matches FreeJoy's own code on thousands of random setups.
- Settings, flashing and the installer are tested end to end.

Testing on built HeliSR boards with real switches and sensors comes next ([PLAN.md](PLAN.md), phase 6).
