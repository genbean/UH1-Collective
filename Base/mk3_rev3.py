"""
MkIII collective base, Rev 3 - GAS STRUT BALANCE (CONCEPT, not print-tested)

Rev 3 = Rev 1 with a gas strut, centred under the tube and the hub, doing the ballast bucket's job, a fixed 32 deg
up-stop, and a 470 mm carbon tube. This script imports Rev 1's model, mk3_pivot.py in this folder, for every part
they share and for the fit parameters you tune with its coupons (python mk3_pivot.py), and writes everything to
this folder:
    python mk3_rev3.py           -> stl/ (all printed parts), stl/ref/ and step/MkIII_Rev3_assembly.step
    python mk3_rev3.py --curve   -> prints the balance table and writes renders/strut_balance.png

Tube: 25 x 23 mm carbon fibre, used whole, 500 mm, uncut: 470 + the head boss's 12.7 + 17.3 down in the socket (it ends at x = -2.7, inside the axial cable bore; notch its sides there for the cables). No lock screw: the hose clamp holds it. The grip's top sits 445 mm from the pivot, and at the
32 deg stop the hand rises about 9.4 in, the real UH-1's 9.25 in.

Strut: X AUTOHAUX 6" 10 lb / 45 N gas spring (Amazon B0CY267GFY, 2 for $13.69), 152.4 mm eye to eye extended,
101.6 mm compressed, sold as 40-53 N, with flat eyelet tabs on both ends (4 mm holes, per the listing). The steel
rod-end tab sits in a fixed clevis printed into the frame, 12 mm ahead of and 40.5 mm below the pivot, gusseted fore
and aft, on an M4 x 16 countersunk screw.
The plastic body-end tab sits in a clevis on a collar clamped to the tube 130 mm out, 32 mm below the tube axis. At the
down-stop the strut lies almost flat under the socket boss. As the tube lifts, its line swings up toward the pivot, so
the leverage falls the way the head's weight does. Sized so a 40 N strut (the bottom of the range) balances within a
few grams at the grip; a stronger one lifts a little too much and you add ballast to the head (about 50 g for 45 N).
Sliding the collar trims +/-20 g.

Lever changes from Rev 1: the hub is the friction drum's 60 mm all the way across; no bucket pad (nothing bolts there
now) and no bottom gusset (the strut runs there); two flat down-stop pads on the socket boss; and an up-stop boss on
the back of the hub's underside. At 32 deg that boss lands flat on a pedestal on the frame between the pillow
blocks. Rev 1's quadrant, stop block, thumb knob and striker are gone.
Down-stop: two M4 screws, head up, in posts either side of the strut stop the pads on the socket boss.
Pivot 58 mm above the desk (Rev 1: 40): the strut's line has to pass about 40 mm below the pivot to clear the hub, and
the clevis around its eye needs the rest.

Bought parts that Rev 1 doesn't have (no bucket, lid, ballast, stop block, thumb knob, M5 stop bolt or striker):
    1 x X AUTOHAUX 6" 45 N gas strut (the pack has 2);  25 x 23 mm carbon tube, 500 mm uncut

Screws and nuts: all from the two kits (mk3_pivot.py, Fasteners). Countersunk (AvrestYPT kit) unless marked:
    lever halves      4 x M4 x 40 socket head cap (HELIFOUNER M4 x 30-50 kit) + 4 M4 nuts in the lower half's pockets
    pillow-block caps 4 x M4 x 20 + 4 M4 nuts, slid in fore and aft from the blocks' front and back faces
    side covers       8 x M3 x 25 (the NIULUNBAO M3 set) from the covers' outer faces, into M3 threads tapped 11 mm deep
                      in the blocks and caps
    friction knob     1 x M5 x 25 hex-head bolt (bought: the kits have no hex heads), its head in the knob's moulded hex
                      pocket, + 1 M5 nut slid into the knob tower
    cable plug        1 x M2 x 12 up from under the cable cover's rim, into an M2 thread tapped in the plug
    shoe hinge        1 x M4 x 20 + 1 M4 nut in the +y lug's pocket
    strut eyes        2 x M4 x 16 + 2 M4 nuts in pockets
    strut collar      1 x M4 x 12 + 1 M4 nut (clamp)
    down-stops        2 x M4 x 16, head up, each in an M4 nut pressed into its post, + 1 M4 lock nut each
"""
import os
import sys
import math
import cadquery as cq
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Cone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk3_pivot as m                                                                     # Rev 1
from mk3_pivot import V, cyl, tube, box, fuse, hexprism, rot_y, xz_plane

# ---------------------------------------------------------------- Rev 3 changes to Rev 1's parameters
m.PLATE_T = 8.0                                  # base plate: at least 5/16 in (7.94 mm) for strength (Rev 1: 6), grown downward
m.AXIS_H = AXIS_H = 58.0                         # pivot height above the underside of the plate (Rev 1: 40), so the top stays at -50
m.Z_PLATE = Z_PLATE = -AXIS_H + m.PLATE_T        # top of plate (-50)
HUB_R = m.DRUM_R                                 # the hub is the friction drum's diameter all the way across (Rev 1: 28)
# pillow blocks and caps 2.5 mm wider each side (Rev 1: 35), so the cap screws' M4 countersunk heads (8.6 mm) sit
# inside the cap's curve and clear of the bearing seat, and the nuts slide in fore and aft well inside the blocks
m.BLOCK_HW = 37.5
m.CAP_BOLT_X = 31.3                              # head 0.64 mm clear of the bearing seat, 1.0 mm inside the cap's curve
# tube socket deeper (Rev 1: bottom at x = -20, 46 mm of engagement; now x = -2.7, 63.3 mm), into the axial cable bore.
# The tube is that much longer, so the head stays exactly where it was.
# side covers: the M3 holes move out to r 31.5 (Rev 1: 30), where the wall to the bearing seat is 2.7 mm rather than 1.2, so
# they can be tapped 11 mm deep (Rev 1: 7) for M3 x 25 screws: 10 mm of thread in the plastic instead of 5, three times the
# pull-out. The covers grow to r 36.5 (Rev 1: 34) to keep 1.5 mm of rim round the countersinks.
m.COVER_HOLE_R, m.COVER_R, m.COVER_TAP_DEPTH = 31.5, 36.5, 11.0
COVER_SCREW_L = 25
# 2026-10-25: the socket now takes the whole 500 mm tube, uncut. 470 + the head boss's 12.7 + TUBE_EXTRA = 500, so the socket
# bottoms out at x = -2.7, inside the axial cable bore (it was 12.0 for a 491 mm cut). The user notches the tube's sides
# where the axial bore crosses its wall, so the cables can get in.
TUBE_BOUGHT = 500.0
TUBE_EXTRA = TUBE_BOUGHT - 470.0 - 12.7
m.SOCK_BOTTOM = 20.0 - TUBE_EXTRA
# the four lever screws: a rectangle centred on the socket's axis (y = -9), 16.75 mm either side, and on the pivot axis (x = 0),
# 17 mm fore and aft. That clears the deeper socket by 1.85 mm at the joint (Rev 1's were 8.5 / -25 and 8.5 / -11, at x = -17 / 14)
m.LEVER_SCREWS = [(x, m.SOCK_Y + dy) for x in (-17.0, 17.0) for dy in (-16.75, 16.75)]

