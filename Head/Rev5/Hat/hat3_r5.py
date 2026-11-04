# UH-1 head Rev 5: the SEARCH CONT hat, Rev 3, with its own lower panel.
#
# Rev 1 and 2 put the switch carrier in the lower panel. It hangs off the panel's back, so the panel needs supports
# there when it prints face down, and the faces that set the hat's fit come out rough. Rev 3 takes the hat out of the
# panel. The panel keeps only a round hole and three short pins on its back. Everything else is in a pod that is glued
# onto the pins from behind. Every part prints flat, without supports.
#
# How it works. A fixed octagonal anvil stands in the middle of the pod. The rocker's square boss sits on it, held there
# by a pen spring and an M3 screw from behind, and the four switches sit round it.
#   - Push the middle: the force goes straight into the anvil. Nothing moves, so no switch clicks.
#   - Push toward a switch: the rocker tips over the anvil's edge on that side, 2.6 mm out, and the switch 8.5 mm out
#     goes in. The far side lifts.
#   - Push toward a diagonal: it tips over the diagonal edge. Both neighbours are 6.0 mm out along it, beyond the
#     2.6 mm edge, so both go in: the hat works as an 8-way switch.
#   - The two switches opposite each other can never go in together, and nor can three.
# The boss is square and sits in a square bore, so the rocker can't slide or turn. Every gap that matters (anvil to
# switch to pusher) lies inside the pod or inside the rocker, each printed as one part, so the panel doesn't set any of
# it.
#
# Stack, box frame, hat centre at the origin, y positive toward the rear wall (the panel's face is y = -2.5, its back 0):
#
#    cap (Rev 1's knob), its underside CAP_GAP over the panel face; its rim on the face is the last-resort tilt stop
#    rocker: stem into the cap; a 45 degree cone out to a 20.2 mm disc in the panel's 23 mm hole; 4 domed pushers and a
#      square boss behind. An M3 nut sits in the stem's front end.                       y -8.2 .. 1.4
#    pod, glued to the panel's back on 3 pins                                               y  0 .. 6.2
#      four TE 1825910-6 in pockets, covers at 1.39, bases on the floor at 5.0, legs out the back to 8.5
#      the anvil's top, 1.4, in a square bore
#    cup, pen spring and the M3 x 20's countersunk head, behind the pod                    y  6.2 .. 12.2
#
# usage: hat3_r5.py <out dir> [asm dir]     (the panel and the hat's printed parts; with asm dir, the assembly too)
#        hat3_r5.py --check                  (overlaps at rest, then every way the rocker can tip and how far)
import os
import sys
import numpy as np
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import hat_r5 as v1
import huey_head_r5 as h
from huey_head_r5 import rect, circle, prism, ycyl, save

SEARCH = h.SEARCH
FACE = -h.PANEL_T                      # -2.5

# ---- the switch: TE 1825910-6, as hat_r5.py
TACT_H, TACT_BODY = h.TACT_H, h.TACT_BODY          # base to button top 5.00, base to cover 3.61
BTN_R = 1.75
CLICK = (0.15, 0.25, 0.45)             # travel to the click: min, nominal, max (datasheet 0.25 +0.20 / -0.10)

# ---- layout
PITCH = 8.5                            # switch centres, N / E / S / W (Rev 1/2: 7.0). Further out gives the diagonals more
                                       # lever over the anvil's edge
