# UH-1 head Rev 5: the SEARCH CONT hat, Rev 4. An ALPS RKJXM1015004 8-direction stick switch on a small breakout
# board (PCB/SearchHat_Rev1.0), screwed to four bosses printed on the lower panel's back, and a cap on the stick.
#
# Rev 3 built the 8-way action out of four tact switches and a printed rocker. Rev 4 buys it: the RKJXM is a sealed
# 8-direction stick with its own stops (10 degrees toward a side, 12 toward a diagonal) and a centre push, so only the
# cap is printed, and nothing is glued: the board's mounts are part of the panel.
#
# Stack, box frame, hat centre at the origin, y positive toward the rear wall (the panel's face is y = -2.5, its back 0):
#
#    cap (Rev 1's knob), its underside CAP_GAP in front of the panel's face, on the stick's tip   y -14.7 .. -6.5
#    the stick, 2.2 mm, its tip SOCKET into the cap; the switch's collar and 11 mm body, through the panel's hole,
#      its front flush with the panel's face                                                   y -11.0 .. 4.0
#    the board, its front on the four bosses, and on its back J1 (JST SH, side entry) and the switch's pins
#                                                                                               y   4.0 .. 8.5
#    the four M2 x 8 countersunk screws, from behind, through the board into the bosses' 1.6 mm pilots
#
# The board's outline, holes and parts come from PCB/SearchHat_Rev1.0/SearchHat_Rev1.0_mech.json, written by the
# board's generator, so the panel's bosses always match the board.
#
# usage: hat4_r5.py <out dir> [asm dir]     (the panel and the cap; with asm dir, the assembly too)
#        hat4_r5.py --check                  (overlaps at rest, then how far the cap can tip before it meets the panel)
import json
import os
import sys
import numpy as np
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import hat_r5 as v1
import huey_head_r5 as h
from huey_head_r5 import rect, prism, ycyl, save

SEARCH = h.SEARCH
FACE = -h.PANEL_T                      # -2.5
MECH = json.load(open(os.path.join(HERE, "..", "..", "..", "PCB", "SearchHat_Rev1.0", "SearchHat_Rev1.0_mech.json")))

# ---- the switch: ALPS RKJXM1015004 (catalog drawing No. 1)
STICK_L = 15.0                         # mounting face to the stick's tip (+-0.4)
STICK_D = 2.2
BODY_H, BODY_W = 6.6, 11.0             # the body: 11 mm across, 6.6 mm from the mounting face
COLLAR_D, COLLAR_L = 4.3, 0.8          # the round collar the stick comes out of, in front of the body (from the drawing)
PIN_L = 3.2                            # terminals, behind the mounting face
TILT_SIDE, TILT_DIAG = 10.0, 12.0      # its own stops: toward A, B, C, D and toward a diagonal (catalog, max.)
PINS = [(1.0, 5.35), (1.0, -4.95), (4.95, 1.0), (-1.0, 4.95), (-4.95, -1.0), (5.35, -1.0), (-5.35, 1.0), (-1.0, -5.35),
        (-4.15, 2.7)]                  # (u, v), seen from the front; the locating peg is at (1, 3)

# ---- placing it
CAP_GAP = 4.0                          # cap's underside in front of the panel's face. A 28 mm cap's rim swings 3.0-3.2 mm
                                       # toward the panel at 12 degrees, so 4.0 keeps it clear even with a 14.6 mm stick
Y_CAPB = FACE - CAP_GAP                # -6.5
SOCKET = 4.5                           # the stick goes this far into the cap, and its tip bears on the socket's end
SOCKET_D = 2.3                         # for the 2.2 mm stick: snug as printed (open it with a 2.2 mm drill if it won't go)
Y_TIP = Y_CAPB - SOCKET                # -11.0
Y_MF = Y_TIP + STICK_L                 # the switch's mounting face = the board's front                       4.0
BOARD_T = MECH["thickness"]
Y_BB = Y_MF + BOARD_T                  # the board's back                                                      5.6

