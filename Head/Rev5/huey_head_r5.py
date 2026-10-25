# UH-1 "Huey" collective switch box, Rev 5: Rev 4 (`../Rev4`) with the box and both panels cut to the real UH-1 panel
# dimensions the user measured (lower panel 85 mm wide, 69.01 / 47.03 mm tall; upper panel 55 x 41 mm), the switches
# re-placed after the user's drawing, and every part checked for collisions by check_r5.py.
#
# The lower box follows the real lower panel all the way round, diagonal bottom edge included, 55 mm deep, with the
# upper box on top. The 25 mm tube runs up through the throttle grip into a short round neck, and an M5
# set screw in the boss's front pins it through a hole in the tube. The grip turns on the tube; a 32-tooth gear on its
# top drives a 20-tooth pinion beside the boss, which turns the AS5600's magnet under the module.
#
# Screws: all but one are from the two kits the user has, AvrestYPT countersunk M2-M5 (Amazon B0FMD5TMSH, with nuts)
# and HIQTRADEBYJJ set screws (B0DG33R714). Panels 8 x M3 x 12 countersunk into tapped pilots; HeliSR 4 x M3 x 12
# countersunk + nuts; tube 1 x M5 x 8 set screw; trigger pull stop 1 x M3 x 4 set
# screw; friction collar (throttle_r5.py) 1 x M4 x 12 countersunk + nut. The trigger pivot is 1 x M3 x 25 countersunk,
# bought separately (the user's choice; the kits stop at 20 mm).
#
# What Rev 4 changed: Rev 3's head (tube centred across the box, faux friction knob, raked starter trigger) in ONE
# piece again. The box, the neck with its friction knob, the tube boss, the tube's set screw, the grip's thrust face,
# stop groove, the gear pocket, the AS5600 pod and the trigger mount are all one print, laid on its
# rear wall like Rev 2's body. The neck, the knob and the tube bore lie about 20 degrees off horizontal that way, so
# they print on tree supports, and the 25.2 mm press-fit bore wants a test fit and a light ream. No ears, key, notch
# or screws hold anything to the box any more; the trigger and its switch, spring and pivot fit to the built-in mount.
# That mount is square to the rear wall, so it prints on the bed with the rest, and the switch's leads run up a straight round hole
# inside the head.
#
# Everything is modelled in the MkII head frame (x across the face, y into the head, z up the tube; the face is at
# y = 0 and the tube axis at (TX, TY)). The body and panels are modelled upright in a "box frame" and tilted up by
# TILT degrees about the x axis through (y = 0, z = ZB), like the real box. The neck block is modelled in the head
# frame, the trigger and its mount in the box frame. The throttle parts (grip, friction collar, pinion, magnet shaft)
# are in throttle_r5.py.
#
# usage: huey_head_r5.py <out dir>      (the 4-way hat is Hat/hat_r5.py's; no MkII file is needed any more)
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

# Lower box: the real UH-1 lower panel (measured by the user) is 85 mm wide, 69.01 mm tall on the right and 47.03 mm on
# the left. Its bottom edge runs 13 mm flat from the left corner, then a 51.8 mm diagonal, then 25 mm flat to the right
# corner. The box follows that outline. It is centred on the same tube x as Rev 4 (TX), and set at the height that puts
# the diagonal bottom under the tube about where Rev 4's was, so the neck, knob and grip keep their places on the tube.
PANEL_W, PANEL_HR, PANEL_HL = 85.0, 69.01, 47.03     # width, right and left heights
DIAG_U = (13.0, PANEL_W - 25.0)                       # the diagonal's ends, from the left edge
X0, X1 = 5.29 - PANEL_W / 2, 5.29 + PANEL_W / 2       # panel left/right (centred on Rev 4's tube x)
ZB = -2.55                      # panel bottom-right
ZT = ZB + PANEL_HR              # panel top
YB = 52.5                       # inside of the rear wall: deep enough for the tube boss and the sensor inside the box
YC = YB + WALL                  # outside of the rear wall

