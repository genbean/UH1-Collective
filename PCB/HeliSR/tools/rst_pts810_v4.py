# Rev 4.0, after finish_all_v4.py: the RST button as a C&K PTS810 on the front, between the AX1 port (J11) and the
# corner hole H4, where the RST track already runs on the back. It replaces the TL1015AF at the far end, whose metal
# frame sat over an AX4_SCL via and grounded it on the first board built, and whose frame tabs had no pads.
# The PTS810 has four pads (1-1 and 2-2 joined inside), so the whole body is soldered down; pads 1 are RST, 2 GND.
# Nothing but its own pads and a GND track is under it. The RST track is cut where it passes the switch: a via there
# and another above it, joined on the back, each with a short front track to a pad 1, and the old run to the far end
# removed. The RST label goes beside the switch and J7's, which sat where the switch is, moves along its socket.
# Then the pours are refilled. Run once on the board as routed with the button at the far end.
# usage: rst_pts810_v4.py <board in> <board out>   (KiCad 9's python)
import math, os, sys
import pcbnew

src, dst = sys.argv[1:3]
mm, FM = pcbnew.ToMM, pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "HeliSR.pretty")

CENTRE = (29.8, 29.5)        # between J11's courtyard (x <= 27.57) and H4's pad keep-out (x <= 32.0)
DIAG = ((27.299, 32.366), (33.123, 26.543))     # the back RST track through the spot, toward the far end
VIA_X = 27.95                                   # where it is cut: left of the switch, 0.74 mm hole to hole from the
                                                # GND via below it; only RST copper is closer
FAR_X = 32.9                                    # RST copper wholly right of this went to the old switch

b = pcbnew.LoadBoard(src)
rst, gnd = b.FindNet("RST"), b.FindNet("GND")

# ---- the switch ---------------------------------------------------------------------------------------------------
old = b.FindFootprintByReference("SW1")
assert old and old.GetValue().startswith("TL1015"), "SW1 is already replaced"
b.Remove(old)

fp = pcbnew.FootprintLoad(LIB, "SW_SPST_PTS810")
fp.SetReference("SW1"); fp.SetValue("PTS810 SJM 250 SMTR LFS")
b.Add(fp)
fp.SetPosition(V(*CENTRE))
# upright (pads in two columns), RST's column on the left, toward the via
fp.SetOrientationDegrees(90)
if min(mm(p.GetPosition().x) for p in fp.Pads() if p.GetNumber() == "1") > CENTRE[0]:
    fp.SetOrientationDegrees(270)
PADS = []                                       # (number, net, x, y), kept: the swig pad list doesn't survive edits
for p in fp.Pads():
    p.SetNet(rst if p.GetNumber() == "1" else gnd)
    PADS.append((p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y)))
BODY = None
for g in fp.GraphicalItems():
    if g.GetLayer() == pcbnew.F_Fab:
        r = g.GetBoundingBox()
        q = (mm(r.GetLeft()), mm(r.GetTop()), mm(r.GetRight()), mm(r.GetBottom()))
        BODY = q if BODY is None else (min(BODY[0], q[0]), min(BODY[1], q[1]), max(BODY[2], q[2]), max(BODY[3], q[3]))
ORIENT = fp.GetOrientationDegrees()
fp.Reference().SetVisible(False)

# ---- labels: J7's sat where the switch now is, and RST goes beside the switch ------------------------------------
# The same rules as silk_fix_v4.py: outside every front courtyard, clear of front pads, 0.5 mm from other labels.
def box(item_bb, grow=0.0):
    return (mm(item_bb.GetLeft()) - grow, mm(item_bb.GetTop()) - grow,
            mm(item_bb.GetRight()) + grow, mm(item_bb.GetBottom()) + grow)
