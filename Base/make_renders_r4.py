"""
Renders for the MkIII base Rev 4, with the shared render helpers (make_renders_r3.py, as R), the diagram helpers in
../renders/make_diagrams.py, and the parts' colours (COLOURS, as the earlier revisions had them).
    python make_renders_r4.py      -> renders/*.png (views, sections, screw maps, the exploded views and the screw chart),
                                      rev4_exploded.html and rev4_lever_exploded.html (the exploded views, a popup
                                      on each part: `python make_renders_r4.py exploded` makes only these),
                                      renders/MkIII_Rev4_Assembly.glb, and the complete collective with the head:
                                      ../renders/HeliCollective_Assembly.glb, _0deg.png, _32deg.png, _side.png
The head comes from ../Head (its STLs and its hat script), apart from its bought parts, which only the collective GLB has.
Run ../renders/make_diagrams.py after it: the head's diagrams read the head from that collective GLB.
Needs cadquery, trimesh, manifold3d, pyvista and pillow.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np                                     # noqa: E402
import trimesh                                         # noqa: E402
from PIL import Image, ImageDraw                        # noqa: E402

_pil_save = Image.Image.save


def _save_retrying(self, fp, *a, **kw):
    """Windows: a PNG open in a viewer (or being indexed) can refuse a write for a moment; try again before failing"""
    import time
    for k in range(20):
        try:
            return _pil_save(self, fp, *a, **kw)
        except OSError:
            if k == 19:
                raise
            time.sleep(0.5)


Image.Image.save = _save_retrying
import make_renders_r3 as R                            # noqa: E402
import mk3_rev4 as v                                   # noqa: E402
from mk3_pivot import cyl, fuse                         # noqa: E402

d, m = R.d, R.m
OUT = os.path.join(HERE, "renders")
RED = (214, 48, 39)
DOWEL = (236, 190, 62)
HW = ("hardware", "lever_screws", "tube_lock", "sensor_screws", "strut_pins")
SUB = ("Screws in red. Countersunk screws and nuts: AvrestYPT kit (the lever halves and the shell: HELIFOUNER M4 x 30-50 socket head "
       "cap kit and its nuts). Brake bolt: M5 x 35 hex head.")


def to_mesh(shape):
    vv, f = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in vv]), np.array(f), process=True)


# every part's colour (RGB). The same as Rev 3's: the shell is its caps' colour, the strap its shoe's, the lever halves
# its upper and lower halves'
COLOURS = {
    "frame": (227, 178, 60), "shell": (217, 166, 48),
    "lever_sensor": (76, 175, 80), "lever_cable": (59, 143, 64), "lever_dowel": DOWEL,
    "strap": (192, 57, 43), "felt": (91, 80, 72), "friction_knob": (35, 37, 39),
    "cover_sensor": (63, 120, 194), "cover_cable": (63, 120, 194), "strut_collar": (232, 118, 44),
    "bearing_inner": (141, 148, 156), "bearing_outer": (141, 148, 156), "bearing_seal": (32, 34, 36),
    "carbon_tube": (58, 61, 66), "gas_strut": (43, 46, 51), "hose_clamp": (213, 217, 221),
    "hardware": (74, 79, 86), "lever_screws": (74, 79, 86), "tube_lock": (74, 79, 86),
    "sensor_screws": (74, 79, 86), "strut_pins": (74, 79, 86), "knob_spring": (184, 190, 197),
    "magnet": (154, 163, 173), "sensor_pcb": (91, 47, 145), "sensor_chip": (17, 17, 17),
    "sensor_wires": (200, 60, 160), "usb_cable": (24, 25, 27),
}


def colours():
    return dict(COLOURS)


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
    """the frame alone from above, the brake strap's bay at the top of the picture"""
    P = {"frame": (to_mesh(v.static_parts()["frame"]), C["frame"])}
    save(title(R.render(P, (-0.3, 0.0, 1.0), up=(1, 0, 0), size=(1100, 1400), zoom=1.0)[0],
               "Rev 4 frame from above", "The up-stop pad, slotted for the brake strap's arm; the clevis's rib and the "
               "webs that carry its hinge pin"), "rev4_frame_top.png")


def frame_strap_top(C):
    """the frame from above with the brake strap on its pin: its cheeks either side of the clevis's rib"""
    S = v.static_parts()
    P = {"frame": (to_mesh(S["frame"]), C["frame"]), "strap": (to_mesh(S["strap"]), C["strap"]),
         "felt": (to_mesh(S["felt"]), C["felt"])}
    for g, shp, _ in v.brake_screws():
        if g.startswith("hinge") or g == "brake nut":
            P[g] = (to_mesh(shp), RED)
    save(title(R.render(P, (-0.3, 0.0, 1.0), up=(1, 0, 0), size=(1100, 1400), zoom=1.0)[0],
               "Rev 4 frame from above, with the brake strap in", "Its cheeks either side of the clevis's rib, its pin "
               "through the rib and the webs"), "rev4_frame_strap_top.png")


def assembly_top(C, P0=None):
    """the whole base straight down from above, tube up the page, to scale"""
    P0 = P0 or scene(0.0, C, tube_to=-200.0)
    img, px = R.render(P0, (0, 0, 1), up=(-1, 0, 0), size=(1100, 1500), focus=((-200, -45, -60), (100, 45, 45)),
                       parallel=True, anchors=[(97, -v.W_HALF, 45), (97, v.W_HALF, 45)])
    width_bar(img, px[0][0], px[1][0], int(px[0][1]) + 40, "73 mm (2.87 in)")
    save(title(img, "Rev 4 from above", "Straight down, to scale, at 0 deg"), "rev4_top.png")


def back_view(C, P0=None):
    """from behind and a little above: the back chamfers through the frame and the shell, and the knob's seat"""
    P0 = P0 or scene(0.0, C, tube_to=-200.0)
    save(title(R.render(hide(P0, "carbon_tube", "strut_collar", "gas_strut", "strut_pins", "hose_clamp"), (1.0, 0.35, 0.45),
                        size=(1400, 1100), focus=((-40, -45, -58), (110, 45, 40)), zoom=1.0)[0],
               "Rev 4 from behind", "One 45 deg chamfer each side through the frame and the shell; the brake knob in "
               "its seat in the shell's top, leaning 30 deg forward"), "rev4_back.png")


