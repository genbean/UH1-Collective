"""
Exploded views, screw maps and screw-size charts for the MkIII base Rev 3 and the Huey head Rev 5, drawn from
HeliCollective_Assembly.glb in this folder (the complete collective at 0 deg: the base in its own frame, the head's
parts named "H:..."). Every screw group in the GLB is split into its screws, and each screw is pulled out along its own
axis, toward its head, in the exploded views.

    python make_diagrams.py            (needs numpy, trimesh, manifold3d, pyvista and pillow)

writes
    ../Base/renders/rev3_exploded.png, rev3_screw_sizes.png
    ../Head/Rev5/renders/HueyHeadR5_Exploded.png, HueyHeadR5_Exploded_Rear.png, HueyHeadR5_ScrewSizes.png,
    HueyHeadR5_Screws_Panels.png, HueyHeadR5_Screws_Inside.png, HueyHeadR5_Screws_Rear.png, HueyHeadR5_Screws_Collar.png

Re-run it after the GLB is regenerated. Two screws the GLB leaves out are added here: the head's pull-stop seat (M2 x 8,
STOP_SCREW and MOUNT_FACE in huey_head_r5.py) and the hat's pivot set screw (M3 x 4, Hat/hat_r5.py).
"""
import os
import textwrap
import numpy as np
import trimesh
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "HeliCollective_Assembly.glb")
BASE_OUT = os.path.join(HERE, "..", "Base", "renders")
HEAD_OUT = os.path.join(HERE, "..", "Head", "Rev5", "renders")

RED = (198, 40, 40)
INK = (20, 20, 20)
SUB = (70, 70, 70)
FONT = "C:/Windows/Fonts/segoeui.ttf"
FONT_B = "C:/Windows/Fonts/segoeuib.ttf"

# Head Rev 5's frame from the collective's (the base's: pivot at the origin, Y the pivot axis, Z up, the tube along -X):
# the head's x across its face is the base's Y, its y (into the head) is -Z, its z (up the tube) is -X. The tube's axis
# is at the head's (TX, TY) = (5.29, 18.52) and the base's (Y, Z) = (-9, 0); its top end is at head z 55.9.
TO_HEAD = np.array([[0, 1, 0, 5.29 + 9.0], [0, 0, -1, 18.52], [-1, 0, 0, -446.8], [0, 0, 0, 1.0]])
TILT = np.radians(20.0)                 # huey_head_r5.TILT, about x through (y = 0, z = ZB)
ZB = -2.55


def tilt_pt(x, y, z):
    """huey_head_r5's box frame -> head frame, for a point."""
    c, s = np.cos(TILT), np.sin(TILT)
    return np.array([x, y * c - (z - ZB) * s, y * s + (z - ZB) * c + ZB])


def tilt_dir(v):
    c, s = np.cos(TILT), np.sin(TILT)
    return np.array([v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c])


# ---------------------------------------------------------------------------------------------------- loading
def load():
    scene = trimesh.load(GLB)
    out = {}
    for node in scene.graph.nodes_geometry:
        T, g = scene.graph[node]
        m = scene.geometry[g].copy()
        m.apply_transform(T)
        col = tuple(int(c) for c in m.visual.material.baseColorFactor[:3])
        out[node] = (trimesh.Trimesh(m.vertices, m.faces, process=False), col)
    return out


def pieces(m):
    return sorted(m.split(only_watertight=False), key=lambda q: tuple(np.round(q.centroid, 1)))


def axis_of(m):
    v = m.vertices - m.vertices.mean(0)
    w, e = np.linalg.eigh(np.cov(v.T))
    return e[:, 2]


def head_end(m, a):
    """The unit vector from a screw's tip to its head along axis a (the head is the wider end), and the head's end point."""
    c = m.vertices.mean(0)
    t = (m.vertices - c) @ a
    r = np.linalg.norm((m.vertices - c) - np.outer(t, a), axis=1)
    lo, hi = t.min(), t.max()
    r_lo = r[t < lo + 1.0].max()
    r_hi = r[t > hi - 1.0].max()
    if r_lo > r_hi:
        a, hi = -a, -lo
    return a, c + a * hi


class Item:
    """A part or a screw, with its colour and, for screws, its out direction (tip to head) and head point."""

    def __init__(self, name, mesh, color, out=None, head=None, kind=None):
        self.name, self.mesh, self.color, self.out, self.head, self.kind = name, mesh, color, out, head, kind
        self.move = np.zeros(3)

    def moved(self):
        return self.mesh.copy().apply_translation(self.move)

    def anchor(self):
        return (self.head if self.head is not None else self.mesh.centroid) + self.move


def screw(name, mesh, color, kind, out=None):
    a = axis_of(mesh) if out is None else np.asarray(out, float) / np.linalg.norm(out)
    if out is None:
        a, hp = head_end(mesh, a)
    else:
        c = mesh.vertices.mean(0)
        hp = c + a * ((mesh.vertices - c) @ a).max()
    return Item(name, mesh, color, a, hp, kind)


def place_copy(item, head_pt, out, kind, name):
    """A copy of screw `item` turned to point `out` and moved so its head end is at head_pt."""
    R = trimesh.geometry.align_vectors(item.out, out)
    m = item.mesh.copy().apply_translation(-item.head).apply_transform(R).apply_translation(head_pt)
    return Item(name, m, RED, np.asarray(out, float), np.asarray(head_pt, float), kind)


