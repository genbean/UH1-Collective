# MkIII base, Rev 4: narrow

Rev 4 is Rev 3 cut down to **82 mm (3.25 in)** wide along the pivot axis, against Rev 3's 130 mm, with the lever symmetrical about the tube. The strut, collar, tube, socket, down-stops, knob and fits are Rev 3's. What changes is everything along the pivot axis, and the brake, which moves behind the hub.

It's a concept: nothing has been printed. Print the [fit-test coupons](#fit-test-coupons) for the new bearings first.

![Rev 4 from the front](renders/rev4_hero.png)

![Rev 3 and Rev 4 from above, to the same scale](renders/rev4_vs_rev3_top.png)

![From behind: the brake knob, and the USB cable leaving the cable cover](renders/rev4_rear.png)

![At the 32° up-stop](renders/rev4_32deg.png)

## What changes from Rev 3

- **Lever:** the hub is 43 mm long (Rev 3: 64), centred on the tube. The tube's plane moves from 9 mm off-centre to the middle. Rev 3's friction drum is gone.
- **Bearings:** 6808-2RS thin-section bearings, 40 × 52 × 7 mm, in place of the 6006-2RS (30 × 55 × 13). The trunnions grow to 40 mm across to suit.
- **Pillow blocks and caps:** 9 mm wide (Rev 3: 17). The caps are held by M3 screws, because Rev 3's M4 heads don't fit in 9 mm.
- **Sensor:** the AS5600 board sits inside the sensor trunnion's end, so the side covers are 9.5 mm deep (Rev 3: 15).
- **USB cable:** it leaves through a notch in the cable cover's rim instead of a spout.
- **Brake:** a narrow, tall shoe presses on the back of the hub, set by the MkII knob on the back of a tower on the frame.
- **Up-stop:** two lugs under the back of the hub, one each side of the shoe, land on a pad further back than Rev 3's.
- **Frame gussets:** 45° gussets at all four corners of both pillow blocks, tying them to the webs behind and the down-stop pillars in front.

The base is longer front to back: the plate is 136 mm long (Rev 3: 116) and the knob stands 35 mm out behind it.

## Files

| | |
|---|---|
| `mk3_rev4.py` | the model. `python mk3_rev4.py` writes `stl/`, `stl/ref/` and `step/`; `--check` runs the interference checks; `--coupons` writes `stl/coupons/` |
| `make_renders_r4.py` | the renders and `renders/MkIII_Rev4_Assembly.glb` |
| `stl/` | the printed parts |
| `stl/ref/` | bought parts and hardware, for reference |
| `step/MkIII_Rev4_assembly.step` | the whole base |

Both scripts import Rev 3's (`../mk3_rev3.py`, `../make_renders_r3.py`) and need CadQuery; the renders also need trimesh, manifold3d and pyvista.

## Fit-test coupons