def tube_lock_views(C):
    """the tube lock: the lever with the tube in, from the head's side (-y, the left) and the nut's side (+y), front and
    below"""
    ls, lc = v.lever_halves(0.0)
    P = {"lever_sensor": (to_mesh(ls), C["lever_sensor"]), "lever_cable": (to_mesh(lc), C["lever_cable"]),
         "carbon_tube": (to_mesh(v.carbon_tube(60.0)), C["carbon_tube"]), "tube_lock": (to_mesh(v.tube_lock()), RED)}
    imgs = [R.render(P, view, size=(1000, 850), focus=((-80, -25, -32), (5, 25, 32)), zoom=1.0)[0]
            for view in ((-0.45, -1.0, -0.35), (-0.45, 1.0, -0.35))]
    both = Image.new("RGB", (2000, 850), (255, 255, 255))
    for k, im in enumerate(imgs):
        both.paste(im, (1000 * k, 0))
    save(title(both, "Rev 4 tube lock",
               "M4 x 35 through the tube's centre line, in bosses over the down-stop pads: head on the left, the side "
               "on show (left picture), nut on the right, against the seat (right picture), both 0.5 mm under the faces"), "rev4_tube_lock.png")


def collar_views(C):
    """the strut collar on the tube with the strut's end, from the left (heads) and the right (nuts), below"""
    P = {"strut_collar": (to_mesh(v.strut_collar()), C["strut_collar"]),
         "pins": (to_mesh(fuse(*[s for n, s, _ in v.strut_screws() if not n.startswith("anchor")])), RED),
         "tube": (to_mesh(v.carbon_tube(170.0).cut(v.box(-120, 0, -20, 20, -20, 20))), C["carbon_tube"]),
         "strut": (to_mesh(v.moved(v.r.strut(0.0)).intersect(v.box(-175, -90, -20, 20, -60, 0))), C["gas_strut"])}
    imgs = [R.render(P, view, size=(1000, 850), focus=((-165, -20, -36), (-112, 20, 20)), zoom=1.0)[0]
            for view in ((-0.3, -1.0, -0.35), (-0.3, 1.0, -0.6))]
    both = Image.new("RGB", (2000, 850), (255, 255, 255))
    for k, im in enumerate(imgs):
        both.paste(im, (1000 * k, 0))
    save(title(both, "Rev 4 strut collar", "Split along the bottom: two M4 x 16 countersunk close the cheeks, the strut "
               "screw and one in front of it. Heads on the left (left picture), nuts on the right (right picture)"),
         "rev4_strut_collar.png")


def drill_guide_views(C):
    """the tube drill guide on the tube's end, in its own frame, from above and from the drilling face"""
    g = v.drill_guide()
    t = v.tube(m.TUBE_OD / 2, m.TUBE_ID / 2, (0, 0, v.GUIDE_END_T), (0, 0, 110.0))
    P = {"guide": (to_mesh(g), (232, 118, 44)), "tube": (to_mesh(t), C["carbon_tube"])}
    imgs = [R.render(P, view, size=(1000, 900), up=(0, 0, 1), zoom=1.0)[0]
            for view in ((1.0, -0.6, 0.5), (1.0, 0.0, 0.0))]
    both = Image.new("RGB", (2000, 900), (255, 255, 255))
    for k, im in enumerate(imgs):
        both.paste(im, (1000 * k, 0))
    save(title(both, "Tube drill guide", "Over the tube's lever end, the tube's end against its closed end. Its drilling "
               "faces are 42.5 mm from the tube's axis, like the head's sides: 30 mm of guide to the tube. Windows mark "
               "the cable notches"), "rev4_drill_guide.png")


def lever_views(C):
    """the lever alone: from the side, the fairings over and under the socket boss running into the hub; and from the
    front and above"""
    ls, lc = v.lever_halves(0.0)
    P = {"lever_sensor": (to_mesh(ls), C["lever_sensor"]), "lever_cable": (to_mesh(lc), C["lever_cable"])}
    save(title(R.render(P, (0.0, -1.0, 0.05), size=(1500, 950), zoom=1.0)[0], "Rev 4 lever from the side",
               "The fairings over and under the socket boss: from the hose-clamp groove, tangent to the hub"),
         "rev4_lever_side.png")
    save(title(R.render(P, (-0.55, -0.2, 1.0), size=(1300, 1100), zoom=1.0)[0], "Rev 4 lever from the front and above",
               "The upper fairing, 21 mm wide; the halves meet on the tube's plane"), "rev4_lever_top.png")
    save(title(R.render(P, (-0.6, -0.55, -0.6), size=(1300, 1000), focus=((-66, -25, -32), (5, 25, 5)), zoom=1.0)[0],
               "Rev 4 lever from the front and below",
               "The down-stop pads run in to the lower fairing, so each half prints with nothing hanging under them"),
         "rev4_lever_under.png")
    save(title(R.render({"lever_sensor": P["lever_sensor"]}, (0.15, -1.0, 0.25), size=(1200, 1000),
                        focus=((-15, -32, -15), (15, -20, 15)), zoom=1.0)[0], "Rev 4 sensor pocket",
               "Four M2 posts for the AS5600 module, each joined to a ledge, 1.6 mm pilots"), "rev4_sensor_pocket.png")
    tube_lock_views(C)
    collar_views(C)
    drill_guide_views(C)
    lever_exploded(C)
    P32 = scene(v.STOP_DEG, C, tube_to=-120.0)
    keep = ("lever_sensor", "lever_cable", "lever_screws", "lever_dowel", "gas_strut", "strut_pins", "carbon_tube",
            "bearing_outer", "bearing_inner", "bearing_seal")
    save(title(R.render({k: x for k, x in P32.items() if k in keep}, (-0.25, -0.75, -0.6), size=(1300, 1050),
                        focus=((-45, -25, -50), (15, 25, 5)), zoom=1.0)[0],
               "Rev 4 lever from below, at the 32° stop",
               "The relief in the hub's underside for the strut's cylinder: 1.5 mm clear of it all the way up"),
         "rev4_strut_relief.png")


