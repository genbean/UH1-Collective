# SearchHat Rev 1.0: a breakout board for the SEARCH CONT hat (head Rev 5, hat Rev 4). It carries an ALPS RKJXM1015004
# 8-direction stick switch on its front, facing the lower panel, and screws to four bosses printed on the panel's
# back (M2 x 8 countersunk, from behind). Its back has a 6-pin JST SH socket (side entry, the cable leaving
# upward), and along the bottom a row of six 2 mm plated holes to solder wires to instead.
#
# The switch: the directions' common is its PUSH terminal (three pins, joined inside); the centre push joins COM to
# PUSH. So PUSH and the frame's GND pin go to GND, A-D are the four directions and COM is the centre push. Looking
# at the board's front (as you look at the panel), A is up (EXT), C down (RETR), B left (L), D right (R).
#
# Frame: the board's own, in mm; u right and v up as seen from the front, the switch at u = v = 0. KiCad's X, Y
# (Y down, looking at the front) are X = SX + u, Y = SY - v. Every route below is hand-placed in (u, v).
#
# Run with KiCad 9's python. usage: gen_searchhat.py <out dir>
# Writes <out dir>/SearchHat_Rev1.0.kicad_pcb, .kicad_pro, .kicad_dru and SearchHat_Rev1.0_mech.json (outline,
# holes and parts in (u, v), for hat4_r5.py).
import json, math, os, shutil, sys
import pcbnew

OUT = sys.argv[1]
NAME = "SearchHat_Rev1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
FP = os.path.join(os.path.dirname(pcbnew.__file__), "..", "..", "..", "share", "kicad", "footprints")
MM = pcbnew.FromMM; mm = pcbnew.ToMM

# ---- outline and placement, in (u, v) -------------------------------------------------------------------------
U0, U1, V0, V1 = -11.0, 11.0, -15.0, 14.0    # 22 x 29 mm
CORNER = 2.0
SX, SY = -U0, V1
XY = lambda u, v: pcbnew.VECTOR2I(MM(SX + u), MM(SY - v))
HOLES = [(-8.5, 8.5), (8.5, 8.5), (-8.5, -8.5), (8.5, -8.5)]   # M2 clearance, 2.2 mm, NPTH
HEAD_R = 2.2                                 # copper keepout round each hole: an M2 countersunk head is 3.8 mm across
J1_V = 10.725                                # J1's origin: its mounting tabs end 0.5 mm in from the top edge
J1_PAD_V = J1_V - 2.0                        # its signal pads' centres
J2_V = -9.5                                  # J2's row (2 mm pitch, u = -5 ... 5)
SIG_W, CLR = 0.3, 0.2

b = pcbnew.BOARD()
b.GetDesignSettings().SetCopperLayerCount(2)

