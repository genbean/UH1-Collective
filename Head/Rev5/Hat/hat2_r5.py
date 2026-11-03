# UH-1 head Rev 5: the SEARCH CONT hat, Rev 2. It fits the carrier already printed in the lower panel (hat_r5.py's),
# so the panel, the switches and the bezel's M2 holes stay; the bezel, rocker plate and cap are new, with a spring.
#
# Rev 1 rocks on one point, its set screw's tip under the bezel. Two faults follow from that:
#   - a push on the middle is stopped only by the screw's rear end, 0.1 mm off the hub's floor, which the print can't
#     hold, so a straight push clicks all four switches;
#   - a point pivot tilts as freely to the diagonals as to the sides, and a 45 degree push moves both neighbours'
#     buttons 0.71 x as far as a straight one, so the thumb has to be within a few degrees to get only one.
#
# Rev 2 sits the plate on eight feet instead, two on each switch's metal cover, either side of its button, and a pen
# spring holds it down on them. So:
#   - a push anywhere inside the feet's octagon moves nothing: all four feet are already down;
#   - a push toward a switch tips the plate over the two feet on that switch (an edge of the octagon 4.6 mm out), and
#     the button 7 mm out goes in, 2.4 mm beyond the edge;
#   - a push toward a diagonal tips it over the edge between the two feet nearest it, 4.81 mm out, which passes 0.14 mm
#     from either button: they move 0.06 x what the pressed one does on a straight push, never to the click.
# The feet bear on the switches' own covers, so the gap from plate to button is set by the switch and this one printed
# part, not by the carrier's bridged faces.
#
# Stack, box frame, hat centre at the origin, y positive toward the rear wall (the panel's face is y = -2.5, its back 0):
#
#    cap, as Rev 1, floats CAP_GAP over the bezel; its rim on the bezel stops the tilt   y -13.7 .. -5.7
#    M3 x 12 countersunk, fixed: threads into the carrier's 2.4 mm key hole, head under the cap
#    pen spring, from the screw head's cone down to the cup                                      (3 mm when fitted)
#    cup, printed, on the plate's face round the screw                                          y -2.95 .. -1.75
#    bezel, 1.6 mm ring on the panel face, with four ears to Rev 1's M2 screws on the diagonals   y  -4.1 .. -2.5
#    rocker plate, a 1.2 mm plus; four legs forward to the cap; eight feet and a boss behind     y -1.75 .. -0.55
#    feet, on the switches' covers                                                                   to y 0.9
#    four TE 1825910-6 in the carrier, unchanged                                                covers at y 0.9
#
# usage: hat2_r5.py <out dir> [asm dir]          (writes the four printed parts; with asm dir, the assembly too)
#        hat2_r5.py --check                       (the kinematic check: every way the plate can tip, and how far)
import os
import sys
import numpy as np
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hat_r5 as v1
import huey_head_r5 as h
from huey_head_r5 import rect, circle, prism, ycyl, save

SEARCH = h.SEARCH
PITCH = v1.PITCH                       # switch centres, N / E / S / W, 7 mm out
Y_COVER = v1.Y_COVER                   # the switches' covers, flush with the carrier's face          0.9
TACT_PROUD = h.TACT_H - h.TACT_BODY    # button top over the cover, 1.4 (datasheet)
BTN_R = 1.75                           # the button, 3.5 mm
CLICK = (0.15, 0.25, 0.45)             # its travel to the click: min, nominal, max (datasheet 0.25 +0.20 / -0.10)

# ---- rocker plate
BTN_GAP = 0.05                         # plate to button at rest. Anything from -0.10 (the plate rides on the buttons,
                                       # 0.1 mm off its feet) to +0.15 works; see the README
PUSH_H, PUSH_R = 0.4, 1.5             # a domed pusher over each button, 0.4 high on a 1.5 mm sphere (2 mm across): it
                                       # meets the button at its centre however the plate tips, not at its rim
FOOT_L = TACT_PROUD + BTN_GAP + PUSH_H # feet stand this far behind the plate
FOOT = (2.5, 4.6)                      # (across, out) of each switch's two feet, on its cover (6 x 6, from 4.0 out)
FOOT_D = 1.6                           # round feet, domed ends
Y_PB = Y_COVER - FOOT_L                # plate's back                                                  -0.95
PL_T = 1.2
Y_PF = Y_PB - PL_T                     # and its face                                                  -2.15
ARM_W, ARM_L = 6.0, 9.2                # plus arms, 6 wide (clear of the bezel's ears as they tip; the feet overhang their edges 0.3), to 9.2 out
BOSS_D, Y_BOSS = 5.2, 1.3              # boss into the carrier's 5.8 mm hub bore (floor at 1.6): it keeps the plate central
HOLE_PL, HOLE_BOSS = 5.0, (4.4, 3.4)   # clearance for the screw: the plate swings round it as it tips, most at its face
                                       # (the boss's hole tapers from 4.4 at the plate's back to 3.4 at its end)
