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
with a slot in its front and top for the socket boss, tube and top gusset to swing through, and a notch in its back
wall round the brake tower. It drops straight down over the lever and bolts on with the four cap screws.
The AS5600 board sits INSIDE the sensor trunnion, in a square pocket in its end, chip facing out and level with the
trunnion's end; the magnet is on a post from the sensor cover, 1 mm off the chip. The USB cable turns out of the
axis inside the cable cover and leaves through a notch in its rim, toward the back; the notch lets the cover go on
over a cable that's already fitted, like Rev 3's.

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
gusset_xz, hex_y = r.gusset_xz, r.hex_y


def chamfer_edges(shape, sizes=r.CHAMFERS, chunk=8, exclude=None):
    """Rev 3's chamfer_edges(), with a guard: OCC can hand back a valid solid with a whole feature missing (on the
    first try it dropped the frame's down-stop pillars), so a set of chamfers is only kept if the volume it takes off
    is about what chamfers that long and that size could take"""
    for c in sizes:
        es = r.sharp_edges(shape, exclude=exclude)
        v0 = shape.Volume()

        def ok(edges):
            res = r._chamfer(shape, edges, c)
            if res is None:
                return False
            dv = v0 - res.Volume()
            return -0.5 <= dv <= sum(e.Length() for e in edges) * c * c * 1.2 + 0.5

        keep = []
        for i in range(0, len(es), chunk):
            part = es[i:i + chunk]
            if ok(keep + part):
                keep += part
                continue
            for e in part:
                if ok(keep + [e]):
                    keep.append(e)
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
# The trunnion. The first Rev 4 lever, drawn round at 40.1 and printed lying on its joint face, measured (both halves
# held together, by calliper, 2026-11-08) 1.575 in across the axes (along the joint and square to it) but 1.585 in
# across the 45 deg diagonals: the layers' stair-steps on the arch's sloped flanks. The bearing's bore measured 1.578 in
# by the same calliper. So the profile is drawn out of round, by that printer's error, to print TRUN_FIT over the bore
# every way: r = R - TRUN_DIAG / 2 * sin^2(2 th)
TRUN_PRINTED = {"drawn": 40.1, "axes": 1.575 * 25.4, "diagonals": 1.585 * 25.4}
BORE_MEASURED = 1.578 * 25.4                     # 40.08
TRUN_FIT = 0.0                                   # printed size over the measured bore: line to line
TRUN_OD = TRUN_PRINTED["drawn"] + (BORE_MEASURED - TRUN_PRINTED["axes"]) + TRUN_FIT       # across the axes: 40.18
TRUN_DIAG = TRUN_PRINTED["diagonals"] - TRUN_PRINTED["axes"]                             # 0.25 less across the diagonals
TRUN_OUT = BLOCK_Y1 + 0.5                        # (32)
BRG_SEAT_D = BRG_D + 0.1                         # +0.1 on the race's outside: a perfect fit on Rev 3, as built
LIP_R = 23.0                                     # clears the inner race (22.0), holds the outer (24.15)
BLOCK_HW = m.BLOCK_HW                            # 37.5, as Rev 3
# pillow-block caps: two M3 x 20 countersunk each, from the top, into an M3 nut slid in fore and aft (the 9 mm blocks are
# too narrow for Rev 3's M4 heads)
CAP_BOLT_X, CAP_HEAD_Z, CAP_SCREW_L = 30.5, 8.0, 20
CAP_NUT_Z = -8.3                                 # the nut's top face, as Rev 3
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
# four M4 socket head cap screws (Rev 3's), 16.25 mm either side of the tube: 1.25 mm from the counterbore to the hub's end
# and 1.35 mm from the clearance hole to the socket at the front pair. The back pair are at x = 10 (Rev 3: 17), clear of
# the up-stop lugs, with 1.3 mm to the axial cable bore.
LEVER_SCREWS = [(x, y) for x in (-17.0, 10.0) for y in (-16.25, 16.25)]
GUSSET_T = 8.0
GUSSET_TOP = [(-48, 16.5), (-4, 33.0), (2, 30.5), (2, 16.5)]  # Rev 1's, its back end cut to x = 2: clear of the shoe at 32 deg
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


