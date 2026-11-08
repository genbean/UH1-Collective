"""
MkIII base, narrow concept (CONCEPT ONLY: nothing here is exported for printing, and Rev 3 is unchanged)

Goal: the whole base no wider than 3.25 in (82.6 mm) along the pivot axis, against Rev 3's 130 mm, with the lever
symmetrical about the tube. The hub is cut back to the socket boss either side, and everything else is fitted between
the hub's ends and y = +-41.

Same frame as Rev 3 except the tube's plane: origin = pivot centre, Y = pivot axis, Z = up, tube along -X at 0 deg,
+Y = USB side, -Y = sensor side. Rev 3's tube is at y = -9; here it is at y = 0, so Rev 3's strut, collar, pins and
hose clamp are moved +9 in y.

What changes to fit (per side, from the hub's end face out):
    hub end             |y| 21.0      (Rev 3: 32; the socket boss is 18 in radius, so 3 mm past it)
    bearing             |y| 21.5-28.5 6808-2RS thin-section, 40 x 52 x 7 (Rev 3: 6006-2RS, 30 x 55 x 13)
    pillow-block lip    |y| 28.5-30.5 2 mm, holds the outer race
    trunnion end        |y| 31.0      40 mm OD (it runs in the 6808's 40 mm bore), 34 mm bore on the sensor side
    side cover          |y| 30.5-41.0 10.5 mm deep (Rev 3: 15)
    The AS5600 board (23 x 23, 32.5 across its corners) sits INSIDE the sensor trunnion's 34 mm bore, chip facing out;
    the magnet is on a post from the cover, 1 mm off the chip. Rev 3 stacks the board, carrier and magnet outside
    the trunnion end, which is what made its cover 15 deep.
    The USB cable bends out of the axis inside the cable cover (4 mm radius) and leaves through a notch in its rim,
    the way the retrofit cover goes on over the cable; there's no spout to stick out.

Brake: there is no room for Rev 3's drum, shoe and knob tower beside the hub, so the brake moves behind it. A curved
shoe with felt on its face rides in a pocket in a tower on the frame's back edge and presses on the hub's own
cylinder (r 30) at the back, level with the axis. An M5 bolt through a captive nut in the tower, turned by a knob on
the back of the tower, pushes the shoe through a spring, the way Rev 3's knob loads its shoe. The up-stop boss moves
round under the hub (contact at x 2-18) so it stays clear of the shoe over the whole travel.

Run:  python narrow_concept.py      -> renders in renders/ (needs cadquery, trimesh, manifold3d, pyvista)
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)

import numpy as np                                     # noqa: E402
import trimesh                                         # noqa: E402
import cadquery as cq                                  # noqa: E402
from PIL import Image, ImageDraw                        # noqa: E402
import make_renders_r3 as R                            # noqa: E402  (Rev 3's model, renderer and GLB)

r, m, d = R.r, R.m, R.d
from mk3_pivot import cyl, tube, box, fuse, rot_y, hexprism, sweep_circle   # noqa: E402

OUT = os.path.join(HERE, "renders")
DY = -m.SOCK_Y                                         # +9: Rev 3's tube plane to y = 0

# ---------------------------------------------------------------- parameters
W_HALF = 41.0                                          # overall width 82 mm (3.25 in = 82.6)
HUB_HW, HUB_R = 21.0, 30.0
BRG = (40.0, 52.0, 7.0)                                # 6808-2RS: bore, OD, width
BRG_IR_SH, BRG_OR_SH = 43.5, 48.5                      # race shoulders (approx.)
B_Y0 = HUB_HW + 0.5
B_Y1 = B_Y0 + BRG[2]
BLK_Y1 = B_Y1 + 2.0                                    # pillow block's outer face (30.5)
TRUN_R = BRG[0] / 2
TRUN_OUT = BLK_Y1 + 0.5                                # 31
LIP_R = 23.0                                           # clears the inner race's shoulder, holds the outer race
BLK_HW = 35.0
CAP_BOLT_X = 30.5
COV_R, COV_IN_R, COV_FLOOR = 33.0, 24.5, 3.0
COV_HOLE_R = 29.5
SENS_BORE_R, SENS_POCKET = 17.0, 24.0                  # sensor trunnion's bore: r 17, from |y| 24 out
PCB_Y = (-28.6, -27.0)                                 # the board in the bore; chip on its outer face
CHIP_Y = (-30.1, -28.6)
MAG_Y = (-33.1, -31.1)                                 # 1.0 mm off the chip
USB_BEND_R, USB_Y = 4.0, 35.5

SOCK_BOSS_R, SOCK_MOUTH, SOCK_BOTTOM = 18.0, 66.0, 20.0
CABLE_R = 6.5
PAD_X, PAD_DY, PAD_Z = r.PAD_X, r.PAD_DY, r.PAD_Z
Z_PLATE, AXIS_H, PLATE_T = r.Z_PLATE, r.AXIS_H, m.PLATE_T
PLATE_X = (-62.0, 60.0)
STOP_DEG = r.STOP_DEG
USTOP_X, USTOP_Z, USTOP_HW = (2.0, 18.0), -38.0, 14.0
LEVER_SCREWS = [(x, y) for x in (-15.0, 17.0) for y in (-13.0, 13.0)]

# brake
SHOE_HW, SHOE_HZ = 15.0, 10.8                          # shoe half width (y), half height (z)
FELT_T = 1.5
SHOE_X1 = 44.0                                         # the shoe's back face
TOWER_X = (38.0, 56.0)
TOWER_HW, TOWER_TOP = 17.0, 15.0
NUT_X = 50.0                                           # captive M5 nut, slid in from the top
KNOB_X = (58.0, 70.0)
KNOB_R = 12.0


# ---------------------------------------------------------------- lever
def wedge_xz(pts, hw):
    """a prism from an (x, z) outline, y from -hw to +hw"""
    return cq.Workplane("XZ").polyline(pts).close().extrude(hw, both=True).val()


def lever_solid():
    hub = cyl(HUB_R, (0, -HUB_HW, 0), (0, HUB_HW, 0))
    trun = cyl(TRUN_R, (0, -TRUN_OUT, 0), (0, TRUN_OUT, 0))
    boss = cyl(SOCK_BOSS_R, (-15, 0, 0), (-SOCK_MOUTH, 0, 0))
    rib_top = wedge_xz([(-58, 0), (-58, 21), (-30, 29), (-12, 29), (-12, 0)], 3.0)
    rib_bot = wedge_xz([(-50, 0), (-50, -20), (-28, -25), (-14, -25), (-14, 0)], 3.0)
    pads = [box(*PAD_X, *sorted((s * PAD_DY[0], s * PAD_DY[1])), PAD_Z, 0) for s in (-1, 1)]
    ustop = rot_y(box(*USTOP_X, -USTOP_HW, USTOP_HW, USTOP_Z, -20), -STOP_DEG)   # lands on the pedestal at STOP_DEG
    s = fuse(hub, trun, boss, rib_top, rib_bot, *pads, ustop)
    s = s.cut(tube(SOCK_BOSS_R + 1, SOCK_BOSS_R - 1.4, (-54, 0, 0), (-63, 0, 0)))          # hose-clamp seat
    s = s.cut(cyl(m.SOCK_BORE_R, (-SOCK_BOTTOM, 0, 0), (-SOCK_MOUTH - 1, 0, 0)))            # socket
    s = s.cut(cyl(CABLE_R, (-SOCK_BOTTOM - 1, 0, 0), (0, 0, 0)))                             # radial cable channel
    s = s.cut(cyl(CABLE_R, (0, -SENS_POCKET - 1, 0), (0, TRUN_OUT + 1, 0)))                  # axial cable bore
    s = s.cut(cyl(SENS_BORE_R, (0, -TRUN_OUT - 1, 0), (0, -SENS_POCKET, 0)))                 # sensor pocket
    for x, y in LEVER_SCREWS:                                                                # M4 caps, top to nuts
        s = s.cut(cyl(2.2, (x, y, -40), (x, y, 40)))
        s = s.cut(cyl(3.6, (x, y, 22), (x, y, 40)))
        s = s.cut(hexprism(7.2, (x, y, -40), (x, y, -20)))
    return s.clean()


_LEVER = []


def lever_halves(th=0.0):
    if not _LEVER:
        s = lever_solid()
        _LEVER.extend([s.intersect(box(-200, 200, -100, 100, 0, 100)).clean(),
                       s.intersect(box(-200, 200, -100, 100, -100, 0)).clean()])
    return [rot_y(h, th) for h in _LEVER]


def lever_screws(th=0.0):
    out = []
    for x, y in LEVER_SCREWS:
        zt = math.sqrt(HUB_R ** 2 - x ** 2) - 3.0
        out += [cyl(3.4, (x, y, zt - 4), (x, y, zt)), cyl(2.0, (x, y, zt - 40), (x, y, zt - 4))]
    return rot_y(fuse(*out), th)


# ---------------------------------------------------------------- frame
def block_bores(s):
    return [cyl(BRG[1] / 2 + 0.05, (0, s * (B_Y0 - 1), 0), (0, s * B_Y1, 0)),
            cyl(LIP_R, (0, s * (B_Y0 - 1), 0), (0, s * (BLK_Y1 + 1), 0))]


def frame():
    plate = (cq.Workplane("XY").box(PLATE_X[1] - PLATE_X[0], 2 * W_HALF, PLATE_T, centered=False)
             .translate((PLATE_X[0], -W_HALF, -AXIS_H)).edges("|Z").fillet(6).val())
    parts = [plate]
    for s in (-1, 1):
        y0, y1 = sorted((s * B_Y0, s * BLK_Y1))
        parts.append(box(-BLK_HW, BLK_HW, y0, y1, Z_PLATE, 0))
        front = (cq.Workplane("XZ", origin=(0, y1, 0))                          # gusset on the block's front face
                 .polyline([(-BLK_HW - 12, Z_PLATE), (-BLK_HW, Z_PLATE), (-BLK_HW, -12)]).close()
                 .extrude(y1 - y0).val())
        parts.append(front)
    parts.append(box(*(x + dx for x, dx in zip(USTOP_X, (-2, 2))), -USTOP_HW - 2, USTOP_HW + 2, Z_PLATE, USTOP_Z))
    for s in (-1, 1):                                                                    # down-stop pillars
        parts.append(box(*PAD_X, *sorted((s * PAD_DY[0], s * PAD_DY[1])), Z_PLATE, PAD_Z))
    # strut anchor clevis: two cheeks either side of the rod's tab
    aw = (r.ROD_TAB_T + 0.6) / 2
    for s in (-1, 1):
        y0, y1 = sorted((s * aw, s * (aw + r.CLEVIS_T)))
        parts += [box(r.ANCH_X - r.CLEVIS_R, r.ANCH_X + r.CLEVIS_R, y0, y1, Z_PLATE, r.ANCH_Z),
                  cyl(r.CLEVIS_R, (r.ANCH_X, y0, r.ANCH_Z), (r.ANCH_X, y1, r.ANCH_Z))]
    # brake tower, behind the hub
    parts.append(box(*TOWER_X, -TOWER_HW, TOWER_HW, Z_PLATE, TOWER_TOP))
    parts.append(wedge_xz([(TOWER_X[1], Z_PLATE), (PLATE_X[1], Z_PLATE), (TOWER_X[1], -20)], TOWER_HW))
    f = fuse(*parts)
    for s in (-1, 1):
        f = f.cut(fuse(*block_bores(s)))
    f = f.cut(cyl(r.PIN_R, (r.ANCH_X, -20, r.ANCH_Z), (r.ANCH_X, 20, r.ANCH_Z)))
    f = f.cut(box(TOWER_X[0] - 1, SHOE_X1 + 4.0, -SHOE_HW - 0.3, SHOE_HW + 0.3, -SHOE_HZ - 0.3, SHOE_HZ + 0.3))  # shoe pocket
    f = f.cut(cyl(2.7, (SHOE_X1, 0, 0), (TOWER_X[1] + 1, 0, 0)))                                        # M5 clearance
    f = f.cut(hexprism(8.2, (NUT_X - 2.1, 0, 0), (NUT_X + 2.1, 0, 0)))                                  # nut ...
    f = f.cut(box(NUT_X - 2.1, NUT_X + 2.1, -4.7, 4.7, 0, TOWER_TOP + 1))                               # ... slid in from the top
    for x in (PLATE_X[0] + 9, PLATE_X[1] - 9):                                                          # desk screws
        for y in (-W_HALF + 8, W_HALF - 8):
            f = f.cut(cyl(2.6, (x, y, -AXIS_H - 1), (x, y, Z_PLATE + 1)))
            f = f.cut(cq.Solid.makeCone(2.6, 5.2, 2.6, cq.Vector(x, y, Z_PLATE - 2.6), cq.Vector(0, 0, 1)))
    for s in (-1, 1):                                                                                   # cap screws' holes
        yc = s * (B_Y0 + BLK_Y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            f = f.cut(cyl(2.2, (x, yc, -16), (x, yc, 1)))
            f = f.cut(box(*sorted((x, x + (12 if x > 0 else -12))), yc - 3.6, yc + 3.6, -11.5, -8.3))   # nut slot
    return f.clean()


def caps():
    out = []
    for s in (-1, 1):
        y0, y1 = sorted((s * B_Y0, s * BLK_Y1))
        c = cyl(BLK_HW, (0, y0, 0), (0, y1, 0)).intersect(box(-50, 50, y0, y1, 0, 50))
        for b in block_bores(s):
            c = c.cut(b)
        yc = (y0 + y1) / 2
        for x in (-CAP_BOLT_X, CAP_BOLT_X):
            c = c.cut(cyl(2.2, (x, yc, -1), (x, yc, 40)))
            c = c.cut(cyl(3.8, (x, yc, math.sqrt(BLK_HW ** 2 - x ** 2) - 3.0), (x, yc, 40)))
        out.append(c.clean())
    return out


def cover(s):
    """side cover: s = -1 sensor (magnet post), +1 USB (rim notch for the cable)"""
    y0, y1 = s * BLK_Y1, s * W_HALF
    c = cyl(COV_R, (0, y0, 0), (0, y1, 0))
    c = c.cut(cyl(COV_IN_R, (0, y0 - s, 0), (0, s * (W_HALF - COV_FLOOR), 0)))
    for a in (45, 135, 225, 315):
        px, pz = COV_HOLE_R * math.cos(math.radians(a)), COV_HOLE_R * math.sin(math.radians(a))
        c = c.cut(cyl(1.7, (px, y0 - s, pz), (px, y1 + s, pz)))
        c = c.cut(cq.Solid.makeCone(1.7, 3.0, 1.3, cq.Vector(px, y1 - s * 1.3, pz), cq.Vector(0, s, 0)))
    if s < 0:
        post = cyl(4.5, (0, -(W_HALF - COV_FLOOR) - 0.5, 0), (0, MAG_Y[1], 0))
        c = c.fuse(post).cut(cyl(2.1, (0, MAG_Y[0] - 0.1, 0), (0, MAG_Y[1] + 0.1, 0)))
    else:
        c = c.cut(cyl(2.45, (0, USB_Y, 0), (COV_R + 2, USB_Y, 0)))                    # the cable's way out, at the back
        c = c.cut(box(USB_BEND_R, COV_R + 2, BLK_Y1 - 1, USB_Y, -2.4, 2.4))           # notch: goes on over the cable
    return c.clean()


def brake():
    """shoe (with its felt), spring, M5 bolt, nut and knob"""
    shoe = box(HUB_R - 4, SHOE_X1, -SHOE_HW, SHOE_HW, -SHOE_HZ, SHOE_HZ).cut(
        cyl(HUB_R + FELT_T, (0, -40, 0), (0, 40, 0)))
    shoe = shoe.cut(cyl(5.3, (SHOE_X1 - 4, 0, 0), (SHOE_X1 + 1, 0, 0))).clean()          # spring seat
    felt = cyl(HUB_R + FELT_T, (0, -SHOE_HW, 0), (0, SHOE_HW, 0)).cut(cyl(HUB_R + 0.05, (0, -40, 0), (0, 40, 0)))
    felt = felt.intersect(box(0, 50, -SHOE_HW, SHOE_HW, -SHOE_HZ, SHOE_HZ)).clean()
    spring = tube(4.9, 4.0, (SHOE_X1 - 4, 0, 0), (SHOE_X1 + 4.5, 0, 0))
    bolt = fuse(cyl(2.4, (SHOE_X1 + 4.5, 0, 0), (KNOB_X[1] - 4, 0, 0)),
                hexprism(8.0, (KNOB_X[1] - 4, 0, 0), (KNOB_X[1] - 0.5, 0, 0)))
    nut5 = hexprism(8.0, (NUT_X - 2, 0, 0), (NUT_X + 2, 0, 0)).cut(cyl(2.5, (NUT_X - 3, 0, 0), (NUT_X + 3, 0, 0)))
    knob = cyl(KNOB_R, (KNOB_X[0], 0, 0), (KNOB_X[1], 0, 0))
    for i in range(10):
        a = math.radians(36 * i)
        knob = knob.cut(cyl(2.2, (KNOB_X[0] + 2, KNOB_R * math.cos(a) * 1.05, KNOB_R * math.sin(a) * 1.05),
                            (KNOB_X[1] + 1, KNOB_R * math.cos(a) * 1.05, KNOB_R * math.sin(a) * 1.05)))
    knob = knob.cut(cyl(2.7, (KNOB_X[0] - 1, 0, 0), (KNOB_X[1] - 4, 0, 0)))
    knob = knob.cut(hexprism(8.1, (KNOB_X[1] - 4.1, 0, 0), (KNOB_X[1] - 0.4, 0, 0))).clean()
    return shoe, felt, spring, fuse(bolt, nut5), knob


# ---------------------------------------------------------------- bought / wiring
def bearing(s):
    y0, y1 = sorted((s * B_Y0, s * B_Y1))
    od, idd = BRG[1] / 2, BRG[0] / 2
    return (tube(od, BRG_OR_SH / 2, (0, y0, 0), (0, y1, 0)), tube(BRG_IR_SH / 2, idd, (0, y0, 0), (0, y1, 0)),
            tube(BRG_OR_SH / 2, BRG_IR_SH / 2, (0, y0 + 0.5, 0), (0, y1 - 0.5, 0)))


def sensor():
    pcb = box(-11.5, 11.5, *PCB_Y, -11.5, 11.5)
    chip = box(-2.5, 2.5, *CHIP_Y, -2.0, 2.0)
    carrier = cyl(SENS_BORE_R - 0.1, (0, -SENS_POCKET, 0), (0, PCB_Y[1], 0)).cut(
        cyl(5.0, (0, -SENS_POCKET - 1, 0), (0, PCB_Y[1] + 1, 0))).clean()
    magnet = cyl(2.0, (0, MAG_Y[0], 0), (0, MAG_Y[1], 0))
    return pcb, chip, carrier, magnet


def usb_cable(x0=-190.0):
    s45 = math.sin(math.radians(45))
    rr, rb = 5.0, USB_BEND_R
    yk = USB_Y - rb
    wp = (cq.Workplane("XY").moveTo(x0, 0).lineTo(-rr, 0)
          .threePointArc((-rr + rr * s45, rr - rr * s45), (0, rr))
          .lineTo(0, yk).threePointArc((rb - rb * s45, yk + rb * s45), (rb, USB_Y)).lineTo(70, USB_Y).wire().val())
    return sweep_circle(2.3, wp, (x0, 0, 0), (1, 0, 0))


def sensor_wires(x0=-190.0):
    return fuse(cyl(1.4, (0, PCB_Y[1], 3.6), (0, 0, 3.6)), cyl(1.4, (0, 0, 3.6), (x0, 0, 3.6)))


def carbon_tube(x_end=-200.0):
    return tube(m.TUBE_OD / 2, m.TUBE_ID / 2, (-SOCK_BOTTOM - 0.01, 0, 0), (x_end, 0, 0))


def moved(shape):
    return shape.translate((0, DY, 0))


# ---------------------------------------------------------------- assembly
def assembly(th=0.0, tube_to=-200.0):
    """{name: (cq shape, colour key)}; th = lever angle"""
    lu, ll = lever_halves(th)
    shoe, felt, spring, bolt, knob = brake()
    pcb, chip, carrier, magnet = sensor()
    A = {"frame": (frame(), "frame"), "lever_upper": (lu, "lever_upper"), "lever_lower": (ll, "lever_lower"),
         "cap_left": (caps()[0], "cap_left"), "cap_right": (caps()[1], "cap_right"),
         "cover_sensor": (cover(-1), "cover_sensor"), "cover_cable": (cover(1), "cover_cable"),
         "shoe": (shoe, "shoe"), "felt": (felt, "felt"), "knob_spring": (spring, "knob_spring"),
         "brake_bolt": (bolt, "hardware"), "friction_knob": (knob, "friction_knob"),
         "sensor_carrier": (rot_y(carrier, th), "sensor_carrier"), "sensor_pcb": (rot_y(pcb, th), "sensor_pcb"),
         "sensor_chip": (rot_y(chip, th), "sensor_chip"), "magnet": (magnet, "magnet"),
         "carbon_tube": (rot_y(carbon_tube(tube_to), th), "carbon_tube"),
         "hose_clamp": (rot_y(moved(m.hose_clamp()), th), "hose_clamp"),
         "strut_collar": (moved(r.collar(th)), "strut_collar"), "gas_strut": (moved(r.strut(th)), "gas_strut"),
         "strut_pins": (moved(r.pins(th)), "strut_pins"), "lever_screws": (lever_screws(th), "lever_screws"),
         "usb_cable": (usb_cable(), "usb_cable"), "sensor_wires": (rot_y(sensor_wires(), th), "sensor_wires")}
    for s in (-1, 1):
        o, i, seal = bearing(s)
        A[f"bearing_outer{s}"], A[f"bearing_inner{s}"], A[f"bearing_seal{s}"] = \
            (o, "bearing_outer"), (rot_y(i, th), "bearing_inner"), (seal, "bearing_seal")
    return A


def clashes():
    """lever against every fixed printed part, through the travel (felt: should just touch)"""
    fixed = {"frame": frame(), "cap_left": caps()[0], "cap_right": caps()[1], "cover_sensor": cover(-1),
             "cover_cable": cover(1), "shoe": brake()[0], "felt": brake()[1]}
    for th in (0.0, 8.0, 16.0, 24.0, STOP_DEG, STOP_DEG + 0.5):
        lv = fuse(*lever_halves(th))
        hits = {k: lv.intersect(v).Volume() for k, v in fixed.items()}
        print(f"{th:5.1f} deg  " + "  ".join(f"{k} {v:6.2f}" for k, v in hits.items() if v > 0.005) or f"{th:5.1f}: clear")


# ---------------------------------------------------------------- renders
def to_mesh(shape):
    v, f = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True)


def scene(A, colours, th=0.0):
    P = {}
    for name, (shape, ck) in A.items():
        col = (214, 48, 39) if ck in ("hardware", "strut_pins", "lever_screws") else colours[ck]
        mesh = to_mesh(shape)
        if name == "usb_cable" and th:                   # inside the lever it turns; out in the cover it stays put
            v = mesh.vertices.copy()
            inside = v[:, 1] < B_Y0
            v[inside] = v[inside] @ trimesh.transformations.rotation_matrix(np.radians(th), (0, 1, 0))[:3, :3].T
            mesh = trimesh.Trimesh(v, mesh.faces, process=False)
        P[name] = (mesh, col)
    return P


def width_bar(img, px_l, px_r, y, text, colour=(20, 20, 24)):
    dr = ImageDraw.Draw(img)
    f = d.font(30, bold=True) if hasattr(d, "font") else None
    for x in (px_l, px_r):
        dr.line([(x, y - 18), (x, y + 18)], fill=colour, width=3)
    dr.line([(px_l, y), (px_r, y)], fill=colour, width=3)
    for x, s in ((px_l, 1), (px_r, -1)):
        dr.polygon([(x, y), (x + s * 16, y - 7), (x + s * 16, y + 7)], fill=colour)
    tw = dr.textlength(text, font=f)
    dr.rectangle([((px_l + px_r) - tw) / 2 - 8, y - 46, ((px_l + px_r) + tw) / 2 + 8, y - 10], fill=(255, 255, 255))
    dr.text((((px_l + px_r) - tw) / 2, y - 44), text, fill=colour, font=f)


def title(img, t, sub=""):
    W, H = img.size
    out = Image.new("RGB", (W, H + 90), (255, 255, 255))
    out.paste(img, (0, 90))
    dr = ImageDraw.Draw(out)
    dr.text((30, 14), t, fill=(20, 20, 24), font=d.font(34, bold=True) if hasattr(d, "font") else None)
    if sub:
        dr.text((30, 56), sub, fill=(80, 80, 88), font=d.font(22) if hasattr(d, "font") else None)
    return out


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p, optimize=True)
    print("wrote", os.path.relpath(p, BASE))


def main():
    os.makedirs(OUT, exist_ok=True)
    src = R.load_glb(R.BASE_GLB)
    colours = {k: c for k, (_, c) in src.items()}
    colours["sensor_wires"] = (200, 60, 160)
    clashes()

    P0 = scene(assembly(0.0), colours)
    P32 = scene(assembly(STOP_DEG), colours, STOP_DEG)
    allb = np.vstack([mesh.bounds for name, (mesh, _) in P0.items() if name not in ("usb_cable",)])
    print("concept y extent (no cable):", allb[:, 1].min(), allb[:, 1].max())

    focus = ((-150, -60, -58), (72, 60, 40))
    save(title(R.render(P0, (-0.45, -0.85, 0.38), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "Narrow base concept: 82 mm wide", "Symmetrical lever, 6808 thin bearings, sensor inside the trunnion, "
               "brake shoe behind the hub"), "narrow_hero.png")
    save(title(R.render(P0, (0.75, 0.6, 0.5), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "Narrow base concept: from behind", "The brake knob on the back of the frame; the USB cable leaves "
               "through the cable cover's rim"), "narrow_rear.png")
    save(title(R.render(P32, (-0.2, -1.0, 0.25), size=(1600, 1000), focus=((-170, -60, -58), (72, 60, 100)),
                        zoom=1.0)[0], "Narrow base concept at the 32 deg up-stop",
               "The up-stop boss under the hub lands on the pedestal; the shoe stays on the hub's back"),
         "narrow_32deg.png")

    # widths: Rev 3 and the concept from above, same scale, tube pointing up the page
    old = R.base_only(R.pose(src, 0.0, tube_to=-200.0))
    view, up, fo = (0, 0, 1), (-1, 0, 0), ((-150, -70, -60), (95, 70, 45))
    ys = (-65.0, 65.0)
    img_o, px_o = R.render(old, view, up=up, size=(1000, 1250), focus=fo, parallel=True,
                           anchors=[(88, ys[0], 50), (88, ys[1], 50)])
    img_n, px_n = R.render(P0, view, up=up, size=(1000, 1250), focus=fo, parallel=True,
                           anchors=[(88, -W_HALF, 50), (88, W_HALF, 50)])
    width_bar(img_o, px_o[0][0], px_o[1][0], int(px_o[0][1]), "Rev 3: 130 mm (5.1 in)")
    width_bar(img_n, px_n[0][0], px_n[1][0], int(px_n[0][1]), "Concept: 82 mm (3.25 in)")
    both = Image.new("RGB", (2000, 1250), (255, 255, 255))
    both.paste(img_o, (0, 0))
    both.paste(img_n, (1000, 0))
    save(title(both, "Width: Rev 3 against the narrow concept, from above, to the same scale",
               "Lever symmetrical about the tube; bearings, covers and brake all inside the 82 mm"), "narrow_vs_rev3_top.png")

    # section on the pivot axis, seen from the front
    Pc = R.cut(P0, 0, 0.0, keep="above")
    img, px = R.render({k: v for k, v in Pc.items() if k not in ("carbon_tube",)}, (-1, 0, 0), size=(1600, 1100),
                       focus=((0, -45, -58), (40, 45, 40)), parallel=True, zoom=1.0,
                       anchors=[(0, -W_HALF, 33), (0, W_HALF, 33)])
    width_bar(img, px[0][0], px[1][0], int(px[0][1]) - 10, "82 mm")
    save(title(img, "Section on the pivot axis, from the front",
               "6808-2RS bearings (40 x 52 x 7). Sensor (right): the AS5600 inside the trunnion, magnet on the cover's "
               "post. USB (left): the cable turns out of the axis inside the cover"), "narrow_section_axis.png")

    # section on the tube's plane, seen from the sensor side
    Pc = R.cut(P0, 1, -0.6, keep="above")
    save(title(R.render(Pc, (0, -1, 0), size=(1700, 1000), focus=((-140, 0, -58), (72, 0, 40)), parallel=True,
                        zoom=1.0)[0], "Section on the tube's plane, from the sensor side",
               "Brake: the knob turns an M5 bolt through a captive nut and pushes the felt-faced shoe onto the hub "
               "through a spring"), "narrow_section_brake.png")


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        clashes()
    else:
        main()
