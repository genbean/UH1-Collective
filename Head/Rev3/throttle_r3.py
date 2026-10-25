# Rev 3 throttle: grip, friction collar, pinion and magnet shaft, in the head frame (huey_head_r3.py's layout). The
# same parts as Rev 2's, except the magnet shaft: a pin under its hex end now runs through the pinion into a bearing hole
# in the neck block's pocket floor, so the pinion turns on two bearings instead of one 3 mm web.
#
# The grip floats on O-rings (huey_head's ORING): two in grooves in its bore, near each end, are its bearings on the
# tube, and the bore itself (BEARING_D) stays clear of the tube; the friction collar's O-ring pushes it up and the
# ceiling's pushes it down. Its
# body is the whole 120 mm MkII grip, so the hand has the same length to hold, with the old top cap bored out to the
# tube; it ends just under the head's round neck. Above it a plain 33.4 mm section
# runs up inside the neck into the box, and on top of it are a 32-tooth, module 1 spur gear and a 74 degree stop lug
# that runs in a groove in the boss's ceiling: 180 degrees from idle to full open, as on the real UH-1, with no idle
# return: the grip stays where it is left. The gear drives a
# 20-tooth pinion beside the boss (1.6:1, so the grip's 180 degrees are 288 degrees at the magnet). The magnet shaft drops through
# the bearing web over the pinion and presses into the pinion's hex hole; its cap rests on the web and holds the
# magnet 1.0 mm under the AS5600 module's chip (cap 0.5 mm taller than the first print).
#
# Below the grip, a split friction collar clamps to the tube. The O-ring in its top face presses the grip up against the
# ceiling's O-ring: slide it up for more friction and tighten its M4 pinch screw.
#
# Needs cadquery, numpy, trimesh and manifold3d. usage: throttle_r3.py <MkII-Grip-bore-relieved-25mm.stl> <out dir>
import os
import sys
import numpy as np
import cadquery as cq
import trimesh
import manifold3d as mf
import huey_head_r3 as h

V = cq.Vector
KNURL_SRC = 120.0                       # the MkII grip's top, its own z = 120: all of it is kept
TUBE_T = (h.TX, h.TY, h.KNURL_TOP - KNURL_SRC)   # MkII tube-frame parts (the knurled grip) -> head frame
GRIP_BORE = 24.6                        # construction bore, under every bearing size: BEARING_D sets the real one
# The grip's bore is BEARING_D at its two ends, where the relieved MkII grip's bearings were: the MkII's bottom 21 mm and
# the top 22 mm (under and through the gear), and everything between is relieved to GRIP_RELIEF, with short tapers like
# the MkII's. Each end carries an O-ring in a RADIAL_GLAND; the bore round them clears the tube (it prints about 0.25 mm
# under size, so 25.8 leaves about 0.25 mm a side) and only catches the grip if it is pushed hard sideways.
BEARING_D = 25.8
# Radial O-ring grooves (the ring stretched on the tube spans r 12.5..14.46): outer radius and width, and where they sit:
# the bottom groove's floor GLAND_UP over the grip's bottom face, the top groove's roof GLAND_UNDER_GEAR under the gear.
# The outer radius squeezes the ring about 8 % if the groove prints 0.1 mm under size (as holes here do), 3 % if exact.
# The roof is a 45 degree cone in to the bore, so the groove prints upright with no overhang.
RADIAL_GLAND = (14.4, 2.1)              # 2.1 wide: at this squeeze the 2 mm ring spreads to about 2.05
GLAND_UP, GLAND_UNDER_GEAR = 4.0, 6.3
COUPON_SIZES = (25.0, 25.1, 25.2, 25.3)   # second round; the first set was 25.4 to 26.0, and 25.4 was still loose
COUPON_H, COUPON_WALL = 8.0, 2.0        # just long and stiff enough to judge the fit: about 1.3 cm3 a ring
BEARING_EPS = 0.03                      # the bore is cut this much over size, grip and coupons alike, so it never lands
                                        # on the MkII mesh's own polygonal bore
