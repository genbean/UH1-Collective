"""
MkIII collective base - Rev 4: narrow, 73 mm (2.87 in) wide

Rev 3 (../mk3_rev3.py) with the base cut down from 130 mm to 73 mm along the pivot axis, and the lever symmetrical about
the tube. Everything Rev 4 doesn't change comes from Rev 3: the gas strut, its collar and anchor, the socket for the
uncut 500 mm carbon tube, the down-stop pads and pillars, the MkII friction knob, the chamfers and the fits.

Same frame as Rev 3, except that the tube's plane is now the middle: origin = pivot centre, Y = pivot axis, Z = up,
tube along -X at 0 deg, +Y = USB side, -Y = sensor side. (Rev 3's tube is at y = -9, so Rev 3's collar, strut, pins
and hose clamp are moved +9 in y.)

The lever is split on the tube's plane (y = 0), not at the pivot axis as Rev 3, so each half prints on its joint face
with its trunnion up and each trunnion is one round piece: lever_sensor (-y) and lever_cable (+y). Four M4 x 35 socket
head cap screws run along the pivot axis through the hub, behind the bearings, with printed hollow dowels round them at
the joint to locate the halves.

Across the pivot axis, from the middle out (each side):
    hub                 |y| 0-21.5     60 mm across (Rev 3: 64 mm long, now 43), 3.5 mm past the socket boss
    bearing             |y| 22.5-29.5  6808-2RS thin-section, 40 x 52 x 7 (Rev 3: 6006-2RS, 30 x 55 x 13)
    retaining lip       |y| 29.5-31.5  the pillow blocks are 9 mm wide (Rev 3: 17); the base plate stops at their
                                       outer faces, 63 mm across
    trunnion end        |y| 29.5       40.1 mm across (the 6808's bore + 0.1), flush with the bearing's outer face
    side covers         |y| 31.5-36.5  5 mm square plates (Rev 3's: 15 mm deep)
One shell over the top takes the place of Rev 3's two bearing caps: a box over the lever whose side walls are the caps,
with a slot in its front and top for the socket boss, tube and top gusset to swing through, and a notch in its back
wall round the brake tower. It drops straight down over the lever and bolts on with four M4 x 50 socket head screws
into nuts slid into the pillow blocks' outer faces, under the side covers; a diamond grid of pyramids in the joint
locates it. The frame's front wall, under the shell's, carries the shell's cut for the lever on down, so they read as one.
The AS5600 board sits INSIDE the sensor trunnion, in a square pocket in its end, chip facing out, the board's face
level with the trunnion's end; the magnet sits in a pocket in the sensor cover's inside face, 1 mm off the chip. The
USB cable turns out of the axis toward the front on an 18 mm bend, through a pie-shaped relief in the cable trunnion's
end, and runs forward in a round tunnel, half in the pillow block's outer face and half in the cable cover, out
through the cover's front bevel; the cover goes on over a cable that's already fitted. The side covers are square plates over the bearings and the shell screws' nut slots,
their front and back ends bevelled 45 deg in line with the frame's corner chamfers.

Brake: Rev 3's drum, shoe and knob tower sat beside the hub, and there's no room for them now. The brake is behind
the hub instead. A narrow, tall shoe (12 mm wide, 44 mm tall, felt on its face) presses on the hub's own cylinder over
+-44 deg either side of the axis. It slides in a pocket 0.1 mm clear all round, so the friction's pull (up or down, as
the lever moves) can't shift it. The pocket is split at the axis like a bearing seat: its lower half is in a tower on
the frame, its upper half in the shell, and both come right up to the hub (0.8 mm off it), wrapping the shoe from its
front corners back. The shoe goes in once the lever is in, before the shell; a back plate screwed across both halves'
back faces carries the M5 nut. The MkII knob turns Rev 3's M5 x 30 hex bolt through that nut; the bolt's tip pushes
a printed spring cap, and the spring (Rev 3's, 10 mm OD, 6.5 mm long when fitted) pushes the shoe.
Up-stop: two lugs under the back of the hub, either side of the shoe, land on a pad behind the axis at 32 deg.

Run with a Python that has cadquery:
    python mk3_rev4.py            -> stl/ (printed), stl/ref/ (bought, reference), step/MkIII_Rev4_assembly.step
    python mk3_rev4.py --check    -> interference check through the travel
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)

import cadquery as cq                                                                    # noqa: E402
import mk3_rev3 as r                                                                     # noqa: E402  (imports Rev 1 as r.m)
from mk3_pivot import V, cyl, tube, box, fuse, hexprism, rot_y                           # noqa: E402

m = r.m
gusset_xz = r.gusset_xz


def chamfer_edges(shape, sizes=r.CHAMFERS, chunk=8, exclude=None):
    """Rev 3's chamfer_edges(), with a guard: OCC can hand back a valid solid with a whole feature missing (on the
    first try it dropped the frame's down-stop pillars), so a set of chamfers is only kept if the volume it takes off
    is about what chamfers that long and that size could take"""
    for c in sizes:
        es = r.sharp_edges(shape, exclude=exclude)
        v0 = shape.Volume()
        # each edge goes with its mirror twin across y = 0, kept or dropped together, so the chamfers stay symmetrical
        key = lambda b, sy=1: (round(b.xmin, 3), round(b.xmax, 3), round(sy * (b.ymin if sy > 0 else b.ymax), 3),
                               round(sy * (b.ymax if sy > 0 else b.ymin), 3), round(b.zmin, 3), round(b.zmax, 3))
        idx = {}
        for e in es:
            idx.setdefault(key(e.BoundingBox()), []).append(e)
        groups, seen = [], set()
        for e in es:
            if id(e) in seen:
                continue
            twin = [t for t in idx.get(key(e.BoundingBox(), -1), []) if t is not e and id(t) not in seen][:1]
            for t in [e] + twin:
                seen.add(id(t))
            groups.append([e] + twin)

        def ok(edges):
            res = r._chamfer(shape, edges, c)
            if res is None:
                return False
            dv = v0 - res.Volume()
            return -0.5 <= dv <= sum(e.Length() for e in edges) * c * c * 1.2 + 0.5

        keep = []
        for i in range(0, len(groups), chunk):
            part = [e for g in groups[i:i + chunk] for e in g]
            if ok(keep + part):
                keep += part
                continue
            for g in groups[i:i + chunk]:
                if ok(keep + g):
                    keep += g
        if keep:
            shape = shape.chamfer(c, None, keep)
    return shape
DY = -m.SOCK_Y                                   # +9: Rev 3's parts that sit on the tube's plane move here

# ---------------------------------------------------------------- across the pivot axis
HUB_R, HUB_HW = 30.0, 21.5
BRG_d, BRG_D, BRG_B = 40.0, 52.0, 7.0            # 6808-2RS
BRG_IR_SH, BRG_OR_SH = 44.0, 48.3                # inner race's outside, outer race's inside (approx.)
BRG_Y0 = HUB_HW + 1.0                            # bearing inner face (22.5)
BRG_Y1 = BRG_Y0 + BRG_B                          # (29.5)
BLOCK_Y1 = BRG_Y1 + 2.0                          # pillow block's outer face (31.5): a 2 mm lip holds the outer race
TRUN_OD = BRG_d + 0.1                            # Rev 3's +0.2 on the race's bore pressed on a hair too tight (as
                                                 # built, 2026-11-08), so +0.1
TRUN_OUT = BRG_Y1                                # (29.5) flush with the bearing's outer face (it was 0.5 past the block,
                                                 # at 32): the USB cable turns out of the axis just past it, inside the
                                                 # lip, which is what lets the covers be 5 mm
BRG_SEAT_D = BRG_D + 0.0                         # +0.1 (perfect on Rev 3's one-piece blocks) left the 6808 a little
                                                 # play in Rev 4's seat, split between the frame and the shell (as
                                                 # built, 2026-11-08), so 0.1 less
LIP_R = 23.0                                     # clears the inner race (22.0), holds the outer (24.15)
BLOCK_HW = m.BLOCK_HW                            # 37.5, as Rev 3
# side covers: square plates COVER_T thick on the pillow blocks' and the shell's side faces, COVER_HZ either side of the
# axis, over the bearings and the shell screws' nut slots, and 2 mm clear of the strut's hex-key hole below them. Their
# ends are bevelled 45 deg: the back on the plane of the frame's and shell's back chamfer (x + |y| = REAR_C), the front
# on the plane of the 0.8 mm chamfer on the pillow blocks' front corners, so both run on flush. Four M3 x 12 countersunk
# each, where the round covers had them, into M3 threads tapped right through the block's and the shell's 9 mm walls
# (COVER_TAP is the back plate's screws' tapped depth)
COVER_HOLE_R, COVER_T, COVER_HZ = 30.5, 5.0, 32.75
COVER_TAP, COVER_SCREW_L = 7.5, 12
COVER_FRONT_C = 0.8                              # the blocks' front corner chamfer (Rev 3's first size)
W_HALF = BLOCK_Y1 + COVER_T                      # 36.5: overall 73 mm
# AS5600 in the sensor trunnion's end: the board (0.915 in = 23.24 mm square, measured; 1.6 thick) in a square pocket
# 0.15 mm clear each side, its front face level with the trunnion's end (2.5 mm deeper than at first), on two ledges
# along its top and bottom edges (clear of both pad columns), with 3.5 mm behind it for the wires soldered in from the
# back and the DIR jumper. The chip sits inside the retaining lip; the magnet sits in a pocket in the sensor cover's
# inside face, 0.5 mm below it, 1 mm off the chip
BOARD = 23.24
BOARD_CLR, BOARD_T, LEDGE, BEHIND = 0.15, 1.6, 1.6, 3.5
BOARD_Y = (TRUN_OUT - BOARD_T, TRUN_OUT)         # |y| of the board's back and front (27.9, 29.5)
CHIP_Y1 = TRUN_OUT + 1.5                         # SOIC-8 top (31.0)
MAGNET_Y = CHIP_Y1 + m.MAGNET_GAP                # magnet face (32.0)
POCKET_FLOOR = BOARD_Y[0] - BEHIND               # (24.4)
# USB cable: along the axis, then an 18 mm bend (about 4x its 4.6 mm across) toward the front, then straight forward at
# USB_Y in a round tunnel USB_TUNNEL_R round, half in the pillow block's outer face (frame and shell) and half in the
# cable cover, out through the cover's front bevel. It leaves 1.1 mm of block to the shell screw's hole and 1.2 mm of
# cover over it. The bend starts inside the axial bore; where it would rub the turning trunnion's end, a pie-shaped
# relief flares the bore's mouth (usb_relief()). On the cable's way out it stays clear of everything by USB_CLR
USB_BEND_R, USB_Y = 18.0, BLOCK_Y1 + 1.3         # (32.8)
USB_R, USB_TUNNEL_R, USB_CLR = 2.3, 2.5, 0.5

# ---------------------------------------------------------------- lever
# Split on the tube's plane (y = 0), not at the pivot axis as Rev 3: two halves, lever_sensor (-y) and lever_cable (+y),
# each printed on its joint face with its trunnion up, so each trunnion is one round piece, printed the way the trunnion
# coupon was. Four M4 x 35 socket head cap screws (HELIFOUNER kit) run along the pivot axis through the hub, on a JS_R
# circle at +-JS_DEG from fore-aft, behind the bearings: heads in counterbores and nuts in hex pockets in the hub's end
# faces, diagonally, so each half has two heads and two nuts. A head seats JS_CB_D under the end face; the screw's tip
# stands 1 mm past its nut, 3 mm inside the far end face. Between the shoulder (r 20.9) and the hub's surface (r 30):
# the counterbores leave 1.55 mm of hub over them, the nut pockets (a flat toward the axis) 1.6, the dowel holes 1.5;
# the front pair's dowel holes are 2.4 mm off the socket's bore (at 45 deg they'd be 1.2). The bearings cover the
# pockets, so the screws go in before the bearings go on.
JS_R, JS_DEG = 24.7, 50.0
JS_SCREW_L = 35
JS_CB_R, JS_CB_D = 3.75, 5.0                     # 7.5 mm counterbore: the 7 mm head 0.25 clear; its top 1 mm under the face
JS_SEAT = HUB_HW - JS_CB_D                       # |y| 16.5: the head's seat
JS_TIP = JS_SCREW_L - JS_SEAT                    # |y| 18.5 on the far side
JS_NUT = (JS_TIP - r.LS_TIP_PAST_NUT - r.LS_NUT_T, JS_TIP - r.LS_TIP_PAST_NUT)   # |y| 14.3..17.5: the nut, pulled up
# (x, z, the side its head is on): front-top and back-bottom heads in lever_sensor, the other two in lever_cable
JOINT_SCREWS = [(sx * JS_R * math.cos(math.radians(JS_DEG)), sz * JS_R * math.sin(math.radians(JS_DEG)),
                 -1 if sx * sz < 0 else 1) for sx in (-1, 1) for sz in (1, -1)]
# Locating them: a printed hollow dowel round each screw at the joint, half in each half, like an engine's dowels to its
# gearbox (lever_dowel, x4, printed standing). Its holes are DOWEL_CLR clear a side (tune with the dowel-hole coupon),
# 0.2 deeper than the dowel's half so the faces close, with a 45 deg lead-in at the mouth that takes the first layer's
# squish. The steel screw inside carries the shear across the dowel's layers.
DOWEL_OD, DOWEL_ID, DOWEL_L = 7.5, 4.5, 8.0
DOWEL_CLR = 0.05                                 # 7.6 mm holes
DOWEL_DEPTH = DOWEL_L / 2 + 0.2                  # 4.2 each side
DOWEL_LEAD = 0.4
JOINT_CH = 0.3                                   # on the joint face's outer edges, against elephant's foot at the seam;
                                                 # none on the bores
# The fairing over the socket boss, on top and mirrored underneath (in place of Rev 3's 8 mm top gusset): FAIR_HW either
# side of the tube, from the hose-clamp groove's back edge back to the hub. Its top is one straight line from the boss's
# top at the groove to the hub's circle and tangent to it, so it runs into the hub without a corner; its long top edges
# are rounded FAIR_R.
GROOVE_X = -54.0                                 # the hose-clamp groove's back edge
FAIR_HW, FAIR_R = 10.5, 3.0
# The down-stop pads run inward into the lower fairing: filled from the pad's inner face (|y| 13.5) to the fairing's side
# (10.5; the fill starts inside it, past its rounded edge), over the pad's length, from the pad's bottom up into the
# boss. The pad's inner face would print as a flat overhang once the lever's split on y = 0; this way pad and fairing
# are one piece, with nothing hanging
PAD_FILL_Y = FAIR_HW - FAIR_R
STOP_DEG = r.STOP_DEG
# The gas strut's anchor. Rev 3's first, at x -12, z -40.5, balanced a 40 N strut, the bottom of the range the 45 N strut
# is sold as; the 45 N strut as bought lifted the lever (about +50..+70 g at the grip). Moved up and back to x -9.5,
# z -36.5 (Rev 3's frame has it too now) it balances 45 N to within 3 g at the grip over the whole travel (the strut 119 mm long at 0 deg, 140 at 32, in its
# 102..152 mm stroke): the strut's line passes closer to the pivot, so it has less leverage. The clevis's cheeks shrink
# to 6.5 mm round the eye (Rev 3: 8), 1.5 mm under the hub, and its back wall runs 2 mm under the hub to the pad.
# Rev 3's strut, collar pin, pins and clevis code read these from Rev 3's module, so they're set there too (this
# process only; Rev 3's own files don't change).
STRUT_F_DESIGN = 45.0
ANCH_X, ANCH_Z, CLEVIS_R = -9.5, -36.5, 6.5
r.ANCH_X, r.ANCH_Z, r.CLEVIS_R, r.STRUT_F_DESIGN = ANCH_X, ANCH_Z, CLEVIS_R, STRUT_F_DESIGN
ANCH_WALL_Z = -(HUB_R + 2.0)                     # the clevis's back wall's top, 2 mm under the hub
STRUT_KEY_R = 1.75                               # a 3.5 mm hole through the +y pillow block on the anchor screw's axis:
                                                 # a 2.5 mm hex key (2.9 across its corners) reaches its head. It's
                                                 # 2 mm below the side cover's bottom edge
# up-stop: two lugs under the back of the hub land on a pad behind the axis at STOP_DEG. The further back they land,
# the further back they swing at 0 deg, toward the webs behind the pillow blocks (x = 37): with the pad at z = -28.5 and
# the contact face ending at x = 24.4, their back corners come to x = 35.8 at 0 deg, 1.2 mm off the webs. The pad's top
# is 2 mm under the hub at its front edge.
USTOP_X, USTOP_Z = (15.0, 24.4), -28.5           # contact face at the stop, world x; the pad's top
USTOP_HW, USTOP_SLOT = 21.0, 11.0                # lugs from |y| 11 to 21: either side of the shoe and the brake tower (+-10)
LUG_R = math.hypot(USTOP_X[1], USTOP_Z)          # the lugs' furthest point from the axis (37.5)
PAD_X, PAD_DY, PAD_Z = r.PAD_X, r.PAD_DY, r.PAD_Z

# ---------------------------------------------------------------- frame
PLATE_X = (-65.0, 62.0)                          # the plate is BLOCK_Y1 either side: no wings
Z_PLATE, AXIS_H = r.Z_PLATE, r.AXIS_H
PED_X = (14.0, 29.5)                             # the up-stop pad, full width between the pillow blocks; the brake
                                                 # tower runs on from its back middle
CG_LEG = 8.0                                     # corner gussets at each end of each pillow block, 45 deg in plan
DESK = [(x, y) for x in (-57.0, 54.0) for y in (-24.0, 24.0)]   # past the pillow blocks' ends and the down-stop
                                                 # pillars, the screws' heads clear of every wall
# the shell over the top: a box on the pillow blocks, x +-BLOCK_HW, |y| <= BLOCK_Y1, z 0..SHELL_TOP, 3 mm walls; its side
# walls (|y| 22.5..31.5) are solid, the bearing caps; the brake housing's upper half runs on out of its back wall
SHELL_TOP, SHELL_T = 38.0, 3.0
SWEEP_CLR = 1.0                                  # the slot in its front and top: this far round the lever's sweep
# The front walls' opening, the frame's and the shell's alike: straight sides FRONT_HW either side of the tube (the
# down-stop pads' outer faces, 1 mm clear) from above the top down to the pivot axis, and a round bottom about it. The
# top wall's slot carries on from it: FRONT_HW wide over the socket boss's swing, then narrowing at 45 deg to the top
# gusset's width plus 1 mm a side, with a round end just past the gusset at the stop. Both are clean 2D cuts that
# contain the lever's whole sweep with 1 mm or more to spare.
FRONT_HW = PAD_DY[1] + SWEEP_CLR                 # 21
FRONT_ZC = -7.0                                  # the round bottom's centre: the lower fairing swings down to z -24.5 in
                                                 # the front walls' plane, 11.5 either side (1 mm clear included)
TOP_TAPER_X, TOP_NOSE_HW = -22.0, FAIR_HW + SWEEP_CLR + 1.0   # the taper starts here; 12.5: the upper fairing needs 11.5
TOP_NOSE_X = -5.0                                # in the top wall, back to x -5.6: the round end's centre
# the shell to the frame: four M4 x 50 socket head cap screws (the lever's HELIFOUNER kit), two each side, from the top
# down the middle of the shell's side walls, centred on the joint: the head's seat 25 mm above it, at the floor of a
# 13 mm counterbore, the tip 25 mm below. Each goes into an M4 nut slid into the pillow block from its outer face, just
# under the side cover's rim, its pocket 1 mm short of the tip. The nut sits flats-in: its inner flat stops it turning
# and keeps 0.9 mm of block to the inner face, and the counterbore keeps 0.9 mm of shell both sides.
CAP_BOLT_X, CAP_BOLT_Y = 30.5, 27.0
SHELL_SCREW_L = 50
SHELL_CB_R = 3.6                                 # the 7 mm heads, 0.1 mm clear
CAP_HEAD_Z = SHELL_SCREW_L / 2                   # 25: the joint at the screw's middle
CAP_NUT_Z = CAP_HEAD_Z - SHELL_SCREW_L + r.LS_TIP_PAST_NUT + r.LS_NUT_T   # -20.8: the nut pocket's top
# The joint between the frame and the shell: a diamond grid of square pyramids standing on the frame's top faces and
# sunk into the shell's, wherever the two meet, so the shell locates positively, fore and aft and side to side, as the
# screws pull it down. Diamond bases (corners fore-aft and across), 45 deg flanks (no supports, either part's way up),
# GRID_A from centre to corner, GRID_H tall with flat tops, GRID_LANE flat between them. The shell's sockets are
# GRID_CLR clear on the flanks and deeper than the pyramids, so the flat faces close on each other; none comes within
# GRID_EDGE of an edge or a hole.
GRID_A, GRID_H, GRID_LANE, GRID_CLR, GRID_EDGE = 1.2, 0.7, 0.6, 0.1, 0.5   # 2.4 mm across: the largest that also
                                                 # fits round the screws on the pillow blocks behind the bearings

# ---------------------------------------------------------------- brake (all on y = 0, z = 0 unless noted)
FELT_T = 1.5
SHOE_HW, SHOE_HZ = 6.0, 22.0                     # 12 wide, 44 tall
SHOE_CLR = 0.1                                   # per side, all round the shoe in its tunnel: no slop (tune it with the
                                                 # shoe-pocket coupon)
SHOE_X1 = 45.0                                   # its back face
SPRING_BORE = (35.0, SHOE_X1)                    # the spring's bore in the shoe's back, 10.6 across (Rev 3's seat)
SPRING_FIT = m.SPRING_FIT                        # 6.5 fitted, as Rev 3
CAP_X = (SPRING_BORE[0] + SPRING_FIT, 47.0)      # printed spring cap, 3.5 mm of it in the shoe's bore: the bolt's tip
                                                 # pushes its back face
# The brake housing, split at z = 0 like a bearing seat: the lower half on the frame, the upper half on the shell. It
# runs from TOWER_X0 (just behind the shoe's front corners at x = 22.5) to TOWER_X1, its front following the hub HUB_CLR
# off, and the pocket runs out through its back face. The shoe goes in with the shell off, standing back SHOE_IN while
# it's set down past the hub, then slid forward.
HUB_CLR = 0.8
TOWER_X0, TOWER_X1 = 24.0, 47.5
TOWER_HW = 10.0
SHOE_IN = 10.5
# The back: one 45 deg chamfer plane each side, |y| + x = REAR_C, from the pillow blocks' outer back corners through the
# frame, the shell and the back plate, so the three read as one block from behind.
REAR_C = BLOCK_HW + BLOCK_Y1                     # 69
# back plate: x TOWER_X1 .. +8.5, from just over the base plate up to the shell's top, the full width of the back face
# (|y| 21.5) tapering along the chamfer to 13 at its back face
BACK_T, BACK_Z = 8.5, Z_PLATE + 0.2
# its screws: M3 x 16 countersunk from its back face, into M3 threads tapped 7.5 mm deep. Three pairs, evenly spaced
# down the plate: one at its middle (z = -5.9, into the frame) and one BACK_PITCH above (into the shell) and below (into
# the frame). Two columns at y = +-8.8: the shoe's pocket runs out through the back face 6.1 either side of the middle,
# so the middle pair's pilots need to be this far out to keep 1.45 mm of wall off it (at +-7 they'd break into it), and
# the heads are still 0.75 mm inside the plate's 13 mm back face.
BACK_ZC = (BACK_Z + SHELL_TOP) / 2               # the plate's middle (-5.9)
BACK_PITCH = 32.9
BACK_SCREWS = [(y, BACK_ZC + k * BACK_PITCH) for y in (-8.8, 8.8) for k in (1, 0, -1)]
NUT5_X = TOWER_X1                                # the M5 nut, in a pocket in the back plate's front face
KNOB_X0 = TOWER_X1 + BACK_T + 3.0                # the knob's underside: 3 mm off the back plate, room to screw in
BOLT_L = 30.0                                    # Rev 3's M5 x 30 hex bolt, its head on the knob's floor
KNOB_FLOOR = CAP_X[1] + BOLT_L - KNOB_X0         # the knob's floor, raised to 18 mm (Rev 3's: 4) for the M5 x 30


def collar_pin(theta=0.0):
    return r.collar_pin(theta)


def moved(shape):
    return shape.translate(V(0, DY, 0))


# ================================================================ lever
def up_stop_lugs():
    """two blocks under the back of the hub, drawn as they sit at the stop (their faces on the pad, their tops inside the
    hub) and turned back to 0 deg. At 0 deg the part outside the hub is all below the split, in the lower half, and the
    hub between them is a plain cylinder for the felt"""
    return [rot_y(box(*USTOP_X, *sorted((s * USTOP_SLOT, s * USTOP_HW)), USTOP_Z, -5.0), -STOP_DEG) for s in (-1, 1)]


def sensor_pocket():
    """square pocket in the sensor trunnion's end: the board's seat, then a narrower recess behind it to the floor"""
    h = BOARD / 2 + BOARD_CLR
    seat = box(-h, h, -TRUN_OUT - 1, -BOARD_Y[0], -h, h)
    behind = box(-h, h, -BOARD_Y[0] - 0.01, -POCKET_FLOOR, -(h - LEDGE), h - LEDGE)
    return seat.fuse(behind)


def lever(pocket=True):
    """the whole lever, unsplit; pocket=False leaves out the sensor's pocket (the rest is symmetrical about y = 0)"""
    core = rot_y(cyl(HUB_R, (0, -HUB_HW, 0), (0, HUB_HW, 0)), 135)      # seam away from the split, the stop and the track
    boss = cyl(m.SOCK_BOSS_R, (-10, 0, 0), (-m.SOCK_MOUTH, 0, 0))
    shoulders = [cyl(BRG_IR_SH / 2 - 1.1, (0, s * HUB_HW, 0), (0, s * BRG_Y0, 0)) for s in (-1, 1)]
    trunnions = [cyl(TRUN_OD / 2, (0, s * BRG_Y0, 0), (0, s * TRUN_OUT, 0)) for s in (-1, 1)]
    gusset = fuse(fairing(1), fairing(-1))
    pads = [box(*PAD_X, *sorted((s * PAD_FILL_Y, s * PAD_DY[1])), PAD_Z, 0) for s in (-1, 1)]   # filled in to the fairing
    h = fuse(core, boss, gusset, *shoulders, *trunnions, *pads, *up_stop_lugs())
    cuts = [cyl(m.SOCK_BORE_R, (-m.SOCK_BOTTOM, 0, 0), (-m.SOCK_MOUTH - 1, 0, 0)),               # tube socket
            tube(m.SOCK_BOSS_R + 1, m.SOCK_BOSS_R - 1.2, (-54, 0, 0), (-63, 0, 0)),               # hose-clamp groove
            cyl(m.CABLE_R, (0, -POCKET_FLOOR - 0.5, 0), (0, TRUN_OUT + 1, 0)),                   # axial 1/2" bore
            cyl(m.CABLE_R, (-m.SOCK_BOTTOM - 1, 0, 0), (3, 0, 0)),                               # radial 1/2" bore
            strut_relief()] + ([sensor_pocket()] if pocket else [])                               # the strut's cylinder
    if pocket:
        cuts.append(usb_relief())                                                                 # the USB cable's bend
    for c in cuts:
        h = h.cut(c)
    return h.clean()


