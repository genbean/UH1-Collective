"""
MkIII base Rev 3: the assembly GLBs and the renders, from the STLs that mk3_rev3.py writes.

    python mk3_rev3.py           (first: stl/, stl/ref/, step/)
    python make_renders_r3.py    (needs cadquery for the strut at 32 deg, numpy, trimesh, manifold3d, pyvista, pillow)

1. Rebuilds renders/MkIII_Rev3_Assembly.glb and ../renders/HeliCollective_Assembly.glb: every base part's mesh is
   replaced by its STL (the parts keep their GLB colours; the head's "H:" parts are left as they are).
2. Draws renders/rev3_*.png (all but rev3_lever_lower, rev3_lever_socket and rev3_screws_levernuts, which show only
   the lever, and rev3_exploded / rev3_screw_sizes, which ../renders/make_diagrams.py draws from the collective GLB)
   and ../renders/HeliCollective_0deg.png, _32deg.png and _side.png.
Run ../renders/make_diagrams.py after it for the exploded views and screw charts.

At an angle the lever, tube, hose clamp, lever screws, sensor carrier and board, the head and the cable inside the lever
turn about the pivot (y axis); the collar, strut and pins are rebuilt by mk3_rev3 at that angle. Sections are cut as
solids, so their cut faces are closed.
"""
import os
import sys
import numpy as np
import trimesh
import manifold3d as mf
import pyvista as pv
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "renders"))
import mk3_rev3 as r                                    # noqa: E402  (cadquery)
import make_diagrams as d                               # noqa: E402  (callout layout, fonts)

m = r.m
OUT = os.path.join(HERE, "renders")
TOP_OUT = os.path.join(ROOT, "renders")
BASE_GLB = os.path.join(OUT, "MkIII_Rev3_Assembly.glb")
ALL_GLB = os.path.join(TOP_OUT, "HeliCollective_Assembly.glb")
RED, PURPLE, EDGE = (214, 48, 39), (150, 92, 190), (30, 30, 34)
HW = ("hardware", "lever_screws", "strut_pins")
TURNS = ("lever_upper", "lever_lower", "lever_screws", "carbon_tube", "hose_clamp", "sensor_carrier", "sensor_pcb",
         "sensor_chip", "bearing_inner", "sensor_wires")
FULL = -m.SOCK_BOTTOM - r.TUBE_BOUGHT                  # the whole 500 mm tube's far end (x = -502.7; the head's top end)
SUB = ("Screws in red. Countersunk screws and nuts: AvrestYPT kit (the lever halves: HELIFOUNER M4 x 30-50 socket head "
       "cap kit and its nuts) (the covers' M3 x 25: the NIULUNBAO M3 set). Set screw: set-screw kit.")


def stl_path(name):
    p = os.path.join(HERE, "stl", name + ".stl")
    return p if os.path.exists(p) else os.path.join(HERE, "stl", "ref", name + ".stl")


# ---------------------------------------------------------------------------------------------------- GLBs
def rebuild_glb(path):
    sc = trimesh.load(path)
    n = 0
    for name, g in list(sc.geometry.items()):
        if name.startswith("H:"):
            continue
        t = trimesh.load(stl_path(name), force="mesh")
        t.visual = trimesh.visual.TextureVisuals(material=g.visual.material)
        sc.geometry[name] = t
        n += 1
    sc.export(path)
    print(f"rebuilt {os.path.relpath(path, ROOT)}: {n} base parts from the STLs")


def load_glb(path):
    sc = trimesh.load(path)
    out = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        mm = sc.geometry[g].copy()
        mm.apply_transform(T)
        out[node] = (trimesh.Trimesh(mm.vertices, mm.faces, process=False),
                     tuple(int(c) for c in mm.visual.material.baseColorFactor[:3]))
    return out


# ---------------------------------------------------------------------------------------------------- poses
def cq_mesh(shape):
    v, f = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True)


def rot(mesh, th):
    return mesh.copy().apply_transform(trimesh.transformations.rotation_matrix(np.radians(th), (0, 1, 0)))


def tube_mesh(x_end):
    """the 25 x 23 carbon tube from the socket bottom (x = -2.7) out to x_end"""
    x0 = -m.SOCK_BOTTOM
    t = trimesh.creation.annulus(r_min=m.TUBE_OD / 2 - 1.0, r_max=m.TUBE_OD / 2, height=x0 - x_end, sections=96)
    t.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    return t.apply_translation(((x0 + x_end) / 2, r.Y0, 0))