GRIP_RELIEF = 26.6                      # over the MkII's own 26 mm relief, so the two never coincide
RELIEF_FROM = 25.0                      # the MkII grip's own z where its bottom bearing's taper ends
TOP_BEARING = 22.0
# The MkII grip's bottom end is rounded about R6, leaving a flat only 28 mm across, so the O-ring rode on the curve.
# Its bottom GRIP_BAND mm are rebuilt as a plain band at the knurl's tip radius with only a GRIP_END_R round, flat out to
# 32.2 mm: more than the collar's 29.9 mm O-ring groove.
GRIP_OD = 37.1                          # the MkII knurl's tips (r 18.55); the collar is just under it
GRIP_END_R = 2.5
GRIP_BAND = 3.5
BACKLASH = 0.1                          # taken off each tooth's thickness at the pitch circle
FRICTION = dict(od=37.0, h=12.0, bore=25.3, gap=0.2, slot=1.5, edge_r=1.0)   # its O-ring groove is huey_head's FACE_GLAND


def cyl(r, z0, z1, x=h.TX, y=h.TY):
    return cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def hex_prism(af, z0, z1, x, y):
    return cq.Workplane("XY", origin=(x, y, z0)).polygon(6, af / np.cos(np.pi / 6)).extrude(z1 - z0).val()


def gear_profile(m, z, backlash=BACKLASH, alpha=20.0, n_inv=12, n_arc=4):
    """Closed 2D outline of a standard involute spur gear centred on the origin."""
    a = np.radians(alpha)
    r = m * z / 2
    rb, ra, rf = r * np.cos(a), r + m, r - 1.25 * m
    inv = lambda t: np.tan(t) - t
    half = (np.pi * m / 2 - backlash) / (2 * r)                 # half tooth angle at the pitch circle
    phi = lambda rho: half + inv(a) - inv(np.arccos(min(1.0, rb / rho)))   # half angle at radius rho
    r_start = max(rb, rf)
    radii = np.linspace(r_start, ra, n_inv)
    pts = []
    for i in range(z):
        c = 2 * np.pi * i / z
        flank = [(rho, phi(rho)) for rho in radii]
        if rf < rb:
            flank = [(rf, phi(rb))] + flank
        right = [(rho * np.cos(c - p), rho * np.sin(c - p)) for rho, p in flank]                  # root -> tip
        tip = [(ra * np.cos(t), ra * np.sin(t)) for t in np.linspace(c - phi(ra), c + phi(ra), n_arc)[1:-1]]
        left = [(rho * np.cos(c + p), rho * np.sin(c + p)) for rho, p in flank[::-1]]           # tip -> root
        nxt = 2 * np.pi * (i + 1) / z
        a0, a1 = c + flank[0][1], nxt - flank[0][1]
        root = [(rf * np.cos(t), rf * np.sin(t)) for t in np.linspace(a0, a1, n_arc + 2)[1:-1]]
        pts += right + tip + left + root
    return pts


def gear_solid(m, z, z0, z1, cx, cy, rot=0.0):
    pts = gear_profile(m, z)
    g = cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).val()
    return g.rotate(V(0, 0, 0), V(0, 0, 1), rot).translate(V(cx, cy, z0))


def sector(r0, r1, a0, a1, z0, z1, cx=h.TX, cy=h.TY):
    wp = cq.Workplane("XY").workplane(offset=z0).center(cx, cy)
    p = lambda r, a: (r * np.cos(np.radians(a)), r * np.sin(np.radians(a)))
    w = (wp.moveTo(*p(r0, a0)).lineTo(*p(r1, a0)).threePointArc(p(r1, (a0 + a1) / 2), p(r1, a1))
         .lineTo(*p(r0, a1)).threePointArc(p(r0, (a0 + a1) / 2), p(r0, a0)).close())
    return w.extrude(z1 - z0).val()


def to_mesh(shape, tol=0.02):
    v, f = shape.tessellate(tol, 0.15)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True)


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def T(man):
    g = man.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