def seg(layer, a, c, w=0.1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(MM(w))
    s.SetStart(XY(*a)); s.SetEnd(XY(*c)); b.Add(s)
def arc(layer, centre, start, angle, w=0.1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(layer); s.SetWidth(MM(w))
    s.SetCenter(XY(*centre)); s.SetStart(XY(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T), True)
    b.Add(s)

r = CORNER
seg(pcbnew.Edge_Cuts, (U0 + r, V1), (U1 - r, V1)); seg(pcbnew.Edge_Cuts, (U1, V1 - r), (U1, V0 + r))
seg(pcbnew.Edge_Cuts, (U1 - r, V0), (U0 + r, V0)); seg(pcbnew.Edge_Cuts, (U0, V0 + r), (U0, V1 - r))
# corner arcs (KiCad's Y is down, so a positive angle runs clockwise as drawn)
arc(pcbnew.Edge_Cuts, (U1 - r, V1 - r), (U1 - r, V1), 90)
arc(pcbnew.Edge_Cuts, (U1 - r, V0 + r), (U1, V0 + r), 90)
arc(pcbnew.Edge_Cuts, (U0 + r, V0 + r), (U0 + r, V0), 90)
arc(pcbnew.Edge_Cuts, (U0 + r, V1 - r), (U0, V1 - r), 90)

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    return nets[name]

def place(libdir, name, ref, u, v, rot=0, value="", back=False):
    f = pcbnew.FootprintLoad(libdir, name)
    f.SetReference(ref); f.SetValue(value or name)
    f.Value().SetVisible(False)
    b.Add(f); f.SetPosition(XY(u, v)); f.SetOrientationDegrees(rot)
    if back: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    return f

def uv(p):
    q = p.GetPosition(); return round(mm(q.x) - SX, 4), round(SY - mm(q.y), 4)

# ---- parts ------------------------------------------------------------------------------------------------------
SW = place(os.path.join(PROJ, "SearchHat.pretty"), "SW_ALPS_RKJXM1015004", "SW1", 0, 0, 0, "ALPS RKJXM1015004")
SW_NET = {"1": "CTR", "2": "EXT", "3": "L", "4": "RETR", "5": "R", "6": "GND", "7": "GND"}
for p in SW.Pads():
    if p.GetNumber(): p.SetNet(net(SW_NET[p.GetNumber()]))

J1 = place(os.path.join(FP, "Connector_JST.pretty"), "JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal", "J1",
           0, J1_V, 180, "JST SM06B-SRSS-TB", back=True)
# after turning and flipping, pin 1 is at u = -2.5 and pin 6 at u = +2.5 (left to right as seen from the front)
J1_NET = {"1": "R", "2": "GND", "3": "RETR", "4": "CTR", "5": "EXT", "6": "L", "MP": "GND"}
for p in J1.Pads(): p.SetNet(net(J1_NET[p.GetNumber()]))

J2 = place(os.path.join(FP, "Connector_PinHeader_2.00mm.pretty"), "PinHeader_1x06_P2.00mm_Vertical", "J2",
           -5.0, J2_V, 90, "Wire pads, 2 mm")
J2_NET = {"1": "R", "2": "RETR", "3": "GND", "4": "EXT", "5": "CTR", "6": "L"}
for p in J2.Pads(): p.SetNet(net(J2_NET[p.GetNumber()]))

for i, (hu, hv) in enumerate(HOLES):
    place(os.path.join(FP, "MountingHole.pretty"), "MountingHole_2.2mm_M2", f"H{i + 1}", hu, hv, 0, "M2")

# check where the library put things
PADS = {}
for f in (SW, J1, J2):
    for p in f.Pads():
        if p.GetNumber(): PADS.setdefault(f.GetReference() + "-" + p.GetNumber(), []).append(uv(p))
exp = {"J1-1": (-2.5, J1_PAD_V), "J1-6": (2.5, J1_PAD_V), "J2-1": (-5.0, J2_V), "J2-6": (5.0, J2_V),
       "SW1-1": (1.0, 5.35), "SW1-2": (1.0, -4.95), "SW1-3": (4.95, 1.0), "SW1-4": (-1.0, 4.95), "SW1-5": (-4.95, -1.0)}
for k, (eu, ev) in exp.items():
    gu, gv = PADS[k][0]
    assert abs(gu - eu) < 0.01 and abs(gv - ev) < 0.01, (k, PADS[k], (eu, ev))

# ---- routes ----------------------------------------------------------------------------------------------------
def route(name, layer, pts, w=SIG_W):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetLayer(layer); t.SetWidth(MM(w)); t.SetNet(net(name))
        t.SetStart(XY(*a)); t.SetEnd(XY(*c)); b.Add(t)

JP = J1_PAD_V
B_, F_ = pcbnew.B_Cu, pcbnew.F_Cu
# Back: J1 to the switch. In u order the pins go R, GND, RETR, CTR, EXT, L, which is the order their switch pins
# come round the ring (left side, upper left, top left, top, through the middle, right), so nothing crosses.
route("R",    B_, [(-2.5, JP), (-2.5, 7.3), (-6.6, 3.2), (-6.6, -1.0), (-4.95, -1.0)])
route("GND",  B_, [(-1.5, JP), (-1.5, 7.0), (-4.15, 4.35), (-4.15, 2.7)])
route("RETR", B_, [(-0.5, JP), (-0.5, 6.25), (-1.0, 5.75), (-1.0, 4.95)])
route("CTR",  B_, [(0.5, JP), (0.5, 6.6), (1.0, 6.1), (1.0, 5.35)])
route("EXT",  B_, [(1.5, JP), (1.5, 7.2), (2.6, 6.1), (2.6, -2.5), (1.0, -4.1), (1.0, -4.95)])
route("L",    B_, [(2.5, JP), (2.5, 7.6), (4.95, 5.15), (4.95, 1.0)])
# Front (under the switch's body): the switch to the wire pads J2, in u order R, RETR, GND, EXT, CTR, L. RETR and CTR
# come down through the ring's middle, either side of the locating hole, and out past the bottom pins.
route("R",    F_, [(-4.95, -1.0), (-4.95, -8.9), (-5.0, J2_V)])
route("RETR", F_, [(-1.0, 4.95), (-1.8, 4.15), (-1.8, -2.5), (-3.0, -3.7), (-3.0, J2_V)])
route("GND",  F_, [(-1.0, -5.35), (-1.0, J2_V)])
route("GND",  B_, [(-5.35, 1.0), (-4.15, 2.2), (-4.15, 2.7)])   # the left PUSH pin's thermal is cut short by R
route("EXT",  F_, [(1.0, -4.95), (1.0, J2_V)])
route("CTR",  F_, [(1.0, 5.35), (2.3, 4.05), (2.3, -2.4), (3.0, -3.1), (3.0, J2_V)])
route("L",    F_, [(4.95, 1.0), (6.6, 1.0), (6.6, -2.6), (5.0, -4.2), (5.0, J2_V)])

# ---- keepouts: the screw heads, and 0.5 mm along the edges for tracks ------------------------------------------
def rule_area(name, pts, pour=True):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(pour)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(F_); ls.AddLayer(B_); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for u, v in pts: o.Append(MM(SX + u), MM(SY - v))
    b.Add(z)
for hu, hv in HOLES:
    rule_area("SCREW_HEAD", [(hu + HEAD_R * math.cos(2 * math.pi * k / 32), hv + HEAD_R * math.sin(2 * math.pi * k / 32))
                             for k in range(32)])

# ---- ground pours on both sides --------------------------------------------------------------------------------
for layer in (F_, B_):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net("GND")); z.SetZoneName("GND")
    z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for u, v in ((U0, V0), (U1, V0), (U1, V1), (U0, V1)): o.Append(MM(SX + u), MM(SY - v))
    b.Add(z)
# stitching vias, in open ground on both sides
for u, v in ((-8.5, 2.5), (8.5, 2.5), (-8.5, -3.5), (8.5, -4.5), (0.0, -7.2), (-6.4, 6.6), (6.4, 6.6), (-5.5, 13.0)):
    vi = pcbnew.PCB_VIA(b); vi.SetViaType(pcbnew.VIATYPE_THROUGH); vi.SetLayerPair(F_, B_)
    vi.SetPosition(XY(u, v)); vi.SetWidth(F_, MM(0.6)); vi.SetDrill(MM(0.3)); vi.SetNet(net("GND"))
    b.Add(vi)

# ---- silkscreen ------------------------------------------------------------------------------------------------
def text(s, u, v, layer, size=0.8, thick=0.15, rot=0, just=0):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer); t.SetPosition(XY(u, v))
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(thick)); t.SetTextAngleDegrees(rot)
    t.SetHorizJustify([pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_H_ALIGN_LEFT, pcbnew.GR_TEXT_H_ALIGN_RIGHT][just])
    if layer == pcbnew.B_SilkS: t.SetMirrored(True)
    b.Add(t); return t