# ---------------------------------------------------------------- parameters
# tube: 25 x 23 mm carbon fibre, 470 mm from Rev 1's socket bottom to the head's reference end (it's cut TUBE_EXTRA longer)
TUBE_L = 470.0
TUBE_G_PER_MM = 0.121                            # carbon ~1.6 g/cm3 (25 x 1 aluminium: 0.204)
HEAD_G, HEAD_GM = 368.0, 133.97                  # HueyHead_Rev2 + grip + friction collar on Rev 1's 357.7 mm tube: g, g*m
HEAD_TUBE0 = 357.7
GRIP_R = 275.0 + TUBE_L - HEAD_TUBE0             # grip centre from the pivot, mm
BOX_R = 386.7 + TUBE_L - HEAD_TUBE0              # head body's centre of mass: where ballast goes


def forward_gm():
    """head, grip, tube, cables, hose clamp, lock screw: g*m about the pivot at 0 deg"""
    mid = 20.0 + TUBE_L / 2                      # the tube from Rev 1's socket bottom (x = -20) out to the head
    deeper = TUBE_G_PER_MM * TUBE_EXTRA * (m.SOCK_BOTTOM + TUBE_EXTRA / 2)       # the extra length down in the socket
    return (HEAD_GM * 1000 + HEAD_G * (TUBE_L - HEAD_TUBE0) + TUBE_G_PER_MM * TUBE_L * mid + deeper
            + 13.0 * TUBE_L / HEAD_TUBE0 * mid + 9 * 58.5 + 1.5 * 50.5) / 1000


FWD_GM = forward_gm()

# gas strut: X AUTOHAUX 6" 10 lb / 45 N (Amazon B0CY267GFY); measure yours, the tabs especially
STRUT_EXT, STRUT_COMP = 152.4, 101.6             # eye to eye, extended / compressed
STRUT_F = 45.0                                   # N, nominal
STRUT_F_RANGE = (40.0, 53.0)                     # as sold ("9-12 lb")
STRUT_F_DESIGN = 40.0                            # the geometry balances this; a stronger strut gets head ballast
STRUT_PROG = 1.3                                 # force rise from extended to compressed (assumed; not in the listing)
STRUT_BODY_D, STRUT_ROD_D, STRUT_BODY_L = 12.1, 4.0, 70.0   # diameters from the listing
TAB_L = 12.0                                     # eye centre to where the tab meets the rod or body
ROD_TAB_T, ROD_TAB_W = 3.0, 10.0                 # steel tab on the rod end (anchor)
# collar end of the 40 N strut, measured: a steel tab with a 4.45 mm eye, then a Ø8 mm boss whose face is 5.72 mm from the eye's
# centre and which runs about 6.9 mm (photo). The boss is wider than the tab is thick, so it cannot go into the collar's slot.
BODY_TAB_T, BODY_TAB_W = 3.94, 8.0
BODY_BOSS_D, BODY_BOSS_AT, BODY_BOSS_L = 8.0, 5.72, 6.9
BODY_TAB_L = BODY_BOSS_AT + BODY_BOSS_L          # eye centre to where the boss meets the body
BOSS_CLR = 0.5                                   # the collar's relief round the boss
PIN_R = 2.2                                      # M4 screws through both eyes (the listing gives 4 mm holes)
STRUT_G = 65.0                                   # strut mass, g (estimate)

# where the strut's eyes sit (lever frame for the collar: d along the tube, e below its axis)
ANCH_X, ANCH_Z = -12.0, -40.5                    # fixed anchor eye
COLLAR_D, COLLAR_E = 128.0, 26.0                 # collar eye, as set for a 40 N strut (E: close under the tube, to spare the plastic a long lever)
COLLAR_RANGE = (-8.0, 8.0)                       # collar slide inside the strut's stroke
Y0 = m.SOCK_Y                                    # the strut's plane = the tube's

# fixed clevis at the anchor, printed into the frame
CLEVIS_T, CLEVIS_R = 6.0, 8.0                    # cheek thickness, radius round the eye
CLEVIS_RUN = 20.0                                # front gussets reach this far forward of the eye, down to the plate
ROD_CLEAR = 1.0                                  # front gussets stop this far short of the strut's rod (both sides)

# collar on the tube
COLLAR_W, COLLAR_WALL = 40.0, 5.0
COLLAR_BACK = 30.0                               # the collar runs this far past the eye away from the strut (the strut's push), 10 mm toward it
COLLAR_BORE = m.TUBE_OD / 2 + 0.15
CHEEK_T = 5.0                                    # (the tab is thinner now; the cheeks make up the width, so the M4 x 16 still ends at its nut)

# down-stop: pads on the socket boss, posts either side of the strut
PAD_X = (-52.0, -40.0)                           # clear of the hose-clamp groove (x -54..-63)
PAD_DY = (13.5, 20.0)                            # |y - SOCK_Y|: clear of the 25.4 mm tube bore
PAD_Z = -16.0                                    # pad underside at 0 deg
STOP_X = sum(PAD_X) / 2
POST_TOP = PAD_Z - 8.0                           # an M4 nut sits in a pocket in each post's top, a lock nut on it
CAP_NUT_Z = -8.3                                 # pillow-block cap screws: the nut's top face (the M4 x 20 ends at -12)
m.FN_NUT_Z = CAP_NUT_Z                           # the friction knob's M5 nut sits as deep, so its slot's roof is thick (Rev 1: -3.2)
m.KNOB_BOLT = (25.0, 3.5)                        # ... which takes an M5 x 25 hex bolt (it ended at -7.0 as an M5 x 16): tip at -16

# up-stop: boss on the back of the hub's underside, landing flat on a frame pedestal at STOP_DEG
STOP_DEG = 32.0
USTOP_X = (12.0, HUB_R)                          # contact face, world x at the stop; the back face is tangent to the hub
USTOP_Z = -36.0                                  # pedestal top (world z)
USTOP_Y = (-m.HUB_HW, m.DRUM_Y0 - 1.0)           # hub's sensor end to 1 mm short of the friction drum (shoe, felt, hinge lugs)
PED_X = (USTOP_X[0] - 2.0, USTOP_X[1] + 2.0)     # pedestal: 2 mm past the boss's faces
PED_Y = (-m.BRG_Y0 - 1.0, USTOP_Y[1] + 2.0)      # pedestal: into the sensor-side pillow block, 2 mm past the boss's other end

# corner gusset, hinge lugs to the knob-side pillow block (plan view, 45 deg): stops 6.5 mm short of the desk screw at
# (PLATE_X1 - 8, PLATE_HW - 8), room for its head
LUG_GUSSET = 78.8                                # its sloping face is x + y = LUG_GUSSET


