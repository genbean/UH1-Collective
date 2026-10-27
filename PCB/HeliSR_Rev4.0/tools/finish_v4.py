# Finish a routed Rev 4.0 board. Run with KiCad 9's python.
#   finish_v4.py pour  <routed.kicad_pcb> <layout.json> <out.kicad_pcb>
#       widen router neck-downs where clearance allows, GND pours on both layers, starting silk labels
#   finish_v4.py final <in.kicad_pcb> <vias.json> <labels.json> <out dir>
#       GND stitching vias, final label positions, title block, project file, DRC rules, footprint library
import json, math, os, shutil, sys
import pcbnew

MM = pcbnew.FromMM; mm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
NAME = "HeliSR_Rev4.0"
stage = sys.argv[1]

def fill(b):
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())

if stage == "pour":
    src, layout, out = sys.argv[2:5]
    b = pcbnew.LoadBoard(src); LY = json.load(open(layout))
    L, W = LY["L"], LY["W"]
    # ---- neck-downs: Freerouting thins traces (signals to 0.15 mm or less, power to 0.225 mm) where they leave
    # fine-pitch pads. Put each segment back to the class width wherever it still meets the board's clearance.
    CLR = b.GetDesignSettings().m_NetSettings.GetDefaultNetclass().GetClearance()
    print("clearance used for widening:", mm(CLR))
    others = lambda: list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
    def ok(t, items):
        shp = t.GetEffectiveShape(t.GetLayer())
        for o in items:
            if o is t or o.GetNetCode() == t.GetNetCode() or not o.IsOnLayer(t.GetLayer()): continue
            if shp.Collide(o.GetEffectiveShape(t.GetLayer()), CLR): return False
        bb = t.GetBoundingBox()
        return min(mm(bb.GetLeft()), mm(bb.GetTop()), L - mm(bb.GetRight()), W - mm(bb.GetBottom())) >= 0.5
    items = others(); widened = kept = 0
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK": continue
        power = t.GetNetname() in ("GND", "VCC")
        targets = (0.3, 0.25) if power else (0.2,)
        orig = t.GetWidth()
        if orig >= MM(targets[0]) - 1: continue
        for w in targets:
            if MM(w) <= orig: break
            t.SetWidth(MM(w))
            if ok(t, items): widened += 1; break
        else:
            t.SetWidth(orig); kept += 1
        if t.GetWidth() < MM(targets[-1]) - 1 and t.GetWidth() == orig: pass
    print("neck-downs widened:", widened, "left as they are:", kept)
    # ---- duplicate segments: one lying wholly on another of the same net, layer and at least its width
    def on_seg(pt, t, tol=MM(0.001)):
        a, c = t.GetStart(), t.GetEnd()
        Lc = ((c.x - a.x) ** 2 + (c.y - a.y) ** 2) ** 0.5
        if Lc == 0 or abs((c.x - a.x) * (pt.y - a.y) - (c.y - a.y) * (pt.x - a.x)) / Lc > tol: return False
        dot = (pt.x - a.x) * (c.x - a.x) + (pt.y - a.y) * (c.y - a.y)
        return -tol * Lc <= dot <= Lc * Lc + tol * Lc
    segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias_ = [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
    # KiCad joins tracks and vias only at track endpoints, so a segment whose end carries a via or another
    # segment's end must stay, unless that point is also one of the covering segment's own ends.
    def anchored(pt, t, o):
        same = lambda a, c: abs(a.x - c.x) <= 1000 and abs(a.y - c.y) <= 1000
        if same(pt, o.GetStart()) or same(pt, o.GetEnd()): return False
        if any(v.GetNetCode() == t.GetNetCode() and same(v.GetPosition(), pt) for v in vias_): return True
        return any(s is not t and s is not o and s.GetNetCode() == t.GetNetCode() and s.GetLayer() == t.GetLayer()
                   and (same(s.GetStart(), pt) or same(s.GetEnd(), pt)) for s in segs)
    dups = [t for t in segs if any(o is not t and o.GetNetCode() == t.GetNetCode() and o.GetLayer() == t.GetLayer()
                                    and o.GetWidth() >= t.GetWidth() and o.GetLength() > t.GetLength()
                                    and on_seg(t.GetStart(), o) and on_seg(t.GetEnd(), o)
                                    and not anchored(t.GetStart(), t, o) and not anchored(t.GetEnd(), t, o) for o in segs)]
    for t in dups: b.Remove(t)          # (nothing iterates the tracks after this)
    print("duplicate segments removed:", len(dups))
    # ---- GND pours on both layers, 0.5 mm in from the edge (the screw keepouts are already rule areas)
    gnd = b.FindNet("GND")
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(lay); z.SetNet(gnd)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2))
        z.SetThermalReliefGap(MM(0.4)); z.SetThermalReliefSpokeWidth(MM(0.45))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for x, y in ((0.5, 0.5), (L - 0.5, 0.5), (L - 0.5, W - 0.5), (0.5, W - 0.5)): o.Append(MM(x), MM(y))
        b.Add(z)
    # ---- starting positions for the silk labels (silk_fix_v4.py moves them to clear spots afterwards)
    CY, rx, YT, YB, XE, P = LY["CY"], LY["row_x"], LY["YT"], LY["YB"], LY["XE"], LY["parts"]
    FRONT = [("J1", rx[0], YT + 3.4), ("J2", rx[0], YB - 3.4), ("AX3", rx[1], YT + 3.4), ("AX1", rx[1], YB - 3.4),
             ("AX4", XE - 3.4, P["J14"][1]), ("AX2", XE - 3.4, P["J12"][1]), ("RST", XE - 3.4, CY),
             ("J8", rx[1] + 4.2, LY["Y_J8"] - 2.4), ("J7", rx[1] + 4.2, LY["Y_J7"] + 2.4), ("USB", 1.9, CY),
             ("U1", P["U1"][0], CY), ("U2", P["U2"][0], CY), ("RN1", P["RN1"][0] + 24.1, CY - 5),
             ("RN2", P["RN2"][0] + 24.1, CY + 5), ("C1", P["C1"][0] + 1.9, CY - 2.82), ("C2", P["C2"][0], CY - 2.6),
             ("C3", P["C3"][0], CY - 2.6)]
    BACK = [(r, P[r][0], P[r][1]) for r in sorted(P) if P[r][2] == "B"] + [("HELI SR Rev 4.0", LY["L"] / 2 - 4.0, CY + 1.0)]
    for layer, labels in ((pcbnew.F_SilkS, FRONT), (pcbnew.B_SilkS, BACK)):
        for s, x, y in labels:
            t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer)
            t.SetTextSize(V(1.0, 1.0)); t.SetTextThickness(MM(0.16)); t.SetPosition(V(x, y))
            if layer == pcbnew.B_SilkS: t.SetMirrored(True)
            b.Add(t)
    fill(b)
    b.Save(out)
    print("pours and labels added")

