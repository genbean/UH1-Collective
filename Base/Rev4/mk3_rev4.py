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
with an opening in its front and top that follows the lever's sweep 2 mm clear, solid behind the hub
round the brake's bay and the knob's seat. It drops straight down over the lever and bolts on with four M4 x 50 socket head screws
into nuts slid into the pillow blocks' outer faces, under the side covers; a diamond grid of pyramids in the joint
locates it. The frame's front wall, under the shell's, carries the shell's cut for the lever on down, so they read as one.
The AS5600 board sits INSIDE the sensor trunnion, in a square pocket in its end, chip facing out, the board's face
level with the trunnion's end; the magnet sits in a pocket in the sensor cover's inside face, 1 mm off the chip. The
USB cable turns out of the axis toward the front on an 18 mm bend, through a pie-shaped relief in the cable trunnion's
end, and runs forward in a round tunnel, half in the pillow block's outer face and half in the cable cover, out
through the cover's front bevel; the cover goes on over a cable that's already fitted. The side covers are square plates over the bearings and the shell screws' nut slots,
their front and back ends bevelled 45 deg in line with the frame's corner chamfers.

Brake: a strap behind the hub. A rigid printed strap, 18 mm wide and 8 mm deep, lined with 1.5 mm felt, wraps the
hub's back between the up-stop lugs, from 54 deg below the axis to 42 above (the felt from 52 to 40), down into the
up-stop pad's slot and up under its head. Its bottom end is a knuckle on an M4 x 50
pin through the up-stop pad, just behind the strut's clevis, in a slot 0.5 mm clear either side that keeps it 1.5 mm or
more off the lugs; gussets run from the knuckle into the band, and from the band's top up into a solid head carrying
an M5 nut. The knob sits in a seat sunk into the shell's top, and its M5 x 35 bolt leans forward 30 deg from vertical,
so turning it draws the head up and forward and the strap swings about its hinge onto the hub: 41 mm of leverage
about the hinge, where a vertical bolt would get 12. The shell is solid behind the hub, so the seat's load goes
straight into its walls. The knob has a pocket in its underside for an optional spring; without one it sits on the
seat. The strap goes in before the lever and leans back onto its bay's back wall while the lever drops past it; a
ramp in the shell's bay swings it forward onto the hub as the shell goes on, so the nut is on the bolt's axis.
Up-stop: two lugs under the back of the hub, either side of the strap, land on a pad behind the axis at 32 deg.

Run with a Python that has cadquery:
    python mk3_rev4.py            -> stl/ (printed), stl/ref/ (bought, reference), step/MkIII_Rev4_assembly.step
    python mk3_rev4.py --check    -> interference check through the travel, the brake's clearances, the assembly
                                     order, the openings' clearance
    python mk3_rev4.py --openings -> the openings' clearance alone
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
COVER_HOLE_R, COVER_T, COVER_HZ = 30.5, 5.0, 32.75
COVER_SCREW_L = 12
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
USTOP_HW, USTOP_SLOT = 21.0, 11.0                # lugs from |y| 11 to 21: either side of the brake strap (+-9)
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
# The lever's opening in the front walls (the frame's and the shell's: one outline, so they read as one) and in the top
# wall: each a clean 2D cut straight through its 3 mm wall, of lines, arcs and ellipse arcs, that follows the lever's
# sweep from the down-stop to the up-stop SWEEP_CLR off everything that passes (the socket boss, the fairings and their
# rounds, the down-stop pads, the hose clamp), measured in 3D (check_openings()). Front walls, from the bottom up:
#   the lower fairing's tab   OPEN_FAIR either side, its bottom open_bottom() (-24.7), its corners rounded FAIR_R +
#                             SWEEP_CLR (the fairing at 0 deg, in the front wall's back face)
#   the boss                  a circle OPEN_BOSS about the axis up to the joint, then straight sides on up
#   the pads' reliefs         from 20 deg on, the pads' back corners swing up through the walls: each side bows out on
#                             one arc to OPEN_PAD, runs straight up and turns back in on a small one under the pads'
#                             tops at the stop
#   the boss at the stop      an ellipse, the boss's section in the front face at 32 deg (OPEN_ELL_Z its centre, the
#                             boss's tilt stretching it to OPEN_ELL_B tall), up through the top
# The joint between the fairing's tab and the boss's circle, and the reliefs' ends, are rounded. Top wall, from the front:
# the boss's footprint at the stop (TOP_ELL, an ellipse), rounded into straight sides OPEN_FAIR either side over the
# fairing, and a square end at TOP_END_X where the fairing's top passes under the wall at the stop, its corners
# quarter-ellipses TOP_END_A long, the fairing's rounds' shadow.
SWEEP_CLR = 2.05                                 # 2 mm, and 0.05 so that no check reads under 2
OPEN_BOSS = m.SOCK_BOSS_R + SWEEP_CLR            # 20.05
OPEN_PAD = PAD_DY[1] + SWEEP_CLR                 # 22.05
OPEN_FAIR = FAIR_HW + SWEEP_CLR                  # 12.55
OPEN_ELL_Z, OPEN_ELL_B = 23.4, 23.75             # BLOCK_HW tan 32 = 23.4; (18 + 2.05) / cos 32 = 23.65, and 0.1 for the
                                                 # boss's top rising in front of the face
OPEN_EAR = (6.4, 15.0, 23.8, 2.25, 4.0, 1.0)     # the reliefs: leave the boss's side at z, reach OPEN_PAD at z, leave it at
                                                 # z, top corner's radius; the fillets at the bottom and top
OPEN_TAB_R = 3.0                                 # where the fairing's tab meets the boss's circle
TOP_ELL = (-52.0, 33.55, 19.45)                  # the boss's footprint: centre x, half length, half width (fitted to the
                                                 # 3D clearance through the wall: the boss crosses it at 32 deg)