def collar_pin(theta=0.0, d=COLLAR_D, e=COLLAR_E):
    """world (x, z) of the collar eye at lever angle theta"""
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return -d * c - e * s, d * s - e * c


def gusset_xz(pts, y0, y1):
    """prism of an XZ-plane polygon between y0 and y1"""
    return cq.Workplane(xz_plane(y1)).polyline(pts).close().extrude(y1 - y0).val()


# ---------------------------------------------------------------- lever
def stop_pads():
    """flat pads on each side of the socket boss for the down-stop screws"""
    return [box(PAD_X[0], PAD_X[1], *sorted((Y0 + s * PAD_DY[0], Y0 + s * PAD_DY[1])), PAD_Z, 0) for s in (-1, 1)]


def up_stop_boss():
    """block on the back of the hub's underside, drawn as it sits at the stop: its face on the pedestal, its back face
    running straight up to the hub and tangent to it (USTOP_X[1] is the hub radius), its inner corners inside the hub.
    Turned back to 0 deg, the split plane cuts it: the lower half carries the stop face, and the upper half a wedge
    that fills the corner up to the tangent. At the stop the lower part is pushed up into the upper part."""
    x0, x1 = USTOP_X
    split = -math.tan(math.radians(STOP_DEG))                                   # the split plane, seen at the stop
    pts = [(x0, USTOP_Z), (x1, USTOP_Z), (x1, 0.0), (x1 - 8.0, 0.0), (20.0, split * 20.0), (x0, -22.0)]
    return rot_y(gusset_xz(pts, *USTOP_Y), -STOP_DEG)


def lever_r3():
    """Rev 1's lever() for Rev 3: hub at the drum's diameter, no bucket pad or its inserts, no bottom gusset, plus the
    down-stop pads and the up-stop boss. The bores are cut last, so nothing added reaches into them."""
    core = rot_y(cyl(HUB_R, (0, -m.HUB_HW, 0), (0, m.HUB_HW, 0)), 135)       # seam away from the split and the stop boss
    boss = cyl(m.SOCK_BOSS_R, (-10, Y0, 0), (-m.SOCK_MOUTH, Y0, 0))
    shoulders = [cyl(m.BRG_IR_SH / 2 - 1.1, (0, s * m.HUB_HW, 0), (0, s * m.BRG_Y0, 0)) for s in (-1, 1)]
    trunnions = [cyl(m.TRUN_OD / 2, (0, s * m.BRG_Y0, 0), (0, s * m.TRUN_OUT, 0)) for s in (-1, 1)]
    gusset = gusset_xz(m.GUSSET_TOP, Y0 - m.GUSSET_T / 2, Y0 + m.GUSSET_T / 2)
    h = fuse(core, boss, gusset, *shoulders, *trunnions, *stop_pads(), up_stop_boss())
    cuts = [cyl(m.SOCK_BORE_R, (-m.SOCK_BOTTOM, Y0, 0), (-m.SOCK_MOUTH - 1, Y0, 0)),                # tube socket
            tube(m.SOCK_BOSS_R + 1, m.SOCK_BOSS_R - 1.2, (-54, Y0, 0), (-63, Y0, 0)),                # hose-clamp groove
            cyl(m.CABLE_R, (0, -m.TRUN_OUT - 1, 0), (0, m.TRUN_OUT + 1, 0)),                         # axial 1/2" bore
            cyl(m.CABLE_R, (-m.SOCK_BOTTOM - 1, Y0, 0), (3, Y0, 0))]                                 # radial 1/2" bore
    for c in cuts:
        h = h.cut(c)
    return h.clean()


m.lever = lever_r3                               # Rev 1's lever_halves() and build() now split this one


# ---------------------------------------------------------------- frame: Rev 1's on the taller pivot, new stops and anchor
def frame_r3():
    """Rev 1's frame_solid() with the pivot 58 mm up, no quadrant or the plate tongue under it, no centre down-stop post, plus the anchor clevis,
    two down-stop posts beside the strut and the up-stop pedestal"""
    plate = (cq.Workplane("XY").box(m.PLATE_X1 - m.PLATE_X0, 2 * m.PLATE_HW, m.PLATE_T, centered=False)
             .translate((m.PLATE_X0, -m.PLATE_HW, -AXIS_H)).edges("|Z").fillet(6).val())
    blocks = [box(-m.BLOCK_HW, m.BLOCK_HW, *sorted((s * m.BRG_Y0, s * m.BLOCK_Y1)), Z_PLATE, 0) for s in (-1, 1)]
    tower = box(-54, -36, m.SHOE_Y0, m.SHOE_Y1, Z_PLATE, -1)
    lugs = [box(40, 51, 12, 16.5, Z_PLATE, 2), box(40, 51, 27.5, 32, Z_PLATE, 2)]
    lug_round = [cyl(5.5, (m.HINGE_X, y0, m.HINGE_Z), (m.HINGE_X, y1, m.HINGE_Z)) for y0, y1 in ((12, 16.5), (27.5, 32))]
    lug_web = box(40, 51, 12, 32, Z_PLATE, -14)
    tower_web = (cq.Workplane("XY").workplane(offset=Z_PLATE - 0.1)
                 .polyline([(-54, 30.5), (-34.5, 30.5), (-34.5, 48)]).close().extrude(-2 - Z_PLATE + 0.1).val())
    stop_posts = [cyl(5.5, (STOP_X, Y0 + s * sum(PAD_DY) / 2, Z_PLATE), (STOP_X, Y0 + s * sum(PAD_DY) / 2, POST_TOP)) for s in (-1, 1)]
    lug_gusset = (cq.Workplane("XY").workplane(offset=Z_PLATE - 0.1)       # corner gusset: hinge lugs to +y pillow block,
                  .polyline([(m.BLOCK_HW - 0.5, 31.5), (LUG_GUSSET - 31.5, 31.5), (m.BLOCK_HW - 0.5, LUG_GUSSET - m.BLOCK_HW + 0.5)])
                  .close().extrude(-14 - Z_PLATE + 0.1).val())                # level with the lug web, under the hinge pin's end
    pedestal = box(*PED_X, *PED_Y, Z_PLATE - 0.1, USTOP_Z)
    f = fuse(plate, *blocks, tower, *lugs, *lug_round, lug_web, tower_web, lug_gusset, *stop_posts, pedestal,
             anchor_clevis())

    cuts = []
    a4, t4 = m.NUT_AF[4], m.NUT_T[4]
    for s in (-1, 1):
        cuts += m.block_cuts(s)
        yb = s * (m.BRG_Y0 + m.BLOCK_Y1) / 2
        for x in (-m.CAP_BOLT_X, m.CAP_BOLT_X):
            # cap screw into an M4 nut slid in fore and aft, from the block's front or back face: flats facing +-y, so
            # the slot is only the nut's width across flats and stays inside the block (4.9 mm each side), under 3.1 mm
            # of block and over the rest. Out at x = +-60: through the face, or through the tower's gusset where it
            # covers the knob-side block's face (the slot then opens on the gusset's sloping face)
            zn = CAP_NUT_Z - t4 - 0.2
            cuts += [cyl(2.2, (x, yb, -13), (x, yb, 1)),
                     hexprism(a4, (x, yb, zn), (x, yb, CAP_NUT_Z)),
                     box(*sorted((x, math.copysign(60.0, x))), yb - a4 / 2, yb + a4 / 2, zn, CAP_NUT_Z)]
        y = Y0 + s * sum(PAD_DY) / 2
        cuts += [hexprism(a4, (STOP_X, y, POST_TOP - t4 - 0.2), (STOP_X, y, POST_TOP + 1)),     # down-stop nut pocket
                 cyl(2.2, (STOP_X, y, POST_TOP - 10), (STOP_X, y, POST_TOP))]
    aw = (ROD_TAB_T + 0.6) / 2 + CLEVIS_T                                                      # anchor's outer faces, +-y
    cuts += [cyl(m.CSK[5][1] / 2, (m.KNOB_X, m.KNOB_Y, 0),
                 (m.KNOB_X, m.KNOB_Y, m.KNOB_HEAD_Z - m.KNOB_BOLT[1] - m.KNOB_BOLT[0] - 1.0)),     # M5 friction bolt, 1 mm past its tip
             box(-55, m.KNOB_X + 4.8, m.KNOB_Y - m.NUT_AF[5] / 2, m.KNOB_Y + m.NUT_AF[5] / 2,
                 m.FN_NUT_Z - m.NUT_T[5] - 0.4, m.FN_NUT_Z),                                     # its nut, in from the front
             cyl(2.2, (m.HINGE_X, 10, m.HINGE_Z), (m.HINGE_X, 34, m.HINGE_Z)),                  # shoe hinge: M4 x 20,
             m.csk_hole(4, (m.HINGE_X, 12, m.HINGE_Z), (0, 1, 0), 1),                           # head in the -y lug,
             hexprism(a4, (m.HINGE_X, 32 - t4 - 0.2, m.HINGE_Z), (m.HINGE_X, 33, m.HINGE_Z)),   # nut in the +y lug
             cyl(PIN_R, (ANCH_X, Y0 - 12, ANCH_Z), (ANCH_X, Y0 + 12, ANCH_Z)),                  # anchor: M4 x 16,
             m.csk_hole(4, (ANCH_X, Y0 + aw, ANCH_Z), (0, -1, 0), 1),                           # head on +y,
             hexprism(a4, (ANCH_X, Y0 - aw + t4 + 0.2, ANCH_Z), (ANCH_X, Y0 - aw - 1, ANCH_Z))]  # nut on -y
    for x in (m.PLATE_X0 + 8, m.PLATE_X1 - 8):
        for y in (-m.PLATE_HW + 8, m.PLATE_HW - 8):
            cuts.append(cyl(2.75, (x, y, -AXIS_H - 1), (x, y, 0)))                               # desk mounting
    for c in cuts:
        f = f.cut(c)
    return f.clean()