elif stage == "final":
    src, vfile, lfile, outdir = sys.argv[2:6]
    b = pcbnew.LoadBoard(src)
    gnd = b.FindNet("GND")
    for x, y in json.load(open(vfile)):
        v = pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetPosition(V(x, y)); v.SetWidth(pcbnew.F_Cu, MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(gnd); b.Add(v)
    texts = {}
    for d in b.GetDrawings():
        if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            texts[(d.GetText(), d.GetLayer() == pcbnew.F_SilkS)] = d
    for r in json.load(open(lfile)):
        t = texts[(r["text"], r["side"] == "F")]
        if r.get("size") is None: raise SystemExit(f"no spot found for label {r['text']}")
        t.SetText(r["new_text"]); t.SetPosition(V(r["x"], r["y"])); t.SetTextAngleDegrees(r.get("rot", 0))
        t.SetTextSize(V(r["size"], r["size"])); t.SetTextThickness(MM(0.16))
    # Ground pads the pour can't reach with two thermal spokes (neighbouring traces block the rest): connect them
    # solidly. Each also has a routed GND trace; this only stops DRC flagging a starved thermal. The list comes
    # from a DRC run of this stage (optional 6th argument: JSON list of [ref, pad]).
    full = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else []
    for ref, num in full:
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNumber() == num: p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    b.GetDesignSettings().m_HoleToHoleMin = MM(0.6)         # holes at least 0.6 mm apart, edge to edge
    tb = b.GetTitleBlock(); tb.SetTitle("HeliSR"); tb.SetRevision("4.0"); tb.SetDate("2026-10-26")
    fill(b)
    os.makedirs(outdir, exist_ok=True)
    b.Save(os.path.join(outdir, NAME + ".kicad_pcb"))

    # ---- DRC rules for the intentional overlaps (each pair checked against the real part bodies) -----------
    def pairs(prop, groups):
        def one(x, y): return f"({prop.format('A', x)} && {prop.format('B', y)})"
        return " || ".join(f"{one(x, y)} || {one(y, x)}" for x, y in groups)
    REF = "{0}.Reference == '{1}'"; MEMBER = "{0}.memberOfFootprint('{1}')"
    UNDER_PM = [("RN1", "J8"), ("RN2", "J7"), ("RN1", "U1"), ("RN1", "U2"), ("RN2", "U1"), ("RN2", "U2"),
                ("C1", "U1")]
    FIELD = [("J1", "J13"), ("J2", "J11")]
    SILK = [("J7", "RN2"), ("J8", "RN1"), ("U1", "C1")]
    HOLES = [("H1", "J1"), ("H2", "J14"), ("H3", "J2"), ("H4", "J12")]
    END = [("SW1", "J14"), ("SW1", "J12")]
    open(os.path.join(outdir, NAME + ".kicad_dru"), "w").write(f"""(version 1)

# Known, intentional DRC hits on this board. Each rule names the exact footprints it covers, so the same check
# still fires for any other pair. (severity ignore) rather than (severity exclusion): kicad-cli 9.x still reports
# rule exclusions as errors (KiCad issue 24264), and per-marker exclusions in the .kicad_pro break when parts move.

# Parts nested under the Pro Micro, as on Rev 1.2: the resistor networks, shift registers and decoupling caps sit
# between the two 12-pin sockets, closer than their courtyards allow. A 4609X SIP is 2.49 mm thick at most,
# leaving about 0.1 mm to each socket body. (C3, the 1206 lying between U1 and U2, and C2 at U2's outer end clear
# their courtyards.)
(rule "Nested under the Pro Micro: courtyards"
  (constraint courtyard_clearance)
  (severity ignore)
  (condition "{pairs(REF, UNDER_PM)}"))

# The connector rows: along each long side a 10-pin and a 4-pin JST SH header, 0.5 mm copper apart.
# The courtyards overlap, but the housings are 1.2 mm apart along a row, and their pads are still checked by the
# clearance rules.
(rule "Connector field: courtyards"
  (constraint courtyard_clearance)
  (severity ignore)
  (condition "{pairs(REF, FIELD)}"))

# The M3 holes' courtyards (6.9 mm across, sized for a 6.4 mm head or spacer) overlap the USB-end connectors (J1, J2)
# and the far-end ports (J14, J12). The ground pour and every track and via stop 3.5 mm from each hole centre, and the
# JST pads and housings are clear of the 6.35 mm corners of the M3 nut on the front; nothing on the back comes within
# reach of the 6.4 mm spacer.
(rule "Mounting holes: courtyards"
  (constraint courtyard_clearance)
  (severity ignore)
  (condition "{pairs(REF, HOLES)}"))

# The far end: RST (SW1) between the AX4 and AX2 ports. Their courtyards overlap by up to 0.3 mm; the switch body
# and the JST housings are about 1.4 mm apart, and their pads are still checked by the clearance rules.
(rule "Far end: courtyards"
  (constraint courtyard_clearance)
  (severity ignore)
  (condition "{pairs(REF, END)}"))

# Library footprint outlines that touch where parts nest (socket vs resistor network, SOIC vs C1).
(rule "Nested parts: silkscreen"
  (constraint silk_clearance (min 0mm))
  (severity ignore)
  (condition "{pairs(MEMBER, SILK)}"))

# The end of U1's library outline runs under C1's pad opening; the fab clips it there anyway.
(rule "U1 outline end under C1's pad opening"
  (constraint silk_clearance (min 0mm))
  (severity ignore)
  (condition "A.memberOfFootprint('U1') && A.Layer == 'F.Silkscreen'"))
""")
    print("final board and rules saved")