# Upper box: the real upper panel is 55 x 41 mm, 15 mm in from each side of the lower box. It sits on the lower box's
# top, set back UY, and shares its rear wall. UY is 5 mm (Rev 4: 10), so the upper toggles' 26 mm bodies end 2 mm clear
# of the HeliSR's Pro Micro in front of the rear wall.
UX0, UX1 = X0 + 15, X0 + 70
UZ0, UZ1 = ZT, ZT + 41
UY = 5.0                        # front of the upper box; its panel is UY - 2.5 .. UY


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
        tm = trimesh.util.concatenate([q for q in pieces if len(q.faces) > 3 and abs(q.volume) > 1e-3])
    tm.export(path)
    back = trimesh.load(path)              # the float32 STL round trip can open edges: check the file itself
    print(f"{os.path.basename(path):38s} {m.volume() / 1000:7.1f} cm3  watertight {back.is_watertight}  "
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


LOWER_PANEL = round_convex(cs([panel_uv(*p) for p in [(0, 0), (PANEL_W, 0), (PANEL_W, PANEL_HR), (DIAG_U[1], PANEL_HR),
                                                        (DIAG_U[0], PANEL_HL), (0, PANEL_HL)]]), 2.5)
UPPER_PANEL = round_convex(rect(UX0, UZ0, UX1, UZ1), 2.5) + rect(UX0, UZ0, UX1, UZ0 + 3)   # square where it meets the lower box

# The lower box is the lower panel's outline carried straight back to the rear wall, so the panel covers its whole
# front and the diagonal is the box's own bottom edge.
BODY = LOWER_PANEL
UPPER_IN = UPPER_PANEL + rect(UX0, UZ0, UX1, UZ0 + 5)
BACK = BODY + UPPER_IN                       # outline of the rear wall
DIAGONAL = (panel_uv(DIAG_U[0], PANEL_HL), panel_uv(DIAG_U[1], PANEL_HR))   # the bottom edge the tube comes up through, (x, z) at each end

# Panel corner screws, into columns that run back to the rear wall.
COLUMNS = [panel_uv(4.5, 4.5), panel_uv(PANEL_W - 4.5, 4.5), panel_uv(PANEL_W - 4.5, PANEL_HR - 4.5),
           panel_uv(4.5, PANEL_HL - 4.5)]
# The upper panel's SL toggle is only 11.2 mm in from its left edge, so its body covers that edge's two corners: the
# top-left screw moves in between the two toggles, and the bottom-left one drops to the floor, under the toggle's body.
# The middle one would run into the HeliSR board, so it stops UPPER_MID_DEPTH behind the panel, hanging from the top.
UPPER_COLUMNS = [(UX0 + 25.25, UZ1 - 4.5), (UX1 - 4.5, UZ1 - 4.5), (UX1 - 4.5, UZ0 + 3.0), (UX0 + 4.5, UZ0 + 3.0)]
UPPER_MID_DEPTH = 26.0

# Each panel has a raised plug on its back that drops inside the box walls, so side knocks go into the walls
# rather than the screws. Reliefs keep it clear of the columns and the switch nuts.
PLUG_H, PLUG_CLR = 1.8, 0.25
NUT_RELIEF = {"toggle": (15.0, 30.4), "pb4": 20.0}   # the bodies sit against the panel (w x h: a rectangle)

# Switch positions (u, v from the panel's top left), measured off the user's drawing of the real UH-1 panels. The
# search hat is 1.8 mm lower than drawn: its carrier's drum clears the lower box's top wall, and SEARCH CONT fits over
# its bezel.
GOV = panel_uv(13.9, 22.5)          # 0.5 mm right of drawn, so its body clears the top-left screw column (by 0.4 mm)
SEARCH = panel_uv(42.5, 16.0)
LDG_EXT = panel_uv(69.6, 21.5)        # 1 mm higher than drawn, to clear the AS5600 module's pin row under its lugs
STOP_REL = panel_uv(70.8, 49.9)     # in the ENGINE IDLE ring
SL = (UX0 + 11.2, UZ1 - 19.1)
LDG_ON = (UX0 + 39.3, UZ1 - 19.1)

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
HELISR_Z0 = UZ0 - 1.4                           # box-frame z of the USB end: 1.4 mm down into WIRE_SLOT, as the upper box
                                                # (38.5 mm inside) is shorter than the board (39.3)
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
def arc_text(s, h, cx, cz, r, top=True, gap=0.15):
    """Letters round a circle of radius r (to their middles) about (cx, cz), centred on its top (reading left to right,
    letters upright) or on its bottom (reading left to right, letters upright, so they run the other way round)."""
    widths = []
    for ch in s:
        g = _cmap.get(ord(ch))
        widths.append((_hmtx[g][0] * h / _CAP if g is not None else h * 0.5) + gap)
    total = sum(widths) / r                                        # radians
    c = mf.CrossSection()
    a = total / 2 if top else -total / 2
    for ch, w in zip(s, widths):
        mid = a - (w / r) / 2 if top else a + (w / r) / 2
        deg = np.degrees(mid)
        g = text(ch, h, 0.0, 0.0)
        if top:   # 0 rad is straight up; positive angles to the left
            g = g.rotate(deg).translate((cx - r * np.sin(mid), cz + r * np.cos(mid)))
            a -= w / r
        else:
            g = g.rotate(deg).translate((cx + r * np.sin(mid), cz - r * np.cos(mid)))
            a += w / r
        c += g
    return c


def lower_labels():
    u = lambda a, b: panel_uv(a, b)
    h, step = 3.0, 4.2
    gx, sx = GOV[0] - X0, SEARCH[0] - X0
    lx, px = LDG_EXT[0] - X0, STOP_REL[0] - X0
    pz = ZT - STOP_REL[1]
    return (
        # after the real panel: GOV stacked up the left edge and RPM right of the switch, INCR and DECR above and below
        vtext("GOV", h, *u(3.6, 12.5), step=5.5) + vtext("RPM", h, *u(gx + 11.2, 11.5), step=step)
        + text("INCR", h, *u(gx, 9.8)) + text("DECR", h, *u(gx, 35.3))
        + text("SEARCH CONT", 2.6, *u(sx, 2.0))
        # RETR under the hat's cap, with the L / R arrow between, longer than the cap is wide (there is no room for EXT
        # over it, under SEARCH CONT)
        + text("L", h, *u(sx - 15.0, 30.8)) + text("R", h, *u(sx + 15.0, 30.8))
        + arrow(u(sx - 17.5, 0)[0], u(sx + 17.5, 0)[0], u(0, 34.6)[1]) + text("RETR", h, *u(sx, 38.6))
        + text("LDG LT", h, *u(lx, 3.3)) + text("FWD", h, *u(lx, 7.6)) + text("DOWN", h, *u(lx, 35.3))
        + vtext("ON", h, *u(81.0, 17.5), step=step)
        # STOP and REL side by side, left of the ENGINE IDLE ring
        + vtext("STOP", h, *u(px - 23.0, 44.0), step=step) + vtext("REL", h, *u(px - 18.6, 46.1), step=step)
        + arc_text("ENGINE", 2.3, STOP_REL[0], STOP_REL[1], 8.4) + arc_text("IDLE", 2.3, STOP_REL[0], STOP_REL[1], 8.4, top=False)
    )


def upper_labels():
    h = 3.0
    ux = lambda a: UX0 + a
    uz = lambda b: UZ1 - b
    sx, lx = SL[0] - UX0, LDG_ON[0] - UX0
    return (
        text("SL", h, ux(sx), uz(4.5)) + text("ON", h, ux(sx), uz(8.6)) + text("STOW", h, ux(sx), uz(33.4))
        + text("LDG LT", h, ux(lx), uz(4.5)) + text("ON", h, ux(lx), uz(8.6)) + text("OFF", h, ux(lx), uz(33.4))
        + vtext("OFF", h, ux(26.0), uz(15.0), step=4.6)
    )


REAR_CHAMFER = 1.0                    # on the rear wall's outline: a little bigger, as the first layers' relief where the head sits on the bed


def edge_cutter(p0, p1, n1, n2, c, o0=0.25, o1=0.25):
    """A triangular prism that takes a c x c chamfer off the convex edge from p0 to p1 between faces with outward normals
    n1 and n2 (any frame). It runs o0 and o1 past the ends, so neighbouring cutters overlap."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    n1, n2 = np.asarray(n1, float), np.asarray(n2, float)
    length = np.linalg.norm(p1 - p0)
    d = (p1 - p0) / length
    t1, t2 = np.cross(n1, d), np.cross(n2, d)                     # into each face, away from the edge
    t1, t2 = t1 / np.linalg.norm(t1), t2 / np.linalg.norm(t2)
    t1, t2 = (-t1 if t1 @ n2 > 0 else t1), (-t2 if t2 @ n1 > 0 else t2)
    w = -(t1 + t2)
    w /= np.linalg.norm(w)
    v = np.cross(d, t1)
    pts = [c * t1, c * t2, w]                                      # the two chamfer points, and a point out in the air
    tri = mf.Manifold.extrude(cs([(float(q @ t1), float(q @ v)) for q in pts]), length + o0 + o1)
    return tri.transform(np.hstack([np.stack([t1, v, d], 1), (p0 - o0 * d).reshape(3, 1)]).tolist())


def rear_chamfers():
    """Box frame: cutters that chamfer every edge round the rear wall's outside face, the face the head prints on (the
    whole outline of both boxes, rounded corners included)."""
    polys = BACK.to_polygons()
    pts = np.asarray(max(polys, key=lambda q: abs(0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]))))
    if np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1]) < 0:
        pts = pts[::-1]                                            # counterclockwise: outward is to the right of each edge
    out = mf.Manifold()
    for a, b in zip(pts, np.roll(pts, -1, axis=0)):
        dx, dz = b - a
        length = np.hypot(dx, dz)
        if length < 0.05:
            continue
        out += edge_cutter((a[0], YC, a[1]), (b[0], YC, b[1]), (0.0, 1.0, 0.0), (dz / length, 0.0, -dx / length), REAR_CHAMFER)
    return out


def body():
    """Both boxes with the rear wall built in, open at the front for the panels. Box frame; body_r5() adds what the
    neck block needs."""
    lower_inner = BODY.offset(-WALL, mf.JoinType.Miter)
    upper_inner = UPPER_IN.offset(-WALL, mf.JoinType.Miter) + rect(UX0 + WALL, UZ0, UX1 - WALL, UZ0 + 5)
    b = prism(BODY, 0, YC) + prism(UPPER_IN + rect(UX0, UZ0 - 1.0, UX1, UZ0 + 1.0), UY, YC)   # each runs through the rear wall;
    # the upper box reaches 1 mm down into the lower one's top wall, so they share no faces (screw holes cross the joint)
    b -= prism(lower_inner, -1, YB) + prism(upper_inner, UY - 1, YB)

    # panel screw columns, blind at the rear wall
    for x, z in COLUMNS:
        b += ycyl(x, z, 6.4, 0, YB)
        b -= ycyl(x, z, 2.5, -1, YB - 1.0)
    for i, (x, z) in enumerate(UPPER_COLUMNS):
        y1 = UY + UPPER_MID_DEPTH if i == 0 else YB
        b += ycyl(x, z, 6.4, UY, y1)
        b -= ycyl(x, z, 2.5, UY - 1, y1 - 1.0)
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
    b -= rear_chamfers()        # every edge round the rear wall's outside face (the face it prints on)
    return b


# ---------------------------------------------------------------- neck block: tube boss, neck and sensor pod (head frame)
TX0 = -1.98                      # Rev 1's tube x (the MkII head's), 7.3 mm left of the box's centre
TX, TY = (X0 + X1) / 2, 18.52    # tube axis: centred across the lower box, as on the real UH-1; Rev 1's y
# Everything that goes with the tube moves with it: across by DX, and down by DZ, the drop of the sloping bottom over
# DX (it is a plane), so every part keeps its height above the bottom.
DX = TX - TX0
DZ = floor_z(TX, TY) - 15.944325351096401          # Rev 4's own floor_z(TX0, TY): heights above the bottom stay Rev 4's
TUBE_OD = 25.0
TUBE_BORE = 25.23                # boss bore: the 25.2 bearing coupon as cut, a press fit on the tube (25.3 slides)
GEAR_M = 1.0                     # 20 degree involute spur gears
GRIP_TEETH, PINION_TEETH = 32, 20
CENTRES = GEAR_M * (GRIP_TEETH + PINION_TEETH) / 2      # 26 mm between the tube and pinion axes
SPIN = 15.0                      # the pinion's direction from the tube, degrees from +x toward the back
PX = TX + CENTRES * np.cos(np.radians(SPIN))
PY = TY + CENTRES * np.sin(np.radians(SPIN))
# The neck: a round sleeve, about the grip's size, from the sloping bottom down through the friction knob to the grip.
# The grip's plain upper end (GRIP_NECK_D) runs up inside it into the box.
NECK_D, NECK_BORE = 37.8, 34.8   # the knurl is 37.1; the bore clears the 34 mm gear tips
GRIP_NECK_D = 33.4
# Faux friction knob, after the UH-1's (part of the head, round the neck just under the box). From the bottom up: a
# bulging wheel with KNOB_FLUTES deep round flutes cut straight down its side, leaving narrow lands between them (the
# wheel's profile and the flutes are measured off the user's own throttle_friction_knob.stl); the wheel runs out into a
# plain band, where the real one carries its THROTTLE INCREASE / FRICTION INCREASE label; and a 45 degree chamfer up into
# the neck. It doesn't turn. Its top is level, KNOB_CLR under the sloping bottom where they come closest (front right),
# so the neck shows above it, more toward the back left.
KNOB_BAND_D = 44.0
KNOB_WHEEL = [(23.3, 0.0), (24.12, 0.3), (24.85, 0.6), (25.52, 1.0), (26.4, 1.75), (27.16, 2.75), (27.62, 3.75),
              (27.87, 4.75), (27.94, 5.75), (27.82, 6.75), (27.51, 7.75), (26.97, 8.75), (26.09, 9.75), (24.55, 10.75),
              (23.3, 11.75), (22.69, 12.75), (22.4, 13.75), (22.36, 14.3)]      # (radius, height above the knob's bottom)
KNOB_D = 2 * max(r for r, _ in KNOB_WHEEL)       # across the lands
KNOB_WHEEL_H = KNOB_WHEEL[-1][1]
KNOB_FLUTES, KNOB_FLUTE_D, KNOB_FLUTE_R = 12, 11.2, 22.35   # count, width, and the radius the flute bottoms reach
KNOB_BAND = 4.7                                  # height of the plain band
KNOB_CHAMFER = (KNOB_BAND_D - NECK_D) / 2        # 45 degree chamfer from the band up into the neck
KNOB_H = KNOB_WHEEL_H + KNOB_BAND + KNOB_CHAMFER
KNOB_CLR = 1.5


def _knob_drop(r):
    """How far under the knob's top (at the neck) its top surface is at radius r."""
    rn, rb = NECK_D / 2, KNOB_BAND_D / 2
    if r <= rb:
        return r - rn
    up = [(KNOB_WHEEL[-1][0], KNOB_WHEEL[-1][1])] + [p for p in reversed(KNOB_WHEEL) if p[1] < KNOB_WHEEL[-1][1] and p[1] >= 5.75]
    rr, zz = zip(*up)
    return KNOB_H - float(np.interp(r, rr, zz)) if r > rr[0] else KNOB_CHAMFER + KNOB_BAND + (r - rb)


