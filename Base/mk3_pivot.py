"""
MkIII collective base - Rev 1 model (CONCEPT, not print-tested)

Rev 3 (mk3_rev3.py) imports this file for every part it shares with Rev 1 and for the fit parameters, and writes
the base's STLs and STEP itself. Rev 1's own parts (ballast bucket, quadrant up-stop, striker) are still modelled
here but no longer exported; the notes below describe Rev 1. Run with a Python that has cadquery installed:
    python mk3_pivot.py            -> only writes the fit-test coupons to stl/coupons/ (see README.md)

Coordinate frame (same as the MkII STLs):
    origin = pivot centre, Y = pivot axis, Z = up, tube points along -X at 0 deg.
    +Y = knob / friction side (USB exits here), -Y = AS5600 sensor side.

Lever = TWO prints split horizontally at z = 0 through the pivot axis and the tube axis (hub, drum,
socket and both trunnions are halved). Each half prints flat on its joint face with no supports.
Four countersunk M4 x 20 screws (screw kit) from the top into hex nuts recessed in the bottom half; the cone
heads centre the halves, and each bearing's inner race clamps its two half trunnions.
Both cable bores are half-round channels in each half, so the cables are laid in before closing it:
    axial  - right through both trunnions along the pivot axis (13 mm)
    radial - from the socket bottom along the tube axis until it meets the axial bore (13 mm)
The hose clamp on the socket mouth holds the two halves together there; the M4 lock screw pins the tube.

Travel: fixed down-stop at 0 deg (screw under the socket boss). Up-stop adjustable 30-40 deg:
a stop block clamps anywhere along an arc slot in the graduated quadrant behind the pivot,
and an M6 striker bolt on the ballast bucket lands on it.

Ballast: a lidded bucket bolts to a pad on the back of the lever (upper half), angled up 40 deg so it
is level at 40 deg of travel and clears the desk. At 20 deg the tube and bucket are mirror images about the
vertical, so the balance is exact there. At 0 and 40 deg it is out by about 34 g*m (25 % of the forward moment
at 20 deg), about 125 g at the grip centre 275 mm out; the friction knob holds that. The ballast
must be FIXED against the far wall (stick-on wheel weights or shot set in epoxy): loose shot would slide
to the pivot end whenever the bucket tilts up.

Sensor (-Y side): WWZMDiB AS5600 module (23 x 23 mm) in a carrier that plugs into the trunnion bore
and turns with the lever; its 4 x 2 mm diametric magnet sits on the axis in the fixed cover, ~1.0 mm
from the chip. Three wires (VCC, OUT, GND) run under the board, through the carrier and up the tube to
AX1 on the HeliSR board. Run at 5 V: remove the module's 0 ohm R1 (it ties VDD3V3 to VDD5V; the 3V3 pin
is rated 4 V max). Jumper DIR to VCC (it floats on this module): the chip turns with the lever and the
magnet is fixed, so DIR = VCC makes OUT rise as the lever lifts. (It can't be checked beforehand: with PGO
low, OUT reads full scale until programming is done.) PGO (labelled GPO on the module) already has 1 k to GND. The range is programmed once through the OUT pin (datasheet Option B) with the
HeliSR Rev 3.0 PROG1 button, because the Pro Micro's I2C pins drive the shift registers.

Gussets: wedge ribs above and below the socket boss tie it into the hub; on the frame a web ties both
shoe hinge lugs into the quadrant stem, and a corner gusset ties the knob tower to the +y pillow block.

Bought parts the geometry is built around:
    2 x 6006-2RS deep-groove ball bearing (30 x 55 x 13)
    25 x 1 mm aluminium tube (unchanged), slides INTO a 46 mm deep socket
    worm-drive hose clamp (approx. 25-40 mm range) on the relieved socket mouth
    4 x M4 x 20 countersunk (DIN 7991) + 4 x M4 nut joining the lever halves

Every screw and nut comes from two kits (see Fasteners below); the base's are listed in mk3_rev3.py.
"""
import os
import sys
import math
import cadquery as cq

V = cq.Vector

# ---------------------------------------------------------------- parameters
TUBE_OD, TUBE_ID = 25.0, 23.0

BRG_d, BRG_D, BRG_B = 30.0, 55.0, 13.0          # 6006-2RS
BRG_IR_SH, BRG_OR_SH = 38.2, 47.0               # inner / outer race shoulder dia (approx.)

HUB_HW = 32.0            # hub spans y = -32..32
HUB_R = 28.0             # hub core radius
DRUM_R, DRUM_Y0, DRUM_Y1 = 30.0, 12.0, 32.0     # friction drum
SOCK_Y = -9.0            # socket centre line (y)
SOCK_BOSS_R = 18.0
SOCK_BORE_R = 12.7       # 25.4 bore for the 25 mm tube
SOCK_BOTTOM = 20.0       # tube bottoms out at x = -20
SOCK_MOUTH = 66.0        # boss ends at x = -66  (46 mm engagement)
CABLE_R = 6.5            # 13 mm (1/2") cable channels, half in each lever half
TUBE_LOCK_X = -50.5      # M4 lock screw on top of the boss (drill the tube 30.5 mm from its end in Rev 1; 38.5 in Rev 3)

TRUN_OD = 30.2                   # trunnion = bearing seat, printed as part of the lever (coupon step +0.2 fits: locked in)
BRG_Y0 = HUB_HW + 1.0            # bearing inner face |y|  (33)
BRG_Y1 = BRG_Y0 + BRG_B          # bearing outer face |y|  (46)
BLOCK_Y1 = BRG_Y1 + 4.0          # pillow block outer face |y| (50), 4 mm retaining lip
TRUN_OUT = BLOCK_Y1 + 2.0        # trunnion outer end |y| (52)
BLOCK_HW = 35.0                  # pillow block half width (x) and cap radius
LIP_R = 21.5                     # lip bore radius: clears inner race, holds outer race
BRG_SEAT_D = BRG_D + 0.1         # printed bearing seat bore in the pillow blocks (coupon step 0 fits: locked in)
CAP_BOLT_X = 31.5
COVER_R, COVER_IN_R, COVER_D = 34.0, 26.0, 15.0   # 34: room round the M3 countersinks in the outer face
COVER_HOLE_R = 30.0              # M3 fixing circle for side covers
COVER_TAP_DEPTH = 7.0            # the covers' M3 holes are tapped this deep into the block face
USB_SIDE, SENSOR_SIDE = 1, -1    # USB exits on the knob side, sensor on the other

AXIS_H = 40.0                    # pivot height above underside of plate
PLATE_T = 6.0
Z_PLATE = -AXIS_H + PLATE_T      # top of plate (-34)
PLATE_X0, PLATE_X1 = -62.0, 54.0
PLATE_HW = BLOCK_Y1              # plate spans y = -50..50