def hex_xz(cx, cz, af, y0, y1):
    """a hexagonal prism along y from y0 to y1, centred on (cx, cz), one flat facing the pivot axis"""
    phi = math.degrees(math.atan2(cz, cx))
    rc = af / 2 / math.cos(math.radians(30))
    pts = [V(cx + rc * math.cos(math.radians(phi + 30 + 60 * k)), y0, cz + rc * math.sin(math.radians(phi + 30 + 60 * k)))
           for k in range(6)]
    return cq.Solid.extrudeLinear(cq.Wire.makePolygon(pts + [pts[0]]), [], V(0, y1 - y0, 0))


def lever_joint_cuts():
    """per joint screw: its counterbore and clearance hole on the head's side, its nut's pocket on the other, and the
    dowel's hole either side of the joint with its lead-in"""
    cuts, out = [], HUB_HW + 1.5
    rd = DOWEL_OD / 2 + DOWEL_CLR
    for x, z, sh in JOINT_SCREWS:
        cuts += [cyl(JS_CB_R, (x, sh * JS_SEAT, z), (x, sh * out, z)),                                 # counterbore
                 cyl(m.LS_CLR_R, (x, sh * (JS_SEAT + 0.01), z), (x, -sh * (JS_NUT[0] + 0.01), z)),       # clearance
                 hex_xz(x, z, m.NUT_AF[4], -sh * JS_NUT[0], -sh * out),                                  # nut pocket
                 cyl(rd, (x, -DOWEL_DEPTH, z), (x, DOWEL_DEPTH, z))]                                     # dowel holes
        cuts += [cq.Solid.makeCone(rd + DOWEL_LEAD, rd, DOWEL_LEAD, V(x, 0, z), V(0, sy, 0)) for sy in (-1, 1)]
    return cuts