def annulus_z(z0, z1, cx, cy, ro=12.5, ri=11.5):
    m = trimesh.creation.annulus(r_min=ri, r_max=ro, height=z1 - z0, sections=96)
    return m.apply_translation((cx, cy, (z0 + z1) / 2))


def hex_nut(af, thick, hole):
    r = af / np.sqrt(3.0)
    body = trimesh.creation.cylinder(radius=r, height=thick, sections=6)
    body.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 6, (0, 0, 1)))
    bore = trimesh.creation.cylinder(radius=hole / 2, height=thick + 1, sections=48)
    return body.difference(bore, engine="manifold")


# ---------------------------------------------------------------------------------------------------- the head
def head_items(src):
    """Every Rev 5 head part in the head frame. Returns {name: Item or [Item, ...]}."""
    H = {}

    def get(n):
        m, col = src["H:" + n]
        return m.copy().apply_transform(TO_HEAD), col

    for n in ("Body", "Lower panel", "Lower panel text", "Upper panel", "Upper panel text", "Lower toggles and STOP REL",
              "Lower switch nuts", "Upper toggles", "Upper switch nuts", "Search hat cap", "Hat tact switches",
              "HeliSR board", "Pro Micro", "JST plugs + wires", "USB plug", "AS5600 module", "AS5600 chip", "Magnet",
              "Magnet shaft", "Pinion", "Friction collar", "Throttle grip", "Trigger", "Trigger spring",
              "Starter tact switch"):
        m, col = get(n)
        H[n] = Item(n, m, col)
    m, col = get("4-way hat: bezel, rocker plate, set screw")
    ps = sorted(m.split(only_watertight=False), key=lambda q: -len(q.faces))
    H["Hat bezel and rocker"] = Item("Hat bezel and rocker", ps[0], col)
    H["hat bezel screws"] = [screw("M2 x 8", q, RED, "M2x8") for q in ps[1:]]
    m, col = get("O-ring")
    rings = sorted(m.split(only_watertight=False), key=lambda q: q.centroid[2])
    H["O-ring collar"], H["O-ring grip low"], H["O-ring grip high"], H["O-ring ceiling"] = (
        Item("O-ring", q, col) for q in rings)
    H["tube"] = Item("Tube", annulus_z(-205.0, 55.9, 5.29, 18.52), (201, 206, 212))
    H["lower panel screws"] = [screw("M3 x 16", q, RED, "M3x16") for q in pieces(get("Lower panel screws M3 x 16")[0])]
    H["upper panel screws"] = [screw("M3 x 16", q, RED, "M3x16") for q in pieces(get("Upper panel screws M3 x 16")[0])]
    H["helisr screws"] = [screw("M3 x 12", q, RED, "M3x12") for q in pieces(get("HeliSR screws M3 x 12")[0])]
    nut_axis = tilt_dir((0, 1, 0))
    H["helisr nuts"] = [screw("M3 nut", q, RED, "M3nut", out=-nut_axis) for q in pieces(get("HeliSR nuts")[0])]
    cs = sorted(get("Collar screw M4 x 12 + nut")[0].split(only_watertight=False), key=lambda q: -q.extents[2])
    H["collar screw"] = screw("M4 x 12", cs[0], RED, "M4x12")
    H["collar nut"] = screw("M4 nut", cs[1], RED, "M4nut", out=-H["collar screw"].out)
    H["tube set screw"] = screw("M5 x 8", get("Tube set screw M5 x 8")[0], RED, "M5x8set", out=(0, -1, 0))
    H["pull stop"] = screw("M3 x 4", get("Pull stop set screw M3 x 4")[0], RED, "M3x4set", out=tilt_dir((0, 1, 0)))
    H["pivot"] = screw("M3 x 25", get("Trigger pivot M3 x 25")[0], RED, "M3x25")
    # not in the GLB: the pull stop's seat, a kit M2 x 8 countersunk flush in the mount's face (MOUNT_FACE = 49) where the
    # stop screw's tip lands (STOP_SCREW x, z = -1.28, -13.1), driven toward the front; and the hat's pivot set screw, M3 x 4
    # in the rocker plate's centre (box frame y -2.5 .. 1.5 at SEARCH = (5.29, 43.96)), its tip on the bezel's underside
    H["stop seat"] = place_copy(H["hat bezel screws"][0], tilt_pt(-1.28, 49.0, -13.1), tilt_dir((0, 1, 0)), "M2x8",
                                "M2 x 8")
    ps = H["pull stop"]
    H["hat pivot"] = place_copy(ps, tilt_pt(5.29, 1.5, 43.96), tilt_dir((0, 1, 0)), "M3x4set", "M3 x 4")
    return H


def flat(H, keys=None):
    out = []
    for k, v in H.items():
        if keys is not None and k not in keys:
            continue
        out += v if isinstance(v, list) else [v]
    return out


