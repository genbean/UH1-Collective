"""
MkIII collective base - Rev 4: narrow, 82 mm (3.25 in) wide (CONCEPT, not print-tested)

Rev 3 (../mk3_rev3.py) with the base cut down from 130 mm to 82 mm along the pivot axis, and the lever symmetrical about
the tube. Everything Rev 4 doesn't change comes from Rev 3: the gas strut, its collar and anchor, the socket for the
uncut 500 mm carbon tube, the down-stop pads and pillars, the lever's cap-screw joint, the MkII friction knob, the
chamfers and the fits.

Same frame as Rev 3, except that the tube's plane is now the middle: origin = pivot centre, Y = pivot axis, Z = up,
tube along -X at 0 deg, +Y = USB side, -Y = sensor side. (Rev 3's tube is at y = -9, so Rev 3's collar, strut, pins
and hose clamp are moved +9 in y.)

Across the pivot axis, from the middle out (each side):
    hub                 |y| 0-21.5     60 mm across (Rev 3: 64 mm long, now 43), 3.5 mm past the socket boss
    bearing             |y| 22.5-29.5  6808-2RS thin-section, 40 x 52 x 7 (Rev 3: 6006-2RS, 30 x 55 x 13)
    retaining lip       |y| 29.5-31.5  the pillow blocks are 9 mm wide (Rev 3: 17); the base plate stops at their
                                       outer faces, 63 mm across
    trunnion end        |y| 32.0       40.1 mm across: the 6808's bore + 0.1
    side covers         |y| 31.5-41.0  9.5 mm deep (Rev 3: 15)
One shell over the top takes the place of Rev 3's two bearing caps: a box over the lever whose side walls are the caps,
with a slot in its front and top for the socket boss, tube and top gusset to swing through, solid behind the hub
round the brake's bay and the knob's seat. It drops straight down over the lever and bolts on with four M4 x 50 socket head screws
into nuts slid into the pillow blocks' outer faces, under the side covers; a diamond grid of pyramids in the joint
locates it. The frame's front wall, under the shell's, carries the shell's cut for the lever on down, so they read as one.
The AS5600 board sits INSIDE the sensor trunnion, in a square pocket in its end, chip facing out and level with the
trunnion's end; the magnet is on a post from the sensor cover, 1 mm off the chip. The USB cable turns out of the
axis inside the cable cover and leaves through a notch in its rim, toward the back; the notch lets the cover go on
over a cable that's already fitted, like Rev 3's.

Brake: a strap behind the hub. A rigid printed strap, 18 mm wide and 8 mm deep, lined with 1.5 mm felt, wraps the
hub's back between the up-stop lugs, from 40 deg below the axis to 24 above. Its bottom end is a knuckle on an M4 x 50
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
    python mk3_rev4.py --check    -> interference check through the travel, the brake's clearances, the assembly order
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
gusset_xz, hex_y = r.gusset_xz, r.hex_y


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
W_HALF = 41.0                                    # overall 82 mm
HUB_R, HUB_HW = 30.0, 21.5
BRG_d, BRG_D, BRG_B = 40.0, 52.0, 7.0            # 6808-2RS
BRG_IR_SH, BRG_OR_SH = 44.0, 48.3                # inner race's outside, outer race's inside (approx.)
BRG_Y0 = HUB_HW + 1.0                            # bearing inner face (22.5)
BRG_Y1 = BRG_Y0 + BRG_B                          # (29.5)
BLOCK_Y1 = BRG_Y1 + 2.0                          # pillow block's outer face (31.5): a 2 mm lip holds the outer race
TRUN_OD = BRG_d + 0.1                            # Rev 3's +0.2 on the race's bore pressed on a hair too tight (as
                                                 # built, 2026-11-08), so +0.1
TRUN_OUT = BLOCK_Y1 + 0.5                        # (32)
BRG_SEAT_D = BRG_D + 0.0                         # +0.1 (perfect on Rev 3's one-piece blocks) left the 6808 a little
                                                 # play in Rev 4's seat, split between the frame and the shell (as
                                                 # built, 2026-11-08), so 0.1 less
LIP_R = 23.0                                     # clears the inner race (22.0), holds the outer (24.15)
BLOCK_HW = m.BLOCK_HW                            # 37.5, as Rev 3
# side covers: four M3 x 16 countersunk each, into M3 threads tapped in the block and shell; the pilot holes go right
# through their 9 mm walls (COVER_TAP is the back plate's screws' tapped depth)
COVER_HOLE_R, COVER_R, COVER_IN_R = 30.5, 35.5, 25.0
COVER_FLOOR, COVER_TAP, COVER_SCREW_L = 2.5, 7.5, 16
COVER_D = W_HALF - BLOCK_Y1                      # 9.5
# AS5600 in the sensor trunnion's end: the board (0.915 in = 23.24 mm square, measured; 1.6 thick) in a square pocket 0.15 mm
# clear each side, front face level
# with the trunnion's end, on two ledges along its top and bottom edges (clear of both pad columns), with 3.5 mm behind it
# for the wires soldered in from the back and the DIR jumper
BOARD = 23.24
BOARD_CLR, BOARD_T, LEDGE, BEHIND = 0.15, 1.6, 1.6, 3.5
BOARD_Y = (TRUN_OUT - BOARD_T, TRUN_OUT)         # |y| of the board's back and front
CHIP_Y1 = TRUN_OUT + 1.5                         # SOIC-8 top
MAGNET_Y = CHIP_Y1 + m.MAGNET_GAP                # magnet face (34.5)
POCKET_FLOOR = BOARD_Y[0] - BEHIND               # (26.9)
MAG_POST_R = 4.5
# USB cable: out of the axis at the trunnion's end, a 4 mm bend, then out through the cable cover's rim toward the back
USB_BEND_R, USB_Y = 4.0, BLOCK_Y1 + 4.0
USB_R = 2.3

# ---------------------------------------------------------------- lever
# four M4 x 40 socket head cap screws, where Rev 3 has them: x = +-17, symmetrical fore and aft, 16.25 mm either side of
# the tube: 1.25 mm from the counterbore to the hub's end and 1.35 mm from the clearance hole to the socket at the front
# pair.
LEVER_SCREWS = [(x, y) for x in (-17.0, 17.0) for y in (-16.25, 16.25)]
# The fairing over the socket boss, on the upper half and mirrored underneath on the lower (in place of Rev 3's 8 mm top
# gusset): FAIR_HW either side of the tube, from the hose-clamp groove's back edge back to the hub. Its top is one
# straight line from the boss's top at the groove to the hub's circle and tangent to it, so it runs into the hub without
# a corner; its long top edges are rounded FAIR_R. 10.5 keeps it 1.75 mm clear of the front lever screws' counterbores
# on top and 1.6 mm of their nut pockets underneath.
GROOVE_X = -54.0                                 # the hose-clamp groove's back edge
FAIR_HW, FAIR_R = 10.5, 3.0
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
                                                 # 37.7 mm from the pivot, so it clears the side cover's rim by 0.45 mm
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
STRAP_PHI = (-40.0, 24.0)                        # the band; the arm on its bottom end, the head on its top end
FELT_PHI = (-38.0, 22.0)                         # the felt, 2 deg in from each end
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
REST_DEG = 4.0
RAMP_CLR = 1.0
BACK_X, BACK_WALL = 52.5, 3.0                    # the frame's and shell's back face, and their wall behind the shell's bay
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


def lever():
    core = rot_y(cyl(HUB_R, (0, -HUB_HW, 0), (0, HUB_HW, 0)), 135)      # seam away from the split, the stop and the track
    boss = cyl(m.SOCK_BOSS_R, (-10, 0, 0), (-m.SOCK_MOUTH, 0, 0))
    shoulders = [cyl(BRG_IR_SH / 2 - 1.1, (0, s * HUB_HW, 0), (0, s * BRG_Y0, 0)) for s in (-1, 1)]
    trunnions = [cyl(TRUN_OD / 2, (0, s * BRG_Y0, 0), (0, s * TRUN_OUT, 0)) for s in (-1, 1)]
    gusset = fuse(fairing(1), fairing(-1))
    pads = [box(*PAD_X, *sorted((s * PAD_DY[0], s * PAD_DY[1])), PAD_Z, 0) for s in (-1, 1)]
    h = fuse(core, boss, gusset, *shoulders, *trunnions, *pads, *up_stop_lugs())
    cuts = [cyl(m.SOCK_BORE_R, (-m.SOCK_BOTTOM, 0, 0), (-m.SOCK_MOUTH - 1, 0, 0)),               # tube socket
            tube(m.SOCK_BOSS_R + 1, m.SOCK_BOSS_R - 1.2, (-54, 0, 0), (-63, 0, 0)),               # hose-clamp groove
            cyl(m.CABLE_R, (0, -POCKET_FLOOR - 0.5, 0), (0, TRUN_OUT + 1, 0)),                   # axial 1/2" bore
            cyl(m.CABLE_R, (-m.SOCK_BOTTOM - 1, 0, 0), (3, 0, 0)),                               # radial 1/2" bore
            sensor_pocket()]
    for c in cuts:
        h = h.cut(c)
    return h.clean()


def lever_screw_seats():
    """Rev 3's rule: per screw (x, y, head seat z, kit length, tip z, nut pocket ceiling z)"""
    out = []
    for x, y in LEVER_SCREWS:
        z_head = math.sqrt(HUB_R ** 2 - (abs(x) + r.CAP_CB_R) ** 2) - r.CAP_K
        z_nut_open = -math.sqrt(HUB_R ** 2 - (abs(x) + m.LS_NUT_AF / 2) ** 2) + r.NUT_WALL
        length = max(k for k in r.KIT_LENGTHS if k <= z_head - (z_nut_open - r.LS_TIP_PAST_NUT))
        z_tip = z_head - length
        out.append((x, y, z_head, length, z_tip, z_tip + r.LS_TIP_PAST_NUT + r.LS_NUT_T))
    return out


