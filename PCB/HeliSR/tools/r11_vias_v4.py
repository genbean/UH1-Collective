# HeliSR Rev 4.0, on the routed board: no via under R11, and the GND pours stitched where they were cut off.
# On the first board built, solder paste ran along R11's underside onto the AX4 SCL via between its pads. This takes
# out every via under the courtyards of PARTS (R11's three: two AX4_SCL and one VCC), and only the tracks
# left dangling after that; everything else stays as routed, locked, while Freerouting reconnects the gaps. The
# courtyards stay in the board as via-only rule areas, so KiCad's DRC keeps vias out of them. Then the pours are
# refilled and stitch_v4.py adds GND vias wherever a patch of pour has none, under its rules (no SMD courtyards,
# 0.45 mm from pads, 0.6 mm between vias).
# Steps run in fresh KiCad pythons (swig loses the board's lists after edits).
# usage: r11_vias_v4.py <work dir with HeliSR_Rev4.0.kicad_pcb/.kicad_pro/.kicad_dru> <freerouting.jar> <java.exe>
import json, math, os, re, shutil, subprocess, sys
import pcbnew
try:                                           # KiCad's internal checks (wx asserts) log instead of opening a dialog
    import wx; wx.DisableAsserts()
except Exception:
    pass

mm, MM = pcbnew.ToMM, pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "HeliSR_Rev4.0"
PARTS = ("R11",)                               # the parts whose courtyards get no vias (every R/C/SW was unroutable)

def box(r, grow=0.0):
    return (mm(r.GetLeft()) - grow, mm(r.GetTop()) - grow, mm(r.GetRight()) + grow, mm(r.GetBottom()) + grow)
def pt_gap(x, y, c):
    return math.hypot(max(c[0] - x, 0, x - c[2]), max(c[1] - y, 0, y - c[3]))
def courtyard(f):
    bs = [box(g.GetBoundingBox()) for g in f.GraphicalItems() if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)]
    return (min(q[0] for q in bs), min(q[1] for q in bs), max(q[2] for q in bs), max(q[3] for q in bs)) if bs else None
def zone(b, name, rect, tracks=False):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for px, py in ((rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])): o.Append(MM(px), MM(py))
    b.Add(z)

def prep(src, dst):
    b = pcbnew.LoadBoard(src)
    fps = list(b.GetFootprints())
    rules = [(f.GetReference(), courtyard(f)) for f in fps if f.GetReference() in PARTS and courtyard(f)]
    items, pads = [], []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            items.append(dict(o=t, via=True, net=t.GetNetname(), x=mm(t.GetPosition().x), y=mm(t.GetPosition().y),
                              r=mm(t.GetWidth(pcbnew.F_Cu)) / 2))
        else:
            items.append(dict(o=t, via=False, net=t.GetNetname(), layer=t.GetLayer(), w=mm(t.GetWidth()) / 2,
                              a=(mm(t.GetStart().x), mm(t.GetStart().y)), c=(mm(t.GetEnd().x), mm(t.GetEnd().y))))
    for f in fps:
        for p in f.Pads():
            pads.append(dict(net=p.GetNetname(), box=box(p.GetBoundingBox()),
                             F=p.IsOnLayer(pcbnew.F_Cu), B=p.IsOnLayer(pcbnew.B_Cu)))
    bad = [i for i in items if i["via"] and any(pt_gap(i["x"], i["y"], rc) < i["r"] for _, rc in rules)]
    for v in bad:
        under = [n for n, rc in rules if pt_gap(v["x"], v["y"], rc) < v["r"]]
        print(f"  {v['net']} via at {v['x']:.2f},{v['y']:.2f} under {', '.join(under)}")
    gone = {id(v["o"]) for v in bad}
    def on_seg(p, s):
        (ax, ay), (cx, cy) = s["a"], s["c"]; L2 = (cx - ax) ** 2 + (cy - ay) ** 2
        t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * (cx - ax) + (p[1] - ay) * (cy - ay)) / L2))
        return math.hypot(p[0] - ax - t * (cx - ax), p[1] - ay - t * (cy - ay)) <= s["w"] + 0.01
    nets = {v["net"] for v in bad}
    while True:                                # tracks of those nets left with a free end: out too, until none is
        alive = [i for i in items if id(i["o"]) not in gone and i["net"] in nets]
        dang = []
        for s in alive:
            if s["via"]: continue
            for end in (s["a"], s["c"]):
                ok = any(v["via"] and math.hypot(v["x"] - end[0], v["y"] - end[1]) <= v["r"] for v in alive if v["net"] == s["net"])
                ok = ok or any(t is not s and not t["via"] and t["net"] == s["net"] and t["layer"] == s["layer"]
                               and on_seg(end, t) for t in alive)
                ok = ok or any(p["net"] == s["net"] and p["F" if s["layer"] == pcbnew.F_Cu else "B"]
                               and pt_gap(end[0], end[1], p["box"]) <= 0.01 for p in pads)
                if not ok: dang.append(id(s["o"])); break
        if not dang: break
        gone |= set(dang)
    print(f"  {len(bad)} vias under {', '.join(PARTS)}; {len(gone)} tracks and vias out")
    for n, rc in rules: zone(b, "NO_VIA_" + n, rc)
    edge = box(b.GetBoardEdgesBoundingBox())
    for r in ((edge[0], edge[1], edge[2], edge[1] + 0.5), (edge[0], edge[3] - 0.5, edge[2], edge[3]),
              (edge[0], edge[1], edge[0] + 0.5, edge[3]), (edge[2] - 0.5, edge[1], edge[2], edge[3])):
        zone(b, "ROUTE_KEEPOUT", r, tracks=True)   # the router's 0.5 mm border; imp_v2.py removes it again
    for i in items:
        if id(i["o"]) in gone: b.Remove(i["o"])
    b.Save(dst)