# ---------------------------------------------------------------- parts
def grip_top():
    """Plain section, gear and stop lug that replace the MkII grip's top (CadQuery, head frame)."""
    rb = GRIP_BORE / 2
    z0, z1 = h.GEAR_Z
    z0 -= GEAR_DOWN
    plain = cyl(h.GRIP_NECK_D / 2, h.KNURL_TOP - 0.1, z0 + 0.01)
    gear = gear_solid(h.GEAR_M, h.GRIP_TEETH, z0, z1, h.TX, h.TY)
    # the wall between the ceiling's O-ring and the stop lug: only over the gear's filled arc, where the lug is. That arc
    # never comes near the pinion, in use or as the grip slides up past it into mesh, so the rim never meets the pinion's
    # teeth (a full ring couldn't get past them), and it stands square on the filled teeth with nothing overhanging
    r0, r1, rh = h.GRIP_RIM
    a0, a1 = h.SPIN + h.TRAVEL + FILL_MARGIN, h.SPIN - 1.0 - FILL_MARGIN + 360.0     # gear_fill()'s arc
    rim = sector(r0, r1, a0, a1, z1 - 0.01, z1 + rh)
    t = plain.fuse(gear).fuse(gear_fill()).fuse(rim).fuse(stop_lug())
    return t.cut(cyl(rb, h.KNURL_TOP - 1, z1 + h.STOP_LUG[3] + 1)).clean()


# With the grip pushed up to the ceiling (0.5 mm over GEAR_Z), the pinion's lower teeth reach below the grip gear's
# modelled bottom, so the grip's teeth run GEAR_DOWN further down. They stand on the 33.4 mm neck (0.3 mm overhang at the
# tips, as before), so they print upright without supports.
GEAR_DOWN = 0.8
FILL_MARGIN = 22.0               # teeth stay this far (degrees at the grip) either side of what ever reaches the pinion


def gear_fill():
    """Solid at the teeth's tip radius over the grip's arc that never comes near the pinion. A grip point at angle a
    (grip frame, 0 at idle) sits at a + t in the head frame, t from -TRAVEL to +1 degree of slack, so it reaches the line
    of centres (SPIN) for a from SPIN - 1 to SPIN + TRAVEL. The pinion's tip circle overlaps the grip's only within 17.3
    degrees of that line, so FILL_MARGIN leaves it over 1 mm clear. The stop lug sits on this solid."""
    a0 = h.SPIN + h.TRAVEL + FILL_MARGIN
    a1 = h.SPIN - 1.0 - FILL_MARGIN + 360.0
    r_tip = h.GEAR_M * (h.GRIP_TEETH + 2) / 2 - 0.02
    return sector(12.0, r_tip, a0, a1, h.GEAR_Z[0] - GEAR_DOWN, h.GEAR_Z[1])


def stop_lug():
    """The 74 degree lug at idle: a plain sector on the gear's top face, as tall as the groove allows."""
    r0, r1, arc, lug_h = h.STOP_LUG
    return sector(r0, r1, h.LUG_IDLE, h.LUG_IDLE + arc, h.GEAR_Z[1] - 0.01, h.GEAR_Z[1] + lug_h)