SHOE_Y0, SHOE_Y1 = 13.0, 31.0
FELT_T = 1.5
SHOE_T = 5.5
KNOB_X, KNOB_Y = -45.0, 22.0
HINGE_X, HINGE_Z = 45.0, -4.0
# friction knob: an M5 x 20 countersunk screw, its head glued into the printed knob, runs down through the spring and
# the shoe's front tab (top at z = 5) into an M5 nut slid into a slot just under the knob tower's top (z = -1)
SPRING_SEAT = 2.0                # the spring sits in a 10.6 mm recess this deep in the shoe's tab
SPRING_FIT = 6.5                 # fitted spring length
KNOB_Z0 = 5.0 - SPRING_SEAT + SPRING_FIT      # the knob's underside (9.5)
KNOB_HEAD_Z = KNOB_Z0 + 3.0      # top of the screw's head, inside the knob: the screw ends at z = -7.5
KNOB_D, KNOB_H, KNOB_FLUTES = 28.0, 10.0, 10
FN_NUT_Z = -3.2                  # the nut's top face, pulled up against its slot's roof

# travel stop
TRAVEL_MIN, TRAVEL_MAX = 30.0, 40.0   # adjustable range of the up-stop
STOP_SET = 35.0                       # where the block sits in the model / renders
STRIKER_R = 62.0                      # striker bolt radius from the pivot
STRIKER_HEAD_R = 5.0                  # M6 hex head ~ 10 mm
STOP_BLOCK = 12.0                     # stop block size in the quadrant plane
QUAD_Y0, QUAD_Y1 = 19.0, 25.0         # quadrant plate
QUAD_R0, QUAD_R1 = 54.0, 86.0
M5_CLR_R = 2.7                        # M5 clearance: arc slot half width, stop block and thumb knob holes
M5_NUT_AF = 8.1                       # M5 nut pocket in the stop block, across flats
M5_HEAD_AF, M5_HEAD_DEPTH = 8.1, 3.6   # M5 hex bolt head pressed into the thumb knob (M5 x 16)

# ballast bucket (local frame: u along the bucket axis, w across it, y as world)
BKT_ANG = 40.0                        # bucket axis above the rear horizontal at 0 deg (level at 40 deg of travel)
BKT_U0, BKT_U1 = 30.0, 160.0
BKT_W = 30.0
BKT_Y0, BKT_Y1 = -30.0, 8.0
BKT_WIDE_U0, BKT_WIDE_Y0 = 53.0, -62.0   # wider section once clear of the pillow block and sensor cover
BKT_T = 3.0
BKT_BOLTS = [(-10, -22), (10, -22), (-10, -1), (10, -1)]     # (w, y) M4 bolts into the lever pad
BKT_LID_BOSSES = [(37, 1.5), (95, 1.5), (154, 1.5), (154, -56), (95, -56), (60, -56), (37, -25)]   # (u, y)
BALANCE_AT = 20.0                     # travel angle where tube and bucket are mirror images (mid of 0-40)

# AS5600 sensor (carrier and cover on the -Y side)
AS5600_BOARD = 23.0              # WWZMDiB module (Amazon B0CM3C8KFT), 23 x 23 mm; measure yours
AS5600_CHIP_OFS = (0.0, 0.0)     # chip centre relative to board centre (x, z); shift if yours is off-centre
AS5600_PAD_X = 4.7               # VCC/OUT/GND through-hole pads: this far in from the board's +x edge (measured off the
AS5600_PAD_PITCH = 2.54          #   product photo, +-0.3 mm; centred on the board's z). No header: wires soldered through
CARRIER_FLANGE_T = 6.0           # board pocket on the outer face, wire channel underneath
MAGNET_GAP = 1.0                 # chip face to magnet face (datasheet: 0.5-3 mm); 1.5 at first, closed up 0.5 on 2026-10-23 to match the head
MAGNET_D, MAGNET_H = 4.0, 2.0    # diametric magnet supplied with the module (about 4 mm across, as measured)
MAGNET_POCKET = 4.2              # the cover's magnet pocket, the same as the head axle's. LOCKED IN: 4.2 fits the magnet, printed 2026-10-24 (4.0 was too small)
BALLAST_L = 42.0                 # fixed ballast depth against the far wall, ~0.95 kg at 6.8 g/cm3 (README)

# Fasteners: every screw and nut is from the two kits the user has. AvrestYPT (Amazon B0FMD5TMSH): countersunk
# hex-socket screws with 90 degree heads (DIN 7991 / ISO 10642), M3 and M4 x 8, 12, 16, 20 and M5 x 10, 12, 16, 20,
# with M3-M5 hex nuts and washers. HIQTRADEBYJJ (Amazon B0DG33R714): set screws, M3 x 3-6, M4 x 4-6, M5 x 5 and 8,
# M6 x 6 and 10, M8 x 8. No heat-set inserts: nuts in pockets, or M3 / M4 threads tapped into the print.
CSK = {3: (6.9, 3.4), 4: (8.6, 4.4), 5: (10.6, 5.5)}   # M size: countersink across at the surface (the heads sit just
                                                        # below flush), clearance hole
NUT_AF = {3: 5.7, 4: 7.2, 5: 8.2}                       # nut pockets across flats (the nuts are 5.5, 7 and 8)
NUT_T = {3: 2.4, 4: 3.2, 5: 4.0}                        # nut thickness
TAP = {3: 2.5, 4: 3.3, 5: 4.2}                          # pilots to tap

# split lever: countersunk M4 x 20 (kit) from the top, M4 nuts recessed in the bottom half
LEVER_SCREWS = [(-17.0, -25.0), (-17.0, 8.5), (14.0, -11.0), (14.0, 8.5)]   # (x, y)
LS_SEAT_Z = 8.5                  # top of the countersink (head flush here), counterbored above
LS_NUT_Z = 8.0                   # nut bears on z = -8, pocket open to the underside; the screw ends 0.3 mm past the nut
LS_CLR_R, LS_HEAD_R, LS_CB_R = 2.2, 4.5, 4.6
LS_NUT_AF = 7.2                  # M4 nut 7 mm across flats + clearance

# socket gussets, profiles in the XZ plane at y = SOCK_Y, mirrored for the bottom one
GUSSET_T = 8.0
GUSSET_TOP = [(-48, 16.5), (-2, 33.0), (8, 26.5), (8, 16.5)]
GUSSET_BOT = [(-48, -16.5), (-2, -30.0), (8, -26.5), (8, -16.5)]

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- helpers
def cyl(r, p0, p1):
    p0, p1 = V(*p0), V(*p1)
    d = p1 - p0
    return cq.Solid.makeCylinder(r, d.Length, p0, d.normalized())


def tube(ro, ri, p0, p1):
    return cyl(ro, p0, p1).cut(cyl(ri, p0, p1))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def xz_plane(y):
    # local (u, v) == world (x, z); extrude goes toward -y
    return cq.Plane(origin=(0, y, 0), xDir=(1, 0, 0), normal=(0, -1, 0))