BS, FS = pcbnew.B_SilkS, pcbnew.F_SilkS
for f in b.GetFootprints():
    f.Reference().SetVisible(False)
# back: J1's pin numbers at its ends, its pin list up both long edges, and J2's names under its holes
text("1", -3.1, 7.3, BS, 0.8, 0.15); text("6", 3.1, 7.3, BS, 0.8, 0.15)
text("J1: 1R 2GND 3RETR", -9.9, 0.0, BS, 0.8, 0.15, 90)
text("J1: 4CTR 5EXT 6L", 9.9, 0.0, BS, 0.8, 0.15, 90)
J2_NAMES = ("R", "RETR", "GND", "EXT", "CTR", "L")
for k, s in enumerate(J2_NAMES):
    for layer in (BS, FS):
        t = text(s, -5.0 + 2 * k, -10.85, layer, 0.8, 0.15, 90, 2 if layer == FS else 1)
# front (it faces the panel): which way is up, and the board's name
seg(FS, (0, 7.1), (0, 8.1), 0.15); seg(FS, (0, 8.1), (-0.5, 7.6), 0.15); seg(FS, (0, 8.1), (0.5, 7.6), 0.15)
text("EXT", 0, 8.9, FS, 0.8, 0.13)
text("PANEL SIDE", 0, 10.4, FS, 0.8, 0.13)
text("SEARCH HAT 1.0", 0, 11.9, FS, 0.9, 0.15)