def grip(mkii_grip_stl):
    knurl = trimesh.load(mkii_grip_stl)
    knurl.apply_translation(TUBE_T)
    k = M(knurl) ^ M(trimesh.creation.box(bounds=[[-100, -100, -300], [100, 100, h.KNURL_TOP]]))
    k -= M(to_mesh(cyl(GRIP_BORE / 2, h.KNURL_TOP - 10.0, h.KNURL_TOP + 1.0)))   # the old cap and spline socket
    # the MkII's bottom bearing is about 25.2-25.4 mm as drawn, and a cut can only open it up: fill it, then bore it
    # to BEARING_D with the top bearing, so both ends are the same size whatever BEARING_D is
    zg = TUBE_T[2] + 0.1875                                        # the grip's bottom face
    fill = mf.Manifold.cylinder(RELIEF_FROM + 0.5 - 0.3, 13.8, 13.8, 128).translate((h.TX, h.TY, zg + 0.3))
    g = k + M(to_mesh(grip_top())) + fill
    g = grip_end(g, zg)
    z0 = TUBE_T[2] + RELIEF_FROM
    z1 = h.GEAR_Z[1] - TOP_BEARING                                 # the top bearing starts here
    ztop = h.GEAR_Z[1] + h.STOP_LUG[3] + 1.0
    # one bore cut, end to end, at the bearing size, then the relief and its taper, which runs on through the bore
    rb, rr, taper = BEARING_D / 2 + BEARING_EPS, GRIP_RELIEF / 2, 2.5
    zb = TUBE_T[2] - 1.0                                           # below the grip's bottom
    cut = mf.Manifold.cylinder(ztop - zb, rb, rb, 128).translate((h.TX, h.TY, zb))
    cut += mf.Manifold.cylinder(z1 - taper + 0.2 - z0, rr, rr, 128).translate((h.TX, h.TY, z0))   # overlaps the taper
    slope = (rr - rb) / taper
    # the taper carries on past the bore's surface
    over = (rb - 12.2) / slope                                     # ...to r 12.2, well inside any bearing size
    cut += mf.Manifold.cylinder(taper + 0.2 + over, rr + 0.2 * slope, 12.2, 128).translate((h.TX, h.TY, z1 - taper - 0.2))
    # the bottom bearing: a 0.3 mm chamfer at the bed (small: the face round the bore carries the collar's O-ring), and a
    # taper up into the relief like the top one's
    cut += mf.Manifold.cylinder(0.5, rb + 0.3 + 0.2, rb, 128).translate((h.TX, h.TY, zg - 0.2))
    cut += radial_gland(zg + GLAND_UP, rb)
    rg, w = RADIAL_GLAND
    cut += radial_gland(h.GEAR_Z[0] - GEAR_DOWN - GLAND_UNDER_GEAR - (rg - rb) - w, rb)
    cut += mf.Manifold.cylinder(taper + 0.2 + over, 12.2, rr + 0.2 * slope, 128).translate((h.TX, h.TY, z0 - taper - over))
    cut = cut.translate((-h.TX, -h.TY, 0)).rotate((0, 0, 0.7)).translate((h.TX, h.TY, 0))   # facets off the MkII's
    return T(g - cut)


def radial_gland(z, rb):
    """An O-ring groove in the grip's bore, its floor at z: RADIAL_GLAND's radius and width, then a 45 degree roof in to
    the bore (rb). The section runs 0.3 mm on into the bore."""
    rg, w = RADIAL_GLAND
    pts = [(rb - 0.3, z), (rg, z), (rg, z + w), (rb - 0.3, z + w + rg - rb + 0.3)]
    return mf.CrossSection([pts]).revolve(128).translate((h.TX, h.TY, 0))


def oring_coupon():
    """A short slice of the grip's bore for test-fitting the O-ring bearing on the tube: the grip's BEARING_D bore and
    0.3 mm bed chamfer, one RADIAL_GLAND cut exactly as the grip's, 2 mm of wall outside it. Print it upright like the
    grip (about 2 g), fit a greased O-ring and slide it along the tube: it should turn with a light, even drag, and the
    plastic shouldn't touch the tube."""
    rb = BEARING_D / 2 + BEARING_EPS
    rg, w = RADIAL_GLAND
    z = 2.0                                                        # the groove's floor, over the bed
    hgt = z + w + (rg - rb) + 1.5
    ro = rg + 2.0
    c = mf.Manifold.cylinder(hgt, ro, ro, 128).translate((h.TX, h.TY, 0.0))
    c -= mf.Manifold.cylinder(hgt + 2.0, rb, rb, 128).translate((h.TX, h.TY, -1.0))
    c -= mf.Manifold.cylinder(0.5, rb + 0.3 + 0.2, rb, 128).translate((h.TX, h.TY, -0.2))
    c -= radial_gland(z, rb)
    return c.translate((-h.TX, -h.TY, 0.0))