def pose(src, th=0.0, tube_to=None):
    """{name: (mesh, colour)} at lever angle th. tube_to: replace the GLB's 160 mm tube with one out to that x"""
    P = {}
    for name, (mesh, col) in src.items():
        if name in TURNS or name.startswith("H:"):
            mesh = rot(mesh, th) if th else mesh
        elif name == "usb_cable" and th:                 # inside the lever it turns; out past the block it stays put
            v = mesh.vertices.copy()
            inside = v[:, 1] < m.BLOCK_Y1
            R = trimesh.transformations.rotation_matrix(np.radians(th), (0, 1, 0))[:3, :3]
            v[inside] = v[inside] @ R.T
            mesh = trimesh.Trimesh(v, mesh.faces, process=False)
        P[name] = (mesh, col)
    if th:
        for name, f in (("strut_collar", r.collar), ("gas_strut", r.strut), ("strut_pins", r.pins)):
            P[name] = (cq_mesh(f(th)), P[name][1])
    if tube_to is not None:
        P["carbon_tube"] = (rot(tube_mesh(tube_to), th), P["carbon_tube"][1])
    return P


def screw_colours(P):
    for n in HW:
        if n in P:
            P[n] = (P[n][0], RED)
    P["shoe"] = (P["shoe"][0], PURPLE)
    return P


def no_cover_screws(P):
    """drop the side covers' M3 screws from the hardware, for views with the covers hidden"""
    hw, col = P["hardware"]
    keep = [q for q in hw.split(only_watertight=False) if abs(q.centroid[1]) < m.BLOCK_Y1]
    return {**P, "hardware": (trimesh.util.concatenate(keep), col)}


def hide(P, *names):
    return {k: v for k, v in P.items() if k not in names}


def base_only(P):
    return {k: v for k, v in P.items() if not k.startswith("H:")}


# ---------------------------------------------------------------------------------------------------- cutting
def to_man(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def from_man(mm):
    me = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)


def cut(P, axis, value, keep="above"):
    """keep each part's material on one side of the plane axis = value, as closed solids"""
    lo, hi = [-2000.0] * 3, [2000.0] * 3
    (lo if keep == "above" else hi)[axis] = value
    box = mf.Manifold.cube(tuple(h - l for l, h in zip(lo, hi))).translate(tuple(lo))
    out = {}
    for k, (mesh, col) in P.items():
        if (mesh.bounds[0][axis] >= value) if keep == "above" else (mesh.bounds[1][axis] <= value):
            out[k] = (mesh, col)
            continue
        mm = to_man(mesh)
        if mm.status() != mf.Error.NoError:
            pd = d.to_pv(mesh).clip(normal=[1 if i == axis else 0 for i in range(3)], origin=[value] * 3,
                                    invert=keep != "above")
            out[k] = (pd, col)
            continue
        c = mm ^ box
        if c.volume() > 0:
            out[k] = (from_man(c), col)
    return out


# ---------------------------------------------------------------------------------------------------- drawing
def as_pv(mesh):
    return mesh if isinstance(mesh, pv.DataSet) else d.to_pv(mesh)