def _knob_top():
    best = BIG
    for t in np.radians(np.arange(0.0, 360.0, 1.0)):
        for r in np.linspace(NECK_D / 2, KNOB_D / 2, 25):
            x, y = TX + r * np.cos(t), TY + r * np.sin(t)
            f = floor_z(x, y)
            if to_box(x, y, f)[1] >= 0.0:                # under the box only
                best = min(best, f + _knob_drop(r))
    return best - KNOB_CLR


KNOB_TOP = min(_knob_top(), 16.0 + DZ - 15.0)   # where the chamfer meets the neck. Held where Rev 3's trigger mount
                                                # needed it (14 mm under that pivot); the grip's height hangs on it
NECK_BOT = KNOB_TOP - KNOB_H                     # the knob's bottom, and the neck's
KNURL_TOP = NECK_BOT - 1.0       # top of the MkII grip body, 1 mm under the neck
GEAR_Z = (20.6 + DZ, 25.6 + DZ)          # grip gear face (5 mm): as low as the pinion pocket can sit above the box floor
CEILING = GEAR_Z[1] + 0.5        # the boss's underside, over the grip's top
# The grip floats on four 24 x 2 mm nitrile O-rings (24 ID, 28 OD, metric; packs of 10). Each is stretched 4 % onto the
# 25 mm tube, which thins its section to about ORING_CS. Two ride in grooves in the grip's bore as its bearings, so the
# grip never touches the tube (throttle script). The other two are face seals round the tube: one in the friction
# collar's top pushes the grip up, and one in a groove in the ceiling pushes it down. Every groove squeezes its ring
# only lightly. The face grooves are FACE_GLAND deep, so the ring stands 0.2 mm proud and is squeezed 11 % at most,
# when the grip's top meets the ceiling.
ORING = (24.0, 2.0)              # ID, cross-section
ORING_CS = 1.96                  # on the tube
FACE_GLAND = (14.6, 1.75)        # the collar's groove: outer radius (2.1 mm wide, open to the tube: at 11 % the ring spreads to ~2.05), depth
# The ceiling's O-ring sits in CEILING_GLAND, a plain pocket round the tube, all round, with no thin walls (the body
# prints on its side). What keeps the ring from spreading out into the lug's path is GRIP_RIM, a thin wall that stands up
# from the grip's top face into the pocket, between the ring and the lug, over the gear's filled arc (throttle script):
# it prints upright, on the grip. The stop lug grows out of it.
CEILING_GLAND = (15.6, 1.75)     # outer radius (0.2 mm outside the rim), depth: the same depth as the collar's groove
GRIP_RIM = (14.6, 15.4, 1.4)     # r0, r1, height over the gear's top: 0.35 mm under the pocket's floor with the grip up
# Throttle travel, after the real UH-1: 180 degrees from the idle stop to full open, rolling away from the pilot to
# open (clockwise looking down the tube from the head: the grip turns negative about z). There is no idle return: the
# grip stays where it is left, held by the friction collar. The grip's 74 degree stop lug runs in a groove in the boss's
# ceiling; the groove's two end walls are the hard stops at idle and at full open, and the lug's 1 degree of slack
# makes the travel 181 degrees, so it is never short of 180 whatever the print does to the groove.
TRAVEL = 180.0
LUG_IDLE = -107.5                # the lug spans LUG_IDLE..LUG_IDLE + 74 at idle; the groove's solid 105 deg faces the pod
# The lug is as long and tall as the boss allows: the groove's solid part keeps about 4 mm of wall to the pinion pocket
# and the pod at one end and 2 mm to the feature at 60-65 degrees at the other, and the lug stays on the gear's filled
# teeth. Radially it is boxed in between the O-ring's lip and the neck bore it passes up through.
STOP_LUG = (GRIP_RIM[1] - 0.05, 17.15, 74.0, 5.2)    # r0 (fused to the rim), r1 (0.25 inside the neck bore), arc (deg), height: 0.3 mm under the groove's roof with the grip up
STOP_GROOVE = (STOP_LUG[0] - 0.2, 17.45, LUG_IDLE - TRAVEL, LUG_IDLE + STOP_LUG[2] + 1.0, 5.5)   # r0 (inside the O-ring pocket, so no lip), r1, a0, a1 (deg), depth
BOSS_D = 42.0                    # the boss around the tube, inside the box
TUBE_END = CEILING + 32.7        # the tube goes 32.7 mm (20 + 1/2 in) into the boss, to a lip
BOSS_TOP = CEILING + 22.0        # top of the boss, the pod and the solid behind them
TUBE_TOP = TUBE_END + 2.0        # top of the lip: the tube's bore runs past BOSS_TOP, up a column of the same boss
TALL_D = BOSS_D - 0.2            # the boss carried up, 0.1 mm in all round (the same radius leaves coincident faces)
CABLE_D = 20.0                   # opening through the lip for the USB cable and the base sensor's lead
BOLT_Z = TUBE_END - 10.0         # the tube's set screw, along y (drill the tube 5.2 mm across, 10 mm from its top)
GRUB_L = 8.0                     # M5 x 8 set screw (set-screw kit) in an M5 thread tapped in the boss's front
GRUB_TIP = TY - TUBE_OD / 2 + 0.9   # its tip, through the tube's front wall, 0.1 short of the wall's inside
# The pinion fills its 6 mm pocket to 0.2 mm off the floor and the ceiling, so it has 0.4 mm of end play (it had 1.2),
# and is the same both ways up: teeth to both faces, chamfered at the tips (throttle script). The O-rings hold the grip
# up to (at most) the ceiling, 0.5 mm over GEAR_Z, so the lower teeth reach below the grip gear's modelled bottom:
# the throttle script runs the grip's teeth further down to meet them (GEAR_DOWN).
PINION_Z = (GEAR_Z[0] - 0.3, CEILING - 0.2)     # the whole pinion
POCKET_D = 23.0                  # pinion tips are 22 mm
WEB = (CEILING, CEILING + 3.0)   # bearing web over the pinion, bored for the magnet shaft
SHAFT_D = 6.15
SHAFT_BORE = 6.3                 # the web's bore for it: 0.075 a side, like the pin's bearing hole
SHAFT_HEX = 4.5                  # the magnet shaft's hex end (across flats) presses into the pinion
CAP = (WEB[1], WEB[1] + 4.0)     # the magnet shaft's cap, resting on the web; magnet flush with its top
CAP_UP = 0.5                     # the cap is this much taller than that (throttle_r5.py): the magnet sits this much closer to the chip
MAGNET = (4.0, 2.0)              # about 4 x 2 mm diametric (supplied with the WWZMDiB module; the user measured it near 4 mm)
CHIP_FACE = CAP[1] + 1.5         # the chip's face: 1.5 mm over the cap's old top, so 1.0 mm over the magnet (datasheet 0.5-3 mm)
BOARD_Z = CHIP_FACE + 1.5        # module underside (SOIC-8 body 1.5 mm)
MODULE = 23.0                    # WWZMDiB AS5600 module, chip assumed centred
MODULE_ROT = 0.0                # the module is square to the box (Rev 4: SPIN), so its way in runs straight to the front: turned
                                # with the pinion, it would come out through the narrower box's right wall