# ---------------------------------------------------------------------------------------------------- the base
def base_items(src):
    B = {}
    for n in ("frame", "lever_lower", "lever_upper", "cap_left", "cap_right", "cover_sensor", "cover_cable", "cable_plug",
              "shoe", "felt", "friction_knob", "knob_spring", "sensor_carrier", "sensor_pcb", "sensor_chip", "magnet",
              "gas_strut", "strut_collar", "hose_clamp", "bearing_inner", "bearing_outer", "bearing_seal"):
        m, col = src[n]
        B[n] = Item(n, m.copy(), col)
    for side in (-1, 1):                                   # one bearing each side
        for n in ("bearing_inner", "bearing_outer", "bearing_seal"):
            m = B[n].mesh
            ps = [q for q in m.split(only_watertight=False) if np.sign(q.centroid[1]) == side]
            B[f"{n}{side}"] = Item(n, trimesh.util.concatenate(ps), B[n].color)
    for n in ("bearing_inner", "bearing_outer", "bearing_seal"):
        del B[n]
    t = annulus_z(-128.65, 128.65, 0, 0)               # the tube, cut short: x -260 .. -2.7 at (y, z) = (-9, 0)
    t.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    B["tube"] = Item("tube", t.apply_translation((-131.35, -9.0, 0)), src["carbon_tube"][1])
    hw = pieces(src["hardware"][0])
    cap_s, stop_s, cover_s, other = [], [], [], []
    for q in hw:
        L = q.extents.max()
        c = q.centroid
        if abs(L - 25.0) < 0.5:
            cover_s.append(screw("M3 x 25", q, RED, "M3x25"))
        elif abs(L - 16.0) < 0.5:
            stop_s.append(screw("M4 x 16", q, RED, "M4x16"))
        elif abs(L - 20.0) < 0.5 and q.extents[2] > 19:
            cap_s.append(screw("M4 x 20", q, RED, "M4x20"))
        elif abs(L - 20.0) < 0.5:
            B["hinge screw"] = screw("M4 x 20", q, RED, "M4x20")
        elif L > 26:
            B["knob bolt"] = screw("M5 x 25 hex", q, RED, "M5x25hex")
        else:
            B["plug screw"] = screw("M2 x 12", q, RED, "M2x12")
    B["cap screws"], B["downstop screws"], B["cover screws"] = cap_s, stop_s, cover_s
    B["lever screws"] = [screw("M4 x 40", q, RED, "M4x40shcs") for q in pieces(src["lever_screws"][0])]
    pins = pieces(src["strut_pins"][0])
    B["strut screws"] = [screw("M4 x 16", q, RED, "M4x16") for q in pins if q.extents.max() > 14]
    B["collar screws"] = [screw("M4 x 12", q, RED, "M4x12") for q in pins if q.extents.max() < 14]
    return B


# ---------------------------------------------------------------------------------------------------- drawing
def to_pv(m):
    f = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).ravel()
    return pv.PolyData(np.asarray(m.vertices, float), f)


BG_TOP, BG_BOT = (250, 251, 252), (228, 231, 236)


def render(items, view, up, size=(1500, 1200), zoom=1.0, anchors=(), focus=None, crop=False):
    """Render items (each drawn where Item.move puts it). view: direction from the scene to the camera; focus: the items
    to frame (all of them if None); crop: trim the empty background round the parts. Returns the image and the anchors'
    pixel positions."""
    p = pv.Plotter(off_screen=True, window_size=size, lighting="light kit")
    p.set_background(BG_BOT, top=BG_TOP)
    for it in items:
        p.add_mesh(to_pv(it.moved()), color=it.color, smooth_shading=True, split_sharp_edges=True, feature_angle=35,
                   ambient=0.22, diffuse=0.8, specular=0.25 if it.kind else 0.12, specular_power=18)
    pts = np.vstack([it.moved().bounds for it in (focus or items)])
    lo, hi = pts.min(0), pts.max(0)
    ctr = (lo + hi) / 2
    view = np.asarray(view, float) / np.linalg.norm(view)
    p.camera_position = [tuple(ctr + view * 1000), tuple(ctr), tuple(up)]
    p.reset_camera(bounds=(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    p.camera.zoom(zoom)
    p.enable_anti_aliasing("ssaa")
    img = Image.fromarray(p.screenshot(return_img=True))
    r = p.renderer
    px = []
    for a in anchors:
        r.SetWorldPoint(*a, 1.0)
        r.WorldToDisplay()
        x, y, _ = r.GetDisplayPoint()
        px.append((x, size[1] - y))
    p.close()
    if crop:                                          # the background is a vertical gradient: compare each row with its
        a = np.asarray(img).astype(int)               # own left edge
        diff = np.abs(a - a[:, :1, :]).sum(2) > 24
        ys, xs = np.nonzero(diff)
        m = 40
        x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, a.shape[1])
        y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, a.shape[0])
        img = img.crop((x0, y0, x1, y1))
        px = [(x - x0, y - y0) for x, y in px]
    return img, px


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def compose(img, px, labels, title, subtitle, out, side=360):
    """labels: [(title, text, [anchor index, ...])]. Draws the render with callout boxes either side and leader lines."""
    W, Hh = img.size
    top = 96
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    ft, fs = font(21, True), font(17)
    bw = side - 40
    boxes = {"L": [], "R": []}
    allb = []
    for t, s, idx in labels:
        pts = [(px[i][0] + side, px[i][1] + top) for i in idx]
        mx = np.mean([p[0] for p in pts])
        my = np.mean([p[1] for p in pts])
        lines = wrap(d, s, fs, bw - 16) if s else []
        h = 12 + 28 + 21 * len(lines) + 8
        allb.append((mx, [my - h / 2, h, t, lines, pts]))
    allb.sort(key=lambda b: b[0])                     # the left half of the labels, by x, go left: no side gets crowded
    half = (len(allb) + 1) // 2
    cx = side + W / 2
    nl = sum(mx < cx for mx, _ in allb)
    nl = min(max(nl, len(allb) - half - 1), half + 1)
    for i, (mx, b) in enumerate(allb):
        boxes["L" if i < nl else "R"].append(b)
    bottom = Hh + top + 10
    for bs in boxes.values():
        bs.sort(key=lambda b: b[0])
        y = top
        for b in bs:                                  # push down so none overlap ...
            b[0] = max(b[0], y)
            y = b[0] + b[1] + 14
        over = y - 14 - (Hh + top)
        if over > 0:                                  # ... then all up, if the last ran off the bottom
            sh = min(over, bs[0][0] - top)
            for b in bs:
                b[0] -= sh
        bottom = max(bottom, max((b[0] + b[1] + 20 for b in bs), default=0))
    canvas = Image.new("RGB", (W + 2 * side, int(bottom)), "white")
    canvas.paste(img, (side, top))
    d = ImageDraw.Draw(canvas)
    d.text((30, 18), title, font=font(30, True), fill=INK)
    d.text((30, 58), subtitle, font=font(18), fill=SUB)
    for k, bs in boxes.items():
        x0 = 20 if k == "L" else W + side + 20
        for y0, h, t, lines, pts in bs:
            ex = x0 + bw if k == "L" else x0
            ey = y0 + 24
            for p in pts:
                d.line([(ex, ey), p], fill=INK, width=1)
            d.rectangle([x0, y0, x0 + bw, y0 + h], fill="white", outline=INK, width=2)
            d.text((x0 + 9, y0 + 8), t, font=ft, fill=INK)
            for i, ln in enumerate(lines):
                d.text((x0 + 9, y0 + 40 + 21 * i), ln, font=fs, fill=SUB)
            for p in pts:
                d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=RED, outline=INK)
    canvas.save(out, optimize=True)
    print("wrote", os.path.relpath(out, HERE))