R_OCT = 2.6                            # the anvil: a regular octagon, edges facing N, NE, E, ..., this far out
POD_R, FLANGE_T = 16.5, 2.4            # pod: a 33 mm flange on the panel's back, then a 45 degree cone in to BACK_R
BACK_R = 13.0
Y_BACK = 6.2                           # pod's back (the face it prints on); its front is y = 0, on the panel
FLOOR_T = 1.2
Y_BASE = Y_BACK - FLOOR_T              # switch bases on the pocket floors                          5.0
Y_COVER = Y_BASE - TACT_BODY           #                                                            1.39
Y_BTN = Y_BASE - TACT_H                # button tops                                                0.0
Y_SEAT = Y_BACK - 4.8                  # the anvil's top, level with the covers (a whole number of 0.2 mm layers) 1.4
ANVIL_H = 0.8                          # the anvil stands this far out of the bore's floor
BORE_D = 0.8                           # the bore is this deep in front of the anvil's top
FRONT_R = 12.2                         # the pod's front recess: the switches go in through it (their corners at 12.04)
POCKET, NOTCH = v1.POCKET, v1.NOTCH    # 6.3 mm pockets, and the leg slots
PIN_R, PIN_D, PIN_H = 14.35, 2.0, 1.5  # the panel's pins; the pod's holes are PIN_D + 0.4, 2 mm deep
PIN_ANG = (45.0, 135.0, 270.0)         # degrees clockwise from N: no turn of the pod but the right one fits them
HOLE_R = 11.5                          # the panel's hole

# ---- rocker
BTN_GAP = 0.2                          # pusher to button at rest (whole layers: see the README)
PUSH_H, PUSH_R = 0.4, 1.5              # domed pushers, as Rev 2: they meet the button at its centre however it tips
BOSS = 3.0                             # square boss, 6 x 6, in a 6.6 mm bore
BOSS_CLR = 0.3
POST = 1.1                             # the pod's wall round the bore
Y_PB = Y_SEAT - (Y_SEAT - (Y_BTN - BTN_GAP)) - PUSH_H   # disc's back: pushers' tips BTN_GAP in front of the buttons  -0.6
DISC_R = 10.1
STEM_R = 6.0
CAP_GAP = 2.7                          # cap's underside over the panel face
Y_CAPB = FACE - CAP_GAP                # -5.2
SOCKET = 3.0                           # the stem goes this far into the cap
Y_STEM = Y_CAPB - SOCKET               # stem's front end                                           -8.2
NUT_AF, NUT_T, NUT_POCKET = 5.5, 2.4, 3.0

# ---- spring stack, behind the pod
CUP_D, CUP_T, CUP_SEAT = 10.0, 1.0, (4.4, 0.4)
SCREW_L, HEAD_D = 20.0, 6.0
Y_HEAD = 12.2                          # the screw head's top, as fitted: the tip ends 0.2 short of the nut's far face


def dirs():
    return [(np.sin(np.radians(90 * k)), np.cos(np.radians(90 * k))) for k in range(4)]


def btn_pts():
    return [(PITCH * a, PITCH * b) for a, b in dirs()]


def at4(c):
    out = mf.CrossSection()
    for k in range(4):
        out += c.rotate(-90.0 * k)
    return out


def octagon(r_in):
    R = r_in / np.cos(np.radians(22.5))
    return h.cs([(R * np.sin(np.radians(22.5 + 45 * k)), R * np.cos(np.radians(22.5 + 45 * k))) for k in range(8)])


def square(half):
    return rect(-half, -half, half, half)


# ---------------------------------------------------------------- panel
def lower_panel():
    """The lower panel with a round hole and three pins for the pod (hat_r5.lower_panel_new less its carrier)."""
    p = prism(h.LOWER_PANEL, -h.PANEL_T, 0)
    p -= h.outline_chamfers(h.LOWER_PANEL, -h.PANEL_T, -1.0, h.PANEL_CHAMFER)
    opening = h.BODY.offset(-h.WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in h.COLUMNS] + [(*h.GOV, h.NUT_RELIEF["toggle"]), (*h.LDG_EXT, h.NUT_RELIEF["toggle"]),
                                                   (*SEARCH, 2 * (POD_R + h.PLUG_CLR))]
    p += prism(h.plug(opening, holes), -0.01, h.PLUG_H)
    p += h.toggle_box(*h.GOV, 0.0, opening, h.COLUMNS) + h.toggle_box(*h.LDG_EXT, 0.0, opening, h.COLUMNS)
    p -= prism(h.toggle_cut(*h.GOV) + h.toggle_cut(*h.LDG_EXT) + h.large_pb_cut(*h.STOP_REL), -h.PANEL_T - 1, h.PLUG_H + 1)
    for x, z in h.COLUMNS:
        p -= h.csk(x, z, -h.PANEL_T, +1, h.PANEL_CSK)
    p -= ycyl(SEARCH[0], SEARCH[1], 2 * HOLE_R, -h.PANEL_T - 1, 1.0)
    for a in PIN_ANG:
        x, z = PIN_R * np.sin(np.radians(a)), PIN_R * np.cos(np.radians(a))
        p += ycyl(SEARCH[0] + x, SEARCH[1] + z, PIN_D, -0.01, PIN_H - 0.3) + ycyl(SEARCH[0] + x, SEARCH[1] + z, PIN_D, PIN_H - 0.31, PIN_H, PIN_D - 0.6)
    return h.inlay(p, h.lower_labels(), -h.PANEL_T)


