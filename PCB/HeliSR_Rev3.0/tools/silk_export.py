# Export silk-label placement problem: label outlines per candidate size, and obstacles per side.
# Runs under KiCad's python. usage: silk_export.py <board> <out.json>
import sys, json, math
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.FromMM; mm = pcbnew.ToMM
ERR = MM(0.005)
SIZES = [(1.0, 0.16), (0.8, 0.16)]
RENAME = {"HELI SR Rev 1.1": "HELI SR Rev 1.1a", "HELI SR Rev 1.1a": "HELI SR Rev 1.2"}


def polys(ps):
    ps = ps.CloneDropTriangulation(); ps.Fracture()
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append([[mm(o.CPoint(k).x), mm(o.CPoint(k).y)] for k in range(o.PointCount())])
    return out


def item_poly(it, layer, clr=0.0):
    ps = pcbnew.SHAPE_POLY_SET()
    it.TransformShapeToPolygon(ps, layer, MM(clr), ERR, pcbnew.ERROR_OUTSIDE)
    return polys(ps)


labels = []
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT" or d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        continue
    side = "F" if d.GetLayer() == pcbnew.F_SilkS else "B"
    pos = d.GetPosition()
    ent = {"text": d.GetText(), "new_text": RENAME.get(d.GetText(), d.GetText()), "side": side,
           "x": mm(pos.x), "y": mm(pos.y), "h": mm(d.GetTextHeight()), "t": mm(d.GetTextThickness()), "shapes": {}}
    for h, t in SIZES:
        for rot in (0, 90):
            c = d.Duplicate()
            c.SetText(ent["new_text"])
            c.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); c.SetTextThickness(MM(t))
            c.SetTextAngleDegrees(rot); c.SetPosition(pcbnew.VECTOR2I(0, 0))
            ent["shapes"][f"{h}" + ("r" if rot else "")] = item_poly(c, d.GetLayer())
    c = d.Duplicate(); c.SetPosition(pcbnew.VECTOR2I(0, 0)); ent["cur"] = item_poly(c, d.GetLayer())
    labels.append(ent)

obst = {"F": {"mask": [], "silk": [], "via": []}, "B": {"mask": [], "silk": [], "via": []}}
for f in b.GetFootprints():
    for p in f.Pads():
        for side, ml in (("F", pcbnew.F_Mask), ("B", pcbnew.B_Mask)):
            if p.IsOnLayer(ml):
                obst[side]["mask"] += item_poly(p, ml)
        if p.GetDrillSize().x > 0:                 # holes cut through silk on both sides
            for side in "FB":
                ps = pcbnew.SHAPE_POLY_SET()
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:   # mounting hole: keep clear of the screw head
                    c = p.GetPosition()                          # M2 head 3.8 mm; M3 nut / spacer 6.4 mm
                    r = 3.4 if mm(p.GetDrillSize().x) > 3.0 else 2.2
                    obst[side]["mask"].append([[mm(c.x) + r * math.cos(a * math.pi / 16), mm(c.y) + r * math.sin(a * math.pi / 16)] for a in range(32)])
                    continue
                p.TransformHoleToPolygon(ps, 0, ERR, pcbnew.ERROR_OUTSIDE)
                obst[side]["mask"] += polys(ps)
    for g in f.GraphicalItems():
        for side, sl in (("F", pcbnew.F_SilkS), ("B", pcbnew.B_SilkS)):
            if g.GetLayer() == sl and (g.GetClass() != "PCB_TEXT" or g.IsVisible()):
                obst[side]["silk"] += item_poly(g, sl)
    for side, sl in (("F", pcbnew.F_SilkS), ("B", pcbnew.B_SilkS)):
        for t in (f.Reference(), f.Value()):
            if t.IsVisible() and t.GetLayer() == sl:
                obst[side]["silk"] += item_poly(t, sl)
for d in b.GetDrawings():                            # non-text board silk (none expected, but be safe)
    if d.GetClass() != "PCB_TEXT":
        for side, sl in (("F", pcbnew.F_SilkS), ("B", pcbnew.B_SilkS)):
            if d.GetLayer() == sl:
                obst[side]["silk"] += item_poly(d, sl)
for v in b.GetTracks():
    if v.GetClass() == "PCB_VIA":
        p = v.GetPosition(); r = mm(v.GetWidth(pcbnew.F_Cu)) / 2
        for side in "FB":
            obst[side]["via"].append([mm(p.x), mm(p.y), r])
bb = b.GetBoardEdgesBoundingBox()
json.dump({"labels": labels, "obst": obst,
           "board": [mm(bb.GetLeft()) + 0.05, mm(bb.GetTop()) + 0.05, mm(bb.GetRight()) - 0.05, mm(bb.GetBottom()) - 0.05]},
          open(sys.argv[2], "w"))
print("labels", len(labels), {s: {k: len(v) for k, v in o.items()} for s, o in obst.items()})