POD_IN, POD_WALL, SHELF = MODULE + 0.6, 2.5, 1.5   # module shaft, its walls, the width of the rails and tabs
# The module sits in a groove along each side edge (near and far from the tube): a rail under the edge, a tab over it.
# It slides in chip down from the front, along its own axis, and stops against the back of the grooves with the chip
# over the magnet. Its pin row goes on the front edge, and the wires leave through the open middle.
GROOVE_H = 1.6 + 0.3             # the board is 1.6 thick
BOARD_CLR = 0.25                 # at each side edge and at the back stop
MODULE_OUT = 40.0                # how far the module's way in runs toward the front
PIN_D, PIN_BORE = 4.15, 4.3      # the magnet shaft's pin under the pinion, and its bearing hole in the pocket floor
PIN_DEPTH = 4.0                  # bearing hole depth, below the pinion pocket

# ---- starter trigger, behind the grip under the box. Its mount is part of the head and hangs from the sloping bottom
# behind the neck. The head prints on its rear wall (the plane box y = YC on the bed, box -y up), so the mount and the
# trigger are laid out in the box frame: the (y, z) below are box y and box z. Every face the trigger works against is
# square to box y and bridges between the two lugs, the lugs run back to the bed and stand on it, and nothing of the
# mount reaches past YC.
# From the front: the mount, with the starter switch in its back face, button facing back; the trigger's arm; and the
# lugs either side with the pivot through them. Pull the trigger and its arm presses the button. A grub screw through
# the arm then meets the mount: the pull stop. It is set at assembly so the switch always clicks first, whatever its
# travel and the print's tolerances, and a hard squeeze bears on the mount, not on the switch. A pen spring between
# mount and arm holds the trigger released, its tail against the mount above the pivot, the button clear of the arm.
# The switch's legs go through slots in the pocket's floor into a well, open below. The leads drop out of it into a
# groove under the mount, open below too, run along it to the right lug, which is wide enough to carry them, and go
# up one straight round hole through the lug, the sloping bottom and the solid behind the boss, out into the box. Every
# bend is in the open; the hole is one straight push, and a drill bit goes the whole way. (Straight up behind the switch there's no room: the neck's bore is
# in front and the trigger's tail behind.)
TRIG_X = (-15.5 + DX, 4.5 + DX)       # the lugs' outer faces, 20 mm apart; the pivot is an M3 x 25 countersunk from the
PIVOT_L = 25.0                        # left lug, threaded 8 mm into the right one (bought separately: the user's choice)
LUG, TRIG_CLR = 3.0, 0.3              # the left lug's thickness and the right lug's pivot length; the trigger's clearance
MOUNT_X1 = TRIG_X[1] + 7.1            # but the right lug carries on to here, round the leads' hole
PIVOT = (51.0, -1.5)                  # as far back as leaves 2.3 mm of lug behind the hole
PIVOT_D = (3.4, 2.5)                  # clearance (left lug and trigger), and the M3 pilot right through the right lug
ARM = (51.0, 55.0)                    # front and back faces of the trigger's arm, from the pivot down past the switch
HEAD_R = 3.75                         # the trigger's boss round the pivot
TOP_CLR = 1.5                         # the trigger's top runs parallel to the sloping bottom, this far under it (its front
                                      # edge rises 0.95 mm by the end of the pull)