def render(P, view, up=(0, 0, 1), size=(1600, 1100), focus=None, zoom=1.0, parallel=False, anchors=()):
    """P: {name: (mesh, colour)}. view: direction from the scene to the camera. focus: (lo, hi) to frame, else all.
    Returns the image and the anchors' pixel positions."""
    p = pv.Plotter(off_screen=True, window_size=size, lighting="light kit")
    p.set_background(d.BG_BOT, top=d.BG_TOP)
    for name, (mesh, col) in P.items():
        p.add_mesh(as_pv(mesh), color=col, smooth_shading=True, split_sharp_edges=True, feature_angle=35,
                   ambient=0.22, diffuse=0.8, specular=0.25 if name in HW else 0.12, specular_power=18,
                   silhouette=dict(color=EDGE, line_width=2.0, feature_angle=40))
    if focus is None:
        b = np.vstack([np.asarray(as_pv(mesh).bounds).reshape(3, 2).T for mesh, _ in P.values()])
        lo, hi = b.min(0), b.max(0)
    else:
        lo, hi = np.asarray(focus[0], float), np.asarray(focus[1], float)
    ctr = (lo + hi) / 2
    v = np.asarray(view, float) / np.linalg.norm(view)
    u = np.asarray(up, float) - v * (np.asarray(up, float) @ v)
    u /= np.linalg.norm(u)
    rt = np.cross(-v, u)                                   # the focus box's corners on screen: fit it, centred
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) - ctr
    half_w, half_h = np.abs(corners @ rt).max(), np.abs(corners @ u).max()
    aspect = size[0] / size[1]
    half = max(half_h, half_w / aspect) * 1.08 / zoom
    va = 30.0
    dist = 1500.0 if parallel else half / np.tan(np.radians(va / 2)) + np.abs(corners @ v).max()
    p.camera.focal_point = tuple(ctr)
    p.camera.position = tuple(ctr + v * dist)
    p.camera.up = tuple(u)
    if parallel:
        p.enable_parallel_projection()
        p.camera.parallel_scale = half
    else:
        p.camera.view_angle = va
    p.reset_camera_clipping_range()
    p.enable_anti_aliasing("ssaa")
    img = Image.fromarray(p.screenshot(return_img=True))
    ren = p.renderer
    px = []
    for a in anchors:
        ren.SetWorldPoint(*a, 1.0)
        ren.WorldToDisplay()
        x, y, _ = ren.GetDisplayPoint()
        px.append((x, size[1] - y))
    p.close()
    return img, px


def save(img, name, folder=OUT):
    path = os.path.join(folder, name)
    img.save(path, optimize=True)
    print("wrote", os.path.relpath(path, ROOT))


def labelled(P, groups, view, title, out, **kw):
    """groups: [(title, text, [anchor point, ...])]"""
    anchors, labels = [], []
    for t, s, pts in groups:
        labels.append((t, s, list(range(len(anchors), len(anchors) + len(pts)))))
        anchors += [tuple(map(float, q)) for q in pts]
    img, px = render(P, view, anchors=anchors, size=kw.pop("size", (1500, 1100)), **kw)
    d.compose(img, px, labels, title, SUB, os.path.join(OUT, out))


# ---------------------------------------------------------------------------------------------------- anchor points
def heads(mesh, pick, toward):
    """the head end (the extreme vertex along `toward`) of each connected piece whose centroid passes pick(c)"""
    out = []
    for q in mesh.split(only_watertight=False):
        if pick(q.centroid):
            out.append(q.vertices[np.argmax(q.vertices @ np.asarray(toward, float))])
    return sorted(out, key=lambda v: tuple(np.round(v, 1)))


def cover_heads(side):
    """the four M3 cover screws' heads on one side"""
    return [np.array([px, side * (m.BLOCK_Y1 + m.COVER_D), pz]) for px, pz in
            (m.on_circle(m.COVER_HOLE_R, a) for a in (45, 135, 225, 315))]


