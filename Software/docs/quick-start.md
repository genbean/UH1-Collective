# Quick start

From a bare Pro Micro to a working game controller in about ten minutes.

## What you need

- A **HeliSR Rev 3.0 board**, assembled (see [`PCB/HeliSR_Rev3.0`](../../PCB/HeliSR_Rev3.0/README.md)).
- A **5 V / 16 MHz Pro Micro** (ATmega32U4): the SparkFun one or a clone, micro-USB or USB-C. The 3.3 V / 8 MHz Pro Micro isn't supported.
- A USB **data** cable (some charging cables have no data wires).
- A PC with **64-bit Windows 10 or 11**.

The board README's "MMJoy2 setup" section is out of date: HeliSR's own firmware and app replace MMJoy2. Everything else in it (wiring, AS5600 preparation) still applies.

## 1. Install HeliSR Configurator

Download `HeliSR-Configurator-x.y.z-Setup.exe` from the project's [Releases](https://github.com/genbean/Heli-Collective/releases) page and run it. It installs for your user account only and needs no administrator rights.

The installer isn't signed, so Windows may show **"Windows protected your PC"**. Click **More info**, then **Run anyway**.

If you'd rather not install anything, use `HeliSR-Configurator-x.y.z-portable.zip` instead: unzip it anywhere and run `HeliSRConfigurator.exe`.

## 2. Flash the firmware

A new Pro Micro comes with a test sketch or an Arduino program, not HeliSR. To put HeliSR on it:

1. Plug the Pro Micro (on its board, or bare) into USB and start **HeliSR Configurator**.
2. Open **Advanced Settings**. Under **Firmware**, keep **HeliSR (5 V / 16 MHz Pro Micro)**.
3. In the list below it, pick the Pro Micro's serial port (COM*n*), if it has one. A board straight from the factory, or one running an Arduino sketch, usually does. If you're not sure, choose **Double tap on RST**.
4. Click **Flash a Pro Micro without HeliSR firmware**.
   - With a serial port picked, the app restarts the board into its bootloader by itself.
   - With **Double tap on RST**, press the board's **RST** button twice quickly when the app asks. On a bare Pro Micro, touch its RST pin to GND twice.
5. The progress bar fills and the app says **Firmware written and verified**. The board restarts as **HeliSR**, and the app connects to it: the status box at the top left turns green and shows the firmware version.

If it doesn't work, see [Flashing](flashing.md#troubleshooting).

## 3. Check it works

With no setup at all, HeliSR is already a game controller:

- **IN1–IN16** are buttons 1–16.
- **AX1–AX4** are the X, Y, Z and Rx axes.
- The device is called **HeliSR**.

Two ways to see it work:

- **In HeliSR Configurator:** the **Button Config** page lights up each input as you press it (the round indicators at the left), and the **Board** page shows the live readings of AX1–AX4.
- **In Windows:** press Win+R, type `joy.cpl` and press Enter. Select **HeliSR**, then **Properties**.

With nothing wired up, the buttons stay off and the axes sit at one end. That's normal.

## 4. Wire your controls

- **Switches and buttons** go on **J1** (IN1–IN8) and **J2** (IN9–IN16), each between its input pin and a GND pin. The inputs have pull-ups on the board, so an open switch reads off and a closed one reads on.
- **Pots, Hall sensors and AS5600 angle sensors** go on **AX1–AX4** (J11–J14): VCC, signal, GND.

The board README has the [connector pinouts](../../PCB/HeliSR_Rev3.0/README.md#connectors). For an AS5600, read the [AS5600 guide](as5600.md) **before** you power it up with the PROG buttons nearby: its range can be programmed only once.

## 5. Set it up

1. Click **Read config from Device**: the pages now show what's on the board.
2. Change what you need: button types, which axes are reported, calibration, the device's name. The [user guide](user-guide.md) explains every page.
3. Click **Write config to Device**. The board saves the settings and restarts with them, and the app reconnects by itself.

**Save config to file** keeps a setup as a profile, so you can put it back or share it. Ready-made profiles, including the UH-1 collective, are described in [Profiles](profiles.md).