def lever_screw_cuts():
    cuts = []
    for x, y, zh, _, _, zn in lever_screw_seats():
        cuts += [cyl(r.CAP_CB_R, (x, y, zh), (x, y, 60)),
                 cyl(m.LS_CLR_R, (x, y, zn - 0.5), (x, y, zh + 0.01)),
                 hex_y(m.LS_NUT_AF, (x, y, -60), (x, y, zn))]
    return cuts


def lever_screws(theta=0.0):
    parts = []
    for x, y, zh, length, zt, zn in lever_screw_seats():
        parts += [cyl(r.CAP_D / 2, (x, y, zh), (x, y, zh + r.CAP_K)), cyl(2.0, (x, y, zt), (x, y, zh)),
                  hex_y(7.0, (x, y, zn - r.LS_NUT_T), (x, y, zn))]
    return rot_y(fuse(*parts), theta)


_HALVES = []


def lever_halves(theta=0.0):
    """split at z = 0, chamfered everywhere but the joint plane (Rev 3)"""
    if not _HALVES:
        h = lever()
        for c in lever_screw_cuts():
            h = h.cut(c)
        h = h.clean()
        on_joint = lambda e: abs(e.BoundingBox().zmin) < 1e-4 and abs(e.BoundingBox().zmax) < 1e-4
        _HALVES.append(chamfer_edges(h.intersect(box(-200, 200, -100, 100, 0, 200)).clean(), exclude=on_joint))
        _HALVES.append(chamfer_edges(h.intersect(box(-200, 200, -100, 100, -200, 0)).clean(), exclude=on_joint))
    return [rot_y(s, theta) for s in _HALVES]