def sector(ri, ro, a0, a1, y0, y1):
    """annular sector in the XZ plane, angles in degrees from +X toward +Z"""
    def p(r, a):
        return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    am = (a0 + a1) / 2
    wp = (cq.Workplane(xz_plane(y1)).moveTo(*p(ri, a0)).lineTo(*p(ro, a0))
          .threePointArc(p(ro, am), p(ro, a1)).lineTo(*p(ri, a1))
          .threePointArc(p(ri, am), p(ri, a0)).close().extrude(y1 - y0))
    return wp.val()


def hexprism(af, p0, p1):
    p0, p1 = V(*p0), V(*p1)
    d = p1 - p0
    pl = cq.Plane(origin=p0, xDir=(1, 0, 0) if abs(d.normalized().x) < .9 else (0, 1, 0), normal=d.normalized())
    return cq.Workplane(pl).polygon(6, af / math.cos(math.radians(30))).extrude(d.Length).val()


def csk_hole(size, p, d, length, out=1.0):
    """cutter for a countersunk M`size` screw whose head top is at p, going `length` along d (into the part): the 90 deg
    cone, the clearance hole, and `out` mm of counterbore back out from p (clears a curved or recessed face)"""
    D, c = CSK[size]
    p, d = V(*p), V(*d).normalized()
    return fuse(cyl(D / 2, (p - d * out).toTuple(), p.toTuple()), cq.Solid.makeCone(D / 2, c / 2, (D - c) / 2, p, d),
                cyl(c / 2, p.toTuple(), (p + d * length).toTuple()))


def csk_screw(size, p, d, length):
    """countersunk M`size` x length (reference, for renders): head top at p, pointing along d"""
    D = CSK[size][0] - 0.3
    p, d = V(*p), V(*d).normalized()
    k = (D - size) / 2
    return fuse(cq.Solid.makeCone(D / 2, size / 2, k, p, d), cyl(0.42 * size, (p + d * k).toTuple(), (p + d * length).toTuple()))


def grub_screw(size, length, p, d):
    """set screw (reference): from p along d"""
    p, d = V(*p), V(*d).normalized()
    return cyl(0.42 * size, p.toTuple(), (p + d * length).toTuple())


def nut(size, p, d, turn=0.0):
    """hex nut (reference): from p along d; turn = 30 puts its flats where hexprism() puts its corners"""
    p, d = V(*p), V(*d).normalized()
    n = hexprism(NUT_AF[size] - 0.2, p.toTuple(), (p + d * NUT_T[size]).toTuple())
    n = n.cut(cyl(0.42 * size, (p - d).toTuple(), (p + d * (NUT_T[size] + 1)).toTuple()))
    return n.rotate(p, p + d, turn) if turn else n


def fuse(*shapes):
    s = shapes[0]
    for o in shapes[1:]:
        s = s.fuse(o)
    return s.clean()


def _perp(t):
    t = V(*t)
    a = V(0, 0, 1) if abs(t.z) < 0.9 else V(1, 0, 0)
    return t.cross(a).normalized()


def sweep_circle(r, path_wire, start, tangent):
    pl = cq.Plane(origin=start, xDir=_perp(tangent), normal=tangent)
    return cq.Workplane(pl).circle(r).sweep(cq.Workplane().add(path_wire), transition="round").val()