def export(src, dsn, via_um):
    b = pcbnew.LoadBoard(src)
    for t in b.GetTracks(): t.SetLocked(True)
    b.Save(src)
    b = pcbnew.LoadBoard(src)
    assert pcbnew.ExportSpecctraDSN(b, dsn), "DSN export failed"
    s = open(dsn).read()
    m = re.search(r"\(class kicad_default (.*?)\(circuit", s, re.S)
    rest = [n for n in m.group(1).split() if n not in ("GND", "VCC")]
    s = s[:m.start(1)] + " ".join(rest) + "\n      " + s[m.end(1):]
    end = s.index("\n    )\n", m.start()) + len("\n    )\n")
    s = s[:end] + ("    (class power GND VCC\n      (circuit\n        (use_via \"Via[0-1]_600:300_um\")\n      )\n"
                   "      (rule\n        (width 300)\n        (clearance 200)\n      )\n    )\n") + s[end:]
    via = '(padstack "Via[0-1]_600:300_um"\n      (shape (circle F.Cu 600))\n      (shape (circle B.Cu 600))'
    assert via in s
    open(dsn, "w").write(s.replace(via, via.replace("600))", f"{via_um}))")))

def dedupe(src):
    b = pcbnew.LoadBoard(src)
    seen, dup, widened = set(), [], 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            k = ("v", t.GetNetname(), round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3))
        else:
            want = MM(0.3 if t.GetNetname() in ("GND", "VCC") else 0.2)
            if t.GetWidth() < want: t.SetWidth(want); widened += 1     # the router's neck-downs back to full width
            e = sorted([(round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)),
                        (round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3))])
            k = ("t", t.GetNetname(), t.GetLayer(), tuple(e), round(mm(t.GetWidth()), 3))
        if k in seen: dup.append(t)
        else: seen.add(k); t.SetLocked(False)
    for t in dup: b.Remove(t)
    b.Save(src)
    print(f"  {len(dup)} repeated tracks and vias dropped, {widened} neck-downs widened")

def fill(src):
    b = pcbnew.LoadBoard(src)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(src)