# ================================================================ frame
def block_cuts(s):
    cuts = [cyl(BRG_SEAT_D / 2, (0, s * (BRG_Y0 - 0.5), 0), (0, s * BRG_Y1, 0)),         # bearing seat
            cyl(LIP_R, (0, s * (BRG_Y1 - 1), 0), (0, s * (BLOCK_Y1 + 1), 0))]           # retaining lip's bore
    for a in (45, 135, 225, 315):
        px, pz = m.on_circle(COVER_HOLE_R, a)
        cuts.append(cyl(m.TAP[3] / 2, (px, s * (BRG_Y0 - 1), pz), (px, s * (BLOCK_Y1 + 1), pz)))   # covers' M3: tap drill, right through the wall
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
def _cover(s):
    y0, y1 = s * BLOCK_Y1, s * W_HALF
    c = cyl(COVER_R, (0, y0, 0), (0, y1, 0))
    c = c.cut(cyl(COVER_IN_R, (0, y0 - s, 0), (0, s * (W_HALF - COVER_FLOOR), 0)))
    for a in (45, 135, 225, 315):
        px, pz = m.on_circle(COVER_HOLE_R, a)
        c = c.cut(m.csk_hole(3, (px, y1, pz), (0, -s, 0), COVER_D + 1))
    return c


def cover_sensor():
    """the magnet on a post from the floor, 1 mm off the chip"""
    c = _cover(-1).fuse(cyl(MAG_POST_R, (0, -(W_HALF - COVER_FLOOR) - 0.5, 0), (0, -MAGNET_Y, 0)))
    c = c.cut(cyl(m.MAGNET_POCKET / 2, (0, -MAGNET_Y + 0.1, 0), (0, -(MAGNET_Y + m.MAGNET_H + 0.1), 0)))
    return chamfer_edges(c.clean())