def trunnion(y0, y1, d=0.0, n=96):
    """a trunnion from y0 to y1: TRUN_OD + d across the axes (along the joint, x, and square to it, z), TRUN_DIAG less
    across the 45 deg diagonals, so that it prints round lying on the joint face"""
    R, k = (TRUN_OD + d) / 2, TRUN_DIAG / 2
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = R - k * math.sin(2 * t) ** 2
        pts.append(V(rr * math.cos(t), y0, rr * math.sin(t)))
    w = cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])
    return cq.Solid.extrudeLinear(w, [], V(0, y1 - y0, 0))


def lever():
    core = rot_y(cyl(HUB_R, (0, -HUB_HW, 0), (0, HUB_HW, 0)), 135)      # seam away from the split, the stop and the track
    boss = cyl(m.SOCK_BOSS_R, (-10, 0, 0), (-m.SOCK_MOUTH, 0, 0))
    shoulders = [cyl(BRG_IR_SH / 2 - 1.1, (0, s * HUB_HW, 0), (0, s * BRG_Y0, 0)) for s in (-1, 1)]
    trunnions = [trunnion(s * BRG_Y0, s * TRUN_OUT) for s in (-1, 1)]
    gusset = gusset_xz(GUSSET_TOP, -GUSSET_T / 2, GUSSET_T / 2)
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
                  box(PAD_X[0], -BLOCK_HW + 0.5, *sorted((s * PAD_DY[0], yi + s * 0.5)), Z_PLATE - 0.1, PAD_Z),
                  # behind the pillow block: the web to the brake housing and the corner, out to the back chamfer
                  rear_fill(s, Z_PLATE - 0.1, 0.0)]
    pad = box(*PED_X, -(BRG_Y0 + 0.5), BRG_Y0 + 0.5, Z_PLATE - 0.1, USTOP_Z)                            # up-stop pad
    parts += [pad, brake_housing(Z_PLATE - 0.1, 0.0), anchor_clevis(), *corner_gussets()]
    f = fuse(*parts)

    a3, t3, a4, t4 = m.NUT_AF[3], m.NUT_T[3], m.NUT_AF[4], m.NUT_T[4]
    cuts = []
    for s in (-1, 1):
        cuts += block_cuts(s)
        yb = s * (BRG_Y0 + BLOCK_Y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            zn = CAP_NUT_Z - t3 - 0.2
            cuts += [cyl(m.CSK[3][1] / 2, (x, yb, CAP_HEAD_Z - CAP_SCREW_L - 1), (x, yb, 1)),
                     hexprism(a3, (x, yb, zn), (x, yb, CAP_NUT_Z)),
                     box(*sorted((x, math.copysign(70.0, x))), yb - a3 / 2, yb + a3 / 2, zn, CAP_NUT_Z)]
    aw = (r.ROD_TAB_T + 0.6) / 2 + r.CLEVIS_T
    cuts += [cyl(r.PIN_R, (r.ANCH_X, -12, r.ANCH_Z), (r.ANCH_X, 12, r.ANCH_Z)),                      # anchor: M4 x 16,
             m.csk_hole(4, (r.ANCH_X, aw, r.ANCH_Z), (0, -1, 0), 1),                                   # head on +y,
             hexprism(a4, (r.ANCH_X, -aw + t4 + 0.2, r.ANCH_Z), (r.ANCH_X, -aw - 1, r.ANCH_Z))]         # nut on -y
    # brake: the shoe's pocket (lower half), and the back plate's lower screws
    cuts.append(shoe_tunnel())
    for y, z in BACK_SCREWS:
        cuts.append(cyl(m.TAP[3] / 2, (TOWER_X1 - COVER_TAP, y, z), (TOWER_X1 + 1, y, z)))
    for x, y in DESK:
        cuts.append(cyl(2.75, (x, y, -AXIS_H - 1), (x, y, 0)))                                         # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def lever_sweep():
    """what the shell has to let through: the socket boss and the top gusset, SWEEP_CLR bigger all round, at every
    angle from 1 deg below the down-stop to 1 deg past the up-stop (2 deg apart: 0.02 mm between them at the shell)"""
    c = SWEEP_CLR
    boss = cyl(m.SOCK_BOSS_R + c, (-8.0, 0, 0), (-90.0, 0, 0))
    g = [(-48 - c, 16.5), (-4, 33.0 + c * 1.2), (2 + c, 30.5 + c * 0.7), (2 + c, 16.5)]
    pads = [box(PAD_X[0] - c, PAD_X[1] + c, *sorted((s * (PAD_DY[0] - c), s * (PAD_DY[1] + c))), PAD_Z - c, 0)
            for s in (-1, 1)]                                                  # the down-stop pads, 20 out from the tube
    env = fuse(boss, gusset_xz(g, -GUSSET_T / 2 - c, GUSSET_T / 2 + c), *pads)
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
        yb = side * (BRG_Y0 + BLOCK_Y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            s = s.cut(m.csk_hole(3, (x, yb, CAP_HEAD_Z), (0, 0, -1), 10, out=SHELL_TOP))
    s = s.fuse(brake_housing(0.0, SHELL_TOP), *[rear_fill(side, 0.0, SHELL_TOP) for side in (-1, 1)])   # brake housing
    s = s.cut(shoe_tunnel())
    for y, z in BACK_SCREWS:
        s = s.cut(cyl(m.TAP[3] / 2, (TOWER_X1 - COVER_TAP, y, z), (TOWER_X1 + 1, y, z)))
    s = s.cut(lever_sweep())
    return chamfer_edges(s.clean(), exclude=joint_edge)


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


def hardware():
    """the fixed base's screws and nuts (reference): the shell's, the covers', the back plate's, the brake bolt and nut"""
    parts = [brake_hardware()]
    for y, z in BACK_SCREWS:
        parts.append(m.csk_screw(3, (TOWER_X1 + BACK_T, y, z), (-1, 0, 0), 16))
    for s in (-1, 1):
        yb = s * (BRG_Y0 + BLOCK_Y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            parts += [m.csk_screw(3, (x, yb, CAP_HEAD_Z), (0, 0, -1), CAP_SCREW_L),
                      m.nut(3, (x, yb, CAP_NUT_Z), (0, 0, -1))]
        for a in (45, 135, 225, 315):
            px, pz = m.on_circle(COVER_HOLE_R, a)
            parts.append(m.csk_screw(3, (px, s * W_HALF, pz), (0, -s, 0), COVER_SCREW_L))
    return fuse(*parts)


# ================================================================ build + export
TURNS = ("lever_upper", "lever_lower", "lever_screws", "carbon_tube", "hose_clamp", "sensor_pcb", "sensor_chip",
         "bearing_inner", "sensor_wires")
PRINTED = ["frame", "shell", "lever_upper", "lever_lower", "shoe", "spring_cap", "back_plate", "cover_sensor",
           "cover_cable", "strut_collar", "friction_knob"]


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
        _STATIC.update({"frame": chamfer_edges(frame(), exclude=joint_edge), "shell": shell(), "shoe": shoe(), "spring_cap": spring_cap(),
                        "back_plate": back_plate(),
                        "cover_sensor": cover_sensor(), "cover_cable": cover_cable(), "friction_knob": friction_knob(),
                        "felt": felt(), "knob_spring": knob_spring(), "hardware": hardware(), "magnet": magnet(),
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
ALLOWED = {("bearing_inner", "lever_upper"), ("bearing_inner", "lever_lower"), ("felt", "shoe"),
           ("frame", "hardware"), ("hardware", "shell"), ("back_plate", "hardware"), ("cover_sensor", "hardware"),
           ("cover_cable", "hardware"), ("friction_knob", "hardware"), ("hardware", "knob_spring"),
           ("hardware", "spring_cap"), ("knob_spring", "shoe"), ("knob_spring", "spring_cap"),
           ("frame", "strut_pins"), ("gas_strut", "strut_pins"), ("strut_collar", "strut_pins"),
           ("lever_lower", "lever_screws"), ("lever_screws", "lever_upper"), ("carbon_tube", "hose_clamp"),
           ("hose_clamp", "lever_lower"), ("hose_clamp", "lever_upper"), ("carbon_tube", "strut_collar"),
           ("cover_sensor", "magnet"), ("sensor_pcb", "sensor_wires"), ("frame", "gas_strut")}


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
                v = P[a].intersect(P[b]).Volume()
                if v > 0.01:
                    hits.append(f"{a} / {b} {v:.2f}")
        print(f"{th:5.1f} deg: " + ("clear" if not hits else "; ".join(hits)))


def check_assembly(step=2.0):
    """the order it goes together in: the lever (bearings on) lowered straight down into the bare frame from 80 mm up;
    the shoe (felt, spring and cap in it) set down into the frame's half of its pocket standing SHOE_IN back, from
    60 mm up, then slid forward onto the hub; then the shell lowered straight down over both from 80 mm up"""
    S = static_parts()
    lever_b = fuse(*lever_halves(0.0), *[bearing(s)[k] for s in (-1, 1) for k in range(3)])
    shoe_b = fuse(S["shoe"], S["felt"], S["spring_cap"])
    worst = {}

    def hit(key, a_, b_, at):
        vol = a_.intersect(b_).Volume()
        if vol > 0.01:
            worst[key] = max(worst.get(key, (0, 0)), (vol, at))

    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        hit("lever / frame", lever_b.translate(V(0, 0, z)), S["frame"], z)
    for i in range(int(60 / step) + 1):
        z = 60.0 - i * step
        for k, f in (("frame", S["frame"]), ("lever", lever_b)):
            hit(f"shoe down / {k}", shoe_b.translate(V(SHOE_IN, 0, z)), f, z)
    for i in range(int(SHOE_IN / 0.5) + 1):
        d = SHOE_IN - i * 0.5
        for k, f in (("frame", S["frame"]), ("lever", lever_b)):
            hit(f"shoe forward / {k}", shoe_b.translate(V(d, 0, 0)), f, d)
    for i in range(int(80 / step) + 1):
        z = 80.0 - i * step
        sh = S["shell"].translate(V(0, 0, z))
        for k, f in (("lever", lever_b), ("frame", S["frame"]), ("shoe", shoe_b)):
            hit(f"shell / {k}", sh, f, z)
    print("lever in, shoe in, shell on: " + ("clear" if not worst else
          "; ".join(f"{k} {v:.2f} mm3 at {zz:.1f}" for k, (v, zz) in worst.items())))


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


# ================================================================ the trunnion's profile (TRUN_PRINTED, at the top)
def trunnion_drawing(path, k=40.0):
    """the trunnion's section with its departures from round blown up k times, and its diameter all the way round:
    the first print as measured, the profile drawn now, and what that should print as (the same printer error)"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    ink, ink2, grid, surf = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    c_bore, c_old, c_new, c_exp = "#8b8a86", "#eb6834", "#2a78d6", "#1baf7a"
    th = np.linspace(0, 2 * np.pi, 721)
    s2 = np.sin(2 * th) ** 2
    ax_m, dg_m, d0 = TRUN_PRINTED["axes"], TRUN_PRINTED["diagonals"], TRUN_PRINTED["drawn"]
    old = ax_m + (dg_m - ax_m) * s2                                   # diameters, as printed (fitted to the 2 readings)
    new = TRUN_OD - TRUN_DIAG * s2                                    # as drawn now
    exp = new + (old - d0)                                            # drawn now, plus the first print's error
    ref = 40.0

    fig = plt.figure(figsize=(14.5, 7.4))
    fig.patch.set_facecolor(surf)
    fig.suptitle("MkIII base Rev 4: the trunnion, drawn out of round so it prints round", x=0.03, y=0.985,
                 ha="left", color=ink, fontsize=15, fontweight="bold")
    fig.text(0.03, 0.895, f"The first lever, drawn round at {d0:.1f} mm, printed {ax_m / 25.4:.3f} in across the axes but "
             f"{dg_m / 25.4:.3f} in across the diagonals; the bearing's bore is {BORE_MEASURED / 25.4:.3f} in.\n"
             f"So it's now drawn {TRUN_OD:.2f} mm across the axes and {TRUN_OD - TRUN_DIAG:.2f} across the diagonals, to print "
             f"{(BORE_MEASURED + TRUN_FIT) / 25.4:.3f} in every way.",
             color=ink2, fontsize=10.5, linespacing=1.5)

    # ---- left: the section, departures from 40.0 mm blown up k times
    a = fig.add_axes([0.02, 0.20, 0.44, 0.69])
    a.set_aspect("equal")
    a.axis("off")
    big = lambda d: (ref + (d - ref) * k) / 2                         # diameter -> exaggerated radius
    for d, col, ls, lw, lab in ((np.full_like(th, BORE_MEASURED), c_bore, (0, (5, 3)), 1.4,
                                 f"bearing's bore, {BORE_MEASURED / 25.4:.3f} in by the same calliper"),
                                (old, c_old, "-", 2.0, "first print, as measured (drawn round, 40.1)"),
                                (new, c_new, "-", 2.6, "drawn now (the STL)"),
                                (exp, c_exp, (0, (2, 2)), 2.0, "drawn now, plus the first print's error: round, on the bore")):
        a.plot(big(d) * np.cos(th), big(d) * np.sin(th), color=col, ls=ls, lw=lw, label=lab)
    R = big(dg_m) + 3
    a.plot([-R - 2, R + 2], [0, 0], color=ink, lw=1.2)                # the joint
    a.text(-R - 2, 0.6, "joint", color=ink, fontsize=9, va="bottom")
    a.text(0, 3.0, "upper half\nprinted on the joint face", color=ink2, fontsize=8.5, ha="center", va="bottom")
    a.text(0, -3.0, "lower half\nprinted on the joint face", color=ink2, fontsize=8.5, ha="center", va="top")
    for ang, col in ((90, "#3b4bd1"), (45, "#e0302a"), (135, "#e0302a")):
        u = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        a.plot([-R * u[0], R * u[0]], [-R * u[1], R * u[1]], color=col, lw=0.9, alpha=0.55)
    a.plot([-R, R], [0, 0], color="#3b4bd1", lw=0.9, alpha=0.55)

    def note(ang, lines, off=(0, 0), ha="left"):
        u = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        p = u * (R + 1.0) + np.array(off)
        a.text(*p, "\n".join(lines), fontsize=8.6, color=ink, ha=ha, va="center", linespacing=1.35)

    note(45, [f"diagonal: printed {dg_m / 25.4:.3f} in ({dg_m:.2f} mm)",
              f"drawn now {TRUN_OD - TRUN_DIAG:.2f} mm ({(TRUN_OD - TRUN_DIAG) / 25.4:.4f} in)"])
    note(90, [f"square to the joint: printed {ax_m / 25.4:.3f} in",
              f"drawn now {TRUN_OD:.2f} mm ({TRUN_OD / 25.4:.4f} in)"], off=(0, 1.2), ha="center")
    note(0, [f"along the joint: printed {ax_m / 25.4:.3f} in",
             f"drawn now {TRUN_OD:.2f} mm ({TRUN_OD / 25.4:.4f} in)"], off=(0.5, -3.2))
    a.text(0, -R - 3.5, f"Departures from 40.0 mm drawn {k:.0f} times bigger, so 0.1 mm shows as 4 mm.",
           color=ink2, fontsize=9, ha="center", va="top")
    a.legend(loc="upper left", bbox_to_anchor=(0.04, -0.02), frameon=False, fontsize=9)
    a.set_xlim(-R - 6, R + 22)
    a.set_ylim(-R - 6, R + 6)

    # ---- right: the diameter all the way round
    b = fig.add_axes([0.565, 0.24, 0.36, 0.60])
    b.set_facecolor(surf)
    b.grid(True, color=grid, lw=0.8)
    for sd in ("top", "right"):
        b.spines[sd].set_visible(False)
    deg = np.degrees(th)
    m = deg <= 180
    b.axhline(BORE_MEASURED, color=c_bore, ls=(0, (5, 3)), lw=1.4, label="bearing's bore (measured)")
    b.plot(deg[m], old[m], color=c_old, lw=2.0, label="first print, as measured")
    b.plot([0, 45, 90, 135, 180], [ax_m, dg_m, ax_m, dg_m, ax_m], "o", color=c_old, ms=6, label="your readings")
    b.plot(deg[m], new[m], color=c_new, lw=2.6, label="drawn now")
    b.plot(deg[m], exp[m], color=c_exp, ls=(0, (2, 2)), lw=2.0, label="what it should print: on the bore")
    b.set_xlim(0, 180)
    b.set_xticks([0, 45, 90, 135, 180])
    b.set_xticklabels(["0\nalong\nthe joint", "45\ndiagonal", "90\nsquare to it", "135\ndiagonal", "180\nalong\nthe joint"])
    b.set_ylabel("diameter across the trunnion, mm", color=ink2)
    b.set_ylim(39.85, 40.32)
    b.tick_params(colors=ink2)
    sec = b.secondary_yaxis("right", functions=(lambda x: x / 25.4, lambda x: x * 25.4))
    sec.set_ylabel("inches", color=ink2)
    sec.tick_params(colors=ink2)
    b.set_title("The diameter at each angle (one half-turn: the other half is the same)", loc="left", color=ink,
                fontsize=10.5)
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=3, frameon=False, fontsize=8.6)
    fig.savefig(path, dpi=150, facecolor=surf)
    plt.close(fig)
    print("wrote", path)


# ================================================================ fit-test coupons for the 6808
# Rev 3's coupon plates (Rev 1's coupon_plate: steps -0.2, 0, +0.2 on the diameter, engraved), sized for the 6808-2RS.
# The tube socket is Rev 3's, so its coupon (and TRUN/seat steps found on the 6006) carry over only as a starting point.
def coupon_trunnion(d, h=8.0, sh=2.0, gap=4.0):
    """the trunnion's stub (its profile, diagonals and all) on its inner-race shoulder, with the 1/2" bore, split at the
    joint like the lever: two halves lying on their joint faces, one behind the other, so they print as the lever's
    halves do. Glue them face to face, then press a 6808 on. The step changes the size across the axes"""
    full = fuse(cyl(BRG_IR_SH / 2 - 1.1, (0, 0, 0), (0, sh, 0)), trunnion(sh, sh + h, d))
    full = full.cut(cyl(m.CABLE_R, (0, -1, 0), (0, sh + h + 1, 0)))
    half = full.intersect(box(-50, 50, -1, sh + h + 1, 0, 50)).clean()
    return fuse(half, half.translate(V(0, sh + h + gap, 0)))


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


def export_coupons():
    out = os.path.join(HERE, "stl", "coupons")
    os.makedirs(out, exist_ok=True)
    for name, f in (("coupon_trunnion_6808", coupon_trunnion), ("coupon_bearing_seat_6808", coupon_seat),
                    ("coupon_shoe_pocket", coupon_shoe_pocket)):
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
    elif "--trunnion" in sys.argv[1:]:
        trunnion_drawing(os.path.join(HERE, "renders", "rev4_trunnion_profile.png"))
    else:
        export()