def labelled(items, groups, view, up, title, subtitle, out, **kw):
    """groups: [(title, text, [Item, ...])], anchored at each item's head (screws) or centroid (parts)."""
    anchors, labels = [], []
    for t, s, its in groups:
        idx = []
        for it in its:
            idx.append(len(anchors))
            anchors.append(it.anchor())
        labels.append((t, s, idx))
    img, px = render(items, view, up, anchors=anchors, **kw)
    compose(img, px, labels, title, subtitle, out)


# ---------------------------------------------------------------------------------------------------- head views
def head_views(src):
    H = head_items(src)
    n_out = -tilt_dir((0, 1, 0))                     # out of the panels' faces
    lower = ["Lower panel", "Lower panel text", "Lower toggles and STOP REL", "Lower switch nuts", "Search hat cap",
             "Hat bezel and rocker", "Hat tact switches"]
    upper = ["Upper panel", "Upper panel text", "Upper toggles", "Upper switch nuts"]
    board = ["HeliSR board", "Pro Micro", "JST plugs + wires", "USB plug"]
    sensor = ["AS5600 module", "AS5600 chip"]
    shaft = ["Magnet shaft", "Magnet"]
    trig = ["Trigger", "Trigger spring", "Starter tact switch"]
    grip = ["Throttle grip", "O-ring grip low", "O-ring grip high"]
    collar = ["Friction collar", "O-ring collar"]
    everything = flat(H)

    # -------- screw maps, assembled
    sub = "Screws in red. Countersunk screws, set screws and nuts: AvrestYPT and set-screw kits; the trigger's M3 x 25 is bought."
    labelled(everything,
             [("M3 x 16 countersunk  (x4)", "upper panel: into the M3 threads printed in the box's corner columns",
               H["upper panel screws"]),
              ("M3 x 16 countersunk  (x4)", "lower panel: into the M3 threads printed in the box's corner columns",
               H["lower panel screws"]),
              ("M2 x 8 countersunk  (x4)", "the hat's bezel, under its cap, into 1.6 mm pilots in the carrier: tap them M2 by hand",
               H["hat bezel screws"])],
             (0.25, -1.0, -0.15), (0, 0, 1), "Huey head Rev 5 screws: the panels", sub,
             os.path.join(HEAD_OUT, "HueyHeadR5_Screws_Panels.png"),
             focus=[H["Body"]], zoom=1.05)
    inside = [it for it in everything if it.name not in lower + upper and it not in H["lower panel screws"]
              + H["upper panel screws"] + H["hat bezel screws"] + [H["hat pivot"]]]
    labelled(inside,
             [("M5 x 8 set screw", "the tube: into the boss's printed M5 thread, its tip in the tube's 5.2 mm hole. "
               "It goes in through the hat's opening with the lower panel off", [H["tube set screw"]]),
              ("M3 nut  (x4)", "the HeliSR board: on the board's front, on the M3 x 12s from outside the rear wall",
               H["helisr nuts"])],
             (0.25, -1.0, -0.3), (0, 0, 1), "Huey head Rev 5 screws: panels off", sub,
             os.path.join(HEAD_OUT, "HueyHeadR5_Screws_Inside.png"),
             focus=[H["Body"]], zoom=1.05)
    labelled(everything,
             [("M3 x 12 countersunk  (x4)", "the HeliSR board: from outside the rear wall, through the spacers and the "
               "board, into M3 nuts on its front", H["helisr screws"]),
              ("M3 x 25 countersunk (bought)", "the trigger's pivot: from the left lug's countersink, through the "
               "trigger, 8 mm into the right lug's printed thread", [H["pivot"]]),
              ("M3 x 4 set screw", "the pull stop: into the trigger arm's printed thread from behind; its tip meets the "
               "M2 seat", [H["pull stop"]]),
              ("M2 x 8 countersunk", "the pull stop's seat: flush in the mount's face, into a 1.6 mm pilot tapped M2 "
               "by hand", [H["stop seat"]])],
             (-0.35, 1.0, -0.45), (0, 0, 1), "Huey head Rev 5 screws: from behind and below", sub,
             os.path.join(HEAD_OUT, "HueyHeadR5_Screws_Rear.png"),
             focus=[H["Body"], H["Trigger"]], zoom=1.0)
    near = [it for it in everything if it.mesh.bounds[0][2] < -60 or it.name == "Tube"]
    labelled(near,
             [("M4 x 12 countersunk", "the friction collar: head 2 mm into one ear", [H["collar screw"]]),
              ("M4 nut", "in the other ear's pocket", [H["collar nut"]])],
             (1.0, -0.8, 0.35), (0, 0, 1), "Huey head Rev 5 screws: the friction collar", sub,
             os.path.join(HEAD_OUT, "HueyHeadR5_Screws_Collar.png"),
             focus=[H["Friction collar"]], zoom=0.45)

    # -------- exploded
    def mv(keys, v):
        for k in keys:
            for it in (H[k] if isinstance(H[k], list) else [H[k]]):
                it.move = np.asarray(v, float)

    def pull(its, base, dist):
        for it in its:
            it.move = np.asarray(base, float) + it.out * dist

    mv(lower, n_out * 120)
    pull(H["lower panel screws"], n_out * 120, 45)
    pull(H["hat bezel screws"], n_out * 120, 22)
    mv(["Search hat cap"], n_out * 150)
    pull([H["hat pivot"]], n_out * 120, 0)
    mv(upper, n_out * 110)
    pull(H["upper panel screws"], n_out * 110, 45)
    mv(board, n_out * 55)
    pull(H["helisr nuts"], n_out * 55, 16)
    pull(H["helisr screws"], (0, 0, 0), 30)
    mv(sensor, (0, -62, 12))
    mv(shaft, (0, -62, -4))
    mv(["Pinion"], (0, -62, -20))
    pull([H["tube set screw"]], (0, 0, 0), 55)
    mv(grip, (0, 0, -60))
    mv(["O-ring ceiling"], (0, 0, -25))
    mv(collar, (0, 0, -105))
    pull([H["collar screw"]], (0, 0, -105), 20)
    pull([H["collar nut"]], (0, 0, -105), 15)
    back = tilt_dir((0, 1, 0))
    mv(["Trigger"], back * 45 + np.array([0, 0, -10]))
    mv(["Trigger spring"], back * 22)
    mv(["Starter tact switch"], back * 8)
    pull([H["pull stop"]], back * 45 + np.array([0, 0, -10]), 18)
    pull([H["pivot"]], back * 45 + np.array([0, 0, -10]), 32)
    pull([H["stop seat"]], (0, 0, 0), 12)

    parts = [("Upper panel", "with its two toggles and their nuts", ["Upper panel"]),
             ("Lower panel", "with GOV, LDG LT, STOP REL and the 4-way hat's carrier, tact switches, rocker plate and "
              "bezel", ["Lower panel"]),
             ("Hat cap", "glued onto the rocker plate's legs last", ["Search hat cap"]),
             ("HeliSR board + Pro Micro", "on four 4 mm spacers on the rear wall", ["HeliSR board"]),
             ("AS5600 module", "chip down, slides into its grooves from the front", ["AS5600 module"]),
             ("Magnet shaft + magnet", "down through the web into the pinion's hex", ["Magnet shaft"]),
             ("Pinion", "up through the neck, sideways into its pocket", ["Pinion"]),
             ("Body", "one print: box, neck, tube boss and trigger mount", ["Body"]),
             ("Throttle grip", "with an O-ring in each end of its bore", ["Throttle grip"]),
             ("O-ring", "in the ceiling's groove", ["O-ring ceiling"]),
             ("Friction collar", "with its O-ring, groove up", ["Friction collar"]),
             ("Tube", "25 x 23 mm carbon", ["tube"])]
    screws_f = [("M3 x 16 countersunk  (x8)", "", H["lower panel screws"] + H["upper panel screws"]),
                ("M2 x 8 countersunk  (x4)", "hat bezel", H["hat bezel screws"]),
                ("M3 nut  (x4)", "", H["helisr nuts"]),
                ("M5 x 8 set screw", "tube", [H["tube set screw"]]),
                ("M4 x 12 countersunk + M4 nut", "", [H["collar screw"]])]
    groups = [(t, s, [H[k] for k in ks]) for t, s, ks in parts] + screws_f
    labelled(everything, groups, (0.75, -1.0, 0.3), (0, 0, 1), "Huey head Rev 5, exploded",
             "Printed parts in their colours, screws and nuts in red. The panels come off toward the front; the "
             "throttle slides down the tube.", os.path.join(HEAD_OUT, "HueyHeadR5_Exploded.png"), size=(1700, 1700),
             crop=True)
    rear = [("Trigger", "slides in from behind between the lugs", ["Trigger"]),
            ("Return spring", "pen spring, about 13 mm", ["Trigger spring"]),
            ("Starter tact switch", "pushed into its pocket from behind, legs first", ["Starter tact switch"]),
            ("Body", "", ["Body"])]
    screws_r = [("M3 x 25 countersunk (bought)", "trigger pivot", [H["pivot"]]),
                ("M3 x 4 set screw", "pull stop, in the trigger's arm", [H["pull stop"]]),
                ("M2 x 8 countersunk", "pull stop's seat", [H["stop seat"]]),
                ("M3 x 12 countersunk  (x4)", "HeliSR board, from outside the rear wall", H["helisr screws"])]
    groups = [(t, s, [H[k] for k in ks]) for t, s, ks in rear] + screws_r
    labelled(everything, groups, (-0.6, 1.0, -0.2), (0, 0, 1), "Huey head Rev 5, exploded from behind",
             "The trigger comes off backward; the HeliSR board's screws come out of the rear wall.",
             os.path.join(HEAD_OUT, "HueyHeadR5_Exploded_Rear.png"), size=(1500, 1300),
             focus=[H["Body"], H["Trigger"], H["pivot"]], zoom=0.95)
    return H