def grip_end(g, zg):
    """Square the grip's bottom end up (see GRIP_END_R): a plain band, started below the face so the MkII's own face is
    swallowed, then trimmed by a revolved envelope whose round reaches 0.05 mm past the band (never coincident)."""
    ro = GRIP_OD / 2
    band = mf.Manifold.cylinder(GRIP_BAND + 1.0, ro, ro, 256).translate((h.TX, h.TY, zg - 1.0))
    re_, rf = ro + 0.05, GRIP_END_R
    pts = [(0.0, 0.0), (re_ - rf, 0.0)]
    pts += [(re_ - rf + rf * np.sin(t), rf - rf * np.cos(t)) for t in np.linspace(0, np.pi / 2, 17)[1:]]
    pts += [(re_, GRIP_BAND - 0.5), (ro + 5.0, GRIP_BAND - 0.5), (ro + 5.0, 300.0), (0.0, 300.0)]
    env = mf.CrossSection([pts]).revolve(256).translate((h.TX, h.TY, zg))
    rot = lambda m: m.translate((-h.TX, -h.TY, 0)).rotate((0, 0, 0.7)).translate((h.TX, h.TY, 0))   # facets off the MkII's
    return (g + rot(band)) ^ rot(env)


def label_text(txt, cap, x, y):
    """Bold, normal-width digits for labels that have to read at a glance (huey_head's panel text is condensed)."""
    if not hasattr(label_text, "font"):
        f = h.instancer.instantiateVariableFont(h.TTFont(h.FONT), {"wght": 700, "wdth": 100})
        label_text.font = (f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["OS/2"].sCapHeight)
    gs, cmap, hmtx, capu = label_text.font
    k, polys, pen_x = cap / capu, [], 0.0
    for ch in txt:
        g = cmap[ord(ch)]
        pen = h.FlatPen(gs)
        gs[g].draw(pen)
        polys += [[(pen_x + px * k, py * k) for px, py in poly] for poly in pen.polys]
        pen_x += hmtx[g][0] * k
    return mf.CrossSection(polys, mf.FillRule.NonZero).translate((x - pen_x / 2, y - cap / 2))


