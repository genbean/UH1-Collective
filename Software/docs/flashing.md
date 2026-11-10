# Flashing the firmware

HeliSR Configurator writes the firmware itself; you don't need the Arduino IDE.

## How it works

The Pro Micro has a small **bootloader** that can rewrite the firmware. It runs for about 8 seconds after the board is reset into it, and shows up as a new serial port (COM*n*). HeliSR Configurator gets the board into the bootloader, finds the new port, and runs **avrdude** (bundled with the app) to write the firmware: `firmware\HeliSR_Rev4.0_16MHz.hex`.

The board's **settings survive flashing**: they're kept in the Pro Micro's EEPROM, which flashing doesn't touch. The one exception: a firmware version with a different settings layout loads the factory settings instead (the app's release notes say when). Save a profile before updating, to be safe.

## Which firmware

The firmware is for the **HeliSR Rev 4.0** board: `HeliSR_Rev4.0_16MHz.hex`. Firmware made for another board can drive the board's lines against its own chips, so every HeliSR firmware file says which board it's for, and the app checks it before flashing:
- **A file for another board** is refused.
- **A connected board whose firmware says it's on another board** (an older HeliSR board, for example): the app asks you to confirm before flashing Rev 4.0 firmware onto it.
- **A file that doesn't say** (not HeliSR firmware, or a HeliSR build from before the check) gets a warning too.

A Pro Micro that isn't on any board yet can take it.

## A new Pro Micro (no HeliSR firmware yet)

**Advanced Settings → Firmware**, pick **HeliSR Rev 4.0 (5 V / 16 MHz Pro Micro)**, then pick how to reach the bootloader:

- **Its serial port.** A Pro Micro running a factory test sketch or any Arduino program has a serial port (COM*n*). Pick it, then click **Flash a Pro Micro without HeliSR firmware**. The app opens the port at 1200 baud, the Arduino signal to restart into the bootloader, and flashes.
- **Double tap on RST.** For any board, including one whose program has no serial port or doesn't work. Pick **Double tap on RST**, click **Flash a Pro Micro without HeliSR firmware**, then press the HeliSR board's **RST** button twice quickly within 20 seconds. On a bare Pro Micro, touch its RST pin to GND twice. The ↻ button next to the list refreshes the ports.

## Updating a HeliSR board

With the board connected (green status), **Advanced Settings → Firmware → Flash firmware to the connected device**. It tells the board to start its bootloader over USB, then flashes. It takes about 10 seconds, and the board reconnects afterwards with its settings and its AS5600 settings.

If the status box is **yellow** ("Firmware … doesn't match this app"), the board has older or newer firmware than this app understands. You can still flash it from there.

**Another .hex file...** in the firmware list flashes a file of your own, for example one you built yourself (see [Development](development.md)).

## Troubleshooting

| Problem | What to do |
|---|---|
| "The bootloader didn't appear" | Use a USB **data** cable. Try **Double tap on RST**, tapping twice within about half a second. Unplug other Arduino boards so the right port is found |
| "COM*n* couldn't be opened" | Another program has the port open: close the Arduino IDE's serial monitor, MMJoy2's tool, or any terminal |
| "avrdude failed" | Try again with a double tap. The last lines of avrdude's output are shown; "not in sync" or "can't open device" usually means the bootloader timed out before avrdude started |
| The board isn't listed, and Windows says "USB device not recognized" | Its firmware is broken or isn't HeliSR: flash it with **Double tap on RST** |
| The board isn't listed, but `joy.cpl` shows it | Unplug and replug it. If it's still missing, flash it again |
| The status is yellow | Update the firmware (above) |
| Windows shows the old name after a rename | **Advanced Settings → Remove name**, then unplug and replug the board |
| "Which board?" | The connected firmware says it's on another board, or the file doesn't say which board it's for. Check the revision printed on the board. Flash only if it's a Rev 4.0 board, or no board (see [Which firmware](#which-firmware)) |
| "This firmware is for the … board" | The file is for another board: the app won't flash it. Use `HeliSR_Rev4.0_16MHz.hex` |
| "Not flashed" on the command line | The same checks. If you're sure the Pro Micro is on a Rev 4.0 board (or on none), add `--board 4.0` |

## Flashing by hand

For other systems or scripts: put the board into its bootloader (double tap on RST), find its new serial port, and within 8 seconds run avrdude from the app's folder:

```
avrdude\avrdude.exe -C avrdude\avrdude.conf -p atmega32u4 -c avr109 -P COM5 -b 57600 -D -U flash:w:firmware\HeliSR_Rev4.0_16MHz.hex:i
```

avrdude doesn't check the board: make sure of it first. `-D` keeps the settings in EEPROM. The app's command line does the same in one step, with the board check: `HeliSRConfigurator --flash-new firmware\HeliSR_Rev4.0_16MHz.hex` (add `--port COM5` for a board with a serial port). `HeliSRConfigurator --hex-info <file>` says which board a file is for.
