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
    retaining lip       |y| 29.5-31.5  the pillow blocks and caps are 9 mm wide (Rev 3: 17)
    trunnion end        |y| 32.0       40.2 mm across: the 6808's bore, +0.2 as Rev 3's coupon fit
    side covers         |y| 31.5-41.0  9.5 mm deep (Rev 3: 15)
The AS5600 board sits INSIDE the sensor trunnion, in a square pocket in its end, chip facing out and level with the
trunnion's end; the magnet is on a post from the sensor cover, 1 mm off the chip. The USB cable turns out of the
axis inside the cable cover and leaves through a notch in its rim, toward the back; the notch lets the cover go on
over a cable that's already fitted, like Rev 3's.

Brake: Rev 3's drum, shoe and knob tower sat beside the hub, and there's no room for them now. The brake is behind
the hub instead. A narrow, tall shoe (12 mm wide, 44 mm tall, felt on its face) rides in a pocket in a tower on the
frame's back edge and presses on the hub's own cylinder over +-44 deg either side of the axis. The MkII knob, on the
back of the tower, turns Rev 3's M5 x 30 hex bolt through a captive nut; the bolt's tip pushes a printed spring cap,
and the spring (Rev 3's, 10 mm OD, still 6.5 mm long when fitted) pushes the shoe. The shoe wraps the hub above its
widest point, so it has to stand back while the lever goes in: the pocket leaves it 10.5 mm to slide back.
Up-stop: a boss under the back of the hub lands on a pedestal at 32 deg, as in Rev 3. At 0 deg it sits where the
shoe's lower end is, so it has a slot down the middle: two lugs, one each side of the shoe and the brake tower, both
landing on the pedestal. Inside the slot the hub is a plain cylinder, so the felt runs on it.

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
TRUN_OD = BRG_d + 0.1                            # Rev 3's +0.2 on the race's bore pressed on a hair too tight (as
                                                 # built, 2026-11-08), so +0.1
TRUN_OUT = BLOCK_Y1 + 0.5                        # (32)
BRG_SEAT_D = BRG_D + 0.1                         # +0.1 on the race's outside: a perfect fit on Rev 3, as built
LIP_R = 23.0                                     # clears the inner race (22.0), holds the outer (24.15)
BLOCK_HW = m.BLOCK_HW                            # 37.5, as Rev 3
# pillow-block caps: two M3 x 20 countersunk each, from the top, into an M3 nut slid in fore and aft (the 9 mm blocks are
# too narrow for Rev 3's M4 heads)
CAP_BOLT_X, CAP_HEAD_Z, CAP_SCREW_L = 30.5, 8.0, 20
CAP_NUT_Z = -8.3                                 # the nut's top face, as Rev 3
# side covers: four M3 x 16 countersunk each, into M3 threads tapped 7.5 mm deep in the block and cap
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
# up-stop: two lugs under the back of the hub land on a pad behind the axis at STOP_DEG. The further back they land,
# the further back they swing at 0 deg, toward the webs behind the pillow blocks (x = 37): with the pad at z = -28.5 and
# the contact face ending at x = 24.4, their back corners come to x = 35.8 at 0 deg, 1.2 mm off the webs. The pad's top
# is 2 mm under the hub at its front edge.
USTOP_X, USTOP_Z = (15.0, 24.4), -28.5           # contact face at the stop, world x; the pad's top
USTOP_HW, USTOP_SLOT = 21.0, 11.0                # lugs from |y| 11 to 21: either side of the shoe and the brake tower (+-10)
LUG_R = math.hypot(USTOP_X[1], USTOP_Z)          # the lugs' furthest point from the axis (37.5)
PAD_X, PAD_DY, PAD_Z = r.PAD_X, r.PAD_DY, r.PAD_Z

# ---------------------------------------------------------------- frame
PLATE_X = (-62.0, 74.0)
Z_PLATE, AXIS_H = r.Z_PLATE, r.AXIS_H
PED_X = (14.0, 29.5)                             # the up-stop pad, full width between the pillow blocks
PED_NOTCH = (24.0, USTOP_SLOT)                   # ... with its back middle cut away (x > 24, |y| < 11), clear of the shoe
CG_LEG = 8.0                                     # corner gussets at each end of each pillow block, 45 deg in plan
DESK = [(x, y) for x in (PLATE_X[0] + 8, PLATE_X[1] - 8) for y in (-W_HALF + 8, W_HALF - 8)]

# ---------------------------------------------------------------- brake (all on y = 0, z = 0 unless noted)
FELT_T = 1.5
SHOE_HW, SHOE_HZ = 6.0, 22.0                     # 12 wide, 44 tall
SHOE_X1 = 47.0                                   # its back face
SPRING_BORE = (35.0, SHOE_X1)                    # the spring's bore in the shoe's back, 10.6 across (Rev 3's seat)
SPRING_FIT = m.SPRING_FIT                        # 6.5 fitted, as Rev 3
CAP_X = (SPRING_BORE[0] + SPRING_FIT, 48.5)      # printed spring cap, 5.5 mm of it in the shoe's bore: the bolt's tip
                                                 # pushes its back face
# The shoe wraps the hub above its widest point, so while the lever is lowered into the frame the shoe has to stand
# back: its top corners are 9.5 mm inside the hub's outline. The pocket runs RETRACT behind the shoe for that, and
# backing the knob out ~11 mm lets the shoe, spring and cap slide back together.
RETRACT = 10.5
TOWER_X, TOWER_HW, TOWER_TOP = (32.0, 71.5), 10.0, 25.0
POCKET_X1 = SHOE_X1 + RETRACT                    # (57.5)
NUT5_X = 63.0                                    # captive M5 nut, slid in from the top
KNOB_X0 = TOWER_X[1] + 3.0                       # the knob's underside: 3 mm off the tower, room to screw in
BOLT_L = 30.0                                    # Rev 3's M5 x 30 hex bolt, its head on the knob's floor


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
        cuts.append(cyl(m.TAP[3] / 2, (px, s * (BLOCK_Y1 - COVER_TAP), pz), (px, s * (BLOCK_Y1 + 1), pz)))   # covers' M3
    return cuts


def anchor_clevis():
    """Rev 3's anchor_clevis() on the middle, its aft wall running level, at the cheeks' top, into the up-stop pad"""
    g = r.ROD_TAB_T + 0.6
    zt, zb = r.ANCH_Z + r.CLEVIS_R, Z_PLATE - 0.1
    ax = r.ANCH_X
    parts = [box(ax + r.ROD_TAB_W / 2 + 1.0, ax + r.CLEVIS_R, -g / 2 - 0.1, g / 2 + 0.1, zb, r.ANCH_Z)]
    for s in (-1, 1):
        y0, y1 = sorted((s * g / 2, s * (g / 2 + r.CLEVIS_T)))
        f0, f1 = sorted((s * (r.STRUT_ROD_D / 2 + r.ROD_CLEAR), s * (g / 2 + r.CLEVIS_T)))
        parts += [cyl(r.CLEVIS_R, (ax, y0, r.ANCH_Z), (ax, y1, r.ANCH_Z)),
                  box(ax - r.CLEVIS_R, ax + r.CLEVIS_R, y0, y1, zb, r.ANCH_Z),
                  gusset_xz([(ax, zt), (PED_X[0] + 1, zt), (PED_X[0] + 1, zb), (ax, zb)], y0, y1),
                  gusset_xz([(ax, zt), (ax - r.CLEVIS_RUN, zb), (ax, zb)], f0, f1)]
    return fuse(*parts)


def corner_gussets():
    """45 deg corner gussets (in plan) at both ends of each pillow block, CG_LEG along each wall:
    behind, outside   the block's back face to the outer face of the web behind it, up to the web's top
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
        out += [prism(q([(bx - 0.5, yw - 0.5), (bx - 0.5, yo), (bx + L, yw - 0.5)]), 0.0),                 # behind, outside
                prism(q([(bx, yi + 0.5), (bx - 0.5 - L, yi + 0.5), (bx, yi - L)]), 0.0)
                .cut(cyl(LUG_R + 1.5, (0, s * (yi - L - 1), 0), (0, s * (yi + 1), 0))),                   # behind, inside
                prism(q([(-bx, yi + 0.5), (-bx + 0.5 + L, yi + 0.5), (-bx, yi - L)]), PAD_Z)
                .cut(cyl(HUB_R + 3.0, (0, s * (yi - L - 1), 0), (0, s * (yi + 1), 0))),                   # in front, inside
                prism(q([(-bx + 0.5, yw - 0.5), (-bx + 0.5, yo), (-bx - L, yw - 0.5)]), PAD_Z)]           # in front, outside
    return out


def frame():
    plate = (cq.Workplane("XY").box(PLATE_X[1] - PLATE_X[0], 2 * W_HALF, m.PLATE_T, centered=False)
             .translate((PLATE_X[0], -W_HALF, -AXIS_H)).edges("|Z").fillet(6).val())
    parts = [plate]
    for s in (-1, 1):
        y0, y1 = sorted((s * BRG_Y0, s * BLOCK_Y1))
        yi, yo = s * BRG_Y0, s * BLOCK_Y1
        parts += [box(-BLOCK_HW, BLOCK_HW, y0, y1, Z_PLATE, 0),                                       # pillow block
                  # under the cover, a gusset from the block's outer face down to the plate's edge
                  (cq.Workplane("YZ").polyline([(yo - s * 0.5, Z_PLATE - 0.1), (yo - s * 0.5, -COVER_R - 1.0),
                                                (s * W_HALF, Z_PLATE - 0.1)]).close()
                   .extrude(2 * BLOCK_HW).translate((-BLOCK_HW, 0, 0)).val()),
                  # down-stop pillar under the pad, run on into the pillow block
                  box(PAD_X[0], -BLOCK_HW + 0.5, *sorted((s * PAD_DY[0], yi + s * 0.5)), Z_PLATE - 0.1, PAD_Z),
                  # web from the brake tower to the pillow block, behind the up-stop lugs
                  box(BLOCK_HW - 0.5, 56.0, *sorted((s * (TOWER_HW - 0.5), yi + s * 0.5)), Z_PLATE - 0.1, 0.0)]
    pad = box(*PED_X, -(BRG_Y0 + 0.5), BRG_Y0 + 0.5, Z_PLATE - 0.1, USTOP_Z).cut(
        box(PED_NOTCH[0], PED_X[1] + 1, -PED_NOTCH[1], PED_NOTCH[1], Z_PLATE, USTOP_Z + 1))
    parts += [pad, box(*TOWER_X, -TOWER_HW, TOWER_HW, Z_PLATE - 0.1, TOWER_TOP),                       # up-stop pad, brake tower
              anchor_clevis(), *corner_gussets()]
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
    # brake: the shoe's pocket (open to the hub), the spring cap's bore, the bolt, and the M5 nut slid in from the top
    nut_r = m.NUT_AF[5] / 2 / math.cos(math.radians(30))
    cuts += [box(TOWER_X[0] - 1, POCKET_X1, -SHOE_HW - 0.3, SHOE_HW + 0.3, -SHOE_HZ - 0.3, SHOE_HZ + 0.3),
             cyl(5.4, (POCKET_X1 - 0.1, 0, 0), (POCKET_X1 + 2.5, 0, 0)),
             cyl(m.CSK[5][1] / 2, (POCKET_X1, 0, 0), (TOWER_X[1] + 1, 0, 0)),
             hexprism(m.NUT_AF[5], (NUT5_X, 0, 0), (NUT5_X + m.NUT_T[5] + 0.2, 0, 0)).rotate(V(0, 0, 0), V(1, 0, 0), 30),
             box(NUT5_X, NUT5_X + m.NUT_T[5] + 0.2, -m.NUT_AF[5] / 2, m.NUT_AF[5] / 2, 0, TOWER_TOP + 1)]
    for x, y in DESK:
        cuts.append(cyl(2.75, (x, y, -AXIS_H - 1), (x, y, 0)))                                         # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def cap(s):
    y0, y1 = sorted((s * BRG_Y0, s * BLOCK_Y1))
    yb = (y0 + y1) / 2
    c = cyl(BLOCK_HW, (0, y0, 0), (0, y1, 0)).intersect(box(-60, 60, y0 - 1, y1 + 1, 0, 60))
    for k in block_cuts(s):
        c = c.cut(k)
    for x in (-CAP_BOLT_X, CAP_BOLT_X):
        c = c.cut(m.csk_hole(3, (x, yb, CAP_HEAD_Z), (0, 0, -1), 10, out=40))
    return c.clean()


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
    """Rev 3's knob (the MkII knob with an M5 hex pocket), lying on its side on the back of the tower"""
    sx, sy, sz = m.KNOB_X, m.KNOB_Y, m.KNOB_Z0
    k = r.friction_knob_r3().translate(V(-sx, -sy, -sz))                   # underside centre to the origin, axis +z
    return rot_y(k, 90).translate(V(KNOB_X0, 0, 0))                        # axis +x


def brake_hardware():
    """M5 x 30 hex bolt (head on the knob's floor) and its nut"""
    hb = KNOB_X0 + r.MK2_KNOB_FLOOR
    bolt = fuse(hexprism(m.M5_HEAD_AF - 0.1, (hb, 0, 0), (hb + m.KNOB_BOLT[1], 0, 0)),
                cyl(2.4, (hb - BOLT_L, 0, 0), (hb + 0.1, 0, 0)))
    return fuse(bolt, m.nut(5, (NUT5_X + 0.1, 0, 0), (1, 0, 0), turn=30))


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
    """the fixed base's screws and nuts (reference): caps, covers, the brake bolt and nut"""
    parts = [brake_hardware()]
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
PRINTED = ["frame", "cap_left", "cap_right", "lever_upper", "lever_lower", "shoe", "spring_cap", "cover_sensor",
           "cover_cable", "strut_collar", "friction_knob"]


_STATIC = {}
_COLLAR = []


def strut_collar(theta=0.0):
    """Rev 3's collar, unchanged (chamfered as Rev 3 prints it), on the middle"""
    if not _COLLAR:
        _COLLAR.append(moved(r.chamfer_edges(r._collar())))
    return rot_y(_COLLAR[0], theta)


def static_parts():
    """the parts that don't move, built once (the frame and caps chamfered, as Rev 3's)"""
    if not _STATIC:
        _STATIC.update({"frame": chamfer_edges(frame()), "cap_left": chamfer_edges(cap(-1)),
                        "cap_right": chamfer_edges(cap(1)), "shoe": shoe(), "spring_cap": spring_cap(),
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
           ("frame", "hardware"), ("cap_left", "hardware"), ("cap_right", "hardware"), ("cover_sensor", "hardware"),
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
    """the lever (bearings on) lowered straight down into the frame, from 80 mm up, with the shoe, spring and cap
    slid RETRACT back"""
    S = static_parts()
    back = V(RETRACT, 0, 0)
    fixed = {"frame": S["frame"], "shoe": S["shoe"].translate(back), "felt": S["felt"].translate(back),
             "spring_cap": S["spring_cap"].translate(back)}
    lever_b = fuse(*lever_halves(0.0), *[bearing(s)[k] for s in (-1, 1) for k in range(3)])
    worst = {}
    z = 80.0
    while z >= -0.01:
        mv = lever_b.translate(V(0, 0, z))
        for k, f in fixed.items():
            vol = mv.intersect(f).Volume()
            if vol > 0.01:
                worst[k] = max(worst.get(k, (0, 0)), (vol, z))
        z -= step
    print("lowering the lever in: " + ("clear" if not worst else
                                         "; ".join(f"{k} {v:.2f} mm3 at z {zz:.0f}" for k, (v, zz) in worst.items())))


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
        check_assembly()
    elif "--coupons" in sys.argv[1:]:
        export_coupons()
    else:
        export()