TOP_ELL_R = 8.0                                  # where it meets the straight sides
TOP_END_X, TOP_END_A = -3.15, 13.3              # the slot's square end; its corners' length along x
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

# ---------------------------------------------------------------- brake (all on y = 0 unless noted; angles in the XZ
# plane are from +x, behind the axis, up positive)
# A rigid printed strap, lined with felt, wraps the back of the hub between the up-stop lugs. Its bottom end is a
# knuckle hinged on an M4 pin through the up-stop pad, just behind the strut's clevis; its top end is a solid head with
# an M5 nut pressed into it. The knob sits in a seat sunk into the shell's top behind the hub, and its M5 bolt leans
# forward KNOB_TILT from vertical: turning the knob draws the head up and forward, so the strap swings about its hinge
# onto the hub. A vertical bolt there would pull nearly along the line from the hinge to the head (12 mm of leverage
# about the hinge), so it would mostly stretch and bend the strap; leaning it forward 30 deg gives 41 mm, so the same
# pull closes the strap 3.4 times as hard. 30 deg is as far as it can lean with the seat sunk into the shell's top (the
# shell prints top down, so nothing can stand proud of it) and 2 mm or more of shell between the seat and the hub.
FELT_T = 1.5
STRAP_HW = 9.0                                   # 18 wide: 2 mm clear of the up-stop lugs (|y| 11..21) either side
SLOT_HW = STRAP_HW + 0.5                         # the knuckle's slot through the up-stop pad: it guides the strap, so it
                                                 # can't shift more than 0.5 toward a lug
BAY_HW = USTOP_SLOT                              # 11: the strap's bay behind the pad, in the frame and the shell
STRAP_R0, STRAP_T = HUB_R + FELT_T, 8.0          # its face (31.5, on the felt) and the band's depth
STRAP_PHI = (-54.0, 42.0)                        # the band; the arm on its bottom end, the head on its top end. At the
                                                 # bottom it runs down into the up-stop pad's slot, into the knuckle; at
                                                 # the top, under the head, its end is cut off level with the head's face
FELT_PHI = (-52.0, 40.0)                         # the felt, 2 deg in from each end
HEAD_FROM = 12.0                                 # the head's gusset takes the band from here up
FELT_HW = STRAP_HW - 1.0                         # 16 wide, clear of the strap's chamfers
HINGE_X, HINGE_Z, KNUCKLE_R = 24.0, -38.0, 6.2   # the hinge: 4 mm of strap round its pin; the knuckle 2.8 mm behind
                                                 # the strut clevis's back walls
HINGE_HOLE_R = 2.1                               # the knuckle on the pin's 4 mm shank: a running fit
HINGE_HEAD_Y = 23.0                              # its pin, an M4 x 50 socket head: the head on the floor of a counterbore
                                                 # in the +y block's outer face, the nut in a hex pocket in the -y block's
KNOB_TILT = 30.0                                 # the bolt leans forward this far from vertical
KNOB_AT = (30.5, 33.0)                           # the centre of the knob's seat (x, z), on the bolt's axis
SEAT_R = 10.5                                    # the seat's recess round the knob (18 across)
SEAT_FLOOR = 4.0                                 # shell under the seat, along the bolt, down to the bay's ceiling
HEAD_GAP = 3.0                                   # the strap's head under that ceiling
HEAD_WALL = 4.0                                  # strap between the head's face and the nut
NUT_POCKET = 5.2                                 # the head below the nut's face: the nut's slot (4.2) and 1 mm under it
HEAD_HW = 6.5                                    # the head either side of the bolt
KNOB_FLOOR = 11.0                                # the knob's floor, under the bolt's head, above its underside
SPRING_POCKET = 7.0                              # the optional spring's pocket in the knob's underside, 10.6 across
BOLT_L = 35.0                                    # M5 x 35 hex bolt
# The strap's head and centre of mass are behind its hinge, so on its own it leans back. In the frame it leans back
# REST_DEG onto the back wall of its bay, which is far enough for the lever's hub to drop past it. In the shell the back
# of its bay is a ramp RAMP_CLR behind the head, parallel to the bolt: lowering the shell, the ramp meets the leaning
# head in the last few mm and swings it forward onto the hub, so the nut ends up on the bolt's axis for the knob.
REST_DEG = 8.0                                   # the dropping hub clears the felt's top end (40 deg up) by 1.0 mm
RAMP_CLR = 1.0
BACK_X, BACK_WALL = 56.5, 3.0                    # the frame's and shell's back face, and their wall behind the shell's
                                                 # bay: 1 mm behind the head leaning back REST_DEG, so the shell's ramp
                                                 # can catch it
