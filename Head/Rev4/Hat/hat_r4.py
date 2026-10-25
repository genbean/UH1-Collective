# UH-1 head Rev 4: new SEARCH CONT 4-way hat. Replaces the MkII thumbstick hat (4way_Cover, Bezel, ThumbStick,
# StickRetainer) and the ringed search hat with a pyramid cap on a rocker plate that presses four TE 1825910-6 tact
# switches. It sits where the MkII hat did (SEARCH in huey_head_r4.py) and fits the same 24 mm hole in the panel's plug.
#
# Stack, box frame, hat centre at the origin of the local frame, y positive toward the rear wall (the panel's face is
# y = -2.5, its back y = 0):
#
#    ribbed round cap, 28 mm, floats 1.4 mm over the bezel          y -13 .. -5.1
#    4 legs, 4 mm with a flared root, part of the rocker plate, through the bezel's holes; the cap is glued onto their tips
#    bezel, 1.6 mm, on the panel face, 4 x M2 x 8 countersunk        y  -4.1 .. -2.5
#    set screw M3 x 4 in the plate's centre: its tip is the pivot,
#       bearing on the bezel's flat underside, and it sets the preload y  -2.5 .. +1.5
#    rocker plate, a 1.2 mm plus, buttons press up at its 4 arms      y  -2.1 .. -0.9  (boss to +0.9)
#    four TE 1825910-6, buttons forward, in pockets in the carrier     covers at y 0.49, bases at 4.10
#    carrier floor 1.2 mm, leg slots, key hole for the set screw       y  4.10 .. 5.30   (legs end at 7.61)
#
# The carrier (drum, pockets, hub, floor) is part of the lower panel, so it prints with it, face down: nothing in it
# needs support (the pockets open toward the bed and are bridged by the floor, which is last).
#
# usage: hat_r4.py <out dir> [asm dir]
import os
import sys
import numpy as np
import trimesh
import manifold3d as mf

REV4 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, REV4)
import huey_head_r4 as h
from huey_head_r4 import cs, rect, circle, prism, ycyl, box, save

SEARCH = h.SEARCH
FACE = -h.PANEL_T                      # the panel's face, y

# ---- the switch: TE 1825910-6 (FSM4JH), datasheet figures as in huey_head_r4.py
TACT_H, TACT_BODY = h.TACT_H, h.TACT_BODY     # base to button top 5.00, base to cover 3.61
LEG_LEN = 3.51                         # legs behind the base
LEG_ROW, LEG_PITCH = 6.5, 4.5          # rows 6.5 apart (across the switch), 4.5 apart along a row

# ---- layout
PITCH = 7.0                            # switch centres from the hat's centre, N / E / S / W
BORE_R = 10.7                          # round hole through the panel; the switches go in through it (corners at 10.55)
DRUM_R = 12.2                          # the carrier is a drum behind the panel; the plug's relief is 12.5
BEZ_T = 1.6
BEZ_R = 11.8
Y_BF, Y_BU = FACE - BEZ_T, FACE        # bezel's front, and its flat underside (the pivot's seat)
SET_PROUD = 0.8                        # set screw tip beyond the plate's front face at its nominal setting (adjustable)
SETSCREW_L = 4.0                       # M3 x 4 set screw (HIQTRADEBYJJ kit)
PL_T = 1.2
Y_PF = Y_BU + SET_PROUD                # plate front
Y_PR = Y_PF + PL_T                     # plate rear = the buttons' free tops (no preload)  -0.9
Y_BTN = Y_PR
Y_BASE = Y_BTN + TACT_H                # the switches' bases on the floor            4.1
Y_COVER = Y_BASE - TACT_BODY           # and their covers                            0.49
FLOOR_T = 1.2
Y_BACK = Y_BASE + FLOOR_T              # back of the carrier                         5.3
Y_TIP = Y_BASE + LEG_LEN               # leg tips                                    7.61
BOSS_D, BOSS_L = 5.0, 1.8
HUB_BORE_D = 5.8
Y_REAR_STOP = Y_BU + SETSCREW_L + 0.1  # the hub bore's floor: 0.1 mm behind the set screw's rear end
KEY_D = 2.4                            # a 1.5 mm hex key through the floor to the set screw
POCKET = 6.3                           # 6.0 mm body + clearance
NOTCH = (2.55, 3.95, 5.9)              # leg notches: from / to across, and along, centred on the switch
BEZ_SCREW = 8.8 / np.sqrt(2)           # M2 x 8 countersunk, on the diagonals
M2_PILOT = 1.6
LEG_D, LEG_HOLE_BEZ = 4.0, 4.6                   # legs: 4 mm, with a flare at the root (below) and a pocket for it in the bezel
FLARE_D, FLARE_H = 5.6, 0.6
POCKET_D, POCKET_H = 7.0, 0.7