# ---- the panel
HOLE_D = 13.5                          # the panel's hole: the body's corners are 11.9 mm across
BOSS_D, PILOT_D = 5.0, 1.6             # M2 bosses, 1.6 mm pilots (tap M2 by hand, or let the screw cut it)
PILOT_END = FACE + 1.0                 # the pilots stop 1 mm short of the face
M2_HEAD_D, M2_HEAD_H, M2_L = 3.8, 1.2, 8.0

# ---- J1's housing and a mated plug (JST SH side entry), on the board's back
J1_H = 2.9
PLUG = (3.5, 4.5, 2.8)                 # half-width, length out of the housing's front, height


def octagon(r_in):
    R = r_in / np.cos(np.radians(22.5))
    return h.cs([(R * np.cos(np.radians(22.5 + 45 * k)), R * np.sin(np.radians(22.5 + 45 * k))) for k in range(8)])


def rounded(u0, v0, u1, v1, r):
    return (mf.CrossSection.square((u1 - u0 - 2 * r, v1 - v0)).translate((u0 + r, v0))
            + mf.CrossSection.square((u1 - u0, v1 - v0 - 2 * r)).translate((u0, v0 + r))
            + sum((mf.CrossSection.circle(r, 48).translate((x, y)) for x in (u0 + r, u1 - r) for y in (v0 + r, v1 - r)),
                  mf.CrossSection()))


# ---------------------------------------------------------------- panel
def lower_panel():
    """The lower panel with a round hole for the switch and four M2 bosses for the board on its back. Everything is
    part of the panel, which prints face down as before: the bosses grow straight up off its back."""
    p = prism(h.LOWER_PANEL, -h.PANEL_T, 0)
    p -= h.outline_chamfers(h.LOWER_PANEL, -h.PANEL_T, -1.0, h.PANEL_CHAMFER)
    opening = h.BODY.offset(-h.WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in h.COLUMNS] + [(*h.GOV, h.NUT_RELIEF["toggle"]), (*h.LDG_EXT, h.NUT_RELIEF["toggle"]),
                                                   (*SEARCH, HOLE_D)]
    p += prism(h.plug(opening, holes), -0.01, h.PLUG_H)
    p += h.toggle_box(*h.GOV, 0.0, opening, h.COLUMNS) + h.toggle_box(*h.LDG_EXT, 0.0, opening, h.COLUMNS)
    p -= prism(h.toggle_cut(*h.GOV) + h.toggle_cut(*h.LDG_EXT) + h.large_pb_cut(*h.STOP_REL), -h.PANEL_T - 1, h.PLUG_H + 1)
    for x, z in h.COLUMNS:
        p -= h.csk(x, z, -h.PANEL_T, +1, h.PANEL_CSK)
    for u, v in MECH["holes"]:
        p += ycyl(SEARCH[0] + u, SEARCH[1] + v, BOSS_D, -0.01, Y_MF)
        p -= ycyl(SEARCH[0] + u, SEARCH[1] + v, PILOT_D, PILOT_END, Y_MF + 1)
        p -= ycyl(SEARCH[0] + u, SEARCH[1] + v, PILOT_D, Y_MF - 0.3, Y_MF + 0.01, PILOT_D + 0.6)   # lead-in
    p -= ycyl(SEARCH[0], SEARCH[1], HOLE_D, -h.PANEL_T - 1, Y_MF)
    return h.inlay(p, h.lower_labels(), -h.PANEL_T)


# ---------------------------------------------------------------- the switch and the board (stand-ins, not printed)
def switch_body(pins=True):
    b = prism(octagon(BODY_W / 2), Y_MF - BODY_H, Y_MF)
    b += ycyl(0, 0, COLLAR_D, Y_MF - BODY_H - COLLAR_L, Y_MF - BODY_H + 0.01)
    if pins:
        for u, v in PINS:
            b += ycyl(u, v, 0.8, Y_MF - 0.01, Y_MF + PIN_L)
    return b


def stick():
    return ycyl(0, 0, STICK_D, Y_TIP, Y_MF - BODY_H - COLLAR_L + 0.01)


def board():
    u0, v0, u1, v1 = MECH["outline"]
    b = prism(rounded(u0, v0, u1, v1, MECH["corner"]), Y_MF, Y_BB)
    for u, v in MECH["holes"]:
        b -= ycyl(u, v, MECH["hole_d"], Y_MF - 1, Y_BB + 1)
    return b