def hit(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]
texts = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS]
labels = {d.GetText(): d for d in texts if d.GetText() in ("J7", "RST")}
fixed = []
outlines = []                                   # each front courtyard as edges, for inside tests
for f in b.GetFootprints():
    edges = []
    for g in f.GraphicalItems():
        if g.GetLayer() != pcbnew.F_CrtYd:
            continue
        if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = g.GetStart(), g.GetEnd()
            edges.append(((mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))))
        else:                                   # a circle or other shape: its bounding square, conservatively
            l, t, r, bt = box(g.GetBoundingBox())
            edges += [((l, t), (r, t)), ((r, t), (r, bt)), ((r, bt), (l, bt)), ((l, bt), (l, t))]
    if edges:
        outlines.append(edges)
        for (x0_, y0_), (x1_, y1_) in edges:    # the outline itself
            fixed.append((min(x0_, x1_) - 0.05, min(y0_, y1_) - 0.05, max(x0_, x1_) + 0.05, max(y0_, y1_) + 0.05))
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.F_Mask):
            fixed.append(box(p.GetBoundingBox(), 0.2))
for d in texts:
    if d.GetText() not in labels:
        fixed.append(box(d.GetBoundingBox(), 0.5))
fixed.append((BODY[0] - 0.25, BODY[1] - 0.25, BODY[2] + 0.25, BODY[3] + 0.25))    # the new switch's courtyard
inside = box(b.GetBoardEdgesBoundingBox(), -0.6)
def within(pt, edges):                          # ray casting to +x
    x, y = pt; n = 0
    for (xa, ya), (xb, yb) in edges:
        if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
            n += 1
    return n % 2 == 1
def in_courtyard(a):
    cx, cy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    return any(within((cx, cy), e) for e in outlines)
moved = {}
def put(name, near_xy, reach, angles):
    lab = labels[name]
    best = None
    for ang in angles:
        lab.SetTextAngleDegrees(ang)
        for i in range(-int(reach * 10), int(reach * 10) + 1):
            for j in range(-int(reach * 10), int(reach * 10) + 1):
                x, y = near_xy[0] + i * 0.1, near_xy[1] + j * 0.1
                lab.SetPosition(V(x, y))
                a = box(lab.GetBoundingBox())
                if a[0] < inside[0] or a[1] < inside[1] or a[2] > inside[2] or a[3] > inside[3]:
                    continue
                if any(hit(a, k) for k in fixed) or in_courtyard(a):
                    continue
                d = math.hypot(x - near_xy[0], y - near_xy[1]) + (0.5 if ang else 0)   # level text if it fits
                if best is None or d < best[0]:
                    best = (d, x, y, ang)
    assert best, f"no free spot for the {name} label"
    lab.SetTextAngleDegrees(best[3]); lab.SetPosition(V(best[1], best[2]))
    fixed.append(box(lab.GetBoundingBox(), 0.5))
    moved[name] = best[1:]
# RST first, beside its switch; then J7 nearest its old place (it names the Pro Micro socket, so anywhere
# along the socket reads right)
j7 = labels["J7"].GetPosition()
j7 = (mm(j7.x), mm(j7.y))
labels["J7"].SetPosition(V(-50, -50))           # off the board while RST looks for room
put("RST", CENTRE, 6.0, (0, 90))
put("J7", j7, 12.0, (0,))

# ---- RST: cut the back track at a via, join it to pad 1, drop the run to the far end ----------------------------
(x0, y0), (x1, y1) = DIAG
t = (VIA_X - x0) / (x1 - x0)
via_xy = (VIA_X, y0 + t * (y1 - y0))
near = lambda a, q: abs(mm(a.x) - q[0]) < 0.01 and abs(mm(a.y) - q[1]) < 0.01
removed = 0
for tr in list(b.GetTracks()):
    if tr.GetNetname() != "RST":
        continue
    if tr.Type() == pcbnew.PCB_VIA_T:
        if mm(tr.GetPosition().x) > FAR_X:
            b.Remove(tr); removed += 1
        continue
    if near(tr.GetStart(), DIAG[0]) and near(tr.GetEnd(), DIAG[1]):
        tr.SetEnd(V(*via_xy))
    elif near(tr.GetStart(), DIAG[1]) and near(tr.GetEnd(), DIAG[0]):
        tr.SetStart(V(*via_xy))
    elif min(mm(tr.GetStart().x), mm(tr.GetEnd().x)) > FAR_X:
        b.Remove(tr); removed += 1