BAY_Z0 = HINGE_Z - KNUCKLE_R - 1.5               # the floor of the slot and the frame's bay
T_CEIL = -SEAT_FLOOR                             # along the bolt from the seat (+ toward the knob): the bay's ceiling,
T_HEAD = T_CEIL - HEAD_GAP                       # the head's face,
T_NUT = T_HEAD - HEAD_WALL                       # the nut's face
T_FAR = T_NUT - NUT_POCKET                       # and the head's far face, where the pocket opens
# The back: one 45 deg chamfer plane each side, |y| + x = REAR_C, from the pillow blocks' outer back corners through the
# frame and the shell, so the two read as one block from behind.
REAR_C = BLOCK_HW + BLOCK_Y1                     # 69


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
                  box(PAD_X[0], -BLOCK_HW + 0.5, *sorted((s * PAD_DY[0], yi + s * 0.5)), Z_PLATE - 0.1, PAD_Z)]
    pad = box(*PED_X, -(BRG_Y0 + 0.5), BRG_Y0 + 0.5, Z_PLATE - 0.1, USTOP_Z)                            # up-stop pad
    parts += [pad, frame_back(), anchor_clevis(), *corner_gussets(), front_wall()]
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
    cuts += hinge_cuts()                                       # brake: the strap's slot, bay and hinge pin
    cuts.append(strut_body_sweep(1.5))                         # the strut's cylinder: through the front wall, over the
                                                               # clevis's front gussets
    for x, y in DESK:
        cuts.append(cyl(2.75, (x, y, -AXIS_H - 1), (x, y, 0)))                                         # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def front_wall():
    """the frame's front wall between the pillow blocks, SHELL_T thick like the shell's above it, from the plate up to
    the joint, with the same opening for the lever as the shell's front wall, so the two read as one; the strut's
    cylinder passes through it, in a slot cut from its sweep (frame())"""
    w = box(-BLOCK_HW, -BLOCK_HW + SHELL_T, -BRG_Y0 - 0.1, BRG_Y0 + 0.1, Z_PLATE - 0.1, 0.0)
    return w.cut(front_cut()).clean()


def _rounded(edges, corners):
    """a face from a closed loop of edges, its corners at the given points rounded: [(point, radius), ...]"""
    f = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))
    for p, rad in corners:
        f = f.fillet2D(rad, [v for v in f.Vertices() if (v.Center() - p).Length < 1e-4])
    return f


def _mirror_y(edges):
    return [e.mirror("XZ") for e in edges]


def _ell(c, a, b, t):
    """a point on the ellipse about c (semi-axes a, b along the plane's two axes) at parameter t, and its outward
    normal"""
    n = (b * math.cos(t), a * math.sin(t))
    k = math.hypot(*n)
    return (c[0] + a * math.cos(t), c[1] + b * math.sin(t)), (n[0] / k, n[1] / k)


def _root(f, lo, hi):
    """f's root between lo and hi (f(lo) < 0 < f(hi)), by bisection"""
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def _mid(c, rad, p, q):
    """the middle of the shorter arc of radius rad about c from p to q"""
    u = (p[0] + q[0] - 2 * c[0], p[1] + q[1] - 2 * c[1])
    k = math.hypot(*u)
    return c[0] + rad * u[0] / k, c[1] + rad * u[1] / k


def open_bottom():
    """the bottom of the fairing's tab in the front walls: the lower fairing's underside at 0 deg (it drops toward the
    hub, so it's lowest in the walls' back face), SWEEP_CLR under it, square to it"""
    px, pz = GROOVE_X, m.SOCK_BOSS_R
    a = math.atan2(pz, px) - math.acos(HUB_R / math.hypot(px, pz))
    k = (HUB_R * math.sin(a) - pz) / (HUB_R * math.cos(a) - px)               # the underside's slope
    return -(pz + k * (-BLOCK_HW + SHELL_T - px)) - SWEEP_CLR * math.sqrt(1 + k * k)


def front_profile(x0):
    """the front walls' opening (see OPEN_*), as a face in the plane x = x0, run on above the shell's top"""
    P = lambda y, z: V(x0, y, z)
    wb, wp, wf, zb = OPEN_BOSS, OPEN_PAD, OPEN_FAIR, open_bottom()
    za, zt, zu, r2, f1, f2 = OPEN_EAR
    a, b, ce, ztop = OPEN_BOSS, OPEN_ELL_B, (0.0, OPEN_ELL_Z), SHELL_TOP + 2.0
    zj = -math.sqrt(wb ** 2 - wf ** 2)                                     # the tab's side meets the boss's circle
    ra = ((wp - wb) ** 2 + (zt - za) ** 2) / (2 * (wp - wb))                # the relief's lower arc, tangent at (wp, zt)
    ca = (wp - ra, zt)
    c2 = (wp - r2, zu)                                                     # the relief's top corner, rounded f2 into the
    t = _root(lambda t: math.hypot(_ell(ce, a, b, t)[0][0] + f2 * _ell(ce, a, b, t)[1][0] - c2[0],   # ellipse
                                   _ell(ce, a, b, t)[0][1] + f2 * _ell(ce, a, b, t)[1][1] - c2[1]) - (r2 + f2), 0.0, 0.7)
    pe, n = _ell(ce, a, b, t)
    cf = (pe[0] + f2 * n[0], pe[1] + f2 * n[1])
    k = math.hypot(cf[0] - c2[0], cf[1] - c2[1])
    pc = (c2[0] + r2 * (cf[0] - c2[0]) / k, c2[1] + r2 * (cf[1] - c2[1]) / k)
    yt = a * math.sqrt(1 - ((ztop - ce[1]) / b) ** 2)
    t9 = math.atan2((ztop - ce[1]) / b, yt / a)
    side = [cq.Edge.makeLine(P(wf, zb), P(wf, zj)),
            cq.Edge.makeThreePointArc(P(wf, zj), P(*_mid((0, 0), wb, (wf, zj), (wb, 0))), P(wb, 0)),
            cq.Edge.makeLine(P(wb, 0), P(wb, za)),
            cq.Edge.makeThreePointArc(P(wb, za), P(*_mid(ca, ra, (wb, za), (wp, zt))), P(wp, zt)),
            cq.Edge.makeLine(P(wp, zt), P(wp, zu)),
            cq.Edge.makeThreePointArc(P(wp, zu), P(*_mid(c2, r2, (wp, zu), pc)), P(*pc)),
            cq.Edge.makeThreePointArc(P(*pc), P(*_mid(cf, f2, pc, pe)), P(*pe)),
            cq.Edge.makeEllipse(a, b, P(*ce), (1, 0, 0), (0, 1, 0), math.degrees(t), math.degrees(t9))]
    edges = [cq.Edge.makeLine(P(-wf, zb), P(wf, zb)), cq.Edge.makeLine(P(-yt, ztop), P(yt, ztop))] + side + _mirror_y(side)
    corners = [(P(s * wf, zb), FAIR_R + SWEEP_CLR) for s in (-1, 1)] + [(P(s * wf, zj), OPEN_TAB_R) for s in (-1, 1)] + \
              [(P(s * wb, za), f1) for s in (-1, 1)]
    return _rounded(edges, corners)


