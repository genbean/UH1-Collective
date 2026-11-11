# MkIII base, Rev 4: narrow

The collective's pivot base. The lever runs on two thin-section bearings and is printed as two halves; the 500 mm carbon tube slides into its socket. A small gas strut, from a clevis on the frame to a collar on the tube, holds the lever up against the head's weight, and a felt-lined brake strap behind the hub sets the drag. An AS5600 magnetic sensor in the lever's end reads its angle, and the USB cable leaves on the other side.

Rev 4 is Rev 3, the first base built (2026-11), cut down to **73 mm (2.87 in)** wide along the pivot axis, against Rev 3's 130 mm, with the lever symmetrical about the tube. One shell over the top encloses the lever, in place of Rev 3's two bearing caps. The strut, collar, tube, socket, down-stops and fits are Rev 3's. What changes is everything along the pivot axis, the enclosure, and the brake, which moves behind the hub. Rev 3's own files are no longer in the repository (they're in its git history); the parts of its model that Rev 4 still uses are in `mk3_rev3.py` and `mk3_pivot.py` (see [Files](#files)).

This is the current base. Its first frame, shell and lever were printed and assembled on 2026-11-08, and the bearing coupons fitted. Since then the lever is split on the tube's plane, the brake is a hinged strap, the side covers are 5 mm square plates, the USB cable leaves toward the front, and the lever's opening is 2 mm clear. So reprint every printed part except the strut collar, and print the dowel-hole [coupon](#fit-test-coupons) before the lever.

[![Rev 4, exploded](renders/rev4_exploded.png)](https://htmlpreview.github.io/?https://github.com/genbean/UH1-Collective/blob/main/Base/renders/rev4_exploded.html)

**[▶ Open the interactive version](https://htmlpreview.github.io/?https://github.com/genbean/UH1-Collective/blob/main/Base/renders/rev4_exploded.html)** (click the picture too): point at any part to see what it is ([the page](renders/rev4_exploded.html), to download and open locally).

![Rev 4 from the front](renders/rev4_hero.png)

![Rev 4 with the shell off](renders/rev4_open.png)

![Rev 4 straight down from above, to scale](renders/rev4_top.png)

![From behind: the brake knob in the shell's top; the USB cable leaves the cable cover toward the front](renders/rev4_rear.png)

![At the 32° up-stop](renders/rev4_32deg.png)

## What changes from Rev 3

- **Lever:** the hub is 43 mm long (Rev 3: 64), centred on the tube. The tube's plane moves from 9 mm off-centre to the middle. Rev 3's friction drum is gone. The halves split on the tube's plane instead of at the pivot axis, so each trunnion prints round, in one piece.
- **Bearings:** 6808-2RS thin-section bearings, 40 × 52 × 7 mm, in place of the 6006-2RS (30 × 55 × 13). The trunnions grow to 40 mm across to suit.
- **Frame:** 9 mm pillow blocks (Rev 3: 17). The base plate stops at their outer faces, so it's 63 × 127 mm (Rev 3: 100 × 116), with no wings or gussets out beside it. A front wall under the shell's carries its cut for the lever on down, so the two read as one piece.
- **Shell:** one box over the lever, in place of the two caps, slotted for the tube. Four M4 × 50 socket head screws hold it to the pillow blocks, and a diamond grid in the joint locates it.
- **Sensor:** the AS5600 board sits inside the sensor trunnion's end, flush with the bearing, so the side covers are 5 mm plates (Rev 3's are 15 mm deep).
- **USB cable:** it turns toward the front on an 18 mm bend, through a pie-shaped relief in the cable trunnion's end, and runs forward in a tunnel under the cable cover, instead of Rev 3's spout.
- **Brake:** a felt-lined strap wraps the back of the hub, hinged at its bottom in the up-stop pad. A knob on top of the shell pulls it on, through a bolt that leans 30° forward.
- **Up-stop:** two lugs under the back of the hub, one each side of the strap, land on a pad further back than Rev 3's.
- **Frame gussets:** 45° gussets at all four corners of both pillow blocks.
- **Strut anchor:** moved up and back, so the 45 N strut as bought balances the lever. Rev 3's first anchor was sized for a 40 N strut, so the 45 N strut pushed the lever up. Rev 3 now has the same anchor.

The knob stands on top of the shell, leaning 30° forward; nothing sticks out behind the back face.

## Files

| | |
|---|---|
| `mk3_rev4.py` | the model. `python mk3_rev4.py` writes `stl/`, `stl/ref/` and `step/`; `--check` runs the interference, assembly and opening-clearance checks; `--openings` the openings' check alone; `--balance` the balance table and `renders/strut_balance_r4.png`; `--coupons` writes `stl/coupons/` |
| `make_renders_r4.py` | the renders, screw maps, exploded view and screw chart, `renders/MkIII_Rev4_Assembly.glb`, and the complete collective in [`../renders`](../renders): the head's printed parts from `../Head/stl`, its search hat from `../Head/Hat`, and its bought parts (board, switches, screws, wires) carried over from the collective's GLB |
| `mk3_rev3.py`, `mk3_pivot.py` | the shared library `mk3_rev4.py` builds on: Rev 3's and Rev 1's models, for the strut, its collar and anchor, the balance model, the MkII knob, the chamfers, the fit parameters and the geometry helpers. Nothing in them writes files |
| `make_renders_r3.py` | the shared render helpers `make_renders_r4.py` uses (drawing, sections, GLB loading) |
| `source/MkII-AdjustKnob.stl` | the MkII friction knob, which the brake knob is made from |
| `stl/` | the printed parts |
| `stl/ref/` | bought parts and hardware, for reference |
| `stl/coupons/` | the fit-test coupons |
| `step/MkIII_Rev4_assembly.step` | the whole base |

Both scripts need CadQuery; the renders also need trimesh, manifold3d, pyvista and pillow, and `../renders/make_diagrams.py`'s helpers.

## Fit-test coupons

The coupons are short slices of the critical fits, so you can tune the tolerances on a few small prints instead of a failed lever or frame. The trunnion's and the bearing seat's have been printed and fitted (below). The lever's dowel holes are new, so print their coupon before the lever halves. The tube socket fitted as built; print its coupon if your tube or printer is new.

| File | What it is | Good fit | Change |
|---|---|---|---|
| `stl/coupons/coupon_trunnion_6808.stl` | 8 mm trunnion stubs on the inner-race shoulder, with the ½" cable bore, 39.9 / 40.1 / 40.3 mm, standing on the shoulder | the race presses on firmly by hand or in a vise, no wobble, and doesn't turn on the stub | `TRUN_OD += step` |
| `stl/coupons/coupon_bearing_seat_6808.stl` | the seat and 2 mm lip, 51.8 / 52.0 / 52.2 mm, lip down | the race goes in with thumb pressure and doesn't drop out upside down; leave it slightly free rather than tight | `BRG_SEAT_D += step` |
| `stl/coupons/coupon_dowel_hole.stl` | one of the lever's dowel holes, 7.4 / 7.6 / 7.8 mm, 4.2 mm deep, opening on the bed with its lead-in, as the halves print it | a printed dowel (`lever_dowel.stl`) pushes in by hand, with no play | `DOWEL_CLR += step / 2` |
| `stl/coupons/coupon_tube_socket.stl` | 20 mm of the tube socket's bore, 25.2 / 25.4 / 25.6 mm, each a closed ring standing on end | the carbon tube slides in from the top by hand, with no rattle or rocking | `SOCK_BORE_R += step / 2` (a radius, in `mk3_pivot.py`) |

**Making them:** `python mk3_rev4.py --coupons` writes all four. Each file is one plate of three variants side by side, tied by a spine. The number engraved in front of each is its step in mm, from `COUPON_STEPS = (-0.2, 0.0, 0.2)` in `mk3_pivot.py`. A step changes the fitted **diameter**, and `0` is exactly what the current parameters print.

**Printing them:** use the same printer, filament and slicer profile as the real parts: walls, line width, layer height, flow and elephant's-foot compensation. The STLs are already oriented, so don't rotate them. The rings stand on end, so their round faces build up layer by layer with no overhangs and any elephant's foot stays off the fit.

**Reading them:** try the real part on each variant and pick the one that fits best. If the best fit falls between two, use the value halfway between them. Change the parameter (above) and re-export the parts. If even an end variant is wrong, move the whole range, for example `COUPON_STEPS = (0.2, 0.4, 0.6)`, and print again. After a change the new value is the new `0`, so reprint the coupon to confirm it.

**What the coupons can't show:** the bearing seat coupon is one piece, so it can't show the frame and shell's split seat (below). The lever halves print as arches in the joint face (the socket and the radial cable bore), whose crowns are the least accurate layers; if the tube is tight only along the crown, scrape it rather than going up a step.

The bearing coupons' `0` comes from how the bearings fitted as built:
- **Seat:** +0.1 on the race's outside was a perfect fit in Rev 3's one-piece blocks. In Rev 4's seat, split between the frame and the shell, it left the bearing a little play, so the seat is now 52.0 mm, the race's own size. The seat coupon is one piece, so it can't show the split: check the play in the frame and shell themselves.
- **Trunnion:** +0.2 on the race's bore pressed on a hair too tight, so Rev 4 uses +0.1 (40.1 mm).

The tube socket is unchanged from Rev 3, where it fitted as built (25.4 mm, `SOCK_BORE_R = 12.7`).

## Across the pivot axis

From the middle out, each side:

| | \|y\|, mm | |
|---|---|---|
| Hub | 0 – 21.5 | 60 mm across; 3.5 mm past the socket boss |
| Bearing | 22.5 – 29.5 | 6808-2RS |
| Retaining lip | 29.5 – 31.5 | the pillow blocks' and the shell's outer faces, and the plate's edge, are at 31.5 |
| Trunnion end | 29.5 | 40.1 mm across, flush with the bearing's outer face |
| Side cover | 31.5 – 36.5 | a 5 mm plate; it overhangs the base plate by 5 mm |

## Shell

![Section on the pivot axis, from the front](renders/rev4_section_axis.png)

The shell is a box over the lever: 75 mm long, 63 mm wide and 38 mm tall, from the pillow blocks' tops. It replaces Rev 3's two caps.

- **Side walls:** solid, 9 mm thick. These are the caps. Each holds the bearing's upper half-seat and lip, and two of the cover's screw holes. Two M4 × 50 socket head screws per side go down through them from the top, each centred on the joint, heads down 13 mm counterbores, into M4 nuts in the pillow blocks (see [The joint](#the-joint)).
- **Front, back and top walls:** 3 mm thick.
- **Tube slot:** one clean opening in the front and top, the same outline as the frame's front wall below it (see [The joint](#the-joint)). It fits the lever closely: 2 mm clear of the socket boss, the lever's fairings, the down-stop pads and the hose clamp, measured in 3D, through their whole swing, 0° to 32°.
- **Behind the hub:** solid, from 2 mm off the hub out to the side walls, the top and the back face, so the brake knob's seat, sunk into the top, bears straight into the walls. The brake strap's bay is under the seat (see [Brake](#brake)).
- **Assembly:** it drops straight down over the lever and the strap, the slot and the strap's bay both open at the bottom.

## Side covers

![The USB side: the square cover over the bearing and the shell screws' nut slots](renders/rev4_hero.png)

Square plates, 5 mm thick, on the pillow blocks' and the shell's side faces, centred on the pivot axis, over the bearing and the shell screws' nut slots. They're bevelled 45° all round, so each reads as one with the block and shell: the back on the plane of the frame's and shell's [back chamfer](#the-back), the front on the plane of the 0.8 mm chamfer on the pillow blocks' front corners, the top on the plane of the 0.8 mm chamfer on the shell's top edge, and the bottom the top's mirror image. The inside face is 74.4 mm tall and the outside face 64.4 mm. Each is held by four M3 × 12 countersunk screws, where the round covers had them, into M3 threads tapped right through the block's and the shell's 9 mm walls. The USB side's cover hides the strut's hex-key hole, so fit the anchor screw before the covers.

- **Sensor cover:** the magnet sits in a pocket in its inside face (see [Sensor](#sensor)).
- **Cable cover:** half of the USB cable's tunnel is a channel in its inside face (see [USB cable](#usb-cable)).

The edges against the block and shell aren't chamfered, so no groove shows at the seams.

## The joint

![The frame's half of the joint: the knurl on every land, both sides of the bearings](renders/rev4_joint_grid.png)

The frame and the shell meet on one flat plane through the pivot axis, which also splits the bearing seats.

- **Screws:** four M4 × 50 socket head cap screws from the lever's HELIFOUNER kit, two per side, 30.5 mm either side of the axis, down the middle of the shell's 9 mm side walls (y = ±27). Each is centred on the joint: its head seats 25 mm above it, at the floor of a 13 mm counterbore, and its tip is 25 mm below. Each goes into an M4 nut slid into a slot in the pillow block's outer face, about 21–24 mm under the joint. The slots open on the blocks' outer faces, under the side covers. The nut sits flats-in: its inner flat stops it turning when you tighten the screw. The counterbore leaves 0.9 mm of shell either side, and the nut's slot leaves 0.9 mm of block to its inside face.
- **Diamond knurl:** the whole face the frame and the shell share is knurled.
  - **Shape:** square pyramids 2.4 mm across their corners and 0.7 mm tall with flat tops, on a diamond grid with 0.6 mm flat lanes. They stand on the frame's half and fit into sockets in the shell's half, 0.1 mm clear on their 45° flanks and 0.2 mm deeper than the pyramids. The flat faces still close on each other, so the bearing seats close, and the knurl stops the shell sliding fore and aft or sideways as the screws pull it down.
  - **Coverage:** it runs over every land, in front of the bearings and behind them, and on across the solid frame behind the pillow blocks. It stops 0.5 mm short of every edge and hole: pyramids at its edge are cut off square, and any piece smaller than a third of a pyramid is left out. The grid is the same mirror image either side of the tube, and fore and aft on the pillow blocks.
  - **Printing:** neither half needs supports: the pyramids point up on the frame, and the sockets open upward on the shell, which prints top down.
- **Front opening:** the frame has a 3 mm front wall between the pillow blocks, under the shell's, and one clean opening runs through both. It follows the lever 2 mm clear (2.0 to 2.4 mm wherever the lever passes close), measured in 3D from the down-stop to the up-stop: `python mk3_rev4.py --openings` measures it. It's drawn in lines, arcs and ellipse arcs, with no facets. From the bottom up:
  - **Lower fairing:** a tab 12.55 mm either side of the tube, its bottom 24.7 mm under the axis, its corners rounded to follow the fairing's 3 mm rounds.
  - **Socket boss:** a circle 20.05 mm about the axis up to the joint, then straight sides. Where the tab meets it, the corners are rounded 3 mm.
  - **Pads' reliefs:** from about 20° on, the down-stop pads' back corners swing up through the shell's wall. Each side bows out on one long arc to 22.05 mm and runs straight up to the pads' tops at the stop, then turns back in.
  - **Boss at the stop:** an ellipse, the boss's own section in the front face at 32°, narrows up to the top. It meets the top slot's sides through the top wall's 3 mm.
  
  On top it carries on as one slot. At the front it follows the boss's footprint as it crosses the wall at the stop, an ellipse, and is rounded into straight sides 12.55 mm either side of the tube over the upper fairing. It ends square 3.15 mm in front of the axis, where the fairing's top passes under the wall at the stop, with corners that follow the fairing's rounds. Below the opening, a smooth round-ended slot lets the strut's cylinder through, 1.5 mm clear over the whole travel. It's cut by the cylinder swung about its anchor pin, so it has no facets.
- **Hex-key hole:** a 3.5 mm hole through the USB-side (+y) pillow block, on the strut anchor screw's axis. A 2.5 mm hex key goes straight in to the M4 × 16's head. The USB side's cover hides it, so fit the anchor screw before the covers; to reach it later, take the cable cover off.

![The front: the frame's wall carries on the shell's cut for the lever](renders/rev4_front.png)

## Lever

Two halves, split on the tube's plane (y = 0) rather than at the pivot axis as Rev 3: `lever_sensor` (−y) and `lever_cable` (+y). Each prints on its joint face with its trunnion up, so each trunnion is one round piece, printed the same way as the trunnion coupon that fitted the 6808.

- **Screws:** four M4 × 35 socket head cap screws run along the pivot axis through the hub, behind the bearings, on a 24.7 mm circle at ±50° from fore and aft. Each half has two heads and two nuts, diagonally opposite: the sensor half has the front-top and back-bottom heads, the cable half the other two. The heads sit in 7.5 mm counterbores 5 mm deep in the hub's end face, and the nuts in hex pockets in the other half's end face, a flat toward the axis. Each tip stands 1 mm past its nut, 3 mm inside the far end face.
- **Walls:** the counterbores leave 1.55 mm of hub over them and the nut pockets 1.6 mm. The counterbores come within 0.05 mm of the bearing's shoulder without breaking into it.
- **Behind the bearings:** the 6808s cover the heads and nuts. Screw the halves up before pressing the bearings on. To split the lever again, pull a bearing first.
- **Dowels:** a printed hollow dowel sits round each screw at the joint, half in each half, like the dowels between an engine and its gearbox. Each is 7.5 mm across with a 4.5 mm bore, and 8 mm long (`lever_dowel.stl`, print four).
  - **Holes:** 7.6 mm across and 4.2 mm deep each side, so the joint faces close on each other, with a 0.4 mm 45° lead-in at the mouth that takes the first layer's squish.
  - **Shear:** the steel screw inside each dowel carries the load across the dowel's layers.
  - **Fit:** tune it with the dowel-hole coupon.
  - **Walls:** the front pair's holes are 2.4 mm from the socket, and the back pair's 1.5 mm under the hub's surface.
- **Seam:** a 0.3 mm chamfer runs round the joint face's outside edge, against elephant's foot at the seam. The bores have none.
- **Down-stop pads:** each runs in to the lower fairing. It's filled from the pad's inner face to the fairing's side over its whole length, and from its bottom up into the boss, so pad and fairing are one piece. With the lever split on the tube's plane, the pad's inner face would otherwise print as a flat overhang.
- **Strength:** up and down at the grip, the main load, the two halves sit side by side, each carrying its share, and nothing crosses the joint. With Rev 3's split at the axis, each half alone had only about a fifth of the section's stiffness, and the joint had to carry the shear between them, about 3 N/mm at 100 N on the grip. A side load crosses the joint now instead: 20 N at the grip puts about 0.7 N/mm across it, which the dowels and the screws' clamp carry easily.
- **Unchanged:** the outside, the bores, the fairings, the strut relief, the hose-clamp groove, the trunnions and the socket for the uncut 500 mm tube. The halves are mirror images, except the sensor's pocket in the sensor half's trunnion and the USB cable's relief in the cable half's (see [USB cable](#usb-cable)).

[![The lever exploded: the halves, dowels, screws and nuts](renders/rev4_lever_exploded.png)](https://htmlpreview.github.io/?https://github.com/genbean/UH1-Collective/blob/main/Base/renders/rev4_lever_exploded.html)

**[▶ Open the interactive version](https://htmlpreview.github.io/?https://github.com/genbean/UH1-Collective/blob/main/Base/renders/rev4_lever_exploded.html)** (click the picture too): point at any part to see what it is ([the page](renders/rev4_lever_exploded.html), to download and open locally).

**Fairing:** in place of Rev 3's 8 mm top gusset, a fairing 21 mm wide runs over the socket boss, and the same one mirrored runs under it. It starts at the hose-clamp groove's back edge. Its top is one straight line from the boss's top there to the hub, tangent to the hub's circle, so it runs into the hub without a corner. Its long top edges are rounded 3 mm.

**Strut relief:** the strut's cylinder sits on the base end, and from 28° up its end comes in under the front of the hub. A shallow relief in the hub's underside lets it by, 1.5 mm clear all the way to the stop: 2.65 mm deep at most, 11.6 mm wide, centred on the tube's plane. It's cut by the cylinder swung about the collar's pin as the lever sees it, so it's smooth, with no facets. It's under the lever, away from the brake's felt.

![The lever from below at the 32° stop: the relief for the strut's cylinder](renders/rev4_strut_relief.png)

![The lever from the side: the fairings top and bottom, tangent to the hub](renders/rev4_lever_side.png)

![The lever from the front and above: the upper fairing; the halves meet on the tube's plane](renders/rev4_lever_top.png)

![The lever from the front and below: the down-stop pads run in to the lower fairing](renders/rev4_lever_under.png)

![The lever's sensor end, bearing off: two heads and two nuts](renders/rev4_screws_lever_sensor.png)

## Sensor

The AS5600 module (WWZMDiB) sits in a square pocket in the sensor trunnion's end, chip facing out, its front face level with the trunnion's end, which is flush with the bearing's outer face. There's no carrier.

- **The pocket:** 23.54 mm square (the board is 0.915 in, 23.24 mm, as measured, plus 0.15 mm a side) and 1.6 mm deep for the board. The board rests on two 1.6 mm ledges along its top and bottom edges, clear of both pad columns.
- **Behind the board:** 3.5 mm of space for the wires soldered in from the back and the DIR jumper. It opens into the axial bore, which takes the lead to the tube.
- **Orientation:** set it in with the pad columns vertical. It fits either way up.
- **Holding it:** a dot of hot glue in two corners. Nothing else holds it in.

The chip stands inside the bearing's retaining lip. The magnet (the module's own diametric magnet, about 4 × 2 mm) sits in a 4.2 mm pocket in the sensor cover's inside face, the same as the head axle's, its face 0.5 mm below the cover's and 1.0 mm off the chip. The lead runs from the back of the board through the axial bore and up the tube to **AX1** on the HeliSR board.

**Wiring:** the module (WWZMDiB, Amazon B0CM3C8KFT) has no header. Its pads are two columns of through-holes, 4.7 mm in from opposite edges: **VCC, OUT, GND** along one, **DIR, SCL, SDA, GPO** along the other. Solder the wires straight in from the back; the space behind the board takes them and the DIR jumper. The pad positions are measured from the product photos (±0.3 mm), so check them against yours.

**With HeliSR Rev 4.0 (I²C):** four wires, **VCC, GND, SDA and SCL**, to the AX1 port (pin 1 SDA, 2 GND, 3 VCC, 4 SCL).
- **5 V:** remove the module's 0 Ω R1. It ties VDD3V3 to VDD5V, and the 3V3 pin is rated 4 V max.
- **DIR to VCC:** a short jumper across the back of the board, from DIR to VCC. DIR floats on this module. The chip turns with the lever and the magnet is fixed, so DIR = VCC makes the angle rise as the lever lifts.
- **Remove R4**, the 1 kΩ from PGO (labelled GPO) to GND. PGO low selects the OUT-pin programming used with Rev 3.0; without R4 the chip's own pull-up holds it high.
- **Pull-ups:** measure the module's SDA→VCC and SCL→VCC resistance before you fit it (see the HeliSR Rev 4.0 board's README, AS5600 modules).
- The range is set by the firmware over I²C, not burnt into the chip, so it can be changed at any time.

**With HeliSR Rev 3.0 (analog):** three wires, **VCC, OUT and GND**, to AX1. Remove R1 and jumper DIR to VCC as above, but keep R4. The range is programmed once through the OUT pin (datasheet option B) with the board's **PROG1** button:
1. Hold the lever on its down-stop and press PROG1 for about a second.
2. Lift it to the 32° stop and press PROG1 again.

It can't be checked beforehand: until programming is done, AX1 reads full scale whatever the lever does.

## USB cable

![The cable's bend, cover off, at 0° (left) and at the 32° stop (right): the relief in the trunnion's end turns with the lever, under the cable](renders/rev4_usb_bend.png)

The cable leaves on the right-hand (USB) side and faces the front.

- **The bend:** it comes along the axis and turns toward the front on an 18 mm radius, about four times its 4.6 mm thickness (Rev 3: 6 mm). The bend starts inside the axial bore and ends just past the trunnion, inside the bearing's retaining lip.
- **The relief:** where the bend would rub the trunnion's end, a pie-shaped relief flares the bore's mouth. It's 4.8 mm deep at the bore and runs out 14 mm from the axis, well inside the bearing. The bend stays put while the trunnion turns under it, so the relief spans the cable's way out over the whole travel, 0° to 32°, and 1° past each end. Its sides are round, the cable's own section. The cable clears the turning trunnion by 0.5 mm all the way.
- **The tunnel:** from the lip, the cable runs straight forward in a round tunnel 5 mm across, 1.3 mm out from the pillow block's face. Half of it is a groove in the block's and the shell's outer faces, half a channel in the cable cover. It leaves through the cover's front bevel. Lay the cable in the groove and the cover goes on over it, so it can go on over a cable that's already through the lever, as Rev 3's does. The groove leaves 1.1 mm of block to the nearest shell screw's hole, and the cover 1.2 mm over the channel.

The trunnions end flush with the bearings so the cable can turn inside the lip: that's what lets the covers be 5 mm.

## Brake

![Section on the tube's plane](renders/rev4_section_brake.png)

A rigid printed strap wraps the back of the hub between the up-stop lugs, from 54° below the axis to 42° above it, and its felt from 52° below to 40° above. It's 18 mm wide and 8 mm deep, lined with 1.5 mm felt. At the bottom the band turns into an arm that runs forward under the hub, through the up-stop pad's slot, to the hinge, just behind the strut's clevis. At the top it runs on under the head, its end cut off level with the head's face, 3 mm under the bay's ceiling. The head is solid, with an M5 nut in it. The knob sits on top of the shell and draws the head up and forward, so the strap swings about its hinge and the felt clamps the hub.

- **The pull:** the knob's M5 × 35 bolt leans 30° forward from vertical, which gives it 59 mm of leverage about the hinge. A vertical bolt would get 31 mm (12 with the hinge where it first was, behind the hub), and would stretch and bend the strap more than close it. 30° is as far as it can lean with the seat sunk into the shell's top and 2 mm or more of shell between the seat and the hub.
- **Gussets:** the head is one solid gusset, from the band 12° above the axis up to its top end, front and back, out to where the bolt pulls. The arm runs from the band's bottom 12° forward to the hinge, with a gusset under it down to the knuckle's bottom. Neither end is a thin tab.
- **Where the hinge is:** under the hub, at x = 5, z = −40, just behind the strut clevis's cheeks, as far forward as it fits. The strap's swing presses each bit of felt in proportion to the hinge's distance from the felt's radius through it. With the hinge forward under the hub, that's even along the felt: its bottom end gets half the pressure of its middle, against a tenth with the hinge behind the hub, where it first was. And the knob's bolt passes further from the hinge, so it gets more leverage.
- **The hinge:** the pin, an M4 × 50 socket head, goes through both pillow blocks, a web inside each, and the strut clevis's back block. Behind the clevis's cheeks the block is cut down to a 6 mm rib, 2 mm under the hub like the rest of it. The strap forks round the rib into two 4.5 mm cheeks, and each runs on the pin between the rib and a web, 1.5 mm clear of both. Its arm runs through the up-stop pad's slot, 0.5 mm clear either side. The slot guides it, so the strap stays at least 1.5 mm off each lug (2 mm when centred). The pin's head is in a counterbore on the USB (+y) side, and its nut in a hex pocket on the sensor (−y) side, both below the side covers.
- **The nut:** it drops into a slot in the head from the strap's +y side. The bolt holds it there, and its pull bears it on the slot's face. A lead-in in the head's face guides the bolt's tip onto it.
- **The knob's seat:** sunk into the shell's top, square to the bolt. There's 4 mm of shell under it, then the strap's bay.
- **The spring, if you want one:** the knob has a 10.6 mm pocket, 7 mm deep, in its underside. Without a spring, the knob sits on its seat and pulls the strap directly. With one (10 mm OD, 10 to 15 mm free length, such as Rev 3's friction knob used), the spring holds the knob off its seat and the knob sets the brake through it. The M5 × 35 keeps its full thread in the nut either way.
- **The bay:** 22 mm wide, out to the lugs' inner faces, in the frame and the shell. In the frame, the strap leans back on its own onto the bay's back wall, at 8.5°: far enough for the lever's hub to drop past the felt's top end, 1.6 mm clear. In the shell, the back of the bay is a ramp parallel to the bolt, 1 mm behind the head. As the shell goes on, the ramp meets the leaning strap's head and swings it forward onto the hub, so its nut lands on the bolt's axis.

**Drag:** about 12.2 N·mm per newton of bolt tension with the lever moving up, and 18.2 moving down: the strap is self-energising by about 49%. It would lock itself only above a friction coefficient of about 1.5, and felt runs about 0.3. 18 N of tension gives the old shoe's 270 N·mm.
- **Pressure along the felt:** it peaks 7° above the axis, and falls to half that at the felt's bottom end and 84% at its top. The felt below 38° under the axis now takes 11% of the grip (5% with the hinge behind the hub), the felt above 22° over it 20% (28%), and the middle 69%. The peak at 400 N is 1.0 MPa.
- **With the spring:** the brake's range is spread over about 10 turns of the knob, up to the spring's 20 N or so. Past that, the knob is down on its seat and the brake firms up.
- **Without it:** the felt is the only give, so the brake goes from free to firm within about a turn.

**Strength:** checked at 400 N of bolt tension, more than a hand gets out of an 18 mm knob (about 130–210 N at 0.3–0.5 N·m).
- **Strap:** it prints on its side, so all its bending runs along its layers (35 MPa allowed). The band peaks at 18.5 MPa, the neck under the head at 21, the arm's cheeks at 20 and the arm behind them at 14.
- **Hinge:** the pin carries 760 N. The cheeks bear 21 MPa on it. It runs between the rib and the webs, so it bends only to 79 MPa in its 12.9 steel. The rib bears 16 MPa, with 5.8 mm of rib over the pin, and the webs 4.
- **Shell:** the 4 mm floor under the seat bends at 17.5 MPa, along its layers. The shell is solid behind the hub, out to its side walls, top and back, so the seat's load goes straight into the walls.

![At the 32° stop](renders/rev4_section_brake_32deg.png)

## Up-stop

![The brake strap between the two up-stop lugs, at 0°](renders/rev4_brake_lugs.png)

Two lugs under the back of the hub land on a pad on the frame at 32°. Each lug is 10 mm wide (|y| 11 to 21), with 22 mm between them for the brake strap.

**Where the pad is:** x = 14 to 29.5, the full width between the pillow blocks, with a slot in its middle for the brake strap's arm. Its top is at z = −28.5, 2 mm under the hub at its front edge.

**Where the lugs land:** x = 15 to 24.4. They can't land further back: the further back a lug lands, the further back it swings at 0°. These come to x = 35.8 at 0°. Behind them the frame is cut away on a 39 mm radius round the axis, 1.5 mm clear of their swing.

At 0°, the strap's arm runs between the lugs, 2 mm clear of each. As the lever lifts, the lugs swing down either side of the strap onto the pad. Between them, the hub is a plain cylinder for the felt to run on.

![At 32°, the lugs on the pad (frame and shell hidden)](renders/rev4_brake_lugs_32deg.png)

The anchor clevis's back wall runs level, at the cheeks' top, into the pad's front face.

## Frame

![The frame from above](renders/rev4_frame_top.png)

The plate is 63 mm wide, the pillow blocks' outer faces, and 127 mm long. The desk screws are 24 mm either side of the middle, past the blocks' ends and the down-stop pillars.

Behind the up-stop pad, the frame is solid back to its back face and out to the [back chamfer](#the-back), except for a 39 mm radius round the axis between the pillow blocks, 1.5 mm clear of the up-stop lugs' swing, and the brake strap's bay in the middle.

**The brake strap's hinge:** behind the strut clevis's cheeks, its back block is cut down to a 6 mm rib through the strap's hinge pin, between the strap's two cheeks, still running 2 mm under the hub into the up-stop pad. Inside each pillow block, a web runs in to 10.5 mm from the middle, round the pin and level with the rib, so the pin is held either side of each of the strap's cheeks. The webs end 3 mm short of the up-stop lugs' swing.

![The frame from above, with the brake strap in](renders/rev4_frame_strap_top.png)

Each pillow block also has a 45° gusset at its front corners, 8 mm along each wall:
- **In front, inside:** the block's inner face to the down-stop pillar's back face, up to the pillar's top, 3 mm clear of the hub.
- **In front, outside:** the block's front face to the pillar's outer face, up to the pillar's top.

The down-stop and strut are unchanged from Rev 3: pads on the socket boss land on two pillars at 0°, and the gas strut runs from a clevis on the frame to the collar on the tube. Everything is on the new centre line. Each pillar runs on into its pillow block.

## The back

![From behind: the back chamfers and the brake knob](renders/rev4_back.png)

The frame and the shell share one 45° chamfer plane each side. It runs from the pillow blocks' outer back corners to the back face, at x = 57 (|y| + x = 69 mm), so from behind the two read as one block. The back face is 24 mm wide. It's that far back so the shell's bay has room for the brake strap's head when the strap leans back 8.5°. The edges in the joint aren't chamfered, so no groove shows at the seam.

## Balance

![Out of balance at the grip, against lever angle](renders/strut_balance_r4.png)

Rev 3 was first built with the anchor at x = −12, z = −40.5, sized for a 40 N strut: the bottom of the range the 45 N strut is sold as. The 45 N strut as bought lifted the lever, by about 50 to 70 g at the grip.

The anchor is now at x = −9.5, z = −36.5 (Rev 3's frame was updated to it too): 4 mm up and 2.5 mm back. The strut's line passes closer to the pivot, so it has less leverage. It now balances 45 N to within 3 g at the grip over the whole travel. The strut is 119 mm long at 0° and 140 mm at 32°, inside its 102–152 mm stroke.

The strut is fitted cylinder down, as built: its cylinder (0.475 in, 12.07 mm, measured) on the anchor clevis, and its rod on the collar. The frame is cut 1.5 mm clear of the cylinder's sweep, through the front wall and over the clevis's front gussets.

| Strut force | Out of balance at the grip | Fix |
|---|---|---|
| 40 N | −59 to −50 g (drops) | — |
| **45 N (as bought)** | **−3 to +1 g** | none |
| 50 N | +49 to +60 g (rises) | about 42 g of ballast in the head |
| 53 N (top of the range) | +79 to +95 g | about 68 g of ballast |

The collar still fine-tunes: 8 mm toward the pivot adds about 21 g of lift at the grip, and 8 mm away takes 21 g off.

**The clevis:**
- **Cheeks:** they're 6.5 mm round the eye (Rev 3: 8), so they stay 1.5 mm under the hub.
- **Back walls:** they run 2 mm under the hub into the up-stop pad. Behind the tab, from 1 mm past its round end, the gap between them is filled, so they print as one solid block with proper infill.
- **Screw:** the strut's M4 × 16 still fits.

`python mk3_rev4.py --balance` prints the table and redraws the plot. It uses the balance model from Rev 3 (`mk3_rev3.py`): Rev 4's lever halves, the collar and half the strut behind the pivot, and an estimate of the head, grip, tube and cables in front of it (a 368 g head, a forward moment of about 195 g·m). The figures assume the strut gains 30 % in force from fully extended to fully compressed; the listing doesn't say, so the real curve may differ by a few grams. If your head is lighter than that, the strut will still lift a little. Slide the collar away from the pivot, or add ballast.

## The strut

**X AUTOHAUX 6" 10 lb / 45 N gas strut**, [Amazon B0CY267GFY](https://www.amazon.com/dp/B0CY267GFY), $13.69 for two (one spare).

| | |
|---|---|
| Length | 152.4 mm eye to eye extended, 101.6 mm compressed (51 mm stroke) |
| Force | 45 N, sold as 9–12 lb (40–53 N) |
| Ends | flat eyelet tabs that bolt through. The collar end, measured: a steel tab 3.94 mm thick and 8 mm wide, a 4.45 mm eye, then a Ø8 mm boss whose face is 5.72 mm from the eye's centre and which runs about 7 mm |

**Measure yours** before printing the frame and collar. The listing gives the eye holes as 4 mm and the rod as 4 mm; the cylinder measures 0.475 in (12.07 mm). The model uses those (`PIN_R` is the M4 screw's 4.4 mm clearance in the printed cheeks). The collar end's tab and boss are measured (`BODY_TAB_T`, `BODY_TAB_W`, `BODY_BOSS_D`, `BODY_BOSS_AT`, `BODY_BOSS_L` in `mk3_rev3.py`); the anchor end's tab is still a guess (`ROD_TAB_T`, `ROD_TAB_W`). The clevis slots are the tab's thickness plus 0.6 mm.

- **Friction and fade:** gas struts have seal friction, and some are oil-damped; neither is published, so expect a little built-in drag. Their force changes about 3 % per 10 °C and fades slowly over the years: the collar or a few grams of ballast correct it.

## The carbon tube

25 × 23 mm carbon fibre, 500 mm, used uncut: 470 mm plus the 12.7 mm the head's boss takes, plus the 17.3 mm in the socket. The socket runs 63.3 mm in from its mouth, to 2.7 mm from the pivot axis, so the tube's end sits 3.8 mm into the axial cable bore: notch its sides there (see [Assembly](#assembly)). The grip's top is 445 mm from the pivot, and at the 32° stop the hand rises about 9.4 in, against the real UH-1's 9.25 in. Program the sensor's range across 0–32°.

- **Buy roll-wrapped, not pultruded.** Pultruded tubes have all their fibres running lengthwise and split easily when clamped or drilled. Roll-wrapped tubes have cross plies and take both.
- **Check the fits** with the socket coupon if your tube's outside diameter differs.
- **Drilling and notching:** use a sharp bit and back the tube with wood, or wrap the spot with tape, so it doesn't splinter.
- **Clamping:** do the collar's two M4 clamp screws and the hose clamp up firmly, but don't crush the tube. There's no lock screw: the hose clamp holds it.

## Printing

- **Frame:** plate down. The brake strap's slot and bay open at the top, the grid's pyramids point up, and the front wall builds straight up.
- **Shell:** top down. The bearing half-seats, the slot, the strap's bay and the grid's sockets all open upward. The knob's seat is on the bed, and its floor slopes at 30°: support it from the bed, in the seat only.
- **Lever halves:** each on its joint face, trunnion up, so the trunnion prints round, axis up, like its coupon.
  - **Opening upward:** the sensor's pocket, the counterbores and the nut pockets.
  - **Arches:** the socket and the radial cable bore print as arches in the joint face. The dowel holes' roofs bridge 1.6 mm.
  - **Supports:** the up-stop lugs' inner faces need a small support each. Each is a flat overhang about 40 mm² across, 11 mm above the bed, and the brake runs between the lugs, so they can't be filled. Nothing else needs support: the down-stop pads run in to the fairing.
  - **Seam:** turn on the slicer's elephant's-foot compensation. The seam's 0.3 mm chamfer takes the rest.
- **Lever dowels:** four, standing on end.
- **Brake strap:** on its side, the nut's slot up. Its bending then runs along the layers. No supports.
- **Side covers:** outer face down. The magnet's pocket and the cable's channel open upward, and the 45° ends lean out at 45°, so no supports.
- **Knob:** underside down, the hex pocket open at the top. Reprint it if you have Rev 3's: its floor is now 11 mm up, and it has a pocket underneath for the spring.
- **Strut collar** (`strut_collar.stl`, unchanged from Rev 3: reuse one you have): stand it on the end away from the strut, the end without the boss's notch, so the bore builds straight up, the web's slope is under 30° and the notch opens at the top.

## Assembly

1. **Frame and shell:** tap the eight cover-screw holes M3, four in the pillow blocks and four in the shell's side walls. The pilot holes go right through the 9 mm walls. Slide an M4 nut into each of the four slots in the blocks' outer faces, two per side, and push it home over the screw hole.
2. **Lever:**
   - **Dowels:** push the four dowels into one half's holes.
   - **Cables:** poke the USB cable through the cable half's axial bore from its joint face, and the sensor lead through the sensor half's. Lay both along the radial channel.
   - **Close:** close the halves on the dowels. Drop an M4 nut into each of the four hex pockets, two in each end face. Fit the four M4 × 35 cap screws, two from each end, and tighten them evenly.
   - **Bearings:** press the bearings onto the trunnions. They cover the screws, so to split the lever again, pull a bearing first.
3. **Sensor:** prepare the module and solder it to the lead (see [Sensor](#sensor)), and set it in the trunnion's pocket, chip out, with a dot of hot glue.
4. **Brake strap in:** stick the felt (16 × 51 mm) on the strap's face, and drop the M5 nut into the slot in its head. Set the strap down into the frame, its cheeks either side of the strut clevis's rib and its arm in the up-stop pad's slot. Push an M4 × 50 socket head through from the USB (+y) side: the pillow block, the web, a cheek, the rib, the other cheek, the other web, and into an M4 nut in the sensor side's hex pocket. Tighten it: the strap still swings freely on it. Let the strap lean back onto its bay's back wall.
5. **Lever in:** lower the lever's bearings straight down into the frame's seats. The hub drops past the top of the leaning strap's felt 1.6 mm clear, and ends 3.0 mm off the felt's bottom end; the strap itself stays 2.0 mm clear. Tip the strap forward onto the hub.

   ![The lever going in past the leaning brake strap](renders/rev4_brake_lever_in.png)

6. **Shell on:** lower it straight down over the lever and the strap, so the grid's pyramids drop into their sockets. If the strap has leaned back, the ramp at the back of the shell's bay meets its head 8 mm before the shell is down and swings it forward. Fit the shell's four M4 × 50 socket head screws into the nuts and tighten them evenly.
7. **Knob:** if you're using the spring, drop it into the pocket in the knob's underside. Drop the M5 × 35 bolt into the knob's hex pocket, head down. Set the knob in its seat and screw the bolt down into the strap's nut. With the shell on, the strap can lean back only 1.2°, which leaves its nut 0.8 mm off the bolt's axis, and the lead-in in the head takes up 2 mm. Then set the drag.
8. **Strut's anchor end:** fit the gas strut's cylinder end into the anchor clevis with its M4 × 16, tightening it with a 2.5 mm hex key through the hole in the USB-side pillow block. Do this before the covers: the cable cover hides that hole.
9. **Covers:** glue the magnet into the sensor cover's pocket, pushed to the bottom. Lay the USB cable into its groove in the USB-side pillow block and shell, push the cable cover on over it, and screw both covers down (M3 × 12).
10. **Tube:** don't cut it. Drill the head's 5.2 mm cross hole, and file a notch in each side of the tube's bottom end, 13 mm wide (centred on its horizontal midline) and at least 4 mm deep, where the axial cable bore crosses its wall, so the cables can get in (see [The carbon tube](#the-carbon-tube)). Slide it into the socket, 63.3 mm deep, and tighten the hose clamp in its groove, with the head on top.
11. **Collar:** clamp it on the tube with its notched end (where the strut's boss sits, toward the pivot) 52 mm out from the front face of the socket boss: the collar is 40 mm long and the strut's eye is 10 mm in from that end, so the eye is 128 mm from the pivot.
12. **Strut, collar end (the rod's):** fit the steel tab into the collar's clevis, up to the shoulder of its Ø8 boss, which sits in the notch at the clevis's end, with an M4 × 16 countersunk screw from the +y side and an M4 nut in the far cheek's pocket. Snug it and thread-lock it; don't clamp the tab.
13. **Balance and drag:** let go of the grip at the bottom of the travel and near the stop. If it climbs, add ballast inside the head's box, close to its middle; then fine-tune with the collar (see [Balance](#balance)). Set the brake to taste.

## Screws

All from two kits, apart from the brake's M5 bolt: the AvrestYPT countersunk kit ([Amazon B0FMD5TMSH](https://www.amazon.com/dp/B0FMD5TMSH): M3 and M4 × 8, 12, 16, 20, with nuts) and the HELIFOUNER M4 × 30–50 socket head kit ([Amazon B0CDSKK7V1](https://www.amazon.com/dp/B0CDSKK7V1), with nuts). There are no heat-set inserts: each screw goes into a nut in a printed pocket, or a thread tapped into the print.

| Where | Screw | Into | Qty |
|---|---|---|---|
| Lever halves | M4 × 35 socket head cap, along the pivot axis through the hub, two from each end, heads in 7.5 mm counterbores | M4 nut in a hex pocket in the other half's end face | 4 |
| Shell | M4 × 50 socket head cap, from the top, down 13 mm counterbores, centred on the joint | M4 nut slid into a slot in the block's outer face, under the side cover | 4 |
| Side covers | M3 × 12 countersunk, from the cover's outer face | M3 thread tapped through the block or the shell's side wall | 8 |
| Brake | **M5 × 35 hex-head bolt**, head on the floor of the knob's hex pocket | M5 nut in the slot in the brake strap's head | 1 |
| Brake strap's hinge | M4 × 50 socket head cap, from the +y side, head in a counterbore | M4 nut in a hex pocket on the −y side | 1 |
| Strut eyes | M4 × 16 countersunk, head on the +y side | M4 nut in the far cheek's pocket | 2 |
| Strut collar clamp | M4 × 12 countersunk | M4 nut in the other ear's pocket | 2 |

The hinge pin is a fifth M4 × 50 from the HELIFOUNER kit.

Every screw and nut, to scale:

![Every screw and nut, to scale](renders/rev4_screw_sizes.png)

Between them, these label every screw and nut in the base:

![The shell's screws, from above](renders/rev4_screws_top.png)

![The lever's sensor end, bearing off: two heads and two nuts](renders/rev4_screws_lever_sensor.png)

![The lever's cable end, bearing off: the other two heads and nuts](renders/rev4_screws_lever_cable.png)

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
| X AUTOHAUX 6" 45 N gas strut | 1 | [Amazon B0CY267GFY](https://www.amazon.com/dp/B0CY267GFY), two for $13.69: see [The strut](#the-strut) |
| 25 × 23 mm carbon tube, 500 mm | 1 | roll-wrapped; used uncut |
| Worm-drive hose clamp, about 25–40 mm | 1 | on the socket's mouth |
| Compression spring, 10 mm OD, 10–15 mm free length | 1 | optional, for the brake knob |
| M5 × 35 hex-head bolt | 1 | any hardware store |
| Felt, 1.5 mm, 16 × 51 mm | 1 | on the brake strap |
| AS5600 module (WWZMDiB, Amazon B0CM3C8KFT) | 1 | with its ~4 × 2 mm diametric magnet |
| #10 × 1-1/2 in wood screws | 4 | desk mounting |

## Notes

- **The checks:** `python mk3_rev4.py --check` runs four checks, and all are clean.
  - **Every pair of parts** at 0°, 8°, 16°, 24°, 31.5° and 32°. The overlaps it allows are the intended ones: screws in their holes, the bearings' inner races on the trunnions, the felt on the strap, the strut's tabs in their clevises, and the hose clamp in its groove. Just past each stop, the lever meets the frame where it should: the pads on the pillars below 0°, both lugs on the up-stop pad above 32°.
  - **The brake's clearances,** measured as distances, not overlaps: through the whole travel, the strap stays 1.5 mm off the lever, the felt 0.02 mm off the hub, and the knob 6.4 mm or more off the lever; the strap is 0.5 mm off the pad's slot either side, and 1 mm off the shell's ramp.
  - **The assembly order:** the strap set down into the frame, leaning back; the lever lowered past it; the strap swung onto the hub; the shell lowered over both, its ramp swinging the strap forward.
  - **The openings' clearance:** the true 3D distance from the frame's front wall and the shell's front and top walls to the lever's halves, the hose clamp and the tube, every 0.25° from 0° to 32°, then every 0.02° round each wall's closest passes. None is under 2 mm. `--openings` runs this one alone.
- **Chamfers:** The shared chamfer step (`mk3_rev3.chamfer_edges`) once returned a valid frame with the down-stop pillars missing. `mk3_rev4.py`'s version refuses any set of chamfers that takes off more than chamfers could; the strut collar, which still uses the shared one, was checked and lost nothing.
- **Brake feel:** untested. The felt patch is 16 × 51 mm, and the drag per newton of bolt tension is worked out for felt on PETG at μ = 0.3. Fit the spring if the knob is too touchy without it.
- **Balance:** see [Balance](#balance). The lever is about 68 cm³ lighter than Rev 3's, mostly near the pivot, and that makes almost no difference: its load at 0° is 1.998 N·m against Rev 3's 1.996.
