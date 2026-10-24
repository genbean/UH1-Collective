# Rev 2 throttle: grip, friction collar, pinion and magnet shaft, in the head frame (huey_head.py's Rev 2 layout).
#
# The grip turns on the aluminium tube itself (25.4 mm bore, bearing at both ends as in the relieved MkII grip). Its
# body is the whole 120 mm MkII grip, so the hand has the same length to hold, with the old top cap bored out to the
# tube; it ends just under the head's round neck. Above it a plain 33.4 mm section
# runs up inside the neck into the box, and on top of it are a 32-tooth, module 1 spur gear and a 30 degree stop lug
# that runs in a groove in the boss's ceiling: 180 degrees from idle to full open, as on the real UH-1, plus a 15
# degree cutoff range past idle where the lug's ramped face lifts the spring-loaded idle plunger. The gear drives a
# 20-tooth pinion beside the boss (1.6:1, so the grip's 195 degrees are 312 degrees at the magnet). The magnet shaft drops through
# the bearing web over the pinion and presses into the pinion's hex hole; its cap rests on the web and holds the
# magnet 1.5 mm under the AS5600 module.
#
# Below the grip, a split friction collar clamps to the tube. A 25 x 3 mm O-ring in its top face presses the grip up
# against the boss: slide it up for more friction and tighten its M4 pinch screw.
#
# Needs cadquery, numpy, trimesh and manifold3d. usage: throttle_r2.py <MkII-Grip-bore-relieved-25mm.stl> <out dir>
import os
import sys
import numpy as np
import cadquery as cq
import trimesh
import manifold3d as mf
import huey_head as h

V = cq.Vector
KNURL_SRC = 120.0                       # the MkII grip's top, its own z = 120: all of it is kept
TUBE_T = (h.TX, h.TY, h.KNURL_TOP - KNURL_SRC)   # MkII tube-frame parts (the knurled grip) -> head frame
GRIP_BORE = 24.6                        # construction bore, under every bearing size: BEARING_D sets the real one
# The grip bears on the tube only at its two ends, as the relieved MkII grip does: the MkII's bottom 21 mm and the top
# 22 mm (under and through the gear), both bored to BEARING_D, and everything between relieved to 26.2 mm, with short
# tapers like the MkII's. That moves the MkII's old top bearing (its own z 90..112) up to the new top end.
BEARING_D = 25.3                        # both bearings: from the bearing coupons (25.3 turns freely without rock on the 25 mm tube)
COUPON_SIZES = (25.0, 25.1, 25.2, 25.3)   # second round; the first set was 25.4 to 26.0, and 25.4 was still loose
COUPON_H, COUPON_WALL = 8.0, 2.0        # just long and stiff enough to judge the fit: about 1.3 cm3 a ring
BEARING_EPS = 0.03                      # the bore is cut this much over size, grip and coupons alike, so it never lands
                                        # on the MkII mesh's own polygonal bore
GRIP_RELIEF = 26.2                      # just over the MkII's 26 mm relief, so the two never coincide
RELIEF_FROM = 25.0                      # the MkII grip's own z where its bottom bearing's taper ends
TOP_BEARING = 22.0
BACKLASH = 0.1                          # taken off each tooth's thickness at the pitch circle
FRICTION = dict(od=40.0, h=12.0, bore=25.3, gap=0.2, slot=1.5, oring=(25.0, 3.0), groove_depth=2.2)


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
    plain = cyl(h.GRIP_NECK_D / 2, h.KNURL_TOP - 0.1, z0 + 0.01)
    gear = gear_solid(h.GEAR_M, h.GRIP_TEETH, z0, z1, h.TX, h.TY)
    t = plain.fuse(gear).fuse(stop_lug())
    return t.cut(cyl(rb, h.KNURL_TOP - 1, z1 + h.STOP_LUG[3] + 1)).clean()


def stop_lug():
    """The 30 degree lug at idle. Its closing face (the + end) ramps down over LUG_RAMP degrees to just under the
    idle plunger's tip, so rolling into the cutoff range lifts the plunger."""
    r0, r1, arc, lug_h = h.STOP_LUG
    z1 = h.GEAR_Z[1]
    a0, a1 = h.LUG_IDLE, h.LUG_IDLE + arc
    ar = a1 - h.LUG_RAMP
    low = h.PLUNGER_TIP[1] - z1                                    # height at the face
    flat = sector(r0, r1, a0, ar + 0.01, z1 - 0.01, z1 + lug_h)
    def section(a, top):
        c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
        p = lambda r, z: V(h.TX + r * c, h.TY + r * s_, z)
        return cq.Wire.makePolygon([p(r0, z1 - 0.01), p(r1, z1 - 0.01), p(r1, z1 + top), p(r0, z1 + top)], close=True)
    n = 6                                                          # ruled loft in short pieces, so it follows the arc
    ramp = None
    for i in range(n):
        aa, ab = ar + h.LUG_RAMP * i / n, ar + h.LUG_RAMP * (i + 1) / n
        ta, tb = lug_h - (lug_h - low) * i / n, lug_h - (lug_h - low) * (i + 1) / n
        piece = cq.Solid.makeLoft([section(aa - 0.01, ta), section(ab, tb)], ruled=True)
        ramp = piece if ramp is None else ramp.fuse(piece)
    return flat.fuse(ramp)


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
    # the bottom bearing: a chamfer at the bed, and a taper up into the relief like the top one's
    cut += mf.Manifold.cylinder(0.8, rb + 0.6 + 0.2, rb, 128).translate((h.TX, h.TY, zg - 0.2))
    cut += mf.Manifold.cylinder(taper + 0.2 + over, 12.2, rr + 0.2 * slope, 128).translate((h.TX, h.TY, z0 - taper - over))
    cut = cut.translate((-h.TX, -h.TY, 0)).rotate((0, 0, 0.7)).translate((h.TX, h.TY, 0))   # facets off the MkII's
    return T(g - cut)


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
    oid, ocs = f["oring"]
    top = grip_bottom - f["gap"] - (ocs - f["groove_depth"])       # O-ring stands proud of the top by cs - depth
    z0 = top - f["h"]
    c = cyl(f["od"] / 2, z0, top)
    ear = box(h.TX + 15.0, h.TX + 26.0, h.TY - 7.0, h.TY + 7.0, z0, top)
    c = c.fuse(ear).cut(cyl(f["bore"] / 2, z0 - 1, top + 1))
    c = c.cut(box(h.TX + 10.0, h.TX + 27.0, h.TY - f["slot"] / 2, h.TY + f["slot"] / 2, z0 - 1, top + 1))   # split
    # O-ring groove in the top face
    c = c.cut(cyl(oid / 2 + ocs + 0.2, top - f["groove_depth"], top + 1))      # open to the bore: the O-ring sits on the tube
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