# ---- cap
CAP_R, CAP_SKIRT, CAP_SLOPE = 14.0, 0.8, 30.0
CAP_TERRACES, CAP_H = 11, 6.0
LEG_SOCKET = 2.4
Y_CAPB = Y_BF - 1.4                    # the cap's underside


def rot(c, k):
    """Cross-section drawn for N turned k quarter turns clockwise (k = 1 gives E)."""
    return c.rotate(-90.0 * k)


def n_shapes(fn):
    """Union of fn(c) for the 4 directions; fn draws on N's cross-section."""
    return fn


def at4(c):
    """The same 2-D shape drawn for N, at N, E, S and W."""
    out = mf.CrossSection()
    for k in range(4):
        out += rot(c, k)
    return out


# ---------------------------------------------------------------- the carrier, built into the lower panel
def carrier():
    """Box frame, hat centred on the origin: the drum behind the panel with the switch pockets, hub, floor and holes.
    Its ring is fused to the panel plate by the caller."""
    drum = ycyl(0, 0, 2 * DRUM_R, -0.02, Y_BACK)
    drum -= ycyl(0, 0, 2 * BORE_R, -1.0, Y_COVER)
    body = at4(rect(-POCKET / 2, PITCH - POCKET / 2, POCKET / 2, PITCH + POCKET / 2))
    notch = at4(rect(NOTCH[0], PITCH - NOTCH[2] / 2, NOTCH[1], PITCH + NOTCH[2] / 2)
                + rect(-NOTCH[1], PITCH - NOTCH[2] / 2, -NOTCH[0], PITCH + NOTCH[2] / 2))
    drum -= prism(body, Y_COVER - 0.01, Y_BASE)
    drum -= prism(notch, Y_BASE - 1.2, Y_BACK + 1.0)               # legs and their kinks, through the floor
    drum -= ycyl(0, 0, HUB_BORE_D, Y_COVER - 0.01, Y_REAR_STOP)    # the plate's boss
    drum -= ycyl(0, 0, KEY_D, Y_REAR_STOP - 0.01, Y_BACK + 1.0)    # hex key to the set screw
    for k in (45, 135, 225, 315):                                  # bezel pilots, M2 tapped
        x, z = 8.8 * np.cos(np.radians(k)), 8.8 * np.sin(np.radians(k))
        drum -= ycyl(x, z, M2_PILOT, Y_COVER - 0.01, Y_BASE + 0.6)
    return drum


def lower_panel_new():
    """The lower panel with the new hat's carrier instead of the MkII hat. (huey_head_r4.lower_panel less its hat lines.)"""
    p = prism(h.LOWER_PANEL, -h.PANEL_T, 0)
    opening = h.BODY.offset(-h.WALL, mf.JoinType.Miter)
    holes = [(x, z, 7.2) for x, z in h.COLUMNS] + [(*h.GOV, h.NUT_RELIEF["toggle"]), (*h.LDG_EXT, h.NUT_RELIEF["toggle"]),
                                                   (*h.STOP_REL, h.NUT_RELIEF["pb4"]), (*SEARCH, 2 * h.HAT_R + 1.0)]
    p += prism(h.plug(opening, holes), -0.01, h.PLUG_H)
    p -= prism(h.toggle_cut(*h.GOV) + h.toggle_cut(*h.LDG_EXT) + h.large_pb_cut(*h.STOP_REL), -h.PANEL_T - 1, h.PLUG_H + 1)
    for x, z in h.COLUMNS:
        p -= h.csk(x, z, -h.PANEL_T, +1)
    p -= ycyl(SEARCH[0], SEARCH[1], 2 * BORE_R, -h.PANEL_T - 1, 0.01)
    p += carrier().translate((SEARCH[0], 0, SEARCH[1]))
    return h.inlay(p, h.lower_labels(), -h.PANEL_T)


