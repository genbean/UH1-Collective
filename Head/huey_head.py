# UH-1 "Huey" collective switch box, Rev 2: the real box shape, straight onto the tube.
#
# The lower box follows the real lower panel all the way round, diagonal bottom edge included: there is no box
# section under the diagonal, no head pot and no extra buttons. The box is deeper than Rev 1's (55 mm), and
# everything that joins it to the tube is inside it. The 25 x 1 aluminium tube runs up through the throttle grip and
# a short round neck into a boss moulded into the body, and an M5 bolt goes right through boss and tube. The grip
# turns on the tube; its plain upper end runs up inside the neck into the box, where a 32-tooth gear on its top drives
# a 20-tooth pinion beside the boss. The pinion turns the AS5600's magnet under the module.
#
# Everything is modelled in the MkII head frame (x across the face, y into the head, z up the tube; the face is at
# y = 0 and the tube axis at (TX, TY)). The body and panels are modelled upright in a "box frame" and tilted up by
# TILT degrees about the x axis through (y = 0, z = ZB), like the real box. The boss, neck, sensor pod and trigger
# mount are modelled in the head frame and added after the tilt. The throttle parts (grip, friction collar, pinion,
# magnet shaft) are in throttle_r2.py.
#
# usage: huey_head.py <MkII-HeadFront.stl> <out dir>      (MkII-HeadFront supplies the 4-way hat cut-out)
import os
import sys
import numpy as np
import trimesh
import manifold3d as mf
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.varLib import instancer

SEG = 96
CLR = 0.2                       # added to switch cutouts: FDM holes print undersize
WALL = 2.5
PANEL_T = 2.5                   # panels are the same thickness as the MkII face
ENGRAVE = 0.6                   # label depth
FONT = "C:/Windows/Fonts/bahnschrift.ttf"   # DIN-style; instanced to SemiBold Condensed

# Lower box: the real UH-1 lower panel is 107 x 75 mm, 50 mm high on the left with a diagonal bottom edge, and the
# box follows that outline.
X0, X1 = -48.21, 58.79          # panel left/right
ZT, ZB = 70.0, -5.0             # panel top / bottom-right; bottom-left is ZB + 25
YB = 52.5                       # inside of the rear wall: deep enough for the tube boss and the sensor inside the box
YC = YB + WALL                  # outside of the rear wall

# Upper box: 67 x 50 mm, 20 mm in from the lower box's left edge and set back 10 mm (UY). It sits on the lower box's
# top and shares its rear wall.
UX0, UX1 = X0 + 20, X0 + 87
UZ0, UZ1 = ZT, ZT + 50
UY = 10.0                       # front of the upper box; its panel is UY - 2.5 .. UY


# ---------------------------------------------------------------- helpers
def P(x, z):
    return (x, z)


def cs(pts):
    return mf.CrossSection([[tuple(map(float, p)) for p in pts]], mf.FillRule.NonZero)


def rect(x0, z0, x1, z1):
    return cs([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])


def circle(d, x=0.0, z=0.0, seg=SEG):
    return mf.CrossSection.circle(d / 2, seg).translate((x, z))


def square(side, x, y, deg):
    """Square cross-section centred on (x, y), turned deg degrees."""
    return mf.CrossSection.square((side, side), center=True).rotate(deg).translate((x, y))


def round_convex(c, r):
    return c.offset(-r, mf.JoinType.Round).offset(r, mf.JoinType.Round)


def prism(c, y0, y1):
    """Extrude a cross-section drawn in (x, z) along y from y0 to y1."""
    return mf.Manifold.extrude(c, y1 - y0).rotate((-90, 0, 0)).mirror((0, 0, 1)).translate((0, y0, 0))


def zprism(c, z0, z1):
    """Extrude a cross-section drawn in (x, y) along z from z0 to z1."""
    return mf.Manifold.extrude(c, z1 - z0).translate((0, 0, z0))


def _side(c, x0, x1):
    """Extrude a cross-section drawn in (y, z) along x from x0 to x1."""
    m = mf.Manifold.extrude(c, x1 - x0)             # (u=y, v=z, w=x)
    v = np.asarray(m.to_mesh().vert_properties)[:, :3]
    f = np.asarray(m.to_mesh().tri_verts)
    v2 = np.stack([v[:, 2] + x0, v[:, 0], v[:, 1]], 1)  # (x, y, z); a cyclic swap keeps orientation
    return mf.Manifold(mf.Mesh(vert_properties=v2.astype(np.float32), tri_verts=f.astype(np.uint32)))


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def ycyl(x, z, d, y0, y1, d1=None, seg=SEG):
    """Cylinder (or cone) along y."""
    c = mf.Manifold.cylinder(y1 - y0, d / 2, (d if d1 is None else d1) / 2, seg)   # along +z from 0
    return c.rotate((-90, 0, 0)).translate((x, y0, z))


def zcyl(x, y, d, z0, z1, seg=SEG):
    return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, seg).translate((x, y, z0))


def load(path):
    m = trimesh.load(path, process=True)
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def save(m, path):
    assert m.status() == mf.Error.NoError, (path, m.status())
    out = m.to_mesh()
    tm = trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts), process=True)
    # drop zero-volume slivers left where faces happened to coincide
    pieces = tm.split(only_watertight=False)
    if len(pieces) > 1:
        tm = trimesh.util.concatenate([q for q in pieces if len(q.faces) > 3 and abs(q.volume) > 1e-6])
    tm.export(path)
    print(f"{os.path.basename(path):34s} {m.volume() / 1000:7.1f} cm3  watertight {tm.is_watertight}  "
          f"size {np.round(tm.extents, 1).tolist()}")


# ---------------------------------------------------------------- text
class FlatPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.polys, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            a = (1 - t) ** 3
            b = 3 * (1 - t) ** 2 * t
            c = 3 * (1 - t) * t ** 2
            d = t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 7)[1:]:
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
                             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.polys.append(self.cur)
        self.cur = []