def usb_views(C):
    """the USB cable's bend, cable cover off, at 0 deg and at the stop: the relief in the trunnion's end turns under it"""
    imgs = []
    for th in (0.0, v.STOP_DEG):
        P = {k: x for k, x in scene(th, C, tube_to=-120.0).items() if k != "cover_cable"}
        imgs.append(R.render(P, (-0.15, 1.0, 0.12), size=(1000, 900), focus=((-45, 15, -25), (15, 40, 25)), zoom=1.0)[0])
    both = Image.new("RGB", (2000, 900), (255, 255, 255))
    both.paste(imgs[0], (0, 0))
    both.paste(imgs[1], (1000, 0))
    save(title(both, "The USB cable's bend, cable cover off: 0° (left) and the 32° stop (right)",
               "18 mm radius, toward the front. The pie-shaped relief in the trunnion's end turns with the lever, "
               "0.5 mm clear of the cable all the way"), "rev4_usb_bend.png")


def joint_views(C, P0=None):
    """the frame's half of the joint with the grid's pyramids; and the front, the frame's wall carrying on the shell's
    cut for the lever"""
    P0 = P0 or scene(0.0, C, tube_to=-200.0)
    n = len(v.grid_sites(v.chamfer_edges(v.frame(), exclude=v.joint_edge), v.shell()))
    save(title(R.render({"frame": P0["frame"]}, (0.35, -0.3, 1.0), size=(1400, 1100), zoom=1.0)[0],
               "Rev 4 frame: its half of the joint",
               f"A diamond knurl, {n} pyramids 2.4 mm across and 0.7 mm tall, on every land either side of the bearings; the shell has a socket over each"),
         "rev4_joint_grid.png")
    keep = ("frame", "shell", "cover_sensor", "cover_cable", "lever_sensor", "lever_cable", "lever_screws", "gas_strut",
            "bearing_outer", "bearing_inner", "bearing_seal", "hardware")
    save(title(R.render({k: x for k, x in P0.items() if k in keep}, (-1.0, -0.35, 0.3), size=(1300, 1100),
                        focus=((-50, -45, -58), (40, 45, 40)), zoom=1.0)[0],
               "Rev 4 from the front (tube off)", "The frame's front wall carries on the shell's cut for the lever, "
               "and lets the strut through below it"), "rev4_front.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    C = colours()
    back_view(C)
    joint_views(C)
    lever_views(C)
    usb_views(C)
    frame_top(C)
    frame_strap_top(C)
    assembly_top(C)
    P0 = scene(0.0, C, tube_to=-200.0)
    P32 = scene(v.STOP_DEG, C, tube_to=-200.0)
    glb(scene(0.0, C), os.path.join(OUT, "MkIII_Rev4_Assembly.glb"))
    focus = ((-150, -60, -58), (100, 60, 40))

    save(title(R.render(P0, (-0.45, -0.85, 0.38), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "MkIII base Rev 4: 73 mm (2.87 in) wide",
               "One shell over the lever in place of the caps, 6808-2RS thin bearings, the brake behind the hub"),
         "rev4_hero.png")
    save(title(R.render(hide(P0, "shell", "friction_knob", "hardware"), (-0.45, -0.85, 0.38), size=(1600, 1050),
                        focus=focus, zoom=1.05)[0], "Rev 4 with the shell off",
               "The lever on its bearings, the brake strap behind the hub"), "rev4_open.png")
    save(title(R.render(P0, (0.75, 0.6, 0.5), size=(1600, 1050), focus=focus, zoom=1.05)[0],
               "Rev 4 from behind", "The brake knob in its seat in the shell's top; the USB cable leaves the cable cover "
               "toward the front"), "rev4_rear.png")
    save(title(R.render(P32, (-0.2, -1.0, 0.25), size=(1600, 1000), focus=((-170, -60, -58), (100, 60, 100)))[0],
               "Rev 4 at the 32 deg up-stop", "Both up-stop lugs land on the pad behind the axis; the strap stays on the hub's back"),
         "rev4_32deg.png")

    # the brake and the slotted up-stop: frame, caps and covers hidden, from behind and below
    inner = ("frame", "shell", "friction_knob", "cover_sensor", "cover_cable", "hardware", "bearing_outer",
             "bearing_seal", "usb_cable", "gas_strut", "strut_pins", "strut_collar", "carbon_tube", "hose_clamp")
    for th, P, name, sub in ((0.0, P0, "rev4_brake_lugs.png", "At 0 deg the strap's arm runs between the two up-stop "
                              "lugs, 2 mm clear of each; the hub between them is a plain cylinder for the felt"),
                             (v.STOP_DEG, P32, "rev4_brake_lugs_32deg.png", "At 32 deg the lugs have swung down, "
                              "either side of the strap, onto the pad behind the axis (frame hidden)")):
        save(title(R.render(hide(P, *inner), (1.0, -0.55, -0.45), size=(1500, 1050),
                            focus=((-10, -35, -45), (75, 35, 35)), zoom=1.0)[0],
                   f"Brake strap and up-stop lugs, {th:.0f} deg", sub), name)

    # section on the pivot axis, from the front
    Pc = R.cut(hide(P0, "carbon_tube"), 0, 0.0, keep="above")
    img, px = R.render(Pc, (-1, 0, 0), size=(1600, 1100), focus=((0, -45, -58), (40, 45, 40)), parallel=True,
                       anchors=[(0, -v.W_HALF, 36), (0, v.W_HALF, 36)])
    width_bar(img, px[0][0], px[1][0], int(px[0][1]) - 10, "73 mm")
    save(title(img, "Section on the pivot axis, from the front",
               "6808-2RS bearings. Sensor (right): the AS5600 in the trunnion's end, the magnet in the cover's pocket. "
               "USB (left): the cable turns toward the front, through the relief in the trunnion's end"), "rev4_section_axis.png")

    # sections on the tube's plane, from the sensor side
    for P, name, t in ((P0, "rev4_section_brake.png", "Section on the tube's plane, 0 deg"),
                       (P32, "rev4_section_brake_32deg.png", "Section on the tube's plane, at the 32 deg stop")):
        Pc = R.cut(P, 1, -0.01, keep="above")
        save(title(R.render(Pc, (0, -1, 0), size=(1700, 1150), focus=((-140, 0, -58), (100, 0, 72)), parallel=True)[0],
                   t, "The brake strap, hinged in the up-stop pad; the knob's M5 bolt leans 30 deg forward and draws its "
                   "head up and forward, swinging the felt onto the hub"), name)

    brake_lever_in(C)
    screw_views(P0)
    exploded(C)
    screw_chart()
    collective(C)


def brake_lever_in(C, lift=12.0):
    """the lever going in: the brake strap leans back on its own onto its bay's back wall, and the hub drops past its
    felt. In section on the tube's plane, the lever lift mm short of its seats; the shell, knob and tube not on yet"""
    up = v.V(0, 0, lift)
    moving = set(v.TURNS) | {"bearing_outer", "bearing_seal"}
    later = ("shell", "friction_knob", "hardware", "cover_sensor", "cover_cable", "magnet", "usb_cable", "gas_strut",
             "strut_pins", "strut_collar", "carbon_tube")
    P = {}
    for name, shp in v.build(0.0).items():
        if name in later:
            continue
        if name in ("strap", "felt"):
            shp = v.strap_at(shp, v.REST_DEG)
        elif name in moving:
            shp = shp.translate(up)
        P[name] = (to_mesh(shp), RED if name in HW else C[name])
    for g, shp, _ in v.brake_screws():
        if g == "brake nut":
            P[g] = (to_mesh(v.strap_at(shp, v.REST_DEG)), RED)
        elif g.startswith("hinge"):
            P[g] = (to_mesh(shp), RED)
    Pc = R.cut(P, 1, -0.01, keep="above")
    save(title(R.render(Pc, (0, -1, 0), size=(1500, 1150), focus=((-40, 0, -58), (65, 0, 50)), parallel=True)[0],
               f"The lever going in, {lift:.0f} mm above its seats (section on the tube's plane)",
               f"The brake strap leans back {v.REST_DEG:g} deg on its own, onto its bay's back wall, and the hub drops "
               "past its felt"), "rev4_brake_lever_in.png")


# ---------------------------------------------------------------------------------------------------- the hardware
def screws_and_nuts():
    """every screw and nut in the base at 0 deg, one shape each: [(group, cq shape, out)], out = tip to head (for nuts:
    the way they come out of their pockets)"""
    r = v.r
    H = []
    for s in (-1, 1):
        yb = s * v.CAP_BOLT_Y
        for x in (-v.CAP_BOLT_X, v.CAP_BOLT_X):
            scr, nut = v.shell_screw(x, yb)
            H += [("shell screw", scr, (0, 0, 1)), ("shell nut", nut, (0, s, 0))]
        for a in (45, 135, 225, 315):
            px, pz = m.on_circle(v.COVER_HOLE_R, a)
            H.append(("cover screw", m.csk_screw(3, (px, s * v.W_HALF, pz), (0, -s, 0), v.COVER_SCREW_L), (0, s, 0)))
    H += v.brake_screws()
    for x, z, sh in v.JOINT_SCREWS:                                               # the lever's, along the pivot axis
        H += [(f"lever screw {v.JS_SCREW_L}", fuse(cyl(r.CAP_D / 2, (x, sh * v.JS_SEAT, z),
                                                       (x, sh * (v.JS_SEAT + r.CAP_K), z)),
                                                   cyl(2.0, (x, -sh * v.JS_TIP, z), (x, sh * v.JS_SEAT, z))), (0, sh, 0)),
              ("lever nut", v.hex_xz(x, z, 7.0, -sh * v.JS_NUT[0], -sh * v.JS_NUT[1]), (0, -sh, 0))]
    H += v.strut_screws()                                                          # anchor, the collar's eye and clamp
    scr, nut = v.tube_lock_parts()
    H += [("tube lock screw", scr, (0, v.TL_HEAD, 0)), ("tube lock nut", nut, (0, -v.TL_HEAD, 0))]
    for x, z in v.AS_HOLES:
        H.append(("sensor screw", m.csk_screw(2, (x, -v.AS_HEAD_TOP, z), (0, 1, 0), v.AS_SCREW_L), (0, -1, 0)))
    return H


_HW = []


def heads_of(group):
    """the head end (or a nut's outer face) of every screw in a group, for the screw maps' anchors"""
    if not _HW:
        _HW.extend((g, to_mesh(shp), o) for g, shp, o in screws_and_nuts())
    return [msh.vertices[np.argmax(msh.vertices @ np.asarray(o, float))] for g, msh, o in _HW if g == group]


# ---------------------------------------------------------------------------------------------------- screw maps
def screw_views(P0):
    """between them, every screw and nut in the base, labelled"""
    covers = lambda s: [np.array([px, s * v.W_HALF, pz]) for px, pz in
                        (m.on_circle(v.COVER_HOLE_R, a) for a in (45, 135, 225, 315))]
    zn = v.CAP_NUT_Z - m.NUT_T[4] / 2
    side_nuts = [np.array([x, -v.BLOCK_Y1, zn]) for x in (-v.CAP_BOLT_X, v.CAP_BOLT_X)]   # the slots' mouths, -y
    desk = [np.array([x, y, v.Z_PLATE]) for x, y in v.DESK]
    bare = hide(P0, "carbon_tube", "strut_collar", "gas_strut", "strut_pins", "hose_clamp", "usb_cable", "sensor_wires")
    labelled(P0, [("M4 x 50 socket head cap  (x4)", "the shell, from the top, heads down 13 mm counterbores, each "
                   "centred on the joint, into M4 nuts slid into the pillow blocks from the sides (HELIFOUNER kit)",
                   heads_of("shell screw"))],
             (0.45, 0.3, 1.0), "MkIII base Rev 4 screws: the shell, from above", "rev4_screws_top.png",
             focus=((-60, -45, -58), (100, 45, 40)), zoom=1.0)
    lever_only = {k: x for k, x in P0.items() if k in ("lever_sensor", "lever_cable", "lever_screws", "lever_dowel")}
    other = {-1: "cable", 1: "sensor"}
    where = lambda x, z: ("front" if x < 0 else "back") + (", top" if z > 0 else ", bottom")
    for s, side, name in ((-1, "sensor (-y)", "rev4_screws_lever_sensor.png"),
                          (1, "cable (+y)", "rev4_screws_lever_cable.png")):
        groups = []
        for x, z, sh in v.JOINT_SCREWS:                             # one label each: no leaders crossing the hub
            if sh == s:
                groups.append((f"M4 x {v.JS_SCREW_L} socket head cap", f"{where(x, z)}: head in a 7.5 mm counterbore "
                               f"5 mm deep, along the pivot axis into a nut in the {other[s]} half (HELIFOUNER kit)",
                               [np.array([x, s * (v.JS_SEAT + v.r.CAP_K), z])]))
            else:
                groups.append(("M4 nut", f"{where(x, z)}: in a hex pocket, a flat toward the axis, for the "
                               f"{other[s]} half's screw. The bearing covers it", [np.array([x, s * v.JS_NUT[1], z])]))
        labelled(lever_only, groups, (-0.06, 1.0 * s, 0.1),
                 f"MkIII base Rev 4 screws: the lever's {side} end, bearing off (screw the halves up before pressing "
                 "the bearings on)", name, focus=((-36, 0, -36), (36, 0, 36)), zoom=1.0, parallel=True)
    labelled(hide(P0, "cover_sensor", "magnet", "carbon_tube", "strut_collar", "hose_clamp", "usb_cable",
                  "sensor_wires", "gas_strut", "strut_pins"),
             [("M4 nut  (x4)", "the shell's: two each side, slid into the slots in the pillow blocks' outer faces "
               "before the shell goes on; the side covers hide the slots", side_nuts)],
             (-0.15, -1.0, 0.2), "MkIII base Rev 4 screws: the shell's nuts (sensor cover off; the same on the USB side)",
             "rev4_screws_shellnuts.png", focus=((-45, -32, -30), (45, -32, 40)), zoom=1.0)
    labelled(bare,
             [("M5 x 35 hex bolt", "the brake: drop it into the knob's hex pocket, head down, and screw it down "
               "through the seat into the strap's nut", [np.array(v.on_bolt(v.r.MK2_KNOB_H).toTuple())])],
             (1.0, 0.4, 0.45), "MkIII base Rev 4 screws: from behind", "rev4_screws_back.png",
             focus=((-40, -45, -58), (110, 45, 75)), zoom=1.0)
    hb = v.on_bolt(v.KNOB_FLOOR + m.KNOB_BOLT[1] / 2)                                # the bolt's head
    a = np.radians(v.STRAP_PHI[0] + 30)
    labelled(R.cut(P0, 1, -0.01, keep="above"),
             [("M5 x 35 hex bolt", "turn the knob: the bolt's head sits on the floor of its hex pocket",
               [np.array(hb.toTuple())]),
              ("M5 nut", "dropped into the slot in the strap's head from its +y side; the bolt holds it",
               [np.array(v.on_bolt(v.T_NUT - m.NUT_T[5] / 2).toTuple())]),
              ("M4 x 50 socket head cap", "the strap's hinge pin: through the pillow blocks, the webs and the strut "
               "clevis's rib, head on +y, nut on -y", [np.array([v.HINGE_X, 0, v.HINGE_Z])]),
              ("Brake strap + felt (printed)", "hinged under the hub, on the clevis's rib; the felt on the hub",
               [np.array([(v.STRAP_R0 + 4) * np.cos(a), 0, (v.STRAP_R0 + 4) * np.sin(a)])]),
              ("Friction knob (printed)", "the MkII knob, in its seat; the pocket in its underside takes an optional "
               "10 mm spring", [np.array(v.on_bolt(4.0, -9.0).toTuple())])],
             (0, -1, 0), "MkIII base Rev 4 screws: the brake, in section on the tube's plane", "rev4_screws_brake.png",
             focus=((-15, 0, -50), (70, 0, 72)), zoom=1.0, parallel=True)
    labelled(P0, [("M3 x 12 countersunk  (x4)", "sensor cover: into M3 threads tapped through the pillow block and the "
                   "shell's side wall", covers(-1)),
                  ("M4 x 16 countersunk  (x2)", "strut collar: the strut's eye and the clamp screw in front of it, into "
                   "nuts in the +y cheek", heads_of("eye screw") + heads_of("clamp screw")),
                  ("M4 x 35 socket head cap", "tube lock: across the lever and the tube, head in the -y boss",
                   heads_of("tube lock screw")),
                  ("M4 nut", "the brake strap's hinge pin: in the pillow block's hex pocket", heads_of("hinge nut")),
                  ("#10 x 1-1/2 in wood screw  (x4)", "desk mounting: not in the kits", desk)],
             (-0.3, -1.0, 0.4), "MkIII base Rev 4 screws: sensor (-y) side", "rev4_screws_sensorside.png",
             focus=((-150, -50, -58), (100, 50, 40)), zoom=1.05)
    labelled(P0, [("M3 x 12 countersunk  (x4)", "cable cover: into M3 threads tapped through the pillow block and the "
                   "shell's side wall", covers(1)),
                  ("M4 nut  (x2)", "strut collar: in the +y cheek's hex pockets", heads_of("eye nut") + heads_of("clamp nut")),
                  ("M4 nut", "tube lock: in the +y boss's hex pocket", heads_of("tube lock nut")),
                  ("Hex-key hole (3.5 mm)", "through the pillow block, on the strut anchor's M4 x 16: a 2.5 mm key reaches "
                   "its head", [np.array([v.ANCH_X, v.BLOCK_Y1, v.ANCH_Z])]),
                  ("M4 x 50 socket head cap", "the brake strap's hinge pin, its head in a counterbore in the pillow "
                   "block", heads_of("hinge screw"))],
             (0.3, 1.0, -0.12), "MkIII base Rev 4 screws: USB (+y) side", "rev4_screws_usbside.png",
             focus=((-150, -50, -58), (100, 50, 40)), zoom=1.05)
    labelled(R.cut(P0, 1, 12.0, keep="below"),
             [("M4 x 16 countersunk", "strut, base end (cylinder): head on +y", heads_of("anchor screw")),
              ("M4 nut", "strut, base end (cylinder): in the -y cheek's pocket", heads_of("anchor nut"))],
             (0.15, 1.0, 0.35), "MkIII base Rev 4 screws: the strut's anchor (cut away at y = +12)",
             "rev4_screws_strut.png", focus=((-60, 12, -58), (30, 12, -5)), zoom=0.8)


# ---------------------------------------------------------------------------------------------------- exploded views
def dowels():
    """the four dowels where they sit, centred on the joint, one shape each"""
    dw = v.lever_dowel().rotate((0, 0, 0), (1, 0, 0), -90).translate(v.V(0, -v.DOWEL_L / 2, 0))
    return [dw.translate(v.V(x, 0, z)) for x, z, _ in v.JOINT_SCREWS]


def lever_exploded(C):
    """the lever's halves parted along the pivot axis: the dowels in the cable half's joint face, the screws out past
    their heads' half and the nuts out past theirs"""
    ls, lc = v.lever_halves(0.0)
    G = 26.0
    I = {"lever_sensor": d.Item("lever_sensor", to_mesh(ls), C["lever_sensor"]),
         "lever_cable": d.Item("lever_cable", to_mesh(lc), C["lever_cable"])}
    I["lever_sensor"].move = np.array([0, -G, 0])
    I["lever_cable"].move = np.array([0, G, 0])
    I["lever_sensor"].head = np.array([-12.0, -15.0, 27.4])             # on the hub's top
    I["lever_cable"].head = np.array([-30.0, 0.0, 21.0])                # on its joint face
    for k, dw in enumerate(dowels()):
        I[f"dowel{k}"] = d.Item("lever_dowel", to_mesh(dw), C["lever_dowel"])
        I[f"dowel{k}"].move = np.array([0, G - v.DOWEL_L / 2 + 0.2, 0])   # pushed into the cable half's holes
    S = []
    for g, shp, o in screws_and_nuts():
        if g.startswith("lever"):
            it = d.screw(g, to_mesh(shp), d.RED, g, out=o)
            s = 1 if it.out[1] > 0 else -1
            it.move = np.array([0, s * G, 0]) + it.out * (26 if g.startswith("lever screw") else 14)
            S.append(it)
    pick = lambda g, s: [it for it in S if it.name.startswith(g) and it.out[1] * s > 0]
    groups = [("Lever, sensor half (-y)", "prints on its joint face, its trunnion up: one round piece; the AS5600's "
               "pocket in its end", [I["lever_sensor"]]),
              ("Lever, cable half (+y)", "the same, mirrored", [I["lever_cable"]]),
              ("Hollow dowels  (x4, printed)", f"{v.DOWEL_OD} x {v.DOWEL_ID} x {v.DOWEL_L:.0f} mm, standing up. Push them "
               "into one half's holes, round the screws, then close the other half on them",
               [I["dowel0"], I["dowel2"]]),
              (f"M4 x {v.JS_SCREW_L} socket head cap  (x2)", "from the sensor half's end, front-top and back-bottom, "
               "into nuts in the cable half (HELIFOUNER kit)", pick("lever screw", -1)),
              (f"M4 x {v.JS_SCREW_L} socket head cap  (x2)", "from the cable half's end, front-bottom and back-top, "
               "into nuts in the sensor half", pick("lever screw", 1)),
              ("M4 nut  (x2)", "in hex pockets in the sensor half's end face", pick("lever nut", -1)),
              ("M4 nut  (x2)", "in hex pockets in the cable half's end face", pick("lever nut", 1))]
    d.labelled(list(I.values()) + S, groups, (-0.65, -0.75, 0.55), (0, 0, 1), "MkIII base Rev 4 lever, exploded",
               "Split on the tube's plane. Close the halves on the dowels, fit the screws, then press the bearings on",
               os.path.join(OUT, "rev4_lever_exploded.png"), size=(1700, 1300), crop=True, html=True)


def exploded(C):
    P = v.build(0.0)
    I = {}
    for n in ("frame", "shell", "lever_sensor", "lever_cable", "strap", "felt", "friction_knob", "cover_sensor",
              "cover_cable", "magnet", "sensor_pcb", "sensor_chip", "gas_strut", "strut_collar", "hose_clamp"):
        I[n] = d.Item(n, to_mesh(P[n]), C[n])
    for s in (-1, 1):
        for k, n in enumerate(("bearing_outer", "bearing_inner", "bearing_seal")):
            I[f"{n}{s}"] = d.Item(n, to_mesh(v.bearing(s)[k]), C[n])
        I[f"bearing_outer{s}"].head = np.array([-17.0, s * (v.BRG_Y0 + v.BRG_Y1) / 2, -17.0])  # on the ring's front
    I["tube"] = d.Item("tube", to_mesh(v.carbon_tube(130.0)), C["carbon_tube"])
    for k, dw in enumerate(dowels()):
        I[f"dowel{k}"] = d.Item("lever_dowel", to_mesh(dw), C["lever_dowel"])
    S = {}
    for g, shp, o in screws_and_nuts():
        S.setdefault(g, []).append(d.screw(g, to_mesh(shp), d.RED, g, out=o))

    def mv(keys, at):
        for k in keys:
            I[k].move = np.asarray(at, float)

    def pull(group, at, dist, pick=lambda it: True):
        for it in S[group]:
            if pick(it):
                it.move = np.asarray(at, float) + it.out * dist

    L = np.array([0, 0, 115.0])                                        # the lever, lifted out of the frame
    G = 38.0                                                           # its halves, parted along the pivot axis
    mv(["lever_sensor"], L + (0, -G, 0))
    mv(["lever_cable"], L + (0, G, 0))
    mv([f"dowel{k}" for k in range(4)], L)
    for s in (-1, 1):                                                  # screws out past their heads' half, nuts past theirs
        pull(f"lever screw {v.JS_SCREW_L}", L + (0, s * G, 0), 30, lambda it, s=s: it.out[1] * s > 0)
        pull("lever nut", L + (0, s * G, 0), 16, lambda it, s=s: it.out[1] * s > 0)
        mv([f"bearing_outer{s}", f"bearing_inner{s}", f"bearing_seal{s}"], L + (0, 85 * s, 0))
    mv(["sensor_pcb", "sensor_chip"], L + (0, -125, 0))
    pull("sensor screw", L + (0, -125, 0), 14)
    pull("tube lock screw", L + (0, -G, 0), 30)
    pull("tube lock nut", L + (0, G, 0), 16)
    mv(["tube"], L + (-95, 0, 0))
    mv(["hose_clamp"], L + (-30, 0, 0))
    mv(["strut_collar"], L + (-95, 0, 0))
    for g in ("clamp screw", "clamp nut"):
        pull(g, L + (-95, 0, 0), 22)
    for g in ("eye screw", "eye nut"):
        pull(g, L + (-95, 0, 0), 25)
    for g in ("anchor screw", "anchor nut"):
        pull(g, (0, 0, 0), 32)
    T = np.array([0, 0, 250.0])                                        # the shell, above the lever
    mv(["shell"], T)
    pull("shell screw", T, 45)
    pull("shell nut", (0, 0, 0), 30)
    mv(["cover_sensor", "magnet"], (0, -130, 30))
    mv(["cover_cable"], (0, 130, 30))
    pull("cover screw", (0, -130, 30), 30, lambda it: it.head[1] < 0)
    pull("cover screw", (0, 130, 30), 30, lambda it: it.head[1] > 0)
    B = np.array([100.0, 0, 10.0])                                     # the strap, back out of its bay
    mv(["strap", "felt"], B)
    pull("brake nut", B, 22)
    pull("hinge screw", (0, 0, 0), 48)
    pull("hinge nut", (0, 0, 0), 30)
    u = np.array(v.bolt_axis()[0].toTuple())
    K = T + u * 45                                                     # the knob, up its bolt's axis off the shell
    mv(["friction_knob"], K)
    pull("brake bolt", K, 40)

    parts = [("Frame", "pillow blocks, anchor clevis, up-stop pad, down-stop pillars, the brake strap's bay",
              ["frame"]),
             ("Shell", "the bearing caps, the knob's seat and the brake strap's bay in one", ["shell"]),
             ("Lever, sensor half", "split on the tube's plane; each half prints on its joint face, trunnion up",
              ["lever_sensor"]),
             ("Lever, cable half", "the cables lie in the halves' channels", ["lever_cable"]),
             ("Hollow dowels  (x4, printed)", "round the lever's screws, half in each half: they locate the halves",
              ["dowel0", "dowel2"]),
             ("6808-2RS bearings  (x2)", "pressed onto the trunnions", ["bearing_outer-1", "bearing_outer1"]),
             ("AS5600 board", "in the sensor trunnion's end, chip out", ["sensor_pcb"]),
             ("Sensor cover", "with the magnet in a pocket in its inside face", ["cover_sensor"]),
             ("Cable cover", "goes on over the USB cable", ["cover_cable"]),
             ("Brake strap + felt", "on its hinge pin before the lever goes in; its nut drops into the head's slot",
              ["strap"]),
             ("Friction knob", "the MkII knob: an M5 hex pocket, and a pocket underneath for an optional spring",
              ["friction_knob"]),
             ("Gas strut", "X AUTOHAUX 6 in, 45 N", ["gas_strut"]),
             ("Strut collar", "clamped on the tube", ["strut_collar"]),
             ("Hose clamp", "on the socket's mouth", ["hose_clamp"]),
             ("Carbon tube", "25 x 23 mm, 500 mm (shortened here)", ["tube"])]
    screws = [(f"M4 x {v.JS_SCREW_L} + M4 nut  (x4)", "lever halves: socket head, along the pivot axis behind the "
               "bearings; two heads and two nuts in each half", S[f"lever screw {v.JS_SCREW_L}"] + S["lever nut"]),
              ("M4 x 50 + M4 nut  (x4)", "the shell: socket head, into nuts slid into the pillow blocks' sides",
               S["shell screw"] + S["shell nut"]),
              ("M3 x 12  (x8)", "side covers, countersunk", S["cover screw"]),
              ("M5 x 35 + M5 nut", "the brake: a hex bolt, head in the knob, nut in the strap's head",
               S["brake bolt"] + S["brake nut"]),
              ("M4 x 50 + M4 nut", "the brake strap's hinge pin, socket head", S["hinge screw"] + S["hinge nut"]),
              ("M4 x 16 + M4 nut  (x3)", "strut eyes (2) and the collar's front clamp screw (1), countersunk",
               S["anchor screw"] + S["anchor nut"] + S["eye screw"] + S["eye nut"] + S["clamp screw"] + S["clamp nut"]),
              ("M4 x 35 + M4 nut", "tube lock: socket head, across the lever and the tube", S["tube lock screw"]
               + S["tube lock nut"]),
              ("M2 x 8  (x4)", "the AS5600 board, countersunk, into the pocket's posts", S["sensor screw"])]
    groups = [(t, s_, [I[k] for k in ks]) for t, s_, ks in parts] + screws
    everything = list(I.values()) + [it for g in S.values() for it in g]
    d.labelled(everything, groups, (-0.55, -1.0, 0.75), (0, 0, 1), "MkIII base Rev 4, exploded",
               "Printed parts in their colours, screws and nuts in red. The tube is cut short.",
               os.path.join(OUT, "rev4_exploded.png"), size=(2200, 2000), crop=True, html=True)


def screw_chart():
    rows = [(d.screw_tile("shcs", 4, v.JS_SCREW_L), f"M4 x {v.JS_SCREW_L} socket head cap", 5,
             "The lever halves (4): along the pivot axis through the hub, behind the bearings, into M4 nuts in the "
             "other half (HELIFOUNER M4 x 30-50 kit). The tube lock (1): across the lever and the tube."),
            (d.screw_tile("shcs", 4, 50), "M4 x 50 socket head cap", 5,
             "The shell (4), from the top, each centred on the joint, into M4 nuts slid into the pillow blocks from "
             "the sides; the brake strap's hinge pin (1), through the pillow blocks and the up-stop pad."),
            (d.screw_tile("hex", 5, 35), "M5 x 35 hex bolt", 1,
             "The brake: head in the knob's hex pocket, down through the knob's seat into the M5 nut in the strap's "
             "head."),
            (d.screw_tile("csk", 3, 12), "M3 x 12 countersunk", 8,
             "The side covers, into threads tapped through the blocks and the shell."),
            (d.screw_tile("csk", 4, 16), "M4 x 16 countersunk", 3,
             "The strut's two eyes, and the collar's front clamp screw, into nuts in the far cheeks."),
            (d.screw_tile("csk", 2, 8), "M2 x 8 countersunk", 4,
             "The AS5600 board, into 1.6 mm pilots in the sensor pocket's posts."),
            (d.nut_tile(7.0, 3.2, 4.0), "M4 nut", 13,
             "Lever (4), tube lock (1), shell (4), strut eyes (2), collar clamp (1), the strap's hinge pin (1)."),
            (d.nut_tile(8.0, 4.0, 5.0), "M5 nut", 1, "In the slot in the brake strap's head.")]
    d.chart(rows, "MkIII base Rev 4: every screw, to scale",
            "Countersunk screws and nuts: AvrestYPT kit. Socket head screws (lever, shell, hinge pin): HELIFOUNER kit. Brake bolt: M5 x 35. "
            "Not shown: four #10 wood screws for the desk.", os.path.join(OUT, "rev4_screw_sizes.png"))


# ---------------------------------------------------------------------------------------------------- the collective
HEAD = os.path.join(os.path.dirname(HERE), "Head")
HEAD_STL = os.path.join(HEAD, "stl")
# the head's parts that come from its own files: (node, file in ../Head/stl, colour). The head's STLs are in its frame
# (x across its face, y into it, z up the tube), so head_to_base() turns them onto this base's tube
HEAD_PARTS = [
    ("Body", "HueyHeadR5-Body.stl", (43, 47, 52)),
    ("Upper panel", "HueyHeadR5-UpperPanel-Black.stl", (35, 38, 41)),
    ("Upper panel text", "HueyHeadR5-UpperPanel-WhiteText.stl", (242, 242, 242)),
    ("Lower panel", "HueyHeadR5-LowerPanel-Black.stl", (35, 38, 41)),
    ("Lower panel text", "HueyHeadR5-LowerPanel-WhiteText.stl", (242, 242, 242)),
    ("Throttle grip", "HueyHeadR5-ThrottleGrip.stl", (74, 79, 87)),
    ("Trigger", "HueyHeadR5-Trigger.stl", (75, 81, 88)),
    ("Friction collar", "HueyHeadR5-FrictionCollar.stl", (192, 57, 43)),
    ("Pinion", "HueyHeadR5-Pinion.stl", (76, 175, 80)),
    ("Magnet shaft", "HueyHeadR5-MagnetShaft.stl", (232, 118, 44)),
    ("Magnet", "ref/magnet.stl", (154, 163, 173)),
    ("AS5600 chip", "ref/chip.stl", (17, 17, 17)),
    ("AS5600 module", "ref/module.stl", (91, 47, 145)),
    ("Tube set screw M5 x 8", "ref/m5_grub.stl", (141, 148, 156)),
]
# the search hat, from the head's hat script (through make_diagrams.hat_meshes(), in the same frame): (node, its key, colour)
HAT_PARTS = [("Search hat cap", "cap", (43, 47, 52)), ("SearchHat board", "board", (31, 111, 67)),
             ("Hat stick switch", "switch", (17, 17, 17)), ("Hat board screws M2 x 8", "screws", (141, 148, 156))]
# head parts in the collective's GLB that the head no longer has (hat 1)
HEAD_GONE = ("4-way hat: bezel, rocker plate, set screw", "Hat tact switches")


def head_to_base():
    """4 x 4 transform from the head's frame onto this base's tube: the head's tube (../Head/stl/ref/tube.stl) on this
    base's, its top end at the far end of the whole 500 mm tube"""
    t = trimesh.load(os.path.join(HEAD_STL, "ref", "tube.stl"), force="mesh")
    (tx0, ty0, _), (tx1, ty1, tz1) = t.bounds
    full = -m.SOCK_BOTTOM - v.r.TUBE_BOUGHT                                     # the tube's far end, base x
    # base (X, Y, Z) = (full - (z - tz1), x - tx, ty - y)
    return np.array([[0, 0, -1, full + tz1], [1, 0, 0, -(tx0 + tx1) / 2], [0, -1, 0, (ty0 + ty1) / 2], [0, 0, 0, 1.0]])


def head_parts():
    """{"H:name": (mesh, colour)}: the head on this base at 0 deg. Its printed parts and the sensor bits from ../Head/stl,
    the search hat from its script; the rest (the HeliSR board, switches, screws, wires: the head has no files for
    them) carried over from the collective's GLB, where they already sit on this base's tube"""
    T = head_to_base()
    H = {}
    for name, f, col in HEAD_PARTS:
        H["H:" + name] = (trimesh.load(os.path.join(HEAD_STL, f), force="mesh").apply_transform(T), col)
    hat = d.hat_meshes()
    for name, k, col in HAT_PARTS:
        H["H:" + name] = (hat[k].apply_transform(T), col)
    src = R.load_glb(R.ALL_GLB)
    ty = float(src["carbon_tube"][0].bounds.mean(0)[1])                         # the GLB's tube, if it's off the middle
    skip = set(H) | {"H:" + n for n in HEAD_GONE}
    for k, (msh, col) in src.items():
        if k.startswith("H:") and k not in skip:
            H[k] = (msh.copy().apply_translation((0, -ty, 0)), col)
    return H


def collective(C):
    """the head on base Rev 4: the collective's GLB and pictures in ../renders"""
    head = head_parts()
    glb({**scene(0.0, C), **head}, R.ALL_GLB)
    full = -m.SOCK_BOTTOM - v.r.TUBE_BOUGHT
    for th, name, view, size in ((0.0, "HeliCollective_0deg.png", (-0.35, -1.0, 0.45), (1800, 1100)),
                                 (v.STOP_DEG, "HeliCollective_32deg.png", (-0.35, -1.0, 0.45), (1800, 1100)),
                                 (0.0, "HeliCollective_side.png", (0, -1.0, 0.12), (1800, 900))):
        rot = trimesh.transformations.rotation_matrix(np.radians(th), (0, 1, 0))
        Hh = {k: (msh.copy().apply_transform(rot), col) for k, (msh, col) in head.items()}
        img = R.render({**scene(th, C, tube_to=full), **Hh}, view, size=size, zoom=1.05)[0]
        R.save(img, name, R.TOP_OUT)


if __name__ == "__main__":
    if sys.argv[1:] == ["exploded"]:                  # only the two exploded views and their pages
        os.makedirs(OUT, exist_ok=True)
        lever_exploded(colours())
        exploded(colours())
    else:
        main()
