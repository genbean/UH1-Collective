# Head Rev 5 collision check: every printed part, the switches, the HeliSR board and the starter leads' hole, in place.
# Prints the overlap volume of every pair that should not touch, and the checks on the leads' hole. Needs the same
# Python packages as huey_head_r5.py.
# usage: check_r5.py
import os
import sys
import numpy as np
import trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "Hat"))
import huey_head_r5 as h
import hat4_r5                                      # the SEARCH CONT hat: the lower panel and the breakout board behind it
from huey_head_r5 import box, ycyl, tilt

TOL = 0.05                                     # mm3: anything smaller is a float graze


def toggle_body(x, z, y0, g=0.0):
    """APEM 600H behind its panel (back face at y0): 14.65 x 29.7 mm, 26 mm deep with its lugs straight; grown by g."""
    return box(x - 7.35 - g, y0, z - 14.85 - g, x + 7.35 + g, y0 + 26.0 + g, z + 14.85 + g)


def helisr():
    """HeliSR Rev 3.0 stand-ins on the rear wall: the board, its four spacers, the parts on its front (JST SR
    connectors and buttons, 4.5 mm), the Pro Micro (18 x 33 mm, 19.4 mm off the wall) and the USB-C plug's overmold
    (12 x 7 mm) running 25 mm down from the Pro Micro's end through WIRE_SLOT."""
    x0, z0 = h.HELISR_X0, h.HELISR_Z0
    w, l = h.HELISR_SIZE[1], h.HELISR_SIZE[0]
    yb = h.YB - 4.0                                               # the board's back, on the spacers
    board = box(x0, yb - 1.6, z0, x0 + w, yb, z0 + l)
    spacers = mf.Manifold()
    for x, z in h.HELISR_MOUNTS:
        spacers += ycyl(x, z, 6.4, yb, h.YB)
    parts = box(x0 + 0.5, yb - 1.6 - 4.5, z0 + 0.5, x0 + w - 0.5, yb - 1.6, z0 + l - 0.5)
    xm = x0 + w / 2
    pro = box(xm - 9.0, h.YB - h.HELISR_STACK, z0, xm + 9.0, yb - 1.6, z0 + 33.0)
    plug = box(xm - 6.0, h.YB - h.HELISR_STACK + 1.0, z0 - 25.0, xm + 6.0, h.YB - h.HELISR_STACK + 8.0, z0 + 1.0)
    return {"helisr_board": board, "helisr_spacers": spacers, "helisr_parts": parts, "pro_micro": pro, "usb_plug": plug}


def tm(m):
    q = m.to_mesh()
    return trimesh.Trimesh(np.asarray(q.vert_properties)[:, :3].copy(), np.asarray(q.tri_verts).copy(), process=False)


