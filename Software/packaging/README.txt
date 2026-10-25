HeliSR Configurator
===================

Sets up a Pro Micro (ATmega32U4) on a HeliSR Rev 3.0 board as a game
controller: buttons, axes, encoders, LEDs, and its USB name. Windows 10 or 11.

First flash of a new Pro Micro
------------------------------
1. Plug the Pro Micro into USB and start HeliSR Configurator.
2. Advanced Settings -> Firmware: pick "HeliSR (5 V / 16 MHz Pro Micro)".
3. Pick the Pro Micro's serial port in the list (a board straight from the
   factory or with an Arduino sketch has one), or "Double tap on RST".
4. Click "Flash a Pro Micro without HeliSR firmware". With "Double tap on
   RST", press the HeliSR board's RST button twice quickly when asked (on a
   bare Pro Micro, touch its RST pin to GND twice).
5. The board restarts as "HeliSR": 16 buttons (IN1-IN16) and 4 axes (AX1-AX4)
   work straight away, with no other setup.

After that
----------
- Read config from Device, change the pages, Write config to Device. The
  board restarts with the new settings.
- Save config to file / Load config from file keep setups as profiles
  (Documents\HeliSR\configs). Example profiles, including the UH-1
  collective, are in Documents\HeliSR\configs\examples.
- Firmware updates: Advanced Settings -> Firmware -> "Flash firmware to the
  connected device". The settings are kept.

What's in this folder
---------------------
HeliSRConfigurator.exe   the app (also has a command line: run it with --help)
firmware\                the HeliSR firmware (5 V / 16 MHz Pro Micro)
profiles\                example profiles
avrdude\                 avrdude, which writes the firmware
licenses\                the licences; see THIRD-PARTY-NOTICES.txt

Full instructions (quick start, user guide, flashing, AS5600 sensors):
https://github.com/genbean/UH1-Collective/tree/main/Software
Source code and the HeliSR board: https://github.com/genbean/UH1-Collective