def anchor_clevis():
    """two cheeks round the strut's steel rod-end tab, printed into the plate. Each cheek is a round boss over the eye on a
    block down to the plate, with a gusset running 20 mm forward down to the plate and a wall running straight back into
    the stop pedestal, its top from the boss's top to the pedestal's front edge. The front gussets stop 1 mm short of
    the strut's rod, so it swings up between them; a web ties the cheeks together behind the tab."""
    g = ROD_TAB_T + 0.6
    zt = ANCH_Z + CLEVIS_R
    zb = Z_PLATE - 0.1
    parts = [box(ANCH_X + ROD_TAB_W / 2 + 1.0, ANCH_X + CLEVIS_R, Y0 - g / 2 - 0.1, Y0 + g / 2 + 0.1, zb, ANCH_Z)]
    for s in (-1, 1):
        y0, y1 = sorted((Y0 + s * g / 2, Y0 + s * (g / 2 + CLEVIS_T)))
        f0, f1 = sorted((Y0 + s * (STRUT_ROD_D / 2 + ROD_CLEAR), Y0 + s * (g / 2 + CLEVIS_T)))
        parts += [cyl(CLEVIS_R, (ANCH_X, y0, ANCH_Z), (ANCH_X, y1, ANCH_Z)),
                  box(ANCH_X - CLEVIS_R, ANCH_X + CLEVIS_R, y0, y1, zb, ANCH_Z),
                  gusset_xz([(ANCH_X, zt), (PED_X[0], USTOP_Z), (PED_X[0] + 1, USTOP_Z - 0.5), (PED_X[0] + 1, zb),
                             (ANCH_X, zb)], y0, y1),                                                         # aft, into the pedestal
                  gusset_xz([(ANCH_X, zt), (ANCH_X - CLEVIS_RUN, zb), (ANCH_X, zb)], f0, f1)]                # fore
    return fuse(*parts)


# ---------------------------------------------------------------- tube collar
def _hull(pts):
    """convex hull (monotone chain) of 2D points"""
    pts = sorted(set(pts))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    half = []
    for seq in (pts, pts[::-1]):
        h = []
        for p in seq:
            while len(h) >= 2 and cross(h[-2], h[-1], p) <= 0:
                h.pop()
            h.append(p)
        half += h[:-1]
    return half