TACT_H, TACT_BODY = 5.0, 3.6          # TE 1825910-6 (FSM4JH): base to button top 5.00, base to cover 3.61 (datasheet)
TACT_TRAVEL = (0.15, 0.45)            # its travel to the click: 0.25 mm +0.20 / -0.10 (datasheet)
REST_GAP = 0.6                        # button to arm with the trigger released, so it's never pressed at rest
MOUNT_FACE = ARM[0] - REST_GAP - (TACT_H - TACT_BODY)   # the mount's back face; the switch's cover is flush with it
UPPER_FACE = PIVOT[0] - HEAD_R - 0.5  # round the pivot the face steps forward, clear of the trigger's boss; the tail
                                      # rests against it (the return stop)
FACE_STEP = PIVOT[1] - np.sqrt(HEAD_R ** 2 - (PIVOT[0] - MOUNT_FACE - 0.4) ** 2)   # the boss clears the lower face
                                      # by 0.4 under this
TACT = (TRIG_X[1] - LUG - 0.6 - 3.15, PIVOT[1] - 9.0)   # (x, z) of the switch's centre, 9 mm under the pivot
TACT_POCKET = (6.3, 8.0)              # (x, z): the 6 mm body, and along z its leg rows (6.5 apart, kinks 7.8 across)
LEG_SLOTS = (2.6, 4.0, 2.95)          # the legs' slots through the floor: from and to |z| off the centre, and |x|
FLOOR, WELL = 1.2, 4.5                # the pocket's floor, and the well behind it for the legs and solder joints
SPRING = (TACT[0] - 6.3, TACT[1] + 2.0)   # (x, z) of the return spring, beside the switch
SPRING_D = 4.2                        # spring pockets, for a pen spring up to 4 mm across
SPRING_DEPTH = (5.0, 3.0)             # pocket depths in the mount and in the trigger
STOP_SCREW = (SPRING[0], TACT[1] - 2.6, 4.0)   # (x, z, length) of the pull stop: a kit M3 x 4 grub screw, in a
                                      # pilot through the arm (tap it M3), turned in from behind
# Where the pull stop's tip meets the mount's face, a kit M2 x 8 countersunk screw sits flush, so the set screw bears on
# steel and not on plastic: a 90 degree countersink (head, 0.2 mm clearance, and its depth) and an M2 pilot (tap it by hand)
STOP_SEAT = (4.2, 1.6, 8.5)           # countersink diameter at the face, M2 pilot diameter, pilot depth from the face
MOUNT_Z0 = TACT[1] - TACT_POCKET[1] / 2 - 1.5   # the mount's bottom; near the neck it meets the knob
KNOB_GAP = 1.0
PAD = (44.25, -17.75)                 # the finger pad's top front corner, where Rev 4's first trigger had it: its tip is
                                      # level with the grip's top
LEAD_WX = 3.3                        # the well and the groove run this far either side of the switch's centre
LEAD_GROOVE = (3.0, 3.0)              # the leads' groove under the mount: its mouth's width (y), and its depth
LEAD_HOLE = (14.2, 42.7, 0.0, 8.0, 4.0, 62.0)   # the leads' round hole, one straight bore: (x, y) where it leaves the groove
                                      # (box frame, at the mount's bottom), how far it leans toward +x and toward the rear wall
                                      # as it climbs (deg: its direction is (tan, tan, 1)), its diameter (three 30 AWG silicone
                                      # wires, or a 3.5 mm drill bit to clean it) and its length
YDIR = np.array([0.0, COS, SIN])     # box +y in the head frame
FLARE_Z = 28.2 + DZ                      # the 45 degree flare in front of the boss meets the boss's side here
PLUG_GAP = 2.25                       # the flare stops this far behind the panel's back (the panel's plug is 1.8 thick)


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


def interior(y0=-1.0, grow=0.0):
    """Head frame: the lower box's inside, from box y = y0 back to the rear wall. grow > 0 makes it overlap the walls by
    that much, so a solid cut to it fuses into them instead of sharing their faces."""
    return tilt(prism(BODY.offset(-WALL + grow, mf.JoinType.Miter), y0, YB + grow))


def walls(y0=0.0):
    """Head frame: the lower box's walls, the sloping bottom included, from box y = y0 to the outside of the rear wall."""
    return tilt(prism(BODY, y0, YC)) - interior(y0 - 1.0)


def by(y0, y1=BIG):
    """Head frame: everything from box y = y0 to y1."""
    return tilt(box(-BIG, y0, -BIG, BIG, y1, BIG))


def sweep(m, d=80.0):
    """m and everything it passes through on its way in along box y, from d mm in front."""
    return mf.Manifold.batch_hull([m, m.translate(tuple(-d * YDIR))])


def axis_cyl(p, d, a, l0, l1, d1=None, seg=48):
    """A cylinder (or a cone from d to d1) along the direction a, from p + l0 a to p + l1 a. Any frame."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    c = mf.Manifold.cylinder(l1 - l0, d / 2, (d if d1 is None else d1) / 2, seg)
    z = np.array([0.0, 0.0, 1.0])
    v, cth = np.cross(z, a), z @ a
    s = np.linalg.norm(v)
    if s < 1e-9:
        R = np.eye(3) if cth > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * ((1 - cth) / s ** 2)
    return c.transform(np.hstack([R, (np.asarray(p, float) + l0 * a).reshape(3, 1)]).tolist())


def bottom_zb(x):
    """Box frame: height of the bottom's outside face at x."""
    (x0, z0), (x1, z1) = DIAGONAL
    return z0 if x < x0 else z1 if x > x1 else z0 + (z1 - z0) * (x - x0) / (x1 - x0)