def bearing_coupons():
    """Test rings for the grip's bearing bore, one per COUPON_SIZES, printed upright like the grip. The bore is cut
    exactly as the grip's (same segments, same BEARING_EPS), with a 0.6 mm chamfer at the bed like the grip's bottom
    end. Each ring is only COUPON_H long with COUPON_WALL walls, and its size stands up in bold 4.5 mm figures on a
    thin tab. Slide each onto your tube and pick the smallest that turns freely without wobble."""
    out = mf.Manifold()
    for i, d in enumerate(COUPON_SIZES):
        cx, cy = (i % 2) * 40.0, -(i // 2) * 44.0                  # two by two
        r, ro = d / 2 + BEARING_EPS, d / 2 + COUPON_WALL
        ring = mf.Manifold.cylinder(COUPON_H, ro, ro, 128).translate((cx, cy, 0))
        ring += mf.Manifold.cube((17.0, 10.0, 1.6)).translate((cx - 8.5, cy - ro - 9.0, 0))     # label tab
        ring -= mf.Manifold.cylinder(COUPON_H + 2, r, r, 128).translate((cx, cy, -1.0))
        ring -= mf.Manifold.cylinder(0.8, r + 0.6 + 0.2, r, 128).translate((cx, cy, -0.2))      # bed chamfer
        ring += mf.Manifold.extrude(label_text(f"{d:.1f}", 4.5, cx, cy - ro - 4.2), 0.8).translate((0, 0, 1.6 - 0.01))
        out += ring
    return out


def friction_collar():
    f = FRICTION
    grip_bottom = TUBE_T[2] + 0.19                                 # the MkII grip's bottom face
    rg, depth = h.FACE_GLAND
    top = grip_bottom - f["gap"] - (h.ORING_CS - depth)            # the O-ring stands proud of the top by its section - depth
    z0 = top - f["h"]
    c = cyl(f["od"] / 2, z0, top)
    ear = box(h.TX + 15.0, h.TX + 26.0, h.TY - 7.0, h.TY + 7.0, z0, top)
    c = c.fuse(ear).clean()
    c = cq.Workplane().add(c).faces(">Z or <Z").edges().fillet(f["edge_r"]).val()   # top and bottom outside edges, ear too
    c = c.cut(cyl(f["bore"] / 2, z0 - 1, top + 1))
    c = c.cut(box(h.TX + 10.0, h.TX + 27.0, h.TY - f["slot"] / 2, h.TY + f["slot"] / 2, z0 - 1, top + 1))   # split
    # O-ring groove in the top face
    c = c.cut(cyl(rg, top - depth, top + 1))                       # open to the bore: the O-ring sits on the tube
    # M4 pinch screw along y through the ears: counterbore on +y, nut pocket on -y
    sx, sz = h.TX + 21.5, (z0 + top) / 2
    ax = lambda r, y0, y1: cq.Solid.makeCylinder(r, y1 - y0, V(sx, y0, sz), V(0, 1, 0))
    c = c.cut(ax(2.2, h.TY - 8, h.TY + 8)).cut(ax(3.75, h.TY + 3.5, h.TY + 8))
    hexa = cq.Workplane("XZ", origin=(sx, h.TY - 3.0, sz)).polygon(6, 7.2 / np.cos(np.pi / 6)).extrude(5.0).val()   # -y
    c = c.cut(hexa)
    return c.clean()


def pinion_phase(sign=1.0):
    """Turn of the pinion's tooth 0 (degrees) that meshes it with the grip gear as modelled: the grip's nearest tooth
    is (SPIN mod pitch) behind the line of centres, so the pinion's facing gap is k times that the other way."""
    pg, pp = 360.0 / h.GRIP_TEETH, 360.0 / h.PINION_TEETH
    k = h.GRIP_TEETH / h.PINION_TEETH
    return (h.SPIN + 180.0 + sign * (h.SPIN % pg) * k - pp / 2) % pp


HEX_CLEAR = -0.03                # pinion hex hole over SHAFT_HEX (the shaft's hex is SHAFT_HEX - 0.05). The user's fit tests
                                 # 2026-10-23: the 4.45 shaft is loose in a 4.6 hole and still slightly loose in 4.5


PINION_CHAMFER = 2.2             # 45 degrees off the tooth tips at both faces; see pinion()


def pinion():
    """Teeth the whole way to both faces (no hubs: a hub's step printed badly), with a 45 degree chamfer off the tips at
    each face. The chamfer is what keeps the pinion clear of the grip's neck: under the grip's gear the neck (r 16.7)
    reaches inside the pinion's tip circle, and with the grip pushed up to the ceiling (0.5 mm) and the pinion down on its
    floor (0.2 mm) the neck's shoulder stands 0.2 mm into the pinion's bottom face. A chamfer of 2.0 clears that exactly;
    2.2 leaves 0.3 mm of margin, and 3.2 of the 5.6 mm of face at the pitch circle. It's the same at both faces, so the
    pinion goes in either way up, and it prints with no step: a 45 degree chamfer needs no support."""
    z0, z1 = h.PINION_Z
    g = gear_solid(h.GEAR_M, h.PINION_TEETH, z0, z1, h.PX, h.PY, rot=pinion_phase())
    ra, c, e = h.GEAR_M * (h.PINION_TEETH + 2) / 2, PINION_CHAMFER, 0.3
    env = [(0, z0), (ra - c, z0), (ra + e, z0 + c + e), (ra + e, z1 - c - e), (ra - c, z1), (0, z1)]   # (r, z)
    g = g.intersect(cq.Workplane("XZ").polyline(env).close().revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(V(h.PX, h.PY, 0)))
    return g.cut(hex_prism(h.SHAFT_HEX + HEX_CLEAR, z0 - 1, z1 + 1, h.PX, h.PY)).clean()   # 4.47 hole on the 4.45 hex: a snug push fit


MAGNET_BORE = 4.2                # the magnet is about 4 mm. LOCKED IN: 4.2 fits, printed 2026-10-24 (4.0 printed too small; 4.6 was for a 5 mm magnet)


def magnet_shaft():
    """Cap on the web with the magnet in its top, a round shaft through the web, a hex end into the pinion, and a pin
    on through the pinion into the bearing hole in the pocket floor (pointed, to find the hole)."""
    z0, z1 = h.PINION_Z
    s = cyl(5.0, h.CAP[0], h.CAP[1] + h.CAP_UP, h.PX, h.PY)
    s = s.fuse(cyl(h.SHAFT_D / 2, z1 + 0.1, h.CAP[0] + 0.01, h.PX, h.PY))         # stops 0.1 above the pinion
    s = s.fuse(hex_prism(h.SHAFT_HEX - 0.05, z0 + 0.3, z1 + 0.11, h.PX, h.PY))
    pz = h.GEAR_Z[0] - 0.5 - h.PIN_DEPTH + 0.5                                   # 0.5 clear of the hole's bottom
    s = s.fuse(cyl(h.PIN_D / 2, pz + 0.5, z0 + 0.31, h.PX, h.PY))
    s = s.fuse(cq.Solid.makeCone(h.PIN_D / 2 - 0.5, h.PIN_D / 2, 0.51, V(h.PX, h.PY, pz)))
    d, t = h.MAGNET
    return s.cut(cyl(MAGNET_BORE / 2, h.CAP[1] + h.CAP_UP - t - 0.1, h.CAP[1] + h.CAP_UP + 1, h.PX, h.PY)).clean()



def refs():
    m = h.MODULE / 2
    d, t = h.MAGNET
    rot = lambda s: s.rotate(V(h.PX, h.PY, 0), V(h.PX, h.PY, 1), h.MODULE_ROT)
    return {
        "tube": cyl(h.TUBE_OD / 2, h.TUBE_END - 200, h.TUBE_END).cut(cyl(h.TUBE_OD / 2 - 1, h.TUBE_END - 201, h.TUBE_END + 1))
                .cut(cq.Solid.makeCylinder(2.6, 40, V(h.TX, h.TY - 20, h.BOLT_Z), V(0, 1, 0))),
        "module": rot(box(h.PX - m, h.PX + m, h.PY - m, h.PY + m, h.BOARD_Z, h.BOARD_Z + 1.6)),
        "chip": rot(box(h.PX - 2.5, h.PX + 2.5, h.PY - 3.1, h.PY + 3.1, h.CHIP_FACE, h.BOARD_Z)),
        "magnet": cyl(d / 2, h.CAP[1] + h.CAP_UP - t, h.CAP[1] + h.CAP_UP, h.PX, h.PY),
        "m5_bolt": cq.Solid.makeCylinder(2.5, 40, V(h.TX, h.TY - h.BOSS_D / 2 + 1.1, h.BOLT_Z), V(0, 1, 0)),
    }


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    os.makedirs(os.path.join(out, "ref"), exist_ok=True)
    parts = {"HueyHeadR3-ThrottleGrip": grip(src), "HueyHeadR3-FrictionCollar": to_mesh(friction_collar()),
             "HueyHeadR3-Pinion": to_mesh(pinion()), "HueyHeadR3-MagnetShaft": to_mesh(magnet_shaft()),
             "HueyHeadR3-GripBearingCoupons": T(bearing_coupons()), "HueyHeadR3-ORingCoupon": T(oring_coupon())}
    for name, m in parts.items():
        m.export(os.path.join(out, name + ".stl"))
        back = trimesh.load(os.path.join(out, name + ".stl"))      # the float32 STL round trip can open edges
        print(f"{name:30s} watertight={back.is_watertight} volume={m.volume / 1000:6.2f} cm3 z {m.bounds[0][2]:.1f}..{m.bounds[1][2]:.1f}")
    for name, s in refs().items():
        to_mesh(s).export(os.path.join(out, "ref", name + ".stl"))
