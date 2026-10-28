# HeliSR Rev 4.0 – Pro Micro + I²C collective board (Huey head)

> **Designed, not ordered, not built.** The HeliSR firmware has a Rev 4.0 build and HeliSR Configurator supports
> the board, but neither has run on one yet. See [Firmware](#firmware).

A small carrier board for the collective's switch box: a **SparkFun Pro Micro 5V/16 MHz** with **16 switch
inputs** read through two 74HC165 shift registers, as on Rev 3.0, and **four I²C ports for AS5600 magnetic angle
sensors**, replacing Rev 3.0's four analog inputs.

Rev 3.0 read each AS5600's analog output, and programmed its angle range once and for all with the PROG buttons.
An analog output picks up noise on a long cable. Rev 4.0 reads the angle digitally over I²C instead. Every AS5600
has the same I²C address (0x36), so a **PCA9546A I²C switch** on the back of the board gives each port its own
channel, and the firmware talks to one sensor at a time. Each port has its own 2.2 kΩ pull-ups, and all four
ports are built the same, so any port takes a short or a long cable.

| | |
|---|---|
| Board size | 39.3 × 33.64 mm (1.55 × 1.32 in), as Rev 3.0, with the same four M3 holes. 2 layers, 1.6 mm FR4 |
| Parts | Connectors, the button, the Pro Micro sockets and Rev 3.0's parts on the **front**; the I²C switch, its capacitor and all the resistors on the **back**. Every resistor and capacitor is **1206**, for hand soldering |
| Switch inputs | 16, on two 10-pin JST SR/SH 1.0 mm connectors (BM10B-SRSS-TBT, SMD), wired exactly as on Rev 3.0 |
| AS5600 ports | 4, each on its own 4-pin JST SR/SH 1.0 mm connector (BM04B-SRSS-TBT, SMD): **1 SDA, 2 GND, 3 VCC, 4 SCL** |
| I²C switch | PCA9546A (TI PCA9546ADR, SOIC-16 narrow), address 0x70, with its /RESET on a Pro Micro pin |
| Pull-ups | 2.2 kΩ on SDA and SCL of each port (R1–R8); 10 kΩ on the Pro Micro's SDA and SCL (R9, R10) and on /RESET (R11) |
| Button | **RST** (SW1, E-Switch TL1015AF160QG). The PROG buttons are gone: over I²C the firmware sets each sensor's range itself |
| Ground | Both layers poured with ground and stitched together (see [Checks](#checks-done-on-this-revision)) |
| Fab specs | Rev 3.0's cheap-fab rules: 0.2 mm clearance, 0.2 mm signal and 0.3 mm VCC/GND tracks, 0.6/0.3 mm vias, holes at least 0.6 mm apart |

## What changed from Rev 3.0

| | Rev 3.0 | Rev 4.0 |
|---|---|---|
| AX1–AX4 | 3-pin analog inputs (VCC, signal, GND) | 4-pin I²C ports (SDA, GND, VCC, SCL), each on its own PCA9546A channel |
| Pro Micro pins 2, 3 | Shift-register data and latch | I²C SDA and SCL (the ATmega32U4's TWI pins) |
| Shift registers | Data on pin 2, latch on pin 3, clock on pin 15 | Data on pin **14**, latch on **A0**, clock on pin 15 (unchanged) |
| A0–A3 | AX4–AX1 | A0 latch, A1 the PCA9546A's /RESET; **A2 and A3 are spare** |
| Buttons | RST, PROG1, PROG4 (and R1, R2) | RST only |
| Far end | The three buttons | AX4, RST, AX2 |
| Back | Nothing | U3 (PCA9546A), C4, R1–R11 |
| Inputs | | Unchanged: J1, J2, U1, U2, RN1, RN2 and C1–C3 are on the same nets as Rev 3.0, so IN1–IN16 come out of the chain in the same order ([`HeliSR_Rev4.0_Input_Map.csv`](HeliSR_Rev4.0_Input_Map.csv)) |

Pots and Hall sensors can't go on the AX ports any more. The Pro Micro still has analog-capable pins free (A2, A3,
4, 6, 8, 9, 10); using one means soldering a wire to the Pro Micro.

## Layout

Viewed from the top, with the USB end on the left:

- **Pro Micro** on two 12-pin sockets, its USB end at the left edge: pins 13–24 (J8) along the top, pins 1–12
  (J7) along the bottom, as on Rev 3.0.
- **Under it**, as on Rev 3.0: RN1, then C1 | U1 | C3 | U2 | C2, then RN2.
- **Top edge:** J1 (inputs 1-8), AX3 (J13).
- **Bottom edge:** J2 (inputs 9-16), AX1 (J11).
- **Far end (right):** AX4 (J14, top), RST (SW1, middle), AX2 (J12, bottom).
- **Back:** U3 under the far half of the Pro Micro with C4 beside its VCC pin, R9 and R10 beside its SDA and SCL,
  R11 beside its /RESET; under each port, that port's pair of pull-ups.

Every connector's pins face the board's middle. The JST plugs go in from the top and the cables leave upwards.

Mounting hole centres, in mm from the board's top-left corner (USB end left, J1 up): (3.2, 3.2), (36.1, 3.2),
(3.2, 30.44) and (36.1, 30.44), as on Rev 3.0.

## In the Huey head

Rev 4.0 has Rev 3.0's outline, holes and Pro Micro position, so it goes in the same place in head Rev 4 and Rev 5,
on the same spacers and screws. The parts on its front are the same JST SH height as Rev 3.0's (head Rev 5's
`check_r5.py` takes them as 4.5 mm); the parts on its back (1.75 mm at most) sit in the 4 mm gap the spacers leave
behind the board.

Two things differ:
- **AX4 and AX2 are at the far end**, where the buttons were: the top of the board in the head, just below the upper
  box's toggles. Their plugs go in from the front, like the others. Leave the wires room to turn there.
- **The throttle's AS5600 needs four wires** instead of three, and so does the collective's, which runs up the tube
  from the MkIII base (`Base`). Check the wire channels take the extra wire.

## Connectors

**J1 (inputs 1-8) and J2 (inputs 9-16)**: 10-pin JST SR/SH 1.0 mm, pinned as on Rev 1.x–3.0, so the same looms fit.

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| J1 | GND | IN1 | IN2 | IN3 | IN4 | IN5 | IN6 | IN7 | IN8 | GND |
| J2 | GND | IN9 | IN10 | IN11 | IN12 | IN13 | IN14 | IN15 | IN16 | GND |

Each switch goes between its input pin and GND. The inputs have 10 kΩ pull-ups on the board.

**AX1–AX4 (J11–J14)**: 4-pin JST SR/SH 1.0 mm.

| Pin | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| AX1–AX4 | SDA | GND | VCC (5 V) | SCL |

The order keeps SDA and SCL apart, with GND beside SDA and VCC beside SCL, which is what you want on a long cable:
twist SDA with GND and SCL with VCC, or use a 4-core cable with those pairs. It is **not** the Qwiic / STEMMA QT
order, on purpose: those boards are 3.3 V and this port is 5 V.

If you make a lead by cutting a pre-made JST SR/SH jumper in half, find which wire is pin 1 with a meter before
soldering the sensor end: the plug is keyed, but the wires may all be one colour.

| Port | Connector | PCA9546A channel | Pull-ups (SDA, SCL) | Suggested use |
|---|---|---|---|---|
| AX1 | J11 | 2 | R1, R2 | Collective (AS5600 in the MkIII base) |
| AX2 | J12 | 1 | R3, R4 | Spare |
| AX3 | J13 | 3 | R5, R6 | Spare |
| AX4 | J14 | 0 | R7, R8 | Throttle (AS5600 in the Huey head) |

The channels follow the board's geometry, not the port numbers: the firmware maps them.

## The I²C circuit

```
Pro Micro "2" SDA ──┬── R9 10k ── VCC                    ┌── R(odd) 2.2k ── VCC
Pro Micro "3" SCL ──┼── R10 10k ── VCC        PCA9546A   ├── port pin 1 SDA ─── AS5600 SDA
Pro Micro "A1" ─────┴── R11 10k ── VCC   ──── SDA/SCL ── SDn/SCn (n = 0..3) ── port pin 4 SCL ─── AS5600 SCL
                                         /RESET, A0-A2 = GND (0x70)           └── R(even) 2.2k ── VCC
```

- **Address:** A0–A2 are tied to GND, so the switch is at **0x70**; the AS5600s are at 0x36 behind it.
- **One channel at a time:** the firmware writes the switch's control register to connect one port, reads that
  sensor, and moves on. Only that port's cable is on the bus, so the long cables don't add up.
- **Pull-ups:** each port has its own 2.2 kΩ pair, on the switch's side of its cable, so each channel is a complete
  I²C bus whether or not the sensor module has pull-ups. With the Pro Micro's 10 kΩ pair in parallel, a low SDA
  sinks 2.3 + 0.5 = 2.8 mA at 5 V. That is within the 3 mA the I²C standard sets, which is also what the PCA9546A
  is rated to sink at 0.4 V (the AS5600 can sink 20 mA; the ATmega32U4 more).
- **/RESET:** R11 holds it high, so the switch works even before the firmware drives A1. Pulling A1 low resets the
  switch (all channels off), which frees a stuck bus. R11 goes to the same 5 V as the chip, as TI's errata ask.
- **Clock speed:** the AS5600 runs up to 1 MHz, but long cables want a slow clock. Plan on **100 kHz**, and less
  (50 or 25 kHz) if a long cable gives errors. Even at 25 kHz, reading all four sensors takes about 10 ms. The clock
  is set in the firmware, not on the board.
- **Cable length:** the limit is the capacitance on each line: 400 pF in the I²C standard (the AS5600 allows
  550 pF). Typical 4-core cable is 50–150 pF per metre, so a metre or more is within it. With 2.2 kΩ and 200 pF
  the rise time is about 0.4 µs, well inside 100 kHz's 1 µs.

## AS5600 modules

For the common WWZMDiB module (23 × 23 mm, Amazon B0CM3C8KFT), running on the Pro Micro's 5 V:

- **Remove R1**, the 0 Ω link between VDD5V and VDD3V3, as for Rev 3.0: it puts 5 V on the chip's 3.3 V pin.
- **Wire DIR** to GND or VCC (it floats on this module). Over I²C it still sets which way the angle rises
  (GND = clockwise, seen from the chip's top face); the firmware can invert an axis either way.
- **Remove R4**, the 1 kΩ from PGO (GPO on the module) to GND. Rev 3.0 kept it, because PGO low selects the
  OUT-pin programming the PROG buttons used. Over I²C that mode isn't wanted: without R4 the chip's internal
  pull-up holds PGO high. Leave OUT unconnected.
- **Wire VCC, GND, SDA and SCL** to the port: pin 1 SDA, 2 GND, 3 VCC, 4 SCL.
- **Check the module's own pull-ups.** The AS5600 has none of its own; the module may add some. With the module
  unpowered and unplugged, measure the resistance from SDA to VCC and from SCL to VCC:
  - **Open circuit (no reading):** no pull-ups. Fit 2.2 kΩ for R1–R8 as listed.
  - **About 10 kΩ:** fine; with the board's 2.2 kΩ the bus sinks about 3.3 mA. Fit R1–R8 as listed.
  - **4.7 kΩ or less:** too strong together with 2.2 kΩ. Either remove the module's two pull-ups, or fit 4.7 kΩ for
    R1–R8 instead (all eight the same).
  - Check also that the module's pull-ups go to VCC, not to the chip's 3.3 V pin; if they read open to VCC but
    about the same value to VDD3V3, remove them.

Nothing is burnt into the chip: the firmware writes each sensor's start and stop angles (ZPOS, MPOS) to its
working registers every time it starts, so the range can be changed as often as you like.

## Pro Micro pins

| Socket pin | Pro Micro pin | Port | Use |
|---|---|---|---|
| 5 | 2 | PD1 | I²C SDA |
| 6 | 3 | PD0 | I²C SCL |
| 15 | 14 | PB3 | Shift register data (U2 QH) |
| 16 | 15 | PB1 | Shift register clock |
| 17 | A0 | PF7 | Shift register load (SH/LD) |
| 18 | A1 | PF6 | PCA9546A /RESET |
| 21, 22, 3/4/23 | VCC, RST, GND | | |

Spare (not connected): TX, RX, 4, 5, 6, 7, 8, 9, 10, 16, A2 and A3. The shift-register pins are the hardware SPI
clock (15) and MISO (14), so a future firmware can read the chain with the SPI unit; pin 16 (MOSI) is then not
free for other use.

## Firmware

The HeliSR firmware in `Software/firmware/HeliSR` has a build for this board: `Software/firmware/build.ps1 -Board 4.0`,
shipped as `firmware\HeliSR_Rev4.0_16MHz.hex`. It:

- reads the shift registers on pins 14 (data), 15 (clock) and A0 (load) instead of 2, 15 and 3, in Rev 3.0's bit order;
- runs the TWI on pins 2 and 3 at 100 kHz, or 50, 25 or 10 kHz for long cables (set in HeliSR Configurator), connects
  one port's PCA9546A channel at a time and reads its AS5600's ANGLE register (address 0x36), scaled to the analog
  inputs' 0–4092. It also reads STATUS, RAW ANGLE and AGC, for the magnet checks and the Configurator's helper;
- writes each sensor's start and stop to its volatile ZPOS and MPOS at start-up, 1 ms apart, from settings it keeps
  in EEPROM (the Configurator sets them), reads them back, and writes them again to a sensor that comes back after an
  error or has lost them. It never burns anything;
- maps channels 2, 1, 3, 0 to AX1–AX4 as above. A stuck bus is freed by pulling A1 low (never driving it high), clocking
  out a half-sent byte and sending a STOP; a port that stuck it is left alone for 250 ms;
- treats A2 and A3 as spare analog pins (axis sources 9 and 10) instead of AX2 and AX1, and leaves pin 14 out of the
  spare pins;
- sets the JTD bit in MCUCR at start-up (written twice, as the ATmega32U4 requires). A0 and A1 are also the JTAG
  pins TDI and TDO (PF7, PF6); SparkFun ships the Pro Micro with JTAG off in its fuses (high fuse 0xD8), but a clone
  with JTAG on would otherwise keep both pins from working as plain I/O.

The sensor code is tested on a PC against a model of the PCA9546A and the AS5600 (`Software/firmware/test/host`).
Nothing of this board's firmware has run on the board itself: the shift-register pins, the I²C timing on real
cables, the bus recovery and the sensors' behaviour all wait for one. `Software/PLAN.md` lists what's still to check.

**Keep the builds apart.** Rev 3.0 firmware on a Rev 4.0 board does no harm: it drives the I²C clock line and listens
on SDA, which only the pull-ups hold, and reads A0–A3 as analog inputs. A Rev 4.0 build on a **Rev 3.0** board would
drive A0 and A1 against whatever is on AX4 and AX3, and pull pin 2 against U2's QH output. So every build carries a tag
saying which board it's for, INFO reports it, and HeliSR Configurator checks the tag in a `.hex` against the connected
firmware before it flashes, and asks before putting Rev 4.0 firmware on a Pro Micro whose board it can't tell.

## Files

| File | What it is |
|---|---|
| `HeliSR_Rev4.0.kicad_pcb` / `.kicad_pro` | KiCad 9 board |
| `HeliSR_Rev4.0.kicad_dru` | Custom DRC rules for the intentional overlaps (see below) |
| `HeliSR.pretty/`, `fp-lib-table` | Project footprint library: the TL1015AF160QG button footprint |
| `HeliSR_Rev4.0_Gerbers.zip` | Gerbers + drill files |
| `HeliSR_Rev4.0_Top.png`, `HeliSR_Rev4.0_Bottom_mirrored.png` | Board renders |
| `HeliSR_Rev4.0_Board_BOM.xlsx` | The parts that go on the board, checked against the board file, plus the Pro Micro and its headers |
| `HeliSR_Rev4.0_Input_Map.csv` | Every input → connector pin → chip pin → shift order (the same as Rev 3.0) |
| `tools/` | The scripts that build, route, finish, check and export this board (see Rebuilding) |

## Assembly order

1. **The back first**, while the front is still flat: **U3** (pin 1 dot toward the far end, at the J1 side), then
   **C4** and **R1–R11** (all 1206). R1–R8 are all 2.2 kΩ (or all 4.7 kΩ: see [AS5600 modules](#as5600-modules)); R9–R11 10 kΩ.
2. On the front, **U1, U2**, then the 1206 caps **C1, C2, C3**.
3. **RN1, RN2**. The dot (pin 1) goes in the square pad.
4. The JST headers and the RST button.
5. The two Pro Micro sockets last.

## Pro Micro RP2040 compatibility

As on Rev 3.0, every pin the board uses is also there on the **SparkFun Pro Micro RP2040**, whose VCC pin is 3.3 V:
its pins 2 and 3 (GPIO2, GPIO3) can be the RP2040's I2C1 SDA and SCL, and the pull-ups then go to 3.3 V, which suits an AS5600 module
run in its 3.3 V mode (R1 left fitted). There is no RP2040 build of the HeliSR firmware. Not tried.

## DRC rules

`HeliSR_Rev4.0.kicad_dru` covers the intentional overlaps, each rule naming the exact footprint pairs, as on Rev 3.0:

- Parts nested under the Pro Micro (resistor networks, shift registers and caps between the sockets), as on Rev 3.0.
- The connector rows: the courtyards of J1 and AX3 (J13), and of J2 and AX1 (J11), overlap; the housings don't.
- The M3 holes: their courtyards (6.9 mm across) overlap J1, J2 and the far-end ports AX4 (J14) and AX2 (J12). Every
  pad, track and via is at least 3.5 mm from each hole centre, clear of the M3 nut's corners (3.18 mm) on the front
  and the 6.4 mm spacer on the back.
- The far end: RST's courtyard overlaps the AX4 and AX2 ports' by up to 0.3 mm; the switch body and the JST housings
  are about 1.4 mm apart.
- Library silkscreen outlines that touch where parts nest.

The rules use `(severity ignore)`, because `kicad-cli` 9.x still reports `(severity exclusion)` rules as errors
(KiCad issue 24264).

## Rebuilding

The board is generated, autorouted and finished by scripts in `tools/`, run with KiCad 9 (its own Python, which has
numpy and PIL) and Freerouting 2.5.0 on a Java 25 runtime. No other Python packages are needed except openpyxl for
the BOM.

1. `gen_v4.py` places the parts, sets the nets, outline and mounting holes, and exports a DSN. The placement used
   here is `rev40_params.json`.
2. `route_v4.py` runs the generator for a list of placement variants, gives VCC/GND a 0.3 mm class, routes with
   Freerouting, imports the result (`imp_v2.py`) and DRCs it. It routes with the vias 0.7 mm across, so their holes
   end up at least 0.6 mm apart, and imports them at 0.6 mm. This board is the best of the 45 variants in the final sweep
   (U3's position, the pull-ups' offset under the ports, the far-end ports' spacing): complete, 44 router vias.
3. `finish_all_v4.py` widens the router's neck-downs, pours GND on both layers, adds GND stitching vias
   (`stitch_v4.py`), writes the DRC rules and title block (`finish_v4.py`), places the silk labels on both sides
   (`silk_fix_v4.py`), and DRCs the result.
4. `verify_netlist_v4.py` checks the netlist against Rev 3.0's board and the PCA9546A datasheet's pinout, and writes
   the input map.
5. `export_v4.py` writes `HeliSR_Rev4.0_Gerbers.zip` and the two renders, and `make_board_bom_v4.py` the board BOM
   (it stops if the board's parts and its list disagree).

## Checks done on this revision

- **KiCad 9 DRC:** 0 violations and 0 unconnected items at every severity (with `HeliSR_Rev4.0.kicad_dru`).
- **Netlist:** checked pad by pad by `verify_netlist_v4.py`. J1, J2, U1, U2, RN1, RN2, C1–C3 and SW1 are on the
  same nets as in the ordered Rev 3.0 board, so the inputs and their shift order are unchanged. U3's pins match the
  PCA9546A datasheet (TI SCPS148I): A0 1, A1 2, /RESET 3, SD0–SC1 4–7, GND 8, SD2–SC3 9–12, A2 13, SCL 14, SDA 15,
  VCC 16. Every port, pull-up and Pro Micro pin is as listed above, and every net joins at least two pads.
- **Clearance:** the cheap-fab rules above. All copper is at least 0.5 mm from the edge, and every track and via at
  least 3.7 mm from a hole centre (every pad 4.1 mm). No neck-downs: every signal track is 0.2 mm and every VCC/GND
  track 0.3 mm.
- **Routing:** 998 mm of track, 78 vias: 44 from the router and 34 GND stitching vias. The I²C lines from U3 to the
  ports are 6–29 mm long.
- **Decoupling:** C4's VCC pad is 2.65 mm from U3's VCC pin (centre to centre); C1's is 1.8 mm from U1's and C2's
  2.7 mm from U2's, as on Rev 3.0.
- **Silkscreen:** every label is 1.0 mm tall with a 0.16 mm stroke, outside every courtyard on its side, and at least
  0.5 mm from the next label. The front names the connectors (J1, J2, AX1–AX4), RST, USB and the front parts; the
  back names U3, C4, R1–R11 and the board.
- **Not checked:** nothing has been built. The I²C circuit and the cable lengths are as calculated in the
  I²C section above, not measured.