# ---------------------------------------------------------------------------------------------------- views
def base_views(src):
    near = -200.0                                         # the tube, cut past the collar and the cable's end in it
    P0 = base_only(pose(src, 0.0, tube_to=near))
    P32 = base_only(pose(src, r.STOP_DEG, tube_to=near))

    # plain views
    save(render(P0, (-0.45, -0.85, 0.38), size=(1500, 1000), zoom=0.85)[0], "rev3_hero.png")
    Pf = base_only(pose(src, 0.0, tube_to=-260.0))
    save(render(Pf, (-0.58, -0.72, 0.48), size=(1600, 1100), focus=((-150, -60, -58), (55, 60, 40)), zoom=1.15)[0],
         "rev3_base_front.png")
    save(render(Pf, (0.72, 0.72, 0.5), size=(1600, 1100), focus=((-150, -60, -58), (55, 60, 40)), zoom=1.15)[0],
         "rev3_base_rear.png")
    Pl = base_only(pose(src, 0.0, tube_to=FULL))
    save(render(Pl, (-0.25, -1.0, 0.28), size=(1600, 900), zoom=0.95)[0], "rev3_full.png")

    # sections through the strut's plane (y = SOCK_Y), from the sensor side
    for P, name, top in ((P0, "rev3_section.png", 45), (P32, "rev3_section32.png", 120)):
        save(render(cut(hide(P, "usb_cable", "sensor_wires"), 1, r.Y0), (0, -1, 0), size=(1600, 900), parallel=True,
                    zoom=1.0, focus=((-200, r.Y0, -60), (60, r.Y0, top)))[0], name)

    # the anchor clevis, the sensor side cut away just outside its cheek
    cheek = r.Y0 - (r.ROD_TAB_T + 0.6) / 2 - r.CLEVIS_T
    save(render(cut(P0, 1, cheek - 0.5), (-0.35, -1.0, 0.32), size=(1400, 1000),
                focus=((-45, cheek, -58), (25, cheek, -10)), zoom=0.65)[0], "rev3_anchor.png")

    # the hinge lugs and their gussets, from behind
    save(render(no_cover_screws(hide(P0, "cover_cable", "cable_plug", "usb_cable")), (0.9, 0.5, 0.8), size=(1400, 1000),
                focus=((15, 0, -58), (60, 52, 10)), zoom=1.0)[0], "rev3_lug_gusset.png")

    # the up-stop at 32 deg: cut through the stop boss, and from behind
    save(render(cut(hide(P32, "usb_cable", "sensor_wires"), 1, -5.0), (0, -1, 0), size=(1400, 950), parallel=True,
                focus=((-25, -5, -58), (62, -5, 40)), zoom=0.9)[0], "rev3_upstop.png")
    save(render(hide(P32, "cover_sensor", "cover_cable", "cable_plug", "magnet", "usb_cable", "hardware"), (1, 0.0, 0.3),
                size=(1400, 950), focus=((0, -52, -58), (40, 52, 40)), zoom=0.95)[0], "rev3_upstop_rear.png")

    # the down-stops and the frame from above
    save(render(Pf, (-0.62, -0.62, 0.45), size=(1600, 1200), focus=((-62, -50, -58), (-20, 20, 0)), zoom=0.8)[0],
         "rev3_downstop.png")
    fr = {"frame": P0["frame"]}
    save(render(fr, (0, 0, 1), up=(1, 0, 0), size=(1400, 1200), parallel=True, zoom=0.95)[0], "rev3_frame_plan.png")


