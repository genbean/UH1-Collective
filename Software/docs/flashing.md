# Flashing the firmware

HeliSR Configurator writes the firmware itself; you don't need the Arduino IDE.

## How it works

The Pro Micro has a small **bootloader** that can rewrite the firmware. It runs for about 8 seconds after the board is reset into it, and shows up as a new serial port (COM*n*). HeliSR Configurator gets the board into the bootloader, finds the new port, and runs **avrdude** (bundled with the app) to write the firmware for your board: `firmware\HeliSR_Rev3.0_16MHz.hex` or `firmware\HeliSR_Rev4.0_16MHz.hex`.

The board's **settings survive flashing**: they're kept in the Pro Micro's EEPROM, which flashing doesn't touch. The one exception: a firmware version with a different settings layout loads the factory settings instead (the app's release notes say when). Save a profile before updating, to be safe.

## Which firmware

Each HeliSR board has its own firmware. The shift registers are on different Pro Micro pins, and Rev 4.0 reads its AS5600s over I²C where Rev 3.0 reads analog inputs.

- **Never put Rev 4.0 firmware on a Rev 3.0 board.** It drives three of the board's lines against the board's own chips (pin 2 against a shift register's output, A0 and A1 against the sensors on AX4 and AX3).
- Rev 3.0 firmware on a Rev 4.0 board does no harm, but its inputs and sensors don't work.

Every HeliSR firmware file says which board it's for, and the app checks it before flashing:
- **A connected board:** its firmware says which board it's on, the app offers the matching file, and it asks before flashing the other board's.
- **A Pro Micro without HeliSR firmware** can't tell: the app asks you to confirm the board before flashing Rev 4.0 firmware onto it. Rev 3.0 firmware goes on without a question, as before.
- **A file that doesn't say** (not HeliSR firmware, or a HeliSR build from before the check) gets a warning too.

A Pro Micro that isn't on any board yet can take either.

## A new Pro Micro (no HeliSR firmware yet)

**Advanced Settings → Firmware**, pick **HeliSR Rev 3.0** or **HeliSR Rev 4.0 (5 V / 16 MHz Pro Micro)** for your board, then pick how to reach the bootloader:

- **Its serial port.** A Pro Micro running a factory test sketch or any Arduino program has a serial port (COM*n*). Pick it, then click **Flash a Pro Micro without HeliSR firmware**. The app opens the port at 1200 baud, the Arduino signal to restart into the bootloader, and flashes.
- **Double tap on RST.** For any board, including one whose program has no serial port or doesn't work. Pick **Double tap on RST**, click **Flash a Pro Micro without HeliSR firmware**, then press the HeliSR board's **RST** button twice quickly within 20 seconds. On a bare Pro Micro, touch its RST pin to GND twice. The ↻ button next to the list refreshes the ports.

## Updating a HeliSR board

With the board connected (green status), **Advanced Settings → Firmware → Flash firmware to the connected device**. The app picks the firmware for the board the connected firmware is for. It tells the board to start its bootloader over USB, then flashes. It takes about 10 seconds, and the board reconnects afterwards with its settings (on Rev 4.0, its AS5600 settings too).

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
| "Which board?" | The file is for the other board than the connected firmware, or the Pro Micro has no HeliSR firmware and the file is for Rev 4.0. Check the revision printed on the board. Flash only if the file is for that board (see [Which firmware](#which-firmware)) |
| "Not flashed" on the command line | The same check. Add `--board 4.0` (or `3.0`) to say which board the Pro Micro is on |

## Flashing by hand

For other systems or scripts: put the board into its bootloader (double tap on RST), find its new serial port, and within 8 seconds run avrdude from the app's folder:

```
avrdude\avrdude.exe -C avrdude\avrdude.conf -p atmega32u4 -c avr109 -P COM5 -b 57600 -D -U flash:w:firmware\HeliSR_Rev3.0_16MHz.hex:i
```

Use `HeliSR_Rev4.0_16MHz.hex` for a Rev 4.0 board. avrdude doesn't check the board: make sure of it first. `-D` keeps the settings in EEPROM. The app's command line does the same in one step, with the board check: `HeliSRConfigurator --flash-new firmware\HeliSR_Rev3.0_16MHz.hex` (add `--port COM5` for a board with a serial port, and `--board 4.0` for Rev 4.0 firmware). `HeliSRConfigurator --hex-info <file>` says which board a file is for.
