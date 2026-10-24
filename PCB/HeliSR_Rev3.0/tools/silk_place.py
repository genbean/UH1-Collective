# Find the nearest clear spot for each silk label at 1.0 mm (JLC min), else 0.8 mm (PCBWay min).
# usage: silk_place.py <problem.json> <placement.json>
import sys, json, math
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.affinity import translate
from shapely.strtree import STRtree

P = json.load(open(sys.argv[1]))
MASK_CLR, SILK_CLR, LABEL_CLR, EDGE_CLR = 0.10, 0.10, 0.15, 0.25
SIZE_PEN = {"1.0": 0.0, "0.8": 0.6, "1.0r": 0.3, "0.8r": 0.9}
VIA_PEN = {"F": 0.8, "B": 2.0}          # tented vias: allowed under silk, but avoided where possible
MAXD, STEP = float(__import__("os").environ.get("SILK_MAXD", "2.0")), 0.05

def poly(pts):
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)

bx0, by0, bx1, by1 = P["board"]
inner = box(bx0 + EDGE_CLR, by0 + EDGE_CLR, bx1 - EDGE_CLR, by1 - EDGE_CLR)
hard, vias = {}, {}
for side in "FB":
    o = P["obst"][side]
    hard[side] = unary_union([poly(p).buffer(MASK_CLR) for p in o["mask"]] + [poly(p).buffer(SILK_CLR) for p in o["silk"]])
    vias[side] = [Point(x, y).buffer(r) for x, y, r in o["via"]]

offsets = []
n = int(MAXD / STEP)
for i in range(-n, n + 1):
    for j in range(-n, n + 1):
        d = math.hypot(i * STEP, j * STEP)
        if d <= MAXD: offsets.append((d, i * STEP, j * STEP))
offsets.sort()

ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None
placed = {"F": [], "B": []}
if ONLY:                                   # labels not being placed stay put and are obstacles
    for L in P["labels"]:
        if L["text"] not in ONLY:
            placed[L["side"]].append(translate(unary_union([poly(s) for s in L["cur"]]), L["x"], L["y"]))
    P["labels"] = [L for L in P["labels"] if L["text"] in ONLY]
result = []
# hardest first: longest labels, then front before back
order = sorted(P["labels"], key=lambda L: -Polygon(L["shapes"]["1.0"][0]).bounds[2] if L["shapes"]["1.0"] else 0)
order = sorted(P["labels"], key=lambda L: -sum(Polygon(s).area for s in L["shapes"]["1.0"]))
for L in order:
    side = L["side"]
    best = None
    vtree = STRtree(vias[side])
    for size, shapes in L["shapes"].items():
        shp = unary_union([poly(s) for s in shapes])
        for d, dx, dy in offsets:
            if best and d + SIZE_PEN[size] >= best[0]: break
            g = translate(shp, L["x"] + dx, L["y"] + dy)
            if not inner.contains(g): continue
            gb = g.buffer(SILK_CLR)
            if gb.intersects(hard[side]): continue
            if any(gb.intersects(q.buffer(LABEL_CLR - SILK_CLR)) for q in placed[side]): continue
            nv = sum(1 for k in vtree.query(g) if g.intersects(vias[side][k]))
            score = d + SIZE_PEN[size] + nv * VIA_PEN[side]
            if best is None or score < best[0]:
                best = (score, size, L["x"] + dx, L["y"] + dy, nv, d, g)
    if best is None:
        print(f"!! no spot for {L['text']} ({side})")
        result.append({**{k: L[k] for k in ("text", "new_text", "side", "x", "y")}, "size": None})
        continue
    score, size, x, y, nv, d, g = best
    placed[side].append(g)
    result.append({"text": L["text"], "new_text": L["new_text"], "side": side, "x": round(x, 3), "y": round(y, 3),
                   "size": float(size.rstrip("r")), "rot": 90 if size.endswith("r") else 0, "thick": 0.16, "moved": round(d, 2), "vias_under": nv,
                   "from": [L["x"], L["y"], L["h"], L["t"]]})
    print(f"{L['new_text']:18} {side} {L['h']}/{L['t']} @({L['x']:.2f},{L['y']:.2f}) -> {size}/0.16 @({x:.2f},{y:.2f}) moved {d:.2f} mm, vias under {nv}")
json.dump(result, open(sys.argv[2], "w"), indent=1)
