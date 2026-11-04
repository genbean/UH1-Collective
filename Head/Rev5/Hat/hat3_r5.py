# UH-1 head Rev 5: the SEARCH CONT hat, Rev 3, with its own lower panel.
#
# The panel has no carrier any more: just a round hole and three alignment pins on its back, so it prints face down
# with no supports. The hat is a separate pod, glued on the panel's back over the pins.
#
#   - The pod prints back down: switch pockets open upward, leg slots through its floor, no overhangs.
#   - The rocker plate stands on 8 domed feet on a flat seat in the pod's middle, a regular octagon 2.2 mm out. A straight
#     push lands on the seat and moves nothing. A push toward a switch tips the plate over one octagon edge and that
#     button goes in; a push toward a diagonal tips it over a diagonal edge and both neighbours go in (8-way). Opposite
#     buttons can't both go in, nor three.
#   - An M3 x 20 countersunk screw comes from the pod's back, through a pen spring and a cup, and self-taps into the
#     rocker's stem: the spring pulls the plate onto its feet, which centres it and gives the break before the click.
#   - The pressed buttons bottoming are the stop; the cap's rim landing on the panel face is the backstop.
#   - The rocker goes in from the front through the panel's hole, so it comes out again.
#
# Box frame, hat centre at the origin, y toward the rear wall: panel face -2.5, back 0.
#
# usage: hat3_r5.py <out dir>      (writes the panel and the hat's parts)
#        hat3_r5.py --check        (every way the plate can tip, how far each button goes, and what it hits)
import os
import sys
import numpy as np
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import hat_r5 as v1
import huey_head_r5 as h
from huey_head_r5 import rect, circle, prism, ycyl, save

SEARCH = h.SEARCH
FACE = -h.PANEL_T
PITCH = 7.0
TACT_H, TACT_BODY = h.TACT_H, h.TACT_BODY          # base to button top 5.0, base to cover 3.61
TACT_PROUD = TACT_H - TACT_BODY                     # 1.39
BTN_R = 1.75
CLICK = (0.15, 0.25, 0.45)                          # travel to the click (and to the bottom): min, nominal, max

# ---- panel
HOLE_R = 10.5                                       # the round hole; the rocker (9.6 at most) goes in and out through it
PIN_R, PIN_D, PIN_H = 13.5, 2.0, 1.5                # alignment pins on the panel's back
PIN_ANG = (30.0, 150.0, 270.0)                      # uneven, so the pod fits only one way... (see PIN_ANG_KEY)
PIN_ANG = (20.0, 150.0, 270.0)
RELIEF_R = 15.8                                     # the plug is cut back this far round the pod

# ---- pod
POD_R = 15.0
Y_COVER = 1.0                                       # switch covers, 1 mm behind the panel's back
Y_BASE = Y_COVER + TACT_BODY                        # 4.61
FLOOR_T = 1.2
Y_BACK = Y_BASE + FLOOR_T                           # 5.81, the pod's back
POCKET = 6.3
NOTCH = v1.NOTCH
SEAT_R = 3.6                                        # flat seat for the feet, its top level with the covers
Y_SEAT = Y_COVER
PIN_HOLE = PIN_D + 0.3
SCREW_HOLE = (3.4, 6.0)                             # through the seat: 3.4 at the seat, opening out to the back for the swing

# ---- rocker
BTN_GAP = 0.15                                      # pusher to button at rest
PUSH_H, PUSH_R = 0.4, 1.5
Y_BTN = Y_COVER - TACT_PROUD                        # button tops -0.39
Y_PB = Y_BTN - BTN_GAP - PUSH_H                     # plate back -0.94
PL_T = 1.2
Y_PF = Y_PB - PL_T                                  # plate face -2.14
FOOT_RHO, FOOT_D = 2.4, 1.6                         # 8 feet on 22.5 + 45k degrees: octagon edges 2.22 out
ARM_W, ARM_L = 6.0, 9.0
STEM_D = 7.0
TAP_D = 2.5                                         # the M3 self-taps into this

# ---- cap (Rev 1's), and its gap over the panel face: the backstop
CAP_GAP = 2.6
Y_CAPB = FACE - CAP_GAP                             # -5.1
SOCKET = (STEM_D + 0.25, 2.0)
Y_STEM_END = Y_CAPB - SOCKET[1] + 0.1