# ---- rules (cheap-fab, as the HeliSR boards) and the title block --------------------------------------------
ds = b.GetDesignSettings()
ds.m_MinClearance = MM(0.127); ds.m_TrackMinWidth = MM(0.127); ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.3); ds.m_ViasMinAnnularWidth = MM(0.1); ds.m_CopperEdgeClearance = MM(0.5)
ds.m_HoleClearance = MM(0.2); ds.m_HoleToHoleMin = MM(0.6)
nc = ds.m_NetSettings.GetDefaultNetclass()
nc.SetClearance(MM(CLR)); nc.SetTrackWidth(MM(SIG_W)); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))
tb = b.GetTitleBlock(); tb.SetTitle("SearchHat breakout"); tb.SetRevision("1.0"); tb.SetDate("2026-11-05")
tb.SetCompany("UH1-Collective")

b.BuildConnectivity()
os.makedirs(OUT, exist_ok=True)
pcb = os.path.join(OUT, NAME + ".kicad_pcb")
b.Save(pcb)                  # the zone filler crashes on a board built in memory: fill it once it's reloaded, below

# project file: the HeliSR's, with this board's net class
src = os.path.join(PROJ, "..", "HeliSR_Rev4.0", "HeliSR_Rev4.0.kicad_pro")
pro = json.load(open(src))
pro["meta"]["filename"] = NAME + ".kicad_pro"
c = pro["net_settings"]["classes"][0]
c["clearance"] = CLR; c["track_width"] = SIG_W
pro["board"]["design_settings"]["rule_severities"] = pro["board"]["design_settings"].get("rule_severities", {})
pro.pop("boards", None)
json.dump(pro, open(os.path.join(OUT, NAME + ".kicad_pro"), "w"), indent=2)
open(os.path.join(OUT, NAME + ".kicad_dru"), "w").write("""(version 1)

# The lower M2 holes' library courtyards (5 mm across) overlap the wire pads' (J2) by about 0.5 mm. An M2
# countersunk head is 3.8 mm across, and its keepout (4.4 mm) stops every track and the pours; the nearest J2 pad is
# 0.9 mm outside the head. (severity ignore), not exclusion: kicad-cli 9 still reports rule exclusions as errors.
(rule "Lower holes and the wire pads: courtyards"
  (constraint courtyard_clearance)
  (severity ignore)
  (condition "(A.Reference == 'H3' && B.Reference == 'J2') || (A.Reference == 'J2' && B.Reference == 'H3') || (A.Reference == 'H4' && B.Reference == 'J2') || (A.Reference == 'J2' && B.Reference == 'H4')"))

# The switch's left PUSH pin (GND) gets one thermal spoke on the back, where R runs past it; a GND track on the back
# and the front pour join it as well.
(rule "Switch GND pins: one spoke is enough"
  (constraint min_resolved_spokes 1)
  (condition "A.memberOfFootprint('SW1') && A.NetName == 'GND'"))
""")
open(os.path.join(OUT, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "SearchHat")(type "KiCad")(uri "${KIPRJMOD}/SearchHat.pretty")(options "")(descr "SearchHat breakout parts"))\n)\n')

b2 = pcbnew.LoadBoard(pcb)
b2.BuildConnectivity()
pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
b2.Save(pcb)

# mechanical data for the head's CAD, in (u, v) mm with the switch at the origin
parts = {}
for f in b.GetFootprints():
    parts[f.GetReference()] = list(uv(f)) + ["B" if f.IsFlipped() else "F"]
json.dump({"outline": [U0, V0, U1, V1], "corner": CORNER, "thickness": 1.6, "holes": HOLES, "hole_d": 2.2,
           "j1_origin_v": J1_V, "j2_v": J2_V, "parts": parts}, open(os.path.join(OUT, NAME + "_mech.json"), "w"), indent=1)
print("wrote", pcb)