def front_cut():
    """the front walls' opening (frame and shell), straight through the 3 mm walls"""
    f = front_profile(-BLOCK_HW - 1.0)
    return cq.Solid.extrudeLinear(f.outerWire(), [], V(SHELL_T + 1.01, 0, 0))


def top_profile(z0):
    """the top wall's slot (see TOP_*), as a face in the plane z = z0, from in front of the shell"""
    P = lambda x, y: V(x, y, z0)
    xc, A, B = TOP_ELL
    R, ce = TOP_ELL_R, (TOP_ELL[0], 0.0)
    wf, yf, x0 = OPEN_FAIR, FAIR_HW - FAIR_R, -BLOCK_HW - 2.0
    ye = B * math.sqrt(1 - ((x0 - xc) / A) ** 2)
    tk = math.atan2(wf / B, math.sqrt(1 - (wf / B) ** 2))                  # the boss's footprint meets the sides here;
    t = _root(lambda t: _ell(ce, A, B, t)[0][1] + R * _ell(ce, A, B, t)[1][1] - (wf + R), tk, tk + 0.6)   # rounded R
    pe, n = _ell(ce, A, B, t)
    cf = (pe[0] + R * n[0], wf + R)
    xe0 = TOP_END_X - TOP_END_A
    t0 = math.atan2(ye / B, (x0 - xc) / A)
    side = [cq.Edge.makeEllipse(A, B, P(*ce), (0, 0, 1), (1, 0, 0), math.degrees(t), math.degrees(t0)),
            cq.Edge.makeThreePointArc(P(*pe), P(*_mid(cf, R, pe, (cf[0], wf))), P(cf[0], wf)),
            cq.Edge.makeLine(P(cf[0], wf), P(xe0, wf)),
            cq.Edge.makeEllipse(TOP_END_A, wf - yf, P(xe0, yf), (0, 0, 1), (1, 0, 0), 0, 90)]
    edges = [cq.Edge.makeLine(P(x0, -ye), P(x0, ye)), cq.Edge.makeLine(P(TOP_END_X, -yf), P(TOP_END_X, yf))] + side + \
        _mirror_y(side)
    return _rounded(edges, [])


def top_cut():
    """the top wall's slot, straight through it"""
    f = top_profile(SHELL_TOP - SHELL_T - 0.5)
    return cq.Solid.extrudeLinear(f.outerWire(), [], V(0, 0, SHELL_T + 1.0))


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


def lever_sweep(theta, extra=()):
    """what passes through the frame's and shell's openings, at angle theta: the lever's halves, the hose clamp and the
    tube, whole (trimming them with a boolean first isn't safe: OCC returns nothing for the chamfered lower half), and
    any extra solids on the lever (drawn at 0 deg)"""
    return [rot_y(s, theta) for p in (*lever_halves(0.0), moved(m.hose_clamp()), carbon_tube(), *extra)
            for s in p.Solids()]


def check_openings(step=0.25, fine=0.02, extra=()):
    """the openings' clearance, measured in 3D: the least distance from the frame's front wall and the shell's front and
    top walls (near the opening) to everything that passes through them, every step degrees from the down-stop to the
    up-stop, then every fine degrees round each wall's three closest passes. The walls are frame() and shell() before
    the frame's chamfers and the joint's knurl: chamfers and the shell's sockets only take material away, and the
    frame's pyramids stand inside the shell's own outline, so this is the closest the finished parts can be"""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    fr, sh = frame(), shell()
    front = box(-BLOCK_HW, -BLOCK_HW + SHELL_T + 0.01, -BRG_Y0, BRG_Y0, -30.0, SHELL_TOP + 1)   # not the pillars
    top = box(-BLOCK_HW - 1, 5.0, -BRG_Y0, BRG_Y0, SHELL_TOP - SHELL_T - 0.01, SHELL_TOP + 1)
    walls = {"frame front wall": fr.intersect(front), "shell front wall": sh.intersect(front),
             "shell top wall": sh.intersect(top)}
    walls = {k: [x for x in w.Solids() if x.Volume() > 1e-3] for k, w in walls.items()}
    for k, ws in walls.items():
        if not ws:
            raise RuntimeError(f"no {k} to measure (boolean failed)")

    def apart(a, b):
        p, q = a.BoundingBox(), b.BoundingBox()
        return max(p.xmin - q.xmax, q.xmin - p.xmax, p.ymin - q.ymax, q.ymin - p.ymax, p.zmin - q.zmax, q.zmin - p.zmax)

    def dist(k, th):
        best = (1e9, None)
        for part in lever_sweep(th, extra):
            for w in walls[k]:
                if apart(w, part) > 3.0:
                    continue
                d = BRepExtrema_DistShapeShape(w.wrapped, part.wrapped)
                if not d.IsDone() or d.NbSolution() == 0:
                    raise RuntimeError(f"no distance for {k} at {th} deg")
                if d.Value() < best[0]:
                    p = d.PointOnShape1(1)
                    best = (d.Value(), (p.X(), p.Y(), p.Z()))
        return best

    n = int(round(STOP_DEG / step))
    ths = [STOP_DEG * i / n for i in range(n + 1)]
    worst = {}
    for k in walls:
        ds = [dist(k, th)[0] for th in ths]
        picks = []
        for i in sorted(range(n + 1), key=lambda i: ds[i]):
            if len(picks) < 3 and all(abs(i - j) > 2 for j in picks):
                picks.append(i)
        res = min(dist(k, th) + (th,) for i in picks for j in range(int(round(2 * step / fine)) + 1)
                  for th in [min(max(ths[i] - step + j * fine, 0.0), STOP_DEG)])
        worst[k] = (res[0], res[2], res[1])
    for k, (dv, th, p) in worst.items():
        where = f", at ({p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f})" if p else ""
        print(f"{k:17s} {dv:6.3f} mm at {th:5.2f} deg{where}")
    return worst