# ---- screw and spring, behind the pod
SCREW_L, HEAD_D = 20.0, 6.0
Y_TIP = Y_STEM_END + 0.3                            # the screw's tip, just short of the tap hole's end
Y_HEAD = Y_TIP + SCREW_L                            # its head's flat top
CUP_D, CUP_T = 8.0, 1.0
CUP_SEAT = (4.4, 0.4)


def ang_pts(r, angles):
    return [(r * np.sin(np.radians(a)), r * np.cos(np.radians(a))) for a in angles]


def btn_pts():
    return ang_pts(PITCH, (0, 90, 180, 270))


def foot_pts():
    return ang_pts(FOOT_RHO, [22.5 + 45 * k for k in range(8)])


def at4(c):
    out = mf.CrossSection()
    for k in range(4):
        out += c.rotate(-90.0 * k)
    return out


# ---------------------------------------------------------------- panel
def lower_panel():
    """Rev 5's lower panel, its hat a round hole and three pins. Box frame (panel coordinates)."""
    p = prism(h.LOWER_PANEL, -h.PANEL_T, 0)
    p -= h.outline_chamfers(h.LOWER_PANEL, -h.PANEL_T, -1.0, h.PANEL_CHAMFER)
    opening = h.BODY.offset(-h.WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in h.COLUMNS] + [(*h.GOV, h.NUT_RELIEF["toggle"]), (*h.LDG_EXT, h.NUT_RELIEF["toggle"]),
                                                   (*SEARCH, 2 * RELIEF_R)]
    p += prism(h.plug(opening, holes), -0.01, h.PLUG_H)
    p += h.toggle_box(*h.GOV, 0.0, opening, h.COLUMNS) + h.toggle_box(*h.LDG_EXT, 0.0, opening, h.COLUMNS)
    p -= prism(h.toggle_cut(*h.GOV) + h.toggle_cut(*h.LDG_EXT) + h.large_pb_cut(*h.STOP_REL), -h.PANEL_T - 1, h.PLUG_H + 1)
    for x, z in h.COLUMNS:
        p -= h.csk(x, z, -h.PANEL_T, +1, h.PANEL_CSK)
    p -= ycyl(SEARCH[0], SEARCH[1], 2 * HOLE_R, -h.PANEL_T - 1, 1.0)
    for x, z in ang_pts(PIN_R, PIN_ANG):
        p += ycyl(SEARCH[0] + x, SEARCH[1] + z, PIN_D, -0.01, PIN_H - 0.3) + ycyl(SEARCH[0] + x, SEARCH[1] + z, PIN_D, PIN_H - 0.31, PIN_H, PIN_D - 0.6)
    return h.inlay(p, h.lower_labels(), -h.PANEL_T)


# ---------------------------------------------------------------- pod
def pod():
    d = ycyl(0, 0, 2 * POD_R, 0.0, Y_BACK)
    d -= prism(at4(rect(-POCKET / 2, PITCH - POCKET / 2, POCKET / 2, PITCH + POCKET / 2)), -1.0, Y_BASE)
    d -= prism(at4(rect(NOTCH[0], PITCH - NOTCH[2] / 2, NOTCH[1], PITCH + NOTCH[2] / 2)
                   + rect(-NOTCH[1], PITCH - NOTCH[2] / 2, -NOTCH[0], PITCH + NOTCH[2] / 2)), Y_BASE - 1.2, Y_BACK + 1)
    # the middle: down to the seat, except the seat itself
    d -= ycyl(0, 0, 2 * (HOLE_R + 0.3), -1.0, Y_SEAT)
    d -= ycyl(0, 0, SCREW_HOLE[0], Y_SEAT - 1, Y_SEAT + 0.6) + ycyl(0, 0, SCREW_HOLE[0], Y_SEAT + 0.59, Y_BACK + 0.01, SCREW_HOLE[1])
    for x, z in ang_pts(PIN_R, PIN_ANG):
        d -= ycyl(x, z, PIN_HOLE, -1.0, PIN_H + 0.4)
    return d


# ---------------------------------------------------------------- rocker
def plate_outline():
    arms = rect(-ARM_W / 2, -ARM_L, ARM_W / 2, ARM_L) + rect(-ARM_L, -ARM_W / 2, ARM_L, ARM_W / 2)
    return arms.offset(-0.8, mf.JoinType.Round).offset(0.8, mf.JoinType.Round).offset(0.6, mf.JoinType.Round).offset(-0.6, mf.JoinType.Round)