# ---------------------------------------------------------------- pod
def pod():
    """Glued to the panel's back. Prints back down: pockets, bore, recess and pin holes all open upward."""
    rev = h.cs([(0, 0), (POD_R, 0), (POD_R, FLANGE_T), (BACK_R, FLANGE_T + POD_R - BACK_R), (BACK_R, Y_BACK), (0, Y_BACK)])
    p = mf.Manifold.revolve(rev, 192).rotate((-90, 0, 0))            # profile (r, y) turned round the y axis
    p -= ycyl(0, 0, 2 * FRONT_R, -1, Y_COVER + 0.01)                 # front recess, down to the covers
    p += prism(square(BOSS + BOSS_CLR + POST), Y_SEAT - BORE_D, Y_COVER + 0.02)   # the post round the bore
    p -= prism(square(BOSS + BOSS_CLR), Y_SEAT - BORE_D - 1, Y_SEAT + ANVIL_H)    # the bore
    p += prism(octagon(R_OCT), Y_SEAT, Y_SEAT + ANVIL_H + 0.01)                   # the anvil
    body = at4(rect(-POCKET / 2, PITCH - POCKET / 2, POCKET / 2, PITCH + POCKET / 2))
    notch = at4(rect(NOTCH[0], PITCH - NOTCH[2] / 2, NOTCH[1], PITCH + NOTCH[2] / 2)
                + rect(-NOTCH[1], PITCH - NOTCH[2] / 2, -NOTCH[0], PITCH + NOTCH[2] / 2))
    p -= prism(body, Y_COVER - 0.01, Y_BASE)
    p -= prism(notch, Y_BASE - 1.2, Y_BACK + 1.0)                    # the legs and their kinks, through the floor
    p -= screw_hole()
    for a in PIN_ANG:
        x, z = PIN_R * np.sin(np.radians(a)), PIN_R * np.cos(np.radians(a))
        p -= ycyl(x, z, PIN_D + 0.4, -1, 2.0)
    return p


def screw_hole():
    """Through the anvil: 3.6 at its top, opening out behind as far as the screw swings at the stop."""
    return ycyl(0, 0, 3.6, Y_SEAT - 1, Y_SEAT + 0.4) + ycyl(0, 0, 3.6, Y_SEAT + 0.39, Y_BACK + 0.01, 6.4)


# ---------------------------------------------------------------- rocker
def rocker():
    """Stem, cone, disc, boss and pushers. Prints stem down: the cone is 45 degrees and everything behind faces up."""
    yc = Y_CAPB                                                       # the cone starts at the cap's underside
    y1 = yc + (DISC_R - STEM_R)
    rev = h.cs([(0, Y_STEM), (STEM_R - 0.4, Y_STEM), (STEM_R, Y_STEM + 0.4), (STEM_R, yc), (DISC_R, y1), (DISC_R, Y_PB), (0, Y_PB)])
    r = mf.Manifold.revolve(rev, 192).rotate((-90, 0, 0))
    r += prism(square(BOSS), Y_PB - 0.01, Y_SEAT)
    for x, z in btn_pts():
        yc_ = Y_PB + PUSH_H - PUSH_R
        r += mf.Manifold.sphere(PUSH_R, 48).translate((x, yc_, z)) - ycyl(x, z, 2 * PUSH_R + 1, yc_ - PUSH_R - 1, Y_PB)
    r -= ycyl(0, 0, 3.4, Y_STEM - 1, Y_SEAT + 1)
    hexs = mf.CrossSection.circle((NUT_AF + 0.2) / 2 / np.cos(np.radians(30)), 6)
    r -= prism(hexs, Y_STEM - 1, Y_STEM + NUT_POCKET)
    return r