def main():
    body = h.body_r5()
    lp, _ = hat4_r5.lower_panel()
    up, _ = h.upper_panel()
    parts = {"body": body, "lower_panel": tilt(lp), "upper_panel": tilt(up), "trigger": h.trigger()}
    sw = {"GOV": toggle_body(*h.GOV, 0.0), "LDG_EXT": toggle_body(*h.LDG_EXT, 0.0),
          "STOP_REL": ycyl(*h.STOP_REL, 12.0, h.PLUG_H, 16.0) + ycyl(*h.STOP_REL, 18.0, h.PLUG_H, h.PLUG_H + 1.5),   # its
          # nut on the plug: 1.5 mm is all the room the head's cut leaves behind it
          "SL": toggle_body(*h.SL, h.UY), "LDG_ON": toggle_body(*h.LDG_ON, h.UY)}
    parts.update({k: tilt(v) for k, v in sw.items()})
    parts.update({k: tilt(v) for k, v in helisr().items()})
    asm = hat4_r5.assembly()                                     # the hat: the board, the switch, J1 and its plug, the
    for k in ("board", "switch", "j1", "plug", "screws"):        # screws (the stick and cap are checked by hat4_r5.py --check)
        parts[f"hat_{k}"] = tilt(asm[k])
    names = list(parts)
    allowed = {("body", "lower_panel"), ("body", "upper_panel")}   # the panels' plugs sit inside the walls: checked below
    allowed.add(("lower_panel", "hat_screws"))                  # the M2s cut their thread in the bosses' pilots; hat4_r5.py
                                                                 # --check tests them against the panel outside the pilots
    bad = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in allowed or a.startswith("hat_") and b.startswith("hat_"):
                continue
            if {a, b} <= {"helisr_board", "helisr_spacers", "helisr_parts", "pro_micro", "usb_plug"}:
                continue
            v = (parts[a] ^ parts[b]).volume()
            if v > TOL:
                bad += 1
                print(f"OVERLAP {a:16s} {b:16s} {v:9.2f} mm3")
    for p in ("lower_panel", "upper_panel"):
        v = (parts["body"] ^ parts[p]).volume()
        print(f"{'body x ' + p:34s} {v:9.2f} mm3 {'OK' if v < TOL else 'OVERLAP'}")
        bad += v >= TOL
    # no neck cut breaks out through a wall: only the bores' open bottom end and the AS5600's way in (out through the
    # open front) leave the solid
    env = tilt(h.prism(h.BODY, 0, h.YC)) + h.neck_solid() + h.trigger_mount()
    keep = h.by(0.0) ^ mf.Manifold.cube((400.0, 400.0, 400.0)).translate((-200.0, -200.0, h.NECK_BOT + 0.5))
    v = ((h.neck_cuts() - env) ^ keep).volume()
    print(f"{'neck cuts outside the solid':34s} {v:9.2f} mm3 {'OK' if v < TOL else 'BREAKS OUT'}")
    bad += v >= TOL
    # the switches clear the neck block's cuts and the AS5600 board by 1 mm (so nothing is left as a skin over the bores)
    # (the AS5600's way in from the front is left out: the module goes in before the lower panel)
    m = h.MODULE / 2
    seated = h.zprism(h.module_xs(-m, m, -m, m), h.BOARD_Z, h.BOARD_Z + 1.6)   # the module board itself, in its grooves
    cuts = (h.neck_cuts() - h.module_seat() - h.pocket_window()) + seated   # the window into the pinion pocket opens into
    # the STOP REL recess on purpose
    grown = {"GOV": toggle_body(*h.GOV, 0.0, 1.0), "LDG_EXT": toggle_body(*h.LDG_EXT, 0.0, 1.0),
             "STOP_REL": ycyl(*h.STOP_REL, 14.0, 0, 17.0) + ycyl(*h.STOP_REL, 20.0, 0, 4.0)}
    for k, m in grown.items():
        v = (tilt(m) ^ cuts).volume()
        if v > TOL:
            bad += 1
            print(f"OVERLAP {k} (grown 1 mm) with the neck cuts or the AS5600 board {v:.2f} mm3")
    bad += labels()
    bad += leads_hole(body)
    bad += usb_cable(parts)
    print("all clear" if not bad else f"{bad} problem(s)")


def labels():
    """Every label clears the screw heads, the toggles' 14 mm nuts, the hat's cap and the STOP REL button's 17.6 mm bezel by 0.5 mm,
    and the panel's edge by 1 mm."""
    c = h.circle
    low = [c(h.PANEL_CSK[0] + 1.0, x, z) for x, z in h.COLUMNS] + [c(14.0, *h.GOV), c(14.0, *h.LDG_EXT),
                                                             c(2 * hat4_r5.CAP_R + 1.0, *h.SEARCH), c(h.PB4_BEZEL_D + 1.0, *h.STOP_REL)]
    up = [c(h.PANEL_CSK[0] + 1.0, x, z) for x, z in h.UPPER_COLUMNS] + [c(14.0, *h.SL), c(14.0, *h.LDG_ON)]
    bad = 0
    for name, lab, holes, outline in (("lower", h.lower_labels(), low, h.LOWER_PANEL), ("upper", h.upper_labels(), up, h.UPPER_PANEL)):
        a = sum((lab ^ x).area() for x in holes) + (lab - outline.offset(-1.0, mf.JoinType.Miter)).area()
        print(f"{name + ' panel labels clear':34s} {a:9.2f} mm2 {'OK' if a < 0.01 else 'CROWDED'}")
        bad += a >= 0.01
    return bad