# ---------------------------------------------------------------------------------------------------- base view
def base_views(src):
    B = base_items(src)
    everything = flat(B)

    def mv(keys, v):
        for k in keys:
            for it in (B[k] if isinstance(B[k], list) else [B[k]]):
                it.move = np.asarray(v, float)

    def pull(its, base, dist):
        for it in its:
            it.move = np.asarray(base, float) + it.out * dist

    L = np.array([0, 0, 95.0])                         # the lever, lifted out of the pillow blocks
    mv(["lever_lower"], L)
    mv(["lever_upper"], L + (0, 0, 50))
    pull(B["lever screws"], L + (0, 0, 50), 60)
    mv(["tube"], L + (-90, 0, 0))
    mv(["hose_clamp"], L + (-30, 0, 0))
    mv(["strut_collar"], L + (-90, 0, 0))
    pull(B["collar screws"], L + (-90, 0, 0), 22)
    for s in (-1, 1):
        mv([f"bearing_inner{s}", f"bearing_outer{s}", f"bearing_seal{s}"], L + (0, 40 * s, 0))
    mv(["sensor_carrier"], L + (0, -75, 0))
    mv(["sensor_pcb", "sensor_chip"], L + (0, -95, 0))
    for c, s in (("cap_left", -1), ("cap_right", 1)):
        mv([c], (0, 40 * s, 165))
    for it in B["cap screws"]:
        it.move = np.array([0, 40 * np.sign(it.head[1]), 165]) + it.out * 40
    mv(["cover_sensor", "magnet"], (0, -150, 40))
    mv(["cover_cable", "cable_plug"], (0, 150, 40))
    pull([B["plug screw"]], (0, 150, 40), 25)
    for it in B["cover screws"]:
        it.move = np.array([0, 150 * np.sign(it.head[1]), 40]) + it.out * 35
    mv(["felt"], (0, 0, 22))
    mv(["friction_knob"], (0, 0, 32))               # under the lifted lever
    mv(["knob_spring"], (0, 0, 16))
    pull([B["knob bolt"]], (0, 0, 32), 0)
    pull([B["hinge screw"]], (0, 0, 0), 40)
    pull(B["downstop screws"], (0, 0, 0), 22)
    for it in B["strut screws"]:                      # the anchor's screw stays with the frame, the eye's with the collar
        if it.head[0] > -60:
            pull([it], (0, 0, 0), 30)
        else:
            pull([it], L + (-90, 0, 0), 30)

    parts = [("Frame", "pillow blocks, knob tower, anchor clevis, stop pedestal, down-stop posts", ["frame"]),
             ("Lever, lower half", "four M4 nuts in its pockets; the cables lie in its channels", ["lever_lower"]),
             ("Lever, upper half", "", ["lever_upper"]),
             ("6006-2RS bearings  (x2)", "pressed onto the trunnions", ["bearing_outer-1", "bearing_outer1"]),
             ("Pillow-block caps  (x2)", "", ["cap_left", "cap_right"]),
             ("Sensor cover", "with the magnet", ["cover_sensor"]),
             ("Cable cover + cable plug", "", ["cover_cable"]),
             ("Sensor carrier + AS5600", "plugs into the trunnion's bore", ["sensor_carrier"]),
             ("Friction knob", "spring under it; the M5 bolt's head in its hex pocket", ["friction_knob"]),
             ("Shoe + felt", "hinged on the frame's lugs", ["shoe", "felt"]),
             ("Gas strut", "X AUTOHAUX 6 in, 45 N", ["gas_strut"]),
             ("Strut collar", "clamped on the tube", ["strut_collar"]),
             ("Hose clamp", "on the socket's mouth", ["hose_clamp"]),
             ("Carbon tube", "25 x 23 mm, 500 mm (shortened here)", ["tube"])]
    screws = [("M4 x 40 socket head cap  (x4)", "lever halves", B["lever screws"]),
              ("M4 x 20 countersunk  (x4)", "caps", B["cap screws"]),
              ("M3 x 25 countersunk  (x8)", "side covers", B["cover screws"]),
              ("M5 x 25 hex bolt (bought)", "knob", [B["knob bolt"]]),
              ("M4 x 20 countersunk", "shoe hinge", [B["hinge screw"]]),
              ("M4 x 16 countersunk  (x4)", "strut eyes and down-stops", B["strut screws"] + B["downstop screws"]),
              ("M4 x 12 countersunk  (x2)", "strut collar clamp", B["collar screws"]),
              ("M2 x 12 countersunk", "cable plug", [B["plug screw"]])]
    groups = [(t, s, [B[k] for k in ks]) for t, s, ks in parts] + screws
    labelled(everything, groups, (-0.55, -1.0, 0.75), (0, 0, 1), "MkIII base Rev 3, exploded",
             "Printed parts in their colours, screws in red with their nuts on them. The tube is cut short.",
             os.path.join(BASE_OUT, "rev3_exploded.png"), size=(2100, 1900), crop=True)
    return B


