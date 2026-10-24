# Standardise the Rev 3.0 silkscreen: every label 1.0 mm tall with a 0.16 mm stroke, every front label clear of
# all part courtyards, and nothing on the back but the board name and revision.
#   - Back: every text except "HELI SR Rev 3.0" is deleted.
#   - Each remaining label goes to the nearest clear spot to where it was: 0.10 mm clear of every courtyard, pad
#     opening and part outline, 0.25 mm from the board edge and 0.5 mm from the other labels. Upright text is preferred;
#     a label turns 90 degrees only where it doesn't fit flat. Tented vias may sit under a label but are avoided.
# Mounting holes count as parts: their courtyards (6.9 mm across) cover the M3 nut on the front and the spacer on
# the back. Run with KiCad 9's python (uses its numpy and PIL).
# usage: silk_fix_v3.py <in.kicad_pcb> <out.kicad_pcb> [preview.png]
import sys
import numpy as np
import pcbnew
from PIL import Image, ImageDraw

src, dst = sys.argv[1:3]
PREVIEW = sys.argv[3] if len(sys.argv) > 3 else None
SIZE, STROKE = 1.0, 0.16
KEEP_BACK = "HELI SR Rev 3.0"
OWNER = {"RST": "SW1", "PROG1": "SW2", "PROG4": "SW3", "USB": None, KEEP_BACK: None}   # label -> part it names
CLR = {"crt": 0.10, "mask": 0.10, "silk": 0.10, "edge": 0.25, "label": 0.50}
ROT_PEN, VIA_PEN, MOVE_W, GAP_W, AMB_W, SEARCH = 1.5, 0.8, 0.15, 1.0, 3.0, 8.0
RES = 0.05                                           # raster step, mm

b = pcbnew.LoadBoard(src)
MM, mm = pcbnew.FromMM, pcbnew.ToMM
ERR = MM(0.002)
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = mm(bb.GetX()) - 1.0, mm(bb.GetY()) - 1.0
NX, NY = int((mm(bb.GetWidth()) + 2.0) / RES) + 1, int((mm(bb.GetHeight()) + 2.0) / RES) + 1
px = lambda x, y: ((x - X0) / RES, (y - Y0) / RES)

def outlines(ps):
    ps = ps.CloneDropTriangulation(); ps.Fracture()
    return [[px(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
            for o in (ps.Outline(i) for i in range(ps.OutlineCount()))]
def item_polys(it, layer):
    ps = pcbnew.SHAPE_POLY_SET(); it.TransformShapeToPolygon(ps, layer, 0, ERR, pcbnew.ERROR_OUTSIDE)
    return outlines(ps)
class Raster:
    def __init__(self): self.img = Image.new("1", (NX, NY), 0); self.d = ImageDraw.Draw(self.img); self.sat = None
    def poly(self, pts):
        if len(pts) > 2: self.d.polygon(pts, fill=1, outline=1)
        self.sat = None
    def rect(self, x0, y0, x1, y1): self.poly([px(x0, y0), px(x1, y0), px(x1, y1), px(x0, y1)])
    def table(self):
        if self.sat is None:
            a = np.asarray(self.img, dtype=np.int32)
            self.sat = np.zeros((NY + 1, NX + 1), np.int32); self.sat[1:, 1:] = a.cumsum(0).cumsum(1)
        return self.sat
def window_sums(r, w, h, c):
    """count of set pixels in a (w x h) px window grown by c px, for every top-left (i, j) of the ungrown window"""
    S = r.table(); W, H = w + 2 * c, h + 2 * c
    s = S[H:, W:] - S[:-H, W:] - S[H:, :-W] + S[:-H, :-W]          # window top-left at (j - c, i - c)
    out = np.full((NY, NX), 1, np.int32)                               # off-raster positions count as blocked
    out[c:c + s.shape[0], c:c + s.shape[1]] = s[:NY - c, :NX - c]
    return out

layers = {"F": (pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_CrtYd), "B": (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_CrtYd)}
R = {s: {k: Raster() for k in ("crt", "mask", "silk", "out", "via", "label")} for s in "FB"}
crt_box = {}
for f in b.GetFootprints():
    f.BuildCourtyardCaches()                         # GetCourtyard() is empty until this has run
    c = f.GetCourtyard(pcbnew.F_CrtYd)
    if c.OutlineCount():
        cb = c.BBox(); crt_box[f.GetReference()] = (mm(cb.GetX()), mm(cb.GetY()), mm(cb.GetRight()), mm(cb.GetBottom()))
        for p in outlines(c):
            R["F"]["crt"].poly(p)
            if f.GetReference().startswith("H"): R["B"]["crt"].poly(p)    # the spacer on the back
    for s, (sl, ml, _) in layers.items():
        for p in f.Pads():
            if p.IsOnLayer(ml) or p.GetDrillSize().x > 0:
                for q in item_polys(p, ml if p.IsOnLayer(ml) else pcbnew.F_Cu): R[s]["mask"].poly(q)
        for g in f.GraphicalItems():
            if g.GetLayer() == sl and (g.GetClass() != "PCB_TEXT" or g.IsVisible()):
                for q in item_polys(g, sl): R[s]["silk"].poly(q)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        x, y, r = mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)) / 2
        for s in "FB": R[s]["via"].d.ellipse([*px(x - r, y - r), *px(x + r, y + r)], fill=1)