# ---------------------------------------------------------------- cap: Rev 1's knob, moved to CAP_GAP, with the stem's socket
def cap():
    c = v1.cap().translate((0, Y_CAPB - v1.Y_CAPB, 0))
    for x, z in btn_pts():                                            # Rev 1's leg sockets aren't used: fill them
        c += ycyl(x * 7.0 / PITCH, z * 7.0 / PITCH, v1.SOCKET_D + 0.02, Y_CAPB - v1.LEG_SOCKET - 0.01, Y_CAPB) ^ v1.cap().translate((0, Y_CAPB - v1.Y_CAPB, 0)).hull()
    c -= ycyl(0, 0, 2 * STEM_R + 0.25, Y_CAPB - SOCKET, Y_CAPB + 0.1)
    c -= ycyl(0, 0, 3.8, Y_CAPB - SOCKET - 2.5, Y_CAPB)               # room for the screw's tip as the spring is set
    return c


def cup():
    c = ycyl(0, 0, CUP_D, Y_BACK, Y_BACK + CUP_T)
    c -= ycyl(0, 0, 3.4, Y_BACK - 1, Y_BACK + CUP_T + 1)
    c -= ycyl(0, 0, CUP_SEAT[0], Y_BACK + CUP_T - CUP_SEAT[1], Y_BACK + CUP_T + 1)
    return c


# ---------------------------------------------------------------- hardware stand-ins
def screw():
    hh = (HEAD_D - 3.0) / 2
    return ycyl(0, 0, 3.0, Y_HEAD - hh, Y_HEAD, HEAD_D) + ycyl(0, 0, 3.0, Y_HEAD - SCREW_L, Y_HEAD - hh + 0.01)


def nut():
    hexs = mf.CrossSection.circle(NUT_AF / 2 / np.cos(np.radians(30)), 6)
    y1 = Y_STEM + NUT_POCKET
    return prism(hexs, y1 - NUT_T, y1) - ycyl(0, 0, 3.0, y1 - NUT_T - 1, y1 + 1)


def spring_len():
    return (Y_HEAD - (HEAD_D - 3.6) / 2) - (Y_BACK + CUP_T - CUP_SEAT[1])


def spring():
    y0 = Y_BACK + CUP_T - CUP_SEAT[1]
    return ycyl(0, 0, 4.0, y0, y0 + spring_len()) - ycyl(0, 0, 3.2, y0 - 1, y0 + spring_len() + 1)


def tact(k):
    """TE 1825910-6 at direction k (0 = N): (body, button, legs)."""
    a, b = dirs()[k]
    c = rect(-3.0, PITCH - 3.0, 3.0, PITCH + 3.0).rotate(-90.0 * k)
    body = prism(c, Y_COVER, Y_BASE)
    button = ycyl(PITCH * a, PITCH * b, 2 * BTN_R, Y_BTN, Y_COVER + 0.01)
    legs = mf.Manifold()
    for sx in (-1, 1):
        for sz in (-1, 1):
            lc = rect(sx * 3.25 - 0.15, PITCH + sz * 2.25 - 0.355, sx * 3.25 + 0.15, PITCH + sz * 2.25 + 0.355)
            tab = rect(min(sx * 2.9, sx * 3.4), PITCH + sz * 2.25 - 0.355, max(sx * 2.9, sx * 3.4), PITCH + sz * 2.25 + 0.355)
            legs += prism(lc.rotate(-90.0 * k), Y_BASE - 0.3, Y_BASE + v1.LEG_LEN) + prism(tab.rotate(-90.0 * k), Y_BASE - 0.3, Y_BASE + 0.01)
    return body, button, legs


