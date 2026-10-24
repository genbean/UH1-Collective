# Pick GND stitching via positions: inside both layers' GND fill, clear of holes, pads and silk labels.
# Farthest-first within each (front island, back island) pair until no spot is > TARGET from a stitch.
# usage: stitch_place.py <stitch.json> <out.json>
import sys, json, math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.prepared import prep

P = json.load(open(sys.argv[1]))
VIA_R, MARGIN, H2H, PAD_CLR, SILK_CLR, STEP = 0.30, 0.05, 0.60, 0.15, 0.10, 0.1
TARGET = float(__import__("os").environ.get("STITCH_TARGET", "4.0"))

def poly(pts):
    p = Polygon(pts); return p if p.is_valid else p.buffer(0)
fills = {s: unary_union([poly(p) for p in P["fills"][s]]) for s in "FB"}
islands = {s: list(getattr(fills[s], "geoms", [fills[s]])) for s in "FB"}
region = fills["F"].buffer(-(VIA_R + MARGIN)).intersection(fills["B"].buffer(-(VIA_R + MARGIN)))
block = [Point(x, y).buffer(r + 0.15 + H2H) for x, y, r in P["holes"]]
block += [poly(pd["poly"][0]).buffer(VIA_R + PAD_CLR) for pd in P["pads"] if pd["poly"]]
block += [poly(l).buffer(VIA_R + SILK_CLR) for s in "FB" for l in P["labels"][s]]
block += [poly(c).buffer(0.1) for r in ("SW1", "SW2", "SW3") for c in P["courtyards"].get(r, [])]   # switch ground tabs rest here
region = region.difference(unary_union(block))
rp = prep(region)
minx, miny, maxx, maxy = region.bounds
cands = [(round(minx + i * STEP, 2), round(miny + j * STEP, 2))
         for i in range(int((maxx - minx) / STEP) + 1) for j in range(int((maxy - miny) / STEP) + 1)
         if rp.contains(Point(minx + i * STEP, miny + j * STEP))]

def island_of(s, x, y):
    pt = Point(x, y)
    for k, g in enumerate(islands[s]):
        if g.buffer(0.01).contains(pt): return k
    return None
key = {}
for c in cands: key[c] = (island_of("F", *c), island_of("B", *c))
stitch = [tuple(p) for p in P["stitch"]]
skey = {p: (island_of("F", *p), island_of("B", *p)) for p in stitch}

chosen = []
def dist(c):
    k = key[c]
    pts = [p for p in stitch if skey[p] == k] + [p for p in chosen if key[p] == k]
    if not pts: return math.inf
    return min(math.hypot(c[0] - p[0], c[1] - p[1]) for p in pts)
def ok_spacing(c):            # chosen vias must also respect hole-to-hole among themselves
    return all(math.hypot(c[0] - p[0], c[1] - p[1]) >= 2 * 0.15 + H2H + 0.3 for p in chosen)
while True:
    best = max(((dist(c), c) for c in cands if ok_spacing(c)), default=(0, None))
    if best[1] is None or best[0] < TARGET: break
    chosen.append(best[1])

before = {}
for p in stitch: before[skey[p]] = before.get(skey[p], 0) + 1
after = dict(before)
for c in chosen: after[key[c]] = after.get(key[c], 0) + 1
print(f"{len(cands)} candidate spots, {len(chosen)} vias chosen")
for k in sorted(set(after), key=lambda k: tuple(-1 if v is None else v for v in k)):
    fa = islands["F"][k[0]].area if k[0] is not None else 0; ba = islands["B"][k[1]].area if k[1] is not None else 0
    print(f"  F island {k[0]} ({fa:.0f} mm2) x B island {k[1]} ({ba:.0f} mm2): {before.get(k, 0)} -> {after[k]}")
print("vias:", [(round(x, 2), round(y, 2)) for x, y in chosen])
json.dump([[round(x, 2), round(y, 2)] for x, y in chosen], open(sys.argv[2], "w"))
