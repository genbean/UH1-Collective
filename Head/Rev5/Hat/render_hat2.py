# Renders for the SEARCH CONT hat, Rev 2 (hat2_r5.py), in the style of renders/make_diagrams.py: parts on the light
# gradient, a title over each.
#
# usage: render_hat2.py <out dir>
import os
import sys
import numpy as np
import pyvista as pv
import manifold3d as mf
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hat2_r5 as m2
import hat_r5 as v1
import huey_head_r5 as h

BG_TOP, BG_BOT = (250, 251, 252), (228, 231, 236)
GREY, DARK, YELLOW, ORANGE, BLUE, STEEL, RED = "#9aa3ad", "#3d4650", "#f2c230", "#e8823a", "#4f8fd6", "#c9ced4", "#d64545"
FONT = "C:/Windows/Fonts/segoeui.ttf"
FONT_B = "C:/Windows/Fonts/segoeuib.ttf"


def to_pv(m):
    out = m.to_mesh()
    v = np.asarray(out.vert_properties)[:, :3].astype(float)
    f = np.asarray(out.tri_verts)
    return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), f]).ravel())


def render(items, view, up, size=(1400, 1100), zoom=1.0, parallel=False):
    p = pv.Plotter(off_screen=True, window_size=size, lighting="light kit")
    p.set_background(BG_BOT, top=BG_TOP)
    for m, col in items:
        p.add_mesh(to_pv(m), color=col, smooth_shading=True, split_sharp_edges=True, feature_angle=35, ambient=0.22,
                   diffuse=0.8, specular=0.15, specular_power=18)
    b = np.array([m.bounding_box() for m, _ in items])
    lo, hi = b[:, :3].min(0), b[:, 3:].max(0)
    ctr = (lo + hi) / 2
    view = np.asarray(view, float) / np.linalg.norm(view)
    p.camera_position = [tuple(ctr + view * 1000), tuple(ctr), tuple(up)]
    if parallel:
        p.enable_parallel_projection()
    p.reset_camera(bounds=(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    p.camera.zoom(zoom)
    p.enable_anti_aliasing("ssaa")
    img = Image.fromarray(p.screenshot(return_img=True))
    p.close()
    a = np.asarray(img).astype(int)                   # trim the background: compare each row with its left edge
    ys, xs = np.nonzero(np.abs(a - a[:, :1, :]).sum(2) > 24)
    mg = 40
    return img.crop((max(xs.min() - mg, 0), max(ys.min() - mg, 0), min(xs.max() + mg, a.shape[1]), min(ys.max() + mg, a.shape[0])))


def titled(img, title, subtitle, out):
    f1, f2 = ImageFont.truetype(FONT_B, 34), ImageFont.truetype(FONT, 22)
    W = max(img.width, 900)
    d = ImageDraw.Draw(img)
    lines, cur = [], ""
    for w in subtitle.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f2) > W - 56 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    top = 70 + 30 * len(lines)
    canvas = Image.new("RGB", (W, img.height + top), "white")
    canvas.paste(img, ((W - img.width) // 2, top))
    d = ImageDraw.Draw(canvas)
    d.text((28, 18), title, font=f1, fill=(20, 24, 30))
    for i, ln in enumerate(lines):
        d.text((28, 64 + 30 * i), ln, font=f2, fill=(80, 88, 98))
    canvas.save(out)
    print("wrote", out)


def carrier_crop():
    lp, _ = v1.lower_panel_new()
    return lp.translate((-m2.SEARCH[0], 0, -m2.SEARCH[1])) ^ v1.ycyl(0, 0, 34, -3.0, 9.0)


def switches():
    out = mf.Manifold()
    for k in range(4):
        b, bt, lg = v1.tact(k)
        out += b + bt
    return out


def exploded(out):
    panel = carrier_crop()
    gap = 9.0
    items = [(panel, GREY), (switches(), YELLOW),
             (m2.plate().translate((0, -1 * gap, 0)), ORANGE),
             (m2.cup().translate((0, -1.6 * gap, 0)), BLUE),
             (m2.spring().translate((0, -2.1 * gap, 0)), STEEL),
             (m2.bezel().translate((0, -2.7 * gap, 0)), DARK),
             (m2.m2_screws().translate((0, -3.0 * gap, 0)), STEEL),
             (m2.screw().translate((0, -3.4 * gap, 0)), STEEL),
             (m2.cap().translate((0, -4.4 * gap, 0)), DARK)]
    img = render(items, view=(1.0, -0.75, 0.45), up=(0, 0, 1), zoom=1.1)
    titled(img, "SEARCH CONT hat, Rev 2", "Front to back: cap, M3 x 12 screw, M2 bezel screws, bezel, pen spring, cup, "
           "rocker plate, the four switches in the panel's carrier", out)


def plate_rear(out):
    img = render([(m2.plate(), ORANGE)], view=(0.45, 1.0, 0.7), up=(0, 0, 1), zoom=1.0)
    titled(img, "Rev 2 rocker plate, from behind", "Two feet on each switch's cover, a domed pusher over each button, "
           "the boss that keeps it central", out)


def section(out):
    """N-S section (x < 0 kept), at rest and tipped north to the nominal click."""
    half = mf.Manifold.cube((40, 40, 60)).translate((-40, -20, -30))
    fixed = [(carrier_crop(), GREY), (switches(), YELLOW), (m2.bezel(), DARK), (m2.screw(), STEEL)]
    n, d = np.array([0.0, 1.0]), m2.FOOT[1]
    th = next(t for t in np.radians(np.arange(0, 20, 0.05)) if m2.btn_travel(n, d, t)[0] >= m2.CLICK[1])
    imgs = []
    for t in (0.0, th):
        moving = [(m2.tipped(m2.plate(), n, d, t), ORANGE), (m2.tipped(m2.cap(), n, d, t), DARK)]
        items = [(m ^ half, c) for m, c in fixed + moving]
        imgs.append(render(items, view=(1, 0, 0), up=(0, 0, 1), zoom=1.05, parallel=True))
    W = imgs[0].width + imgs[1].width
    Hh = max(i.height for i in imgs)
    both = Image.new("RGB", (W, Hh + 40), BG_TOP)
    both.paste(imgs[0], (0, 40))
    both.paste(imgs[1], (imgs[0].width, 40))
    d = ImageDraw.Draw(both)
    f = ImageFont.truetype(FONT_B, 24)
    d.text((30, 6), "At rest: all eight feet down", font=f, fill=(20, 24, 30))
    d.text((imgs[0].width + 30, 6), f"Pushed north, {np.degrees(th):.1f} degrees: N clicks", font=f, fill=(20, 24, 30))
    titled(both, "Rev 2 hat, cut north to south", "Thumb side to the left, north up. It tips over the two feet on the "
           "north switch, so the south side rises and only the north button goes in", out)


def feet_diagram(out):
    """Looking at the hat from the front: the feet's octagon, the buttons, and the line it tips over for N and NE."""
    fig, ax = plt.subplots(figsize=(8, 8), dpi=130)
    ax.set_aspect("equal")
    ax.axis("off")
    pts = np.array(m2.foot_pts())
    ang = np.arctan2(pts[:, 0], pts[:, 1])
    pts = pts[np.argsort(ang)]
    for k in range(4):                                             # switch covers
        a = np.radians(90 * k)
        R = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])
        sq = np.array([[-3, 4], [3, 4], [3, 10], [-3, 10]]) @ R.T
        ax.add_patch(Polygon(sq, closed=True, fc="#fbe7a1", ec="#b8941a", lw=1))
    ax.add_patch(Polygon(pts, closed=True, fc="#e8f0fa", ec=BLUE, lw=1.5, ls="--"))
    for x, z in m2.btn_pts():
        ax.add_patch(Circle((x, z), m2.BTN_R, fc=YELLOW, ec="#8a6d00", lw=1))
    for x, z in pts:
        ax.add_patch(Circle((x, z), m2.FOOT_D / 2, fc=ORANGE, ec="#7a3b0b", lw=1))
    ax.plot([-6, 6], [m2.FOOT[1]] * 2, color=RED, lw=2.5)
    ax.text(-6.3, m2.FOOT[1] + 1.2, "push N: it tips over this line;\nthe N button is 2.4 mm beyond it", color=RED,
            ha="right", fontsize=10)
    a, b = (m2.FOOT[0], m2.FOOT[1]), (m2.FOOT[1], m2.FOOT[0])
    e = np.array(b) - np.array(a)
    e /= np.linalg.norm(e)
    ax.plot([a[0] - 3.5 * e[0], b[0] + 3.5 * e[0]], [a[1] - 3.5 * e[1], b[1] + 3.5 * e[1]], color=RED, lw=2.5)
    ax.text(8.6, 5.2, "push NE: it tips over this line,\nwhich runs just past the centres\nof the N and E buttons, where\n"
            "the plate's pushers touch them:\nneither goes in", color=RED, fontsize=10)
    ax.text(0, 0, "push here:\nall feet down,\nnothing moves", ha="center", va="center", fontsize=10, color=DARK)
    for x, z, s in ((0, 7, "N"), (7, 0, "E"), (0, -7, "S"), (-7, 0, "W")):
        ax.text(x * 1.62, z * 1.62, s, ha="center", va="center", fontsize=14, weight="bold", color=DARK)
    ax.set_xlim(-17, 17)
    ax.set_ylim(-13, 13)
    fig.savefig(out + ".tmp.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    img = Image.open(out + ".tmp.png").convert("RGB")
    os.remove(out + ".tmp.png")
    titled(img, "Why only one switch can click", "From the front: switch covers (pale yellow), buttons (yellow), the "
           "plate's eight feet (orange) and their octagon", out)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    feet_diagram(os.path.join(out, "hat2_feet.png"))
    exploded(os.path.join(out, "hat2_exploded.png"))
    plate_rear(os.path.join(out, "hat2_plate_rear.png"))
    section(os.path.join(out, "hat2_section.png"))