def j1():
    """J1's housing on the board's back, and a plug in it with its wires turning back toward the rear wall."""
    jv = MECH["j1_origin_v"]
    housing = h.box(-4.05, Y_BB, jv - 1.73, 4.05, Y_BB + J1_H, jv + 2.62)
    w, l, t = PLUG
    plug = h.box(-w, Y_BB + 0.05, jv + 2.62, w, Y_BB + 0.05 + t, jv + 2.62 + l)
    wires = h.box(-2.0, Y_BB + 0.3, jv + 2.62 + l, 2.0, Y_BB + 7.0, jv + 2.62 + l + 2.0)
    return housing, plug + wires


def screws():
    s = mf.Manifold()
    y_seat = Y_BB + 0.1                                       # the cone's 2.2 mm section sits in the board's 2.2 mm hole
    for u, v in MECH["holes"]:
        s += ycyl(u, v, 2.0, y_seat - (M2_L - M2_HEAD_H), y_seat + 0.01) + ycyl(u, v, 2.0, y_seat, y_seat + 0.9, M2_HEAD_D)
        s += ycyl(u, v, M2_HEAD_D, y_seat + 0.89, y_seat + M2_HEAD_H)
    return s


# ---------------------------------------------------------------- cap: Rev 1's knob, with a socket for the stick
def cap():
    c0 = v1.cap().translate((0, Y_CAPB - v1.Y_CAPB, 0))
    c = c0
    for k in range(4):                                        # Rev 1's leg sockets aren't used: fill them
        x, z = v1.PITCH * np.sin(np.radians(90 * k)), v1.PITCH * np.cos(np.radians(90 * k))
        c += ycyl(x, z, v1.SOCKET_D + 0.02, Y_CAPB - v1.LEG_SOCKET - 0.01, Y_CAPB) ^ c0.hull()
    c -= ycyl(0, 0, SOCKET_D, Y_TIP, Y_CAPB + 0.1)
    c -= ycyl(0, 0, SOCKET_D, Y_CAPB - 0.4, Y_CAPB + 0.01, SOCKET_D + 0.82)   # lead-in, and room for the first layer's squash
    return c


# ---------------------------------------------------------------- tipping
def tip_matrix(n, theta, y_pivot):
    """Rotation by theta about the line through (0, y_pivot, 0) square to n (unit (x, z)), the stick leaning toward n
    (its tip moves toward n, so the cap's rim on that side swings back toward the panel)."""
    nv = np.array([n[0], 0.0, n[1]])
    u = np.cross([0.0, 1.0, 0.0], nv)
    u /= np.linalg.norm(u)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * K @ K
    c = np.array([0.0, y_pivot, 0.0])
    return R, c - R @ c


def tipped(m, n, theta, y_pivot):
    R, t = tip_matrix(n, theta, y_pivot)
    return m.transform(np.hstack([R, t.reshape(3, 1)]).tolist())


def vol(m):
    return m.volume() if m.num_vert() else 0.0