_font = instancer.instantiateVariableFont(TTFont(FONT), {"wght": 600, "wdth": 75})
_gs, _cmap, _hmtx = _font.getGlyphSet(), _font.getBestCmap(), _font["hmtx"]
_CAP = _font["OS/2"].sCapHeight


def text(s, h, x, z, anchor="c"):
    """Text with cap height h, centred (anchor 'c') on (x, z) in the panel plane, reading left to right."""
    k = h / _CAP
    polys, pen_x = [], 0.0
    for ch in s:
        g = _cmap.get(ord(ch))
        if g is None:
            continue
        pen = FlatPen(_gs)
        _gs[g].draw(pen)
        polys += [[(pen_x + px * k, py * k) for px, py in poly] for poly in pen.polys]
        pen_x += _hmtx[g][0] * k
    if not polys:
        return mf.CrossSection()
    c = mf.CrossSection(polys, mf.FillRule.NonZero)
    dx = -pen_x / 2 if anchor == "c" else 0.0
    return c.translate((x + dx, z - h / 2))


def vtext(s, h, x, ztop, step=None):
    """Letters stacked vertically, the first one at ztop."""
    step = step or h * 1.3
    c = mf.CrossSection()
    for i, ch in enumerate(s):
        c += text(ch, h, x, ztop - i * step)
    return c


def arrow(x0, x1, z, w=0.6, head=2.2):
    """Double-headed horizontal arrow."""
    shaft = rect(x0 + head, z - w / 2, x1 - head, z + w / 2)
    left = cs([(x0, z), (x0 + head * 1.4, z + head * 0.7), (x0 + head * 1.4, z - head * 0.7)])
    right = cs([(x1, z), (x1 - head * 1.4, z - head * 0.7), (x1 - head * 1.4, z + head * 0.7)])
    return shaft + left + right


# ---------------------------------------------------------------- switch cutouts (datasheet + CLR)
def toggle_cut(x, z):
    """APEM 600H toggle (679-1217/1219/1223-ND), M12 x 0.75 bushing: 12.2 mm round. The body (about 14.65 x 29.7 mm, long
    side vertical) sets the lever to throw up and down."""
    return circle(12.2 + CLR, x, z)


def large_pb_cut(x, z):
    """Same Sky PB4, M12: 12 mm with two flats 11 mm apart."""
    d = 12.0 + CLR
    return (circle(d) ^ rect(-(11.0 + 0.1) / 2, -d, (11.0 + 0.1) / 2, d)).translate((x, z))


# M3 countersunk screws (ISO 10642 / DIN 7991 / ISO 7046 heads are at most 6.72 mm across, 90 degrees): every
# countersink is a true 90 degree cone 6.9 mm across at the surface, so the head sits just below flush. The
# holes the screws thread into are 2.5 mm pilots, sized to tap M3.
CSK_D, CSK_HOLE = 6.9, 3.4
CSK_DEPTH = (CSK_D - CSK_HOLE) / 2                 # 1.75 mm


def csk(x, z, y_face, inward):
    """Countersunk M3 clearance hole through a 2.5 mm part whose outer face is at y_face; inward is +1 or -1."""
    y_in = y_face + inward * 3.0
    hole = ycyl(x, z, CSK_HOLE, min(y_face, y_in) - 1, max(y_face, y_in) + 1)
    if inward > 0:
        cone = ycyl(x, z, CSK_D + 1.0, y_face - 0.5, y_face + CSK_DEPTH, CSK_HOLE)
    else:
        cone = ycyl(x, z, CSK_HOLE, y_face - CSK_DEPTH, y_face + 0.5, CSK_D + 1.0)
    return hole + cone


# ---------------------------------------------------------------- outlines
def panel_uv(u, v):
    return (X0 + u, ZT - v)


LOWER_PANEL = round_convex(cs([panel_uv(*p) for p in [(0, 0), (107, 0), (107, 75), (82, 75), (15, 50), (0, 50)]]), 2.5)
UPPER_PANEL = round_convex(rect(UX0, UZ0, UX1, UZ1), 2.5) + rect(UX0, UZ0, UX1, UZ0 + 3)   # square where it meets the lower box

# The lower box is the lower panel's outline carried straight back to the rear wall, so the panel covers its whole
# front and the diagonal is the box's own bottom edge.
BODY = LOWER_PANEL
UPPER_IN = UPPER_PANEL + rect(UX0, UZ0, UX1, UZ0 + 5)
BACK = BODY + UPPER_IN                       # outline of the rear wall
DIAGONAL = (panel_uv(15, 50), panel_uv(82, 75))   # the bottom edge the tube comes up through, (x, z) at each end

# Panel corner screws, into columns that run back to the rear wall.
COLUMNS = [panel_uv(4.5, 4.5), panel_uv(102.5, 4.5), panel_uv(102.5, 70.5), panel_uv(4.5, 45.5)]
UPPER_COLUMNS = [(UX0 + 4.5, UZ1 - 4.5), (UX1 - 4.5, UZ1 - 4.5), (UX1 - 4.5, UZ0 + 4.5), (UX0 + 4.5, UZ0 + 4.5)]

# Each panel has a raised plug on its back that drops inside the box walls, so side knocks go into the walls
# rather than the screws. Reliefs keep it clear of the columns and the switch nuts.
PLUG_H, PLUG_CLR = 1.8, 0.25
NUT_RELIEF = {"toggle": (15.0, 30.4), "pb4": 20.0}   # the bodies sit against the panel (w x h: a rectangle)

# Switch positions (u, v from the panel's top left), after the real UH-1 panel.
GOV = panel_uv(13, 27.5)            # high enough that its APEM body clears the left column
SEARCH = panel_uv(52, 31)
LDG_EXT = panel_uv(88, 28)
STOP_REL = panel_uv(90, 60)
SL = (UX0 + 18, UZ1 - 27)
LDG_ON = (UX0 + 49, UZ1 - 27)