def on_circle(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def rot_y(shape, deg):
    """rotate about the pivot axis; +deg lifts the tube (same sense as lever travel)"""
    return shape.rotate((0, 0, 0), (0, 1, 0), deg)


def to_bucket(shape):
    """local bucket frame (u along +X, w along +Z) -> lever frame"""
    return rot_y(shape, -BKT_ANG)


def mirror_y(shape):
    return shape.mirror("XZ")


def side_shape(shape, side):
    return shape if side > 0 else mirror_y(shape)


# ---------------------------------------------------------------- lever (two halves, split at z = 0)
def lever_screw_cuts():
    """per screw: counterbore + 90 deg countersink + clearance from the top, hex nut pocket from the bottom"""
    cuts = []
    for x, y in LEVER_SCREWS:
        sink = LS_HEAD_R - LS_CLR_R
        cuts += [cyl(LS_CB_R, (x, y, LS_SEAT_Z), (x, y, 60)),
                 cq.Solid.makeCone(LS_CLR_R, LS_HEAD_R, sink, V(x, y, LS_SEAT_Z - sink), V(0, 0, 1)),
                 cyl(LS_CLR_R, (x, y, -LS_NUT_Z), (x, y, LS_SEAT_Z)),
                 hexprism(LS_NUT_AF, (x, y, -60), (x, y, -LS_NUT_Z))]
    return cuts


def lever_halves():
    h = lever()
    for c in lever_screw_cuts():
        h = h.cut(c)
    h = h.clean()
    up = h.intersect(box(-200, 200, -100, 100, 0, 200)).clean()
    lo = h.intersect(box(-200, 200, -100, 100, -200, 0)).clean()
    return up, lo


def lever():
    """the whole lever as one solid; lever_halves() splits it and adds the joint screws"""
    core = cyl(HUB_R, (0, -HUB_HW, 0), (0, HUB_HW, 0))
    drum = cyl(DRUM_R, (0, DRUM_Y0, 0), (0, DRUM_Y1, 0))
    boss = cyl(SOCK_BOSS_R, (-10, SOCK_Y, 0), (-SOCK_MOUTH, SOCK_Y, 0))
    # shoulders touch the bearing inner races only
    shoulders = [cyl(BRG_IR_SH / 2 - 1.1, (0, s * HUB_HW, 0), (0, s * BRG_Y0, 0)) for s in (-1, 1)]
    trunnions = [cyl(TRUN_OD / 2, (0, s * BRG_Y0, 0), (0, s * TRUN_OUT, 0)) for s in (-1, 1)]
    pad = to_bucket(box(18, BKT_U0, BKT_Y0, BKT_Y1, -18, 18))            # ballast bucket mount
    gussets = [cq.Workplane(xz_plane(SOCK_Y + GUSSET_T / 2)).polyline(pts).close().extrude(GUSSET_T).val()
               for pts in (GUSSET_TOP, GUSSET_BOT)]
    h = fuse(core, drum, boss, pad, *gussets, *shoulders, *trunnions)

    cuts = [
        cyl(SOCK_BORE_R, (-SOCK_BOTTOM, SOCK_Y, 0), (-SOCK_MOUTH - 1, SOCK_Y, 0)),          # tube socket
        tube(SOCK_BOSS_R + 1, SOCK_BOSS_R - 1.2, (-54, SOCK_Y, 0), (-63, SOCK_Y, 0)),        # hose-clamp groove
        cyl(CABLE_R, (0, -TRUN_OUT - 1, 0), (0, TRUN_OUT + 1, 0)),                            # axial 1/2" bore
        cyl(CABLE_R, (-SOCK_BOTTOM - 1, SOCK_Y, 0), (3, SOCK_Y, 0)),                          # radial 1/2" bore
        cyl(2.8, (TUBE_LOCK_X, SOCK_Y, 10), (TUBE_LOCK_X, SOCK_Y, 20)),                       # M4 insert, tube lock
    ]
    for w, y in BKT_BOLTS:                                                                    # M4 inserts for bucket
        cuts.append(to_bucket(cyl(2.8, (BKT_U0 - 9, y, w), (BKT_U0 + 1, y, w))))
    for c in cuts:
        h = h.cut(c)
    return h.clean()


# ---------------------------------------------------------------- ballast bucket + lid
def bucket():
    U0, U1, W, T = BKT_U0, BKT_U1, BKT_W, BKT_T
    outer = fuse(box(U0, U1, BKT_Y0, BKT_Y1, -W, W), box(BKT_WIDE_U0, U1, BKT_WIDE_Y0, BKT_Y0 + 1, -W, W))
    inner = fuse(box(U0 + 4, U1 - T, BKT_Y0 + T, BKT_Y1 - T, -W + T, W + 1),
                 box(BKT_WIDE_U0 + T, U1 - T, BKT_WIDE_Y0 + T, BKT_Y0 + T + 1, -W + T, W + 1))
    b = outer.cut(inner)
    for u, y in BKT_LID_BOSSES:                                                               # lid screw bosses
        b = b.fuse(cyl(3.6, (u, y, -W + T - 0.1), (u, y, W)))
    su = STRIKER_R                                                                            # striker boss, +y wall
    b = b.fuse(box(su - 7, su + 7, BKT_Y1 - 0.1, BKT_Y1 + 4, -7, 7))
    b = b.clean()
    cuts = [cyl(4.0, (su, BKT_Y1 - T - 1, 0), (su, BKT_Y1 + 5, 0))]                          # M6 heat-set insert
    for u, y in BKT_LID_BOSSES:
        cuts.append(cyl(2.1, (u, y, W - 7), (u, y, W + 1)))                                   # M3 inserts
    for w, y in BKT_BOLTS:
        cuts.append(cyl(2.25, (U0 - 1, y, w), (U0 + 5, y, w)))                                # M4 through floor
    for c in cuts:
        b = b.cut(c)
    return to_bucket(b.clean())


def bucket_lid():
    W = BKT_W
    lid = fuse(box(BKT_U0, BKT_U1, BKT_Y0, BKT_Y1, W, W + 2.5),
               box(BKT_WIDE_U0, BKT_U1, BKT_WIDE_Y0, BKT_Y0 + 1, W, W + 2.5))
    lip = fuse(box(BKT_U0 + 4.4, BKT_U1 - 3.4, BKT_Y0 + 3.4, BKT_Y1 - 3.4, W - 2, W + 0.1),
               box(BKT_WIDE_U0 + 3.4, BKT_U1 - 3.4, BKT_WIDE_Y0 + 3.4, BKT_Y0 + 4, W - 2, W + 0.1))
    for u, y in BKT_LID_BOSSES:
        lip = lip.cut(cyl(4.2, (u, y, W - 3), (u, y, W + 1)))
    lid = lid.fuse(lip).clean()
    for u, y in BKT_LID_BOSSES:
        lid = lid.cut(cyl(1.7, (u, y, W - 3), (u, y, W + 3)))
        lid = lid.cut(cq.Solid.makeCone(1.7, 3.3, 1.6, V(u, y, W + 0.95), V(0, 0, 1)))
    return to_bucket(lid.clean())


def striker():
    """M6 bolt in a heat-set insert; its head is the stop striker"""
    su = STRIKER_R
    s = fuse(cyl(3, (su, BKT_Y1 - 3, 0), (su, BKT_Y1 + 5, 0)), cyl(STRIKER_HEAD_R, (su, BKT_Y1 + 5, 0), (su, BKT_Y1 + 9, 0)))
    return to_bucket(s)


# ---------------------------------------------------------------- travel stop
def stop_angle(theta):
    """quadrant angle of the stop-block centre that stops the lever at theta"""
    half = STOP_BLOCK / 2
    return BKT_ANG - theta - math.degrees(math.asin((half + STRIKER_HEAD_R) / STRIKER_R))


def arc_slot(a0, a1, r=M5_CLR_R):
    """cutter for the M5 clamp-bolt slot through the quadrant, end centres at a0..a1 deg"""
    slot = sector(STRIKER_R - r, STRIKER_R + r, a0, a1, QUAD_Y0 - 1, QUAD_Y1 + 1)
    for a in (a0, a1):
        x, z = on_circle(STRIKER_R, a)
        slot = slot.fuse(cyl(r, (x, QUAD_Y0 - 1, z), (x, QUAD_Y1 + 1, z)))
    return slot


def quadrant():
    q = sector(QUAD_R0, QUAD_R1, stop_angle(TRAVEL_MAX + 1) - 8, stop_angle(TRAVEL_MIN - 1) + 8, QUAD_Y0, QUAD_Y1)
    q = q.fuse(box(48, 86, QUAD_Y0, QUAD_Y1, Z_PLATE - 0.1, -18)).intersect(box(0, 100, 0, 40, Z_PLATE, 40)).clean()
    q = q.cut(arc_slot(stop_angle(TRAVEL_MAX + 1), stop_angle(TRAVEL_MIN - 1)))
    # engraved scale on the outer (+y) face, read against the pointer on the thumb knob
    for t in range(int(TRAVEL_MIN), int(TRAVEL_MAX) + 1):
        a = stop_angle(t)
        major = t % 5 == 0
        r0, r1 = (69.0, 79.0) if major else (72.0, 77.0)
        p0, p1 = on_circle(r0, a), on_circle(r1, a)
        d = V(p1[0] - p0[0], 0, p1[1] - p0[1])
        tick = cq.Solid.makeBox(d.Length, 0.8, 0.9 if major else 0.6, V(0, 0, 0))
        tick = tick.translate(V(0, -0.4, -0.45 if major else -0.3)).rotate((0, 0, 0), (0, 1, 0), -a)
        tick = tick.translate(V(p0[0], QUAD_Y1 - 0.4, p0[1]))
        q = q.cut(tick)
        if major:
            x, z = on_circle(82.5, a)
            pl = cq.Plane(origin=(x, QUAD_Y1, z), xDir=(-1, 0, 0), normal=(0, 1, 0))
            txt = cq.Workplane(pl).text(str(t), 4.2, -0.6, combine=False, halign="center", valign="center").val()
            q = q.cut(txt)
    return q.clean()


def _stop_block(clr=M5_CLR_R, af=M5_NUT_AF):
    h = STOP_BLOCK / 2
    b = box(STRIKER_R - h, STRIKER_R + h, 13, QUAD_Y0, -h, h)                              # 1 mm clear of the striker boss
    b = b.cut(cyl(clr, (STRIKER_R, 12, 0), (STRIKER_R, QUAD_Y0 + 1, 0)))
    return b.cut(hexprism(af, (STRIKER_R, 12, 0), (STRIKER_R, 17, 0)))                     # M5 nut pocket


def stop_block(theta=STOP_SET):
    return rot_y(_stop_block(), -stop_angle(theta)).clean()


def thumb_knob(theta=STOP_SET):
    k = cyl(9, (STRIKER_R, QUAD_Y1, 0), (STRIKER_R, QUAD_Y1 + 7, 0))
    pointer = box(STRIKER_R + 6, STRIKER_R + 15, QUAD_Y1, QUAD_Y1 + 2.5, -1.5, 1.5)
    k = k.fuse(pointer).cut(cyl(M5_CLR_R, (STRIKER_R, QUAD_Y1 - 1, 0), (STRIKER_R, QUAD_Y1 + 8, 0)))
    k = k.cut(hexprism(M5_HEAD_AF, (STRIKER_R, QUAD_Y1 + 7 - M5_HEAD_DEPTH, 0), (STRIKER_R, QUAD_Y1 + 8, 0)))   # bolt head, pressed in
    for i in range(8):
        a = i * 45 + 22.5
        x, z = on_circle(9.6, a)
        k = k.cut(cyl(1.6, (STRIKER_R + x, QUAD_Y1 + 2.5, z), (STRIKER_R + x, QUAD_Y1 + 8, z)))
    return rot_y(k, -stop_angle(theta)).clean()


# ---------------------------------------------------------------- frame
def block_cuts(s):
    cuts = [cyl(BRG_SEAT_D / 2, (0, s * (BRG_Y0 - 0.5), 0), (0, s * BRG_Y1, 0)),         # bearing seat
            cyl(LIP_R, (0, s * (BRG_Y1 - 1), 0), (0, s * (BLOCK_Y1 + 1), 0))]           # retaining lip bore
    for a in (45, 135, 225, 315):
        px, pz = on_circle(COVER_HOLE_R, a)
        cuts.append(cyl(TAP[3] / 2, (px, s * (BLOCK_Y1 - COVER_TAP_DEPTH), pz), (px, s * (BLOCK_Y1 + 1), pz)))  # covers' M3
    return cuts


def frame_solid():
    plate = (cq.Workplane("XY").box(PLATE_X1 - PLATE_X0, 2 * PLATE_HW, PLATE_T, centered=False)
             .translate((PLATE_X0, -PLATE_HW, -AXIS_H)).edges("|Z").fillet(6).val())
    tongue = (cq.Workplane("XY").box(90 - 40, 34 - 10, PLATE_T, centered=False)
              .translate((40, 10, -AXIS_H)).edges("|Z").fillet(5).val())                     # under the quadrant
    blocks = [box(-BLOCK_HW, BLOCK_HW, *sorted((s * BRG_Y0, s * BLOCK_Y1)), Z_PLATE, 0) for s in (-1, 1)]
    tower = box(-54, -36, SHOE_Y0, SHOE_Y1, Z_PLATE, -1)
    lugs = [box(40, 51, 12, 16.5, Z_PLATE, 2), box(40, 51, 27.5, 32, Z_PLATE, 2)]
    lug_round = [cyl(5.5, (HINGE_X, y0, HINGE_Z), (HINGE_X, y1, HINGE_Z)) for y0, y1 in ((12, 16.5), (27.5, 32))]
    down_post = cyl(5, (-50, SOCK_Y, Z_PLATE), (-50, SOCK_Y, -26))
    lug_web = box(40, 51, 12, 32, Z_PLATE, -14)                       # ties both hinge lugs into the quadrant stem
    tower_web = (cq.Workplane("XY").workplane(offset=Z_PLATE - 0.1)  # corner gusset: knob tower to +y pillow block
                 .polyline([(-54, 30.5), (-34.5, 30.5), (-34.5, 48)]).close().extrude(-2 - Z_PLATE + 0.1).val())
    f = fuse(plate, tongue, *blocks, tower, *lugs, *lug_round, down_post, lug_web, tower_web, quadrant())

    cuts = []
    for s in (-1, 1):
        cuts += block_cuts(s)
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            cuts.append(cyl(2.8, (x, s * (BRG_Y0 + BLOCK_Y1) / 2, -9), (x, s * (BRG_Y0 + BLOCK_Y1) / 2, 1)))  # M4 inserts
    cuts += [cyl(3.3, (KNOB_X, KNOB_Y, 0), (KNOB_X, KNOB_Y, Z_PLATE - 7)),                    # M6 clearance
             box(-55, KNOB_X + 5.8, KNOB_Y - 5.2, KNOB_Y + 5.2, -16, -10.6),                  # side-loaded M6 nut
             cyl(2.2, (HINGE_X, 10, HINGE_Z), (HINGE_X, 34, HINGE_Z)),                        # hinge pin
             cyl(2.8, (-50, SOCK_Y, -34), (-50, SOCK_Y, -25))]                                # down-stop insert
    for x in (PLATE_X0 + 8, PLATE_X1 - 8):
        for y in (-PLATE_HW + 8, PLATE_HW - 8):
            cuts.append(cyl(2.75, (x, y, -50), (x, y, 0)))                                     # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def cap(side):
    s = side
    yb = s * (BRG_Y0 + BLOCK_Y1) / 2
    c = cyl(BLOCK_HW, (0, s * BRG_Y0, 0), (0, s * BLOCK_Y1, 0)).intersect(box(-60, 60, -60, 60, 0, 60))
    cuts = block_cuts(s)
    for x in (-CAP_BOLT_X, CAP_BOLT_X):
        cuts.append(csk_hole(4, (x, yb, 8), (0, 0, -1), 10, out=40))       # M4 x 20 countersunk, head 8 mm above the joint
    for k in cuts:
        c = c.cut(k)
    return c.clean()


# ---------------------------------------------------------------- friction shoe
def shoe():
    ri, ro = DRUM_R + FELT_T, DRUM_R + FELT_T + SHOE_T
    arc = sector(ri, ro, 0, 180, SHOE_Y0, SHOE_Y1)
    front_tab = box(-54, -ri - 1, SHOE_Y0, SHOE_Y1, 0, 5)
    web = box(ri + 1, HINGE_X, 17, 27, HINGE_Z - 5, 3)
    eye = cyl(5.5, (HINGE_X, 17, HINGE_Z), (HINGE_X, 27, HINGE_Z))
    s = fuse(arc, front_tab, web, eye)
    s = s.cut(cyl(DRUM_R + FELT_T, (0, 0, 0), (0, 40, 0)))
    s = s.cut(cyl(CSK[5][1] / 2, (KNOB_X, KNOB_Y, -5), (KNOB_X, KNOB_Y, 10)))                  # M5 friction screw
    s = s.cut(cyl(5.3, (KNOB_X, KNOB_Y, 5 - SPRING_SEAT), (KNOB_X, KNOB_Y, 6)))                # spring seat
    s = s.cut(cyl(2.2, (HINGE_X, 10, HINGE_Z), (HINGE_X, 34, HINGE_Z)))
    return s.clean()


def friction_knob():
    """printed knob on the M5 x 20 friction screw: the screw's head is glued into its countersink (a hex key still
    reaches the head through the top), and a spigot under it centres the spring. Prints top face down."""
    z0, z1 = KNOB_Z0, KNOB_Z0 + KNOB_H
    r = KNOB_D / 2
    k = cyl(r, (KNOB_X, KNOB_Y, z0), (KNOB_X, KNOB_Y, z1)).fuse(cyl(3.7, (KNOB_X, KNOB_Y, z0 - 1.5), (KNOB_X, KNOB_Y, z0 + 0.1)))
    k = k.intersect(cyl(r + 1, (KNOB_X, KNOB_Y, z0 - 2), (KNOB_X, KNOB_Y, z1 - 1)).fuse(
        cq.Solid.makeCone(r + 1, r - 1.0, 2.0, V(KNOB_X, KNOB_Y, z1 - 1.01), V(0, 0, 1))))          # 1 mm top chamfer
    for i in range(KNOB_FLUTES):
        x, y = on_circle(r + 1.0, (i + 0.5) * 360 / KNOB_FLUTES)
        k = k.cut(cyl(2.5, (KNOB_X + x, KNOB_Y + y, z0 - 1), (KNOB_X + x, KNOB_Y + y, z1 + 1)))
    k = k.cut(csk_hole(5, (KNOB_X, KNOB_Y, KNOB_HEAD_Z), (0, 0, -1), 10, out=z1 - KNOB_HEAD_Z + 1))
    return k.clean()


def felt():
    return sector(DRUM_R + 0.05, DRUM_R + FELT_T, 2, 178, SHOE_Y0 + 0.5, SHOE_Y1 - 0.5)


# ---------------------------------------------------------------- sensor + side covers
# built on +Y, then mirrored to the sensor side
FLANGE_Y1 = TRUN_OUT + CARRIER_FLANGE_T              # outer face of the carrier flange
BOARD_Y0 = FLANGE_Y1 - 1.8                            # board sits in a 1.8 mm pocket
CHIP_Y1 = BOARD_Y0 + 1.6 + 1.5                        # SOIC-8 top face
MAGNET_Y = CHIP_Y1 + MAGNET_GAP                       # magnet face / inner face of the cover floor


def _carrier():
    plug = cyl(CABLE_R - 0.15, (0, TRUN_OUT - 7, 0), (0, TRUN_OUT, 0))
    flange = cyl(20, (0, TRUN_OUT, 0), (0, FLANGE_Y1, 0))
    c = fuse(plug, flange)
    b = AS5600_BOARD / 2 + 0.25
    cx, cz = AS5600_CHIP_OFS
    c = c.cut(cyl(3.5, (0, TRUN_OUT - 8, 0), (0, FLANGE_Y1 + 1, 0)))                       # wire hole
    c = c.cut(box(-b - cx, b - cx, BOARD_Y0, FLANGE_Y1 + 1, -b - cz, b - cz))             # board pocket
    px = AS5600_BOARD / 2 - AS5600_PAD_X - cx                                               # pad column x
    c = c.cut(box(-3.5, px + 2.2, TRUN_OUT + 0.4, FLANGE_Y1 + 1, -AS5600_PAD_PITCH - 1.8 - cz,
                  AS5600_PAD_PITCH + 1.8 - cz))                                             # wire channel: hole to pads
    return c.clean()


def sensor_carrier():
    return side_shape(_carrier(), SENSOR_SIDE)


def _cover_base():
    y0, y1 = BLOCK_Y1, BLOCK_Y1 + COVER_D
    return cyl(COVER_R, (0, y0, 0), (0, y1, 0))


def _cover_finish(c, inner_to):
    y0, y1 = BLOCK_Y1, BLOCK_Y1 + COVER_D
    c = c.cut(cyl(COVER_IN_R, (0, y0 - 1, 0), (0, inner_to, 0)))
    for a in (45, 135, 225, 315):                       # M3 x 20 countersunk from the outer face into the block
        px, pz = on_circle(COVER_HOLE_R, a)
        c = c.cut(csk_hole(3, (px, y1, pz), (0, -1, 0), COVER_D + 1))
    return c


def cover_cable():
    spout_y = BLOCK_Y1 + 7
    c = _cover_base().fuse(cyl(6.5, (20, spout_y, 0), (COVER_R + 10, spout_y, 0)))
    c = _cover_finish(c, BLOCK_Y1 + 9.5)
    c = c.cut(cyl(3.75, (0, spout_y, 0), (COVER_R + 12, spout_y, 0)))           # cable bore through spout
    c = c.cut(box(20, COVER_R + 12, spout_y - 2.5, spout_y + 2.5, -8, 0))       # slot underneath: the cable drops in sideways,
                                                                                 # so the USB-C plug never has to pass the bore
    return side_shape(c.clean(), USB_SIDE)


def cover_sensor():
    c = _cover_finish(_cover_base(), MAGNET_Y)
    c = c.cut(cyl(MAGNET_POCKET / 2, (0, MAGNET_Y - 1, 0), (0, MAGNET_Y + MAGNET_H + 0.1, 0)))   # diametric magnet pocket
    return side_shape(c.clean(), SENSOR_SIDE)


# ---------------------------------------------------------------- bought parts (for renders)
def bearing(side):
    s = side
    y0, y1 = s * BRG_Y0, s * BRG_Y1
    outer = tube(BRG_D / 2, BRG_OR_SH / 2, (0, y0, 0), (0, y1, 0))
    inner = tube(BRG_IR_SH / 2, BRG_d / 2, (0, y0, 0), (0, y1, 0))
    seal = tube(BRG_OR_SH / 2, BRG_IR_SH / 2, (0, y0 + s * 0.5, 0), (0, y1 - s * 0.5, 0))
    return outer, inner, seal


def alu_tube(length=160):
    return tube(TUBE_OD / 2, TUBE_ID / 2, (-SOCK_BOTTOM, SOCK_Y, 0), (-SOCK_BOTTOM - length, SOCK_Y, 0))


def hose_clamp():
    band = tube(SOCK_BOSS_R - 0.4, SOCK_BOSS_R - 1.2, (-55, SOCK_Y, 0), (-62, SOCK_Y, 0))
    housing = box(-61.5, -55.5, SOCK_Y - 6, SOCK_Y + 6, SOCK_BOSS_R + 0.2, SOCK_BOSS_R + 4)
    screw = cyl(2.4, (-58.5, SOCK_Y - 9, SOCK_BOSS_R + 2), (-58.5, SOCK_Y + 9, SOCK_BOSS_R + 2))
    return fuse(band, housing, screw)


def usb_path(x0=-190.0, y_end=None):
    """tube -> short bend at the bore intersection -> along the axis (+y) -> rear exit"""
    s45 = math.sin(math.radians(45))
    r = 5.0
    yk = BLOCK_Y1 + 1
    wp = (cq.Workplane("XY").moveTo(x0, SOCK_Y).lineTo(-r, SOCK_Y)
          .threePointArc((-r + r * s45, SOCK_Y + r - r * s45), (0, SOCK_Y + r)))
    if y_end is not None:
        return wp.lineTo(0, y_end).wire().val()
    return (wp.lineTo(0, yk).threePointArc((6 - 6 * s45, yk + 6 * s45), (6, yk + 6))
            .lineTo(80, yk + 6).wire().val())


def usb_cable():
    return sweep_circle(2.3, usb_path(), (-190, SOCK_Y, 0), (1, 0, 0))


def sensor_wires():
    """3-core lead (VCC, OUT, GND): under the board, through the carrier, along the axis, up the tube"""
    yc = -(TRUN_OUT + 2.3)
    pts = [V(11, yc, 0), V(0, yc, 0), V(0, -16, 0), V(0, -12, 4), V(-6, -10, 4), V(-190, -10, 4)]
    return sweep_circle(1.6, cq.Wire.makePolygon(pts), pts[0], (-1, 0, 0))


def sensor_board():
    h = AS5600_BOARD / 2
    cx, cz = AS5600_CHIP_OFS
    pcb = box(-h - cx, h - cx, BOARD_Y0, BOARD_Y0 + 1.6, -h - cz, h - cz)
    chip = box(-2.5, 2.5, BOARD_Y0 + 1.6, CHIP_Y1, -2.0, 2.0)
    px = h - cx - AS5600_PAD_X
    pins = fuse(*[cyl(0.5, (px, BOARD_Y0 - 3.5, (i - 1) * AS5600_PAD_PITCH - cz), (px, BOARD_Y0 + 1.0, (i - 1) * AS5600_PAD_PITCH - cz))
                  for i in range(3)])                                                     # the three soldered wires, leaving the back
    return side_shape(pcb.fuse(pins).clean(), SENSOR_SIDE), side_shape(chip, SENSOR_SIDE)


def magnet():
    return side_shape(cyl(MAGNET_D / 2, (0, MAGNET_Y, 0), (0, MAGNET_Y + MAGNET_H, 0)), SENSOR_SIDE)


def ballast(length=None):
    """fixed ballast against the far wall (stick-on wheel weights or shot set in epoxy), for renders and the
    balance estimate; loose shot would slide to the pivot end when the bucket tilts up at low collective"""
    W, T = BKT_W, BKT_T
    L = BALLAST_L if length is None else length
    u1 = BKT_U1 - T - 0.3
    b = box(u1 - L, u1, BKT_WIDE_Y0 + T + 0.3, BKT_Y1 - T - 0.3, -W + T + 0.3, W - 2.3)
    for u, y in BKT_LID_BOSSES:
        b = b.cut(cyl(3.8, (u, y, -W), (u, y, W)))
    return to_bucket(b.clean())


def lever_screws():
    """countersunk M4 x 20 + nuts joining the lever halves (reference)"""
    parts = []
    for x, y in LEVER_SCREWS:
        sink = LS_HEAD_R - 0.1 - 2.0
        parts += [cq.Solid.makeCone(2.0, LS_HEAD_R - 0.1, sink, V(x, y, LS_SEAT_Z - sink), V(0, 0, 1)),
                  cyl(2.0, (x, y, LS_SEAT_Z - 20), (x, y, LS_SEAT_Z - sink)),
                  hexprism(7.0, (x, y, -LS_NUT_Z - 3.2), (x, y, -LS_NUT_Z))]
    return fuse(*parts)


def knob_spring():
    p0, p1 = V(KNOB_X, KNOB_Y, 5.0 - SPRING_SEAT), V(KNOB_X, KNOB_Y, KNOB_Z0)
    helix = cq.Wire.makeHelix(1.6, (p1 - p0).Length, 4.6, p0, V(0, 0, 1))
    pl = cq.Plane(origin=helix.startPoint(), xDir=_perp(helix.tangentAt(0)), normal=helix.tangentAt(0))
    return cq.Workplane(pl).circle(0.55).sweep(cq.Workplane().add(helix), isFrenet=True).val()


def stop_bolt(theta=STOP_SET):
    """M5 x 16 hex bolt: head pressed into the thumb knob, through the quadrant slot into the nut in the stop block"""
    seat = QUAD_Y1 + 7 - M5_HEAD_DEPTH                                                    # under-head face
    b = fuse(cyl(2.5, (STRIKER_R, seat - 16, 0), (STRIKER_R, seat, 0)),
             hexprism(8.0, (STRIKER_R, seat, 0), (STRIKER_R, seat + 3.5, 0)))
    return rot_y(b, -stop_angle(theta))


def hardware(include_stop_bolt=True):
    parts = [cyl(3, (KNOB_X, KNOB_Y, 14), (KNOB_X, KNOB_Y, -16)),                       # M6 friction bolt
             hexprism(10, (KNOB_X, KNOB_Y, -15.8), (KNOB_X, KNOB_Y, -10.8)),            # M6 nut
             cyl(2, (HINGE_X, 10.5, HINGE_Z), (HINGE_X, 33.5, HINGE_Z)),                 # M4 hinge pin
             cyl(3.6, (HINGE_X, 9, HINGE_Z), (HINGE_X, 12, HINGE_Z)),
             cyl(2, (-50, SOCK_Y, -26), (-50, SOCK_Y, -18.6)),                           # down-stop screw
             hexprism(7, (-50, SOCK_Y, -26), (-50, SOCK_Y, -23.2))]
    for s in (-1, 1):
        yb = s * (BRG_Y0 + BLOCK_Y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            parts.append(cyl(3.5, (x, yb, 8), (x, yb, 12)))
    if include_stop_bolt:
        parts.append(stop_bolt())
    return fuse(*parts)


# ---------------------------------------------------------------- fit-test coupons
# python mk3_pivot.py --coupons -> stl/coupons/. Short slices of the real fits, one plate per fit, one variant
# per step. A step changes the fitted diameter (nut pocket: across flats) by that many mm; see README.md.
COUPON_STEPS = (-0.2, 0.0, 0.2)
COUPON_BASE_T, COUPON_SPINE_W = 2.0, 9.0     # spine tying the variants together, step labels engraved in it
COUPON_FONT = 4.5


def step_label(d):
    return "0" if abs(d) < 1e-9 else f"{d:+.2f}".rstrip("0").rstrip(".")


def label(text, x, y, z_top, size=COUPON_FONT):
    """0.6 mm engraving cutter on a top face, reads from the front (-y)"""
    pl = cq.Plane(origin=(x, y, z_top), xDir=(1, 0, 0), normal=(0, 0, 1))
    return cq.Workplane(pl).text(text, size, -0.6, combine=False, halign="center", valign="center").val()


def coupon_plate(variant, pitch=None, gap=4.0):
    """one variant(d) per step along +X, tied by a spine along their front edge with each step engraved in it.
    variant(d) is built centred on x = 0, standing on z = 0, front toward -y."""
    bb = variant(COUPON_STEPS[0]).BoundingBox()
    hw, y0, w = bb.xlen / 2, bb.ymin, COUPON_SPINE_W
    pitch = pitch or bb.xlen + gap
    n = len(COUPON_STEPS)
    spine = (cq.Workplane("XY").box((n - 1) * pitch + 2 * hw, w + 2, COUPON_BASE_T, centered=False)
             .translate((-hw, y0 - w, 0)).edges("|Z").fillet(2).val())
    p = fuse(spine, *[variant(d).translate((i * pitch, 0, 0)) for i, d in enumerate(COUPON_STEPS)])
    for i, d in enumerate(COUPON_STEPS):
        p = p.cut(label(step_label(d), i * pitch, y0 - w / 2, COUPON_BASE_T))
    return p.clean()


def half_pair(full, length, wall, gap=3.0):
    """a part built along +y from y = 0, split at z = 0 like the lever, as two halves standing on their y = 0 end
    (axis vertical, so the round faces build up layer by layer with no overhangs), split faces towards each other
    across a gap, joined by a thin snap-off tab at the base so the pair keeps its step label. wall = (r_in, r_out)
    of the material at the base, where the tab goes."""
    up = full.intersect(box(-100, 100, -1, length + 1, 0, 100))
    lo = full.intersect(box(-100, 100, -1, length + 1, -100, 0)).mirror("XY")
    stand = lambda h: h.rotate((0, 0, 0), (1, 0, 0), 90)                  # (x, y, z) -> (x, -z, y): split face at y = 0
    a = stand(up)                                                         # occupies y <= 0
    b = stand(lo).mirror("XZ").translate((0, gap, 0))                     # occupies y >= gap, split face towards a
    r0, r1 = wall
    tab = box(r0 + 0.6, r1 - 0.6, -0.5, gap + 0.5, 0, 0.8)
    return fuse(a, b, tab)


def coupon_trunnion(d, h=8.0, sh=2.0):
    """trunnion stub with its inner-race shoulder and the lever's 1/2" bore, as one ring standing on the shoulder
    (the stub's wall is the lever's, so it gives like the lever's). Push the 6006 on from the top"""
    c = fuse(cyl(BRG_IR_SH / 2 - 1.1, (0, 0, 0), (0, 0, sh)), cyl((TRUN_OD + d) / 2, (0, 0, sh), (0, 0, sh + h)))
    return c.cut(cyl(CABLE_R, (0, 0, -1), (0, 0, sh + h + 1)))


def coupon_seat(d, depth=7.0, lip=2.0, wall=4.0):
    """pillow-block bearing seat and retaining lip as a ring, lip down; the 6006 presses in from the top"""
    c = cyl(BRG_SEAT_D / 2 + wall, (0, 0, 0), (0, 0, lip + depth))
    c = c.cut(cyl((BRG_SEAT_D + d) / 2, (0, 0, lip), (0, 0, lip + depth + 1)))
    return c.cut(cyl(LIP_R, (0, 0, -1), (0, 0, lip + 1)))


def coupon_socket(d, length=20.0, wall=3.0):
    """plain inner end of the tube socket as one closed ring standing on its end (the tube slides in from the top)"""
    c = cyl(SOCK_BORE_R + wall, (0, 0, 0), (0, 0, length))
    return c.cut(cyl(SOCK_BORE_R + d / 2, (0, 0, -1), (0, 0, length + 1)))


def coupon_slot(d, length=10.0, hw=8.0):
    """piece of the quadrant lying on its inner face, with a short length of the arc slot running along y"""
    half = math.degrees(length / 2 / STRIKER_R)
    L = length / 2 + M5_CLR_R + 4
    q = box(STRIKER_R - hw, STRIKER_R + hw, QUAD_Y0, QUAD_Y1, -L, L).cut(arc_slot(-half, half, M5_CLR_R + d / 2))
    return q.rotate((0, 0, 0), (1, 0, 0), 90).translate((-STRIKER_R, 0, -QUAD_Y0))


def coupon_stop_block(d, tab=9.0):
    """stop block on its clamp face, nut pocket up, plus a label tab (coupon only) so loose blocks stay identified"""
    h = STOP_BLOCK / 2
    b = _stop_block(M5_CLR_R + d / 2, M5_NUT_AF + d).rotate((0, 0, 0), (1, 0, 0), -90)
    b = fuse(b.translate((-STRIKER_R, 0, QUAD_Y0)), box(-h, h, h - 1, h + tab, 0, 2))
    return b.cut(label(step_label(d), 0, h + tab / 2, 2, size=4.0)).clean()


def coupons():
    return {                    # Rev 1's stop-slot coupon is left out: Rev 3 has no quadrant
        "coupon_trunnion": coupon_plate(coupon_trunnion),
        "coupon_bearing_seat": coupon_plate(coupon_seat),
        "coupon_tube_socket": coupon_plate(coupon_socket),
    }


def export_coupons():
    out = os.path.join(HERE, "stl", "coupons")
    os.makedirs(out, exist_ok=True)
    for name, shp in coupons().items():
        solids = shp.Solids()
        valid = shp.isValid() and all(s.isValid() for s in solids)
        bb = shp.BoundingBox()
        print(f"{name:20s} solids={len(solids)} valid={valid} vol={shp.Volume():8.1f}"
              f" size={bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}")
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(out, f"{name}.stl"),
                            tolerance=0.04, angularTolerance=0.12)


# ---------------------------------------------------------------- build + export
def build():
    outer_l, inner_l, seal_l = bearing(-1)
    outer_r, inner_r, seal_r = bearing(1)
    pcb, chip = sensor_board()
    lever_up, lever_lo = lever_halves()
    return {
        # printed
        "frame": frame_solid(),
        "cap_left": cap(-1),
        "cap_right": cap(1),
        "lever_upper": lever_up,
        "lever_lower": lever_lo,
        "ballast_bucket": bucket(),
        "bucket_lid": bucket_lid(),
        "shoe": shoe(),
        "stop_block": stop_block(),
        "stop_thumb_knob": thumb_knob(),
        "sensor_carrier": sensor_carrier(),
        "cover_sensor": cover_sensor(),
        "cover_cable": cover_cable(),
        # bought / reference
        "felt": felt(),
        "bearing_outer": fuse(outer_l, outer_r),
        "bearing_inner": fuse(inner_l, inner_r),
        "bearing_seal": fuse(seal_l, seal_r),
        "alu_tube": alu_tube(),
        "hose_clamp": hose_clamp(),
        "usb_cable": usb_cable(),
        "sensor_wires": sensor_wires(),
        "sensor_pcb": pcb,
        "sensor_chip": chip,
        "magnet": magnet(),
        "striker": striker(),
        "ballast": ballast(),
        "knob_spring": knob_spring(),
        "hardware": hardware(),
        "lever_screws": lever_screws(),
    }


PRINTED = ["frame", "cap_left", "cap_right", "lever_upper", "lever_lower", "ballast_bucket", "bucket_lid", "shoe", "stop_block",
           "stop_thumb_knob", "sensor_carrier", "cover_sensor", "cover_cable"]

if __name__ == "__main__":      # the base's own STLs and STEP come from mk3_rev3.py, which shares this folder
    export_coupons()