# ---------------------------------------------------------------------------------------------------- size charts
PPM = 11.0                                            # pixels per mm in the charts


def screw_mesh(kind, d, L):
    """A plain screw along +x, head end at x = 0, to ISO proportions: "csk" (90 degree head of 2 d, L overall, as
    countersunk screws are sized), "shcs" (socket head 1.5 d across and d tall, L under it), "hex" (hex head, L under it)
    or "set" (L end to end). The charts draw these rather than the GLB's screws, some of which have their nuts merged on."""
    def lathe(profile, sections=64):
        m = trimesh.creation.revolve(np.array(profile, float), sections=sections)    # (r, z) about z
        return m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))  # z -> x
    r = d / 2
    if kind == "csk":
        return lathe([(0, 0), (d, 0), (r, r), (r, L), (0, L)])        # head 2 d across, d / 2 tall
    if kind == "shcs":
        return lathe([(0, -d), (0.75 * d, -d), (0.75 * d, 0), (r, 0), (r, L), (0, L)])
    if kind == "hex":
        h = trimesh.creation.cylinder(radius=1.6 * d / np.sqrt(3.0), height=0.7 * d, sections=6)
        h.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
        return trimesh.util.concatenate([h.apply_translation((-0.35 * d, 0, 0)), lathe([(0, 0), (r, 0), (r, L), (0, L)])])
    return lathe([(0, 0), (r, 0), (r, L), (0, L)])