def joint_edge(e):
    """edges in the face where the frame and the shell meet: no chamfer there, so no groove shows at the seam"""
    b = e.BoundingBox()
    return abs(b.zmin) < 1e-4 and abs(b.zmax) < 1e-4


def shell():
    """the box over the lever, in place of Rev 3's two caps: its side walls are the caps (the bearing's upper half-seat
    and lip, the cover screws' upper threads, the cap screws counterbored from the top), joined by 3 mm front, back and
    top walls. The front and top are slotted for the lever's sweep. Behind the hub it's solid out to the walls and the
    back face, the knob's seat sunk into it and the strap's bay under that. Prints top down"""
    h = BLOCK_HW
    s = box(-h, h, -BLOCK_Y1, BLOCK_Y1, 0, SHELL_TOP).cut(
        box(-h + SHELL_T, h - SHELL_T, -BRG_Y0, BRG_Y0, -1, SHELL_TOP - SHELL_T))
    s = s.fuse(shell_back())
    for side in (-1, 1):
        for k in block_cuts(side):
            s = s.cut(k)
        yb = side * CAP_BOLT_Y
        for x in (-CAP_BOLT_X, CAP_BOLT_X):                                     # the M4 x 50s: clearance, counterbore
            s = s.cut(cyl(m.LS_CLR_R, (x, yb, -1), (x, yb, CAP_HEAD_Z + 0.01)))
            s = s.cut(cyl(SHELL_CB_R, (x, yb, CAP_HEAD_Z), (x, yb, SHELL_TOP + 1)))
    for c in knob_seat_cuts():                                          # brake: the knob's seat, the strap's bay
        s = s.cut(c)
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
def bolt_axis():
    """the knob's bolt: (u, w), u along it toward the knob, w across it, up and back"""
    a = math.radians(KNOB_TILT)
    return V(-math.sin(a), 0, math.cos(a)), V(math.cos(a), 0, math.sin(a))


def on_bolt(t, s=0.0):
    """t along the bolt from the centre of the knob's seat (+ toward the knob), s across it (+ up and back)"""
    u, w = bolt_axis()
    return V(KNOB_AT[0], 0, KNOB_AT[1]) + u * t + w * s


def _pt(rr, a):
    return (rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a)))


def _arc(rr, a0, a1, n=24):
    return [_pt(rr, a0 + (a1 - a0) * i / n) for i in range(n + 1)]


def hex_on(af, p0, p1, corner):
    """a hexagonal prism af across its flats from p0 to p1, a corner toward `corner` (square to its axis)"""
    p0, p1 = V(*p0), V(*p1)
    pl = cq.Plane(origin=p0, xDir=V(*corner), normal=(p1 - p0).normalized())
    return cq.Workplane(pl).polygon(6, af / math.cos(math.radians(30))).extrude((p1 - p0).Length).val()


def strap_outline():
    """the strap in the XZ plane, as three outlines that overlap: the band on the hub; the head, the hull of the nut's
    block and the band from HEAD_FROM up, one solid gusset from the band's front and back out to where the bolt pulls; and
    the arm, the hull of the knuckle and the band's bottom 12 deg, a gusset from the band down to the hinge. The chords
    inside the band's face come off with the face's cylinder (strap())"""
    r0, r1 = STRAP_R0, STRAP_R0 + STRAP_T
    p0, p1 = STRAP_PHI
    band = _arc(r0, p0, p1, 60) + _arc(r1, p1, p0, 60)
    blk = [(q.x, q.z) for q in (on_bolt(t, s) for t in (T_HEAD, T_FAR) for s in (-HEAD_HW, HEAD_HW))]
    head = r._hull(blk + _arc(r0, HEAD_FROM, p1) + _arc(r1, HEAD_FROM, p1))
    knuckle = [(HINGE_X + KNUCKLE_R * math.cos(math.radians(a)), HINGE_Z + KNUCKLE_R * math.sin(math.radians(a)))
               for a in range(0, 360, 3)]
    arm = r._hull(knuckle + _arc(r0, p0, p0 + 12.0) + _arc(r1, p0, p0 + 12.0))
    return band, head, arm


def swing_2d(pts, deg):
    """XZ points swung deg about the hinge (+ = back, off the hub), as strap_at() swings a part"""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(HINGE_X + (x - HINGE_X) * c + (z - HINGE_Z) * s, HINGE_Z - (x - HINGE_X) * s + (z - HINGE_Z) * c)
            for x, z in pts]


def frame_bay_back():
    """the frame's bay ends where the strap, leaning back REST_DEG, rests on its top back edge: the furthest back the
    strap's outline reaches below the joint at that angle"""
    best = 0.0
    for poly in strap_outline():
        q = swing_2d(poly, REST_DEG)
        for (x0, z0), (x1, z1) in zip(q, q[1:] + q[:1]):
            for i in range(41):
                x, z = x0 + (x1 - x0) * i / 40, z0 + (z1 - z0) * i / 40
                if z <= 0.0 and math.hypot(x, z) >= STRAP_R0 - 0.01:
                    best = max(best, x)
    return round(best, 2)


