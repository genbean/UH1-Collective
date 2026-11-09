# MkIII base, Rev 4: narrow

Rev 4 is Rev 3 cut down to **82 mm (3.25 in)** wide along the pivot axis, against Rev 3's 130 mm, with the lever symmetrical about the tube. One shell over the top encloses the lever, in place of Rev 3's two bearing caps. The strut, collar, tube, socket, down-stops and fits are Rev 3's. What changes is everything along the pivot axis, the enclosure, and the brake, which moves behind the hub.

This is the current base. It hasn't been printed yet: print the [fit-test coupons](#fit-test-coupons) first.

![Rev 4, exploded](renders/rev4_exploded.png)

![Rev 4 from the front](renders/rev4_hero.png)

![Rev 4 with the shell off](renders/rev4_open.png)

![Rev 4 straight down from above, to scale](renders/rev4_top.png)

![Rev 3 and Rev 4 from above, to the same scale](renders/rev4_vs_rev3_top.png)

![From behind: the brake knob in the shell's top, and the USB cable leaving the cable cover](renders/rev4_rear.png)

![At the 32° up-stop](renders/rev4_32deg.png)

## What changes from Rev 3

- **Lever:** the hub is 43 mm long (Rev 3: 64), centred on the tube. The tube's plane moves from 9 mm off-centre to the middle. Rev 3's friction drum is gone.
- **Bearings:** 6808-2RS thin-section bearings, 40 × 52 × 7 mm, in place of the 6006-2RS (30 × 55 × 13). The trunnions grow to 40 mm across to suit.
- **Frame:** 9 mm pillow blocks (Rev 3: 17). The base plate stops at their outer faces, so it's 63 × 127 mm (Rev 3: 100 × 116), with no wings or gussets out beside it. A front wall under the shell's carries its cut for the lever on down, so the two read as one piece.
- **Shell:** one box over the lever, in place of the two caps, slotted for the tube. Four M4 × 50 socket head screws hold it to the pillow blocks, and a diamond grid in the joint locates it.
- **Sensor:** the AS5600 board sits inside the sensor trunnion's end, so the side covers are 9.5 mm deep (Rev 3: 15).
- **USB cable:** it leaves through a notch in the cable cover's rim instead of a spout.
- **Brake:** a felt-lined strap wraps the back of the hub, hinged at its bottom in the up-stop pad. A knob on top of the shell pulls it on, through a bolt that leans 30° forward.
- **Up-stop:** two lugs under the back of the hub, one each side of the strap, land on a pad further back than Rev 3's.
- **Frame gussets:** 45° gussets at all four corners of both pillow blocks.
- **Strut anchor:** moved up and back, so the 45 N strut as bought balances the lever. Rev 3's first anchor was sized for a 40 N strut, so the 45 N strut pushed the lever up. Rev 3 now has the same anchor.

The knob stands on top of the shell, leaning 30° forward; nothing sticks out behind the back face.

## Files

| | |
|---|---|
| `mk3_rev4.py` | the model. `python mk3_rev4.py` writes `stl/`, `stl/ref/` and `step/`; `--check` runs the interference and assembly checks; `--coupons` writes `stl/coupons/` |
| `make_renders_r4.py` | the renders, screw maps, exploded view and screw chart, `renders/MkIII_Rev4_Assembly.glb`, and the complete collective with head Rev 5 in [`../../renders`](../../renders) |
| `stl/` | the printed parts |
| `stl/ref/` | bought parts and hardware, for reference |
| `step/MkIII_Rev4_assembly.step` | the whole base |

Both scripts import Rev 3's (`../mk3_rev3.py`, `../make_renders_r3.py`) and need CadQuery; the renders also need trimesh, manifold3d and pyvista.

## Fit-test coupons

The trunnion and bearing seat are new, so print these before the big parts. They're made and read like [Rev 3's coupons](../README.md#fit-test-coupons-print-these-before-the-big-parts).

| File | What it is | Good fit | Change |
|---|---|---|---|
| `stl/coupons/coupon_trunnion_6808.stl` | 8 mm trunnion stubs on the inner-race shoulder, 39.9 / 40.1 / 40.3 mm | the race presses on firmly, no wobble | `TRUN_OD += step` |
| `stl/coupons/coupon_bearing_seat_6808.stl` | the seat and 2 mm lip, 51.8 / 52.0 / 52.2 mm | the race goes in with thumb pressure | `BRG_SEAT_D += step` |

The bearing coupons' `0` comes from how the bearings fitted as built:
- **Seat:** +0.1 on the race's outside was a perfect fit in Rev 3's one-piece blocks. In Rev 4's seat, split between the frame and the shell, it left the bearing a little play, so the seat is now 52.0 mm, the race's own size. The seat coupon is one piece, so it can't show the split: check the play in the frame and shell themselves.
- **Trunnion:** +0.2 on the race's bore pressed on a hair too tight, so Rev 4 uses +0.1 (40.1 mm).

The tube socket is unchanged, so Rev 3's socket fit stands.

## Across the pivot axis

From the middle out, each side:

| | \|y\|, mm | |
|---|---|---|
| Hub | 0 – 21.5 | 60 mm across; 3.5 mm past the socket boss |
| Bearing | 22.5 – 29.5 | 6808-2RS |
| Retaining lip | 29.5 – 31.5 | the pillow blocks' and the shell's outer faces, and the plate's edge, are at 31.5 |
| Trunnion end | 32.0 | 40.1 mm across |
| Side cover | 31.5 – 41.0 | 2.5 mm floor; it overhangs the plate |

## Shell

![Section on the pivot axis, from the front](renders/rev4_section_axis.png)

The shell is a box over the lever: 75 mm long, 63 mm wide and 38 mm tall, from the pillow blocks' tops. It replaces Rev 3's two caps.

- **Side walls:** solid, 9 mm thick. These are the caps. Each holds the bearing's upper half-seat and lip, and two of the cover's screw holes. Two M4 × 50 socket head screws per side go down through them from the top, each centred on the joint, heads down 13 mm counterbores, into M4 nuts in the pillow blocks (see [The joint](#the-joint)).
- **Front, back and top walls:** 3 mm thick.
- **Tube slot:** one clean opening in the front and top, the same outline as the frame's front wall below it (see [The joint](#the-joint)). It holds the socket boss, the tube, the lever's fairings and the down-stop pads through their whole swing, 0° to 32°, with at least 1 mm all round.
- **Behind the hub:** solid, from 2 mm off the hub out to the side walls, the top and the back face, so the brake knob's seat, sunk into the top, bears straight into the walls. The brake strap's bay is under the seat (see [Brake](#brake)).
- **Assembly:** it drops straight down over the lever and the strap, the slot and the strap's bay both open at the bottom.

## The joint

![The frame's half of the joint: the knurl on every land, both sides of the bearings](renders/rev4_joint_grid.png)

The frame and the shell meet on one flat plane through the pivot axis, which also splits the bearing seats.

- **Screws:** four M4 × 50 socket head cap screws from the lever's HELIFOUNER kit, two per side, 30.5 mm either side of the axis, down the middle of the shell's 9 mm side walls (y = ±27). Each is centred on the joint: its head seats 25 mm above it, at the floor of a 13 mm counterbore, and its tip is 25 mm below. Each goes into an M4 nut slid into a slot in the pillow block's outer face, about 21–24 mm under the joint. The slots open just below the side covers' rim. The nut sits flats-in: its inner flat stops it turning when you tighten the screw. The counterbore leaves 0.9 mm of shell either side, and the nut's slot leaves 0.9 mm of block to its inside face.
- **Diamond knurl:** the whole face the frame and the shell share is knurled.
  - **Shape:** square pyramids 2.4 mm across their corners and 0.7 mm tall with flat tops, on a diamond grid with 0.6 mm flat lanes. They stand on the frame's half and fit into sockets in the shell's half, 0.1 mm clear on their 45° flanks and 0.2 mm deeper than the pyramids. The flat faces still close on each other, so the bearing seats close, and the knurl stops the shell sliding fore and aft or sideways as the screws pull it down.
  - **Coverage:** it runs over every land, in front of the bearings and behind them, and on across the solid frame behind the pillow blocks. It stops 0.5 mm short of every edge and hole: pyramids at its edge are cut off square, and any piece smaller than a third of a pyramid is left out. The grid is the same mirror image either side of the tube, and fore and aft on the pillow blocks.
  - **Printing:** neither half needs supports: the pyramids point up on the frame, and the sockets open upward on the shell, which prints top down.
- **Front opening:** the frame has a 3 mm front wall between the pillow blocks, under the shell's, and one clean opening runs through both. It has straight sides 21 mm either side of the tube (the down-stop pads, 1 mm clear) from the top down to 7 mm under the pivot axis, and a round bottom of the same radius below that: the lever's lower fairing swings down to 24.5 mm under the axis in the walls' plane. On top it carries on as one slot, as wide at the front, narrowing at 45° to 12.5 mm either side of the tube for the upper fairing, and ending round just behind the hub's top. Both contain the lever's whole sweep, 1 mm clear or more. Below the opening, a smooth round-ended slot lets the strut's cylinder through, 1.5 mm clear over the whole travel. It's cut by the cylinder swung about its anchor pin, so it has no facets.
- **Hex-key hole:** a 3.5 mm hole through the USB-side (+y) pillow block, on the strut anchor screw's axis, just below the side cover's rim. A 2.5 mm hex key goes straight in to the M4 × 16's head.

![The front: the frame's wall carries on the shell's cut for the lever](renders/rev4_front.png)

## Lever

Two halves split at the pivot axis, as Rev 3, joined by four M4 × 40 socket head cap screws from the top into nuts in the lower half. They're where Rev 3 has them: x = ±17, symmetrical fore and aft, 16.25 mm either side of the tube. The front pair's holes are 1.35 mm from the socket.

Each counterbore is 1.25 mm from the hub's end. The bores, the down-stop pads, the hose-clamp groove and the socket for the uncut 500 mm tube are all Rev 3's.

**Fairing:** in place of Rev 3's 8 mm top gusset, a fairing 21 mm wide runs over the socket boss on the upper half, and the same one mirrored under it on the lower half. It starts at the hose-clamp groove's back edge. Its top is one straight line from the boss's top there to the hub, tangent to the hub's circle, so it runs into the hub without a corner. Its long top edges are rounded 3 mm. It stays 1.75 mm clear of the front screws' counterbores on top and 1.6 mm clear of their nut pockets underneath.

![The lever from the side: the fairings top and bottom, tangent to the hub](renders/rev4_lever_side.png)

![The lever from the front and above: the upper fairing between the front screws](renders/rev4_lever_top.png)

![The lever's screws, with the shell off](renders/rev4_screws_lever.png)

## Sensor

The AS5600 module (WWZMDiB) sits in a square pocket in the sensor trunnion's end, chip facing out, its front face level with the trunnion's end. There's no carrier.

- **The pocket:** 23.54 mm square (the board is 0.915 in, 23.24 mm, as measured, plus 0.15 mm a side) and 1.6 mm deep for the board. The board rests on two 1.6 mm ledges along its top and bottom edges, clear of both pad columns.
- **Behind the board:** 3.5 mm of space for the wires soldered in from the back and the DIR jumper. It opens into the axial bore, which takes the lead to the tube.
- **Orientation:** set it in with the pad columns vertical. It fits either way up.
- **Holding it:** a dot of hot glue in two corners. Nothing else holds it in.

The magnet (4 × 2 mm, in Rev 3's 4.2 mm pocket) is on a post from the sensor cover's floor, 1.0 mm off the chip, as in Rev 3. The wiring and the module's changes (R1 off, DIR to VCC, R4 off for I²C) are exactly as in [Rev 3](../README.md#sensor).

## USB cable

The cable comes out of the trunnion on the axis and turns toward the back inside the cable cover, on a 4 mm radius (Rev 3: 6). It leaves through a hole in the cover's rim. A 4.8 mm notch runs from that hole to the face that seats on the block, so the cover goes on over a cable that's already through the lever, as Rev 3's does.

## Brake

![Section on the tube's plane](renders/rev4_section_brake.png)

A rigid printed strap wraps the back of the hub between the up-stop lugs, from 40° below the axis to 24° above it. It's 18 mm wide and 8 mm deep, lined with 1.5 mm felt, and hinged at its bottom end in the up-stop pad, just behind the strut's clevis. Its top end is a solid head with an M5 nut in it. The knob sits on top of the shell and draws the head up and forward, so the strap swings about its hinge and the felt clamps the hub.

- **The pull:** the knob's M5 × 35 bolt leans 30° forward from vertical, which gives it 41 mm of leverage about the hinge. A vertical bolt there would get 12 mm, and would mostly stretch and bend the strap instead of closing it. 30° is as far as it can lean with the seat sunk into the shell's top and 2 mm or more of shell between the seat and the hub.
- **Gussets:** the head is one solid gusset, from the band's top 12°, front and back, out to where the bolt pulls. Another runs from the band's bottom 12° down to the hinge's knuckle. Neither end is a thin tab.
- **The hinge:** the knuckle sits in a slot through the up-stop pad, 0.5 mm clear either side. The slot guides it, so the strap stays at least 1.5 mm off each lug (2 mm when centred). The pin, an M4 × 50 socket head, goes through both pillow blocks and the pad, head in a counterbore on the USB (+y) side, nut in a hex pocket on the sensor (−y) side.
- **The nut:** it drops into a slot in the head from the strap's +y side. The bolt holds it there, and its pull bears it on the slot's face. A lead-in in the head's face guides the bolt's tip onto it.
- **The knob's seat:** sunk into the shell's top, square to the bolt. There's 4 mm of shell under it, then the strap's bay.
- **The spring, if you want one:** the knob has a 10.6 mm pocket, 7 mm deep, in its underside. Without a spring, the knob sits on its seat and pulls the strap directly. With one (10 mm OD, 10 to 15 mm free length, such as Rev 3's), the spring holds the knob off its seat and the knob sets the brake through it. The M5 × 35 keeps its full thread in the nut either way.
- **The bay:** 22 mm wide, out to the lugs' inner faces, in the frame and the shell. In the frame, the strap leans back on its own onto the bay's back wall, at 4°: far enough for the lever's hub to drop past it. In the shell, the back of the bay is a ramp parallel to the bolt, 1 mm behind the head. As the shell goes on, the ramp meets the leaning strap's head and swings it forward onto the hub, so its nut lands on the bolt's axis.

**Drag:** about 10 N·mm per newton of bolt tension with the lever moving up, and 11 moving down; the strap is self-energising by about 9%. 26 N of tension gives the old shoe's 270 N·mm.
- **With the spring:** the brake's range is spread over about 10 turns of the knob, up to the spring's 20 N or so. Past that, the knob is down on its seat and the brake firms up.
- **Without it:** the felt is the only give, so the brake goes from free to firm within about a turn.

**Strength:** checked at 400 N of bolt tension, more than a hand gets out of an 18 mm knob (about 130–210 N at 0.3–0.5 N·m).
- **Strap:** it prints on its side, so all its bending runs along its layers (35 MPa allowed). The band peaks at 22 MPa, the neck under the head at 21, and the arm to the hinge at 10.
- **Hinge:** the knuckle bears 7.5 MPa on its pin. The pin carries 540 N, at 214 MPa in its 12.9 steel.
- **Shell:** the 4 mm floor under the seat bends at 17.5 MPa, along its layers. The shell is solid behind the hub, out to its side walls, top and back, so the seat's load goes straight into the walls.

![At the 32° stop](renders/rev4_section_brake_32deg.png)

## Up-stop

![The brake strap between the two up-stop lugs, at 0°](renders/rev4_brake_lugs.png)

Two lugs under the back of the hub land on a pad on the frame at 32°. Each lug is 10 mm wide (|y| 11 to 21), with 22 mm between them for the brake strap.

**Where the pad is:** x = 14 to 29.5, the full width between the pillow blocks, with a slot in its middle for the brake strap's knuckle. Its top is at z = −28.5, 2 mm under the hub at its front edge.

**Where the lugs land:** x = 15 to 24.4. They can't land further back: the further back a lug lands, the further back it swings at 0°. These come to x = 35.8 at 0°. Behind them the frame is cut away on a 39 mm radius round the axis, 1.5 mm clear of their swing.

At 0°, the strap's arm and knuckle sit between the lugs, 2 mm clear of each. As the lever lifts, the lugs swing down either side of the strap onto the pad. Between them, the hub is a plain cylinder for the felt to run on.

![At 32°, the lugs on the pad (frame and shell hidden)](renders/rev4_brake_lugs_32deg.png)

The anchor clevis's back wall runs level, at the cheeks' top, into the pad's front face.

## Frame

![The frame from above](renders/rev4_frame_top.png)

The plate is 63 mm wide, the pillow blocks' outer faces, and 127 mm long. The desk screws are 24 mm either side of the middle, past the blocks' ends and the down-stop pillars.

Behind the up-stop pad, the frame is solid back to its back face and out to the [back chamfer](#the-back), except for a 39 mm radius round the axis between the pillow blocks, 1.5 mm clear of the up-stop lugs' swing, and the brake strap's bay in the middle.

Each pillow block also has a 45° gusset at its front corners, 8 mm along each wall:
- **In front, inside:** the block's inner face to the down-stop pillar's back face, up to the pillar's top, 3 mm clear of the hub.
- **In front, outside:** the block's front face to the pillar's outer face, up to the pillar's top.

The down-stop and strut are unchanged from Rev 3: pads on the socket boss land on two pillars at 0°, and the gas strut runs from a clevis on the frame to the collar on the tube. Everything is on the new centre line. Each pillar runs on into its pillow block.

## The back

![From behind: the back chamfers and the brake knob](renders/rev4_back.png)

The frame and the shell share one 45° chamfer plane each side. It runs from the pillow blocks' outer back corners to the back face, at x = 52.5 (|y| + x = 69 mm), so from behind the two read as one block. The back face is 33 mm wide. The edges in the joint aren't chamfered, so no groove shows at the seam.

## Balance

![Out of balance at the grip, against lever angle](renders/strut_balance_r4.png)

Rev 3 was first built with the anchor at x = −12, z = −40.5, sized for a 40 N strut: the bottom of the range the 45 N strut is sold as. The 45 N strut as bought lifted the lever, by about 50 to 70 g at the grip.

The anchor is now at x = −9.5, z = −36.5, in Rev 4 and in Rev 3's updated frame: 4 mm up and 2.5 mm back. The strut's line passes closer to the pivot, so it has less leverage. It now balances 45 N to within 3 g at the grip over the whole travel. The strut is 119 mm long at 0° and 140 mm at 32°, inside its 102–152 mm stroke.

The strut is fitted cylinder down, as built: its cylinder (0.475 in, 12.07 mm, measured) on the anchor clevis, and its rod on the collar. The frame is cut 1.5 mm clear of the cylinder's sweep, through the front wall and over the clevis's front gussets.

| Strut force | Out of balance at the grip | Fix |
|---|---|---|
| 40 N | −58 to −50 g (drops) | — |
| **45 N (as bought)** | **−3 to +2 g** | none |
| 50 N | +49 to +60 g (rises) | about 42 g of ballast in the head |
| 53 N (top of the range) | +79 to +95 g | about 68 g of ballast |

The collar still fine-tunes: 8 mm toward the pivot adds about 21 g of lift at the grip, and 8 mm away takes 21 g off.

**The clevis:**
- **Cheeks:** they're 6.5 mm round the eye (Rev 3: 8), so they stay 1.5 mm under the hub.
- **Back walls:** they run 2 mm under the hub into the up-stop pad. Behind the tab, from 1 mm past its round end, the gap between them is filled, so they print as one solid block with proper infill.
- **Screw:** the strut's M4 × 16 still fits.

`python mk3_rev4.py --balance` prints the table and redraws the plot. It uses Rev 3's model: Rev 4's lever halves and Rev 3's estimate of the head (368 g). If your head is lighter than that, the strut will still lift a little. Slide the collar away from the pivot, or add ballast.

## Printing

- **Frame:** plate down, as Rev 3. The brake strap's slot and bay open at the top, the grid's pyramids point up, and the front wall builds straight up.
- **Shell:** top down. The bearing half-seats, the slot, the strap's bay and the grid's sockets all open upward. The knob's seat is on the bed, and its floor slopes at 30°: support it from the bed, in the seat only.
- **Lever halves:** on their joint faces, as Rev 3. The sensor pocket's roof bridges 23 mm in each half.
- **Brake strap:** on its side, the nut's slot up. Its bending then runs along the layers. No supports.
- **Side covers:** outer face down. The magnet's post and pocket, and the cable cover's notch, open upward.
- **Knob:** as Rev 3's, underside down. Reprint it: its floor is now 11 mm up, and it has a pocket underneath for the spring.
- **Strut collar:** Rev 3's, unchanged. Reuse it.

## Assembly

1. **Frame and shell:** tap the eight cover-screw holes M3, four in the pillow blocks and four in the shell's side walls. The pilot holes go right through the 9 mm walls. Slide an M4 nut into each of the four slots in the blocks' outer faces, two per side, and push it home over the screw hole.
2. **Lever:** press the four M4 nuts into the lower half's pockets. Lay the USB cable and the sensor lead into its channels, close the upper half, and fit the four M4 × 40 cap screws. Press the bearings onto the trunnions.
3. **Sensor:** solder the module to the lead, as in Rev 3, and set it in the trunnion's pocket, chip out, with a dot of hot glue.
4. **Brake strap in:** stick the felt (16 × 33 mm) on the strap's face, and drop the M5 nut into the slot in its head. Set the strap down into the frame with its knuckle in the up-stop pad's slot. Push an M4 × 50 socket head through from the USB (+y) side, through the pillow block, the pad and the knuckle, into an M4 nut in the sensor side's hex pocket. Tighten it: the strap still swings freely on it. Let the strap lean back onto its bay's back wall.
5. **Lever in:** lower the lever's bearings straight down into the frame's seats. The hub drops past the leaning strap; once it's down, the felt's bottom end is 1.1 mm off it. Tip the strap forward onto the hub.
6. **Shell on:** lower it straight down over the lever and the strap, so the grid's pyramids drop into their sockets. If the strap has leaned back, the ramp at the back of the shell's bay meets its head 4 mm before the shell is down and swings it forward. Fit the shell's four M4 × 50 socket head screws into the nuts and tighten them evenly.
7. **Knob:** if you're using the spring, drop it into the pocket in the knob's underside. Drop the M5 × 35 bolt into the knob's hex pocket, head down. Set the knob in its seat and screw the bolt down into the strap's nut. With the shell on, the strap can lean back only 1.0°, which leaves its nut 0.8 mm off the bolt's axis, and the lead-in in the head takes up 2 mm. Then set the drag.
8. **Covers:** fit the sensor cover, with the magnet in its post. Lay the USB cable into the cable cover's notch, push the cover onto the block and shell, and screw both down (M3 × 16).
9. **Strut and tube:** as Rev 3.

## Screws

All from the same kits as Rev 3: the AvrestYPT countersunk kit (M3 and M4 × 8, 12, 16, 20, with nuts) and the HELIFOUNER M4 × 30–50 socket head kit. The NIULUNBAO M3 set isn't needed.

| Where | Screw | Into | Qty |
|---|---|---|---|
| Lever halves | M4 × 40 socket head cap, from the top, two in front and two behind | M4 nut in a pocket in the lower half | 4 |
| Shell | M4 × 50 socket head cap, from the top, down 13 mm counterbores, centred on the joint | M4 nut slid into a slot in the block's outer face, just below the side cover's rim | 4 |
| Side covers | M3 × 16 countersunk, from the cover's outer face | M3 thread tapped through the block or the shell's side wall | 8 |
| Brake | **M5 × 35 hex-head bolt**, head on the floor of the knob's hex pocket | M5 nut in the slot in the brake strap's head | 1 |
| Brake strap's hinge | M4 × 50 socket head cap, from the +y side, head in a counterbore | M4 nut in a hex pocket on the −y side | 1 |
| Strut eyes | M4 × 16 countersunk, head on the +y side | M4 nut in the far cheek's pocket | 2 |
| Strut collar clamp | M4 × 12 countersunk | M4 nut in the other ear's pocket | 2 |

The hinge pin is a fifth M4 × 50 from the HELIFOUNER kit.

Every screw and nut, to scale:

![Every screw and nut, to scale](renders/rev4_screw_sizes.png)

Between them, these label every screw and nut in the base:

![The shell's screws, from above](renders/rev4_screws_top.png)

![The lever's screws, with the shell off](renders/rev4_screws_lever.png)

![The lever's nuts, from below](renders/rev4_screws_levernuts.png)

![The shell's nuts, in the pillow blocks' outer faces (sensor cover off)](renders/rev4_screws_shellnuts.png)

![From behind: the brake knob and its bolt](renders/rev4_screws_back.png)

![The brake in section: the bolt, its nut in the strap's head, the hinge pin, the strap and the knob](renders/rev4_screws_brake.png)

![The sensor side: the cover, the collar clamp, the strut's body-end nut, the hinge pin's nut, the desk screws](renders/rev4_screws_sensorside.png)

![The USB side: the cover, the strut's body-end screw, the collar clamp's nuts, the brake strap's hinge pin](renders/rev4_screws_usbside.png)

![The strut's anchor](renders/rev4_screws_strut.png)

## Bought parts

| Part | Qty | Notes |
|---|---|---|
| **6808-2RS thin-section ball bearing (40 × 52 × 7)** | 2 | new for Rev 4 |
| X AUTOHAUX 6" 45 N gas strut | 1 | Rev 3's |
| 25 × 23 mm carbon tube, 500 mm | 1 | Rev 3's, uncut |
| Worm-drive hose clamp, about 25–40 mm | 1 | Rev 3's |
| Compression spring, 10 mm OD, 10–15 mm free length | 1 | optional: Rev 3's fits |
| M5 × 35 hex-head bolt | 1 | any hardware store |
| Felt, 1.5 mm, 16 × 33 mm | 1 | on the brake strap |
| AS5600 module (WWZMDiB) | 1 | Rev 3's, with its magnet |
| #10 × 1-1/2 in wood screws | 4 | desk mounting |

## Notes

- **The checks:** `python mk3_rev4.py --check` runs three checks, and all are clean.
  - **Every pair of parts** at 0°, 8°, 16°, 24°, 31.5° and 32°. The overlaps it allows are the intended ones: screws in their holes, the bearings' inner races on the trunnions, the felt on the strap, the strut's tabs in their clevises, and the hose clamp in its groove. Just past each stop, the lever meets the frame where it should: the pads on the pillars below 0°, both lugs on the up-stop pad above 32°.
  - **The brake's clearances,** measured as distances, not overlaps: through the whole travel, the strap stays 1.5 mm off the lever, the felt 0.02 mm off the hub, and the knob more than 6 mm off the lever; the strap is 0.5 mm off the pad's slot either side, and 1 mm off the shell's ramp.
  - **The assembly order:** the strap set down into the frame, leaning back; the lever lowered past it; the strap swung onto the hub; the shell lowered over both, its ramp swinging the strap forward.
- **Chamfers:** Rev 3's chamfer step once returned a valid frame with the down-stop pillars missing. Rev 4's version refuses any set of chamfers that takes off more than chamfers could. Rev 3's parts were checked, and none of them lost anything.
- **Brake feel:** untested. The felt patch is 16 × 33 mm, and the drag per newton of bolt tension is worked out for felt on PETG at μ = 0.3. Fit the spring if the knob is too touchy without it.
- **Balance:** see [Balance](#balance). The lever is about 68 cm³ lighter than Rev 3's, mostly near the pivot, and that makes almost no difference: its load at 0° is 1.998 N·m against Rev 3's 1.996.