# Rib along the front of the upper box's floor: the upper panel's bottom edge bears on it when the panel is
# pushed in. Its back face is chamfered at 45 degrees so it prints off the floor.
RIB_D = 3.0

# MkII hat (4-way): copied from the MkII face, centred on (0, 1.15).
HAT_SRC = (0.0, 1.15)
HAT_R = 12.0

# ---- tilt
TILT = 20.0                           # the real box leans up ~20 degrees relative to the tube
TAN = np.tan(np.radians(TILT))
COS = np.cos(np.radians(TILT))
SIN = np.sin(np.radians(TILT))


def tilt(m):
    """Box frame -> head frame: rotate about the x axis through (y = 0, z = ZB), the box's bottom front edge."""
    return m.translate((0, 0, -ZB)).rotate((TILT, 0, 0)).translate((0, 0, ZB))


def untilt(m):
    return m.translate((0, 0, -ZB)).rotate((-TILT, 0, 0)).translate((0, 0, ZB))


def to_box(x, y, z):
    """A head-frame point in the box frame."""
    return x, y * COS + (z - ZB) * SIN, -y * SIN + (z - ZB) * COS + ZB


# The diagonal bottom's outside face is a plane. In the box frame it holds the y axis and the diagonal; tilted, it
# slopes 28 degrees, down to the right and toward the front.
_D0, _D1 = np.array(DIAGONAL[0]), np.array(DIAGONAL[1])
_NB = np.array([_D0[1] - _D1[1], 0.0, _D1[0] - _D0[0]])                      # box-frame normal (up and in)
_NH = np.array([_NB[0], -_NB[2] * SIN, _NB[2] * COS])                         # head-frame normal
_PH = np.array([_D0[0], -(_D0[1] - ZB) * SIN, (_D0[1] - ZB) * COS + ZB])      # a point on it, head frame


def floor_z(x, y):
    """Head-frame height of the diagonal bottom's outside face at (x, y)."""
    return _PH[2] - (_NH[0] * (x - _PH[0]) + _NH[1] * (y - _PH[1])) / _NH[2]


BIG = 300.0


def above_floor():
    """Head frame: everything above the plane of the diagonal bottom's outside face."""
    k = (_D1[1] - _D0[1]) / (_D1[0] - _D0[0])
    line = lambda x: _D0[1] + k * (x - _D0[0])
    return tilt(prism(cs([(-BIG, line(-BIG)), (BIG, line(BIG)), (BIG, 2 * BIG), (-BIG, 2 * BIG)]), -BIG, BIG))


# ---- HeliSR Rev 3.0 board (39.3 x 33.64 mm), upright on the inside of the rear wall, centred in the upper box, on four
# 4 mm round spacers (Bivar SRS-4-4MM, 6.4 mm across), one in each corner. An M3 countersunk screw from outside goes
# through the rear wall, a spacer and the board, with a nut on the board's front. Seen from the open front you look at
# the components, with the USB end down, so the Pro Micro's plug points down through WIRE_SLOT toward the tube's top
# end: J1, AX3 and AX4 up the left edge, J2, AX1 and AX2 up the right edge, and PROG4, RST and PROG1 along the top.
# The Pro Micro (19.4 mm off the rear wall, 21 mm at its USB socket) sits between the upper box's two toggles; the
# JST SR connectors along the edges are behind the toggles' solder tabs.
HELISR_SIZE = (39.3, 33.64)                     # (x_b, y_b): length, width
HELISR_X0 = (UX0 + UX1) / 2 - HELISR_SIZE[1] / 2     # x of the J1 edge: the board is centred across the upper box
HELISR_Z0 = (UZ0 + UZ1 - WALL) / 2 - HELISR_SIZE[0] / 2   # box-frame z of the USB end: centred up and down too
HELISR_STACK = 19.4                             # rear wall to the Pro Micro's front
HELISR_IN = 3.2                                 # hole centres from the two nearest edges, as in the KiCad board
HELISR_HOLES = [(HELISR_IN, HELISR_IN), (HELISR_SIZE[0] - HELISR_IN, HELISR_IN),
                (HELISR_IN, HELISR_SIZE[1] - HELISR_IN), (HELISR_SIZE[0] - HELISR_IN, HELISR_SIZE[1] - HELISR_IN)]
HELISR_MOUNTS = [(HELISR_X0 + yb, HELISR_Z0 + xb) for xb, yb in HELISR_HOLES]
# Slot through the floor between the boxes for the USB plug and all the wires from the lower box: across the upper box
# between its panel-screw columns (1 mm clear of each), and from the rear wall to 25 mm in front of it, clear of the
# plug's overmold. Its front edge is a 50 mm bridge when the body prints.
WIRE_SLOT = (UX0 + 4.5 + 3.2 + 1.0, UX1 - 4.5 - 3.2 - 1.0, YB - 25.0, YB)   # x0, x1, y0, y1


# ---------------------------------------------------------------- parts
def lower_labels():
    u = lambda a, b: panel_uv(a, b)
    h, step = 3.6, 4.5
    return (
        # GOV and RPM stacked on three rows; INCR and DECR 12 mm above and below the switch, as EXT / RETR are
        # on the LDG LT side
        # (all centred on the switch across the panel: GOV and RPM 9.5 mm either side)
        vtext("GOV", h, *u(3.5, 11.0), step=step) + vtext("RPM", h, *u(22.5, 11.0), step=step)
        + text("INCR", h, *u(13.0, 11.0 + step)) + text("DECR", h, *u(13.0, 39.5))
        + text("SEARCH CONT", h, *u(52.0, 6.5)) + text("EXT", h, *u(52.0, 11.5))
        # the L / R arrow just under the search hat (30 mm, bottom at v 46), longer than the hat is wide, with L
        # and R above its ends beside the hat and RETR under it
        + text("L", h, *u(36.0, 44.0)) + text("R", h, *u(68.0, 44.0))
        + arrow(u(33.5, 0)[0], u(70.5, 0)[0], u(0, 47.6)[1]) + text("RETR", h, *u(52.0, 51.8))
        + text("LDG LT", h, *u(88.0, 11.0)) + text("EXT", h, *u(88.0, 16.0)) + vtext("OFF", h, *u(101.0, 23.0))
        + text("RETR", h, *u(88.0, 40.0))
        # STOP and REL side by side, each centred on the STOP REL button
        + vtext("STOP", h, *u(72.5, 60.0 - 1.5 * 4.4), step=4.4) + vtext("REL", h, *u(77.5, 60.0 - 4.4), step=4.4)
    )


