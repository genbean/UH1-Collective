# Renders for the SEARCH CONT hat, Rev 3 (hat3_r5.py), in render_hat2.py's style.
#
# usage: render_hat3.py <out dir>
import os
import sys
import numpy as np
import manifold3d as mf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hat3_r5 as m3
import huey_head_r5 as h
from render_hat2 import render, titled, GREY, DARK, YELLOW, ORANGE, BLUE, STEEL, FONT_B

GREEN = "#3fae7c"                                       # the spring cup, so it stands out from the pod


def panel_crop():
    lp, _ = m3.lower_panel()
    return lp.translate((-m3.SEARCH[0], 0, -m3.SEARCH[1])) ^ h.ycyl(0, 0, 44, -3.0, 3.0)


def switches():
    out = mf.Manifold()
    for k in range(4):
        b, bt, lg = m3.tact(k)
        out += b + bt + lg
    return out


def coil(warp=None, turns=6, wire=0.4, od=4.0):
    """The pen spring as a wire helix, from the cup's seat to the screw head, as fitted. warp(p) moves its points
    (N x 3) for a tipped pose."""
    y0 = m3.Y_BACK + m3.CUP_T - m3.CUP_SEAT[1]
    L, rm = m3.spring_len(), (od - wire) / 2
    w = mf.Manifold.cylinder(turns, wire / 2, wire / 2, 12).refine_to_length(0.03)

    def f(p):
        t = p[:, 2]
        a = 2 * np.pi * t
        er = np.stack([np.cos(a), np.zeros_like(a), np.sin(a)], 1)
        c = rm * er + np.stack([np.zeros_like(t), y0 + wire / 2 + t / turns * (L - wire), np.zeros_like(t)], 1)
        q = c + p[:, :1] * er + p[:, 1:2] * [0, 1, 0]
        return q if warp is None else warp(q)
    return w.warp_batch(f)


def pushed(n, d, th):
    """The cup slid to follow the screw, and the spring between it and the tipped head."""
    sx, sz = m3.cup_shift(n, d, th)
    R, t = m3.tip_matrix(n, d, th)
    y0, y1 = m3.Y_BACK + m3.CUP_T - m3.CUP_SEAT[1], m3.Y_BACK + m3.CUP_T - m3.CUP_SEAT[1] + m3.spring_len()

    def warp(q):
        s = np.clip((q[:, 1:2] - y0) / (y1 - y0), 0, 1)
        return (1 - s) * (q + [sx, 0, sz]) + s * (q @ R.T + t)
    return m3.cup().translate((sx, 0, sz)), coil(warp)


def exploded(out):
    g = 10.0
    back = 1.2 * g + 16                                 # the cup, spring and screw spread out behind the pod, clear of it
    items = [(m3.cap().translate((0, -2.6 * g, 0)), DARK), (m3.nut().translate((0, -1.9 * g, 0)), STEEL),
             (m3.rocker().translate((0, -1.4 * g, 0)), ORANGE), (panel_crop(), GREY),
             (switches().translate((0, 0.6 * g, 0)), YELLOW), (m3.pod().translate((0, 1.2 * g, 0)), BLUE),
             (m3.cup().translate((0, back, 0)), GREEN), (coil().translate((0, back + 8, 0)), STEEL),
             (m3.screw().translate((0, back + 16, 0)), STEEL)]
    img = render(items, view=(1.0, -0.8, 0.5), up=(0, 0, 1), zoom=1.1)
    titled(img, "SEARCH CONT hat, Rev 3", "Front to back: cap, M3 nut, rocker, the panel with its round hole and pins, "
           "the four switches, the pod (glued to the panel), the spring cup (green, loose on the pod's back), "
           "pen spring, M3 x 20", out)


def pod_view(out):
    img = render([(m3.pod(), BLUE), (switches(), YELLOW)], view=(0.5, -1.0, 0.8), up=(0, 0, 1), zoom=1.0)
    titled(img, "Rev 3 pod, from the front", "The octagonal anvil in its square bore, the four switches in their "
           "pockets, and the three holes for the panel's pins. It prints back down", out)


def back_view(out):
    """Assembled, from behind: where the cup, spring and screw go."""
    items = [(panel_crop(), GREY), (m3.pod(), BLUE), (switches(), YELLOW), (m3.cup(), GREEN), (coil(), STEEL),
             (m3.screw(), STEEL), (m3.rocker(), ORANGE), (m3.cap(), DARK)]
    img = render(items, view=(0.55, 1.0, 0.55), up=(0, 0, 1), zoom=1.15)
    titled(img, "Rev 3 hat from behind", "The spring cup (green) sits loose on the middle of the pod's back, seat "
           "outward, with the screw through it. The pen spring sits in the seat, under the screw's head. "
           "Don't glue the cup: it slides a little as the hat tips", out)


def section(out):
    half = mf.Manifold.cube((40, 40, 60)).translate((-40, -20, -30))
    fixed = [(panel_crop(), GREY), (switches(), YELLOW), (m3.pod(), BLUE)]
    n, d = np.array([0.0, 1.0]), m3.R_OCT
    th = next(t for t in np.radians(np.arange(0, 20, 0.05)) if m3.btn_travel(n, d, t)[0] >= m3.BTN_GAP + m3.CLICK[1])
    imgs = []
    for t in (0.0, th):
        moving = [(m3.tipped(p, n, d, t), c) for p, c in ((m3.rocker(), ORANGE), (m3.cap(), DARK), (m3.screw(), STEEL), (m3.nut(), STEEL))]
        cup, spring = pushed(n, d, t) if t else (m3.cup(), coil())
        items = [(mm ^ half, c) for mm, c in fixed + moving + [(cup, GREEN), (spring, STEEL)]]
        imgs.append(render(items, view=(1, 0, 0), up=(0, 0, 1), zoom=1.05, parallel=True))
    W, Hh = imgs[0].width + imgs[1].width, max(i.height for i in imgs)
    both = Image.new("RGB", (W, Hh + 40), (250, 251, 252))
    both.paste(imgs[0], (0, 40))
    both.paste(imgs[1], (imgs[0].width, 40))
    d_ = ImageDraw.Draw(both)
    f = ImageFont.truetype(FONT_B, 24)
    d_.text((30, 6), "At rest: the boss sits on the anvil", font=f, fill=(20, 24, 30))
    d_.text((imgs[0].width + 30, 6), f"Pushed north, {np.degrees(th):.1f} degrees: N clicks", font=f, fill=(20, 24, 30))
    titled(both, "Rev 3 hat, cut north to south", "Thumb side to the left, north up. The rocker tips over the anvil's "
           "north edge; the north button goes in and the south side lifts. A push on the middle goes into the anvil. "
           "Behind the pod, the pen spring is squeezed between the spring cup (green) and the screw's head, so it pulls "
           "the screw, and with it the rocker, back onto the anvil", out)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    exploded(os.path.join(out, "hat3_exploded.png"))
    pod_view(os.path.join(out, "hat3_pod.png"))
    back_view(os.path.join(out, "hat3_back.png"))
    section(os.path.join(out, "hat3_section.png"))