def screw_tile(kind, d, L):
    """The screw side-on, head left, at PPM pixels per mm."""
    m = screw_mesh(kind, d, L)
    m.apply_translation((-m.bounds[0][0], 0, 0))
    W = int(max(m.extents[0], 10) * PPM + 40)
    H = int(max(m.extents[1], m.extents[2]) * PPM + 30)
    p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="light kit")
    p.set_background("white")
    p.add_mesh(to_pv(m), color=(176, 52, 46), smooth_shading=True, split_sharp_edges=True, ambient=0.25,
               specular=0.3, specular_power=15)
    p.enable_parallel_projection()
    cx = (W / 2 - 20) / PPM
    p.camera_position = [(cx, -500, 0), (cx, 0, 0), (0, 0, 1)]
    p.camera.parallel_scale = H / 2 / PPM
    p.enable_anti_aliasing("ssaa")
    img = Image.fromarray(p.screenshot(return_img=True))
    p.close()
    return img


def nut_tile(af, thick, hole):
    m = hex_nut(af, thick, hole)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-70), (1, 0, 0)))
    W = H = int(af * 1.25 * PPM + 30)
    p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="light kit")
    p.set_background("white")
    p.add_mesh(to_pv(m), color=(176, 52, 46), smooth_shading=True, split_sharp_edges=True, ambient=0.25,
               specular=0.3)
    p.enable_parallel_projection()
    p.camera_position = [(0, -500, 0), (0, 0, 0), (0, 0, 1)]
    p.camera.parallel_scale = H / 2 / PPM
    p.enable_anti_aliasing("ssaa")
    img = Image.fromarray(p.screenshot(return_img=True))
    p.close()
    return img


