# Heli Collective firmware

Arduino firmware for the OSOYOO USB-C Pro Micro clone (5V/16 MHz, ATmega32U4) on the HeliSR Rev 3.0 board. It replaces MMJoy2: the board README's MMJoy2 setup steps don't apply. Windows sees a game controller called **Heli Collective** with no drivers or configuration tool needed.

## What the PC sees

| HID | Source | Notes |
|---|---|---|
| Buttons 1–16 | IN1–IN16 (J1, J2) | INx is button x. The firmware undoes the chain's shift order from `HeliSR_Rev3.0_Input_Map.csv`. |
| Button 17 | IN3 and IN4 both open | LDG LT EXT / RETR toggle in the middle (OFF) |
| Button 18 | IN5 and IN6 both open | SL ON / STOW toggle in the middle (OFF) |
| Button 19 | IN7 open | LDG LT ON / OFF toggle at OFF |
| Z axis | AX1 (A3) | Collective, 0–4095 |
| X rotation | AX4 (A0) | Throttle, 0 at cutoff, full at full open |
| Y / Z rotation | AX2 / AX3 | Off by default (spare in head Rev 2–4). Set `USE_AX2` / `USE_AX3` to 1 to add them. |

With head Rev 4's wiring: GOV RPM INCR/DECR = 1/2, LDG LT EXT/RETR = 3/4, SL ON/STOW = 5/6, LDG LT ON = 7, search hat = 9–12, STOP REL = 13, starter trigger = 14.

Buttons 17–19 are there because sims bind a toggle's OFF position more easily as its own button. Set `VIRTUAL_CENTER_BUTTONS` to 0 if you don't want them.

Switches are debounced (5 ms). Each axis averages 16 ADC readings, which gives 12 bits, and is lightly smoothed.

## Building and flashing

Everything needed is already on this PC: the Arduino IDE and its Arduino AVR Boards 1.8.8 core. No extra libraries are used.

**With the script** (PowerShell, from this folder):

```powershell
.\build.ps1
```

This builds `build\HeliCollective.ino.hex`. To build and flash, plug the Pro Micro in, find its COM port (Device Manager → Ports), and run:

```powershell
.\build.ps1 -Port COM5
```

**With the Arduino IDE:** open `HeliCollective\HeliCollective.ino`, pick **Arduino Leonardo** as the board and the Pro Micro's port, then Upload. This works the same, but Windows will list the device as "Arduino Leonardo" instead of "Heli Collective".

**If the upload can't find the board** (a fresh clone, or a sketch that crashed): start the upload, and when the console says it's waiting for the port, short RST to GND twice quickly. On the HeliSR, press the RST button twice. The bootloader stays up for about 8 seconds.

## First test

1. Flash it, then open the Arduino IDE's Serial Monitor (any baud rate). Ten times a second it prints the 16 inputs (`1` = closed) and each axis's raw reading (0–4092) and output (0–4095).
2. Close each switch in turn and check the right INx lights. If the inputs come out in the wrong order, fix `BIT_TO_INPUT` at the top of the sketch.
3. Move each axis to both stops and note the raw numbers. Windows: press Win+R, type `joy.cpl`, and open **Heli Collective** → Properties to see the buttons and axes.

Without the HeliSR board under it, the Pro Micro's data and analog pins float, so the buttons flicker and the axes wander. That's normal.

## Settings (top of the sketch)

- `axes[]`: for each axis, the pin, `invert`, and `rawMin` / `rawMax`. The default trims 20 counts off each end, so a programmed AS5600 reaches 0 and full scale. If an axis doesn't reach an end, set these from the Serial Monitor's raw readings at the stops. If it runs backwards, set `invert` to `true`. Or leave both alone and calibrate in the sim or `joy.cpl`.
- `USE_AX2`, `USE_AX3`, `VIRTUAL_CENTER_BUTTONS`, `DEBOUNCE_MS`.

After changing the button count or the axes, Windows may keep the old layout until you unplug and replug. If it still shows the old one, remove the device in Device Manager.

## Pins

These match the HeliSR Rev 3.0 board:

- 74HC165 latch (SH/LD): pin 3 (PD0)
- 74HC165 data: pin 2 (PD1)
- 74HC165 clock: pin 15 (PB1)
- AX1–AX4: A3, A2, A1, A0