LEG_D, FLARE_D, FLARE_H = v1.LEG_D, v1.FLARE_D, v1.FLARE_H

# ---- bezel: a ring now, so the far arms can rise past it as the plate tips
Y_BU, Y_BF = v1.Y_BU, v1.Y_BF          # underside on the panel face -2.5, front -4.1
BEZ_R, RING_IN = v1.BEZ_R, 10.3
EAR_R = 2.6                            # round ears at the M2 screws, 8.8 out on the diagonals
M2_R = 8.8

# ---- cap
CAP_GAP = 1.4                          # cap over the bezel; its rim landing on the bezel's edge is the tilt stop
Y_CAPB = Y_BF - CAP_GAP                # -5.5
RECESS_D, RECESS_H = 8.4, 1.7          # pocket in the cap's underside for the screw head

# ---- spring stack
SCREW_L, HEAD_D = 12.0, 6.0            # M3 x 12 countersunk (kit), 90 degree head
Y_HEAD = -6.8                          # its head's top, as fitted
CUP_D, CUP_T, CUP_HOLE = 7.0, 1.0, 3.4
CUP_SEAT = (4.4, 0.4)                  # the spring's end sits in this
Y_CUP = Y_PF - CUP_T                   # cup's top


def at4(c):
    out = mf.CrossSection()
    for k in range(4):
        out += c.rotate(-90.0 * k)
    return out


def foot_pts():
    """The eight feet's (x, z), going round."""
    pts = []
    for k in range(4):
        a = np.radians(90 * k)
        for s in (-1, 1):
            x, z = s * FOOT[0], FOOT[1]
            pts.append((x * np.cos(a) + z * np.sin(a), -x * np.sin(a) + z * np.cos(a)))
    return pts


def btn_pts():
    return [(PITCH * np.sin(np.radians(90 * k)), PITCH * np.cos(np.radians(90 * k))) for k in range(4)]


# ---------------------------------------------------------------- rocker plate
def plate_outline():
    arms = rect(-ARM_W / 2, -ARM_L, ARM_W / 2, ARM_L) + rect(-ARM_L, -ARM_W / 2, ARM_L, ARM_W / 2)
    return arms.offset(-0.8, mf.JoinType.Round).offset(0.8, mf.JoinType.Round).offset(0.6, mf.JoinType.Round).offset(-0.6, mf.JoinType.Round)


def plate(trim=0.0):
    """Plate, legs forward, feet and boss behind. trim shortens the feet (the check uses it to leave out their
    rolling contact)."""
    arms = plate_outline()
    p = prism(arms, Y_PF, Y_PB)
    p += ycyl(0, 0, BOSS_D, Y_PB - 0.01, Y_BOSS)
    for x, z in foot_pts():
        r = FOOT_D / 2
        p += ycyl(x, z, FOOT_D, Y_PB - 0.01, Y_COVER - r - trim)
        p += mf.Manifold.sphere(r, 32).translate((x, Y_COVER - r - trim, z)) - ycyl(x, z, 2 * r + 1, Y_PB - 1, Y_COVER - r - trim)
    for x, z in btn_pts():
        yc = Y_PB + PUSH_H - PUSH_R
        p += mf.Manifold.sphere(PUSH_R, 48).translate((x, yc, z)) - ycyl(x, z, 2 * PUSH_R + 1, yc - PUSH_R - 1, Y_PB)
    p -= ycyl(0, 0, HOLE_PL, Y_PF - 1, Y_PB + 0.01)
    p -= ycyl(0, 0, HOLE_BOSS[0], Y_PB - 0.02, Y_BOSS + 0.01, HOLE_BOSS[1] - (HOLE_BOSS[0] - HOLE_BOSS[1]) * 0.01 / (Y_BOSS - Y_PB))
    for x, z in btn_pts():
        p += ycyl(x, z, LEG_D, Y_CAPB - v1.LEG_SOCKET + 0.1, Y_PF + 0.01)
        p += ycyl(x, z, LEG_D, Y_PF - FLARE_H, Y_PF + 0.01, FLARE_D) ^ prism(arms, Y_PF - FLARE_H - 1, Y_PF + 0.01)
    return p


