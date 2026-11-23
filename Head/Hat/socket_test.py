# A test plug for the hat cap's socket: round holes and D holes for the RKJXM's stick, in 0.05 mm steps, so the cap's
# SOCKET_D and SOCKET_FLAT_W can be picked from one small print instead of a cap at a time.
#
# The stick (catalog, and measured 0.085" = 2.16 mm): 2.2 round, its last 3.5 mm cut to a D 1.4 from the flat to the
# far side. The plug is 3.0 mm thick, so a D hole takes only the stick's D, and the stick pushes on through a round
# hole until its round part is in. Prints like the cap: the holes open on the bed, with the same lead-in.
#
# Only the sizes still in question. Caps so far: round 2.4 too tight, 2.5 too loose; D 1.69 and 1.72 too tight.
#   top row, "O":    round holes 2.35 .. 2.55                                    -> SOCKET_D
#   bottom row, "D": D holes 1.70 .. 2.00 from the flat to the far side, their round part the cap's 2.5
#                                                                                -> SOCKET_FLAT_W
#
# usage: socket_test.py <out dir>
import os
import sys
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import huey_head_r5 as h


def steps(a, b):
    return [round(a + 0.05 * k, 2) for k in range(round((b - a) / 0.05) + 1)]


ROUND = steps(2.35, 2.55)
DFLAT = steps(1.70, 2.00)
D_ROUND = 2.5                                         # the D holes' round part: the cap's SOCKET_D
T = 3.0                                               # plug thickness
PITCH, X0 = 10.0, 13.0
Y_D, Y_O = 10.0, 24.0                                 # hole rows
TEXT_H, RAISE = 3.0, 0.6                              # labels stand 0.6 proud of the top: sunk ones fill in and blur
W, L = X0 + PITCH * (max(len(ROUND), len(DFLAT)) - 1) + 6.0, 31.0


def d_hole(d, w):
    return (mf.CrossSection.circle(d / 2, 64)
            ^ mf.CrossSection.square((d + 1, w)).translate((-(d + 1) / 2, -d / 2)))


def hole(cs, x, y):
    """Through the plug, with a 0.3 mm lead-in on the bed side (the cap's, for the first layer's squash)."""
    c = cs.translate((x, y))
    return (h.zprism(c, -0.1, T + 0.1)
            + h.zprism(c.offset(0.3, mf.JoinType.Round), -0.1, 0.3))


def plug():
    p = h.box(0, 0, 0, W, L, T)
    cut, txt = mf.Manifold(), mf.CrossSection()
    for i, d in enumerate(ROUND):
        x = X0 + PITCH * i
        cut += hole(mf.CrossSection.circle(d / 2, 64), x, Y_O)
        txt += h.text(f"{d:.2f}", TEXT_H, x, Y_O - 5.0)
    for i, w in enumerate(DFLAT):
        x = X0 + PITCH * i
        cut += hole(d_hole(D_ROUND, w), x, Y_D)
        txt += h.text(f"{w:.2f}", TEXT_H, x, Y_D - 5.5)
    txt += h.text("O", TEXT_H + 1.0, 4.0, Y_O) + h.text("D", TEXT_H + 1.0, 4.0, Y_D)
    return p + h.zprism(txt, T - 0.01, T + RAISE) - cut


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    h.save(plug(), os.path.join(out, "HueyHeadR5-Hat-SocketTest.stl"))