def rocker(trim=0.0):
    p = prism(plate_outline(), Y_PF, Y_PB)
    r = FOOT_D / 2
    for x, z in foot_pts():
        p += ycyl(x, z, FOOT_D, Y_PB - 0.01, Y_SEAT - r - trim)
        p += mf.Manifold.sphere(r, 32).translate((x, Y_SEAT - r - trim, z)) - ycyl(x, z, 2 * r + 1, Y_PB - 1, Y_SEAT - r - trim)
    for x, z in btn_pts():
        yc = Y_PB + PUSH_H - PUSH_R
        p += mf.Manifold.sphere(PUSH_R, 48).translate((x, yc, z)) - ycyl(x, z, 2 * PUSH_R + 1, yc - PUSH_R - 1, Y_PB)
    p += ycyl(0, 0, STEM_D, Y_STEM_END, Y_PF + 0.01)
    p -= ycyl(0, 0, TAP_D, Y_STEM_END + 0.3, Y_PB + 1)
    return p


def cap():
    """Rev 1's cap at the new height (its four leg sockets left, unused), with a socket for the stem."""
    c = v1.cap().translate((0, Y_CAPB - v1.Y_CAPB, 0))
    return c - ycyl(0, 0, SOCKET[0], Y_CAPB - SOCKET[1], Y_CAPB + 0.1)


def cup():
    c = ycyl(0, 0, CUP_D, Y_BACK, Y_BACK + CUP_T)
    c -= ycyl(0, 0, 3.4, Y_BACK - 1, Y_BACK + CUP_T + 1)
    c -= ycyl(0, 0, CUP_SEAT[0], Y_BACK + CUP_T - CUP_SEAT[1], Y_BACK + CUP_T + 1)
    return c


def screw():
    hh = (HEAD_D - 3.0) / 2
    return ycyl(0, 0, 3.0, Y_TIP, Y_HEAD - hh + 0.01) + ycyl(0, 0, 3.0, Y_HEAD - hh, Y_HEAD, HEAD_D)


def spring_len():
    return (Y_HEAD - (HEAD_D - 3.6) / 2) - (Y_BACK + CUP_T - CUP_SEAT[1])


def tact(k):
    a = -90.0 * k
    body = prism(rect(-3.0, PITCH - 3.0, 3.0, PITCH + 3.0).rotate(a), Y_COVER, Y_BASE)
    x, z = btn_pts()[k]
    return body, ycyl(x, z, 2 * BTN_R, Y_BTN, Y_COVER + 0.01)


# ---------------------------------------------------------------- tipping (as Rev 2: about a line on the seat plane)
def tip_matrix(n, d, theta):
    nv = np.array([n[0], 0.0, n[1]])
    u = np.cross(nv, [0.0, 1.0, 0.0])
    u /= np.linalg.norm(u)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * K @ K
    c = np.array([d * n[0], Y_SEAT, d * n[1]])
    return R, c - R @ c


def tipped(m, n, d, theta):
    R, t = tip_matrix(n, d, theta)
    return m.transform(np.hstack([R, t.reshape(3, 1)]).tolist())


def btn_travel(n, d, theta):
    """How far each button is pushed in (beyond BTN_GAP)."""
    R, t = tip_matrix(n, d, theta)
    a = np.radians(np.linspace(0, 360, 72, endpoint=False))
    e = np.radians(np.linspace(0, 40, 21))
    A, E = np.meshgrid(a, e)
    dome = np.stack([PUSH_R * np.sin(E) * np.cos(A), PUSH_R * np.cos(E), PUSH_R * np.sin(E) * np.sin(A)], -1).reshape(-1, 3)
    out = []
    for bx, bz in btn_pts():
        pts = dome + [bx, Y_PB + PUSH_H - PUSH_R, bz]
        dy = (pts @ R.T + t)[:, 1].max() - (Y_PB + PUSH_H)
        out.append(max(0.0, dy - BTN_GAP))
    return out