def cover_cable():
    """the cable leaves through a hole in the rim toward the back, with a notch from the face that seats on the block,
    so the cover goes on over the cable"""
    c = chamfer_edges(_cover(1).clean())
    w = r.NOTCH_W
    c = c.cut(cyl(w / 2 + 0.05, (0, USB_Y, 0), (COVER_R + 2, USB_Y, 0)))
    c = c.cut(box(COVER_IN_R - 1, COVER_R + 2, BLOCK_Y1 - 1, USB_Y, -w / 2, w / 2))
    return c.clean()


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
    block and the band's top 12 deg, one solid gusset from the band's front and back out to where the bolt pulls; and
    the arm, the hull of the knuckle and the band's bottom 12 deg, a gusset from the band down to the hinge. The chords
    inside the band's face come off with the face's cylinder (strap())"""
    r0, r1 = STRAP_R0, STRAP_R0 + STRAP_T
    p0, p1 = STRAP_PHI
    band = _arc(r0, p0, p1, 60) + _arc(r1, p1, p0, 60)
    blk = [(q.x, q.z) for q in (on_bolt(t, s) for t in (T_HEAD, T_FAR) for s in (-HEAD_HW, HEAD_HW))]
    head = r._hull(blk + _arc(r0, p1 - 12.0, p1) + _arc(r1, p1 - 12.0, p1))
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


def usb_cable(theta=0.0, x0=-190.0):
    """down the tube and along the axis, turning with the lever; then the bend and the run out through the cover, fixed"""
    s45 = math.sin(math.radians(45))
    rr, rb = 5.0, USB_BEND_R
    yk = USB_Y - rb
    inside = (cq.Workplane("XY").moveTo(x0, 0).lineTo(-rr, 0).threePointArc((-rr + rr * s45, rr - rr * s45), (0, rr))
              .lineTo(0, yk).wire().val())
    out = (cq.Workplane("XY").moveTo(0, yk).threePointArc((rb - rb * s45, yk + rb * s45), (rb, USB_Y))
           .lineTo(90, USB_Y).wire().val())
    return fuse(rot_y(m.sweep_circle(USB_R, inside, (x0, 0, 0), (1, 0, 0)), theta),
                m.sweep_circle(USB_R, out, (0, yk, 0), (0, 1, 0)))


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
TURNS = ("lever_upper", "lever_lower", "lever_screws", "carbon_tube", "hose_clamp", "sensor_pcb", "sensor_chip",
         "bearing_inner", "sensor_wires")
PRINTED = ["frame", "shell", "lever_upper", "lever_lower", "strap", "cover_sensor", "cover_cable", "strut_collar",
           "friction_knob"]


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
    lu, ll = lever_halves(theta)
    pcb, chip = sensor_board()
    P = static_parts()
    P.update({"lever_upper": lu, "lever_lower": ll, "strut_collar": strut_collar(theta),
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
ALLOWED = {("bearing_inner", "lever_upper"), ("bearing_inner", "lever_lower"), ("felt", "strap"),
           ("frame", "hardware"), ("hardware", "shell"), ("cover_sensor", "hardware"),
           ("cover_cable", "hardware"), ("friction_knob", "hardware"),
           ("frame", "strut_pins"), ("gas_strut", "strut_pins"), ("strut_collar", "strut_pins"),
           ("lever_lower", "lever_screws"), ("lever_screws", "lever_upper"), ("carbon_tube", "hose_clamp"),
           ("hose_clamp", "lever_lower"), ("hose_clamp", "lever_upper"), ("carbon_tube", "strut_collar"),
           ("cover_sensor", "magnet"), ("sensor_pcb", "sensor_wires"), ("frame", "gas_strut")}


def overlap(a, b):
    """the volume two solids share: OCC's boolean, or a mesh boolean (manifold) where OCC fails on the pair"""
    try:
        return a.intersect(b).Volume()
    except Exception:
        import numpy as np
        import trimesh

        def tm(s):
            vs, fs = s.tessellate(0.05, 0.2)
            return trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs))
        try:
            return trimesh.boolean.intersection([tm(a), tm(b)], engine="manifold").volume
        except Exception:
            return float("nan")


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
                elif v > 0.01:
                    hits.append(f"{a} / {b} {v:.2f}")
        print(f"{th:5.1f} deg: " + ("clear" if not hits else "; ".join(hits)))