# ---------------------------------------------------------------- tipping
def tip_matrix(n, d, theta):
    """Rotation by theta about the line in the anvil's top (y = Y_SEAT) d out along n (unit (x, z)); beyond the line
    goes back (+y)."""
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
    """How far each pusher's dome reaches behind its rest (mm): BTN_GAP of it is taken up before the button moves."""
    R, t = tip_matrix(n, d, theta)
    a = np.radians(np.linspace(0, 360, 72, endpoint=False))
    e = np.radians(np.linspace(0, 40, 21))
    A, E = np.meshgrid(a, e)
    dome = np.stack([PUSH_R * np.sin(E) * np.cos(A), PUSH_R * np.cos(E), PUSH_R * np.sin(E) * np.sin(A)], -1).reshape(-1, 3)
    out = []
    for bx, bz in btn_pts():
        pts = dome + [bx, Y_PB + PUSH_H - PUSH_R, bz]
        out.append(max(0.0, (pts @ R.T + t)[:, 1].max() - (Y_PB + PUSH_H)))
    return out


def modes():
    R = R_OCT / np.cos(np.radians(22.5))
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    out = []
    for k in range(8):
        a = np.radians(45 * k)
        out.append((f"edge {names[k]}", np.array([np.sin(a), np.cos(a)]), R_OCT))
        for f in (0.25, 0.5, 0.75):                     # over the corner between this edge and the next
            g = np.radians(45 * k + 45 * f)
            n = np.array([np.sin(g), np.cos(g)])
            v = np.radians(45 * k + 22.5)
            out.append((f"corner {np.degrees(g):5.1f}", n, float(R * np.cos(g - v))))
    return out


def vol(m):
    return m.volume() if m.num_vert() else 0.0


def check():
    lp, _ = lower_panel()
    panel = lp.translate((-SEARCH[0], 0, -SEARCH[1])) ^ h.box(-20, -3.0, -20, 20, 3.0, 20)
    bodies, buttons, legs = mf.Manifold(), mf.Manifold(), mf.Manifold()
    for k in range(4):
        b, bt, lg = tact(k)
        bodies, buttons, legs = bodies + b, buttons + bt, legs + lg
    P = pod()
    print("at rest:")
    pairs = {("pod", "panel"): (P, panel), ("pod", "switch bodies"): (P, bodies), ("pod", "switch legs"): (P, legs),
             ("rocker", "pod"): (rocker(), P), ("rocker", "panel"): (rocker(), panel),
             ("rocker", "switch bodies"): (rocker(), bodies), ("rocker", "buttons"): (rocker(), buttons),
             ("cap", "panel"): (cap(), panel), ("screw", "pod"): (screw(), P), ("nut", "rocker"): (nut(), rocker()),
             ("screw", "rocker"): (screw() - ycyl(0, 0, 3.0, -50, 50), rocker()), ("cup", "pod"): (cup(), P),
             ("cup", "switch legs"): (cup(), legs), ("spring", "switch legs"): (spring(), legs)}
    for (a, b), (ma, mb) in pairs.items():
        print(f"  {a:7s} x {b:14s} {vol(ma ^ mb):7.3f} mm3")
    pins = sum(vol(ycyl(PIN_R * np.sin(np.radians(a)), PIN_R * np.cos(np.radians(a)), PIN_D + 0.4, 0, 2.0) - P) for a in PIN_ANG)
    print(f"  pin holes {pins:.1f} mm3 open; pins {PIN_D} x {PIN_H} in {PIN_D + 0.4} x 2.0 holes")
    print(f"  pusher to button {BTN_GAP:.2f}; spring fitted {spring_len():.2f} mm; screw tip {Y_HEAD - SCREW_L:.2f}, nut "
          f"{Y_STEM + NUT_POCKET - NUT_T:.2f} .. {Y_STEM + NUT_POCKET:.2f}, stem front {Y_STEM:.2f}")

    fixed = {"panel": panel, "pod": pod_trim(P), "switch bodies": bodies}
    unit = rocker() + cap() + screw() + nut()
    loose = screw()                                      # the screw's shank in the pod: checked on its own

    def hits(theta, n, d):
        u = tipped(unit, n, d, theta)
        return [k for k, m in fixed.items() if vol(u ^ m) > 0.002]

    print("\nevery way it can tip, to where it stops (buttons left out: they bottom first, see the angles):")
    print(f"  {'mode':14s} {'stop':>6s}  {'N':>5s} {'E':>5s} {'S':>5s} {'W':>5s}  click nom/max at   stopped by")
    worst = []
    for label, n, d in modes():
        lo, hi = 0.0, np.radians(30)
        assert not hits(1e-4, n, d), (label, hits(1e-4, n, d))
        for _ in range(13):
            mid = (lo + hi) / 2
            if hits(mid, n, d):
                hi = mid
            else:
                lo = mid
        tr = btn_travel(n, d, lo)
        s = sorted(tr)

        def first(c):
            for t in np.radians(np.arange(0, 30, 0.1)):
                if max(btn_travel(n, d, t)) >= BTN_GAP + c:
                    return np.degrees(t)
            return float("nan")
        clicks = sum(v >= BTN_GAP + CLICK[2] for v in tr)
        worst.append((label, s[-3] if len(s) > 2 else 0, clicks))
        print(f"  {label:14s} {np.degrees(lo):5.1f}d  " + " ".join(f"{v:5.2f}" for v in tr) +
              f"  {first(CLICK[1]):4.1f} / {first(CLICK[2]):4.1f}d   " + ", ".join(hits(hi, n, d)))
    print(f"\nmost a third button moves: {max(w[1] for w in worst):.3f} mm (a click needs {BTN_GAP + CLICK[0]:.2f} at the least)")