def lever_screws(theta=0.0):
    """the four M4 x 35s (reference), heads on their seats, and their nuts pulled up against the pockets' floors"""
    parts = []
    for x, z, sh in JOINT_SCREWS:
        parts += [cyl(r.CAP_D / 2, (x, sh * JS_SEAT, z), (x, sh * (JS_SEAT + r.CAP_K), z)),
                  cyl(2.0, (x, sh * JS_SEAT, z), (x, -sh * JS_TIP, z)),
                  hex_xz(x, z, 7.0, -sh * JS_NUT[0], -sh * JS_NUT[1]).cut(
                      cyl(2.0, (x, -sh * (JS_NUT[0] - 1), z), (x, -sh * (JS_NUT[1] + 1), z)))]
    return rot_y(fuse(*parts), theta)


def lever_dowel():
    """one hollow dowel, standing on its end as it prints"""
    d = tube(DOWEL_OD / 2, DOWEL_ID / 2, (0, 0, 0), (0, 0, DOWEL_L))
    return d.chamfer(0.4, None, [e for e in d.Edges() if e.geomType() == "CIRCLE" and e.radius() > DOWEL_OD / 2 - 0.01])


def lever_dowels(theta=0.0):
    """the four dowels in their holes, centred on the joint"""
    d0 = lever_dowel().rotate((0, 0, 0), (1, 0, 0), -90).translate(V(0, -DOWEL_L / 2, 0))   # along y
    return rot_y(fuse(*[d0.translate(V(x, 0, z)) for x, z, _ in JOINT_SCREWS]), theta)


def _channel(p):
    """on the socket, the radial bore or the axial bore, where the joint face meets them (no chamfer there)"""
    return -m.SOCK_MOUTH - 1 <= p.x <= m.CABLE_R + 0.1 and abs(p.z) <= m.SOCK_BORE_R + 0.05


_HALVES = []


def lever_halves(theta=0.0):
    """[lever_sensor (-y), lever_cable (+y)]. The cable half is split off the lever (without the sensor's pocket or the
    USB cable's relief, so symmetrical about y = 0), chamfered as Rev 3 everywhere but its joint face, and JOINT_CH round
    the joint face's outside edge, not on the bores. The sensor half is its mirror image, so their outsides match
    exactly, with the sensor's pocket cut and chamfered; then the cable half gets the USB cable's relief, chamfered the
    same way. Then the joint's screw and dowel holes go into both, their mouths left sharp (the counterbores come within
    0.05 mm of the bearing's shoulder)"""
    if not _HALVES:
        on_joint = lambda e: abs(e.BoundingBox().ymin) < 1e-4 and abs(e.BoundingBox().ymax) < 1e-4
        cable = chamfer_edges(lever(pocket=False).intersect(box(-200, 200, 0, 100, -100, 100)).clean(), exclude=on_joint)
        face = max((f for f in cable.Faces() if f.geomType() == "PLANE" and abs(f.Center().y) < 1e-4),
                   key=lambda f: f.Area())
        cable = cable.chamfer(JOINT_CH, None, [e for e in face.outerWire().Edges() if not _channel(e.positionAt(0.5))])
        sensor = cable.mirror("XZ").cut(sensor_pocket()).clean()
        k = BOARD / 2 + BOARD_CLR + 0.1
        in_pocket = lambda e: (lambda b: b.ymax < -POCKET_FLOOR + 0.1 and max(abs(b.xmin), abs(b.xmax), abs(b.zmin),
                                                                             abs(b.zmax)) < k)(e.BoundingBox())
        sensor = chamfer_edges(sensor, exclude=lambda e: not in_pocket(e))
        cable = cable.cut(usb_relief()).clean()
        in_relief = lambda e: (lambda b: b.ymin > POCKET_FLOOR and b.xmax < -2.0 and b.xmin > -16.0 and b.zmin > -10.0
                                         and b.zmax < 5.0)(e.BoundingBox())
        cable = chamfer_edges(cable, exclude=lambda e: not in_relief(e))
        for half in (sensor, cable):
            for c in lever_joint_cuts():
                half = half.cut(c)
            _HALVES.append(half.clean())
    return [rot_y(s, theta) for s in _HALVES]


# ================================================================ frame
def block_cuts(s):
    cuts = [cyl(BRG_SEAT_D / 2, (0, s * (BRG_Y0 - 0.5), 0), (0, s * BRG_Y1, 0)),         # bearing seat
            cyl(LIP_R, (0, s * (BRG_Y1 - 1), 0), (0, s * (BLOCK_Y1 + 1), 0))]           # retaining lip's bore
    for a in (45, 135, 225, 315):
        px, pz = m.on_circle(COVER_HOLE_R, a)
        cuts.append(cyl(m.TAP[3] / 2, (px, s * (BRG_Y0 - 1), pz), (px, s * (BLOCK_Y1 + 1), pz)))   # covers' M3: tap drill, right through the wall
    if s > 0:
        cuts.append(usb_tunnel())                                       # the USB cable's tunnel: the block's half
    return cuts