def bottom_normal(x):
    """Box frame: the bottom's inward normal at x: the diagonal's, or straight up under the level parts either side."""
    (x0, _), (x1, _) = DIAGONAL
    return _NB / np.linalg.norm(_NB) if x0 <= x <= x1 else np.array([0.0, 0.0, 1.0])


def neck_cyl(grow=0.0):
    """The neck's outside, carried up into the boss and stopped at the rear wall, which leans over its top. Grown, it
    is what the notch in the bottom has to let through."""
    return zcyl(TX, TY, NECK_D + 2 * grow, NECK_BOT - (1.0 if grow else 0.0), BOSS_TOP) ^ by(-BIG, YB - (0.3 if grow else 0.0))


def flare():
    """A 45 degree skirt in front of the boss, down to the sloping bottom (in Rev 3 it carried the neck block's key). It
    stops PLUG_GAP behind the panel."""
    cone = mf.Manifold.cylinder(FLARE_Z + 40.0, BOSS_D / 2 + FLARE_Z + 40.0, BOSS_D / 2, 128).translate((TX, TY, -40.0))
    return cone ^ sweep(zcyl(TX, TY, BOSS_D, -40.0, FLARE_Z)) ^ by(PLUG_GAP) ^ interior(grow=0.02)


def neck_solid():
    """Head frame. Rev 3's neck block, as part of the box: the boss, the pod beside it and the solid behind them fill
    the lower box up to the top of the boss, on the sloping bottom and against the rear wall, with the 45 degree flare in
    front of the boss, and the neck and friction knob under the box. Cut by neck_cuts() in body_r5()."""
    inner = interior(grow=0.02)
    boss = zcyl(TX, TY, BOSS_D, NECK_BOT, BOSS_TOP) ^ by(PLUG_GAP)   # not past the flare's face: it grazed it by 0.25 mm
    pod = zprism(square(POD_IN + 2 * POD_WALL, PX, PY, MODULE_ROT), NECK_BOT, BOSS_TOP)
    pod = mf.Manifold.batch_hull([pod, tilt(untilt(pod).translate((0, YC, 0)))])     # its walls run back to the rear wall
    fill = box(TX - BOSS_D / 2, TY, NECK_BOT, PX - POD_IN / 2 - POD_WALL + 0.5, BIG, BOSS_TOP)   # solid behind the boss
    n = ((boss + pod + fill) ^ inner) + flare() + neck_cyl()
    column = zcyl(TX, TY, TALL_D, BOSS_TOP - 1.0, TUBE_TOP) ^ inner         # the tube's extra depth
    n = (((n ^ box(-BIG, -BIG, -BIG, BIG, BIG, BOSS_TOP + 0.01)) + column)) - tilt(switch_bodies(0.5))   # clear of the panel's switches
    return n + friction_knob()


def module_xs(u0, u1, v0, v1):
    """Cross-section in the module's own frame (u out from the tube, v toward the back), centred on the pinion."""
    return mf.CrossSection.square((u1 - u0, v1 - v0)).translate((u0, v0)).rotate(MODULE_ROT).translate((PX, PY))


def module_seat():
    """The module's grooves and their way in from the front, and the open middle, from the web up."""
    m = MODULE / 2
    a = np.radians(MODULE_ROT)
    out = (MODULE_OUT * np.sin(a), -MODULE_OUT * np.cos(a))          # toward the front, along the module's axis
    swept = lambda c: (c + c.translate(out)).hull()
    mid = module_xs(-(m - SHELF), m - SHELF, -m - BOARD_CLR, m + BOARD_CLR)        # between the rails, and the tabs
    board = module_xs(-m - BOARD_CLR, m + BOARD_CLR, -m - BOARD_CLR, m + BOARD_CLR)
    k = zprism(mid, WEB[1], BOSS_TOP + 1.0)                     # magnet shaft in from the top, wires out
    k += zprism(swept(mid), CHIP_FACE - 0.4, BOSS_TOP + 1.0)   # the front is open from the chip's level up
    k += zprism(swept(board), BOARD_Z, BOARD_Z + GROOVE_H)      # the grooves; the board stops at their back ends
    return k


def neck_cuts():
    k = zcyl(TX, TY, NECK_BORE, NECK_BOT - 1, CEILING)                   # the grip's way up through the neck
    k += zcyl(TX, TY, TUBE_BORE, CEILING - 0.1, TUBE_END)               # tube bore; the tube end stops at the lip
    k += zcyl(TX, TY, CABLE_D, TUBE_END - 0.1, TUBE_TOP + 1.0)          # cable opening through the lip
    r0, r1, a0, a1, d = STOP_GROOVE
    k += sector(r0, r1, a0, a1, CEILING - 0.1, CEILING + d, n=180)      # stop groove in the ceiling
    k += zcyl(TX, TY, 2 * CEILING_GLAND[0], CEILING - 0.1, CEILING + CEILING_GLAND[1])   # the top O-ring's pocket, open to the tube
    # pinion pocket, open to the neck bore: the pinion goes up the neck and slides sideways into place
    path = (circle(POCKET_D, TX, TY) + circle(POCKET_D, PX, PY)).hull()
    k += zprism(path, GEAR_Z[0] - 0.5, CEILING)
    k += zcyl(PX, PY, SHAFT_BORE, CEILING - 0.1, WEB[1] + 0.1)      # magnet shaft through the web
    zp = GEAR_Z[0] - 0.5                                                # bearing hole for the shaft's pin, with a lead-in
    k += zcyl(PX, PY, PIN_BORE, zp - PIN_DEPTH, zp + 0.1)
    k += mf.Manifold.cylinder(0.7, PIN_BORE / 2, PIN_BORE / 2 + 0.7, SEG).translate((PX, PY, zp - 0.6))
    k += module_seat()
    # The tube's set screw: an M5 pilot (4.2 mm, tap it M5) from the boss's front into the bore. The screw goes in with
    # the lower panel off and its tip pins the tube through the front wall's hole; the tube is pressed in as well.
    k += ycyl(TX, BOLT_Z, 4.2, TY - BOSS_D / 2 - 3.0, TY - TUBE_BORE / 2 + 0.3)
    return k