def chart(rows, title, subtitle, out):
    """rows: [(tile image, name, qty, where)]"""
    tw = max(r[0].size[0] for r in rows)
    W = 40 + tw + 40 + 760
    H = 150 + sum(max(r[0].size[1], 80) + 18 for r in rows) + 20
    c = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(c)
    d.text((30, 18), title, font=font(30, True), fill=INK)
    d.text((30, 58), subtitle, font=font(18), fill=SUB)
    x0, y = 40 + 20, 112                                  # the ruler: 0 .. 50 mm at PPM
    d.line([(x0, y), (x0 + 50 * PPM, y)], fill=INK, width=2)
    for mm in range(0, 51):
        h = 12 if mm % 10 == 0 else (8 if mm % 5 == 0 else 4)
        d.line([(x0 + mm * PPM, y), (x0 + mm * PPM, y - h)], fill=INK, width=1)
        if mm % 10 == 0:
            d.text((x0 + mm * PPM - 6, y + 4), str(mm), font=font(14), fill=SUB)
    d.text((x0 + 50 * PPM + 14, y - 10), "mm. Countersunk screws are sized overall, head included; socket head and hex bolts under the head",
           font=font(15), fill=SUB)
    y = 150
    for img, name, qty, where in rows:
        h = max(img.size[1], 80)
        c.paste(img, (40, y + (h - img.size[1]) // 2))
        tx = 40 + tw + 40
        d.text((tx, y + 4), f"{name}   x{qty}", font=font(22, True), fill=INK)
        for i, ln in enumerate(textwrap.wrap(where, 78)[:3]):
            d.text((tx, y + 36 + 21 * i), ln, font=font(17), fill=SUB)
        y += h + 18
        d.line([(30, y - 9), (W - 30, y - 9)], fill=(225, 225, 225), width=1)
    c.save(out, optimize=True)
    print("wrote", os.path.relpath(out, HERE))


def head_chart(H):
    rows = [(screw_tile("csk", 3, 16), "M3 x 16 countersunk", 8,
             "Both panels, into the M3 threads printed in the box's corner columns (an M3 x 20 fits too)."),
            (screw_tile("csk", 3, 12), "M3 x 12 countersunk", 4,
             "The HeliSR board, from outside the rear wall, through the spacers and the board."),
            (screw_tile("csk", 3, 25), "M3 x 25 countersunk (bought)", 1,
             "The trigger's pivot (ISO 10642 / DIN 7991; NIULUNBAO M3 set): the kits stop at 20 mm."),
            (screw_tile("csk", 2, 8), "M2 x 8 countersunk", 5,
             "The hat's bezel (4) and the pull stop's seat (1), into 1.6 mm pilots tapped M2 by hand."),
            (screw_tile("csk", 4, 12), "M4 x 12 countersunk", 1, "The friction collar's pinch screw."),
            (screw_tile("set", 5, 8), "M5 x 8 set screw", 1,
             "The tube, into the boss's printed thread; its tip in the tube's 5.2 mm hole."),
            (screw_tile("set", 3, 4), "M3 x 4 set screw", 2,
             "The trigger's pull stop and the hat's pivot (in the rocker plate's centre)."),
            (nut_tile(5.5, 2.4, 3.0), "M3 nut", 4, "On the HeliSR board's front."),
            (nut_tile(7.0, 3.2, 4.0), "M4 nut", 1, "In the friction collar's ear.")]
    chart(rows, "Huey head Rev 5: every screw, to scale",
          "Countersunk screws and nuts: AvrestYPT kit. Set screws: HIQTRADEBYJJ kit. The M3 x 25 is bought separately.",
          os.path.join(HEAD_OUT, "HueyHeadR5_ScrewSizes.png"))


def base_chart(B):
    rows = [(screw_tile("shcs", 4, 40), "M4 x 40 socket head cap", 4,
             "The lever halves, from the top, into M4 nuts in the lower half (HELIFOUNER M4 x 30-50 kit)."),
            (screw_tile("hex", 5, 25), "M5 x 25 hex bolt (bought)", 1,
             "The friction knob: head in the knob's hex pocket, into an M5 nut in the knob tower."),
            (screw_tile("csk", 3, 25), "M3 x 25 countersunk", 8,
             "The side covers, into M3 threads tapped 11 mm deep in the blocks and caps (NIULUNBAO M3 set)."),
            (screw_tile("csk", 4, 20), "M4 x 20 countersunk", 5,
             "The pillow-block caps (4), into nuts slid into the blocks; the shoe's hinge (1)."),
            (screw_tile("csk", 4, 16), "M4 x 16 countersunk", 4,
             "The strut's two eyes (into nuts in the far cheeks) and the two down-stops (head up, with lock nuts)."),
            (screw_tile("csk", 4, 12), "M4 x 12 countersunk", 2, "The strut collar's clamp, into nuts in the "
             "other ear."),
            (screw_tile("csk", 2, 12), "M2 x 12 countersunk", 1,
             "The cable plug, up from under the cable cover's rim into a thread tapped M2 in the plug."),
            (nut_tile(7.0, 3.2, 4.0), "M4 nut", 15,
             "Lever (4), caps (4), shoe hinge (1), strut eyes (2), collar clamp (2), down-stop posts (2); plus 2 M4 "
             "lock nuts on the down-stops."),
            (nut_tile(8.0, 4.0, 5.0), "M5 nut", 1, "In the knob tower, slid in from the front.")]
    chart(rows, "MkIII base Rev 3: every screw, to scale",
          "Countersunk screws and nuts: AvrestYPT kit, except where named.",
          os.path.join(BASE_OUT, "rev3_screw_sizes.png"))


if __name__ == "__main__":
    pv.OFF_SCREEN = True
    src = load()
    H = head_views(src)
    head_chart(H)
    B = base_views(src)
    base_chart(B)