# ---------------------------------------------------------------- bezel
def bezel():
    b = ycyl(0, 0, 2 * BEZ_R, Y_BF + 0.4, Y_BU) + ycyl(0, 0, 2 * BEZ_R - 0.8, Y_BF, Y_BF + 0.4 + 0.01, 2 * BEZ_R)
    for k in range(4):
        x, z = PITCH * np.sin(np.radians(90 * k)), PITCH * np.cos(np.radians(90 * k))
        b -= ycyl(x, z, LEG_HOLE_BEZ, Y_BF - 1, Y_BU + 1)
        b -= ycyl(x, z, POCKET_D, Y_BU - POCKET_H, Y_BU + 1)             # room for the leg's flare when the plate tilts
    for k in (45, 135, 225, 315):
        x, z = 8.8 * np.cos(np.radians(k)), 8.8 * np.sin(np.radians(k))
        b -= ycyl(x, z, 2.4, Y_BF - 1, Y_BU + 1)
        b -= ycyl(x, z, 4.5, Y_BF - 0.01, Y_BF + 1.05, 2.4)       # 90 degree countersink for an M2 head
    return b


# ---------------------------------------------------------------- rocker plate
def plate():
    """Rocker plate with its four legs: a plus, boss behind, legs standing forward through the bezel into the cap's sockets."""
    arms = rect(-3.5, -9.0, 3.5, 9.0) + rect(-9.0, -3.5, 9.0, 3.5)
    arms = arms.offset(-0.8, mf.JoinType.Round).offset(0.8, mf.JoinType.Round)
    p = prism(arms, Y_PF, Y_PR)
    p += ycyl(0, 0, BOSS_D, Y_PR - 0.01, Y_PR + BOSS_L)
    p -= ycyl(0, 0, 2.5, Y_PF - 1, Y_PR + BOSS_L + 1)             # M3 set screw pilot, tapped
    for k in range(4):
        x, z = PITCH * np.sin(np.radians(90 * k)), PITCH * np.cos(np.radians(90 * k))
        p += ycyl(x, z, LEG_D, Y_CAPB - LEG_SOCKET + 0.1, Y_PF + 0.01)
        p += ycyl(x, z, LEG_D, Y_PF - FLARE_H, Y_PF + 0.01, FLARE_D) ^ prism(arms, Y_PF - FLARE_H - 1, Y_PF + 0.01)   # fillet at the root, cut off where it would overhang the arm's edge
    return p


# ---------------------------------------------------------------- cap
def cap():
    """Huey SEARCH CONT knob: a flanged round cone of CAP_TERRACES terraces on a parabolic profile (steep at the centre,
    flattening toward the rim, as the real knob), with a centre pin. Prints base down, so every terrace is narrower than
    the one under it. Four 3.1 mm sockets in the underside take the plate's legs."""
    y0 = Y_CAPB
    z0 = CAP_SKIRT + 0.35
    r_rim, r_c = CAP_R - 1.0, 1.5                                   # first terrace's outer edge, and the top's radius
    def zp(u):                                                      # u = 1 at the rim, 0 at the centre
        return CAP_H * (0.5 * (1 - u) ** 2 + 0.5 * (1 - u))
    pts = [(0.0, 0.0), (CAP_R, 0.0), (CAP_R, CAP_SKIRT), (CAP_R - 0.5, CAP_SKIRT), (CAP_R - 0.5, z0)]       # flange
    for i in range(CAP_TERRACES):
        r_out = r_rim - i * (r_rim - r_c) / CAP_TERRACES
        r_in = r_rim - (i + 1) * (r_rim - r_c) / CAP_TERRACES
        zi = z0 + zp((r_in - r_c) / (r_rim - r_c)) - zp(1.0) * 0
        zi = z0 + zp((r_in - r_c) / (r_rim - r_c))
        zprev = z0 + zp((r_out - r_c) / (r_rim - r_c))
        pts += [(r_out, zprev), (r_out, zi), (r_in, zi)]
    pts += [(0.9, zi), (0.9, zi + 1.0), (0.0, zi + 1.0)]            # centre pin
    prof = mf.CrossSection([pts], mf.FillRule.NonZero)
    body = mf.Manifold.revolve(prof, 160).rotate((90, 0, 0)).translate((0, y0, 0))      # z (up) -> -y (toward the thumb)
    for k in range(4):
        x, zz = PITCH * np.sin(np.radians(90 * k)), PITCH * np.cos(np.radians(90 * k))
        body -= ycyl(x, zz, LEG_D + 0.1, y0 - LEG_SOCKET, y0 + 0.1)
    return body