def _collar(d=COLLAR_D):
    """split clamp collar in the lever frame (tube along -X at z = 0): slit and M4 clamp on top, clevis below.
    The ring is COLLAR_W long and the eye hangs off its strut end: a web tapers from the ring's whole length down to the eye,
    solid behind the eye where the strut pushes and split into two cheeks round the strut's tab.
    Prints standing on its -x end, so the bore and the cheeks build straight up and the web's slope is under 30 deg."""
    x0, x1 = -d - COLLAR_BACK, -d + COLLAR_W - COLLAR_BACK
    xc = (x0 + x1) / 2                                                                           # the clamp screw: mid-ring
    ro = COLLAR_BORE + COLLAR_WALL
    ring = cyl(ro, (x0, Y0, 0), (x1, Y0, 0))
    ears = box(x0, x1, Y0 - 7, Y0 + 7, ro - 3, ro + 8)
    gap = BODY_TAB_T + 0.6
    cw = gap / 2 + CHEEK_T
    re = BODY_TAB_W / 2 + 3.5                                                                    # the eye's radius round the pin
    hull = _hull([(x0, -ro + 2), (x1, -ro + 2)] + [(-d + re * math.cos(a * math.pi / 18), -COLLAR_E + re * math.sin(a * math.pi / 18))
                                                    for a in range(36)])
    web = gusset_xz(hull, Y0 - cw, Y0 + cw)
    c = fuse(ring, ears, web)
    c = c.cut(cyl(COLLAR_BORE, (x0 - 1, Y0, 0), (x1 + 1, Y0, 0)))
    c = c.cut(box(x0 - 1, x1 + 1, Y0 - 1.0, Y0 + 1.0, 0, ro + 9))                                # clamp slit
    c = c.cut(cyl(2.2, (xc, Y0 - 8, ro + 3), (xc, Y0 + 8, ro + 3)))                              # M4 x 12 clamp screw,
    c = c.cut(m.csk_hole(4, (xc, Y0 - 5, ro + 3), (0, 1, 0), 1, out=3))                          # its head 2 mm in on -y
    c = c.cut(hexprism(7.2, (xc, Y0 + 3.8, ro + 3), (xc, Y0 + 8, ro + 3)))                       # its nut
    c = c.cut(box(-d - BODY_TAB_W / 2 - 1.2, x1 + 1, Y0 - gap / 2, Y0 + gap / 2, -COLLAR_E - BODY_TAB_W / 2 - 4, -ro + 0.5))   # tab slot
    # the strut's boss is wider than its tab, so the cheeks stop short of it on the strut's side (+x, the strut lies within
    # 5 deg of the tube) and leave room for the boss all round: it sits BOSS_CLR off the tab's shoulder, 0.3 mm more of height
    # for the strut's tilt. The notch opens on the end face.
    c = c.cut(box(-d + BODY_BOSS_AT - BOSS_CLR, x1 + 1, Y0 - cw - 1, Y0 + cw + 1, -COLLAR_E - BODY_TAB_W / 2 - 6,
                  -COLLAR_E + BODY_BOSS_D / 2 + BOSS_CLR + 0.3))
    c = c.cut(cyl(PIN_R, (-d, Y0 - 10, -COLLAR_E), (-d, Y0 + 10, -COLLAR_E)))                    # M4 x 16 strut screw,
    c = c.cut(m.csk_hole(4, (-d, Y0 + cw, -COLLAR_E), (0, -1, 0), 1))                            # head on +y,
    c = c.cut(hexprism(7.2, (-d, Y0 - cw + 2.5, -COLLAR_E), (-d, Y0 - cw - 1, -COLLAR_E)))       # nut 2.5 deep on -y
    return c.clean()


def collar(theta=0.0):
    return rot_y(_collar(), theta)


# ---------------------------------------------------------------- bought parts (for renders)
def strut(theta=0.0):
    """the gas strut between the anchor eye and the collar eye at lever angle theta"""
    cx, cz = collar_pin(theta)
    a, c = V(ANCH_X, Y0, ANCH_Z), V(cx, Y0, cz)
    u = (c - a).normalized()

    def tab(at, t, w, toward, length):
        """flat eyelet tab: round end on the eye, running `length` toward the rod or body"""
        body = cq.Solid.makeBox(length, t, w, V(0, -t / 2, -w / 2)).fuse(cyl(w / 2, (0, -t / 2, 0), (0, t / 2, 0)))
        body = body.cut(cyl(PIN_R - 0.2, (0, -t, 0), (0, t, 0)))
        return body.rotate((0, 0, 0), (0, 1, 0), math.degrees(math.atan2(-toward.z, toward.x))).translate(at)

    boss = cyl(BODY_BOSS_D / 2, (c - u * BODY_TAB_L).toTuple(), (c - u * BODY_BOSS_AT).toTuple())
    return fuse(tab(a, ROD_TAB_T, ROD_TAB_W, u, TAB_L), tab(c, BODY_TAB_T, BODY_TAB_W, -u, BODY_BOSS_AT + 1.0), boss,
                cyl(STRUT_ROD_D / 2, (a + u * TAB_L).toTuple(), (c - u * (BODY_TAB_L + STRUT_BODY_L - 2)).toTuple()),
                cyl(STRUT_BODY_D / 2, (c - u * (BODY_TAB_L + STRUT_BODY_L)).toTuple(), (c - u * BODY_TAB_L).toTuple()))


def pins(theta=0.0):
    """kit M4 x 16 countersunk screws + nuts through both eyes (head on +y, nut on -y), and the collar's M4 x 12 clamp
    screw + nut; the collar's turn with the lever (theta)"""
    aw = (ROD_TAB_T + 0.6) / 2 + CLEVIS_T
    cw = (BODY_TAB_T + 0.6) / 2 + CHEEK_T
    d, ro = COLLAR_D, COLLAR_BORE + COLLAR_WALL
    xc = -d + (COLLAR_W - 2 * COLLAR_BACK) / 2
    anchor = fuse(m.csk_screw(4, (ANCH_X, Y0 + aw, ANCH_Z), (0, -1, 0), 16), m.nut(4, (ANCH_X, Y0 - aw + 3.4, ANCH_Z), (0, -1, 0)))
    col = fuse(m.csk_screw(4, (-d, Y0 + cw, -COLLAR_E), (0, -1, 0), 16), m.nut(4, (-d, Y0 - cw + 2.5, -COLLAR_E), (0, -1, 0)),
               m.csk_screw(4, (xc, Y0 - 5, ro + 3), (0, 1, 0), 12), m.nut(4, (xc, Y0 + 3.8, ro + 3), (0, 1, 0)))
    return fuse(anchor, rot_y(col, theta))


# ---------------------------------------------------------------- cable cover and its plug
# The cable cover's slot (Rev 1's cover_cable()) lets the USB cable drop into its bore sideways, so the plug never has to
# pass through it. The plug is the piece that slot cut away, 0.1 mm smaller each side: with the cable in, it slides in
# from the spout's outer end, under the cable, and fills the slot again. An M2 x 12 countersunk comes up from under the
# cover's rim, through a clearance hole, and threads into the plug: tightening it pulls the plug's head down onto the
# cover's shoulders, the way the cable pushes it, and pins it in place.
m.CSK[2], m.TAP[2] = (4.0, 2.4), 1.6               # M2 countersunk head and clearance; pilot to tap
PLUG_CLR = 0.1
PLUG_SCREW = (29.0, -14.0)                        # (x, z of the head's top): up through the rim's underside, its head
                                                  # in a counterbore 3.7 mm up from the curved surface; its tip ends at
                                                  # z -2, 0.4 mm under the plug's top and 5.9 mm into the plug
# The slot is a T (seen along the spout): 5 mm wide at the mouth, where the cable drops in, and SLOT_HEAD wide from the
# bore down to SLOT_HEAD_Z. The plug's head bears on the cover's shoulders either side of the mouth all along the slot,
# so pushing the cable down loads the cover.
SLOT_MOUTH, SLOT_HEAD, SLOT_HEAD_Z = 5.0, 6.8, -4.6
SPOUT_R = 6.9                                     # Rev 1: 6.5. Room round the T's head; it just clears the block's face
# The plug's top, under the cable, is flat (it prints better than the bore's curve), level with where the bore meets the
# slot's side walls in the cover, so it lines up with the cover's edges and stays out of the bore's sides
PLUG_TOP = -math.sqrt(3.75 ** 2 - (SLOT_HEAD / 2) ** 2)    # -1.58: 1.58 mm under the bore's axis


_CABLE_COVER = []


