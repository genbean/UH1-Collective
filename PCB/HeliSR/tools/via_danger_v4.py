# The vias that can bridge to another net: within 0.5 mm (copper) of an SMD pad of a different net (paste goes on
# those), or under a resistor, capacitor or switch body (between its pads' outer edges). Round through-hole pads
# are measured as circles. Tracks ending on each via are listed, and whether it's a bare stitching via.
# usage: danger.py <board>
import math, sys
import pcbnew
try:
    import wx; wx.DisableAsserts()
except Exception:
    pass
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
pads, bodies = [], []
for f in b.GetFootprints():
    ref = f.GetReference()
    side = "B" if f.IsFlipped() else "F"
    ps = list(f.Pads())
    if ref[0] in "RCS" and not ref.startswith("RN") and len(ps) >= 2:
        bb = [p.GetBoundingBox() for p in ps]
        bodies.append((ref, min(mm(r.GetLeft()) for r in bb), min(mm(r.GetTop()) for r in bb),
                       max(mm(r.GetRight()) for r in bb), max(mm(r.GetBottom()) for r in bb)))
    for p in ps:
        bb = p.GetBoundingBox()
        th = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        pads.append((f"{ref}.{p.GetNumber()}", p.GetNetname(), th, mm(p.GetPosition().x), mm(p.GetPosition().y),
                     mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()),
                     p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE))
tracks = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T]
n = 0
for v in b.GetTracks():
    if v.Type() != pcbnew.PCB_VIA_T: continue
    x, y, net = mm(v.GetPosition().x), mm(v.GetPosition().y), v.GetNetname()
    why = []
    for p in pads:
        if p[1] == net or p[2]: continue                     # same net, or through-hole (no paste)
        d = math.hypot(max(p[5] - x, 0, x - p[7]), max(p[6] - y, 0, y - p[8])) - 0.3
        if d < 0.5: why.append(f"{p[0]}({p[1]}) {d:.2f}")
    for r, x0, y0, x1, y1 in bodies:
        if x0 < x < x1 and y0 < y < y1: why.append(f"under {r}")
    if not why: continue
    n += 1
    own = [t for t in tracks if t.GetNetname() == net and
           (abs(mm(t.GetStart().x) - x) < 0.01 and abs(mm(t.GetStart().y) - y) < 0.01 or
            abs(mm(t.GetEnd().x) - x) < 0.01 and abs(mm(t.GetEnd().y) - y) < 0.01)]
    kind = "stitch" if not own else f"{len(own)} tracks"
    print(f"{net:9} {x:.3f},{y:.3f}  {kind:9} | " + "; ".join(why))
print(f"{n} vias")