def modes():
    pts = np.array(foot_pts())
    pts = pts[np.argsort(np.arctan2(pts[:, 0], pts[:, 1]))]
    edges = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        e = b - a
        n = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        if n @ a < 0:
            n = -n
        edges.append((n, float(n @ a), b))
    names = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}
    out = []
    for i, (n, d, b) in enumerate(edges):
        deg = int(round(np.degrees(np.arctan2(n[0], n[1])))) % 360
        out.append((f"edge {names.get(deg, deg)}", n, d))
        n2 = edges[(i + 1) % len(edges)][0]
        for f in (0.25, 0.5, 0.75):
            m = (1 - f) * n + f * n2
            m /= np.linalg.norm(m)
            out.append((f"corner {np.degrees(np.arctan2(m[0], m[1])) % 360:5.1f}", m, float(m @ b)))
    return out


def check():
    vol = lambda m: m.volume() if m.num_vert() else 0.0
    panel = lower_panel()[0].translate((-SEARCH[0], 0, -SEARCH[1])) ^ h.box(-20, -3.0, -20, 20, 9.0, 20)
    bodies, buttons = mf.Manifold(), mf.Manifold()
    for k in range(4):
        b, bt = tact(k)
        bodies += b
    fixed = {"panel": panel, "pod": pod(), "switch bodies": bodies}
    print("at rest:")
    rest = {"rocker": rocker(), "cap": cap(), "screw": screw(), "cup": cup()}
    bad = 0
    for a, ma in rest.items():
        for b, mb in fixed.items():
            v = vol(ma ^ mb)
            bad += v > 0.002
            print(f"  {a:6s} x {b:14s} {v:7.3f} mm3")
    v = vol(pod() ^ panel)
    print(f"  pod    x panel          {v:7.3f} mm3")
    print(f"  spring fitted length {spring_len():.2f} mm; octagon edges {FOOT_RHO * np.cos(np.radians(22.5)):.2f} mm out")
    unit = rocker(trim=0.1) + cap() + screw()

    def hits(theta, n, d):
        u = tipped(unit, n, d, theta)
        return [k for k, m in fixed.items() if vol(u ^ m) > 0.002]

    def bottomed(theta, n, d):
        return max(btn_travel(n, d, theta)) >= CLICK[2]

    print("\nevery way it can tip: where the first button bottoms (worst-case switch, 0.45 mm), and what the plate hits first")
    print(f"  {'mode':14s} {'click':>6s} {'bottom':>6s} {'free to':>7s}  {'N':>5s} {'E':>5s} {'S':>5s} {'W':>5s}  (travel at bottom)")
    worst3 = 0.0
    for label, n, d in modes():
        ths = np.radians(np.arange(0, 25, 0.05))
        tc = next((t for t in ths if max(btn_travel(n, d, t)) >= CLICK[1]), None)
        tb = next((t for t in ths if bottomed(t, n, d)), None)
        lo, hi = 0.0, np.radians(25)
        assert not hits(1e-4, n, d), (label, hits(1e-4, n, d))
        for _ in range(12):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if hits(mid, n, d) else (mid, hi)
        tr = btn_travel(n, d, tb if tb is not None else lo)
        worst3 = max(worst3, sorted(tr)[-3])
        if tb is None or tb > lo:
            bad += 1
        f = lambda t: f"{np.degrees(t):5.1f}d" if t is not None else "  -   "
        print(f"  {label:14s} {f(tc)} {f(tb)} {f(lo)}   " + " ".join(f"{v:5.2f}" for v in tr) + "   " + ", ".join(hits(hi, n, d)))
    print(f"\nmost a third button moves: {worst3:.3f} mm (clicks from {CLICK[0]})")
    bad += worst3 >= CLICK[0]
    print("all clear" if not bad else f"{bad} problem(s)")


def print_pose(m, front_down=True):
    bb = m.bounding_box()
    if front_down:
        return m.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -bb[1]]])
    return m.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, bb[4]]])


if __name__ == "__main__":
    if sys.argv[1] == "--check":
        check()
        sys.exit()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    lp, lt = lower_panel()
    save(h.tilt(lp), os.path.join(out, "HueyHeadR5-LowerPanel3-Black.stl"))
    save(h.tilt(lt), os.path.join(out, "HueyHeadR5-LowerPanel3-WhiteText.stl"))
    save(print_pose(pod(), False), os.path.join(out, "HueyHeadR5-Hat3-Pod.stl"))
    save(print_pose(rocker()), os.path.join(out, "HueyHeadR5-Hat3-Rocker.stl"))
    save(print_pose(cup()), os.path.join(out, "HueyHeadR5-Hat3-SpringCup.stl"))
    save(print_pose(cap(), False), os.path.join(out, "HueyHeadR5-Hat3-Cap.stl"))
