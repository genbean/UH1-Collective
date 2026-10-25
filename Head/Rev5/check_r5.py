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
import hat_r5
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
    lp, _ = hat_r5.lower_panel_new()
    up, _ = h.upper_panel()
    parts = {"body": body, "lower_panel": tilt(lp), "upper_panel": tilt(up), "trigger": h.trigger()}
    sw = {"GOV": toggle_body(*h.GOV, 0.0), "LDG_EXT": toggle_body(*h.LDG_EXT, 0.0),
          "STOP_REL": ycyl(*h.STOP_REL, 12.0, 0, 16.0) + ycyl(*h.STOP_REL, 18.0, 0, 3.0),
          "SL": toggle_body(*h.SL, h.UY), "LDG_ON": toggle_body(*h.LDG_ON, h.UY)}
    parts.update({k: tilt(v) for k, v in sw.items()})
    parts.update({k: tilt(v) for k, v in helisr().items()})
    for k in range(4):                                           # the hat's tact switches, in their pockets
        b, bt, lg = hat_r5.tact(k)
        parts[f"hat_tact{k}"] = tilt((b + bt + lg).translate((h.SEARCH[0], 0, h.SEARCH[1])))
    names = list(parts)
    allowed = {("body", "lower_panel"), ("body", "upper_panel")}   # the panels' plugs sit inside the walls: checked below
    bad = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in allowed or a.startswith("hat_tact") and b == "lower_panel" or (a == "lower_panel" and b.startswith("hat_tact")):
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
    # the switches clear the neck block's cuts by 1 mm (so nothing is left as a skin over the pod or the bores)
    # (the AS5600's way in from the front is left out: the module goes in before the lower panel)
    m = h.MODULE / 2 + h.BOARD_CLR
    seated = h.zprism(h.module_xs(-m, m, -m, m), h.BOARD_Z - 0.5, h.BOARD_Z + h.GROOVE_H + 0.5)   # the module in its grooves
    cuts = (h.neck_cuts() - h.module_seat()) + seated
    grown = {"GOV": toggle_body(*h.GOV, 0.0, 1.0), "LDG_EXT": toggle_body(*h.LDG_EXT, 0.0, 1.0),
             "STOP_REL": ycyl(*h.STOP_REL, 14.0, 0, 17.0) + ycyl(*h.STOP_REL, 20.0, 0, 4.0)}
    for k, m in grown.items():
        v = (tilt(m) ^ cuts).volume()
        if v > TOL:
            bad += 1
            print(f"OVERLAP {k} with the neck cuts + 1 mm {v:.2f} mm3")
    bad += leads_hole(body)
    print("all clear" if not bad else f"{bad} problem(s)")


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

    B = tm(body)
    S0 = tm((tilt(h.body()) + h.neck_solid() + h.trigger_mount()) - h.neck_cuts())
    NC = tm(h.neck_cuts())
    cav = tm(h.interior())
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


if __name__ == "__main__":
    main()