def _cable_cover_solid():
    """Rev 1's cable cover before its slot is cut, its outside edges already chamfered, and the slot (USB side: no
    mirroring). Cover and plug are both cut from it, so the plug carries the cover's own chamfers and the slot's edges
    stay sharp: the plug fills it with only a hairline round it"""
    sy = m.BLOCK_Y1 + 7
    if not _CABLE_COVER:
        c = m._cover_base().fuse(cyl(SPOUT_R, (20, sy, 0), (m.COVER_R + 10, sy, 0)))
        c = m._cover_finish(c, m.BLOCK_Y1 + 9.5)
        c = c.cut(cyl(3.75, (0, sy, 0), (m.COVER_R + 12, sy, 0)))
        _CABLE_COVER.append(chamfer_edges(c))
    return _CABLE_COVER[0], sy, _slot(sy)


def _slot(sy, k=0.0):
    """the T-slot, shrunk by k all round (k = PLUG_CLR gives the plug's outline)"""
    x0, x1 = 20, m.COVER_R + 12
    mouth = box(x0, x1, sy - SLOT_MOUTH / 2 + k, sy + SLOT_MOUTH / 2 - k, -8 + k, 0)
    head = box(x0, x1, sy - SLOT_HEAD / 2 + k, sy + SLOT_HEAD / 2 - k, SLOT_HEAD_Z + k, 0)
    return mouth.fuse(head)


def cover_cable_r3():
    c, sy, slot = _cable_cover_solid()
    x, zh = PLUG_SCREW
    c = c.cut(slot)
    rim = math.sqrt(m.COVER_R ** 2 - x ** 2)                                  # the rim's surface under the screw, below the axis
    c = c.cut(m.csk_hole(2, (x, sy, zh), (0, 0, 1), -8.0 + 0.5 - zh, out=rim + zh + 2.0))   # up through the rim into the slot;
                                                                                # the counterbore runs out through the rim's surface
    return c.clean()


def cable_plug():
    c, sy, _ = _cable_cover_solid()
    x, zh = PLUG_SCREW
    k = PLUG_CLR
    bore = cyl(3.75, (0, sy, 0), (m.COVER_R + 12, sy, 0))
    p = c.fuse(bore).intersect(_slot(sy, k))
    p = p.intersect(box(0, m.COVER_R + 10, sy - 10, sy + 10, -20, PLUG_TOP))           # flat top; ends at the spout's end
    p = p.cut(cyl(m.COVER_IN_R, (0, m.BLOCK_Y1 - 1, 0), (0, sy + SLOT_HEAD / 2 + 1, 0)))   # starts at the hollow's wall
    return p.cut(cyl(m.TAP[2] / 2, (x, sy, -9.0), (x, sy, 1.0))).clean()               # tap M2, from below


def hardware_r3():
    """the fixed base's kit screws and nuts (reference): friction screw, shoe hinge, side covers, pillow-block caps and
    down-stops"""
    hz = m.KNOB_HEAD_Z - m.KNOB_BOLT[1]
    parts = [m.fuse(m.hexprism(m.M5_HEAD_AF - 0.1, (m.KNOB_X, m.KNOB_Y, hz), (m.KNOB_X, m.KNOB_Y, m.KNOB_HEAD_Z)),
                    m.cyl(2.1, (m.KNOB_X, m.KNOB_Y, hz - m.KNOB_BOLT[0]), (m.KNOB_X, m.KNOB_Y, hz + 0.1))),   # M5 x 25 hex bolt
             m.nut(5, (m.KNOB_X, m.KNOB_Y, m.FN_NUT_Z), (0, 0, -1)),
             m.csk_screw(4, (m.HINGE_X, 12, m.HINGE_Z), (0, 1, 0), 20), m.nut(4, (m.HINGE_X, 28.6, m.HINGE_Z), (0, 1, 0))]
    for s in (-1, 1):
        y = Y0 + s * sum(PAD_DY) / 2
        parts += [m.csk_screw(4, (STOP_X, y, PAD_Z), (0, 0, -1), 16),
                  m.nut(4, (STOP_X, y, POST_TOP - 3.2), (0, 0, 1)), m.nut(4, (STOP_X, y, POST_TOP), (0, 0, 1))]
        yb = s * (m.BRG_Y0 + m.BLOCK_Y1) / 2
        for x in (-m.CAP_BOLT_X, m.CAP_BOLT_X):
            parts += [m.csk_screw(4, (x, yb, 8), (0, 0, -1), 20), m.nut(4, (x, yb, CAP_NUT_Z), (0, 0, -1))]
        for a in (45, 135, 225, 315):
            px, pz = m.on_circle(m.COVER_HOLE_R, a)
            parts.append(m.csk_screw(3, (px, s * (m.BLOCK_Y1 + m.COVER_D), pz), (0, -s, 0), COVER_SCREW_L))
    x, zh = PLUG_SCREW
    parts.append(m.csk_screw(2, (x, m.BLOCK_Y1 + 7, zh), (0, 0, 1), 12))              # the cable plug's screw, from below
    return fuse(*parts)


def lever_hardware():
    """Rev 1's lever screws + nuts: they turn with the lever (reference)"""
    return m.lever_screws()


def carbon_tube(length=TUBE_L + TUBE_EXTRA):
    return tube(m.TUBE_OD / 2, m.TUBE_ID / 2, (-m.SOCK_BOTTOM, Y0, 0), (-m.SOCK_BOTTOM - length, Y0, 0))


# ---------------------------------------------------------------- balance
def strut_torque(theta, F=STRUT_F, collar_dd=0.0):
    """nose-up torque of the strut about the pivot, N*mm; None if it would leave its stroke"""
    cx, cz = collar_pin(theta, COLLAR_D + collar_dd)
    dx, dz = cx - ANCH_X, cz - ANCH_Z
    L = math.hypot(dx, dz)
    if not STRUT_COMP - 0.01 <= L <= STRUT_EXT + 0.01:
        return None
    f = F * (1 + (STRUT_PROG - 1) * (STRUT_EXT - L) / (STRUT_EXT - STRUT_COMP))
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    d, e = COLLAR_D + collar_dd, COLLAR_E
    return f * (dx * (d * s - e * c) + dz * (d * c + e * s)) / L


def printed_mass(shp, shell=1.2, infill=0.2, rho=1.27):
    """grams for a print with `shell` mm walls and `infill`, PETG-ish density"""
    v, a = shp.Volume() / 1000, shp.Area() / 100
    s = min(v, a * shell / 10)
    return rho * (s + infill * max(0, v - s))


def rear_items(parts):
    """(grams, centre of mass at 0 deg) for everything that turns with the lever, apart from the forward items"""
    cx, cz = collar_pin(0.0)
    items = [(printed_mass(parts[n]), cq.Shape.centerOfMass(parts[n])) for n in ("lever_upper", "lever_lower")]
    return items + [(4 * 3.6, V(-1.5, -5, 0)),                                               # lever screws + nuts
                    (printed_mass(parts["strut_collar"], infill=0.4) + 8.0, cq.Shape.centerOfMass(parts["strut_collar"])),
                    (STRUT_G / 2, V(cx, Y0, cz))]                                            # half the strut hangs on the collar


