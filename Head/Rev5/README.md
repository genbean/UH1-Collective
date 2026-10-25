# UH-1 "Huey" head, Rev 5: the real panel dimensions

Rev 5 is head Rev 4 ([`../Rev4`](../Rev4/README.md)) with the box and both panels cut to the real UH-1 panels' dimensions, measured off the user's drawing. The switches are moved to where the drawing has them, and everything is checked for collisions. The throttle, the friction knob, the starter trigger and its mount (with the M2 pull-stop seat), the leads' hole, the AS5600 pod and the 4-way hat work as in Rev 4. For them, and for the assembly steps, see Rev 4's README.

**Status:** designed and checked in CAD only. Nothing has been printed. The BOM in [`../../BOM`](../../BOM) still lists Rev 4.

![Rev 5's panels](renders/HueyHeadR5_Front.png)

## Dimensions

| | Rev 4 | Rev 5 (real panels) |
|---|---|---|
| Lower panel | 107 × 75 mm, 50 mm on the left | **85 mm wide, 69.01 mm tall on the right, 47.03 mm on the left** |
| Its bottom edge | 15 mm flat, diagonal, 25 mm flat | **13 mm flat, a 51.8 mm diagonal, 25 mm flat** |
| Upper panel | 67 × 50 mm, 20 mm in from the left | **55 × 41 mm, 15 mm in from each side** |
| Upper box set back from the lower panel | 10 mm | 5 mm (see below) |
| Box depth | 55 mm | 55 mm |

The tube stays centred across the lower box, at the same x as in Rev 4. The box is set at the height that puts the diagonal bottom under the tube where Rev 4's was, within 0.16 mm. So the neck, the knob, the grip, the gears and the trigger keep their places on the tube, and the 491 mm tube cut is unchanged.

## Switches

Positions are from the drawing, measured from each panel's top-left corner (u across, v down), in mm:

| Switch | Drawn | Rev 5 | Why it moved |
|---|---|---|---|
| GOV RPM INCR / DECR toggle | 13.4, 22.5 | 13.9, 22.5 | Its body clears the top-left panel-screw column by 0.4 mm |
| SEARCH CONT hat | 42.7, 14.2 | 42.5, 16.0 | At 14.2 its carrier's drum hits the lower box's top wall (13 mm³). It is centred over the tube, and the lower position leaves room for SEARCH CONT over its bezel |
| LDG LT FWD / DOWN toggle | 69.6, 22.5 | 69.6, 21.5 | Its lugs clear the AS5600 module's pin row better |
| STOP REL button (in the ENGINE IDLE ring) | 70.8, 49.9 | 70.8, 49.9 | |
| SL ON / STOW toggle (upper) | 11.2, 19.1 | 11.2, 19.1 | |
| LDG LT ON / OFF toggle (upper) | 39.3, 19.1 | 39.3, 19.1 | |

The labels follow the drawing too:
- GOV up the left edge, RPM beside the switch, INCR / DECR;
- SEARCH CONT over the hat, the L / R arrow and RETR under it;
- LDG LT, FWD / DOWN, and ON down the right edge;
- STOP REL;
- ENGINE and IDLE round the STOP REL button;
- SL, ON, STOW, LDG LT, ON, OFF, and OFF stacked between the upper toggles.

EXT is gone: there is no room for it between SEARCH CONT and the hat. The labels are 3 mm tall (Rev 4: 3.6 mm), and 2.3–2.6 mm in the ENGINE IDLE ring and for SEARCH CONT.

## What else changed to make it fit

| | |
|---|---|
| **Upper box** | Set back 5 mm instead of 10, so the upper toggles' 26 mm bodies end 2 mm in front of the HeliSR's Pro Micro. |
| **Upper panel screws** | The SL toggle is only 11.2 mm from the panel's left edge, so its body covers both left corners. The top-left screw moves to the top middle, between the toggles. Its column is only 26 mm deep, hanging from the top wall, so it stops short of the HeliSR board. The two bottom screws drop to 3 mm above the floor. |
| **HeliSR board** | The upper box is 38.5 mm tall inside, which is less than the board's 39.3 mm. The board's USB end now sits 1.4 mm down in the wire slot through the floor. It is still centred across the upper box. |
| **AS5600 module** | It is square to the box (Rev 4 turned it 15°, with the pinion). Turned, its way in from the front would come out through the narrower box's right wall. The chip is still centred over the magnet. |
| **Search hat cap** | 22 mm across (Rev 4: 28 mm), as on the real panel, with 9 terraces and a 2 mm plain side under them. That side keeps 1.4 mm of cap over the legs' sockets. The bezel, rocker plate, switches and carrier are Rev 4's. |
| **Lower box's upper-box joint** | The upper box reaches 1 mm down into the lower box's top wall, so the HeliSR's lower screw holes don't cut through a seam (that left the body's mesh open). |

## Collision check

`check_r5.py` builds every part in place and tests every pair that shouldn't touch:
- the body, both panels (with the hat's carrier), the trigger;
- the five toggles' and the STOP REL button's bodies, from their datasheets;
- the hat's four tact switches;
- the HeliSR board, its spacers, the parts on its face, the Pro Micro and its USB-C plug.

It also checks three more things:
- no cut in the neck block breaks out through a wall (only the bores' open bottom and the AS5600's way in out of the open front leave the solid);
- the module, in its grooves, clears every switch by 1 mm;
- the starter leads' 4 mm hole is open from the groove to the box, keeps 1.2 mm of wall all round, and comes out in the box's open inside.

All of it passes:

```
body x lower_panel                      0.00 mm3 OK
body x upper_panel                      0.00 mm3 OK
neck cuts outside the solid            -0.00 mm3 OK
leads hole open, groove to end     OK
leads hole 1.2 mm walls            OK
leads hole comes out in the box    OK
all clear
```

The throttle grip, friction collar, pinion and magnet shaft don't overlap the body either. The trigger swings clear the same way as in Rev 4.

Closest clearances:
- GOV body to the top-left screw column: 0.4 mm;
- hat drum to the lower box's top wall: 1.3 mm;
- the other switch bodies to the neck block: 0.5 mm (the block is cut 0.5 mm clear of them, as in Rev 4).

![Inside, with the switches (orange), the hat's tact switches (yellow), the HeliSR board and Pro Micro (green, blue) and the AS5600 module (purple)](renders/HueyHeadR5_Inside.png)

![The body](renders/HueyHeadR5_Body.png)

## Parts

`stl/` has the same parts as Rev 4, named `HueyHeadR5-*`. They print the same way: the body on its rear wall, with tree supports for the neck, the knob and the tube bore, and the panels face down. See [Rev 4's printing table](../Rev4/README.md#printing). The body is 147 cm³ (Rev 4: 166 cm³), the lower panel 16.6 cm³ and the upper panel 6.2 cm³.

The screws are Rev 4's, from the same two kits.

## Regenerating

From this folder, with the same Python packages as Rev 4:

```
python huey_head_r5.py stl
python throttle_r5.py ../source/MkII-Grip-bore-relieved-25mm.stl stl
python check_r5.py
```

The outline is set by `PANEL_W`, `PANEL_HR`, `PANEL_HL` and `DIAG_U`, and the upper box by `UX0`, `UX1`, `UZ1` and `UY`, at the top of `huey_head_r5.py`. The switch positions are `GOV`, `SEARCH`, `LDG_EXT`, `STOP_REL`, `SL` and `LDG_ON`, and the labels are in `lower_labels()` and `upper_labels()`.

## Not done yet

- Nothing is printed. The press-fit bore, the O-ring fits and the sensor seat still need their Rev 4 coupons.
- The base's balance (`Base/mk3_rev3.py`) still assumes an older head. Rev 5's body is about 19 cm³ lighter than Rev 4's.
- No 3D assembly model (`.glb`) yet. The friction knob is Rev 4's as of 2026-10-25. If Rev 4's knob changes again, copy `friction_knob()` across.