def anchor_clevis():
    """Rev 3's anchor_clevis() on the middle, at ANCH_X, ANCH_Z, its back walls running level, 2 mm under the hub, into
    the up-stop pad, and the gap between them filled from 1 mm behind the tab's round end: one solid block, for proper
    infill"""
    g = r.ROD_TAB_T + 0.6
    zt, zb = r.ANCH_Z + r.CLEVIS_R, Z_PLATE - 0.1
    ax = r.ANCH_X
    aft = [(ax, ANCH_WALL_Z), (PED_X[0] + 1, ANCH_WALL_Z), (PED_X[0] + 1, zb), (ax, zb)]
    parts = [gusset_xz(aft, -g / 2 - 0.1, g / 2 + 0.1).intersect(
        box(ax + r.ROD_TAB_W / 2 + 1.0, PED_X[0] + 2, -g, g, zb - 1, 0))]          # the gap between the walls, behind the tab
    for s in (-1, 1):
        y0, y1 = sorted((s * g / 2, s * (g / 2 + r.CLEVIS_T)))
        f0, f1 = sorted((s * (r.STRUT_ROD_D / 2 + r.ROD_CLEAR), s * (g / 2 + r.CLEVIS_T)))
        parts += [cyl(r.CLEVIS_R, (ax, y0, r.ANCH_Z), (ax, y1, r.ANCH_Z)),
                  box(ax - r.CLEVIS_R, ax + r.CLEVIS_R, y0, y1, zb, r.ANCH_Z),
                  gusset_xz(aft, y0, y1),
                  gusset_xz([(ax, zt), (ax - r.CLEVIS_RUN, zb), (ax, zb)], f0, f1)]
    return fuse(*parts)


def corner_gussets():
    """45 deg corner gussets (in plan) at both ends of each pillow block, CG_LEG along each wall:
    behind, inside    the block's inner face to the web's front face, kept 1.5 mm outside the up-stop lugs' swing
    in front, inside  the block's inner face to the down-stop pillar's back face, up to the pillar's top and 3 mm clear of
                      the hub
    in front, outside the block's front face to the pillar's outer face, up to the pillar's top"""
    def prism(pts, top):
        return (cq.Workplane("XY").workplane(offset=Z_PLATE - 0.1).polyline(pts).close()
                .extrude(top - Z_PLATE + 0.1).val())
    L, bx, yo, yi = CG_LEG, BLOCK_HW, BLOCK_Y1 - 0.5, BRG_Y0       # yo: 0.5 inside the block's outer face
    yw = BRG_Y0 + 0.5                                               # the web's and the pillar's outer faces (23)
    out = []
    for s in (-1, 1):
        q = lambda pts: [(x, s * y) for x, y in pts]
        out += [prism(q([(bx, yi + 0.5), (bx - 0.5 - L, yi + 0.5), (bx, yi - L)]), 0.0)
                .cut(cyl(LUG_R + 1.5, (0, s * (yi - L - 1), 0), (0, s * (yi + 1), 0))),                   # behind, inside
                prism(q([(-bx, yi + 0.5), (-bx + 0.5 + L, yi + 0.5), (-bx, yi - L)]), PAD_Z)
                .cut(cyl(HUB_R + 3.0, (0, s * (yi - L - 1), 0), (0, s * (yi + 1), 0))),                   # in front, inside
                prism(q([(-bx + 0.5, yw - 0.5), (-bx + 0.5, yo), (-bx - L, yw - 0.5)]), PAD_Z)]           # in front, outside
    return out


def frame():
    plate = (cq.Workplane("XY").box(PLATE_X[1] - PLATE_X[0], 2 * BLOCK_Y1, m.PLATE_T, centered=False)
             .translate((PLATE_X[0], -BLOCK_Y1, -AXIS_H)).edges("|Z").fillet(6).val())
    parts = [plate]
    for s in (-1, 1):
        y0, y1 = sorted((s * BRG_Y0, s * BLOCK_Y1))
        yi, yo = s * BRG_Y0, s * BLOCK_Y1
        parts += [box(-BLOCK_HW, BLOCK_HW, y0, y1, Z_PLATE, 0),                                       # pillow block
                  # down-stop pillar under the pad, run on into the pillow block
                  box(PAD_X[0], -BLOCK_HW + 0.5, *sorted((s * PAD_DY[0], yi + s * 0.5)), Z_PLATE - 0.1, PAD_Z),
                  # behind the pillow block: the web to the brake housing and the corner, out to the back chamfer
                  rear_fill(s, Z_PLATE - 0.1, 0.0)]
    pad = box(*PED_X, -(BRG_Y0 + 0.5), BRG_Y0 + 0.5, Z_PLATE - 0.1, USTOP_Z)                            # up-stop pad
    parts += [pad, brake_housing(Z_PLATE - 0.1, 0.0), anchor_clevis(), *corner_gussets(), front_wall()]
    f = fuse(*parts)

    a4, t4 = m.NUT_AF[4], m.NUT_T[4]
    cuts = []
    for s in (-1, 1):
        cuts += block_cuts(s)
        yb = s * CAP_BOLT_Y
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            zb, hc = CAP_NUT_Z - t4 - 0.3, a4 / math.sqrt(3)                       # hc: centre to corner
            cuts += [cyl(m.LS_CLR_R, (x, yb, CAP_HEAD_Z - SHELL_SCREW_L - 1), (x, yb, 1)),   # M4 x 50, past its tip
                     hexprism(a4, (x, yb, zb), (x, yb, CAP_NUT_Z)),                          # its nut, flats facing y,
                     box(x - hc, x + hc, *sorted((yb, s * (BLOCK_Y1 + 1))), zb, CAP_NUT_Z)]  # slid in from outside
    aw = (r.ROD_TAB_T + 0.6) / 2 + r.CLEVIS_T
    cuts += [cyl(r.PIN_R, (r.ANCH_X, -12, r.ANCH_Z), (r.ANCH_X, 12, r.ANCH_Z)),                      # anchor: M4 x 16,
             m.csk_hole(4, (r.ANCH_X, aw, r.ANCH_Z), (0, -1, 0), 1),                                   # head on +y,
             hexprism(a4, (r.ANCH_X, -aw + t4 + 0.2, r.ANCH_Z), (r.ANCH_X, -aw - 1, r.ANCH_Z)),          # nut on -y
             cyl(STRUT_KEY_R, (r.ANCH_X, BRG_Y0 - 1, r.ANCH_Z), (r.ANCH_X, BLOCK_Y1 + 1, r.ANCH_Z))]      # hex key in
    # brake: the shoe's pocket (lower half), and the back plate's lower screws
    cuts.append(shoe_tunnel())
    cuts.append(strut_body_sweep(1.5))                         # the strut's cylinder: through the front wall, over the
                                                               # clevis's front gussets
    for y, z in BACK_SCREWS:
        cuts.append(cyl(m.TAP[3] / 2, (TOWER_X1 - COVER_TAP, y, z), (TOWER_X1 + 1, y, z)))
    for x, y in DESK:
        cuts.append(cyl(2.75, (x, y, -AXIS_H - 1), (x, y, 0)))                                         # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def front_wall():
    """the frame's front wall between the pillow blocks, SHELL_T thick like the shell's above it, from the plate up to
    the joint, with the same cut for the lever's sweep as the shell's front wall, so the two read as one; the strut's
    cylinder passes through it, in a slot cut from its sweep (frame())"""
    w = box(-BLOCK_HW, -BLOCK_HW + SHELL_T, -BRG_Y0 - 0.1, BRG_Y0 + 0.1, Z_PLATE - 0.1, 0.0)
    return w.cut(front_cut()).clean()


def front_cut():
    """the front walls' opening (frame and shell): straight sides FRONT_HW either side of the tube from above the top
    down to the pivot axis, and a round bottom about it, straight through the 3 mm walls"""
    w, zc = FRONT_HW, FRONT_ZC
    return (cq.Workplane("YZ", origin=(-BLOCK_HW - 1.0, 0, 0)).moveTo(-w, SHELL_TOP + 2).lineTo(-w, zc)
            .threePointArc((0, zc - w), (w, zc)).lineTo(w, SHELL_TOP + 2).close().extrude(SHELL_T + 1.01).val())


def top_cut():
    """the top wall's slot: FRONT_HW wide from the front over the socket boss's swing, narrowing at 45 deg from
    TOP_TAPER_X to TOP_NOSE_HW either side, and a round end of that radius just past the top gusset at the stop"""
    w, g, xt, xe = FRONT_HW, TOP_NOSE_HW, TOP_TAPER_X, TOP_NOSE_X
    xn = xt + (w - g)                                                    # where the taper meets the nose's width
    return (cq.Workplane("XY", origin=(0, 0, SHELL_TOP - SHELL_T - 0.5)).moveTo(-BLOCK_HW - 2, -w).lineTo(xt, -w)
            .lineTo(xn, -g).lineTo(xe, -g).threePointArc((xe + g, 0), (xe, g)).lineTo(xn, g).lineTo(xt, w)
            .lineTo(-BLOCK_HW - 2, w).close().extrude(SHELL_T + 1.0).val())


def strut_body_sweep(clr):
    """the strut's cylinder, clr bigger all round, over the travel (-1 to 33 deg). As fitted it's on the base end, from
    the anchor's tab forward, so it swings up through the clevis's front gussets and the front wall. It pivots on the
    anchor's pin, so this is its long section revolved about the pin from the lowest angle to the highest, with the
    cylinder itself at both ends: smooth, without facets"""
    A = V(ANCH_X, 0, ANCH_Z)

    def u(th):
        cx, cz = r.collar_pin(th)
        return (V(cx, 0, cz) - A).normalized()

    s0, s1, h = r.TAB_L - 0.5, r.TAB_L + r.STRUT_BODY_L + 0.5, r.STRUT_BODY_D / 2 + clr
    u0, u1 = u(-1.0), u(STOP_DEG + 1.0)
    turn = math.degrees(math.atan2(u0.z, u0.x) - math.atan2(u1.z, u1.x))
    pts = [A + u0 * s0 + V(0, -h, 0), A + u0 * s1 + V(0, -h, 0), A + u0 * s1 + V(0, h, 0), A + u0 * s0 + V(0, h, 0)]
    fan = cq.Solid.revolve(cq.Wire.makePolygon(pts + [pts[0]]), [], turn, A, A + V(0, 1, 0))
    if fan.intersect(cyl(h - 0.5, (A + u1 * (s0 + 1)).toTuple(), (A + u1 * (s1 - 1)).toTuple())).Volume() < 1.0:
        fan = cq.Solid.revolve(cq.Wire.makePolygon(pts + [pts[0]]), [], -turn, A, A + V(0, 1, 0))   # the other way
    return fuse(fan, *[cyl(h, (A + uu * s0).toTuple(), (A + uu * s1).toTuple()) for uu in (u0, u1)])


STRUT_RELIEF_CLR = 1.5


