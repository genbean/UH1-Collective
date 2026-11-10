# Pick GND stitching-via positions for a poured board: inside the GND fill on both layers, clear of holes and pads,
# farthest-first within each (front island, back island) pair until no spot is more than TARGET mm from a stitch.
# The same search as Rev 3.0's stitch_export.py + stitch_place.py, done on a raster in KiCad's own python (numpy and
# PIL), so it needs no shapely.
# Run with KiCad 9's python. usage: stitch_v4.py <poured.kicad_pcb> <out vias.json> [target mm]
import json, math, sys
import numpy as np
import pcbnew
from PIL import Image, ImageDraw

src, dst = sys.argv[1:3]
TARGET = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
VIA_R, MARGIN, H2H, PAD_CLR, STEP = 0.30, 0.05, 0.60, 0.15, 0.1
RES = 0.05
MM, mm = pcbnew.FromMM, pcbnew.ToMM
ERR = MM(0.002)

b = pcbnew.LoadBoard(src)
for z in b.Zones():                           # see every island, including ones not yet tied to GND
    if not z.GetIsRuleArea(): z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = mm(bb.GetX()), mm(bb.GetY())
NX, NY = int(mm(bb.GetWidth()) / RES) + 2, int(mm(bb.GetHeight()) / RES) + 2
px = lambda x, y: ((x - X0) / RES, (y - Y0) / RES)

def outlines(ps):
    ps = ps.CloneDropTriangulation(); ps.Fracture()
    return [[px(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
            for o in (ps.Outline(i) for i in range(ps.OutlineCount()))]
def item_outlines(it, layer, clr=0.0):
    ps = pcbnew.SHAPE_POLY_SET(); it.TransformShapeToPolygon(ps, layer, MM(clr), ERR, pcbnew.ERROR_OUTSIDE)
    return outlines(ps)
def sat(a):
    s = np.zeros((a.shape[0] + 1, a.shape[1] + 1), np.int64); s[1:, 1:] = a.astype(np.int64).cumsum(0).cumsum(1); return s
def box_sum(a, r):
    """for every pixel, the number of set pixels in the (2r+1)-square around it (off-raster counts as set)"""
    p = np.pad(a.astype(np.int64), r, constant_values=1); S = sat(p); k = 2 * r + 1
    return S[k:, k:] - S[:-k, k:] - S[k:, :-k] + S[:-k, :-k]

# ---- islands: one label per filled outline, per layer -------------------------------------------------------
label = {}
for side, lay in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
    img = Image.new("I", (NX, NY), 0); d = ImageDraw.Draw(img); n = 0
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND" or not z.IsOnLayer(lay): continue
        for o in outlines(z.GetFilledPolysList(lay)):
            n += 1; d.polygon(o, fill=n, outline=n)
    label[side] = np.asarray(img, dtype=np.int32)
    print(side, "islands:", n)

# ---- where a via may go -------------------------------------------------------------------------------------
rv = int(math.ceil((VIA_R + MARGIN) / RES))
ok = np.ones((NY, NX), bool)
for side in "FB":
    ok &= box_sum(label[side] == 0, rv) == 0          # the via's whole square inside the fill
pads = Image.new("1", (NX, NY), 0); dp = ImageDraw.Draw(pads)
holes = []
for f in b.GetFootprints():
    for p in f.Pads():
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(lay):
                for o in item_outlines(p, lay): dp.polygon(o, fill=1, outline=1)
        if p.GetDrillSize().x > 0:
            holes.append((mm(p.GetPosition().x), mm(p.GetPosition().y), mm(p.GetDrillSize().x) / 2, p.GetNetname()))
    if f.GetReference().startswith("SW"):             # the switches' ground tabs rest on their courtyards
        f.BuildCourtyardCaches()
        for o in outlines(f.GetCourtyard(pcbnew.F_CrtYd)): dp.polygon(o, fill=1, outline=1)
vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetDrillValue()) / 2, v.GetNetname())
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
ok &= box_sum(np.asarray(pads, dtype=bool), int(math.ceil((VIA_R + PAD_CLR) / RES))) == 0
hole_img = Image.new("1", (NX, NY), 0); dh = ImageDraw.Draw(hole_img)
for x, y, r, _ in holes + vias:
    R = r + 0.15 + H2H + 0.05                         # + a margin for the raster's rounding
    dh.ellipse([*px(x - R, y - R), *px(x + R, y + R)], fill=1)
ok &= ~np.asarray(hole_img, dtype=bool)

# candidates on a STEP grid
s = int(round(STEP / RES))
ii, jj = np.nonzero(ok[::s, ::s]); ii *= s; jj *= s
cx, cy = X0 + jj * RES, Y0 + ii * RES
ckey = np.stack([label["F"][ii, jj], label["B"][ii, jj]], 1)
print(len(cx), "candidate spots")

# existing stitches: GND through-holes and GND vias, keyed by the islands around them
def key_near(x, y, r):
    i0, j0 = int((y - Y0) / RES), int((x - X0) / RES); k = int(math.ceil(r / RES))
    out = []
    for side in "FB":
        w = label[side][max(0, i0 - k):i0 + k + 1, max(0, j0 - k):j0 + k + 1]; w = w[w > 0]
        out.append(int(np.bincount(w).argmax()) if w.size else 0)
    return tuple(out)
stitch = [(x, y, key_near(x, y, r + 0.9)) for x, y, r, n in holes + vias if n == "GND"]

mind = np.full(len(cx), np.inf)
def update(x, y, k):
    m = (ckey[:, 0] == k[0]) & (ckey[:, 1] == k[1])
    mind[m] = np.minimum(mind[m], np.hypot(cx[m] - x, cy[m] - y))
for x, y, k in stitch: update(x, y, k)
alive = np.ones(len(cx), bool)
chosen = []
while True:
    sc = np.where(alive, mind, -1.0)
    i = int(np.argmax(sc))
    if sc[i] < TARGET: break
    x, y, k = float(cx[i]), float(cy[i]), (int(ckey[i, 0]), int(ckey[i, 1]))
    chosen.append((round(x, 2), round(y, 2)))
    update(x, y, k)
    alive &= np.hypot(cx - x, cy - y) >= 2 * 0.15 + H2H + 0.3      # vias keep hole-to-hole among themselves
print(len(chosen), "vias chosen:", chosen)
json.dump([list(c) for c in chosen], open(dst, "w"))
