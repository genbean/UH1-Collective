"""
MkIII base - shared render library (from base Rev 3's renderer; base Rev 3 itself is gone)

This is not a render script. make_renders_r4.py imports it as R for the drawing helpers: render() (pyvista, off
screen, framed on a focus box, with anchors' pixel positions back), cut() (sections cut as closed solids with
manifold3d), save(), load_glb(), hide(), and the paths of the collective's GLB and pictures in ../renders
(ALL_GLB, TOP_OUT). It imports ../renders/make_diagrams.py (as d) for the callout layout and fonts, and the shared
model (mk3_rev3, as r; Rev 1's mk3_pivot as m).
Needs cadquery, numpy, trimesh, manifold3d, pyvista and pillow.
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
ALL_GLB = os.path.join(TOP_OUT, "HeliCollective_Assembly.glb")
RED, EDGE = (214, 48, 39), (30, 30, 34)
HW = ("hardware", "lever_screws", "strut_pins")


# ---------------------------------------------------------------------------------------------------- GLBs
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


# ---------------------------------------------------------------------------------------------------- meshes
def cq_mesh(shape):
    v, f = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True)


def rot(mesh, th):
    return mesh.copy().apply_transform(trimesh.transformations.rotation_matrix(np.radians(th), (0, 1, 0)))


def hide(P, *names):
    return {k: v for k, v in P.items() if k not in names}


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