def check_assembly(step=2.0):
    """the order it goes together in: the strap (felt on) set down into the bare frame from 60 mm up, leaning back
    REST_DEG as it rests on its own, and its pin fitted; the lever (bearings on) lowered straight down past it from
    80 mm up; the strap swung forward onto the hub; then the shell lowered straight down from 80 mm up, the strap
    leaning back again until the shell's ramp meets it and swings it forward. Last, how far off the bolt's axis that
    leaves the strap's nut for the knob"""
    S = static_parts()
    lever_b = cq.Compound.makeCompound([*lever_halves(0.0), *[bearing(s)[k] for s in (-1, 1) for k in range(3)]])
    strap_b = cq.Compound.makeCompound([S["strap"], S["felt"]])
    worst = {}

    def meet(p, q):
        a, b = p.BoundingBox(), q.BoundingBox()
        return (a.xmax >= b.xmin and b.xmax >= a.xmin and a.ymax >= b.ymin and b.ymax >= a.ymin and
                a.zmax >= b.zmin and b.zmax >= a.zmin)

    def hit(key, a_, b_, at):
        vol = sum(overlap(sa, sb) for sa in a_.Solids() for sb in b_.Solids() if meet(sa, sb))
        if vol != vol:
            worst[key + " NOT CHECKED"] = (0.0, at)
        elif vol > 0.01:
            worst[key] = max(worst.get(key, (0, 0)), (vol, at))

    def gap(a_, b_):
        return min((sa.distance(sb) for sa in a_.Solids() for sb in b_.Solids()), default=99.0)

    rest = strap_at(strap_b, REST_DEG)
    for i in range(int(60 / step) + 1):
        z = 60.0 - i * step
        hit("strap down / frame", rest.translate(V(0, 0, z)), S["frame"], z)
    near = 99.0
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        lv = lever_b.translate(V(0, 0, z))
        hit("lever / frame", lv, S["frame"], z)
        hit("lever / strap", lv, rest, z)
        near = min(near, gap(lv, rest))
    print(f"  the lever goes in past the strap leaning back {REST_DEG:.0f} deg: {near:.2f} mm at the closest")
    for i in range(int(REST_DEG / 0.5) + 1):
        a = REST_DEG - i * 0.5
        hit("strap forward / lever", strap_at(S["strap"], a), lever_b, a)
        hit("strap forward / frame", strap_at(strap_b, a), S["frame"], a)
    lean, met = REST_DEG, None
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        sh = S["shell"].translate(V(0, 0, z))
        hit("shell / lever", sh, lever_b, z)
        hit("shell / frame", sh, S["frame"], z)
        while lean > 0.0 and gap(sh, strap_at(strap_b, lean)) < 0.05:     # the ramp swings the strap forward
            lean = max(0.0, lean - 0.1)
            met = met if met is not None else z
        if gap(sh, strap_at(strap_b, lean)) < 0.05:
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
    for name in PRINTED:
        print(f"{name:16s} valid={P[name].isValid()} vol={P[name].Volume():9.1f}")
    for name, shp in P.items():
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
    lu, ll = lever_halves(0.0)
    items = r.rear_items({"lever_upper": lu, "lever_lower": ll, "strut_collar": strut_collar(0.0)})
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
# The tube socket is Rev 3's, so its coupon (and TRUN/seat steps found on the 6006) carry over only as a starting point.
def coupon_trunnion(d, h=8.0, sh=2.0):
    """the trunnion's stub on its inner-race shoulder, with the 1/2" bore, standing on the shoulder"""
    c = fuse(cyl(BRG_IR_SH / 2 - 1.1, (0, 0, 0), (0, 0, sh)), cyl((TRUN_OD + d) / 2, (0, 0, sh), (0, 0, sh + h)))
    return c.cut(cyl(m.CABLE_R, (0, 0, -1), (0, 0, sh + h + 1)))


def coupon_seat(d, depth=BRG_B, lip=BLOCK_Y1 - BRG_Y1, wall=4.0):
    """the pillow block's seat and lip as a ring, lip down; the 6808 presses in from the top"""
    c = cyl(BRG_SEAT_D / 2 + wall, (0, 0, 0), (0, 0, lip + depth))
    c = c.cut(cyl((BRG_SEAT_D + d) / 2, (0, 0, lip), (0, 0, lip + depth + 1)))
    return c.cut(cyl(LIP_R, (0, 0, -1), (0, 0, lip + 1)))


def export_coupons():
    out = os.path.join(HERE, "stl", "coupons")
    os.makedirs(out, exist_ok=True)
    for name, f in (("coupon_trunnion_6808", coupon_trunnion), ("coupon_bearing_seat_6808", coupon_seat)):
        shp = m.coupon_plate(f)
        bb = shp.BoundingBox()
        print(f"{name:26s} valid={shp.isValid()} size={bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}")
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(out, f"{name}.stl"), tolerance=0.04, angularTolerance=0.12)


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        check()
        check_brake()
        check_assembly()
    elif "--balance" in sys.argv[1:]:
        balance(plot=os.path.join(HERE, "renders", "strut_balance_r4.png"))
    elif "--coupons" in sys.argv[1:]:
        export_coupons()
    else:
        export()