def add_via(xy):
    v = pcbnew.PCB_VIA(b)
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetPosition(V(*xy)); v.SetDrill(FM(0.3)); v.SetNet(rst)
    b.Add(v)                                    # its size is set in the saved file below: KiCad 9's python saves 0
def track(a, c, layer):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(FM(0.2)); t.SetLayer(layer); t.SetNet(rst)
    b.Add(t)
# Both pads 1 get copper, none of it under the switch body. A front GND track runs diagonally between them (from
# J11's tab toward the far end), so the far pad is reached from a second via above that track, joined to the first on
# the back. (The switch joins its pads 1 inside too, but KiCad 9 can't be told so.)
ones = sorted((q for q in PADS if q[0] == "1"), key=lambda q: math.hypot(q[2] - via_xy[0], q[3] - via_xy[1]))
via2_xy = (VIA_X, ones[1][3] + 0.175)           # 1.2 mm from the VCC via above it, 2.1 mm from the GND track
add_via(via_xy)
add_via(via2_xy)
track(via_xy, (ones[0][2], ones[0][3]), pcbnew.F_Cu)
track(via_xy, via2_xy, pcbnew.B_Cu)
track(via2_xy, (ones[1][2], ones[1][3]), pcbnew.F_Cu)

b.Save(dst)
import re
s = open(dst, encoding="utf-8").read()
s, n = re.subn(r"(\(via\s*\(at [^)]*\)\s*)\(size 0\)", r"\g<1>(size 0.6)", s)    # the board's vias: 0.6 / 0.3 mm
assert n == 2, f"{n} vias of size 0 found, want the 2 new ones"
open(dst, "w", encoding="utf-8", newline="").write(s)

body = BODY
print(f"SW1 PTS810 at {CENTRE} rot {ORIENT:.0f}, body x {body[0]:.2f}-{body[2]:.2f} y {body[1]:.2f}-{body[3]:.2f}")
for q in PADS:
    print(f"  pad {q[0]} {q[1]} {q[2]:.3f},{q[3]:.3f}")
print(f"RST vias at {via_xy[0]:.3f},{via_xy[1]:.3f} and {via2_xy[0]:.3f},{via2_xy[1]:.3f}; "
      f"{removed} far-end RST items removed")
for name, (x, y, ang) in moved.items():
    print(f"label {name} now at {x:.1f},{y:.1f} angle {ang}")

# ---- refill the pours and check under the switch, in a fresh interpreter: after the edits above, KiCad's swig
# wrapper hands back bare objects for every board list in this one
import subprocess
FILL = """
import sys, pcbnew
mm = pcbnew.ToMM
dst = sys.argv[1]; body = [float(v) for v in sys.argv[2:6]]
b = pcbnew.LoadBoard(dst)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(dst)
under = []
for tr in b.GetTracks():
    via = tr.Type() == pcbnew.PCB_VIA_T
    if not via and tr.GetLayer() != pcbnew.F_Cu:
        continue
    r = tr.GetBoundingBox()
    if mm(r.GetLeft()) < body[2] and body[0] < mm(r.GetRight()) and mm(r.GetTop()) < body[3] and body[1] < mm(r.GetBottom()):
        if via or tr.GetNetname() != 'RST':
            under.append(tr.GetNetname() + (' via' if via else ' track'))
print('pours refilled; vias or front tracks under the switch body:', under or 'none')
"""
r = subprocess.run([sys.executable, "-I", "-c", FILL, dst] + [f"{v:.3f}" for v in body], capture_output=True, text=True)
print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "swig" not in l and "image handler" not in l))
if r.returncode:
    raise SystemExit("refill failed")
