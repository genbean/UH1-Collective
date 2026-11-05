# Renders for the SEARCH CONT hat, Rev 4 (hat4_r5.py), in render_hat2.py's style.
#
# usage: render_hat4.py <out dir>
import os
import sys
import numpy as np
import manifold3d as mf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hat4_r5 as m4
import huey_head_r5 as h
from render_hat2 import render, titled, GREY, DARK, YELLOW, ORANGE, BLUE, STEEL, FONT_B

GREEN = "#2e8b57"                                       # the board
BLACK = "#2b2f33"                                       # the switch's body
WHITE = "#f4f4f4"


def panel_crop(r=18.5):
    lp, txt = m4.lower_panel()
    crop = h.ycyl(0, 0, 2 * r, -3.0, 8.0)
    return ((lp.translate((-m4.SEARCH[0], 0, -m4.SEARCH[1])) ^ crop),
            (txt.translate((-m4.SEARCH[0], 0, -m4.SEARCH[1])) ^ crop))


def hat_parts():
    hous, plug = m4.j1()
    return [(m4.board(), GREEN), (m4.switch_body(), BLACK), (m4.stick(), STEEL), (hous, WHITE), (m4.screws(), STEEL)]


def exploded(out):
    panel, txt = panel_crop()
    g = 10.0
    sh = lambda parts, dy: [(p.translate((0, dy, 0)), c) for p, c in parts]
    items = ([(m4.cap().translate((0, -1.4 * g, 0)), DARK), (panel, GREY), (txt, WHITE)]
             + sh([(m4.board(), GREEN), (m4.switch_body(), BLACK), (m4.stick(), STEEL), (m4.j1()[0], WHITE)], 2.0 * g)
             + sh([(m4.screws(), STEEL)], 3.4 * g))
    img = render(items, view=(1.0, 0.55, 0.45), up=(0, 0, 1), zoom=1.1)
    titled(img, "SEARCH CONT hat, Rev 4", "From behind and to the side. Front to back: the cap, the panel with its hole "
           "and the four bosses on its back, the breakout board with the ALPS RKJXM1015004 on its front and J1 on its "
           "back, the four M2 x 8 countersunk screws", out)


def back_view(out):
    panel, txt = panel_crop()
    hous, plug = m4.j1()
    items = [(panel, GREY), (txt, WHITE)] + hat_parts() + [(m4.cap(), DARK)]
    img = render(items, view=(0.55, 1.0, 0.6), up=(0, 0, 1), zoom=1.15)
    titled(img, "Rev 4 hat from behind", "The board sits on the four bosses printed on the panel's back, held by four "
           "M2 x 8 countersunk screws. J1 (JST SH, 6-pin) is at its top, the cable leaving upward; the six wire pads "
           "along its bottom are the other way to wire it", out)


def section(out):
    half = mf.Manifold.cube((40, 60, 70)).translate((-40, -30, -35))
    panel, txt = panel_crop()
    hous, plug = m4.j1()
    fixed = [(panel, GREY), (txt, WHITE), (m4.board(), GREEN), (m4.switch_body(), BLACK), (hous, WHITE), (m4.screws(), STEEL)]
    n, yp, th = np.array([0.0, 1.0]), m4.Y_MF - m4.BODY_H / 2, np.radians(m4.TILT_SIDE)
    imgs = []
    for t in (0.0, th):
        moving = [(m4.tipped(m4.stick(), n, t, yp), STEEL), (m4.tipped(m4.cap(), n, t, yp), DARK)]
        items = [(mm ^ half, c) for mm, c in fixed + moving]
        imgs.append(render(items, view=(1, 0, 0), up=(0, 0, 1), zoom=1.05, parallel=True))
    W, Hh = imgs[0].width + imgs[1].width, max(i.height for i in imgs)
    both = Image.new("RGB", (W, Hh + 40), (250, 251, 252))
    both.paste(imgs[0], (0, 40))
    both.paste(imgs[1], (imgs[0].width, 40))
    d_ = ImageDraw.Draw(both)
    f = ImageFont.truetype(FONT_B, 24)
    d_.text((30, 6), "At rest", font=f, fill=(20, 24, 30))
    d_.text((imgs[0].width + 30, 6), f"Pushed EXT to the switch's stop, {m4.TILT_SIDE:.0f} degrees", font=f, fill=(20, 24, 30))
    titled(both, "Rev 4 hat, cut through EXT and RETR", "Thumb side to the left, EXT up. The stick's tip bears on the end "
           "of the cap's socket. The switch's body comes through the panel's hole, flush with its face; the board sits on "
           "the bosses behind. At the switch's stop the cap's rim is still 1.8 degrees or more from the panel", out)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    exploded(os.path.join(out, "hat4_exploded.png"))
    back_view(os.path.join(out, "hat4_back.png"))
    section(os.path.join(out, "hat4_section.png"))