def leads_hole(body):
    """The starter leads' hole: open from the groove into the box, 1.2 mm of wall to every other cut and the outside,
    and it comes out into the box's open inside."""
    hx, hy, lx, ly, hd, hl = h.LEAD_HOLE
    d = np.array([np.tan(np.radians(lx)), np.tan(np.radians(ly)), 1.0])
    d /= np.linalg.norm(d)
    p0 = np.array([hx, hy, h.MOUNT_Z0 + 1.0])
    a = np.cross(d, [0.0, 1.0, 0.3])
    a /= np.linalg.norm(a)
    b = np.cross(d, a)
    c, s = np.cos(np.radians(h.TILT)), np.sin(np.radians(h.TILT))

    def hf(q):
        q = np.atleast_2d(np.asarray(q, float))
        z = q[:, 2] - h.ZB
        return np.stack([q[:, 0], q[:, 1] * c - z * s, q[:, 1] * s + z * c + h.ZB], 1)

    def ring(r, ts, n=16):
        return np.vstack([hf(p0 + np.outer(ts, d) + r * (np.cos(g) * a + np.sin(g) * b))
                          for g in np.linspace(0, 2 * np.pi, n, endpoint=False)])

    near = tilt(box(hx - 20.0, 20.0, h.MOUNT_Z0 - 10.0, hx + 20.0, h.YC + 2.0, h.MOUNT_Z0 + hl + 20.0))   # only round the
    B = tm(body ^ near)                                                  # hole: the threads make the whole body's mesh huge
    S0 = tm(((tilt(h.body()) + h.neck_solid() + h.trigger_mount()) - h.neck_cuts()) ^ near)
    NC = tm(h.neck_cuts() ^ near)
    cav = tm(h.interior() ^ near)
    bad = 0
    ok = not B.contains(ring(hd / 2 - 0.05, np.arange(-2.5, hl, 0.5))).any()
    print(f"{'leads hole open, groove to end':34s} {'OK' if ok else 'BLOCKED'}")
    bad += not ok
    rg = ring(hd / 2 + 1.2, np.arange(0, hl, 1.0), 24)
    n = int(NC.contains(rg).sum() + (~S0.contains(rg) & ~cav.contains(rg)).sum())
    print(f"{'leads hole 1.2 mm walls':34s} {'OK' if n == 0 else f'{n} thin points'}")
    bad += n > 0
    e = hf(p0 + np.outer(np.arange(hl, hl + 3, 1.0), d))
    ok = bool((cav.contains(e) & ~S0.contains(e)).all())
    print(f"{'leads hole comes out in the box':34s} {'OK' if ok else 'NO'}")
    bad += not ok
    return bad


# The carbon tube and the two cables that come up it into the head (Base/README.md, BOM/make_final_bom.py)
TUBE_OD, TUBE_ID = 25.0, 23.0
USB_OD = 4.5                     # the Stewart SC-2CAK020M's diameter isn't published; USB 2.0 cables run 3.5-4.5 mm
AX1_OD = 3.61                    # the base sensor's 4-core lead
AX1_AT = 7.5                     # it goes through the lip's 20 mm opening this far in front of the centre (panel side)
USB_MARGIN = 1.0                 # the plug and its cable must clear the body, the tube and the HeliSR's parts by this


def head_pt(p):
    """Box frame -> head frame, for points (tilt() does it for solids)."""
    c, s = np.cos(np.radians(h.TILT)), np.sin(np.radians(h.TILT))
    x, y, z = p
    z -= h.ZB
    return np.array([x, y * c - z * s, y * s + z * c + h.ZB])


def cable(pts, d):
    """A round cable of diameter d through the points (head frame): hulls of spheres along the path."""
    s = [mf.Manifold.sphere(d / 2, 20).translate(tuple(map(float, p))) for p in pts]
    return sum((mf.Manifold.batch_hull([a, b]) for a, b in zip(s, s[1:])), mf.Manifold())