def upper_labels():
    h = 3.6
    ux = lambda a: UX0 + a
    uz = lambda b: UZ1 - b
    return (
        text("SL", h, ux(18), uz(7.0)) + text("ON", h, ux(18), uz(12.0)) + vtext("OFF", h, ux(28.5), uz(22.0))
        + text("STOW", h, ux(18), uz(41.0))
        + text("LDG LT", h, ux(49), uz(7.0)) + text("ON", h, ux(49), uz(12.0)) + text("OFF", h, ux(49), uz(41.0))
    )


def body():
    """Both boxes with the rear wall built in, open at the front for the panels. Box frame, without the tube boss,
    neck and sensor pod (body_rev2() adds them)."""
    lower_inner = BODY.offset(-WALL, mf.JoinType.Miter)
    upper_inner = UPPER_IN.offset(-WALL, mf.JoinType.Miter) + rect(UX0 + WALL, UZ0, UX1 - WALL, UZ0 + 5)
    b = prism(BODY, 0, YC) + prism(UPPER_IN, UY, YC)          # each runs through the rear wall: a clean union
    b -= prism(lower_inner, -1, YB) + prism(upper_inner, UY - 1, YB)

    # panel screw columns, blind at the rear wall
    for x, z in COLUMNS:
        b += ycyl(x, z, 6.4, 0, YB)
        b -= ycyl(x, z, 2.5, -1, YB - 1.0)
    for x, z in UPPER_COLUMNS:
        b += ycyl(x, z, 6.4, UY, YB)
        b -= ycyl(x, z, 2.5, UY - 1, YB - 1.0)
    # rib under the upper panel's bottom edge, the same height as the walls so the panel's plug sits on it
    rib = cs([(UY, UZ0 - 0.01), (UY + RIB_D + WALL, UZ0 - 0.01), (UY + RIB_D, UZ0 + WALL), (UY, UZ0 + WALL)])
    b += _side(rib, UX0 + WALL - 0.01, UX1 - WALL + 0.01)

    # slot through the floor between the boxes for the USB plug and the wires
    sx0, sx1, sy0, sy1 = WIRE_SLOT
    b -= box(sx0, sy0, UZ0 - WALL - 1.0, sx1, sy1, UZ0 + 0.1)
    # HeliSR board screws, from outside. The countersinks are on the face the body prints on, so each one is a
    # 45 degree overhang with nothing to bridge.
    for x, z in HELISR_MOUNTS:
        b -= csk(x, z, YC, -1)
    return b