def add_vias(src, vfile):
    b = pcbnew.LoadBoard(src)
    gnd = b.FindNet("GND")
    pts = json.load(open(vfile))
    for x, y in pts:
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y))
        v.SetWidth(pcbnew.F_Cu, MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(gnd); b.Add(v)
    b.Save(src)
    print(f"  {len(pts)} GND stitching vias added: {pts}")

def islands(src):
    """how much GND pour there is (mm2 per layer), to compare before and after"""
    b = pcbnew.LoadBoard(src)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND": continue
        for lay, name in ((pcbnew.F_Cu, "front"), (pcbnew.B_Cu, "back")):
            if z.IsOnLayer(lay):
                ps = z.GetFilledPolysList(lay)
                print(f"  GND pour, {name}: {ps.OutlineCount()} pieces, {mm(mm(ps.Area())):.0f} mm2")

if len(sys.argv) > 2 and sys.argv[1] == "stage":
    st, a = sys.argv[2], sys.argv[3:]
    {"prep": lambda: prep(*a), "export": lambda: export(a[0], a[1], int(a[2])), "dedupe": lambda: dedupe(*a),
     "fill": lambda: fill(*a), "add_vias": lambda: add_vias(*a), "islands": lambda: islands(*a)}[st]()
    sys.exit(0)

work, JAR, JAVA = sys.argv[1:4]
KPY = sys.executable
KCLI = os.path.join(os.path.dirname(KPY), "kicad-cli.exe")
quiet = lambda s: "\n".join(l for l in s.splitlines() if "swig" not in l and "image handler" not in l and l.strip())
me = os.path.abspath(__file__)
def run(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    out = quiet(r.stdout + r.stderr)
    if out: print(out, flush=True)
    if check and r.returncode: raise SystemExit("FAILED: " + " ".join(os.path.basename(x) for x in args[2:4]))
    return r
src = os.path.join(work, NAME + ".kicad_pcb")
print("== before"); run([KPY, "-I", me, "stage", "islands", src])
base = os.path.join(work, "prepped.kicad_pcb")
print("== vias out"); run([KPY, "-I", me, "stage", "prep", src, base])
for via_um in (700, 800, 900, 750, 850):
    print(f"\n== reconnecting, vias routed at {via_um / 1000} mm")
    d = os.path.join(work, f"v{via_um}"); os.makedirs(d, exist_ok=True)
    pcb = os.path.join(d, NAME + ".kicad_pcb")
    shutil.copy(base, pcb)
    for ext in (".kicad_pro", ".kicad_dru"): shutil.copy(os.path.join(work, NAME + ext), os.path.join(d, NAME + ext))
    dsn, ses = os.path.join(d, "fix.dsn"), os.path.join(d, "fix.ses")
    run([KPY, "-I", me, "stage", "export", pcb, dsn, str(via_um)])
    r = subprocess.run([JAVA, "-Djava.awt.headless=true", "-jar", JAR, "-de", dsn, "-do", ses, "-mp", "100", "-mt", "1",
                        "--gui.enabled=false"], capture_output=True, text=True, timeout=1500)
    log = r.stdout + r.stderr; open(os.path.join(d, "freerouting.log"), "w").write(log)
    print("  " + (re.findall(r"Auto-routing stage completed.*", log) or ["router: no summary"])[-1][:160])
    if not os.path.exists(ses): continue
    routed = os.path.join(d, "routed.kicad_pcb")
    run([KPY, "-I", os.path.join(HERE, "imp_v2.py"), pcb, ses, routed])
    shutil.copy(routed, pcb)
    run([KPY, "-I", me, "stage", "dedupe", pcb])
    run([KPY, "-I", me, "stage", "fill", pcb])
    vj = os.path.join(d, "stitch.json")
    run([KPY, "-I", os.path.join(HERE, "stitch_v4.py"), pcb, vj, "5.0"])
    run([KPY, "-I", me, "stage", "add_vias", pcb, vj])
    run([KPY, "-I", me, "stage", "fill", pcb])
    rpt = os.path.join(d, "drc.json")
    run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, pcb], check=False)
    j = json.load(open(rpt))
    errs = [v for v in j["violations"] if v["severity"] == "error"]
    print(f"  DRC: {len(errs)} errors, {len(j['violations']) - len(errs)} warnings, {len(j['unconnected_items'])} unconnected")
    for v in j["violations"][:10]:
        print("    ", v["severity"], v["type"], "|", "; ".join(i["description"] for i in v["items"])[:140])
    if not errs and not j["unconnected_items"]:
        print("\n== after"); run([KPY, "-I", me, "stage", "islands", pcb])
        print("RESULT", pcb); sys.exit(0)
print("RESULT none")