def nut_slot():
    """the M5 nut's slot in the strap's head: a hex pocket on the bolt's axis, its corners along y, and a slot the
    nut's width from it out through the strap's +y face (its top as it prints), so the nut drops in sideways and the
    bolt holds it. The bolt's pull bears it on the slot's face toward the knob"""
    t0, t1, a = T_NUT - m.NUT_T[5] - 0.2, T_NUT, m.NUT_AF[5] / 2
    pts = [(q.x, q.z) for q in (on_bolt(t0, -a), on_bolt(t1, -a), on_bolt(t1, a), on_bolt(t0, a))]
    return fuse(hex_on(m.NUT_AF[5], on_bolt(t0).toTuple(), on_bolt(t1).toTuple(), (0, 1, 0)),
                gusset_xz(pts, 0.0, STRAP_HW + 1.0))


def strap():
    """felt-lined, hinged at its bottom, pulled at its head. Prints on its side, +y up, so the bending all runs along
    its layers and the nut's slot opens upward"""
    r0, (p0, p1), hw = STRAP_R0, STRAP_PHI, STRAP_HW
    band, head, arm = strap_outline()
    u, _ = bolt_axis()
    s = fuse(m.sector(r0, r0 + STRAP_T, p0, p1, -hw, hw), gusset_xz(head, -hw, hw), gusset_xz(arm, -hw, hw),
             cyl(KNUCKLE_R, (HINGE_X, -hw, HINGE_Z), (HINGE_X, hw, HINGE_Z)))
    s = s.cut(cyl(r0, (0, -20, 0), (0, 20, 0)))                                              # its face, on the felt
    s = s.cut(cyl(HINGE_HOLE_R, (HINGE_X, -20, HINGE_Z), (HINGE_X, 20, HINGE_Z)))             # the hinge pin
    s = s.cut(nut_slot())                                                                    # the M5 nut
    s = s.cut(cyl(2.8, on_bolt(-40.0).toTuple(), on_bolt(T_HEAD + 1.0).toTuple()))          # the bolt, right through
    top = [(q.x, q.z) for q in (on_bolt(T_HEAD, -80), on_bolt(T_HEAD + 80, -80), on_bolt(T_HEAD + 80, 80),
                                on_bolt(T_HEAD, 80))]
    s = s.cut(gusset_xz(top, -20, 20))                         # the band's top end, level with the head's face
    s = chamfer_edges(s.clean())
    return s.cut(cq.Solid.makeCone(4.5, 2.8, 1.7, on_bolt(T_HEAD + 0.01), -u)).clean()   # lead-in for the bolt's tip


def felt():
    """self-adhesive felt, FELT_T thick, on the strap's face (drawn 0.02 off the hub)"""
    return m.sector(HUB_R + 0.02, STRAP_R0, *FELT_PHI, -FELT_HW, FELT_HW)


def strap_at(shape, deg):
    """a part of the strap swung deg about its hinge (+ = back, off the hub)"""
    return shape.rotate((HINGE_X, 0, HINGE_Z), (HINGE_X, 1, HINGE_Z), deg)


def hinge_cuts():
    """the knuckle's slot through the up-stop pad, the bay behind it, the pin's hole through the pad and both pillow
    blocks, the pin's head's counterbore (+y) and its nut's pocket (-y)"""
    return [box(HINGE_X - KNUCKLE_R - 1.5, PED_X[1] + 0.5, -SLOT_HW, SLOT_HW, BAY_Z0, USTOP_Z + 1),
            box(PED_X[1], frame_bay_back(), -BAY_HW, BAY_HW, BAY_Z0, 1.0),
            cyl(m.LS_CLR_R, (HINGE_X, -BLOCK_Y1 - 1, HINGE_Z), (HINGE_X, BLOCK_Y1 + 1, HINGE_Z)),
            cyl(SHELL_CB_R, (HINGE_X, HINGE_HEAD_Y, HINGE_Z), (HINGE_X, BLOCK_Y1 + 1, HINGE_Z)),
            hexprism(m.NUT_AF[4], (HINGE_X, -HINGE_HEAD_Y, HINGE_Z), (HINGE_X, -BLOCK_Y1 - 1, HINGE_Z))]


def back_outline(x0, yi):
    """the back in plan: from x0 back, |y| <= yi in front of the pillow blocks' back ends, then their full width, then
    in along the 45 deg chamfers to the back face"""
    yo, bx, c = BLOCK_Y1, BLOCK_HW, REAR_C
    return [(x0, -yi), (bx, -yi), (bx, -yo), (BACK_X, -(c - BACK_X)), (BACK_X, c - BACK_X), (bx, yo), (bx, yi), (x0, yi)]


def frame_back():
    """behind the up-stop pad, between the pillow blocks and on behind them to the back face: solid from the base plate
    to the joint, except round the axis, 39 mm out between the blocks (1.5 mm clear of the up-stop lugs' swing)"""
    z0 = Z_PLATE - 0.1
    b = cq.Workplane("XY").workplane(offset=z0).polyline(back_outline(PED_X[1], BRG_Y0 + 0.5)).close() \
        .extrude(-z0).val()
    return b.cut(cyl(LUG_R + 1.5, (0, -BRG_Y0 - 0.5, 0), (0, BRG_Y0 + 0.5, 0)))


def shell_back():
    """the shell behind the hub: solid from 2 mm off the hub out to the side walls, the top and the back face, behind a
    plane at 75 deg over the hub's top (the upper fairing sweeps the hub down to 71 deg at the stop)"""
    b = cq.Workplane("XY").polyline(back_outline(0.0, BRG_Y0 + 0.5)).close().extrude(SHELL_TOP).val()
    b = b.cut(cyl(HUB_R + 2.0, (0, -BLOCK_Y1 - 1, 0), (0, BLOCK_Y1 + 1, 0)))
    a = math.radians(75.0)
    return b.cut(gusset_xz([(-1.0, -1.0), (60 * math.cos(a), 60 * math.sin(a)), (-1.0, 60.0)], -40, 40))