# ---------------------------------------------------------------- Rev 2: tube boss, neck and sensor pod (head frame)
TX, TY = -1.98, 18.52            # tube axis: Rev 1's x and y. It comes up through the middle of the diagonal.
TUBE_OD = 25.0
TUBE_BORE = 25.23                # boss bore: the 25.2 bearing coupon as cut, a press fit on the tube (25.3 slides)
GEAR_M = 1.0                     # 20 degree involute spur gears
GRIP_TEETH, PINION_TEETH = 32, 20
CENTRES = GEAR_M * (GRIP_TEETH + PINION_TEETH) / 2      # 26 mm between the tube and pinion axes
SPIN = 15.0                      # the pinion's direction from the tube, degrees from +x toward the back
PX = TX + CENTRES * np.cos(np.radians(SPIN))
PY = TY + CENTRES * np.sin(np.radians(SPIN))
# The neck: a short round sleeve, about the grip's size, from the sloping bottom down to the grip. The grip's plain
# upper end (GRIP_NECK_D) runs up inside it into the box. Its bottom is level, 3 mm under the bottom's lowest point
# around it, so it shows 3 mm at the front right and 24 mm at the back left.
NECK_D, NECK_BORE = 37.8, 34.8   # the knurl is 37.1; the bore clears the 34 mm gear tips
GRIP_NECK_D = 33.4
NECK_BOT = 2.4
KNURL_TOP = NECK_BOT - 1.0       # top of the MkII grip body, 1 mm under the neck
GEAR_Z = (20.6, 25.6)            # grip gear face (5 mm): as low as the pinion pocket can sit above the box floor
CEILING = GEAR_Z[1] + 0.5        # the grip's top bears on the boss here, pushed up by the friction collar
# Throttle travel, after the real UH-1: 180 degrees from the idle stop to full open, rolling away from the pilot to
# open (clockwise looking down the tube from the head: the grip turns negative about z), and past idle a small
# spring-loaded cutoff range. The grip's 30 degree stop lug runs in a groove in the boss's ceiling, with hard stops at
# full open and at cutoff. At idle the lug's closing face, a ramp, meets the idle plunger: a pin a pen spring pushes
# down into the groove. Rolling into the cutoff range lifts it; let go and it pushes the grip back to idle.
TRAVEL, CUTOFF = 180.0, 15.0
LUG_IDLE = -97.5                 # the lug spans LUG_IDLE..LUG_IDLE + 30 at idle; the groove's solid 135 deg faces the pod
STOP_LUG = (12.85, 16.7, 30.0, 3.3)            # r0, r1, arc (deg), height
LUG_RAMP = 18.0                  # the lug's closing face ramps down over its last 18 degrees
STOP_GROOVE = (12.6, 17.0, LUG_IDLE - TRAVEL, LUG_IDLE + STOP_LUG[2] + CUTOFF, 4.0)   # r0, r1, a0, a1 (deg), depth
BOSS_D = 42.0                    # the boss around the tube, inside the box
TUBE_END = CEILING + 20.0        # the tube goes 20 mm into the boss, to a lip
BOSS_TOP = TUBE_END + 2.0
# Idle plunger, upright in the boss just past the lug's face at idle: a 2.6 mm tip through a guide into the groove,
# a 4 mm body resting on the guide's step, a pen spring, and an M5 x 5 set screw in the top of its bore.
PLUNGER_R = 15.4
PLUNGER_A = LUG_IDLE + STOP_LUG[2] + np.degrees(0.36 / PLUNGER_R)   # its round tip just touches the ramp at idle
PLX = TX + PLUNGER_R * np.cos(np.radians(PLUNGER_A))
PLY = TY + PLUNGER_R * np.sin(np.radians(PLUNGER_A))
PLUNGER_TIP = (2.6, CEILING + 0.3)            # tip diameter, its lowest point at rest
PLUNGER_STEP = CEILING + STOP_GROOVE[4] + 1.4  # the body rests on this step
PLUNGER_BODY = (4.0, 6.0)                     # body diameter, length
PLUNGER_BORE = 4.3                            # tap its top 5 mm M5 for the set screw
CABLE_D = 20.0                   # opening through the lip for the USB cable and the base sensor's lead
BOLT_Z = TUBE_END - 10.0         # M5 x 40 countersunk bolt along y through boss and tube (drill the tube 5.2 mm)
M5_HEAD_D, M5_NUT_AF, M5_NUT_T = 10.4, 8.1, 4.0
NUT_Y = (TY + TUBE_BORE / 2 + 0.6, TY + TUBE_BORE / 2 + 0.6 + M5_NUT_T + 0.4)   # nut slot, open at the boss top
PINION_Z = (GEAR_Z[0] + 0.1, GEAR_Z[1] - 0.1)    # 4.8 mm face, inside the grip gear's 5 mm
POCKET_D = 23.0                  # pinion tips are 22 mm
WEB = (CEILING, CEILING + 3.0)   # bearing web over the pinion, bored for the magnet shaft
SHAFT_D = 6.0
SHAFT_HEX = 4.5                  # the magnet shaft's hex end (across flats) presses into the pinion
CAP = (WEB[1], WEB[1] + 4.0)     # the magnet shaft's cap, resting on the web; magnet flush with its top
MAGNET = (5.0, 2.0)              # 5 x 2 mm diametric (supplied with the WWZMDiB module)
CHIP_FACE = CAP[1] + 1.5         # 1.5 mm air gap (datasheet 0.5-3 mm)
BOARD_Z = CHIP_FACE + 1.5        # module underside (SOIC-8 body 1.5 mm)
MODULE = 23.0                    # WWZMDiB AS5600 module, chip assumed centred
MODULE_ROT = SPIN               # the module's square faces the tube: its near edge is 14.2 mm from the tube's axis
POD_IN, POD_WALL, SHELF = MODULE + 0.6, 2.5, 1.5   # module shaft, its walls, the rails it rests on (near and far edges)
MODULE_SLOT = 3.0                # height of the module's way in: the board and what is on its top
MODULE_OUT = 40.0                # how far the module's way in runs toward the front, along the rails
POD_TOP = BOARD_Z + 1.6 + 1.0

# ---- starter trigger, behind the grip under the box. Its mount is a separate part: it sits against the back of the
# neck and ends level with the neck's bottom, clear of the grip. A tenon on its top locates it in a mortise in the
# sloping bottom, and one screw from below holds it up. Inside it, left to right: the screw, the starter switch (just
# above the bottom face) and the return spring beside it.
TRIG_X = (-16.5, 6.0)                 # mount width; the lugs are the outer 3 mm each side
TRIG_ARM = (45.6, 49.6)               # front and back faces (y) of the trigger's arm, 8.5 mm behind the grip
MOUNT_BACK = TRIG_ARM[0] - 1.6        # the mount's back face, where the switch and spring are
PIVOT = (MOUNT_BACK + 4.5, 16.0)      # (y, z): low enough that the trigger's head clears the sloping bottom
MOUNT_Z0 = NECK_BOT                   # the mount's bottom face, level with the neck's
TACT = (-6.0, MOUNT_Z0 + 4.2)         # (x, z) of the 6 x 6 mm tact switch (TE 1825910-6, 5 mm tall)
TACT_POCKET = 3.25                    # pocket depth: the button just touches the trigger at rest
TACT_H = 5.0                          # the switch's height to the top of its button
PULL_STOP = 0.25                      # button travel when the arm meets the pull stop: the switch's full travel
SPRING = (0.0, TACT[1] + 5.0)         # (x, z) of the return spring, beside the switch
SPRING_D = 4.2                        # spring pockets, for a pen spring up to 4 mm across
SPRING_DEPTH = (5.0, 3.0)             # pocket depths in the mount and in the trigger
PAD_DROP = 22.0                       # the finger pad starts this far under the pivot, beside the knurl's top
MOUNT_SCREW = (-12.5, 39.0)           # (x, y): M3 x 12 socket head from below, up into the body
SCREW_SEAT = 5.0                      # its head sits this far under the sloping bottom, in a counterbore
TENON = (0.0, 2.8, 39.0, 42.5, 4.0)   # x0, x1, y0, y1, height above the sloping bottom
LEADS = (38.8, 41.3)                  # (y) the switch leads' channel, up from the pocket into the box
FILL_TOP = 36.0                       # the body is solid behind the boss up to here