# ---------------------------------------------------------------- hardware stand-ins (not printed)
def tact(k):
    """TE 1825910-6 at direction k (0 = N), as a stand-in with its legs. Returns (body, button, legs)."""
    body = prism(rot(rect(-3.0, PITCH - 3.0, 3.0, PITCH + 3.0), k), Y_COVER, Y_BASE)
    button = ycyl(*(np.array([PITCH * np.sin(np.radians(90 * k)), PITCH * np.cos(np.radians(90 * k))])), 3.5,
                  Y_BTN, Y_COVER + 0.01)
    legs = mf.Manifold()
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = rect(sx * 3.25 - 0.15, PITCH + sz * LEG_PITCH / 2 - 0.355, sx * 3.25 + 0.15, PITCH + sz * LEG_PITCH / 2 + 0.355)
            tab = rect(min(sx * 2.9, sx * 3.4), PITCH + sz * LEG_PITCH / 2 - 0.355, max(sx * 2.9, sx * 3.4), PITCH + sz * LEG_PITCH / 2 + 0.355)
            legs += prism(rot(c, k), Y_BASE - 0.3, Y_TIP) + prism(rot(tab, k), Y_BASE - 0.3, Y_BASE + 0.01)
    return body, button, legs


def set_screw():
    """M3 x 4 set screw: the end chamfered to a 1.6 mm flat, which is what bears on the bezel."""
    return ycyl(0, 0, 1.6, Y_BU, Y_BU + 0.7, 3.0) + ycyl(0, 0, 3.0, Y_BU + 0.69, Y_BU + SETSCREW_L)


def m2_screws():
    out = mf.Manifold()
    for k in (45, 135, 225, 315):
        x, z = 8.8 * np.cos(np.radians(k)), 8.8 * np.sin(np.radians(k))
        out += ycyl(x, z, 4.0, Y_BF, Y_BF + 1.0, 2.0) + ycyl(x, z, 2.0, Y_BF + 0.99, Y_BF + 8.0)
    return out


# ---------------------------------------------------------------- tilting the rocker unit
def tilt_unit(m, deg, about_deg=0.0):
    """Rotate m about the pivot (0, Y_BU, 0), a tilt of deg that presses the direction `about_deg` (0 = N, 90 = E)
    back (toward +y)."""
    a = np.radians(deg)
    d = np.array([np.sin(np.radians(about_deg)), 0.0, np.cos(np.radians(about_deg))])    # in (x, y, z): N is +z
    u = np.array([0.0, 1.0, 0.0])
    # rotation about the axis perpendicular to d and y, taking +d toward +y
    ax = np.cross(d, u)
    ax /= np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    R = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
    c = np.array([0.0, Y_BU, 0.0])
    T = np.hstack([R, (c - R @ c).reshape(3, 1)])
    return m.transform(T.tolist())


def vol(m):
    return m.volume() if m.num_vert() else 0.0


def print_pose(m):
    """Assembly pose -> print pose: the front face (smallest y) on the bed, the part's own x and z kept."""
    y0 = m.bounding_box()[1]
    return m.transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -y0]])


def write_hat_parts(out):
    """The hat's own printed parts, in print pose."""
    save(print_pose(bezel()), os.path.join(out, "HueyHeadR4-Hat-Bezel.stl"))
    save(print_pose(plate()), os.path.join(out, "HueyHeadR4-Hat-RockerPlate.stl"))
    c_ = cap()
    save(c_.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, c_.bounding_box()[4]]]), os.path.join(out, "HueyHeadR4-Hat-Cap.stl"))



if __name__ == "__main__":
    out = sys.argv[1]
    asm_dir = sys.argv[2] if len(sys.argv) > 2 else None
    os.makedirs(out, exist_ok=True)
    lp, lp_text = lower_panel_new()
    save(h.tilt(lp), os.path.join(out, "HueyHeadR4-LowerPanel-Hat-Black.stl"))
    save(h.tilt(lp_text), os.path.join(out, "HueyHeadR4-LowerPanel-Hat-WhiteText.stl"))
    write_hat_parts(out)
    if asm_dir:                                   # the assembly pose, box frame, for renders and checks
        os.makedirs(asm_dir, exist_ok=True)
        asm = {"panel": lp, "panel_text": lp_text, "bezel": bezel(), "plate": plate(), "cap": cap(), "setscrew": set_screw(),
               "m2": m2_screws()}
        for name, m in asm.items():
            save(m.translate((SEARCH[0], 0, SEARCH[1])) if name not in ("panel", "panel_text") else m,
                 os.path.join(asm_dir, f"asm_{name}.stl"))
        for k in range(4):
            b, bt, lg = tact(k)
            save((b + bt + lg).translate((SEARCH[0], 0, SEARCH[1])), os.path.join(asm_dir, f"asm_tact{k}.stl"))
