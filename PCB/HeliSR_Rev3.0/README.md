# HeliSR Rev 3.0 – Pro Micro + MMJoy2 collective board (Huey head)

> **Bare PCBs ordered from OSH Park on 2026-10-21 (three boards, no parts fitted, $10.20, due back about
> 2026-10-29). This revision is frozen.** `HeliSR_Rev3.0.kicad_pcb` and
> `HeliSR_Rev3.0_Gerbers.zip` are the ordered design (checksums in [Ordered files](#ordered-files)), and the files in
> this folder are read-only. Make any change in a new revision folder (Rev 3.1), not here.

A small carrier board for the collective's switch box: a **SparkFun Pro Micro 5V/16 MHz** running **MMJoy2**,
with **16 switch inputs** read through two 74HC165 shift registers (the same idea as the original Gazmac design)
and **4 analog inputs**.

Rev 3.0 is the Rev 2.0 circuit plus two **PROG** buttons for AS5600 magnetic angle sensors (one for AX1, one for
AX4, so a second AS5600 can go on AX4) and a fourth mounting hole. The board is laid out again and is nearly
symmetrical. The Pro Micro sits at the USB end, centred across the board, with both shift registers and both
pull-up networks under it. A 10-pin and two 3-pin connectors run along each long edge, and the three buttons are
across the far end.

| | |
|---|---|
| Board size | 39.3 × 33.64 mm (1.55 × 1.32 in), 2 layers, 1.6 mm FR4 |
| Ground | Both layers poured with ground and stitched together with 47 vias. Every pour island left is tied to ground; the only gaps are slivers of 2.5 mm² or less between pads and tracks |
| Fab specs | Standard cheap-fab rules (≥0.127 mm track/space, 0.3 mm drills). Designed with **0.2 mm clearance**, **0.2 mm signal tracks** and **0.3 mm VCC/GND tracks**. The only neck-down is 1.6 mm of IN11 at 0.15 mm, where the router squeezed between pads (still well above the 0.127 mm fab minimum). Vias are 0.6/0.3 mm, 76 in all |
| Switch inputs | 16, on two 10-pin JST SR/SH 1.0 mm connectors (BM10B-SRSS-TBT, SMD) |
| Analog inputs | 4, each on its own 3-pin JST SR/SH 1.0 mm connector (BM03B-SRSS-TBT, SMD; VCC / signal / GND) |
| Buttons | 3 SMD push buttons (E-Switch TL1015AF160QG): **RST** (SW1), **PROG1** (SW2, programs an AS5600 on AX1) and **PROG4** (SW3, programs an AS5600 on AX4) |
| Mounting | Four M3 holes (3.2 mm), one in each corner, 3.2 mm in from both edges. Copper keeps 3.5 mm from each hole's centre, and every part clears an M3 nut on the front and a 6.4 mm spacer behind |

## Layout

Viewed from the top, with the USB end on the left:

- **Pro Micro** on two 12-pin sockets, its USB end at the left edge: pins 13–24 (J8) along the top, pins 1–12
  (J7) along the bottom.
- **Under it**, from top to bottom: RN1, then C1 | U1 | C3 | U2 | C2, then RN2. U2 is turned 180° from U1, so
  each chip's VCC pin (pin 16) is at its outer end, next to its own 100 nF cap (C1 for U1, C2 for U2), and the
  22 µF bulk cap C3 lies between the chips.
- **Top edge:** J1 (inputs 1-8), AX3 (J13), AX4 (J14).
- **Bottom edge:** J2 (inputs 9-16), AX1 (J11), AX2 (J12).
- **Right end:** PROG4 (SW3, top), RST (SW1, middle), PROG1 (SW2, bottom). R2 and R1 (1 kΩ) sit just inside
  PROG4 and PROG1.

Every connector's pins face the Pro Micro. The JST plugs go in from the top and the cables leave upwards.

Mounting hole centres, in mm from the board's top-left corner (USB end left, J1 up): (3.2, 3.2), (36.1, 3.2),
(3.2, 30.44) and (36.1, 30.44).

## In the Huey head

**Rev 2 (`Head`)** stands the board upright on the rear wall, centred in the upper box, with the USB end
down so the Pro Micro's plug points down through a slot in the floor at the tube's top end. Seen from the front:
J1, AX3 and AX4 up the left edge, J2, AX1 and AX2 up the right, and PROG4, RST and PROG1 along the top, above the
upper box's toggles: take the upper panel off to reach them. It's on the same spacers and screws; the holes'
positions are `HELISR_MOUNTS` in `Head/huey_head.py`.

**Rev 1 (the `HueyHead` folder, since removed):** `docs/HeliSR_Rev3.0_in_Huey_head.png` shows the board to scale. It stands upright on the inside of the rear wall,
USB end down, and reaches up through a slot in the floor between the lower and upper boxes (`BOARD_SLOT` in
`huey_head.py`). Seen from the open front you look at the components: J1, AX3, AX4 and PROG4 face the GOV RPM
toggle, and J2, AX1, AX2 and PROG1 face the LDG LT EXT/RETR toggle.

- **Mounting:** four M3 × 12 countersunk screws from outside the rear wall, through 4 mm Bivar SRS-4-4MM spacers
  and the board, with M3 nuts on the front. The head's countersunk holes are at these points on the rear wall, in
  `huey_head.py`'s box frame (x, z): (−1.8, 40.9), (25.44, 40.9), (−1.8, 73.8) and (25.44, 73.8). The top two
  are in the upper box, just above its floor. `Head/README.md` gives Rev 2's fitting order.
- The board sits toward the slot's +x end (1.36 mm from it), so the USB plug comes down beside the throttle pot,
  2.05 mm clear of it, instead of over it. A 20 mm micro-USB overmold ends 6.7 mm above the top of the pot and a
  25 mm one 1.7 mm above it. The stack (4 mm spacer, board, socket, header, Pro Micro) is 19.4 mm off
  the rear wall, 2.2 mm short of the slot's front edge.
- The top edge is 1.15 mm below the upper box's two toggles (SL and LDG LT ON), so don't mount it any higher.
  The three buttons are at that end, in the upper box: take the upper panel off to reach them.
- It clears the GOV RPM toggle by 22.9 mm and the LDG LT EXT/RETR toggle by 3.8 mm.
- Fit the board after the pot holder and pot (or the AS5600 throttle sensor parts), which go in through the open front below it.

## Files

| File | What it is |
|---|---|
| `HeliSR_Rev3.0.kicad_pcb` / `.kicad_pro` | KiCad 9 board |
| `HeliSR_Rev3.0.kicad_dru` | Custom DRC rules for the intentional overlaps (see below) |
| `HeliSR.pretty/`, `fp-lib-table` | Project footprint library: the TL1015AF160QG button footprint |
| `HeliSR_Rev3.0_Gerbers.zip` | Gerbers + drill files, ready to upload to PCBWay / JLCPCB etc. |
| `HeliSR_Rev3.0_Top.png`, `HeliSR_Rev3.0_Bottom_mirrored.png` | Board renders |
| `HeliSR_Rev3.0_Board_BOM.xlsx` | Board BOM: only the parts that go on the board, checked against the board file, plus the Pro Micro and its headers. Set the number of boards to build and the quantities and prices follow (generated by `tools/make_board_bom_v3.py`) |
| `HeliSR_Rev3.0_BOM.xlsx` | Full BOM: the Digi-Key order, parts bought elsewhere (the AS5600 modules), and the MkII collective hardware (generated by `tools/make_bom_v3.py`) |
| `HeliSR_Rev3.0_Input_Map.csv` | Every input → connector pin → chip pin → MMJoy2 shift order, with the Rev 2.0 order beside it |
| `docs/HeliSR_Rev3.0_in_Huey_head.png` | To-scale fit check in the Huey head (drawn by `tools/fit_figure_rev3.py`) |
| `tools/` | The scripts that build, route, finish, check and export this board (see Rebuilding) |

## Connectors

**J1 (inputs 1-8) and J2 (inputs 9-16)**: 10-pin JST SR/SH 1.0 mm. The pinout is the same as Rev 1.x and Rev 2.0, so the same
looms fit.

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| J1 | GND | IN1 | IN2 | IN3 | IN4 | IN5 | IN6 | IN7 | IN8 | GND |
| J2 | GND | IN9 | IN10 | IN11 | IN12 | IN13 | IN14 | IN15 | IN16 | GND |

Each switch goes between its input pin and GND. The inputs have 10 kΩ pull-ups on the board, so an open switch reads
"off" and a closed switch reads "on".

**AX1–AX4 (J11–J14)**: 3-pin JST SR/SH 1.0 mm. Pin 1 is VCC, pin 2 is the signal
and pin 3 is GND. On a pot, wire the two ends to VCC and GND and the wiper to the signal pin. On an AS5600 module,
wire VCC, OUT and GND.

| Connector | Pro Micro pin | MMJoy2 pin name | Suggested use | Button |
|---|---|---|---|---|
| AX1 (J11) | A3 | F4 | Collective (AS5600 in the MkIII base, or the MkII Hall sensor) | PROG1 |
| AX2 (J12) | A2 | F5 | Throttle pot (spare if the throttle uses the AS5600 on AX4) | |
| AX3 (J13) | A1 | F6 | Head knob | |
| AX4 (J14) | A0 | F7 | Throttle AS5600 (the Huey head's geared throttle, `Head/README.md`), or spare | PROG4 |

## AS5600 sensors and the PROG buttons

The Pro Micro's I²C pins (2 and 3) drive the shift registers' data and latch lines, so the board can't program an AS5600 over I²C.
Instead it uses the chip's own one-time **OUT-pin programming** (datasheet "Option B"): the chip learns its start
and stop angles and then spreads its full 0–5 V output over that range, so the whole of the Pro Micro's ADC is
used for the collective's travel. Each PROG button pulls its axis line (the AS5600's OUT pin) to GND through 1 kΩ
while it's held. On a pot or a Hall sensor the buttons do nothing harmful, they just pull the reading down.

**Preparing the module** (WWZMDiB AS5600, Amazon B0CM3C8KFT, 23 × 23 mm):

- **Keep R4** (1 kΩ from PGO, labelled GPO on the module, to GND). PGO low is what selects OUT-pin programming. Some reviews say to remove R4
  or tie PGO high to get an analog output straight away; that gives the factory full-circle range instead, which
  leaves only about a tenth of the ADC for 35° of travel, and it needs I²C to change.
- **Remove R1** (0 Ω between VDD5V and VDD3V3). It ties the chip's 3.3 V pin to the 5 V supply, and that pin's
  absolute maximum is 4.0 V. Without it the chip's own regulator feeds VDD3V3, with the module's 10 µF on it, which
  is also what the datasheet asks for while programming.
- **Wire DIR** to GND or VCC (it floats on this module). DIR sets which way the reading rises: GND = clockwise,
  VCC = counterclockwise, seen from the chip's top face. The programming must turn the magnet in that direction
  from the start to the stop position. In the MkIII base (`Base`, sensor on the −Y trunnion, opposite
  the friction knob, with the chip facing out at the magnet in the cover), raising the collective turns the magnet counterclockwise as the
  chip sees it: **wire DIR to VCC** and program with the collective fully down as the start and fully up as the
  stop. (With DIR on GND the start would have to be fully up, and the axis would fall as the collective rises.)

**Programming (once per sensor):**

1. With the sensor assembled and connected, plug the Pro Micro into USB. Until it's programmed, the AS5600 holds
   OUT high, so the axis reads full scale whatever its position.
2. Move the collective to the **start** position of the DIR direction and hold it there.
3. Press and hold **PROG1** (PROG4 for AX4) for about a second (the chip needs at least 100 ms), then release it.
4. Move the collective to the **stop** position. It must be more than 18° from the start.
5. Press and hold PROG1 again for about a second, then release it. The chip burns both angles.
6. Check the axis now follows the collective from 0 to full scale. If it reads 0 whatever the position, the burn
   failed (the chip drives OUT to GND to show an error).

This can only be done once per chip. Re-programming takes I²C (an Arduino on SDA/SCL with the module unplugged
from the HeliSR), or a fresh module. If the axis rises the wrong way, invert it in MMJoy2.

## MMJoy2 setup

1. Flash MMJoy2 onto the Pro Micro with the MMJoy2 configuration tool. Pick the ATmega32U4 (Pro Micro / Leonardo)
   firmware. If the tool asks for the bootloader, press the **RST** button twice quickly.
2. **Buttons → Shift registers**: type **74HC165**, count **2**.
   - SR **CS / latch** pin: **D0** (Pro Micro pin "3")
   - SR **Data** pin: **D1** (Pro Micro pin "2")
   - Clock is the SPI clock, **B1** (Pro Micro pin "15"), and is fixed.
   This gives 16 buttons. The chips are wired to keep the traces short, so the order in which bits come out of the
   chain is not IN1…IN16. The "Shift order" column in `HeliSR_Rev3.0_Input_Map.csv` shows it: IN5–IN16 come
   out first, as bits 1–12 in order, then IN1–IN4 as bits 13–16. **IN1–IN4 keep their Rev 1.x / 2.0 bit numbers;
   IN5–IN16 changed**, so a Rev 2.0 MMJoy2 button table needs those twelve re-assigned (the CSV's last column has
   the Rev 2.0 order). To make INx button x in games, assign the logical button numbers in MMJoy2's button table:
   press each input and set its button number.
3. **Axes**: enable the axes you use on **F4, F5, F6 and F7** (A3, A2, A1, A0 = AX1, AX2, AX3, AX4) and give them
   whatever HID axis you want (for example Z, Rx, Ry). Set filtering, dead zones and inversion there too.
4. Write the configuration to the board. Then calibrate in the MMJoy2 tool or in the Windows game controller dialog.

The device name can be set in MMJoy2's USB settings (for example "Heli Collective").

## Assembly order

1. **U1, U2**, then the 1206 caps **C1, C2, C3** and the 0805 resistors **R1, R2**.
2. **RN1, RN2**. The dot (pin 1) goes in the square pad.
3. The JST headers and the three buttons.
4. The two Pro Micro sockets last.

## Pro Micro RP2040 compatibility

All four analog inputs use Pro Micro pins that are also analog on the **SparkFun Pro Micro RP2040** (A0–A3 =
GPIO26–29), so the same PCB takes either board:

- On the RP2040, the VCC pin is 3.3 V, so the sensors and shift registers run at 3.3 V automatically. That suits the
  RP2040's ADC. An AS5600 module then runs in its 3.3 V mode: leave its R1 fitted.
- MMJoy2 does **not** run on the RP2040. It would need its own firmware, such as a port of the Arduino sketch in
  `firmware/` to the RP2040 Arduino core. The shift register lines are on GPIO3 (latch), GPIO2 (data) and GPIO22 (clock).

## Not connected

RAW, and the Pro Micro pins not listed above, are left unconnected on purpose.

## Checks done on this revision

- **KiCad 9 DRC:** 0 violations and 0 unconnected items at every severity (with `HeliSR_Rev3.0.kicad_dru`).
- **Clearance:** nothing on the board comes closer than 0.200 mm to another net. Copper is at least 0.5 mm from the
  edge, and holes are at least 0.6 mm apart (edge to edge).
- **Netlist:** checked pad by pad against Rev 2.0 by `tools/verify_netlist_v3.py`. Every net other than the 16
  inputs is identical apart from the new parts: PROG1 is R1 + SW2 from AX1 to GND, and PROG4 is R2 + SW3 from AX4 to
  GND. Each input goes from the same connector pin as before through one pull-up to one shift-register input, and
  no input is used twice. The 74HC165 control pins, the chain (U1 QH → U2 SER, U1 SER to GND), the Pro Micro pins
  and the reset button are all as in Rev 2.0.
- **Ground pour:** 94 % of the pourable area on the front and all of it on the back is filled. The gaps left are
  slivers of 2.5 mm² or less between pads and tracks, and every island that remains is stitched to ground.
- **Decoupling:** each shift register's 100 nF cap has its VCC pad beside the chip's VCC pin (pin 16): measured
  centre to centre, C1's is 1.8 mm from U1's and C2's is 2.7 mm from U2's.
- **Mounting holes:** the ground pour stops 3.5 mm from each hole centre, the nearest pad, track or via is 3.57 mm
  from it, and the JST housings 4.1 mm. Everything clears the M3 nut's corners (3.18 mm) on the front and the 6.4 mm
  spacer on the back.
- **Silkscreen:** every label is 1.0 mm tall with a 0.16 mm stroke. The front carries the part references (the
  buttons are labelled RST, PROG1 and PROG4) and USB at the Pro Micro's USB end. Each label is outside every part's
  courtyard (at least 0.1 mm clear) and at least 0.45 mm from the next label. The back carries only the board name
  and revision. None comes within 3.6 mm of a hole centre, so none is under a nut or spacer. J1, J8, U2 and PROG4
  each print over a tented via.

## DRC rules

`HeliSR_Rev3.0.kicad_dru` covers the intentional overlaps. Each rule names the exact footprint pairs, so the same
checks still fire for anything else:

- Parts nested under the Pro Micro (resistor networks, shift registers and caps between the sockets).
- The connector fields. The JST courtyards along each edge overlap, but the housings are 1.2 mm apart.
- The M3 holes. Their courtyards (6.9 mm across) overlap the corner connectors' (J1, J14, J2, J12), but the part
  bodies are clear of the nut's corners (6.35 mm across).
- Library silkscreen outlines that touch where parts nest.

The rules use `(severity ignore)`, because `kicad-cli` 9.x still reports `(severity exclusion)` rules as errors
(KiCad issue 24264).

## Rebuilding

The board is generated, autorouted and finished by scripts in `tools/`, run with KiCad 9 (and Freerouting 2.5.0 on a
Java 25 runtime for the routing):

1. `gen_v3.py` places the parts, sets the nets, outline and mounting holes, and exports a DSN. The placement used
   here is `rev30_params.json`.
2. `route_v3.py` runs the generator, gives VCC/GND a 0.3 mm class, routes with Freerouting, imports the result
   (`imp_v2.py`) and DRCs it. It takes a list of placement variants; this board is
   the best of 8 tried for the three-button layout. With 0.5 mm between the connectors along each row (`row_gap`)
   every pour island can be stitched to ground; the tighter rows left islands of up to 21 mm² cut off on both
   sides. One router via (AX2) is nudged 0.09 mm (`nudge_vias.py`, listed in the placement) so every hole is at
   least 0.6 mm from the next.
3. `finish_all_v3.py` (any Python with shapely) pours GND, adds GND stitching vias (`stitch_export.py`,
   `stitch_place.py`), places the silk labels (`silk_export.py`, `silk_place.py`), writes the DRC rules
   (`finish_v3.py`), and DRCs the result.
4. `silk_fix_v3.py` (KiCad's Python) deletes every back label but the board name, sets every label to 1.0 mm with
   a 0.16 mm stroke, and moves each one to the nearest spot clear of every courtyard, pad opening and part outline.
   The search prefers upright text near the part it names, and avoids spots nearer another part or over a via.
5. `verify_netlist_v3.py` checks the netlist against Rev 2.0 and writes the input map. Rev 2.0's board file has
   since been removed from this folder, so restore `HeliSR_Rev2.0.kicad_pcb` before running this step again.
6. `export_v2.py` (any Python 3) writes `HeliSR_Rev3.0_Gerbers.zip` (Protel extensions, X2, job file, separate
   PTH/NPTH drill files in mm) and the two renders: KiCad SVG plots in the default colours, rasterised 1500 px wide by
   Microsoft Edge in headless mode.
7. `make_bom_v3.py` writes the full BOM, `make_board_bom_v3.py` the board BOM (it stops if the board's parts and
   its list disagree), and `fit_figure_rev3.py` draws the fit check in the head.

## Ordered files

These are the files of the board that was ordered from OSH Park. Their SHA-256 checksums let you check a copy
against the order. `SHA256SUMS.txt` lists every file in this folder.

| File | SHA-256 |
|---|---|
| `HeliSR_Rev3.0.kicad_pcb` | `f9aae27404272bbd14053b13542258cda9e641bc79a1633d5a4afcf2f9d423d8` |
| `HeliSR_Rev3.0_Gerbers.zip` | `7505c41f81fa5c9f4e06fdbbcfae35a1ab03944308fe8e0c85dd58d18a1d83b7` |

The folder's files are marked read-only (the KiCad session files `HeliSR_Rev3.0.kicad_prl` and `fp-info-cache`,
and KiCad's backup folder, are left writable so the board still opens). To unlock a file deliberately, clear its
read-only attribute (`attrib -R <file>`).

After the order, on 2026-10-22, the two BOMs and their scripts (`make_board_bom_v3.py`, `make_bom_v3.py`) got the
JST header prices from the Digi-Key cart. Nothing in the ordered design changed.

On 2026-10-22 the board BOM was reworded to make clear that OSH Park makes only the bare PCB, and its PCB line got
the order's price. The parts to solder on it come from Digi-Key. For ordering, `../../BOM/Heli_Collective_Final_BOM.xlsx`
supersedes both BOMs here: it covers the whole collective and has the Digi-Key order on its own sheet.