def sector(r0, r1, a0, a1, z0, z1, cx=TX, cy=TY, n=48):
    a = np.radians(np.linspace(a0, a1, n))
    pts = [(cx + r1 * np.cos(t), cy + r1 * np.sin(t)) for t in a] + [(cx + r0 * np.cos(t), cy + r0 * np.sin(t)) for t in a[::-1]]
    return mf.Manifold.extrude(cs(pts), z1 - z0).translate((0, 0, z0))


def lower_volume():
    """Head frame: the whole lower box, walls included, from the front face to the outside of the rear wall."""
    return tilt(prism(BODY, 0, YC))


def switch_bodies(grow=0.0):
    """Box frame: what the lower panel's switches put behind it. APEM 600H toggles 14.65 x 29.7 mm and 26 mm deep
    with their lugs straight; the PB4 is 11.85 mm across and 18.7 mm long overall; the hat's tact switches only
    put their legs a few mm behind the carrier."""
    g = grow
    t = lambda x, z: box(x - 7.35 - g, 0, z - 14.85 - g, x + 7.35 + g, 26.0 + g, z + 14.85 + g)
    return (t(*GOV) + t(*LDG_EXT) + ycyl(*STOP_REL, 12.0 + 2 * g, 0, 16.0 + g) + ycyl(*STOP_REL, 18.0 + 2 * g, 0, 3.0 + g)
            + ycyl(*SEARCH, 2 * HAT_R + 2 * g, 0, 7.0 + g))


def socket():
    """Head frame: the solid that holds the tube and the sensor. The boss, the pod beside it and the fill behind it
    stay inside the box; only the round neck shows under the sloping bottom."""
    vol = lower_volume()
    s = zcyl(TX, TY, BOSS_D, NECK_BOT, BOSS_TOP) ^ vol
    s += zcyl(TX, TY, NECK_D, NECK_BOT, CEILING)
    # The pod's walls step back from the LDG LT toggle and the STOP REL button, and its back runs into the rear wall,
    # so it prints as a column standing on the rear wall.
    pod = zprism(square(POD_IN + 2 * POD_WALL, PX, PY, MODULE_ROT), NECK_BOT, POD_TOP)
    pod = mf.Manifold.batch_hull([pod, tilt(untilt(pod).translate((0, YC, 0)))]) ^ vol
    s += pod - tilt(switch_bodies(0.5))
    # solid between the boss and the rear wall, from the boss's left side to the pod: it takes the trigger mount's
    # screw and tenon, and leaves nothing hanging over a gap when the body prints on its rear wall
    s += box(TX - BOSS_D / 2, TY, NECK_BOT, PX - POD_IN / 2 - POD_WALL + 0.5, BIG, FILL_TOP) ^ vol
    return s


def socket_cuts():
    k = zcyl(TX, TY, NECK_BORE, NECK_BOT - 1, CEILING)                   # the grip's way up through the neck
    k += zcyl(TX, TY, TUBE_BORE, CEILING - 0.1, TUBE_END)               # tube bore; the tube end stops at the lip
    k += zcyl(TX, TY, CABLE_D, TUBE_END - 0.1, BOSS_TOP + 1.0)          # cable opening through the lip
    r0, r1, a0, a1, d = STOP_GROOVE
    k += sector(r0, r1, a0, a1, CEILING - 0.1, CEILING + d, n=180)      # stop groove in the ceiling
    k += zcyl(PLX, PLY, PLUNGER_TIP[0] + 0.2, CEILING + d - 0.1, PLUNGER_STEP)   # idle plunger: tip guide,
    k += zcyl(PLX, PLY, PLUNGER_BORE, PLUNGER_STEP, BOSS_TOP + 1.0)              # and the bore for body, spring, screw
    # pinion pocket, open to the neck bore: the pinion goes up the neck and slides sideways into place
    path = (circle(POCKET_D, TX, TY) + circle(POCKET_D, PX, PY)).hull()
    k += zprism(path, GEAR_Z[0] - 0.5, CEILING)
    k += zcyl(PX, PY, SHAFT_D + 0.3, CEILING - 0.1, WEB[1] + 0.1)      # magnet shaft through the web
    # Module shaft: the module rests on two rails, along its edges nearest and furthest from the tube, with the magnet
    # shaft's cap between them. It slides in on the rails from the front (lower panel off), through a 3 mm slot in the
    # side of the boss, until it meets the pod's back wall. The pod is also open at the front over the pinion and
    # under the module, except where it joins the boss: with the body on its rear wall it prints as an open channel.
    shaft = square(POD_IN, PX, PY, MODULE_ROT)
    between = mf.CrossSection.square((POD_IN - 2 * SHELF, POD_IN), center=True).rotate(MODULE_ROT).translate((PX, PY))
    chip = mf.CrossSection.square((9.0, POD_IN), center=True).rotate(MODULE_ROT).translate((PX, PY))
    fwd = lambda c: (c + c.translate((0, -POD_IN))).hull()
    opening = zprism(fwd(between), WEB[1], BOARD_Z + 0.5) + zprism(fwd(shaft), BOARD_Z, POD_TOP + 1.0)   # cuts overlap, never just touch
    opening += zprism(fwd(circle(POCKET_D, PX, PY)), GEAR_Z[0] - 0.5, CEILING)
    k += opening - zcyl(TX, TY, BOSS_D - 0.6, NECK_BOT - 1, BOSS_TOP + 1)
    k += zprism(shaft, BOARD_Z, POD_TOP + 1.0) + zprism(between, WEB[1], BOARD_Z + 0.5)
    # The pod is open above the module, outside the boss: the magnet shaft drops in from above, and the module's wires
    # leave straight up from its pin row (slide it in with that row on the edge away from the tube). The opening stops
    # 1 mm in front of the rear wall, which leans over the pod's back.
    k += (zprism(shaft, BOARD_Z, POD_TOP + 12.0) - zcyl(TX, TY, BOSS_D - 1.0, NECK_BOT - 1, BOSS_TOP + 1))         ^ tilt(box(-BIG, -BIG, -BIG, BIG, YB - 1.0, BIG))
    a = np.radians(MODULE_ROT)
    slide = lambda c: (c + c.translate((MODULE_OUT * np.sin(a), -MODULE_OUT * np.cos(a)))).hull()
    region = zcyl(TX, TY, BOSS_D + 2.0, NECK_BOT - 1, BOSS_TOP + 1) + zprism(square(POD_IN + 2 * POD_WALL + 2.0, PX, PY, MODULE_ROT),
                                                                         NECK_BOT - 1, POD_TOP + 2)
    k += (zprism(slide(shaft), BOARD_Z, BOARD_Z + MODULE_SLOT) + zprism(slide(chip), CHIP_FACE - 0.4, BOARD_Z + 0.5)) ^ region
    # M5 cross bolt: countersunk head in the boss's front (counterbored below the curve), nut in a slot from the top
    yf = TY - BOSS_D / 2
    k += ycyl(TX, BOLT_Z, 5.4, yf - 1, NUT_Y[1] + 4.5)                 # room past the nut for the bolt's tip
    k += ycyl(TX, BOLT_Z, M5_HEAD_D + 0.2, yf - 6, yf + 1.0)
    k += ycyl(TX, BOLT_Z, M5_HEAD_D + 0.2, yf + 1.0, yf + 1.0 + (M5_HEAD_D + 0.2 - 5.4) / 2, 5.4)
    a = (M5_NUT_AF + 0.2) / 2
    nut = mf.CrossSection.circle(a / np.cos(np.pi / 6), 6).rotate(90).translate((TX, BOLT_Z))   # flats facing +-x
    k += prism(nut + rect(TX - a, BOLT_Z, TX + a, BOSS_TOP + 1.0), *NUT_Y)
    # trigger mount: screw pilot, the tenon's mortise, and the tact switch's leads up into the box
    x, y = MOUNT_SCREW
    zf = floor_z(x, y)
    k += zcyl(x, y, 2.5, zf - 1.0, zf - SCREW_SEAT + 12.5)                # M3 x 12: 7 mm into the body
    k += tenon(0.2)
    k += lead_channel()
    return k