def knob_seat_cuts():
    """the knob's seat, sunk square to the bolt into the shell's top; the bolt's hole under it; and the strap's bay
    under that: SEAT_FLOOR below the seat, and behind the head a ramp RAMP_CLR off it, parallel to the bolt"""
    lo, hi = -80.0, 80.0
    pts = [(q.x, q.z) for q in (on_bolt(lo, lo), on_bolt(T_CEIL, lo), on_bolt(T_CEIL, HEAD_HW + RAMP_CLR),
                                on_bolt(lo, HEAD_HW + RAMP_CLR))]
    bay = gusset_xz(pts, -BAY_HW, BAY_HW).intersect(box(0.0, BACK_X - BACK_WALL, -BAY_HW, BAY_HW, -1.0, SHELL_TOP))
    return [cyl(SEAT_R, on_bolt(0.0).toTuple(), on_bolt(hi).toTuple()),
            cyl(m.M5_CLR_R, on_bolt(T_CEIL - 1.0).toTuple(), on_bolt(1.0).toTuple()), bay]


def friction_knob(s=0.0):
    """Rev 3's knob (the MkII knob with an M5 hex pocket) with its floor at KNOB_FLOOR and a pocket in its underside for
    an optional spring; in its seat, s along the bolt off it (0: no spring, the knob on the seat)"""
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
    k = k.cut(cyl(5.3, (0, 0, -1), (0, 0, SPRING_POCKET)))                  # the spring's pocket
    k = k.cut(cq.Solid.makeCone(hr + 0.8, hr - 0.2, 1.0, V(0, 0, zt - 1.0), V(0, 0, 1)))   # lead-in at the mouth
    return rot_y(k.clean(), -KNOB_TILT).translate(on_bolt(s))


def knob_spring(fit=10.0):
    """the optional spring (reference): fitted `fit` long between the seat and the floor of the knob's pocket, so the
    knob stands fit - SPRING_POCKET off the seat"""
    u, _ = bolt_axis()
    p0 = on_bolt(0.55)
    helix = cq.Wire.makeHelix(1.6, fit - 1.1, 4.45, p0, u)
    pl = cq.Plane(origin=helix.startPoint(), xDir=m._perp(helix.tangentAt(0)), normal=helix.tangentAt(0))
    return cq.Workplane(pl).circle(0.5).sweep(cq.Workplane().add(helix), isFrenet=True).val()


def brake_screws(s=0.0):
    """the brake's bought parts (reference), each with the way it comes out: the knob's M5 x 35 hex bolt (its head on
    the knob's floor, the knob s off its seat), its M5 nut in the strap's slot, and the hinge's M4 x 50 socket head pin
    (head on +y) and its M4 nut (-y). [(name, shape, out)]"""
    u, w = bolt_axis()
    hb = on_bolt(s + KNOB_FLOOR)                                           # the bolt head's underside
    bolt = fuse(hex_on(m.M5_HEAD_AF - 0.1, hb.toTuple(), (hb + u * m.KNOB_BOLT[1]).toTuple(), w.toTuple()),
                cyl(2.4, (hb - u * BOLT_L).toTuple(), (hb + u * 0.1).toTuple()))
    nut = hex_on(m.NUT_AF[5] - 0.2, on_bolt(T_NUT - m.NUT_T[5]).toTuple(), on_bolt(T_NUT).toTuple(), (0, 1, 0)).cut(
        cyl(2.0, on_bolt(T_NUT - 6).toTuple(), on_bolt(T_NUT + 1).toTuple()))
    y = HINGE_HEAD_Y
    pin = fuse(cyl(r.CAP_D / 2, (HINGE_X, y, HINGE_Z), (HINGE_X, y + r.CAP_K, HINGE_Z)),
               cyl(2.0, (HINGE_X, y - 50, HINGE_Z), (HINGE_X, y, HINGE_Z)))
    pnut = hexprism(7.0, (HINGE_X, -y, HINGE_Z), (HINGE_X, -y - m.NUT_T[4], HINGE_Z)).cut(
        cyl(2.0, (HINGE_X, -y + 1, HINGE_Z), (HINGE_X, -y - 5, HINGE_Z)))
    return [("brake bolt", bolt, u.toTuple()), ("brake nut", nut, (0, 1, 0)), ("hinge screw", pin, (0, 1, 0)),
            ("hinge nut", pnut, (0, -1, 0))]