def strut_relief(clr=STRUT_RELIEF_CLR):
    """the strut's cylinder, clr bigger all round, where the lever sees it over the travel (-1 to 33 deg). As fitted
    (cylinder on the base end) its anchor end comes in under the hub's front from 28 deg up, 0.94 mm into it at the
    stop, so this is cut from the lower half's underside. In the lever's frame the strut pivots on the collar's pin
    while its anchor swings round the pivot, so this is its long section (as far along as it ever reaches) revolved
    about the pin from the lowest angle to the highest, with the cylinder itself at both ends: smooth, no facets"""
    C = V(-r.COLLAR_D, 0, -r.COLLAR_E)                                   # the collar's pin, fixed on the lever

    def anchor(th):                                                      # the anchor, in the lever's frame
        c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
        return V(ANCH_X * c - ANCH_Z * s, 0, ANCH_X * s + ANCH_Z * c)

    t0, t1 = -1.0, STOP_DEG + 1.0
    span = [(anchor(t0 + 0.5 * k) - C).Length for k in range(int((t1 - t0) / 0.5) + 1)]
    d0 = min(span) - r.TAB_L - r.STRUT_BODY_L - clr                     # from the pin, toward the anchor; clr past
    d1 = max(span) - r.TAB_L + clr                                       # both ends too
    h = r.STRUT_BODY_D / 2 + clr
    w0, w1 = (anchor(t0) - C).normalized(), (anchor(t1) - C).normalized()
    turn = math.degrees(math.atan2(w0.z, w0.x) - math.atan2(w1.z, w1.x))
    pts = [C + w0 * d0 + V(0, -h, 0), C + w0 * d1 + V(0, -h, 0), C + w0 * d1 + V(0, h, 0), C + w0 * d0 + V(0, h, 0)]
    wire = cq.Wire.makePolygon(pts + [pts[0]])
    fan = cq.Solid.revolve(wire, [], turn, C, C + V(0, 1, 0))
    probe = cyl(h - 0.5, (C + w1 * (d0 + 1)).toTuple(), (C + w1 * (d1 - 1)).toTuple())
    if fan.intersect(probe).Volume() < 1.0:
        fan = cq.Solid.revolve(wire, [], -turn, C, C + V(0, 1, 0))      # the other way
    ends = [cyl(h, (C + w * ((anchor(t) - C).Length - r.TAB_L - r.STRUT_BODY_L - clr)).toTuple(),
                (C + w * ((anchor(t) - C).Length - r.TAB_L + clr)).toTuple()) for w, t in ((w0, t0), (w1, t1))]
    return fuse(fan, *ends)


def fairing(sz, grow=0.0):
    """the fairing over the socket boss (sz = 1) or under it (sz = -1), grow bigger all round (for the sweep): a prism
    FAIR_HW either side of the tube under the line from the boss's top at the groove to its tangent point on the hub"""
    px, pz = GROOVE_X - grow, m.SOCK_BOSS_R + grow
    rr = HUB_R + grow
    a = math.atan2(pz, px) - math.acos(rr / math.hypot(px, pz))         # the upper tangent point, from the groove
    tx, tz = rr * math.cos(a), rr * math.sin(a)
    hw = FAIR_HW + grow
    f = gusset_xz([(px, 0.0), (px, pz), (tx, tz), (tx, 0.0)], -hw, hw)
    if grow == 0.0:                                                     # round the two long top edges
        top = [e for e in f.Edges() if abs(abs(e.BoundingBox().ymin) - hw) < 1e-6 and
               abs(e.BoundingBox().ymax - e.BoundingBox().ymin) < 1e-6 and e.BoundingBox().zmin > pz - 0.1 and
               e.BoundingBox().xmax - e.BoundingBox().xmin > 10]
        f = f.fillet(FAIR_R, top)
    return f if sz > 0 else f.mirror("XY")


def lever_sweep():
    """what the frame's and shell's openings have to let through: the socket boss, the fairings top and bottom and the
    down-stop pads, SWEEP_CLR bigger all round, at every angle from 1 deg below the down-stop to 1 deg past the up-stop
    (2 deg apart: 0.02 mm between them at the shell)"""
    c = SWEEP_CLR
    boss = cyl(m.SOCK_BOSS_R + c, (-8.0, 0, 0), (-90.0, 0, 0))
    pads = [box(PAD_X[0] - c, PAD_X[1] + c, *sorted((s * (PAD_DY[0] - c), s * (PAD_DY[1] + c))), PAD_Z - c, 0)
            for s in (-1, 1)]                                                  # the down-stop pads, 20 out from the tube
    env = fuse(boss, fairing(1, c), fairing(-1, c), *pads)
    return fuse(*[rot_y(env, a) for a in range(-1, int(STOP_DEG) + 3, 2)])


def rear_fill(s, z0, z1):
    """behind a pillow block (side s), between z0 and z1: solid from the brake housing's side (|y| 9.5) out to the
    block's outer face and back to the housing's back face, its outer back corner cut off by the back chamfer"""
    bx, yo, yh = BLOCK_HW, BLOCK_Y1, TOWER_HW - 0.5
    pts = [(bx - 0.5, yh), (bx - 0.5, yo), (bx, yo), (TOWER_X1, REAR_C - TOWER_X1), (TOWER_X1, yh)]
    return (cq.Workplane("XY").workplane(offset=z0).polyline([(x, s * y) for x, y in pts]).close()
            .extrude(z1 - z0).val())


def joint_edge(e):
    """edges in the faces where the frame, shell and back plate meet: no chamfer there, so no groove shows at the seams
    (and none runs along the inside of the shoe's pocket)"""
    b = e.BoundingBox()
    return (abs(b.zmin) < 1e-4 and abs(b.zmax) < 1e-4) or (abs(b.xmin - TOWER_X1) < 1e-4 and abs(b.xmax - TOWER_X1) < 1e-4)


def shell():
    """the box over the lever, in place of Rev 3's two caps: its side walls are the caps (the bearing's upper half-seat
    and lip, the cover screws' upper threads, the cap screws counterbored from the top), joined by 3 mm front, back and
    top walls. The front and top are slotted for the lever's sweep; the upper half of the brake housing runs on out of
    the back wall. Prints top down"""
    h = BLOCK_HW
    s = box(-h, h, -BLOCK_Y1, BLOCK_Y1, 0, SHELL_TOP).cut(
        box(-h + SHELL_T, h - SHELL_T, -BRG_Y0, BRG_Y0, -1, SHELL_TOP - SHELL_T))
    for side in (-1, 1):
        for k in block_cuts(side):
            s = s.cut(k)
        yb = side * CAP_BOLT_Y
        for x in (-CAP_BOLT_X, CAP_BOLT_X):                                     # the M4 x 50s: clearance, counterbore
            s = s.cut(cyl(m.LS_CLR_R, (x, yb, -1), (x, yb, CAP_HEAD_Z + 0.01)))
            s = s.cut(cyl(SHELL_CB_R, (x, yb, CAP_HEAD_Z), (x, yb, SHELL_TOP + 1)))
    s = s.fuse(brake_housing(0.0, SHELL_TOP), *[rear_fill(side, 0.0, SHELL_TOP) for side in (-1, 1)])   # brake housing
    s = s.cut(shoe_tunnel())
    for y, z in BACK_SCREWS:
        s = s.cut(cyl(m.TAP[3] / 2, (TOWER_X1 - COVER_TAP, y, z), (TOWER_X1 + 1, y, z)))
    s = s.cut(front_cut()).cut(top_cut())                               # the lever's opening, clean
    s = s.cut(usb_tunnel())                                             # the USB cable's tunnel, through the back corner too
    return chamfer_edges(s.clean(), exclude=joint_edge)


# ================================================================ the joint's diamond grid
def grid_pyramid(cx, cy, a, z0, z1):
    """a square pyramid on a diamond base (its corners fore-aft and across), a from its centre to a corner at z = 0,
    45 deg flanks, from z0 up to z1 (cut flat there)"""
    k = math.sqrt(2)
    ws = [cq.Wire.makePolygon([V(cx + h, cy, z), V(cx, cy + h, z), V(cx - h, cy, z), V(cx, cy - h, z), V(cx + h, cy, z)])
          for z, h in ((z0, a - k * z0), (z1, a - k * z1))]
    return cq.Solid.makeLoft(ws, True)


def joint_face(frame_s, shell_s):
    """the face the frame and the shell share at z = 0, as a thin slab just under it"""
    t = 0.05
    return frame_s.intersect(box(-200, 200, -100, 100, -t, 0)).intersect(
        shell_s.intersect(box(-200, 200, -100, 100, 0, t)).translate(V(0, 0, -t)))


def _inset(slab, d, z0, z1):
    """the slab's top faces (z = 0) brought in d from their outlines and out d from their holes, as prisms z0..z1"""
    def pick(w, d, smaller):
        got = [(cq.Face.makeFromWires(o).Area(), o) for k in (d, -d) for o in w.offset2D(k, "arc")]
        return min(got)[1] if smaller else max(got)[1]
    out = []
    for f in slab.Faces():
        c = f.Center()
        if abs(c.z) > 1e-6 or f.normalAt(c).z < 0.5:
            continue
        face = cq.Face.makeFromWires(pick(f.outerWire(), d, True))
        for w in f.innerWires():
            face = face.cut(cq.Face.makeFromWires(pick(w, d, False)))
        for ff in face.Faces():
            ff = ff.translate(V(0, 0, z0))
            out.append(cq.Solid.extrudeLinear(ff.outerWire(), ff.innerWires(), V(0, 0, z1 - z0)))
    return fuse(*out)


_KNURL = {}


def knurl(frame_s, shell_s):
    """the joint's diamond grid as a knurl over the whole shared face: one lattice, symmetrical about both axes, kept
    GRID_EDGE inside every edge and hole (the shell's sockets GRID_CLR more), the pyramids at its edges cut off square
    and any piece under a third of a pyramid left out. Returns (pyramids, sockets, centres)."""
    if _KNURL:
        return _KNURL["v"]
    k, slab = math.sqrt(2), joint_face(frame_s, shell_s)
    keep = _inset(slab, GRID_EDGE, -0.3, GRID_H + 0.5)
    room = _inset(slab, GRID_EDGE - GRID_CLR, -0.3, GRID_H + 1.0)
    af = GRID_A + k * GRID_CLR
    zf = min(GRID_H + 0.3, af / k - 0.05)                               # 0.3 deeper than the pyramids, short of a point
    full = grid_pyramid(0, 0, GRID_A, -0.2, GRID_H).Volume()
    bb, d = keep.BoundingBox(), GRID_A + GRID_LANE / k
    inside = lambda x, y: keep.isInside(V(x, y, 0.1))
    males, females, centres = [], [], []
    for i in range(math.floor((bb.xmin - GRID_A) / d), math.ceil((bb.xmax + GRID_A) / d) + 1):
        for j in range(math.floor((bb.ymin - GRID_A) / d), math.ceil((bb.ymax + GRID_A) / d) + 1):
            if (i + j) % 2:
                continue
            x, y = i * d, j * d
            pm, pf = grid_pyramid(x, y, GRID_A, -0.2, GRID_H), grid_pyramid(x, y, af, -0.2, zf)
            ring = [(x + u, y + w) for u, w in ((0, 0), (GRID_A, 0), (-GRID_A, 0), (0, GRID_A), (0, -GRID_A))]
            hits = [inside(*q) for q in ring]
            if all(hits):
                m_, f_ = pm, pf.intersect(room)
            elif not any(hits) and not inside(x + GRID_A / 2, y + GRID_A / 2) and not inside(x - GRID_A / 2, y - GRID_A / 2) \
                    and not inside(x + GRID_A / 2, y - GRID_A / 2) and not inside(x - GRID_A / 2, y + GRID_A / 2):
                continue
            else:
                m_ = pm.intersect(keep)
                if m_.Volume() < full / 3:
                    continue
                f_ = pf.intersect(room)
            males.append(m_)
            females.append(f_)
            centres.append((x, y))
    # only those whose twin across y = 0 is there too (the USB tunnel takes a few off the +y side), so it stays symmetrical
    have = {(round(x, 3), round(y, 3)) for x, y in centres}
    keep = [i for i, (x, y) in enumerate(centres) if (round(x, 3), round(-y, 3)) in have]
    males, females, centres = [males[i] for i in keep], [females[i] for i in keep], [centres[i] for i in keep]
    _KNURL["v"] = (males, females, centres)
    return _KNURL["v"]