def lead_channel():
    tx, tz = TACT
    return box(tx - 2.5, LEADS[0], tz, tx + 2.5, LEADS[1], FILL_TOP + 1.0)


def tenon(grow=0.0):
    """Head frame: the block on the trigger mount's top that fits up into the sloping bottom."""
    x0, x1, y0, y1, ht = TENON
    zs = [floor_z(x, y) for x in (x0, x1) for y in (y0, y1)]
    return box(x0 - grow, y0 - grow, min(zs) - 1.0, x1 + grow, y1 + grow, max(zs) + ht + grow)


def body_rev2():
    """Head frame: the tilted body with the boss, neck and sensor pod moulded in."""
    return tilt(body()) + socket() - socket_cuts()


def plug(opening, holes):
    """Raised locating plug on a panel back: the box opening less a clearance, with reliefs."""
    c = opening.offset(-PLUG_CLR, mf.JoinType.Miter)
    for x, z, d in holes:
        c -= rect(x - d[0] / 2, z - d[1] / 2, x + d[0] / 2, z + d[1] / 2) if isinstance(d, tuple) else circle(d, x, z)
    return c


def lower_panel(front):
    p = prism(LOWER_PANEL, -PANEL_T, 0)
    opening = BODY.offset(-WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in COLUMNS] + [(*GOV, NUT_RELIEF["toggle"]), (*LDG_EXT, NUT_RELIEF["toggle"]),
                                               (*STOP_REL, NUT_RELIEF["pb4"]), (*SEARCH, 2 * HAT_R + 1.0)]
    p += prism(plug(opening, holes), -0.01, PLUG_H)
    p -= prism(toggle_cut(*GOV) + toggle_cut(*LDG_EXT) + large_pb_cut(*STOP_REL), -PANEL_T - 1, PLUG_H + 1)
    for x, z in COLUMNS:
        p -= csk(x, z, -PANEL_T, +1)
    # MkII 4-way hat: cut-out, tact switch carrier and all, moved from the MkII face to SEARCH CONT
    sx, sz = HAT_SRC
    hat = front ^ ycyl(sx, sz, 2 * HAT_R, 0, 6.0)
    p -= ycyl(SEARCH[0], SEARCH[1], 2 * HAT_R - 0.2, -PANEL_T - 1, 0.01)   # copy overlaps the panel by 0.1
    p += hat.translate((SEARCH[0] - sx, -PANEL_T, SEARCH[1] - sz))
    return inlay(p, lower_labels(), -PANEL_T)


def upper_panel():
    p = prism(UPPER_PANEL, UY - PANEL_T, UY)
    opening = UPPER_IN.offset(-WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in UPPER_COLUMNS] + [(*SL, NUT_RELIEF["toggle"]), (*LDG_ON, NUT_RELIEF["toggle"])]
    p += prism(plug(opening, holes), UY - 0.01, UY + PLUG_H)
    p -= prism(toggle_cut(*SL) + toggle_cut(*LDG_ON), UY - PANEL_T - 1, UY + PLUG_H + 1)
    for x, z in UPPER_COLUMNS:
        p -= csk(x, z, UY - PANEL_T, +1)
    return inlay(p, upper_labels(), UY - PANEL_T)


def inlay(part, labels, y_face):
    """Split off a white text inlay that fills the engraved labels flush with the face at y_face."""
    text_body = prism(labels, y_face, y_face + ENGRAVE) ^ part
    return part - prism(labels, y_face - 1, y_face + ENGRAVE), text_body


