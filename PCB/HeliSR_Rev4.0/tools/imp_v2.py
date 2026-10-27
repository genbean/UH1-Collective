# Import a Freerouting session (all nets) into the board, drop the routing keepout border, save.
# Run with KiCad 9's python. usage: imp_v2.py <in.kicad_pcb> <in.ses> <out.kicad_pcb>
import re, sys
import pcbnew

src, ses, dst = sys.argv[1:4]
b = pcbnew.LoadBoard(src); MM = pcbnew.FromMM
body = open(ses).read()
res = re.search(r"\(resolution\s+(\w+)\s+(\d+)\)", body)
unit_nm = {"um": 1000.0, "mm": 1e6, "mil": 25400.0, "inch": 2.54e7}[res.group(1)] / int(res.group(2))
U = lambda v: int(round(float(v) * unit_nm))
body = body[body.index("(network_out"):]

def blocks(s, head):
    out, i = [], 0
    while True:
        i = s.find(head, i)
        if i < 0: return out
        d = 0
        for j in range(i, len(s)):
            if s[j] == "(": d += 1
            elif s[j] == ")":
                d -= 1
                if d == 0: out.append(s[i:j + 1]); i = j + 1; break

n_tr = n_via = 0
for nb in blocks(body, "(net "):
    name = re.match(r'\(net\s+"?([^\s"()]+)"?', nb).group(1)
    net = b.FindNet(name)
    assert net is not None, name
    for wb in blocks(nb, "(path "):
        toks = wb.strip("()").split()
        layer, width, xy = toks[1], U(toks[2]), toks[3:]
        pts = [(U(xy[k]), -U(xy[k + 1])) for k in range(0, len(xy) - 1, 2)]
        for a, z in zip(pts, pts[1:]):
            if a == z: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(*a)); t.SetEnd(pcbnew.VECTOR2I(*z))
            t.SetWidth(width); t.SetLayer(pcbnew.F_Cu if layer == "F.Cu" else pcbnew.B_Cu); t.SetNet(net); b.Add(t); n_tr += 1
    for vx, vy in re.findall(r'\(via\s+"[^"]*"\s+(-?[\d.]+)\s+(-?[\d.]+)', nb):
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(U(vx), -U(vy)))
        v.SetWidth(pcbnew.F_Cu, MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(net); b.Add(v); n_via += 1
for z in [z for z in b.Zones()]:
    if z.GetIsRuleArea() and z.GetZoneName() == "ROUTE_KEEPOUT": b.Remove(z)
b.BuildConnectivity()
b.Save(dst)
print("imported", n_tr, "segments", n_via, "vias")