def screw_views(src):
    P = screw_colours(base_only(pose(src, 0.0, tube_to=-175.0)))
    hw, ls, pins = P["hardware"][0], P["lever_screws"][0], P["strut_pins"][0]
    xm = -r.COLLAR_D + (r.COLLAR_W - 2 * r.COLLAR_BACK) / 2
    collar_heads = heads(pins, lambda c: c[0] < xm + 15 and c[0] > xm - 15 and c[2] > 5, (0, -1, 0))
    collar_nuts = heads(pins, lambda c: c[0] < xm + 15 and c[0] > xm - 15 and c[2] > 5, (0, 1, 0))
    eye = heads(pins, lambda c: abs(c[0] + r.COLLAR_D) < 6 and c[2] < 0, (0, 1, 0))
    eye_nut = heads(pins, lambda c: abs(c[0] + r.COLLAR_D) < 6 and c[2] < 0, (0, -1, 0))
    anch = np.array([r.ANCH_X, r.Y0 + (r.ROD_TAB_T + 0.6) / 2 + r.CLEVIS_T, r.ANCH_Z])
    caps = [np.array([x, s * (m.BRG_Y0 + m.BLOCK_Y1) / 2, 8.0]) for s in (-1, 1) for x in (-m.CAP_BOLT_X, m.CAP_BOLT_X)]
    knob = np.array([m.KNOB_X, m.KNOB_Y, m.KNOB_HEAD_Z])
    lever = heads(ls, lambda c: True, (0, 0, 1))
    hinge_head = np.array([m.HINGE_X, 12.0, m.HINGE_Z])
    hinge_nut = np.array([m.HINGE_X, 32.0, m.HINGE_Z])
    nut5 = np.array([-54.0, m.KNOB_Y, m.FN_NUT_Z - m.NUT_T[5] / 2])
    cap_nuts = [np.array([-m.BLOCK_HW, s * (m.BRG_Y0 + m.BLOCK_Y1) / 2, r.CAP_NUT_Z - 1.7]) for s in (-1, 1)]
    desk = [np.array([x, y, r.Z_PLATE]) for x in (m.PLATE_X0 + 8, m.PLATE_X1 - 8) for y in (-m.PLATE_HW + 8, m.PLATE_HW - 8)]
    x, zh = r.PLUG_SCREW
    plug = np.array([x, m.BLOCK_Y1 + 7, zh])

    labelled(P, [("M4 socket head cap  (x4)", "lever halves, from the top: x 40; M4 nuts in the lower half", lever),
                 ("M4 x 20 countersunk  (x4)", "pillow-block caps, from the top; each into an M4 nut slid into a slot in "
                  "the block's front or back face", caps),
                 ("M5 x 30 hex bolt (bought)", "friction knob: its head sits in the knob's hex pocket, on its floor; ends in the "
                  "M5 nut", [knob]),
                 ("M4 nut  (x2)", "strut collar clamp: +y ear", collar_nuts)],
             (-0.5, 0.55, 1.0), "MkIII base Rev 3 screws: from above", "rev3_screws_top.png",
             focus=((-150, -55, -58), (55, 60, 45)), zoom=1.05)
    labelled(P, [("M3 x 25 countersunk  (x4)", "cable cover: tap the block and cap M3, 11 mm deep", cover_heads(1)),
                 ("M4 nut", "shoe hinge: in the +y lug's pocket", [hinge_nut]),
                 ("M4 x 16 countersunk", "strut, body end: head on +y", eye)],
             (0.6, 1.0, 0.45), "MkIII base Rev 3 screws: knob (+y) side, from behind", "rev3_screws_knobside.png",
             focus=((-150, -50, -58), (55, 62, 40)), zoom=1.05)
    labelled(P, [("M4 x 12 countersunk  (x2)", "strut collar clamp: head 2 mm into the -y ear", collar_heads),
                 ("M4 nut", "strut, body end: in the -y cheek's pocket", eye_nut),
                 ("M4 x 20 countersunk", "shoe hinge: head in the -y lug, nut in the +y lug; snug, thread-lock",
                  [hinge_head]),
                 ("M3 x 25 countersunk  (x4)", "sensor cover: tap the block and cap M3, 11 mm deep", cover_heads(-1)),
                 ("#10 x 1-1/2 in wood screw  (x4)", "desk mounting: not in the kits", desk)],
             (0.3, -1.0, 0.45), "MkIII base Rev 3 screws: sensor (-y) side", "rev3_screws_sensorside.png",
             focus=((-150, -62, -58), (55, 50, 40)), zoom=1.05)
    labelled(hide(P, "carbon_tube", "strut_collar", "hose_clamp", "strut_pins", "usb_cable", "sensor_wires"),
             [("M5 nut", "friction bolt: slides into the knob tower's slot from the front", [nut5]),
              ("M4 nut  (x2)", "front pillow-block caps: slide into the slots in the blocks' front faces", cap_nuts)],
             (-1.0, -0.1, 0.18), "MkIII base Rev 3 screws: from the front, under the socket (tube and collar hidden)",
             "rev3_screws_front.png", focus=((-62, -55, -58), (10, 55, 40)), zoom=1.0)
    labelled(P, [("M2 x 12 countersunk", "cable plug: up from under the cover's rim; tap the plug M2 (1.6 mm pilot)",
                  [plug])],
             (0.3, 1.0, -0.45), "MkIII base Rev 3 screws: the cable plug's screw, under the cable cover's spout",
             "rev3_screws_plug.png", focus=((0, 40, -45), (60, 70, 15)), zoom=0.9)
    cutP = cut(P, 1, 12.0, keep="below")
    labelled(cutP, [("M4 x 16 countersunk + M4 nut", "strut, rod end: head on +y, nut in the -y cheek's pocket", [anch])],
             (0.15, 1.0, 0.35), "MkIII base Rev 3 screws: the strut's anchor (cut away at y = +12)",
             "rev3_screws_strut.png", focus=((-60, 12, -58), (30, 12, -5)), zoom=0.8)


def collective_views(src):
    for th, name, view, size in ((0.0, "HeliCollective_0deg.png", (-0.35, -1.0, 0.45), (1800, 1100)),
                                 (r.STOP_DEG, "HeliCollective_32deg.png", (-0.35, -1.0, 0.45), (1800, 1100)),
                                 (0.0, "HeliCollective_side.png", (0, -1.0, 0.12), (1800, 900))):
        P = pose(src, th, tube_to=FULL)
        save(render(P, view, size=size, zoom=1.05)[0], name, TOP_OUT)


if __name__ == "__main__":
    pv.OFF_SCREEN = True
    rebuild_glb(BASE_GLB)
    rebuild_glb(ALL_GLB)
    src_all = load_glb(ALL_GLB)
    which = set(sys.argv[1:]) or {"base", "screws", "collective"}
    if "base" in which:
        base_views(src_all)
    if "screws" in which:
        screw_views(src_all)
    if "collective" in which:
        collective_views(src_all)
