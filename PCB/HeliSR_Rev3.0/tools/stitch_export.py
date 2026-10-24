# Export what a GND stitching-via search needs: GND fill per layer, holes, pads, silk labels,
# existing stitch points. Runs under KiCad's python. usage: stitch_export.py <board> <out.json>
import sys, json
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1]); MM = pcbnew.FromMM; mm = pcbnew.ToMM; ERR = MM(0.005)

def polys(ps):
    ps = ps.CloneDropTriangulation(); ps.Fracture()
    return [[[mm(o.CPoint(k).x), mm(o.CPoint(k).y)] for k in range(o.PointCount())]
            for o in (ps.Outline(i) for i in range(ps.OutlineCount()))]
def item_poly(it, layer):
    ps = pcbnew.SHAPE_POLY_SET(); it.TransformShapeToPolygon(ps, layer, 0, ERR, pcbnew.ERROR_OUTSIDE); return polys(ps)

if "--keep-islands" in sys.argv:            # see the whole pour, including islands not yet tied to GND
    for z in b.Zones():
        if not z.GetIsRuleArea(): z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
fills = {}
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetNetname() == "GND":
        for lay in z.GetLayerSet().Seq():
            fills["F" if lay == pcbnew.F_Cu else "B"] = polys(z.GetFilledPolysList(lay))
holes, stitch, pads, courtyards = [], [], [], {}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSize().x > 0:
            holes.append([mm(p.GetPosition().x), mm(p.GetPosition().y), mm(p.GetDrillSize().x) / 2])
            if p.GetNetname() == "GND": stitch.append([mm(p.GetPosition().x), mm(p.GetPosition().y)])
        for side, lay in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
            if p.IsOnLayer(lay): pads.append({"side": side, "net": p.GetNetname(), "poly": item_poly(p, lay)})
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    courtyards[f.GetReference()] = polys(cy)
for v in b.GetTracks():
    if v.GetClass() == "PCB_VIA":
        holes.append([mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetDrillValue()) / 2])
        if v.GetNetname() == "GND": stitch.append([mm(v.GetPosition().x), mm(v.GetPosition().y)])
labels = {"F": [], "B": []}
for d in ([] if "--no-labels" in sys.argv else b.GetDrawings()):      # --no-labels: vias first, labels move later
    if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        labels["F" if d.GetLayer() == pcbnew.F_SilkS else "B"] += item_poly(d, d.GetLayer())
json.dump({"fills": fills, "holes": holes, "stitch": stitch, "pads": pads, "labels": labels, "courtyards": courtyards},
          open(sys.argv[2], "w"))
print({k: len(v) for k, v in fills.items()}, "holes", len(holes), "stitch points", len(stitch))