# ---------------------------------------------------------------- bezel
def bezel():
    ring = circle(2 * BEZ_R) - circle(2 * RING_IN)
    for k in (45, 135, 225, 315):
        a = np.radians(k)
        x, z = M2_R * np.cos(a), M2_R * np.sin(a)
        ring += circle(2 * EAR_R, x, z) + rect(-EAR_R, 0, EAR_R, BEZ_R).rotate(k - 90).translate((x, z)) ^ circle(2 * BEZ_R)
    b = prism(ring, Y_BF + 0.4, Y_BU) + (prism(ring.offset(-0.4, mf.JoinType.Round), Y_BF, Y_BF + 0.41))
    for k in (45, 135, 225, 315):
        x, z = M2_R * np.cos(np.radians(k)), M2_R * np.sin(np.radians(k))
        b -= ycyl(x, z, 2.4, Y_BF - 1, Y_BU + 1)
        b -= ycyl(x, z, 4.5, Y_BF - 0.01, Y_BF + 1.05, 2.4)       # 90 degree countersink for an M2 head
    return b


# ---------------------------------------------------------------- cap: Rev 1's, raised to the new bezel gap, with a pocket for the screw head
def cap():
    c = v1.cap().translate((0, Y_CAPB - v1.Y_CAPB, 0))
    return c - ycyl(0, 0, RECESS_D, Y_CAPB - RECESS_H, Y_CAPB + 0.1)


# ---------------------------------------------------------------- the spring's cup
def cup():
    c = ycyl(0, 0, CUP_D, Y_CUP, Y_PF)
    c -= ycyl(0, 0, CUP_HOLE, Y_CUP - 1, Y_PF + 1)
    c -= ycyl(0, 0, CUP_SEAT[0], Y_CUP - 1, Y_CUP + CUP_SEAT[1])
    return c


# ---------------------------------------------------------------- hardware stand-ins
def screw(in_hole=3.0):
    """M3 x 12 countersunk, head top at Y_HEAD. in_hole = 2.4 gives the check a screw that leaves out the thread it
    cuts in the key hole (behind the hub bore's floor); it is 3 mm everywhere else."""
    hh = (HEAD_D - 3.0) / 2
    return (ycyl(0, 0, HEAD_D, Y_HEAD, Y_HEAD + hh, 3.0) + ycyl(0, 0, 3.0, Y_HEAD + hh - 0.01, v1.Y_REAR_STOP)
            + ycyl(0, 0, in_hole, v1.Y_REAR_STOP - 0.01, Y_HEAD + SCREW_L))


def spring_len():
    """Fitted length of the spring: cup seat to where a 3.6 mm mean coil meets the head's cone."""
    return (Y_CUP + CUP_SEAT[1]) - (Y_HEAD + (HEAD_D - 3.6) / 2)


def spring():
    L = spring_len()
    y1 = Y_CUP + CUP_SEAT[1]
    return ycyl(0, 0, 4.0, y1 - L, y1) - ycyl(0, 0, 3.2, y1 - L - 1, y1 + 1)


def m2_screws():
    out = mf.Manifold()
    for k in (45, 135, 225, 315):
        x, z = M2_R * np.cos(np.radians(k)), M2_R * np.sin(np.radians(k))
        out += ycyl(x, z, 4.0, Y_BF, Y_BF + 1.0, 2.0) + ycyl(x, z, 2.0, Y_BF + 0.99, Y_BF + 8.0)
    return out


# ---------------------------------------------------------------- tipping
def tip_matrix(n, d, theta):
    """Rotation by theta about the line on the covers' plane (y = Y_COVER) at distance d out along n (a unit (x, z)),
    the side beyond the line going back (+y)."""
    nv = np.array([n[0], 0.0, n[1]])
    u = np.cross(nv, [0.0, 1.0, 0.0])
    u /= np.linalg.norm(u)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * K @ K
    c = np.array([d * n[0], Y_COVER, d * n[1]])
    return R, c - R @ c


def tipped(m, n, d, theta):
    R, t = tip_matrix(n, d, theta)
    return m.transform(np.hstack([R, t.reshape(3, 1)]).tolist())