outline = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(outline)
for s in "FB":
    R[s]["out"].d.rectangle([0, 0, NX, NY], fill=1)
    for p in outlines(outline): R[s]["out"].d.polygon(p, fill=0, outline=0)

# ---- the labels -------------------------------------------------------------------------------------------
texts = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
gone = [t for t in texts if t.GetLayer() == pcbnew.B_SilkS and t.GetText() != KEEP_BACK]
labels = [t for t in texts if t not in gone]
for t in gone: b.Remove(t)
print("back labels deleted:", sorted(t.GetText() for t in gone))
def shape(t, rot):                                   # bbox of the text at 1.0 mm, relative to its anchor
    c = t.Duplicate(); c.SetTextSize(pcbnew.VECTOR2I(MM(SIZE), MM(SIZE))); c.SetTextThickness(MM(STROKE))
    c.SetTextAngleDegrees(rot); c.SetPosition(pcbnew.VECTOR2I(0, 0))
    ps = pcbnew.SHAPE_POLY_SET(); c.TransformShapeToPolygon(ps, t.GetLayer(), 0, ERR, pcbnew.ERROR_OUTSIDE)
    q = ps.BBox(); return mm(q.GetX()), mm(q.GetY()), mm(q.GetRight()), mm(q.GetBottom())

Ii, Jj = np.mgrid[0:NY, 0:NX]
XX, YY = X0 + Jj * RES, Y0 + Ii * RES               # mm coordinates of each window's top-left corner
LCLR = int(np.ceil(CLR["label"] / RES))
class Option:                                        # one label at one rotation: score for every clear spot
    def __init__(self, t, rot):
        s = "F" if t.GetLayer() == pcbnew.F_SilkS else "B"
        x0, y0 = mm(t.GetPosition().x), mm(t.GetPosition().y)
        owner = OWNER.get(t.GetText(), t.GetText())
        ox0, oy0, ox1, oy1 = shape(t, rot)
        self.t, self.s, self.rot, self.off = t, s, rot, (ox0, oy0)
        self.w, self.h = int(np.ceil((ox1 - ox0) / RES)) + 1, int(np.ceil((oy1 - oy0) / RES)) + 1
        bad = np.zeros((NY, NX), bool)
        for k in ("crt", "mask", "silk", "out"):
            bad |= window_sums(R[s][k], self.w, self.h, int(np.ceil(CLR["edge" if k == "out" else k] / RES))) > 0
        rx0, ry0, rx1, ry1 = XX, YY, XX + (ox1 - ox0), YY + (oy1 - oy0)
        move = np.hypot(XX - ox0 - x0, YY - oy0 - y0)
        gap_to = lambda c: np.hypot(np.maximum(0, np.maximum(c[0] - rx1, rx0 - c[2])), np.maximum(0, np.maximum(c[1] - ry1, ry0 - c[3])))
        if owner in crt_box:                         # gap to the part it names, and how much nearer some other part is
            self.gap = gap_to(crt_box[owner])
            other = np.min([gap_to(c) for r, c in crt_box.items() if r != owner and not r.startswith("H")], axis=0)
            amb = np.maximum(0, self.gap - other)
        else:
            self.gap = amb = np.zeros_like(move)
        self.move = move
        self.score = (GAP_W * self.gap + AMB_W * amb + MOVE_W * move + (ROT_PEN if rot else 0)
                      + VIA_PEN * (window_sums(R[s]["via"], self.w, self.h, 0) > 0)).astype(np.float32)
        self.score[bad | (move > SEARCH)] = np.inf
        self.n = int(np.isfinite(self.score).sum())
