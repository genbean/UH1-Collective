"""
Renders for the MkIII base Rev 4, with Rev 3's renderer (../make_renders_r3.py) and colours.
    python make_renders_r4.py      -> renders/*.png and renders/MkIII_Rev4_Assembly.glb
Needs cadquery, trimesh, manifold3d, pyvista and pillow.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np                                     # noqa: E402
import trimesh                                         # noqa: E402
from PIL import Image, ImageDraw                        # noqa: E402
import make_renders_r3 as R                            # noqa: E402
import mk3_rev4 as v                                   # noqa: E402

d, m = R.d, R.m
OUT = os.path.join(HERE, "renders")
RED = (214, 48, 39)
HW = ("hardware", "lever_screws", "strut_pins")
SUB = ("Screws in red. Countersunk screws and nuts: AvrestYPT kit (the lever halves: HELIFOUNER M4 x 30-50 socket head "
       "cap kit and its nuts). Brake bolt: M5 x 30 hex head (Rev 3's).")


def to_mesh(shape):
    vv, f = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in vv]), np.array(f), process=True)


def colours():
    c = {k: col for k, (_, col) in R.load_glb(R.BASE_GLB).items()}
    c.update({"spring_cap": c["shoe"], "sensor_wires": (200, 60, 160)})
    return c


def scene(theta, C, tube_to=None):
    P = {}
    for name, shp in v.build(theta).items():
        if name == "carbon_tube" and tube_to is not None:
            shp = v.rot_y(v.carbon_tube(-m.SOCK_BOTTOM - tube_to), theta)
        P[name] = (to_mesh(shp), RED if name in HW else C[name])
    return P


def hide(P, *names):
    return {k: x for k, x in P.items() if k not in names}


def title(img, t, sub=""):
    W, H = img.size
    out = Image.new("RGB", (W, H + 90), (255, 255, 255))
    out.paste(img, (0, 90))
    dr = ImageDraw.Draw(out)
    dr.text((30, 14), t, fill=(20, 20, 24), font=d.font(34, bold=True))
    if sub:
        dr.text((30, 56), sub, fill=(80, 80, 88), font=d.font(22))
    return out


def width_bar(img, xl, xr, y, text):
    dr = ImageDraw.Draw(img)
    ink = (20, 20, 24)
    for x in (xl, xr):
        dr.line([(x, y - 18), (x, y + 18)], fill=ink, width=3)
    dr.line([(xl, y), (xr, y)], fill=ink, width=3)
    for x, s in ((xl, 1), (xr, -1)):
        dr.polygon([(x, y), (x + s * 16, y - 7), (x + s * 16, y + 7)], fill=ink)
    f = d.font(30, bold=True)
    tw = dr.textlength(text, font=f)
    dr.rectangle([(xl + xr - tw) / 2 - 8, y - 46, (xl + xr + tw) / 2 + 8, y - 10], fill=(255, 255, 255))
    dr.text(((xl + xr - tw) / 2, y - 44), text, fill=ink, font=f)


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p, optimize=True)
    print("wrote", os.path.relpath(p, HERE))


def labelled(P, groups, view, t, out, **kw):
    anchors, labels = [], []
    for g, s, pts in groups:
        labels.append((g, s, list(range(len(anchors), len(anchors) + len(pts)))))
        anchors += [tuple(map(float, q)) for q in pts]
    img, px = R.render(P, view, anchors=anchors, size=kw.pop("size", (1500, 1100)), **kw)
    d.compose(img, px, labels, t, SUB, os.path.join(OUT, out))
    print("wrote", os.path.join("renders", out))


def glb(P, path):
    sc = trimesh.Scene()
    for name, (mesh, col) in P.items():
        mm = mesh.copy()
        mm.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[*col, 255], metallicFactor=0.1, roughnessFactor=0.7))
        sc.add_geometry(mm, node_name=name, geom_name=name)
    sc.export(path)
    print("wrote", os.path.relpath(path, HERE))


def frame_top(C):
    """the frame alone from above, the brake tower at the top of the picture"""
    P = {"frame": (to_mesh(v.static_parts()["frame"]), C["frame"])}
    save(title(R.render(P, (-0.3, 0.0, 1.0), up=(1, 0, 0), size=(1100, 1400), zoom=1.0)[0],
               "Rev 4 frame from above", "The up-stop pad behind the axis, and the 45 deg gussets at each corner of the "
               "pillow blocks"), "rev4_frame_top.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    C = colours()
    frame_top(C)
    P0 = scene(0.0, C, tube_to=-200.0)
    P32 = scene(v.STOP_DEG, C, tube_to=-200.0)
    glb(scene(0.0, C), os.path.join(OUT, "MkIII_Rev4_Assembly.glb"))
    focus = ((-150, -60, -58), (100, 60, 40))

    save(title(R.render(P0, (-0.45, -0.85, 0.38), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "MkIII base Rev 4: 82 mm (3.25 in) wide",
               "Symmetrical lever on 6808-2RS thin bearings, the AS5600 inside the trunnion, the brake behind the hub"),
         "rev4_hero.png")
    save(title(R.render(P0, (0.75, 0.6, 0.5), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "Rev 4 from behind", "The brake knob on the back of the tower; the USB cable leaves through the cable "
               "cover's rim"), "rev4_rear.png")
    save(title(R.render(P32, (-0.2, -1.0, 0.25), size=(1600, 1000), focus=((-170, -60, -58), (100, 60, 100)))[0],
               "Rev 4 at the 32 deg up-stop", "Both up-stop lugs land on the pad behind the axis; the shoe stays on the hub's back"),
         "rev4_32deg.png")

    # the brake and the slotted up-stop: frame, caps and covers hidden, from behind and below
    inner = ("frame", "cap_left", "cap_right", "cover_sensor", "cover_cable", "hardware", "bearing_outer",
             "bearing_seal", "usb_cable", "gas_strut", "strut_pins", "strut_collar", "carbon_tube", "hose_clamp")
    for th, P, name, sub in ((0.0, P0, "rev4_brake_lugs.png", "At 0 deg the shoe's lower end sits between the two "
                              "up-stop lugs; the hub between them is a plain cylinder for the felt"),
                             (v.STOP_DEG, P32, "rev4_brake_lugs_32deg.png", "At 32 deg the lugs have swung down, "
                              "either side of the shoe, onto the pad behind the axis (frame hidden)")):
        save(title(R.render(hide(P, *inner), (1.0, -0.55, -0.45), size=(1500, 1050),
                            focus=((-10, -35, -45), (75, 35, 35)), zoom=1.0)[0],
                   f"Brake shoe and up-stop lugs, {th:.0f} deg", sub), name)

    # widths: Rev 3 and Rev 4 from above, same scale, tube pointing up the page
    src = R.load_glb(R.BASE_GLB)
    old = R.base_only(R.pose(src, 0.0, tube_to=-200.0))
    view, up, fo = (0, 0, 1), (-1, 0, 0), ((-150, -70, -60), (100, 70, 45))
    img_o, px_o = R.render(old, view, up=up, size=(1000, 1300), focus=fo, parallel=True,
                           anchors=[(92, -65.0, 50), (92, 65.0, 50)])
    img_n, px_n = R.render(P0, view, up=up, size=(1000, 1300), focus=fo, parallel=True,
                           anchors=[(92, -v.W_HALF, 50), (92, v.W_HALF, 50)])
    width_bar(img_o, px_o[0][0], px_o[1][0], int(px_o[0][1]), "Rev 3: 130 mm (5.1 in)")
    width_bar(img_n, px_n[0][0], px_n[1][0], int(px_n[0][1]), "Rev 4: 82 mm (3.25 in)")
    both = Image.new("RGB", (2000, 1300), (255, 255, 255))
    both.paste(img_o, (0, 0))
    both.paste(img_n, (1000, 0))
    save(title(both, "Rev 3 and Rev 4 from above, to the same scale",
               "Lever symmetrical about the tube; bearings, covers and brake all inside the 82 mm"), "rev4_vs_rev3_top.png")

    # section on the pivot axis, from the front
    Pc = R.cut(hide(P0, "carbon_tube"), 0, 0.0, keep="above")
    img, px = R.render(Pc, (-1, 0, 0), size=(1600, 1100), focus=((0, -45, -58), (40, 45, 40)), parallel=True,
                       anchors=[(0, -v.W_HALF, 36), (0, v.W_HALF, 36)])
    width_bar(img, px[0][0], px[1][0], int(px[0][1]) - 10, "82 mm")
    save(title(img, "Section on the pivot axis, from the front",
               "6808-2RS bearings. Sensor (right): the AS5600 in the trunnion's end, the magnet on the cover's post. "
               "USB (left): the cable turns out of the axis inside the cover"), "rev4_section_axis.png")

    # sections on the tube's plane, from the sensor side
    for P, name, t in ((P0, "rev4_section_brake.png", "Section on the tube's plane, 0 deg"),
                       (P32, "rev4_section_brake_32deg.png", "Section on the tube's plane, at the 32 deg stop")):
        Pc = R.cut(P, 1, -0.01, keep="above")
        save(title(R.render(Pc, (0, -1, 0), size=(1700, 1000), focus=((-140, 0, -58), (100, 0, 40)), parallel=True)[0],
                   t, "The knob turns an M5 bolt through a captive nut; its tip pushes the spring cap, the spring pushes "
                   "the felt-faced shoe onto the hub"), name)

    # screws
    caps = [np.array([x, s * (v.BRG_Y0 + v.BLOCK_Y1) / 2, v.CAP_HEAD_Z]) for s in (-1, 1) for x in (-v.CAP_BOLT_X, v.CAP_BOLT_X)]
    lev = [np.array([x, y, zh + 4]) for x, y, zh, *_ in v.lever_screw_seats()]
    covers = lambda s: [np.array([px, s * v.W_HALF, pz]) for px, pz in
                        (m.on_circle(v.COVER_HOLE_R, a) for a in (45, 135, 225, 315))]
    knob = np.array([v.KNOB_X0 + 34, 0, 0])
    nut5 = np.array([v.NUT5_X + 2, 0, v.TOWER_TOP])
    labelled(P0, [("M4 socket head cap  (x4)", "lever halves, from the top: front pair x 40, back pair x 50; M4 nuts "
                   "in the lower half", lev),
                  ("M3 x 20 countersunk  (x4)", "pillow-block caps, from the top, into M3 nuts slid into the blocks "
                   "from the front and back", caps),
                  ("M5 x 30 hex bolt (Rev 3's)", "brake: its head on the floor of the knob's hex pocket", [knob]),
                  ("M5 nut", "brake: slides into the tower's slot from the top", [nut5])],
             (0.55, 0.35, 1.0), "MkIII base Rev 4 screws: from above and behind", "rev4_screws_top.png",
             focus=((-60, -45, -58), (100, 45, 40)), zoom=1.0)
    labelled(P0, [("M3 x 16 countersunk  (x4)", "sensor cover: tap the block and cap M3, 7.5 mm deep", covers(-1)),
                  ("M4 nut  (x2)", "the strut's eyes: M4 x 16 countersunk from the +y side, nuts in the -y cheeks",
                   [np.array([-v.r.COLLAR_D, -7.3, -v.r.COLLAR_E]),
                    np.array([v.r.ANCH_X, -((v.r.ROD_TAB_T + 0.6) / 2 + v.r.CLEVIS_T), v.r.ANCH_Z])])],
             (-0.3, -1.0, 0.4), "MkIII base Rev 4 screws: sensor (-y) side", "rev4_screws_sensorside.png",
             focus=((-150, -50, -58), (100, 50, 40)), zoom=1.05)
    labelled(P0, [("M3 x 16 countersunk  (x4)", "cable cover: tap the block and cap M3, 7.5 mm deep", covers(1))],
             (0.5, 1.0, 0.4), "MkIII base Rev 4 screws: USB (+y) side", "rev4_screws_usbside.png",
             focus=((-60, -50, -58), (100, 50, 40)), zoom=1.05)


if __name__ == "__main__":
    main()