def bezier(p0, t0, p1, t1, n=30):
    k = np.linalg.norm(p1 - p0) / 3
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * (p0 + t0 * k) + 3 * (1 - u) * u ** 2 * (p1 - t1 * k) + u ** 3 * p1


def usb_plug_box(w, t, length, g=0.0):
    """The USB-C plug's overmold, w x t, hanging length mm from the Pro Micro's end (box frame), grown by g."""
    xm, yc, z0 = h.HELISR_X0 + h.HELISR_SIZE[1] / 2, h.YB - h.HELISR_STACK + 4.5, h.HELISR_Z0
    return box(xm - w / 2 - g, yc - t / 2 - g, z0 - length - g, xm + w / 2 + g, yc + t / 2 + g, z0 + 1)


def usb_cable(parts):
    """The USB-C plug's cable and the base sensor's lead, down into the carbon tube. The plug hangs from the Pro Micro
    through the wire slot and its end goes into the tube's top end, through the lip's 20 mm opening. Its cable bends
    20 degrees into the tube's axis (the box leans on the tube). The sensor's lead comes up the tube beside it and
    through the same opening, in front of the plug."""
    tube = h.zcyl(h.TX, h.TY, TUBE_OD, h.TUBE_END - 120, h.TUBE_END) - h.zcyl(h.TX, h.TY, TUBE_ID, h.TUBE_END - 121, h.TUBE_END + 1)
    xm, yc, z0 = h.HELISR_X0 + h.HELISR_SIZE[1] / 2, h.YB - h.HELISR_STACK + 4.5, h.HELISR_Z0
    down = head_pt((0, 0, -1)) - head_pt((0, 0, 0))                 # the plug points straight down the box
    axis = lambda z: np.array([h.TX, h.TY, z])

    def stub(length, d):
        p0 = head_pt((xm, yc, z0 - length))
        return cable(list(bezier(p0, down, axis(h.TUBE_END - 45), np.array([0, 0, -1.0]))) + [axis(h.TUBE_END - 110)], d)

    plug, usb = parts["usb_plug"], stub(25.0, USB_OD)
    up = head_pt((0, 0, 1)) - head_pt((0, 0, 0))
    q = lambda z: np.array([h.TX, h.TY - AX1_AT, z])
    lead = cable([q(h.TUBE_END - 60), q(h.TUBE_TOP + 2), q(h.TUBE_TOP + 2) + 12 * up], AX1_OD)
    others = {k: m for k, m in parts.items() if k not in ("usb_plug", "pro_micro")}
    others["tube"] = tube
    bad = 0

    def line(name, hits):
        nonlocal bad
        print(f"{name:34s} {'OK' if not hits else 'HITS ' + ', '.join(hits)}")
        bad += bool(hits)
    hit = lambda m, pool: [k for k, o in pool.items() if (m ^ o).volume() > TOL]
    line("USB plug into the tube", hit(plug, {"tube": tube}))
    line("USB cable down the tube", hit(usb, others))
    line("sensor lead beside them", hit(lead, {**others, "usb_plug": plug, "usb_cable": usb}))
    g = USB_MARGIN                                                    # room round the plug and its cable
    grown = tilt(usb_plug_box(12.0, 7.0, 25.0, g)) + stub(25.0, USB_OD + 2 * g)
    line(f"USB plug and cable, {g:.0f} mm clear", hit(grown, {k: others[k] for k in ("body", "tube", "helisr_parts", "helisr_board")}))
    # how long an overmold still fits (the plug is modelled 25 mm long; measure yours)
    fits = []
    for w, t in ((12.0, 7.0), (14.0, 8.0)):
        n = 25.0
        while n < 60 and not hit(tilt(usb_plug_box(w, t, n + 1.0)), {"tube": tube, "body": parts["body"]}):
            n += 1.0
        fits.append(f"{w:.0f} x {t:.0f} up to {n:.0f} mm")
    print(f"{'USB-C overmold that fits':34s} {'; '.join(fits)}")
    return bad


if __name__ == "__main__":
    main()