def gravity(theta, items):
    """nose-down moment about the pivot in g*m: forward items ~ cos(theta), the rest from their centres of mass"""
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return FWD_GM * c + sum(g * -(p.x * c + p.z * s) for g, p in items) / 1000


def frange(t_max, step=0.5):
    return [i * step for i in range(int(t_max / step) + 1)]


def balance(plot=None):
    nmm = lambda gm: gm * 9.80665                                                           # g*m -> N*mm
    grip = lambda n: n / 9.80665e-3 / GRIP_R                                                # N*mm -> grams at the grip
    items = rear_items(build())
    load = lambda t: nmm(gravity(t, items))
    th = frange(STOP_DEG)
    print(f"forward moment {FWD_GM:.1f} g*m (470 mm carbon tube); load {load(0) / 1000:.3f} N*m at 0 deg, "
          f"{load(STOP_DEG) / 1000:.3f} at {STOP_DEG:.0f}")
    L0, L1 = (math.hypot(collar_pin(t)[0] - ANCH_X, collar_pin(t)[1] - ANCH_Z) for t in (0, STOP_DEG))
    print(f"strut {L0:.0f} mm at 0 deg -> {L1:.0f} mm at {STOP_DEG:.0f} deg (stroke window {STRUT_COMP:.0f}..{STRUT_EXT:.0f})")
    for F in (STRUT_F_DESIGN, STRUT_F, STRUT_F_RANGE[1]):
        err = [strut_torque(t, F) - load(t) for t in th]
        ballast = sum(err) / len(err) / 9.80665e-3 / BOX_R
        print(f"  {F:.0f} N: {grip(min(err)):+.0f} .. {grip(max(err)):+.0f} g at the grip (+ = rises)"
              + (f"; about {ballast:.0f} g of ballast in the head evens it out" if ballast > 5 else ""))
    for k in COLLAR_RANGE:
        print(f"  collar {k:+.0f} mm: {grip(strut_torque(0, STRUT_F, k) - strut_torque(0, STRUT_F)):+.0f} g at 0 deg")
    if plot:
        plot_balance(plot, load, grip)


def plot_balance(path, load, grip):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, grid, surf = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    blue, aqua, orange = "#2a78d6", "#1baf7a", "#eb6834"
    th = frange(STOP_DEG, 0.25)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": ink2, "axes.labelcolor": ink2,
                         "xtick.color": ink2, "ytick.color": ink2})
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 7.6), sharex=True, gridspec_kw=dict(height_ratios=[1, 1.05], hspace=0.12))
    fig.patch.set_facecolor(surf)
    for a in (a1, a2):
        a.set_facecolor(surf)
        a.grid(True, color=grid, lw=0.8)
        for sd in ("top", "right"):
            a.spines[sd].set_visible(False)
    a1.plot(th, [load(t) / 1000 for t in th], color=ink2, lw=2, label="gravity, nose down (head, grip, tube, lever)")
    a1.plot(th, [strut_torque(t, STRUT_F_DESIGN) / 1000 for t in th], color=blue, lw=2,
            label=f"strut at {STRUT_F_DESIGN:.0f} N (the geometry's design point)")
    a1.plot(th, [strut_torque(t, STRUT_F) / 1000 for t in th], color=orange, lw=2, label=f"strut at {STRUT_F:.0f} N (nominal)")
    a1.set_ylabel("torque about the pivot, N·m")
    a1.legend(loc="lower left", frameon=False, fontsize=9)
    a1.set_title(f"MkIII Rev 3: gas strut, 470 mm carbon tube, {STOP_DEG:.0f}° stop", loc="left", color=ink, fontsize=12, pad=10)
    a2.axhline(0, color=ink2, lw=1)
    for F, col, ls in ((STRUT_F_DESIGN, blue, "-"), (STRUT_F, orange, "-"), (STRUT_F_RANGE[1], aqua, (0, (5, 3)))):
        err = [strut_torque(t, F) - load(t) for t in th]
        ballast = sum(err) / len(err) / 9.80665e-3 / BOX_R
        lab = f"{F:.0f} N" + ("" if abs(ballast) < 10 else f": add about {ballast:.0f} g to the head")
        a2.plot(th, [grip(x) for x in err], color=col, lw=2, ls=ls, label=lab)
    a2.set_ylabel(f"out of balance at the grip ({GRIP_R:.0f} mm), g\n+ = rises, − = drops")
    a2.set_xlabel("lever angle, deg (0 = down-stop)")
    a2.set_xlim(0, STOP_DEG)
    a2.legend(loc="center right", frameon=False, fontsize=9)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=surf)
    print("wrote", path)


# ---------------------------------------------------------------- edge chamfers
# Every printed part's sharp outside edges get a 45 degree chamfer, as on the head: CHAMFERS[0] where it fits, then the
# smaller sizes on what's left (thin walls, crowded corners). Hole rims are left alone, so bores, bearing seats and
# screw holes keep their fits; so are edges already blunter than 120 degrees between faces (a chamfer's own edges).
CHAMFERS = (0.8, 0.5, 0.3)


def _faces_of_edges(shape):
    em = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, em)
    return em


def _hole_wall(f, p, n):
    """a cylinder or cone whose outward normal at p points toward its axis"""
    ad = BRepAdaptor_Surface(f.wrapped)
    t = ad.GetType()
    if t not in (GeomAbs_Cylinder, GeomAbs_Cone):
        return False
    ax = (ad.Cylinder() if t == GeomAbs_Cylinder else ad.Cone()).Axis()
    o, d = V(ax.Location().X(), ax.Location().Y(), ax.Location().Z()), V(ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z())
    return ((p - o) - d * (p - o).dot(d)).dot(n) < 0


def sharp_edges(shape, eps=0.05, max_dot=0.5, exclude=None):
    """convex edges between two faces meeting at under 120 degrees, neither face a hole's wall"""
    em = _faces_of_edges(shape)
    out = []
    for i in range(1, em.Extent() + 1):
        e, fs = cq.Edge(em.FindKey(i)), [cq.Face(f) for f in em.FindFromIndex(i)]
        if len(fs) != 2 or e.Length() < 0.5 or (exclude is not None and exclude(e)):
            continue
        p = e.positionAt(0.5)
        n1, n2 = fs[0].normalAt(p), fs[1].normalAt(p)
        if n1.dot(n2) >= max_dot or _hole_wall(fs[0], p, n1) or _hole_wall(fs[1], p, n2):
            continue
        if not shape.isInside(p + (n1 - n2) * eps, 1e-4):     # inside just off the bisector: a concave edge
            out.append(e)
    return out


def _chamfer(shape, edges, c):
    try:
        r = shape.chamfer(c, None, edges)
        return r if r.isValid() else None
    except Exception:
        return None