def grid_sites(frame_s, shell_s):
    """the knurl's pyramid centres"""
    return knurl(frame_s, shell_s)[2]


def joint_grid(frame_s, shell_s):
    """the frame with the pyramids on, the shell with their sockets in"""
    males, females, centres = knurl(frame_s, shell_s)
    return (frame_s.fuse(cq.Compound.makeCompound(males)).clean(),
            shell_s.cut(cq.Compound.makeCompound(females)).clean(), centres)


# ================================================================ side covers
def cover_seat_edge(e):
    """edges in the face a cover seats on: no chamfer there, so no groove shows at the seam"""
    b = e.BoundingBox()
    return abs(abs(b.ymin) - BLOCK_Y1) < 1e-4 and abs(abs(b.ymax) - BLOCK_Y1) < 1e-4


def _cover(s):
    """a square plate COVER_T thick on the side face (side s), COVER_HZ either side of the axis, its back bevelled on the
    back chamfer's plane and its front on the plane of the pillow blocks' front corner chamfer; four countersunk M3s"""
    y0, y1 = BLOCK_Y1, W_HALF
    xb = lambda y: REAR_C - y                                      # back bevel: x + |y| = REAR_C
    xf = lambda y: y - (REAR_C - COVER_FRONT_C)                    # front bevel: x - |y| = -(REAR_C - 0.8)
    pts = [(xf(y0), s * y0), (xb(y0), s * y0), (xb(y1), s * y1), (xf(y1), s * y1)]
    c = cq.Workplane("XY").workplane(offset=-COVER_HZ).polyline(pts).close().extrude(2 * COVER_HZ).val()
    for a in (45, 135, 225, 315):
        px, pz = m.on_circle(COVER_HOLE_R, a)
        c = c.cut(m.csk_hole(3, (px, s * y1, pz), (0, -s, 0), COVER_T + 1))
    return c


def cover_sensor():
    """the magnet in a pocket in its inside face, its face 0.5 mm below it and 1 mm off the chip. Prints outside face
    down"""
    c = _cover(-1).cut(cyl(m.MAGNET_POCKET / 2, (0, -BLOCK_Y1 + 0.5, 0), (0, -(MAGNET_Y + m.MAGNET_H + 0.1), 0)))
    return chamfer_edges(c.clean(), exclude=cover_seat_edge)


def cover_cable():
    """the cable's half of its tunnel in its inside face, round the bend and straight back out through the back bevel,
    so the cover goes on over a cable that's already fitted. Prints outside face down"""
    c = _cover(1).cut(usb_tunnel()).clean()
    return chamfer_edges(c, exclude=cover_seat_edge)


# ================================================================ brake
def brake_housing(z0, z1):
    """the block round the shoe's pocket between heights z0 and z1, its front HUB_CLR off the hub"""
    return box(TOWER_X0, TOWER_X1, -TOWER_HW, TOWER_HW, z0, z1).cut(cyl(HUB_R + HUB_CLR, (0, -20, 0), (0, 20, 0)))


def shoe_tunnel(clr=SHOE_CLR):
    return box(TOWER_X0 - 4, TOWER_X1 + 1, -SHOE_HW - clr, SHOE_HW + clr, -SHOE_HZ - clr, SHOE_HZ + clr)


def back_plate():
    """closes the pocket's back, screwed across the frame's and the shell's halves of the housing; the M5 nut sits in
    a pocket in its front face, and the bolt's push goes into it. Prints on its front face"""
    x0, x1 = TOWER_X1, TOWER_X1 + BACK_T
    pts = [(x0, -(REAR_C - x0)), (x1, -(REAR_C - x1)), (x1, REAR_C - x1), (x0, REAR_C - x0)]
    p = cq.Workplane("XY").workplane(offset=BACK_Z).polyline(pts).close().extrude(SHELL_TOP - BACK_Z).val()
    p = p.cut(hexprism(m.NUT_AF[5], (x0 - 0.1, 0, 0), (x0 + m.NUT_T[5] + 0.2, 0, 0)))
    p = p.cut(cyl(m.CSK[5][1] / 2, (x0 - 1, 0, 0), (x1 + 1, 0, 0)))
    for y, z in BACK_SCREWS:
        p = p.cut(m.csk_hole(3, (x1, y, z), (-1, 0, 0), BACK_T + 1))
    return chamfer_edges(p.clean(), exclude=joint_edge)


def shoe():
    s = box(HUB_R - 9.0, SHOE_X1, -SHOE_HW, SHOE_HW, -SHOE_HZ, SHOE_HZ)
    s = s.cut(cyl(HUB_R + FELT_T, (0, -20, 0), (0, 20, 0)))                                    # its face, under the felt
    s = s.cut(cyl(5.3, (SPRING_BORE[0], 0, 0), (SHOE_X1 + 1, 0, 0)))                          # the spring's bore
    return chamfer_edges(s.clean())


def felt():
    f = cyl(HUB_R + FELT_T, (0, -SHOE_HW + 0.5, 0), (0, SHOE_HW - 0.5, 0)).cut(cyl(HUB_R + 0.05, (0, -20, 0), (0, 20, 0)))
    return f.intersect(box(0, 50, -20, 20, -SHOE_HZ + 0.5, SHOE_HZ - 0.5)).clean()


def spring_cap():
    """the bolt's tip bears in the dimple on its back; the spring on its front"""
    c = cyl(5.1, (CAP_X[0], 0, 0), (CAP_X[1], 0, 0))
    c = c.cut(cq.Solid.makeCone(2.6, 0.5, 1.2, V(CAP_X[1] + 0.01, 0, 0), V(-1, 0, 0)))
    return chamfer_edges(c.clean(), sizes=(0.5,))


def knob_spring():
    p0 = V(SPRING_BORE[0], 0, 0)
    L = CAP_X[0] - SPRING_BORE[0]
    helix = cq.Wire.makeHelix(1.6, L, 4.6, p0, V(1, 0, 0))
    pl = cq.Plane(origin=helix.startPoint(), xDir=m._perp(helix.tangentAt(0)), normal=helix.tangentAt(0))
    return cq.Workplane(pl).circle(0.55).sweep(cq.Workplane().add(helix), isFrenet=True).val()


def friction_knob():
    """Rev 3's knob (the MkII knob with an M5 hex pocket) with its floor raised to KNOB_FLOOR, so Rev 3's M5 x 30 reaches
    the spring cap from it; lying on its side behind the back plate"""
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopoDS import TopoDS_Shape
    raw = TopoDS_Shape()
    StlAPI_Reader().Read(raw, r.MK2_KNOB)
    k = cq.Solid.makeSolid(cq.Shell.makeShell(cq.Shape.cast(raw).Faces())).fix()
    x0, y0, z0 = r.MK2_KNOB_AT
    k = k.translate(V(-x0, -y0, -z0))                                      # underside centre to the origin, axis +z
    zt, zf, hr = r.MK2_KNOB_H, KNOB_FLOOR, m.M5_HEAD_AF / 2 / math.cos(math.pi / 6)
    k = k.fuse(cyl(6.2, (0, 0, 0.5), (0, 0, zt - 0.3)))                     # fill the MkII's M6 pocket and hole
    k = k.cut(hexprism(m.M5_HEAD_AF, (0, 0, zf), (0, 0, zt + 1)))           # M5 hex pocket, open at the top
    k = k.cut(cyl(m.M5_CLR_R, (0, 0, -1), (0, 0, zf + 0.1)))                # M5 clearance up to the floor
    k = k.cut(cq.Solid.makeCone(hr + 0.8, hr - 0.2, 1.0, V(0, 0, zt - 1.0), V(0, 0, 1)))   # lead-in at the mouth
    return rot_y(k.clean(), 90).translate(V(KNOB_X0, 0, 0))                # axis +x


def brake_hardware():
    """M5 x 30 hex bolt (head on the knob's floor) and its nut"""
    hb = KNOB_X0 + KNOB_FLOOR
    bolt = fuse(hexprism(m.M5_HEAD_AF - 0.1, (hb, 0, 0), (hb + m.KNOB_BOLT[1], 0, 0)),
                cyl(2.4, (hb - BOLT_L, 0, 0), (hb + 0.1, 0, 0)))
    return fuse(bolt, m.nut(5, (NUT5_X + 0.1, 0, 0), (1, 0, 0)))


# ================================================================ bought parts and wiring
def bearing(s):
    y0, y1 = sorted((s * BRG_Y0, s * BRG_Y1))
    return (tube(BRG_D / 2, BRG_OR_SH / 2, (0, y0, 0), (0, y1, 0)), tube(BRG_IR_SH / 2, BRG_d / 2, (0, y0, 0), (0, y1, 0)),
            tube(BRG_OR_SH / 2, BRG_IR_SH / 2, (0, y0 + 0.5, 0), (0, y1 - 0.5, 0)))


def sensor_board():
    h = BOARD / 2
    pcb = box(-h, h, -BOARD_Y[1], -BOARD_Y[0], -h, h)
    chip = box(-2.5, 2.5, -CHIP_Y1, -TRUN_OUT, -2.0, 2.0)
    px = h - m.AS5600_PAD_X
    pins = fuse(*[cyl(0.5, (sx * px, -BOARD_Y[0] + 2.5, z), (sx * px, -BOARD_Y[0] - 1.0, z))
                  for sx in (-1, 1) for z in (-m.AS5600_PAD_PITCH, m.AS5600_PAD_PITCH)])
    return pcb.fuse(pins).clean(), chip


def magnet():
    return cyl(m.MAGNET_D / 2, (0, -MAGNET_Y, 0), (0, -(MAGNET_Y + m.MAGNET_H), 0))


def usb_path():
    """the USB cable's fixed run: the bend out of the axis toward the front, then straight forward at USB_Y"""
    s45 = math.sin(math.radians(45))
    rb, yk = USB_BEND_R, USB_Y - USB_BEND_R
    return (cq.Workplane("XY").moveTo(0, yk).threePointArc((-(rb - rb * s45), yk + rb * s45), (-rb, USB_Y))
            .lineTo(-90, USB_Y).wire().val())