def pinion():
    z0, z1 = h.PINION_Z
    g = gear_solid(h.GEAR_M, h.PINION_TEETH, z0, z1, h.PX, h.PY, rot=pinion_phase())
    return g.cut(hex_prism(h.SHAFT_HEX, z0 - 1, z1 + 1, h.PX, h.PY)).clean()     # exact size: a press fit as printed


def magnet_shaft():
    """Cap on the web with the magnet in its top, a round shaft through the web, and a hex end into the pinion."""
    z0, z1 = h.PINION_Z
    s = cyl(5.0, h.CAP[0], h.CAP[1], h.PX, h.PY)
    s = s.fuse(cyl(h.SHAFT_D / 2, z1 + 0.1, h.CAP[0] + 0.01, h.PX, h.PY))         # stops 0.1 above the pinion
    s = s.fuse(hex_prism(h.SHAFT_HEX - 0.05, z0 + 0.3, z1 + 0.11, h.PX, h.PY))
    d, t = h.MAGNET
    return s.cut(cyl(d / 2 + 0.1, h.CAP[1] - t - 0.1, h.CAP[1] + 1, h.PX, h.PY)).clean()


def idle_plunger():
    """At rest: the round tip's lowest point at PLUNGER_TIP[1], the body sitting on the guide's step (mesh)."""
    d, z0 = h.PLUNGER_TIP
    bd, bl = h.PLUNGER_BODY
    zs = h.PLUNGER_STEP
    tip = mf.Manifold.cylinder(zs + 0.01 - (z0 + d / 2), d / 2, d / 2, 64).translate((h.PLX, h.PLY, z0 + d / 2))
    tip += mf.Manifold.sphere(d / 2, 64).translate((h.PLX, h.PLY, z0 + d / 2))
    return T(tip + mf.Manifold.cylinder(bl, bd / 2, bd / 2, 64).translate((h.PLX, h.PLY, zs)))


def refs():
    m = h.MODULE / 2
    d, t = h.MAGNET
    rot = lambda s: s.rotate(V(h.PX, h.PY, 0), V(h.PX, h.PY, 1), h.MODULE_ROT)
    return {
        "tube": cyl(h.TUBE_OD / 2, h.TUBE_END - 200, h.TUBE_END).cut(cyl(h.TUBE_OD / 2 - 1, h.TUBE_END - 201, h.TUBE_END + 1))
                .cut(cq.Solid.makeCylinder(2.6, 40, V(h.TX, h.TY - 20, h.BOLT_Z), V(0, 1, 0))),
        "module": rot(box(h.PX - m, h.PX + m, h.PY - m, h.PY + m, h.BOARD_Z, h.BOARD_Z + 1.6)),
        "chip": rot(box(h.PX - 2.5, h.PX + 2.5, h.PY - 3.1, h.PY + 3.1, h.CHIP_FACE, h.BOARD_Z)),
        "magnet": cyl(d / 2, h.CAP[1] - t, h.CAP[1], h.PX, h.PY),
        "m5_bolt": cq.Solid.makeCylinder(2.5, 40, V(h.TX, h.TY - h.BOSS_D / 2 + 1.1, h.BOLT_Z), V(0, 1, 0)),
        "m5_setscrew": cyl(2.5, h.BOSS_TOP - 5.0, h.BOSS_TOP, h.PLX, h.PLY),
    }


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    os.makedirs(os.path.join(out, "ref"), exist_ok=True)
    parts = {"HueyHead-ThrottleGrip": grip(src), "HueyHead-FrictionCollar": to_mesh(friction_collar()),
             "HueyHead-Pinion": to_mesh(pinion()), "HueyHead-MagnetShaft": to_mesh(magnet_shaft()),
             "HueyHead-IdlePlunger": idle_plunger(), "HueyHead-GripBearingCoupons": T(bearing_coupons())}
    for name, m in parts.items():
        m.export(os.path.join(out, name + ".stl"))
        print(f"{name:26s} watertight={m.is_watertight} volume={m.volume / 1000:6.2f} cm3 z {m.bounds[0][2]:.1f}..{m.bounds[1][2]:.1f}")
    for name, s in refs().items():
        to_mesh(s).export(os.path.join(out, "ref", name + ".stl"))