opts = {id(t): [Option(t, r) for r in (0, 90)] for t in labels}
for t in labels:
    if not any(o.n for o in opts[id(t)]): raise SystemExit(f"no clear spot for {t.GetText()} on {t.GetLayerName()}")

def run(order):
    """place labels greedily in this order; each placed label blocks windows that would come within 0.5 mm"""
    placed, total, out = {"F": [], "B": []}, 0.0, {}
    for t in order:
        best = None
        for o in opts[id(t)]:
            sc = o.score.copy()
            for (pi0, pj0, pi1, pj1) in placed[o.s]:
                sc[max(0, pi0 - LCLR - o.h + 1):pi1 + LCLR, max(0, pj0 - LCLR - o.w + 1):pj1 + LCLR] = np.inf
            k = np.unravel_index(np.argmin(sc), sc.shape)
            if np.isfinite(sc[k]) and (best is None or sc[k] < best[0]): best = (float(sc[k]), o, k)
        if best is None: return None
        score, o, (i, j) = best
        placed[o.s].append((i, j, i + o.h, j + o.w)); total += score; out[id(t)] = (o, i, j)
    return total, out
rng = np.random.default_rng(1)
first = sorted(labels, key=lambda t: sum(o.n for o in opts[id(t)]))          # fewest clear spots first
best = run(first)
for _ in range(600):
    order = list(first); rng.shuffle(order)
    r = run(order)
    if r and (best is None or r[0] < best[0]): best = r
if best is None: raise SystemExit("no complete placement found")
print(f"placement score {best[0]:.2f}")
report = []
for t in labels:
    o, i, j = best[1][id(t)]
    x, y = float(XX[i, j] - o.off[0]), float(YY[i, j] - o.off[1])
    old = (mm(t.GetPosition().x), mm(t.GetPosition().y), t.GetTextAngleDegrees(), mm(t.GetTextHeight()))
    t.SetTextSize(pcbnew.VECTOR2I(MM(SIZE), MM(SIZE))); t.SetTextThickness(MM(STROKE)); t.SetTextAngleDegrees(o.rot)
    t.SetPosition(pcbnew.VECTOR2I(MM(round(x, 3)), MM(round(y, 3))))
    report.append((t.GetText(), o.s, old, (round(x, 2), round(y, 2), o.rot), round(float(o.gap[i, j]), 2), round(float(o.move[i, j]), 2)))
for r in sorted(report, key=lambda r: (r[1] == "B", r[0])):
    name, s, (ox, oy, orot, oh), (x, y, rot), gap, move = r
    print(f"{name:16} {s}  {oh:.1f} mm @({ox:6.2f},{oy:6.2f}) rot {orot:3.0f}  ->  1.0 mm @({x:6.2f},{y:6.2f}) rot {rot:3d}"
          f"   moved {move:4.2f}, {gap:4.2f} mm from its part")
b.Save(dst)

if PREVIEW:                                          # courtyards grey, pad openings pink, outlines and labels
    S = 20; img = Image.new("RGB", (NX * S // 4, NY * S // 4), "white"); d = ImageDraw.Draw(img)
    sc = lambda p: (p[0] * S / 4, p[1] * S / 4)
    for f in b.GetFootprints():
        for p in outlines(f.GetCourtyard(pcbnew.F_CrtYd)): d.polygon([sc(q) for q in p], outline=(150, 150, 150), fill=(238, 238, 238))
    for f in b.GetFootprints():
        for p in f.Pads():
            for q in item_polys(p, pcbnew.F_Mask if p.IsOnLayer(pcbnew.F_Mask) else pcbnew.F_Cu): d.polygon([sc(v) for v in q], fill=(225, 120, 170))
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT":
                for q in item_polys(g, pcbnew.F_SilkS): d.polygon([sc(v) for v in q], fill=(120, 120, 60))
    for p in outlines(outline): d.polygon([sc(q) for q in p], outline=(0, 0, 0))
    for t in labels:
        if t.GetLayer() == pcbnew.F_SilkS:
            for q in item_polys(t, pcbnew.F_SilkS): d.polygon([sc(v) for v in q], fill=(20, 60, 200))
    img.save(PREVIEW)