def brake_hardware(s=0.0):
    """the brake's bolt and nut and its hinge pin and nut, as one shape"""
    return fuse(*[shp for _, shp, _ in brake_screws(s)])


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
    """the fixed base's screws and nuts (reference): the shell's, the covers', the brake's bolt and nut and its hinge
    pin and nut"""
    parts = [brake_hardware()]
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
PRINTED = ["frame", "shell", "lever_sensor", "lever_cable", "lever_dowel", "strap", "cover_sensor", "cover_cable",
           "strut_collar", "friction_knob"]


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
        _STATIC.update({"frame": fr, "shell": sh, "strap": strap(), "felt": felt(),
                        "cover_sensor": cover_sensor(), "cover_cable": cover_cable(), "friction_knob": friction_knob(),
                        "hardware": hardware(), "magnet": magnet(),
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
ALLOWED = {("bearing_inner", "lever_cable"), ("bearing_inner", "lever_sensor"), ("felt", "strap"),
           ("frame", "hardware"), ("hardware", "shell"), ("cover_sensor", "hardware"),
           ("cover_cable", "hardware"), ("friction_knob", "hardware"),
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
    """the order it goes together in: the strap (felt on) set down into the bare frame from 60 mm up, leaning back
    REST_DEG as it rests on its own, and its pin fitted; the lever (halves screwed up on their dowels, bearings on)
    lowered straight down past it from 80 mm up; the strap swung forward onto the hub; then the shell lowered straight
    down from 80 mm up, the strap leaning back again until the shell's ramp meets it and swings it forward. Last, how
    far off the bolt's axis that leaves the strap's nut for the knob. Part by part, so a race landing in its seat is
    held to SHARED's sliver like check()"""
    S = static_parts()
    ls, lc = lever_halves(0.0)
    lever_b = {"lever_sensor": ls, "lever_cable": lc, "lever_screws": lever_screws(0.0), "lever_dowel": lever_dowels(0.0),
               "bearing_outer": S["bearing_outer"], "bearing_seal": S["bearing_seal"],
               "bearing_inner": fuse(*[bearing(s)[1] for s in (-1, 1)])}
    strap_b = {"strap": S["strap"], "felt": S["felt"]}
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

    def gap(group, fixed):
        return min((sa.distance(sb) for pa in group.values() for pb in fixed.values() for sa in pa.Solids()
                    for sb in pb.Solids()), default=99.0)

    def lean_(group, a):
        return {k: strap_at(x, a) for k, x in group.items()}

    o, frame_ = V(0, 0, 0), {"frame": S["frame"]}
    rest = lean_(strap_b, REST_DEG)
    for i in range(int(60 / step) + 1):
        z = 60.0 - i * step
        hit(rest, V(0, 0, z), frame_, z)
    near, halves = 99.0, {k: lever_b[k] for k in ("lever_sensor", "lever_cable")}
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        hit(lever_b, V(0, 0, z), {**frame_, **rest}, z)
        near = min(near, gap({k: x.translate(V(0, 0, z)) for k, x in halves.items()}, rest))
    print(f"  the lever goes in past the strap leaning back {REST_DEG:.0f} deg: {near:.2f} mm at the closest")
    for i in range(int(REST_DEG / 0.5) + 1):
        a = REST_DEG - i * 0.5
        hit(lean_(strap_b, a), o, {**frame_, **lever_b}, a)
    lean, met = REST_DEG, None
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        sh = {"shell": S["shell"].translate(V(0, 0, z))}
        hit(sh, o, {**frame_, **lever_b}, z)
        while lean > 0.0 and gap(sh, lean_({"strap": S["strap"]}, lean)) < 0.05:     # the ramp swings the strap forward
            lean = max(0.0, lean - 0.1)
            met = met if met is not None else z
        if gap(sh, lean_({"strap": S["strap"]}, lean)) < 0.05:
            worst["shell / strap"] = (0.0, z)
    u, w = bolt_axis()
    c = V(HINGE_X, 0, HINGE_Z)
    n0 = on_bolt(T_NUT - m.NUT_T[5] / 2)
    a = math.radians(lean)
    dx, dz = n0.x - c.x, n0.z - c.z
    n1 = V(c.x + dx * math.cos(a) + dz * math.sin(a), 0, c.z - dx * math.sin(a) + dz * math.cos(a))
    off = (n1 - n0) - u * (n1 - n0).dot(u)
    print(f"  the shell's ramp meets the leaning strap {met if met is not None else 0:.0f} mm up and swings it forward; "
          f"on, the strap can lean back {lean:.1f} deg, the nut {off.Length:.2f} mm off the bolt's axis "
          f"(the lead-in takes up to {4.5 - 2.5:.1f})")
    print("strap in, lever in, shell on: " + ("clear" if not worst else
          "; ".join(f"{k} {v:.2f} mm3 at {zz:.1f}" for k, (v, zz) in worst.items())))


def check_brake(angles=None):
    """the brake's clearances as distances (OCC's boolean can miss a clash with a chamfered part): the strap, felt and
    knob against the lever through its travel, and the strap against the frame, the shell and the hardware"""
    S = static_parts()
    angles = angles or [float(a) for a in range(0, int(STOP_DEG) + 1, 2)] + [STOP_DEG]

    def gap(a_, b_):
        return min(sa.distance(sb) for sa in a_.Solids() for sb in b_.Solids())

    lo = {}
    for th in angles:
        lev = cq.Compound.makeCompound([*lever_halves(th), lever_screws(th)])
        for k in ("strap", "felt", "friction_knob"):
            d = gap(S[k], lev)
            if k not in lo or d < lo[k][0]:
                lo[k] = (d, th)
    for k, (d, th) in lo.items():
        print(f"  {k:14s} to the lever: {d:.2f} mm at the closest ({th:.0f} deg)")
    for k in ("frame", "shell", "hardware", "friction_knob"):
        print(f"  strap to the {k}: {gap(S['strap'], S[k]):.2f} mm, overlap {overlap(S['strap'], S[k]):.2f} mm3")
    print("  (the strap touches the hardware where the nut bears on its slot's face)")


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
                    ("coupon_dowel_hole", coupon_dowel_hole)):
        shp = m.coupon_plate(f)
        bb = shp.BoundingBox()
        print(f"{name:26s} valid={shp.isValid()} size={bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}")
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(out, f"{name}.stl"), tolerance=0.04, angularTolerance=0.12)


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        check()
        check_brake()
        check_assembly()
        check_openings()
    elif "--openings" in sys.argv[1:]:
        check_openings()
    elif "--balance" in sys.argv[1:]:
        balance(plot=os.path.join(HERE, "renders", "strut_balance_r4.png"))
    elif "--coupons" in sys.argv[1:]:
        export_coupons()
    else:
        export()