def usb_relief():
    """the pie-shaped relief in the cable trunnion's end. The bend is fixed while the trunnion turns under it, so in the
    lever's frame the cable's way out swings from straight forward at 0 deg to 32 deg below it at the stop. This is the
    bend, USB_R + USB_CLR round, swung through that (and 1 deg past each end): its long section revolved about the axis,
    with the bend itself at both ends. Only the trunnion's end, round the bore's mouth, is in it"""
    rb, yk, w = USB_BEND_R, USB_Y - USB_BEND_R, USB_R + USB_CLR
    c = (-rb, yk)                                                         # the bend's centre (x, y), at z = 0
    band = (cq.Workplane("XY").moveTo(c[0] + rb - w, c[1])
            .threePointArc((c[0] + (rb - w) * math.cos(math.pi / 4), c[1] + (rb - w) * math.sin(math.pi / 4)),
                           (c[0], c[1] + rb - w))
            .lineTo(c[0], c[1] + rb + w)
            .threePointArc((c[0] + (rb + w) * math.cos(math.pi / 4), c[1] + (rb + w) * math.sin(math.pi / 4)),
                           (c[0] + rb + w, c[1]))
            .close().wire().val())
    band = cq.Face.makeFromWires(band).intersect(cq.Face.makeFromWires(
        cq.Wire.makePolygon([V(-60, -5, 0), V(-0.01, -5, 0), V(-0.01, 60, 0), V(-60, 60, 0), V(-60, -5, 0)])))
    wire = band.Faces()[0].outerWire()
    t0, t1 = -1.0, STOP_DEG + 1.0
    start = rot_y(cq.Face.makeFromWires(wire), -t0)                       # lever frame: the way out is rot_y(-theta)
    sweep = cq.Solid.revolve(start.outerWire(), [], t1 - t0, V(0, 0, 0), V(0, 1, 0))
    a = math.radians(-(t0 + t1) / 2)                                     # the bend's middle, at the middle angle
    px, py = -(rb - rb * math.sin(math.pi / 4)), yk + rb * math.sin(math.pi / 4)
    if not sweep.isInside(V(px * math.cos(a), py, -px * math.sin(a))):
        sweep = cq.Solid.revolve(start.outerWire(), [], -(t1 - t0), V(0, 0, 0), V(0, 1, 0))   # the other way
    bend = (cq.Workplane("XY").moveTo(0, yk - 1).lineTo(0, yk)
            .threePointArc((-(rb - rb * math.sin(math.pi / 4)), yk + rb * math.sin(math.pi / 4)), (-rb, USB_Y))
            .wire().val())
    ends = [rot_y(m.sweep_circle(w, bend, (0, yk - 1, 0), (0, 1, 0)), -t) for t in (t0, t1)]
    return fuse(sweep, *ends)


def usb_tunnel():
    """the cable's tunnel, USB_TUNNEL_R round along its run: cut from the +y pillow block and shell, and the cable cover"""
    return m.sweep_circle(USB_TUNNEL_R, usb_path(), (0, USB_Y - USB_BEND_R, 0), (0, 1, 0))


def usb_cable(theta=0.0, x0=-190.0):
    """down the tube and along the axis, turning with the lever; then the bend and the run out through the cover, fixed"""
    s45 = math.sin(math.radians(45))
    rr, yk = 5.0, USB_Y - USB_BEND_R
    inside = (cq.Workplane("XY").moveTo(x0, 0).lineTo(-rr, 0).threePointArc((-rr + rr * s45, rr - rr * s45), (0, rr))
              .lineTo(0, yk).wire().val())
    return fuse(rot_y(m.sweep_circle(USB_R, inside, (x0, 0, 0), (1, 0, 0)), theta),
                m.sweep_circle(USB_R, usb_path(), (0, yk, 0), (0, 1, 0)))


def sensor_wires():
    """from the board's back, along the axis, into the tube beside the USB cable"""
    pts = [V(6.8, -BOARD_Y[0] + 1.5, 3.0), V(0, -POCKET_FLOOR - 0.5, 4.0), V(0, -6, 4.0), V(-6, -2, 4.0),
           V(-190, -2, 4.0)]
    return m.sweep_circle(1.6, cq.Wire.makePolygon(pts), pts[0], (pts[1] - pts[0]).normalized())


def carbon_tube(length=160.0):
    return tube(m.TUBE_OD / 2, m.TUBE_ID / 2, (-m.SOCK_BOTTOM, 0, 0), (-m.SOCK_BOTTOM - length, 0, 0))


def shell_screw(x, y):
    """an M4 x 50 socket head cap screw (reference) with its head on the counterbore's floor, and its nut pulled up
    against its pocket's top: [screw, nut]"""
    zt = CAP_HEAD_Z - SHELL_SCREW_L
    return [fuse(cyl(r.CAP_D / 2, (x, y, CAP_HEAD_Z), (x, y, CAP_HEAD_Z + r.CAP_K)), cyl(2.0, (x, y, zt), (x, y, CAP_HEAD_Z))),
            hexprism(7.0, (x, y, CAP_NUT_Z - r.LS_NUT_T), (x, y, CAP_NUT_Z)).cut(
                cyl(2.0, (x, y, CAP_NUT_Z - 5), (x, y, CAP_NUT_Z + 1)))]


def hardware():
    """the fixed base's screws and nuts (reference): the shell's, the covers', the back plate's, the brake bolt and nut"""
    parts = [brake_hardware()]
    for y, z in BACK_SCREWS:
        parts.append(m.csk_screw(3, (TOWER_X1 + BACK_T, y, z), (-1, 0, 0), 16))
    for s in (-1, 1):
        yb = s * CAP_BOLT_Y
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            parts += shell_screw(x, yb)
        for a in (45, 135, 225, 315):
            px, pz = m.on_circle(COVER_HOLE_R, a)
            parts.append(m.csk_screw(3, (px, s * W_HALF, pz), (0, -s, 0), COVER_SCREW_L))
    return fuse(*parts)


# ================================================================ build + export
TURNS = ("lever_sensor", "lever_cable", "lever_screws", "lever_dowel", "carbon_tube", "hose_clamp", "sensor_pcb",
         "sensor_chip", "bearing_inner", "sensor_wires")
PRINTED = ["frame", "shell", "lever_sensor", "lever_cable", "lever_dowel", "shoe", "spring_cap", "back_plate",
           "cover_sensor", "cover_cable", "strut_collar", "friction_knob"]


_STATIC = {}
_COLLAR = []


def strut_collar(theta=0.0):
    """Rev 3's collar, unchanged (chamfered as Rev 3 prints it), on the middle"""
    if not _COLLAR:
        _COLLAR.append(moved(r.chamfer_edges(r._collar())))
    return rot_y(_COLLAR[0], theta)


def static_parts():
    """the parts that don't move, built once (chamfered, as Rev 3's)"""
    if not _STATIC:
        fr, sh, _ = joint_grid(chamfer_edges(frame(), exclude=joint_edge), shell())
        _STATIC.update({"frame": fr, "shell": sh, "shoe": shoe(), "spring_cap": spring_cap(),
                        "back_plate": back_plate(),
                        "cover_sensor": cover_sensor(), "cover_cable": cover_cable(), "friction_knob": friction_knob(),
                        "felt": felt(), "knob_spring": knob_spring(), "hardware": hardware(), "magnet": magnet(),
                        "bearing_outer": fuse(*[bearing(s)[0] for s in (-1, 1)]),
                        "bearing_seal": fuse(*[bearing(s)[2] for s in (-1, 1)])})
    return dict(_STATIC)


def build(theta=0.0):
    """every part at lever angle theta (the strut, collar and pins rebuilt for it)"""
    ls, lc = lever_halves(theta)
    pcb, chip = sensor_board()
    P = static_parts()
    P.update({"lever_sensor": ls, "lever_cable": lc, "lever_dowel": lever_dowels(theta), "strut_collar": strut_collar(theta),
              "bearing_inner": rot_y(fuse(*[bearing(s)[1] for s in (-1, 1)]), theta),
              "carbon_tube": rot_y(carbon_tube(), theta), "hose_clamp": rot_y(moved(m.hose_clamp()), theta),
              "gas_strut": moved(r.strut(theta)), "strut_pins": moved(r.pins(theta)),
              "lever_screws": lever_screws(theta), "sensor_wires": rot_y(sensor_wires(), theta),
              "usb_cable": usb_cable(theta),
              "sensor_pcb": rot_y(pcb, theta), "sensor_chip": rot_y(chip, theta)})
    return P


# ================================================================ interference check
# Overlaps that are meant to be there: presses and fits, screws in their holes (modelled at their thread's outside
# diameter, so they overlap a tapped pilot), parts that rest on each other, and the cables in their channels.
ALLOWED = {("bearing_inner", "lever_cable"), ("bearing_inner", "lever_sensor"), ("felt", "shoe"),
           ("frame", "hardware"), ("hardware", "shell"), ("back_plate", "hardware"), ("cover_sensor", "hardware"),
           ("cover_cable", "hardware"), ("friction_knob", "hardware"), ("hardware", "knob_spring"),
           ("hardware", "spring_cap"), ("knob_spring", "shoe"), ("knob_spring", "spring_cap"),
           ("frame", "strut_pins"), ("gas_strut", "strut_pins"), ("strut_collar", "strut_pins"),
           ("lever_cable", "lever_screws"), ("lever_screws", "lever_sensor"), ("carbon_tube", "hose_clamp"),
           ("hose_clamp", "lever_cable"), ("hose_clamp", "lever_sensor"), ("carbon_tube", "strut_collar"),
           ("cover_sensor", "magnet"), ("sensor_pcb", "sensor_wires"), ("frame", "gas_strut")}
# Parts that share a curved face (the races in their seats, the seal between them): the mesh boolean finds a sliver
# where the two faces' facets don't line up (2.3 mm3 for an outer race in its seat, up to 2.7 for an inner race against
# its seal). Up to this much is that sliver; more would be a real interference.
SHARED = {("bearing_outer", "frame"): 5.0, ("bearing_outer", "shell"): 5.0, ("bearing_inner", "bearing_seal"): 5.0,
          ("bearing_outer", "bearing_seal"): 5.0}


_MESH = {}


def _mesh(s, tol=0.02):
    """s tessellated (cached: the static parts are the same solids at every angle)"""
    import numpy as np
    import trimesh
    bb = s.BoundingBox()
    key = (s.hashCode(), round(s.Volume(), 3), round(bb.xmin, 3), round(bb.zmax, 3))
    if key not in _MESH:
        vs, fs = s.tessellate(tol, 0.1)
        _MESH[key] = trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs))
    return _MESH[key]


def overlap(a, b):
    """the volume two solids share, the larger of OCC's boolean and a mesh boolean (manifold). OCC alone can come back
    empty when it isn't: it gave 0 for the chamfered lower lever half against the strut's cylinder, 26 mm3 into it at
    32 deg. NaN if both fail. The mesh is 0.02 mm off true, so parts that share a curved face (a press fit, a race in
    its seat) show a sliver: those pairs are in ALLOWED"""
    import trimesh
    got = []
    try:
        got.append(a.intersect(b).Volume())
    except Exception:
        pass
    try:
        got.append(trimesh.boolean.intersection([_mesh(a), _mesh(b)], engine="manifold").volume)
    except Exception:
        pass
    return max(got) if got else float("nan")


def check(angles=(0.0, 8.0, 16.0, 24.0, 31.5, 32.0)):
    names = None
    for th in angles:
        P = build(th)
        names = sorted(P)
        bb = {k: P[k].BoundingBox() for k in names}
        hits = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if (a, b) in ALLOWED:
                    continue
                A, B = bb[a], bb[b]
                if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
                    continue
                # solid by solid: OCC can hand back a whole solid of a multi-solid part as the "overlap" (it did for
                # the collar's screw against the lever, 30 mm apart)
                v = sum(overlap(sa, sb) for sa in P[a].Solids() for sb in P[b].Solids()
                        if sa.BoundingBox().xmax >= sb.BoundingBox().xmin and sb.BoundingBox().xmax >= sa.BoundingBox().xmin
                        and sa.BoundingBox().zmax >= sb.BoundingBox().zmin and sb.BoundingBox().zmax >= sa.BoundingBox().zmin
                        and sa.BoundingBox().ymax >= sb.BoundingBox().ymin and sb.BoundingBox().ymax >= sa.BoundingBox().ymin)
                if v != v:
                    hits.append(f"{a} / {b} NOT CHECKED (both booleans failed)")
                elif v > SHARED.get((a, b), 0.01):
                    hits.append(f"{a} / {b} {v:.2f}")
        print(f"{th:5.1f} deg: " + ("clear" if not hits else "; ".join(hits)))


