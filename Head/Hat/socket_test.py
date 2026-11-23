# Test coupons for the hat cap's socket: one hole each, loose but in one STL so they print together, in small steps,
# so the cap's SOCKET_D and SOCKET_FLAT_W can be picked from one small print instead of a cap at a time.
#
# The stick (catalog, and measured 0.085" = 2.16 mm): 2.2 round, its last 3.5 mm cut to a D 1.4 from the flat to the
# far side. Each coupon is 12 x 15 x 3 mm, small enough to go over the stick with the hat installed: a D hole takes
# only the stick's D, and the stick pushes on through a round hole until its round part is in. Prints like the cap:
# the holes open on the bed, with the same lead-in.
#
# Only the sizes still in question. The 0.05 coupons: 2.50 fits. Caps: D 1.69 and 1.72 too tight.
#   back row:  round holes 2.45 .. 2.50, 0.01 steps                      -> SOCKET_D
#   front row: D holes 1.70 .. 2.00 from the flat to the far side                     -> SOCKET_FLAT_W
#              (off for now, WITH_D: they come next, their round part the round size that fits)
#
# usage: socket_test.py <out dir>
import os
import sys
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import huey_head_r5 as h


def steps(a, b, s=0.05):
    return [round(a + s * k, 2) for k in range(round((b - a) / s) + 1)]


ROUND = steps(2.45, 2.50, 0.01)                       # 0.05 coupons: 2.50 fits; this narrows it down
DFLAT = steps(1.70, 2.00)
D_ROUND = 2.5                                         # the D holes' round part: set it to the round coupon that fits
WITH_D = False                                        # round coupons first; D coupons once the round size is picked
T = 3.0                                               # coupon thickness
CW, CL, GAP = 12.0, 15.0, 3.0                         # each coupon, small enough to go over the installed stick
HOLE_Y = 4.0                                          # the hole's centre from the coupon's near end; the label above
TEXT_H, RAISE = 3.0, 0.6                              # labels stand 0.6 proud of the top: sunk ones fill in and blur


def d_hole(d, w):
    return (mf.CrossSection.circle(d / 2, 64)
            ^ mf.CrossSection.square((d + 1, w)).translate((-(d + 1) / 2, -d / 2)))


def hole(cs, x, y):
    """Through the plug, with a 0.3 mm lead-in on the bed side (the cap's, for the first layer's squash)."""
    c = cs.translate((x, y))
    return (h.zprism(c, -0.1, T + 0.1)
            + h.zprism(c.offset(0.3, mf.JoinType.Round), -0.1, 0.3))


def coupon(hole_cs, label, x0, y0):
    """One loose coupon: a hole near one end, its size raised above it."""
    xc = x0 + CW / 2
    c = h.box(x0, y0, 0, x0 + CW, y0 + CL, T)
    c += h.zprism(h.text(label, TEXT_H, xc, y0 + CL - 4.0), T - 0.01, T + RAISE)
    return c - hole(hole_cs, xc, y0 + HOLE_Y)


def plug():
    """All the coupons, apart, in one STL: row O (round) behind row D."""
    m = mf.Manifold()
    for i, d in enumerate(ROUND):
        m += coupon(mf.CrossSection.circle(d / 2, 64), f"{d:.2f}", i * (CW + GAP), CL + GAP)
    if WITH_D:
        for i, w in enumerate(DFLAT):
            m += coupon(d_hole(D_ROUND, w), f"{w:.2f}", i * (CW + GAP), 0)
    return m


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    h.save(plug(), os.path.join(out, "HueyHeadR5-Hat-SocketTest.stl"))
