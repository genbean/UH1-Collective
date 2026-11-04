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


def panel_crop():
    lp, _ = m3.lower_panel()
    return lp.translate((-m3.SEARCH[0], 0, -m3.SEARCH[1])) ^ h.ycyl(0, 0, 44, -3.0, 3.0)


def switches():
    out = mf.Manifold()
    for k in range(4):
        b, bt, lg = m3.tact(k)
        out += b + bt + lg
    return out


def exploded(out):
    g = 10.0
    items = [(m3.cap().translate((0, -2.6 * g, 0)), DARK), (m3.nut().translate((0, -1.9 * g, 0)), STEEL),
             (m3.rocker().translate((0, -1.4 * g, 0)), ORANGE), (panel_crop(), GREY),
             (switches().translate((0, 0.6 * g, 0)), YELLOW), (m3.pod().translate((0, 1.2 * g, 0)), BLUE),
             (m3.cup().translate((0, 1.8 * g, 0)), BLUE), (m3.spring().translate((0, 2.2 * g, 0)), STEEL),
             (m3.screw().translate((0, 2.8 * g, 0)), STEEL)]
    img = render(items, view=(1.0, -0.8, 0.5), up=(0, 0, 1), zoom=1.1)
    titled(img, "SEARCH CONT hat, Rev 3", "Front to back: cap, M3 nut, rocker, the panel with its round hole and pins, "
           "the four switches, the pod (glued to the panel), cup, pen spring, M3 x 20", out)


def pod_view(out):
    img = render([(m3.pod(), BLUE), (switches(), YELLOW)], view=(0.5, -1.0, 0.8), up=(0, 0, 1), zoom=1.0)
    titled(img, "Rev 3 pod, from the front", "The octagonal anvil in its square bore, the four switches in their "
           "pockets, and the three holes for the panel's pins. It prints back down", out)


def section(out):
    half = mf.Manifold.cube((40, 40, 60)).translate((-40, -20, -30))
    fixed = [(panel_crop(), GREY), (switches(), YELLOW), (m3.pod(), BLUE), (m3.cup(), BLUE)]
    n, d = np.array([0.0, 1.0]), m3.R_OCT
    th = next(t for t in np.radians(np.arange(0, 20, 0.05)) if m3.btn_travel(n, d, t)[0] >= m3.BTN_GAP + m3.CLICK[1])
    imgs = []
    for t in (0.0, th):
        moving = [(m3.tipped(p, n, d, t), c) for p, c in ((m3.rocker(), ORANGE), (m3.cap(), DARK), (m3.screw(), STEEL), (m3.nut(), STEEL))]
        items = [(mm ^ half, c) for mm, c in fixed + moving]
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
           "north edge; the north button goes in and the south side lifts. A push on the middle goes into the anvil", out)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    exploded(os.path.join(out, "hat3_exploded.png"))
    pod_view(os.path.join(out, "hat3_pod.png"))
    section(os.path.join(out, "hat3_section.png"))