def trigger_mount():
    """Head frame. It sits behind the neck, against it and up against the sloping bottom, and the trigger hangs from
    it behind the grip."""
    x0, x1 = TRIG_X
    py, pz = PIVOT
    z0, yb = MOUNT_Z0, MOUNT_BACK
    base = box(x0, TY, z0, x1, yb, BIG)
    # lugs run down to the base of the mount so they print standing up
    lug = mf.CrossSection.hull(rect(yb - 0.01, z0, py, pz + 5.0) + circle(9.0, py, pz))   # (y, z)
    m = base + _side(lug, x0, x0 + 3.0) + _side(lug, x1 - 3.0, x1)
    m = m - zcyl(TX, TY, NECK_D + 0.6, z0 - 1, BIG) - above_floor() + tenon()
    # pivot: clearance in the first lug, M3 pilot in the second
    m -= _side(circle(3.4, py, pz), x0 - 1, x0 + 3.01) + _side(circle(2.5, py, pz), x1 - 3.01, x1 + 1)
    # tact switch pocket (6 x 6 mm body), and a channel up from it for the leads
    tx, tz = TACT
    m -= box(tx - 3.1, yb - TACT_POCKET, tz - 3.1, tx + 3.1, yb + 0.1, tz + 3.1)
    m -= lead_channel() + box(tx - 2.5, LEADS[0], tz, tx + 2.5, LEADS[1], BIG)
    # return spring: a pen spring between this pocket and the one in the trigger holds the trigger released, against
    # its stop
    m -= ycyl(SPRING[0], SPRING[1], SPRING_D, yb - SPRING_DEPTH[0], yb + 0.1)
    # pull stop: a pad under the switch that the trigger's arm meets once the button has travelled PULL_STOP, so a
    # hard squeeze bears on the mount rather than the switch. Its face is where the arm's face is at that rotation,
    # at the pad's bottom edge, where the arm meets it first.
    th = (TRIG_ARM[0] - (yb - TACT_POCKET + TACT_H - PULL_STOP)) / (pz - TACT[1])
    d = py - TRIG_ARM[0]
    face = py - d * np.cos(th) - (pz - z0 + d * np.sin(th)) / np.cos(th) * np.sin(th)
    for xa, xb in ((x0 + 3.5, TACT[0] - 3.3), (TACT[0] + 3.3, x1 - 3.5)):    # either side of the switch
        m += box(xa, yb - 0.01, z0, xb, face, z0 + 2.0)
    # M3 socket head screw up into the body, its head in a counterbore in the bottom face
    x, y = MOUNT_SCREW
    zf = floor_z(x, y)
    m -= zcyl(x, y, 3.4, z0 - 1, zf + 1) + zcyl(x, y, 5.8, z0 - 1, zf - SCREW_SEAT)
    return m


def trigger():
    py, pz = PIVOT
    x0, x1 = TRIG_X[0] + 3.3, TRIG_X[1] - 3.3          # 0.3 mm clearance to each lug
    yb, ya = MOUNT_BACK, TRIG_ARM[0]
    head = mf.CrossSection.hull(circle(8.0, py, pz) + rect(yb + 0.05, pz + 2.0, yb + 7.0, pz + 6.5))
    zp = pz - PAD_DROP                                  # top of the finger pad
    arm = rect(TRIG_ARM[0], zp, TRIG_ARM[1], pz)
    pad = cs([(ya, zp), (ya + 1.0, zp - 22.0), (ya + 2.9, zp - 24.5), (ya + 6.4, zp - 24.0), (ya + 8.7, zp - 20.5),
              (ya + 7.4, zp - 15.0), (ya + 5.8, zp - 9.0), (ya + 4.7, zp - 4.0), (ya + 4.0, zp)])
    t = _side(round_convex(head + arm + pad, 0.8), x0, x1)
    t -= _side(circle(3.4, py, pz), x0 - 1, x1 + 1)
    # return spring pocket, facing the one in the mount
    t -= ycyl(SPRING[0], SPRING[1], SPRING_D, TRIG_ARM[0] - 1.0, TRIG_ARM[0] + SPRING_DEPTH[1])
    return t


def search_hat():
    """Huey SEARCH CONT knob: a ringed cone that slips over the top of the MkII thumbstick (any ball size;
    the caps are identical) and is glued on. z = 0 is the top of the thumbstick."""
    r_cyl, r_out = 11.15, 15.0
    pts = [(10.75, -3.0), (r_out, -3.0), (r_out, -1.5)]      # inside cone is just steeper than 45 deg
    # 45 degree cone from r_out to r = 3 with 0.5 mm wide, 0.6 mm deep rings every 2 mm
    zc = lambda r: -1.5 + (r_out - r)
    r = r_out
    while r - 2.0 > 3.0:
        pts += [(r - 1.5, zc(r - 1.5)), (r - 1.5, zc(r - 1.5) - 0.6), (r - 2.0, zc(r - 1.5) - 0.6), (r - 2.0, zc(r - 2.0))]
        r -= 2.0
    pts += [(3.0, zc(3.0)), (0.0, zc(3.0)), (0.0, zc(3.0) - 1.9), (3.0, zc(3.0) - 1.9), (r_cyl, 0.35),
            (r_cyl, -2.6)]
    prof = mf.CrossSection([pts], mf.FillRule.NonZero)
    return mf.Manifold.revolve(prof, 128)


if __name__ == "__main__":
    front_path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    front = load(front_path)
    lp, lp_text = lower_panel(front)
    up, up_text = upper_panel()
    parts = {
        "HueyHead-Body.stl": body_rev2(),
        "HueyHead-LowerPanel-Black.stl": tilt(lp),
        "HueyHead-LowerPanel-WhiteText.stl": tilt(lp_text),
        "HueyHead-UpperPanel-Black.stl": tilt(up),
        "HueyHead-UpperPanel-WhiteText.stl": tilt(up_text),
        "HueyHead-TriggerMount.stl": trigger_mount(),
        "HueyHead-Trigger.stl": trigger(),
        "HueyHead-SearchHat.stl": search_hat(),
    }
    for name, m in parts.items():
        save(m, os.path.join(out, name))