def pod_trim(P):
    """The pod with the anvil's top let down 0.02, so rolling on its edge isn't counted as a hit."""
    return P - prism(octagon(R_OCT + 0.1), Y_SEAT - 0.5, Y_SEAT + 0.02)


# ---------------------------------------------------------------- output
def pose_back_down(m):
    """Back (largest y) on the bed, front up."""
    y1 = m.bounding_box()[4]
    return m.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, y1]])


def write_parts(out):
    lp, txt = lower_panel()
    save(h.tilt(lp), os.path.join(out, "HueyHeadR5-LowerPanel-Hat3-Black.stl"))
    save(h.tilt(txt), os.path.join(out, "HueyHeadR5-LowerPanel-Hat3-WhiteText.stl"))
    save(pose_back_down(pod()), os.path.join(out, "HueyHeadR5-Hat3-Pod.stl"))
    save(v1.print_pose(rocker()), os.path.join(out, "HueyHeadR5-Hat3-Rocker.stl"))
    save(pose_back_down(cap()), os.path.join(out, "HueyHeadR5-Hat3-Cap.stl"))
    save(v1.print_pose(cup()), os.path.join(out, "HueyHeadR5-Hat3-SpringCup.stl"))


def assembly():
    a = {"panel": lower_panel()[0], "pod": pod(), "rocker": rocker(), "cap": cap(), "cup": cup(), "screw": screw(),
         "nut": nut(), "spring": spring()}
    for k in range(4):
        b, bt, lg = tact(k)
        a[f"tact{k}"] = b + bt + lg
    return {k: (m if k == "panel" else m.translate((SEARCH[0], 0, SEARCH[1]))) for k, m in a.items()}


if __name__ == "__main__":
    if sys.argv[1] == "--check":
        check()
        sys.exit()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write_parts(out)
    if len(sys.argv) > 2:
        os.makedirs(sys.argv[2], exist_ok=True)
        for k, m in assembly().items():
            save(m, os.path.join(sys.argv[2], f"asm3_{k}.stl"))