The trunnion and bearing seat are new sizes, so print these before the lever and frame. They're Rev 3's coupons, sized for the 6808, read the same way: see [Rev 3's coupon notes](../README.md#fit-test-coupons-print-these-before-the-big-parts).

| File | What it is | Change |
|---|---|---|
| `stl/coupons/coupon_trunnion_6808.stl` | 8 mm trunnion stubs on the inner-race shoulder, 39.9 / 40.1 / 40.3 mm | `TRUN_OD += step` |
| `stl/coupons/coupon_bearing_seat_6808.stl` | the pillow block's seat and 2 mm lip, 51.9 / 52.1 / 52.3 mm | `BRG_SEAT_D += step` |

`0` comes from how Rev 3's bearings fitted as built:
- **Seat:** +0.1 on the race's outside was a perfect fit, so it stays.
- **Trunnion:** +0.2 on the race's bore pressed on a hair too tight, so Rev 4 uses +0.1 (40.1 mm).

The tube socket is unchanged, so Rev 3's socket fit stands.

## Across the pivot axis

From the middle out, each side:

| | \|y\|, mm | |
|---|---|---|
| Hub | 0 – 21.5 | 60 mm across; 3.5 mm past the socket boss |
| Bearing | 22.5 – 29.5 | 6808-2RS |
| Retaining lip | 29.5 – 31.5 | the pillow block's outer face is at 31.5 |
| Trunnion end | 32.0 | 40.2 mm across |
| Side cover | 31.5 – 41.0 | 2.5 mm floor |

## Lever

Two halves split at the pivot axis, as Rev 3, joined by four M4 socket head cap screws from the top into nuts in the lower half. The screws are 16.25 mm either side of the tube:
- **Front pair, x = −17:** M4 × 40, as Rev 3. Each hole is 1.35 mm from the socket.
- **Back pair, x = +10** (Rev 3: +17): M4 × 50, so their nut pockets clear the up-stop lugs. Each hole is 1.3 mm from the axial cable bore.

Each counterbore is 1.25 mm from the hub's end. The bores, the down-stop pads, the hose-clamp groove and the socket for the uncut 500 mm tube are all Rev 3's. The top gusset over the socket stops at x = 2 (Rev 3: 8), so it clears the brake shoe at 32°.

## Sensor

The AS5600 module (WWZMDiB, 23 × 23 mm) sits in a square pocket in the sensor trunnion's end, chip facing out, its front face level with the trunnion's end. There's no carrier.

- **The pocket:** 23.54 mm square (the board is 0.915 in, 23.24 mm, as measured, plus 0.15 mm a side) and 1.6 mm deep for the board. The board rests on two 1.6 mm ledges along its top and bottom edges, clear of both pad columns.
- **Behind the board:** 3.5 mm of space for the wires soldered in from the back and the DIR jumper. It opens into the axial bore, which takes the lead to the tube.
- **Orientation:** set it in with the pad columns vertical. It fits either way up.
- **Holding it:** a dot of hot glue in two corners. Nothing else holds it in.

The magnet (4 × 2 mm, in Rev 3's 4.2 mm pocket) is on a post from the sensor cover's floor, 1.0 mm off the chip, as in Rev 3. The wiring and the module's changes (R1 off, DIR to VCC, R4 off for I²C) are exactly as in [Rev 3](../README.md#sensor).

## USB cable

The cable comes out of the trunnion on the axis and turns toward the back inside the cable cover, on a 4 mm radius (Rev 3: 6). It leaves through a hole in the cover's rim. A 4.8 mm notch runs from that hole to the face that seats on the block, so the cover goes on over a cable that's already through the lever, as Rev 3's does.

## Brake

![Section on the tube's plane](renders/rev4_section_brake.png)

The shoe is 12 mm wide and 44 mm tall (Rev 3's was 30 wide), with felt on its curved face. It presses on the hub's own cylinder, ±44° either side of the axis, from behind.

- **The tower:** the shoe slides fore and aft in a pocket in a tower on the frame's back edge. The tower is 20 mm wide, and the shoe sits in it with 0.3 mm clearance all round.
- **The knob:** the MkII knob lies on its side on the back of the tower. It turns Rev 3's M5 × 30 hex bolt through an M5 nut, which slides into the tower from the top.
- **The spring:** the bolt's tip pushes a printed spring cap in the shoe's back. Rev 3's 10 mm spring sits under it, still 6.5 mm long when fitted, and pushes the shoe.
- **Using it:** screw the knob in for more drag. There's 3 mm between the knob and the tower.

**The shoe stands back while the lever goes in.** It wraps the hub above the hub's widest point, so with the shoe on the hub, the lever can't be lowered into its bearing seats. The pocket runs 10.5 mm behind the shoe. Back the knob out about 11 mm, push the shoe back, and the lever drops in clear. The check lowers the lever in from 80 mm up and finds it clear with 9 mm or more.

## Up-stop

![The shoe between the two up-stop lugs, at 0°](renders/rev4_brake_lugs.png)

Two lugs under the back of the hub land on a pad on the frame at 32°. Each lug is 10 mm wide (|y| 11 to 21), with 22 mm between them for the shoe and the brake tower.

**Where the pad is:** further back than Rev 3's pedestal, x = 14 to 29.5, the full width between the pillow blocks. Its back middle (x over 24, |y| under 11) is cut away, clear of the shoe. Its top is at z = −28.5, 2 mm under the hub at its front edge.

**Where the lugs land:** x = 15 to 24.4. They can't land further back: the further back a lug lands, the further back it swings at 0°. These come to x = 35.8 at 0°, 1.2 mm off the webs behind the pillow blocks.

At 0°, the shoe's lower end and the brake tower sit between the lugs. As the lever lifts, the lugs swing down either side of the shoe onto the pad. Between them, the hub is a plain cylinder for the felt to run on.

![At 32°, the lugs on the pad (frame hidden)](renders/rev4_brake_lugs_32deg.png)

The anchor clevis's back wall now runs level, at the cheeks' top, into the pad's front face.

## Frame gussets

![The frame from above: the up-stop pad and the eight corner gussets](renders/rev4_frame_top.png)

Each pillow block has a 45° gusset at each corner, 8 mm along each wall:
- **Behind, outside:** the block's back face to the outer face of the web running back to the brake tower, up to the web's top. The cap screws' nut slots run out through its sloping face.
- **Behind, inside:** the block's inner face to the web's front face. Its top is cut back to stay 1.5 mm outside the up-stop lugs' swing.
- **In front, inside:** the block's inner face to the down-stop pillar's back face, up to the pillar's top, 3 mm clear of the hub.
- **In front, outside:** the block's front face to the pillar's outer face, up to the pillar's top.

## Down-stop and strut

These are unchanged from Rev 3: pads on the socket boss land on two pillars at 0°, and the gas strut runs from a clevis on the frame to the collar on the tube. Everything is on the new centre line. Each pillar runs on into its pillow block.

## Printing

- **Frame:** plate down, as Rev 3. The shoe's pocket is open at the front; its roof bridges 12.6 mm.
- **Lever halves:** on their joint faces, as Rev 3. The sensor pocket's roof bridges 23 mm in each half.
- **Shoe:** stand it on its back face. The spring's bore opens on the bed, and the curved face is on top.
- **Spring cap:** on its flat front face, dimple up.
- **Side covers:** outer face down. The magnet's post and pocket, and the cable cover's notch, open upward.
- **Caps:** on their joint face.
- **Strut collar and knob:** Rev 3's, unchanged. Reuse them.

## Assembly

1. **Frame:** tap the eight M3 cover holes, in the pillow blocks and the caps, 7.5 mm deep. Slide an M3 nut into each of the four slots in the blocks' front and back faces. Slide the M5 nut into the tower's slot from the top.
2. **Brake:** glue the felt onto the shoe's face. Drop the spring into the shoe's bore, then the spring cap. Slide the shoe into the tower's pocket from the front and push it all the way back. Drop the M5 × 30 bolt into the knob's hex pocket, head down, and screw it into the nut until it just touches the cap.
3. **Lever:** press the four M4 nuts into the lower half's pockets. Lay the USB cable and the sensor lead into its channels, close the upper half, and fit the cap screws: M4 × 40 at the front, M4 × 50 at the back. Press the bearings onto the trunnions.
4. **Sensor:** solder the module to the lead, as in Rev 3, and set it in the trunnion's pocket, chip out, with a dot of hot glue.
5. **Into the frame:** lower the lever's bearings into the seats, past the shoe, and fit the caps (M3 × 20, into the slotted nuts).
6. **Brake:** screw the knob in until the shoe meets the hub, then set the drag.
7. **Covers:** fit the sensor cover, with the magnet in its post. Lay the USB cable into the cable cover's notch, push the cover onto the block, and screw both down (M3 × 16).
8. **Strut and tube:** as Rev 3.

## Screws

All from the same kits as Rev 3: the AvrestYPT countersunk kit (M3 and M4 × 8, 12, 16, 20, with nuts) and the HELIFOUNER M4 × 30–50 socket head kit. The NIULUNBAO M3 set isn't needed: the covers' M3 × 16s are in the AvrestYPT kit.

| Where | Screw | Into | Qty |
|---|---|---|---|
| Lever halves, front | M4 × 40 socket head cap, from the top | M4 nut in a pocket in the lower half | 2 |
| Lever halves, back | M4 × 50 socket head cap, from the top | M4 nut in a pocket in the lower half | 2 |
| Pillow-block caps | M3 × 20 countersunk, from the top | M3 nut slid into a slot in the block's front or back face | 4 |
| Side covers | M3 × 16 countersunk, from the cover's outer face | M3 thread tapped 7.5 mm deep in the block or cap | 8 |
| Brake | **M5 × 30 hex-head bolt (Rev 3's)**, head on the floor of the knob's hex pocket | M5 nut slid into the tower from the top | 1 |
| Strut eyes | M4 × 16 countersunk, head on the +y side | M4 nut in the far cheek's pocket | 2 |
| Strut collar clamp | M4 × 12 countersunk | M4 nut in the other ear's pocket | 2 |

Rev 3's shoe hinge screw is gone.

![Screws from above and behind](renders/rev4_screws_top.png)

![Screws on the sensor side](renders/rev4_screws_sensorside.png)

![Screws on the USB side](renders/rev4_screws_usbside.png)

## Bought parts

| Part | Qty | Notes |
|---|---|---|
| **6808-2RS thin-section ball bearing (40 × 52 × 7)** | 2 | new for Rev 4 |
| X AUTOHAUX 6" 45 N gas strut | 1 | Rev 3's |
| 25 × 23 mm carbon tube, 500 mm | 1 | Rev 3's, uncut |
| Worm-drive hose clamp, about 25–40 mm | 1 | Rev 3's |
| Compression spring, 10 mm OD | 1 | Rev 3's |
| Felt, 1.5 mm, about 11 × 48 mm | 1 | on the shoe |
| AS5600 module (WWZMDiB) | 1 | Rev 3's, with its magnet |
| #10 × 1-1/2 in wood screws | 4 | desk mounting |

## Notes

- **The checks:** `python mk3_rev4.py --check` tries every pair of parts at 0°, 8°, 16°, 24°, 31.5° and 32°, and it's clean. The overlaps it allows are the intended ones: screws in their holes, the bearings' inner races on the trunnions, the felt on the shoe, the spring and cap, the strut's tabs in their clevises, and the hose clamp in its groove. Just past each stop, the lever meets the frame where it should: the pads on the pillars below 0°, both lugs on the up-stop pad above 32°. It also lowers the lever in past the stood-back shoe.
- **Chamfers:** Rev 3's chamfer step once returned a valid frame with the down-stop pillars missing. Rev 4's version refuses any set of chamfers that takes off more than chamfers could. Rev 3's parts were checked, and none of them lost anything.
- **Brake feel:** the felt patch is about 11 × 48 mm (Rev 3's drum shoe was wider and shorter). The spring and knob are the same, so the range of drag should be similar, but it's untested.
- **Balance:** the strut, collar, tube and head are unchanged. The lever is about 68 cm³ lighter, mostly near the pivot, so the balance should be close to Rev 3's. It hasn't been recalculated.
- **Sensor pocket:** sized for the measured board, 0.915 in (23.24 mm), with 0.15 mm a side.