def chamfer_edges(shape, sizes=CHAMFERS, chunk=8, exclude=None):
    """chamfer what will take it: one awkward edge sinks a whole set, so add the edges a chunk at a time and a failing
    chunk one edge at a time"""
    for c in sizes:
        keep = []
        es = sharp_edges(shape, exclude=exclude)
        for i in range(0, len(es), chunk):
            part = es[i:i + chunk]
            if _chamfer(shape, keep + part, c) is not None:
                keep += part
                continue
            for e in part:
                if _chamfer(shape, keep + [e], c) is not None:
                    keep.append(e)
        if keep:
            shape = shape.chamfer(c, None, keep)
    return shape


# the four lever screws: M4 socket head cap screws from the HELIFOUNER kit (M4 x 30/35/40/45/50, with nuts). Each head sits at
# the top of its counterbore, flush with the hub's surface at the counterbore's lowest edge, and each nut in a pocket open to
# the underside, so the seats are as far apart as the lever allows. The kit length is the longest whose tip stays inside the
# lever's outline, and the nut's open face sits level with the hub's surface at its far flat (hex corners along y, flats
# facing fore and aft, so the nut reaches only AF/2 along the hub's curve).
KIT_LENGTHS = (30, 35, 40, 45, 50)
CAP_K, CAP_D, CAP_CB_R = 4.0, 7.0, 4.0           # M4 cap head (ISO 4762): height, diameter; counterbore radius (0.5 mm clear all round)
LS_NUT_T, LS_TIP_PAST_NUT = 3.2, 1.0             # M4 nut thickness; the screw's tip stands this far past the nut's far face
NUT_WALL = 0.1                                   # hub left under the nut's far flat at its open face


def hex_y(af, p0, p1):
    """m.hexprism with its corners along y (flats facing x), to stay inside the hub's curve fore and aft"""
    p0, p1 = V(*p0), V(*p1)
    pl = cq.Plane(origin=p0, xDir=(0, 1, 0), normal=(p1 - p0).normalized())
    return cq.Workplane(pl).polygon(6, af / math.cos(math.radians(30))).extrude((p1 - p0).Length).val()


def lever_screw_seats():
    """per screw (x, y, head seat z, kit length, tip z, nut pocket ceiling z), in the lever's frame"""
    out = []
    for x, y in m.LEVER_SCREWS:
        z_head = math.sqrt(HUB_R ** 2 - (abs(x) + CAP_CB_R) ** 2) - CAP_K     # head top level with the hub's lowest point under the counterbore
        z_nut_open = -math.sqrt(HUB_R ** 2 - (abs(x) + m.LS_NUT_AF / 2) ** 2) + NUT_WALL   # lowest the nut's open face may sit
        length = max(k for k in KIT_LENGTHS if k <= z_head - (z_nut_open - LS_TIP_PAST_NUT))
        z_tip = z_head - length
        out.append((x, y, z_head, length, z_tip, z_tip + LS_TIP_PAST_NUT + LS_NUT_T))
    return out


def lever_screw_cuts_r3():
    """per screw: counterbore from the head seat to the top, clearance hole, and a hex pocket from the underside up to the
    nut's seat"""
    cuts = []
    for x, y, zh, _, _, zn in lever_screw_seats():
        cuts += [cyl(CAP_CB_R, (x, y, zh), (x, y, 60)),
                 cyl(m.LS_CLR_R, (x, y, zn - 0.5), (x, y, zh + 0.01)),
                 hex_y(m.LS_NUT_AF, (x, y, -60), (x, y, zn))]
    return cuts


def lever_screws_r3():
    """the cap screws and their nuts (reference)"""
    parts = []
    for x, y, zh, length, zt, zn in lever_screw_seats():
        parts += [cyl(CAP_D / 2, (x, y, zh), (x, y, zh + CAP_K)), cyl(2.0, (x, y, zt), (x, y, zh)),
                  hex_y(7.0, (x, y, zn - LS_NUT_T), (x, y, zn))]
    return fuse(*parts)


m.lever_screw_cuts = lever_screw_cuts_r3
m.lever_screws = lever_screws_r3


def lever_halves_r3():
    """Rev 1's lever_halves() with the chamfers kept off every edge in the joint plane, so only the edges that stay outside
    when the halves are bolted together are chamfered: the joint's mating faces keep their sharp edges"""
    h = m.lever()
    for c in m.lever_screw_cuts():
        h = h.cut(c)
    h = h.clean()
    on_joint = lambda e: abs(e.BoundingBox().zmin) < 1e-4 and abs(e.BoundingBox().zmax) < 1e-4
    up = chamfer_edges(h.intersect(box(-200, 200, -100, 100, 0, 200)).clean(), exclude=on_joint)
    lo = chamfer_edges(h.intersect(box(-200, 200, -100, 100, -200, 0)).clean(), exclude=on_joint)
    return up, lo


m.lever_halves = lever_halves_r3


# ---------------------------------------------------------------- build + export
def build():
    parts = m.build()                                                                       # lever halves are Rev 3's (m.lever)
    for k in ("ballast_bucket", "bucket_lid", "ballast", "frame", "hardware", "striker", "stop_block", "stop_thumb_knob",
              "alu_tube"):
        parts.pop(k)
    parts.update({
        # printed
        "frame": frame_r3(),
        "strut_collar": collar(),
        "friction_knob": m.friction_knob(),
        "cover_cable": cover_cable_r3(),
        "cable_plug": cable_plug(),
        # bought / reference
        "carbon_tube": carbon_tube(160.0),
        "gas_strut": strut(),
        "strut_pins": pins(),
        "hardware": hardware_r3(),
        "lever_screws": lever_hardware(),
    })
    for name in PRINTED:
        if name not in ("cover_cable", "cable_plug", "lever_upper", "lever_lower"):   # those: see their own steps
            parts[name] = chamfer_edges(parts[name])
    return parts


PRINTED = ["frame", "cap_left", "cap_right", "lever_upper", "lever_lower", "shoe", "sensor_carrier", "cover_sensor",
           "cover_cable", "cable_plug", "strut_collar", "friction_knob"]

if __name__ == "__main__" and "--curve" in sys.argv[1:]:
    balance(plot=os.path.join(HERE, "renders", "strut_balance.png"))
elif __name__ == "__main__":
    parts = build()
    for name, shp in parts.items():
        print(f"{name:22s} valid={shp.isValid()} vol={shp.Volume():10.1f}")
        sub = os.path.join(HERE, "stl") if name in PRINTED else os.path.join(HERE, "stl", "ref")
        os.makedirs(sub, exist_ok=True)
        cq.exporters.export(cq.Workplane().add(shp), os.path.join(sub, f"{name}.stl"), tolerance=0.04, angularTolerance=0.12)
    os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    asm = cq.Assembly(name="MkIII_Rev3")
    for name, shp in parts.items():
        asm.add(shp, name=name)
    asm.export(os.path.join(HERE, "step", "MkIII_Rev3_assembly.step"))
    print("done")