def lead_path():
    """Head frame: the starter switch's leads, drawn in the box frame. The well behind the switch's pocket; the groove
    under the mount, which the well opens into, along to the lug; and one straight round hole, up from the groove's end
    through the lug, the sloping bottom and the solid behind the boss, out into the box. The hole leans a little as it
    climbs (LEAD_HOLE), which keeps 1.2 mm of wall to the neck's bore, the sensor seat and the rear wall's outside all the way. The groove prints on its side, so its roof slopes at 45 degrees: 3 mm wide at its mouth, wider inside."""
    tx, tz = TACT
    hx, hy, lx, ly, hd, hl = LEAD_HOLE
    w, d = LEAD_GROOVE
    yb = MOUNT_FACE - TACT_BODY - FLOOR                                  # the well's back
    h = TACT_POCKET[1] / 2 + 0.1
    well = box(tx - LEAD_WX, yb - WELL, tz - h, tx + LEAD_WX, yb + 0.1, tz + h)
    z0 = MOUNT_Z0 - 0.5
    sec = cs([(yb - w, z0), (yb, z0), (yb, MOUNT_Z0 + d), (yb - w - (d + 0.5), MOUNT_Z0 + d)])   # (y, z)
    groove = _side(sec, tx - LEAD_WX, hx + hd / 2 + 0.3)
    dv = np.array([np.tan(np.radians(lx)), np.tan(np.radians(ly)), 1.0])
    dv /= np.linalg.norm(dv)
    ax = np.cross([0.0, 0.0, 1.0], dv)                                  # the rotation taking z to the hole's direction
    ang = np.degrees(np.arctan2(np.linalg.norm(ax), dv[2]))
    ax /= np.linalg.norm(ax)
    kx = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    rot = np.eye(3) + np.sin(np.radians(ang)) * kx + (1 - np.cos(np.radians(ang))) * kx @ kx
    hole = mf.Manifold.cylinder(hl + 3.0, hd / 2, hd / 2, 64).translate((0, 0, -3.0)).transform(
        np.hstack([rot, np.array([[hx], [hy], [MOUNT_Z0 + 1.0]])]).tolist())   # starts 3 mm down in the groove
    return tilt(well + groove + hole)


def body_r5():
    """Head frame: the one-piece head: the box, the neck block's solid with the friction knob, and the trigger mount,
    then the neck block's cuts (neck and tube bores, gear pocket, AS5600 seat, set screw) and the
    starter's leads."""
    return (tilt(body()) + neck_solid() + trigger_mount()) - neck_cuts() - lead_path()


def seat_coupon():
    """An 8 mm slice of the head across the AS5600's grooves, rails, tabs and pod walls, to try the module in before
    printing the whole head. The top 1.2 mm of the bearing web holds the two sides at their spacing."""
    m = MODULE / 2
    c = module_xs(-m - POD_WALL - 4.0, m + POD_WALL + 4.0, -4.0, 4.0)
    return body_r5() ^ zprism(c, WEB[1] - 1.2, BOARD_Z + GROOVE_H + 2.5)


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


def under_bottom(d):
    """Box frame: everything under the sloping bottom's outside face moved up by d. (The trigger and its mount are well
    inside the diagonal's ends.)"""
    (xa, za), (xb, zb) = DIAGONAL
    line = lambda x: za + (zb - za) * (x - xa) / (xb - xa) + d
    return prism(cs([(-BIG, line(-BIG)), (BIG, line(BIG)), (BIG, -BIG), (-BIG, -BIG)]), -BIG, BIG)


def xcyl(y, z, d, x0, x1, d1=None):
    """Box or head frame: a cylinder (or a cone from d to d1) along x."""
    return mf.Manifold.cylinder(x1 - x0, d / 2, (d if d1 is None else d1) / 2, SEG).rotate((0, 90, 0)).translate((x0, y, z))


def _knob_outline(z0, rin):
    """(radius, z) points of the knob's outline, unfluted, from the bottom on the inside round to the top on the inside."""
    zw = z0 + KNOB_WHEEL_H
    rb, rn = KNOB_BAND_D / 2, NECK_D / 2
    return [(rin, z0)] + [(r, z0 + z) for r, z in KNOB_WHEEL] + [(rb, zw + KNOB_WHEEL[-1][0] - rb), (rb, zw + KNOB_BAND), (rn, KNOB_TOP), (rin, KNOB_TOP)]


def knob_envelope(grow):
    """Head frame: the friction knob's outline without its flutes, grown by grow."""
    prof = cs(_knob_outline(NECK_BOT, 0.0))
    prof = prof.offset(grow, mf.JoinType.Round) ^ rect(0.0, -BIG, BIG, BIG)
    return mf.Manifold.revolve(prof, 180).translate((TX, TY, 0.0))


CHAMFER = 0.8                         # on every edge that is outside the body and could be handled


def _wedge(sp, sq, p, q, c, e=1.0):
    """Cross-section of what a c x c chamfer takes off the corner at (p, q) of a solid lying toward (sp, sq)."""
    return cs([(p + sp * c, q), (p, q + sq * c), (p - sp * e, q + sq * c), (p - sp * e, q - sq * e), (p + sp * c, q - sq * e)])


def mount_chamfers():
    """Box frame: cutters that chamfer the mount's outside edges: along its bottom face, the lugs' back faces and the
    step in its back face, and the lugs' back corners. They stop under the bottom."""
    x0, x1 = TRIG_X
    c = CHAMFER
    k = mf.Manifold()
    for x, sp in ((x0, 1), (MOUNT_X1, -1)):                              # bottom face, along y
        k += prism(_wedge(sp, 1, x, MOUNT_Z0, c), 25.0, YC + 1.0)
    for x, sp in ((x0 + LUG, -1), (x1 - LUG, 1)):                        # the lugs' inner sides, behind the faces
        k += prism(_wedge(sp, 1, x, MOUNT_Z0, c), MOUNT_FACE, YC + 1.0)
    for xa, xb in ((x0, x0 + LUG), (x1 - LUG, MOUNT_X1)):                # the lugs' back ends (the bed), along x
        k += _side(_wedge(-1, 1, YC, MOUNT_Z0, c), xa - 1.0, xb + 1.0)
    k += _side(_wedge(-1, 1, MOUNT_FACE, MOUNT_Z0, c), x0 + LUG, x1 - LUG)   # the back face between the lugs
    k += _side(_wedge(-1, -1, MOUNT_FACE, FACE_STEP, c), x0 + LUG, x1 - LUG)   # and its step
    z = mf.Manifold()
    for x, sp in ((x0, 1), (x0 + LUG, -1), (x1 - LUG, 1), (MOUNT_X1, -1)):   # the lugs' back corners, along z
        z += zprism(_wedge(sp, -1, x, YC, c), MOUNT_Z0 - 1.0, 40.0)
    return k + (z ^ under_bottom(-0.3))