def check():
    lp, txt = lower_panel()
    crop = h.box(-25, -4, -25, 25, 12, 25).translate((SEARCH[0], 0, SEARCH[1]))
    panel = (lp + txt).translate((-SEARCH[0], 0, -SEARCH[1])) ^ crop.translate((-SEARCH[0], 0, -SEARCH[1]))
    sw, st, bd, sc, cp = switch_body(), stick(), board(), screws(), cap()
    hous, plug = j1()
    print("at rest:")
    pairs = {("switch", "panel"): (sw, panel), ("stick", "panel"): (st, panel), ("board", "panel"): (bd, panel),
             ("board", "switch body"): (bd, switch_body(pins=False)),
             ("screws", "panel less pilots"): (sc, panel - sum((ycyl(u, v, 2.05, -5, 12) for u, v in MECH["holes"]), mf.Manifold())),
             ("screws", "board"): (sc, bd), ("J1", "board"): (hous, bd), ("plug", "board"): (plug, bd),
             ("cap", "panel"): (cp, panel), ("cap", "stick"): (cp, st), ("cap", "switch"): (cp, sw),
             ("J1", "screws"): (hous + plug, sc), ("J1", "switch pins"): (hous, sw)}
    for (a, b), (ma, mb) in pairs.items():
        print(f"  {a:7s} x {b:18s} {vol(ma ^ mb):7.3f} mm3")
    print(f"  stick tip {Y_TIP:.2f} (cap's socket end); mounting face {Y_MF:.2f}; switch body's front {Y_MF - BODY_H:.2f} "
          f"(panel face {FACE}); board back {Y_BB:.2f}; J1 to {Y_BB + J1_H:.2f}; pins to {Y_MF + PIN_L:.2f}")
    print(f"  M2 x 8: tip at {Y_BB + 0.1 - (M2_L - M2_HEAD_H):.2f}, pilot to {PILOT_END:.2f}; "
          f"{Y_MF - (Y_BB + 0.1 - (M2_L - M2_HEAD_H)):.1f} mm of thread in the boss and panel")

    # Where is the stick's pivot? The drawing doesn't say. Try it at the body's front, its middle and the mounting
    # face, and the stick at its shortest (14.6 mm: the cap 0.4 mm nearer the panel).
    print("\nhow far the cap can tip before its rim meets the panel's face (the switch stops at "
          f"{TILT_SIDE:.0f} toward a side, {TILT_DIAG:.0f} toward a diagonal):")
    print(f"  {'pivot':>22s} {'stick':>6s}   " + "  ".join(f"{d:>5s}" for d in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")))
    worst = 99.0
    face = panel ^ h.box(-30, FACE - 0.5, -30, 30, FACE + 0.6, 30)
    for yp, pname in ((Y_MF - BODY_H, "body front"), (Y_MF - BODY_H / 2, "body middle"), (Y_MF, "mounting face")):
        for dy, sname in ((0.0, "15.0"), (0.4, "14.6")):
            cc = cp.translate((0, dy, 0))
            row = []
            for k in range(8):
                a = np.radians(45 * k)
                n = np.array([np.sin(a), np.cos(a)])
                lo, hi = 0.0, np.radians(30)
                for _ in range(14):
                    mid = (lo + hi) / 2
                    lo, hi = (lo, mid) if vol(tipped(cc, n, mid, yp) ^ face) > 0.002 else (mid, hi)
                need = TILT_DIAG if k % 2 else TILT_SIDE
                worst = min(worst, np.degrees(lo) - need)
                row.append(np.degrees(lo))
            print(f"  {pname + ' y=' + format(yp, '.1f'):>22s} {sname:>6s}   " + "  ".join(f"{v:5.1f}" for v in row))
    print(f"  the cap's rim stays clear of the panel to {worst:+.1f} degrees past the switch's own stop, at the worst")
    hits = []
    for k in range(8):
        a = np.radians(45 * k)
        n = np.array([np.sin(a), np.cos(a)])
        th = np.radians(TILT_DIAG)
        for yp in (Y_MF - BODY_H, Y_MF):
            if vol(tipped(st, n, th, yp) ^ panel) > 0.002:
                hits.append(("stick", k, yp))
            if vol(tipped(cp, n, th, yp) ^ sw) > 0.002:
                hits.append(("cap/switch", k, yp))
    print(f"  at 12 degrees every way: stick vs the panel's hole, cap vs the switch's body: {hits or 'clear'}")


# ---------------------------------------------------------------- output
def pose_back_down(m):
    """Back (largest y) on the bed, front up."""
    y1 = m.bounding_box()[4]
    return m.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, y1]])


def write_parts(out):
    lp, txt = lower_panel()
    save(h.tilt(lp), os.path.join(out, "HueyHeadR5-LowerPanel-Hat4-Black.stl"))
    save(h.tilt(txt), os.path.join(out, "HueyHeadR5-LowerPanel-Hat4-WhiteText.stl"))
    save(pose_back_down(cap()), os.path.join(out, "HueyHeadR5-Hat4-Cap.stl"))


def assembly():
    hous, plug = j1()
    a = {"panel": lower_panel()[0], "board": board(), "switch": switch_body(), "stick": stick(), "j1": hous,
         "plug": plug, "screws": screws(), "cap": cap()}
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
            save(m, os.path.join(sys.argv[2], f"asm4_{k}.stl"))