def check_assembly(step=2.0):
    """the order it goes together in: the lever (halves screwed up on their dowels, bearings on) lowered straight down
    into the bare frame from 80 mm up; the shoe (felt, spring and cap in it) set down into the frame's half of its pocket
    standing SHOE_IN back, from 60 mm up, then slid forward onto the hub; then the shell lowered straight down over all
    of it from 80 mm up. Part by part, so a race landing in its seat is held to SHARED's sliver like check()"""
    S = static_parts()
    ls, lc = lever_halves(0.0)
    lever_b = {"lever_sensor": ls, "lever_cable": lc, "lever_screws": lever_screws(0.0), "lever_dowel": lever_dowels(0.0),
               "bearing_outer": S["bearing_outer"], "bearing_seal": S["bearing_seal"],
               "bearing_inner": fuse(*[bearing(s)[1] for s in (-1, 1)])}
    shoe_b = {"shoe": S["shoe"], "felt": S["felt"], "spring_cap": S["spring_cap"]}
    worst = {}

    def meet(p, q):
        a, b = p.BoundingBox(), q.BoundingBox()
        return (a.xmax >= b.xmin and b.xmax >= a.xmin and a.ymax >= b.ymin and b.ymax >= a.ymin and
                a.zmax >= b.zmin and b.zmax >= a.zmin)

    def hit(group, d, fixed, at):
        """each part of the moving group, moved by d, against each fixed part"""
        for a, pa in group.items():
            pa = pa.translate(d)
            for b, pb in fixed.items():
                vol = sum(overlap(sa, sb) for sa in pa.Solids() for sb in pb.Solids() if meet(sa, sb))
                key = f"{a} / {b}"
                if vol != vol:
                    worst[key + " NOT CHECKED"] = (0.0, at)
                elif vol > SHARED.get(tuple(sorted((a, b))), 0.01):
                    worst[key] = max(worst.get(key, (0, 0)), (vol, at))

    frame_ = {"frame": S["frame"]}
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        hit(lever_b, V(0, 0, z), frame_, z)
    for i in range(int(60 / step) + 1):
        z = 60.0 - i * step
        hit(shoe_b, V(SHOE_IN, 0, z), {**frame_, **lever_b}, z)
    for i in range(int(SHOE_IN / 0.5) + 1):
        d = SHOE_IN - i * 0.5
        hit(shoe_b, V(d, 0, 0), {**frame_, **lever_b}, d)
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        hit({"shell": S["shell"]}, V(0, 0, z), {**frame_, **lever_b, **shoe_b}, z)
    print("lever in, shoe in, shell on: " + ("clear" if not worst else
          "; ".join(f"{k} {v:.2f} mm3 at {zz:.1f}" for k, (v, zz) in worst.items())))


def export():
    P = build(0.0)
    one = {"lever_dowel": lever_dowel()}                       # one, standing as it prints: print four
    for name in PRINTED:
        shp = one.get(name, P[name])
        print(f"{name:16s} valid={shp.isValid()} vol={shp.Volume():9.1f}" + ("  (print 4)" if name in one else ""))
    for name, shp in P.items():
        shp = one.get(name, shp)
        sub = os.path.join(HERE, "stl") if name in PRINTED else os.path.join(HERE, "stl", "ref")
        os.makedirs(sub, exist_ok=True)
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(sub, f"{name}.stl"), tolerance=0.04, angularTolerance=0.12)
    os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    asm = cq.Assembly(name="MkIII_Rev4")
    for name, shp in P.items():
        asm.add(shp, name=name)
    asm.export(os.path.join(HERE, "step", "MkIII_Rev4_assembly.step"))
    print("done")


# ================================================================ balance
def balance(plot=None):
    """the strut's lift against the head's weight, at the grip, with Rev 4's lever and anchor (Rev 3's model: the head,
    tube and cables forward of the pivot, the lever halves, screws, collar and half the strut behind it)"""
    ls, lc = lever_halves(0.0)
    items = r.rear_items({"lever_upper": ls, "lever_lower": lc, "strut_collar": strut_collar(0.0)})
    items[2] = (4 * 3.6 + r.printed_mass(lever_dowels(0.0), infill=1.0), V(0, 0, 0))   # the joint's screws, nuts and
                                                                                        # dowels: centred on the pivot
    load = lambda t: r.gravity(t, items) * 9.80665                                         # N*mm, nose down
    grip = lambda nmm: nmm / 9.80665e-3 / r.GRIP_R                                          # N*mm -> g at the grip
    th = r.frange(STOP_DEG, 0.5)
    L0, L1 = (math.hypot(r.collar_pin(t)[0] - ANCH_X, r.collar_pin(t)[1] - ANCH_Z) for t in (0, STOP_DEG))
    print(f"anchor x {ANCH_X}, z {ANCH_Z}: strut {L0:.0f} mm at 0 deg -> {L1:.0f} at {STOP_DEG:.0f} "
          f"(stroke {r.STRUT_COMP:.0f}..{r.STRUT_EXT:.0f}); load {load(0) / 1000:.3f} N*m at 0 deg")
    rows = []
    for F in (40.0, STRUT_F_DESIGN, 50.0, r.STRUT_F_RANGE[1]):
        err = [grip(r.strut_torque(t, F) - load(t)) for t in th]
        rows.append((F, err))
        print(f"  {F:.0f} N: {min(err):+.0f} .. {max(err):+.0f} g at the grip (+ = rises)")
    for k in r.COLLAR_RANGE:
        print(f"  collar {k:+.0f} mm: {grip(r.strut_torque(0, STRUT_F_DESIGN, k) - r.strut_torque(0, STRUT_F_DESIGN)):+.0f} g at 0 deg")
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ink, ink2, grid, surf = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
        cols = {40.0: "#2a78d6", STRUT_F_DESIGN: "#eb6834", 50.0: "#1baf7a", r.STRUT_F_RANGE[1]: "#8a5cc7"}
        fig, ax = plt.subplots(figsize=(8.4, 4.6))
        fig.patch.set_facecolor(surf)
        ax.set_facecolor(surf)
        ax.grid(True, color=grid, lw=0.8)
        for sd in ("top", "right"):
            ax.spines[sd].set_visible(False)
        ax.axhline(0, color=ink2, lw=1)
        for F, err in rows:
            ax.plot(th, err, color=cols[F], lw=2.4 if F == STRUT_F_DESIGN else 1.6,
                    label=f"{F:.0f} N" + ("  (as bought: the design point)" if F == STRUT_F_DESIGN else ""))
        ax.set_xlim(0, STOP_DEG)
        ax.set_xlabel("lever angle, deg (0 = down-stop)", color=ink2)
        ax.set_ylabel(f"out of balance at the grip ({r.GRIP_R:.0f} mm), g\n+ = rises, - = drops", color=ink2)
        ax.set_title(f"MkIII Rev 4: the strut's anchor at x {ANCH_X}, z {ANCH_Z}", loc="left", color=ink, fontsize=12)
        ax.legend(loc="center right", frameon=False, fontsize=9, bbox_to_anchor=(1.0, 0.52))
        fig.savefig(plot, dpi=150, bbox_inches="tight", facecolor=surf)
        print("wrote", plot)


# ================================================================ fit-test coupons for the 6808
# Rev 3's coupon plates (Rev 1's coupon_plate: steps -0.2, 0, +0.2 on the diameter, engraved), sized for the 6808-2RS.
# Printed and tried, 2026-11-08: the trunnion's 0 (40.1) and the seat's 0 (52.0) both fit the 6808 perfectly, so
# TRUN_OD and BRG_SEAT_D stand. The tube socket is Rev 3's, which fit perfectly as built, so it has no coupon.
def coupon_trunnion(d, h=8.0, sh=2.0):
    """the trunnion's stub on its inner-race shoulder, with the 1/2" bore, standing on the shoulder"""
    c = fuse(cyl(BRG_IR_SH / 2 - 1.1, (0, 0, 0), (0, 0, sh)), cyl((TRUN_OD + d) / 2, (0, 0, sh), (0, 0, sh + h)))
    return c.cut(cyl(m.CABLE_R, (0, 0, -1), (0, 0, sh + h + 1)))


def coupon_seat(d, depth=BRG_B, lip=BLOCK_Y1 - BRG_Y1, wall=4.0):
    """the pillow block's seat and lip as a ring, lip down; the 6808 presses in from the top"""
    c = cyl(BRG_SEAT_D / 2 + wall, (0, 0, 0), (0, 0, lip + depth))
    c = c.cut(cyl((BRG_SEAT_D + d) / 2, (0, 0, lip), (0, 0, lip + depth + 1)))
    return c.cut(cyl(LIP_R, (0, 0, -1), (0, 0, lip + 1)))


def coupon_shoe_pocket(d, length=10.0, wall=4.0):
    """10 mm of the brake shoe's tunnel, printed as the frame prints it (its axis level, its roof a bridge). The step
    changes the clearance across it, on its width and height alike: -0.2 / 0 / +0.2 = 0 / 0.1 / 0.2 mm a side. Slide
    the printed shoe through each: no rattle, no rocking, and still sliding under a finger"""
    w, h = 2 * (SHOE_HW + SHOE_CLR) + d, 2 * (SHOE_HZ + SHOE_CLR) + d
    c = box(-w / 2 - wall, w / 2 + wall, 0, length, 0, h + 2 * wall)
    return c.cut(box(-w / 2, w / 2, -1, length + 1, wall, wall + h)).clean()


def coupon_dowel_hole(d, w=14.0, h=8.0):
    """one of the lever's dowel holes as the halves print it: opening on the bed with its lead-in, the screw's clearance
    hole on through, so its ceiling bridges the same ring. The step is on the hole's diameter: 7.4 / 7.6 / 7.8. A printed
    dowel should push in by hand with no play"""
    rd = DOWEL_OD / 2 + DOWEL_CLR + d / 2
    c = box(-w / 2, w / 2, -w / 2, w / 2, 0, h)
    c = c.cut(cyl(rd, (0, 0, -1), (0, 0, DOWEL_DEPTH))).cut(cyl(m.LS_CLR_R, (0, 0, -1), (0, 0, h + 1)))
    return c.cut(cq.Solid.makeCone(rd + DOWEL_LEAD, rd, DOWEL_LEAD, V(0, 0, 0), V(0, 0, 1))).clean()


def export_coupons():
    out = os.path.join(HERE, "stl", "coupons")
    os.makedirs(out, exist_ok=True)
    for name, f in (("coupon_trunnion_6808", coupon_trunnion), ("coupon_bearing_seat_6808", coupon_seat),
                    ("coupon_shoe_pocket", coupon_shoe_pocket), ("coupon_dowel_hole", coupon_dowel_hole)):
        shp = m.coupon_plate(f)
        bb = shp.BoundingBox()
        print(f"{name:26s} valid={shp.isValid()} size={bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}")
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(out, f"{name}.stl"), tolerance=0.04, angularTolerance=0.12)


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        check()
        check_assembly()
    elif "--balance" in sys.argv[1:]:
        balance(plot=os.path.join(HERE, "renders", "strut_balance_r4.png"))
    elif "--coupons" in sys.argv[1:]:
        export_coupons()
    else:
        export()