def trigger_mount():
    """Head frame. Part of the one-piece head: it hangs from the sloping bottom behind the neck, fused into the neck and
    0.5 mm into the bottom, solid with the friction knob, and the trigger hangs from it behind the grip. Drawn
    in the box frame (see the constants)."""
    x0, x1 = TRIG_X
    py, pz = PIVOT
    tx, tz = TACT
    top = 40.0                                                          # trimmed to the bottom below
    # the block in front of the faces, from inside the neck back; its face steps forward round the pivot
    m = box(x0, 25.0, MOUNT_Z0, MOUNT_X1, UPPER_FACE, top) + box(x0, 25.0, MOUNT_Z0, MOUNT_X1, MOUNT_FACE, FACE_STEP)
    # the lugs, back to the plane of the rear wall's outside (the bed); the right one wide enough for the leads' hole
    m += box(x0, UPPER_FACE - 0.01, MOUNT_Z0, x0 + LUG, YC, top) + box(x1 - LUG, UPPER_FACE - 0.01, MOUNT_Z0, MOUNT_X1, YC, top)
    m ^= under_bottom(0.5)
    m -= mount_chamfers()
    # pivot: an M3 x 25 countersunk screw from the left lug's outside, through the trigger, into a pilot right through
    # the right lug; it threads in 8 mm and its tip stays 0.9 mm inside
    m -= xcyl(py, pz, CSK_D + 1.0, x0 - 0.5, x0 + CSK_DEPTH, CSK_HOLE) + xcyl(py, pz, PIVOT_D[0], x0 - 1.0, x0 + LUG + 0.01)
    m -= xcyl(py, pz, PIVOT_D[1], x1 - LUG - 0.01, MOUNT_X1 + 1.0)
    # the switch's pocket, its cover flush with the face, and the slots through its floor for the two rows of legs
    yp = MOUNT_FACE - TACT_BODY
    m -= box(tx - TACT_POCKET[0] / 2, yp, tz - TACT_POCKET[1] / 2, tx + TACT_POCKET[0] / 2, MOUNT_FACE + 0.1,
             tz + TACT_POCKET[1] / 2)
    s0, s1, sx = LEG_SLOTS
    m -= box(tx - sx, yp - FLOOR - 0.1, tz + s0, tx + sx, yp + 0.1, tz + s1)
    m -= box(tx - sx, yp - FLOOR - 0.1, tz - s1, tx + sx, yp + 0.1, tz - s0)
    # return spring: a pen spring between this pocket and the one in the trigger holds the trigger released
    m -= ycyl(SPRING[0], SPRING[1], SPRING_D, MOUNT_FACE - SPRING_DEPTH[0], MOUNT_FACE + 0.1)
    # the pull stop's seat: the stop screw's tip meets the face here; a countersunk M2 screw in this hole sits flush
    cd, pd, pdepth = STOP_SEAT
    sx, sz = STOP_SCREW[0], STOP_SCREW[1]
    m -= ycyl(sx, sz, pd, MOUNT_FACE - pdepth, MOUNT_FACE + 0.1)
    m -= ycyl(sx, sz, pd, MOUNT_FACE - cd / 2 + pd / 2, MOUNT_FACE + 0.5, cd + 1.0)
    return tilt(m)                                     # solid with the friction knob where they meet: no gap


def trigger():
    """Head frame, drawn in the box frame. It prints on either flat side."""
    py, pz = PIVOT
    x0, x1 = TRIG_X[0] + LUG + TRIG_CLR, TRIG_X[1] - LUG - TRIG_CLR
    ya, yb = ARM
    px, pzz = PAD
    tail = rect(UPPER_FACE, pz + 1.5, py + 1.0, pz + 8.0)          # its front against the mount: the return stop
    head = mf.CrossSection.hull(circle(2 * HEAD_R, py, pz) + tail)
    jz = MOUNT_Z0 - 1.5                                             # the arm runs straight down past the mount's bottom,
    arm = rect(ya, jz, yb, pz)
    link = mf.CrossSection.hull(rect(ya, jz - 4.0, yb, jz) + rect(px, pzz - 1.0, px + 4.0, pzz))   # forward under it,
    pad = cs([(px, pzz), (px + 1.0, pzz - 22.0), (px + 2.9, pzz - 24.5), (px + 6.4, pzz - 24.0),    # to the finger pad
              (px + 8.7, pzz - 20.5), (px + 7.4, pzz - 15.0), (px + 5.8, pzz - 9.0), (px + 4.7, pzz - 4.0), (px + 4.0, pzz)])
    sec = round_convex(head + arm + link + pad, 0.8)
    n = 4
    t = _side(sec.offset(-CHAMFER, mf.JoinType.Round), x0, x1)
    for i in range(n):
        d = CHAMFER * (1 - (i + 0.5) / n)                      # 45 degrees: each layer is this much smaller than the section
        w = CHAMFER / n
        t += _side(sec.offset(-d, mf.JoinType.Round), x0 + i * w, x0 + (i + 1) * w + 0.01)
        t += _side(sec.offset(-d, mf.JoinType.Round), x1 - (i + 1) * w - 0.01, x1 - i * w)
    t += _side(sec, x0 + CHAMFER, x1 - CHAMFER)
    t = t ^ under_bottom(-TOP_CLR)
    t -= xcyl(py, pz, PIVOT_D[0], x0 - 1.0, x1 + 1.0)
    # return spring pocket, facing the one in the mount; the pull stop's pilot, right through the arm
    t -= ycyl(SPRING[0], SPRING[1], SPRING_D, ya - 1.0, ya + SPRING_DEPTH[1])
    t -= ycyl(STOP_SCREW[0], STOP_SCREW[1], 2.5, ya - 1.0, yb + 1.0)
    return tilt(t)


def friction_knob():
    """Head frame: the faux friction knob, part of the head: a bulging wheel with KNOB_FLUTES round flutes cut down its
    side, a plain band and the chamfer up into the neck (see KNOB_WHEEL)."""
    ri = NECK_BORE / 2 + 0.5                            # inside the neck's wall, to fuse
    z0 = NECK_BOT
    pts = _knob_outline(z0, ri)
    pts[-2] = (NECK_D / 2 - 0.3, KNOB_TOP + 0.3)
    pts[-1] = (ri, KNOB_TOP + 0.3)
    k = mf.Manifold.revolve(cs(pts), 180).translate((TX, TY, 0.0))
    fr = KNOB_FLUTE_D / 2
    rc = KNOB_FLUTE_R + fr                              # the flutes' axes: their bottoms reach KNOB_FLUTE_R
    flute = mf.Manifold.cylinder(KNOB_WHEEL_H + 2.0, fr, fr, 64).translate((0, 0, -1.0))
    for a in np.radians(np.arange(KNOB_FLUTES) * 360.0 / KNOB_FLUTES):
        k -= flute.translate((TX + rc * np.cos(a), TY + rc * np.sin(a), z0))
    return k


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
    out = sys.argv[-1]
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Hat"))
    import hat_r5                                     # the new SEARCH CONT hat: panel carrier, bezel, rocker plate, cap, legs
    lp, lp_text = hat_r5.lower_panel_new()
    up, up_text = upper_panel()
    parts = {
        "HueyHeadR5-Body.stl": body_r5(),
        "HueyHeadR5-LowerPanel-Black.stl": tilt(lp),
        "HueyHeadR5-LowerPanel-WhiteText.stl": tilt(lp_text),
        "HueyHeadR5-UpperPanel-Black.stl": tilt(up),
        "HueyHeadR5-UpperPanel-WhiteText.stl": tilt(up_text),
        "HueyHeadR5-Trigger.stl": trigger(),
        "HueyHeadR5-SensorSeatCoupon.stl": seat_coupon(),
    }
    for name, m in parts.items():
        save(m, os.path.join(out, name))
    hat_r5.write_hat_parts(out)
