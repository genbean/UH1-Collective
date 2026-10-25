# SEARCH CONT 4-way hat (head Rev 4)

Replaces the MkII thumbstick hat and the ringed search hat. It sits where the MkII hat did (`SEARCH` in `huey_head_r4.py`), uses the same four TE 1825910-6 tact switches, and changes nothing in the printed body. `python huey_head_r4.py <out dir>` builds it with the head and needs no MkII file; `hat_r4.py <out dir> [asm dir]` builds it alone.

The cap copies the real knob: a flanged round cone of 11 terraces on a curved profile (steep at the centre, flatter toward the rim), a centre pin, 28 mm across.

## How it is attached

| Part | Held by |
|---|---|
| Switches (4) | Drop into square pockets in the carrier from the front, buttons facing out, bases on the carrier floor. Their legs go through notches in the floor; solder the leads to the legs' sides. A dab of hot glue if loose. |
| Carrier (pockets, hub, floor) | Printed as part of the lower panel. It is a drum behind the panel's hat hole, 12.2 mm radius. |
| Bezel | 4 x M2 x 8 countersunk (AvrestYPT kit) through the bezel into M2 threads tapped in the carrier, on the diagonals. Its rim sits on the panel face. |
| Rocker plate | Not fastened. It sits on the switch buttons and is captured by the bezel over it; the buttons' springs push it forward. Its boss sits in the hub bore. Its four 4 mm legs (flared at the root, with a pocket for the flare in the bezel) are part of it and stand forward through the bezel's holes. |
| Cap | Glued onto the tips of the plate's four legs, last, after the bezel is on. Cap and plate then move as one rigid piece. |
| Set screw | M3 x 4 (HIQTRADEBYJJ kit), threaded into the plate's centre (tap the 2.5 mm pilot), from behind. |

## How it pivots

The rocker unit (cap, plate with its legs) rocks about one point: the tip of the M3 set screw in the plate's centre, pushed up against the bezel's flat underside by the four switch buttons. Pressing a face of the cap tilts the unit about that point. The pressed direction's plate arm goes back onto its button; the opposite arm lifts toward the bezel (0.8 mm of room at its end, enough for a 5 degree tilt). The two arms on the pivot's axis don't move, so a press doesn't touch the neighbours' switches. Pressing between two directions presses both. The buttons' own springs return and centre the cap. The cap floats 1.4 mm over the bezel so it can rock, and the legs have 0.3 mm of play in the bezel's holes.

Limits: the plate can only go back 0.1 mm at the centre (the set screw's rear end meets the hub bore's floor), so a straight push on the middle should stay under the switches' 0.15 mm minimum click travel. That depends on the preload below, so check it with a meter.

**Setting the preload.** A 1.5 mm hex key goes through the 2.4 mm hole in the carrier floor to the set screw's socket. Turning it out pushes the plate closer to the buttons. Turn it until the cap sits with no play and none of the four switches reads closed, with a meter on the leads; if any switch reads closed at rest, turn the screw back in. Its nominal setting has the plate just touching the buttons with the screw's tip 0.8 mm proud of the plate's front. Keep at least 0.65 mm of that: less and the far arm hits the bezel before the near button clicks.

## Assembly order

1. Thread the set screw into the plate from its boss side, tip about 0.8 mm proud of the plate's front.
2. Solder leads to the switches' legs, push the switches into their pockets, button out.
3. Lay the plate on the switches, legs up, boss in the hub bore.
4. Put the bezel over the legs and screw it down with the 4 M2 screws.
5. Glue the cap onto the four legs' tips.
6. Set the preload from behind.

## Parts

Bezel 1.6 mm thick, with a 7 mm pocket on its underside around each leg for the leg's flare. Legs 4 mm, flared to 5.6 mm over the last 0.6 mm at the plate, so they are strong printed standing up. The flare is trimmed to the arm's outline, so it never overhangs the end of an arm.

Panel (hat carrier built in), bezel, rocker plate (legs included), cap, 4 x M2 x 8 countersunk, 1 x M3 x 4 set screw, 4 TE 1825910-6. Print the cap base down, the plate with its legs down on the bed with its boss up (the legs hold it up, no supports), the bezel front face down. The panel prints face down like the others; the carrier needs no support.

## Checked in CAD

- No overlaps at rest, except the screws in their threads and the switch buttons' 0.01 mm seats.
- The rocker tilts 5 degrees in every direction with nothing hitting. A button needs 4.1 degrees to move 0.5 mm.
- Closest to the printed body: 1.8 mm, the south switch's leg tips. 6 mm to the grip, 10 mm to the tube. Solder blobs beyond the leg tips would take that margin: solder to the sides.

## Not checked

Printing it, the fit of the leg holes, the real pivot feel, the M2 threads in the print, how much the switches' height varies, and whether the cap's terraces print cleanly. Renders are in `renders/` (the cap, bezel, plate and legs are shown in `hat_exploded.png`, the pivot in `hat_section.png` and `hat_section_tilt.png`).