def btn_travel(n, d, theta):
    """How far each button is pushed in (mm, less BTN_GAP): how far behind its rest the pusher's dome reaches."""
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
    """Every way the plate can tip off its feet: over each edge of their octagon, and over each corner (a foot) with
    the tipping line turned anywhere between its two edges'. Returns (label, n, d)."""
    pts = np.array(foot_pts())
    ang = np.arctan2(pts[:, 0], pts[:, 1])
    pts = pts[np.argsort(ang)]
    out = []
    names = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}
    edges = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        e = b - a
        n = np.array([e[1], -e[0]])
        n /= np.linalg.norm(n)
        if n @ a < 0:
            n = -n
        edges.append((n, float(n @ a), a, b))
    for i, (n, d, a, b) in enumerate(edges):
        deg = int(round(np.degrees(np.arctan2(n[0], n[1])))) % 360
        out.append((f"edge {names.get(deg, deg)}", n, d))
        n2 = edges[(i + 1) % len(edges)][0]
        for f in (0.25, 0.5, 0.75):                    # over the foot b, between this edge and the next
            m = (1 - f) * n + f * n2
            m /= np.linalg.norm(m)
            dd = np.degrees(np.arctan2(m[0], m[1])) % 360
            out.append((f"corner {dd:5.1f}", m, float(m @ b)))
    return out


def check():
    lp, _ = v1.lower_panel_new()
    panel = lp.translate((-SEARCH[0], 0, -SEARCH[1])) ^ h.box(-16, -3.0, -16, 16, 9.0, 16)
    tacts = mf.Manifold()
    for k in range(4):
        b, bt, lg = v1.tact(k)
        tacts += b
    fixed = {"bezel": bezel(), "panel": panel, "switch bodies": tacts, "screw": screw(2.4), "M2 screws": m2_screws()}
    unit = plate(trim=0.1) + cap()
    vol = lambda m: m.volume() if m.num_vert() else 0.0

    print("at rest:")
    rest = {"plate": plate(), "cap": cap(), "cup": cup(), "bezel": fixed["bezel"]}
    for a, ma in rest.items():
        for b, mb in fixed.items():
            if a != b:
                print(f"  {a:6s} x {b:14s} {vol(ma ^ mb):7.3f} mm3")
    print(f"  spring fitted length {spring_len():.2f} mm; the plate's centre rises at most "
          f"{FOOT[1] * np.radians(14):.2f} mm more as it tips")

    def hits(theta, n, d):
        u = tipped(unit, n, d, theta)
        return [k for k, m in fixed.items() if vol(u ^ m) > 0.002]

    print("\nevery way it can tip, to where it stops:")
    print(f"  {'mode':14s} {'stop':>6s}  {'N':>5s} {'E':>5s} {'S':>5s} {'W':>5s}   stopped by")
    worst_two = 0.0
    for label, n, d in modes():
        lo, hi = 0.0, np.radians(25)
        assert not hits(lo + 1e-4, n, d), (label, hits(lo + 1e-4, n, d))
        for _ in range(14):
            mid = (lo + hi) / 2
            if hits(mid, n, d):
                hi = mid
            else:
                lo = mid
        tr = btn_travel(n, d, lo)
        s = sorted(tr)
        worst_two = max(worst_two, s[-2])
        print(f"  {label:14s} {np.degrees(lo):5.1f}d  " + " ".join(f"{v:5.2f}" for v in tr) + "   " + ", ".join(hits(hi, n, d)))
    print(f"\nmost any second button moves: {worst_two:.3f} mm (clicks from {CLICK[0]} mm at the least)")


def print_pose(m):
    y0 = m.bounding_box()[1]
    return m.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -y0]])


def write_parts(out):
    save(print_pose(bezel()), os.path.join(out, "HueyHeadR5-Hat2-Bezel.stl"))
    save(print_pose(plate()), os.path.join(out, "HueyHeadR5-Hat2-RockerPlate.stl"))
    save(print_pose(cup()), os.path.join(out, "HueyHeadR5-Hat2-SpringCup.stl"))
    c_ = cap()
    save(c_.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, c_.bounding_box()[4]]]), os.path.join(out, "HueyHeadR5-Hat2-Cap.stl"))


if __name__ == "__main__":
    if sys.argv[1] == "--check":
        check()
        sys.exit()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write_parts(out)
    if len(sys.argv) > 2:
        asm_dir = sys.argv[2]
        os.makedirs(asm_dir, exist_ok=True)
        asm = {"bezel": bezel(), "plate": plate(), "cap": cap(), "cup": cup(), "screw": screw(), "spring": spring(),
               "m2": m2_screws()}
        for name, m in asm.items():
            save(m.translate((SEARCH[0], 0, SEARCH[1])), os.path.join(asm_dir, f"asm2_{name}.stl"))
