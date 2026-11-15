# AS5600 sensor board Rev 1.0: a drop-in for the 23.24 mm square AS5600 module in the base's lever and the head's pod,
# plugged straight into a HeliSR Rev 4.0 AX port with a JST SR 1:N jumper (A04SR04SR30K254B).
#   Front (chip side, faces the magnet): the AS5600 (SOIC-8) on the board's centre, C1 100 nF on VDD5V and C2 1 uF on
#     VDD3V3 (both 1206). Nothing over 1.75 mm tall, all inside +-7 mm of the centre (the head's rails and the base's
#     M2 screw heads are outside that).
#   Back: J1, a vertical JST SH 4-pin (BM04B-SRSS-TB), centred, the same part as the HeliSR's AX ports.
#   The AS5600 runs in 5 V mode, wired as its datasheet asks (ams v1-06, page 3): 1 VDD5V to VCC with 100 nF, 2 VDD3V3
#     to 1 uF only, 3 OUT open, 4 GND, 5 PGO open (internal pull-up: no OTP programming by OUT), 6 SDA, 7 SCL,
#     8 DIR to GND. No pull-ups: each HeliSR port has its own 2.2k pair.
#   J1's pins are the HeliSR port's (1 SDA, 2 GND, 3 VCC, 4 SCL) seen through a 1:N cable (pin n to pin 5-n):
#     1 SCL, 2 VCC, 3 GND, 4 SDA.
# Run with KiCad 9's python (tools/build.py does). usage: gen_as5600.py <out.kicad_pcb>
import faulthandler, math, os, sys
faulthandler.enable()
try:                                          # KiCad's internal checks (wx asserts) log instead of opening a dialog
    import wx; wx.DisableAsserts()
except Exception:
    pass
import pcbnew

out = sys.argv[1]
FP = os.path.join(os.path.dirname(pcbnew.__file__), "..", "..", "..", "share", "kicad", "footprints")
MM = pcbnew.FromMM; mm = pcbnew.ToMM

S = 23.24                                     # the module's size, as measured (0.915 in square)
O = 100.0                                     # board's top-left corner in KiCad's page
C = O + S / 2                                 # board centre
V = lambda x, y: pcbnew.VECTOR2I(MM(C + x), MM(C + y))     # x, y from the centre (KiCad: y down)
HOLE_PITCH = 16.0                             # the holes on a 16 mm square, centre to centre
HOLES = [(sx * HOLE_PITCH / 2, sy * HOLE_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
HOLE_D = 2.4                                  # for M2 (the base screws the board down with four M2 x 8 flat heads)
SIG_W, PWR_W, CLEAR = 0.25, 0.4, 0.2
PORT = {"SDA": 1, "GND": 2, "VCC": 3, "SCL": 4}                     # HeliSR Rev 4.0 AX port
J1_PIN = {5 - n: sig for sig, n in PORT.items()}                     # through the 1:N cable
assert J1_PIN == {1: "SCL", 2: "VCC", 3: "GND", 4: "SDA"}

b = pcbnew.BOARD()
b.GetDesignSettings().SetCopperLayerCount(2)
corners = [(-S / 2, -S / 2), (S / 2, -S / 2), (S / 2, S / 2), (-S / 2, S / 2)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1)); s.SetStart(V(*corners[i])); s.SetEnd(V(*corners[(i + 1) % 4])); b.Add(s)

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    return nets[name]
def place(lib, name, ref, x, y, rot=0, value="", back=False, add=True):
    f = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), name)
    f.SetReference(ref); f.SetValue(value or name)
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    if add: b.Add(f)
    f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot)
    if back: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    return f
def pad(f, num):
    return [p for p in f.Pads() if p.GetNumber() == str(num)]
def xy(p):
    return round(mm(p.GetPosition().x) - C, 3), round(mm(p.GetPosition().y) - C, 3)
def connect(f, num, name):
    for p in pad(f, num): p.SetNet(net(name))
def track(pts, name, w=SIG_W, layer=pcbnew.F_Cu):
    for a, z in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*z)); t.SetWidth(MM(w))
        t.SetLayer(layer); t.SetNet(net(name)); b.Add(t)
def via(x, y, name):
    v = pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetPosition(V(x, y)); v.SetWidth(pcbnew.F_Cu, MM(0.6)); v.SetDrill(MM(0.3))
    v.SetNet(net(name)); b.Add(v)

# ---- front: the AS5600 and its two capacitors -------------------------------------------------------------------
U1 = place("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm", "U1", 0, 0, 0, "AS5600")
for n, name in ((1, "VCC"), (2, "VDD3V3"), (4, "GND"), (6, "SDA"), (7, "SCL"), (8, "GND")):
    connect(U1, n, name)
P = {n: xy(pad(U1, n)[0]) for n in range(1, 9)}
assert P[1] == (-2.475, -1.905) and P[8] == (2.475, -1.905) and P[6] == (2.475, 0.635), P
C1 = place("Capacitor_SMD", "C_1206_3216Metric", "C1", P[1][0] + 1.475, -5.0, 0, "100nF")   # pad 1 straight over pin 1
connect(C1, 1, "VCC"); connect(C1, 2, "GND")
C2 = place("Capacitor_SMD", "C_1206_3216Metric", "C2", -5.2, P[2][1] + 1.475, 90, "1uF")    # its upper pad level with pin 2
c2 = sorted(C2.Pads(), key=lambda p: p.GetPosition().y)
c2[0].SetNet(net("VDD3V3")); c2[1].SetNet(net("GND"))
C2_TOP, C2_BOT = xy(c2[0]), xy(c2[1])
assert abs(C2_TOP[1] - P[2][1]) < 0.01, C2_TOP

# ---- back: J1, centred, its signal pads in a column on the right (toward U1's SDA and SCL), pin 1 at the top ------
J1 = place("Connector_JST", "JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical", "J1", 0, 0, 0, "HeliSR AX port", back=True)
for rot in (0, 90, 180, 270):                  # turn it on the back until it's the right way round
    J1.SetOrientationDegrees(rot)
    q = {n: xy(pad(J1, n)[0]) for n in range(1, 5)}
    if q[1][0] > 0 and abs(q[1][0] - q[4][0]) < 0.01 and q[1][1] < q[4][1]: break
else:
    raise SystemExit("J1: no orientation with pin 1 at the top of a right-hand column")
bb = J1.GetCourtyard(pcbnew.B_CrtYd).BBox()
dx, dy = -(mm(bb.Centre().x) - C), -(mm(bb.Centre().y) - C)              # centre the courtyard on the board
J1.Move(pcbnew.VECTOR2I(MM(dx), MM(dy)))
for n, sig in J1_PIN.items(): connect(J1, n, sig)
connect(J1, "MP", "GND")
JP = {n: xy(pad(J1, n)[0]) for n in range(1, 5)}
MP = sorted(xy(p) for p in pad(J1, "MP"))
assert all(m[0] < 0 for m in MP), MP                                      # the mounting pads on the left

# ---- mounting holes ---------------------------------------------------------------------------------------------
for i, (hx, hy) in enumerate(HOLES):
    h = place("MountingHole", "MountingHole_2.2mm_M2", f"H{i + 1}", hx, hy, 0, "M2")
    for p in h.Pads(): p.SetDrillSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D))); p.SetSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))

# ---- tracks -----------------------------------------------------------------------------------------------------
VCC_VIA = (-3.2, -3.4)                                                    # between U1 and C1, left of J1's mounting pad
track([P[1], xy(pad(C1, 1)[0])], "VCC", PWR_W)
track([(P[1][0], VCC_VIA[1]), VCC_VIA], "VCC", PWR_W)
via(*VCC_VIA, "VCC")
track([P[2], C2_TOP], "VDD3V3", PWR_W)
track([P[4], (C2_BOT[0], P[4][1])], "GND", PWR_W)                         # pin 4 into C2's ground pad
track([C2_BOT, (C2_BOT[0], C2_BOT[1] + 1.5)], "GND", PWR_W); via(C2_BOT[0], C2_BOT[1] + 1.5, "GND")
c1g = xy(pad(C1, 2)[0])
track([c1g, (c1g[0] + 1.45, c1g[1])], "GND", PWR_W); via(c1g[0] + 1.45, c1g[1], "GND")
track([P[8], (P[8][0], -3.4)], "GND", SIG_W); via(P[8][0], -3.4, "GND")  # DIR to GND
SCL_VIA, SDA_VIA = (4.4, P[7][1]), (4.4, P[6][1])
track([P[7], SCL_VIA], "SCL"); via(*SCL_VIA, "SCL")
track([P[6], SDA_VIA], "SDA"); via(*SDA_VIA, "SDA")
BK = pcbnew.B_Cu
track([SCL_VIA, (SCL_VIA[0] - abs(JP[1][1] - SCL_VIA[1]), JP[1][1]), JP[1]], "SCL", SIG_W, BK)
track([SDA_VIA, (SDA_VIA[0] - abs(JP[4][1] - SDA_VIA[1]), JP[4][1]), JP[4]], "SDA", SIG_W, BK)
track([VCC_VIA, (VCC_VIA[0], JP[2][1]), JP[2]], "VCC", PWR_W, BK)          # down, then across between the mounting pads
for x, y in ((-6.0, -6.0), (6.0, -6.0), (6.0, 5.0), (-1.0, 4.6), (-8.0, -2.0), (7.5, 2.8)):   # ground stitching
    via(x, y, "GND")

# ---- test pads on the front (bare 1.0 mm pads, nothing to fit): 5V, GND, 3V3 along the top, SCL and SDA on the
# right by their vias, OUT on the left (the AS5600's analog / PWM output, otherwise unused). 3V3 sits in from the
# corner hole's courtyard ------------------------------------------------------------------------------------------
TP_Y = -7.3
TP = {"5V": ("VCC", (P[1][0], TP_Y)), "GND": ("GND", (c1g[0], TP_Y)), "3V3": ("VDD3V3", (-4.6, TP_Y)),
      "SCL": ("SCL", (6.6, -1.4)), "SDA": ("SDA", (6.6, 1.4)), "OUT": ("OUT", (-8.0, 0.84))}
for i, (label, (name, (x, y))) in enumerate(TP.items()):
    f = place("TestPoint", "TestPoint_Pad_D1.0mm", f"TP{i + 1}", x, y, 0, label)
    connect(f, 1, name)
connect(U1, 3, "OUT")
track([xy(pad(C1, 1)[0]), TP["5V"][1]], "VCC", PWR_W)                 # straight up from C1
track([c1g, TP["GND"][1]], "GND", PWR_W)
t3 = TP["3V3"][1]
track([C2_TOP, (C2_TOP[0], t3[1] + 0.9), (t3[0], t3[1] + 0.3), t3], "VDD3V3", PWR_W)   # up the left from C2
track([SCL_VIA, TP["SCL"][1]], "SCL"); track([SDA_VIA, TP["SDA"][1]], "SDA")
track([P[3], (-3.6, P[3][1]), (-3.8, TP["OUT"][1][1]), TP["OUT"][1]], "OUT")   # under C2's body, between its pads

# ---- ground pours, both sides -------------------------------------------------------------------------------------
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net("GND"))
    z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25)); z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.4)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    o = z.Outline(); o.NewOutline()
    for x, y in corners: o.Append(MM(C + x), MM(C + y))
    b.Add(z)

# ---- silkscreen ---------------------------------------------------------------------------------------------------
def text(s, x, y, back=False, size=0.8, just=0):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(V(x, y))
    t.SetLayer(pcbnew.B_SilkS if back else pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(0.15))
    if just: t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if just > 0 else pcbnew.GR_TEXT_H_ALIGN_LEFT)
    if back: t.SetMirrored(True)
    b.Add(t)
text("AS5600 Rev 1.0", 0, 7.2)
for label, (_, (x, y)) in TP.items():                                    # each test pad's name
    if y == TP_Y: text(label, x, TP_Y - 1.6)                              # over the top row
    elif label == "OUT": text(label, x, y + 1.5)                          # under OUT
    else: text(label, x + 2.3, y)                                         # right of SCL, SDA
text("UH1-Collective", 0, -7.0, back=True)
for n, sig in J1_PIN.items():                                             # on the back, past the SDA/SCL vias
    text(f"{n} {sig}", JP[n][0] + 5.9, JP[n][1], back=True, size=0.8)
text("1:N SR CABLE", 0, 6.4, back=True)
text("TO HeliSR AX PORT", 0, 7.6, back=True, size=0.8)

# ---- rules --------------------------------------------------------------------------------------------------------
ds = b.GetDesignSettings()
ds.m_MinClearance = MM(0.15); ds.m_TrackMinWidth = MM(0.15); ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.3); ds.m_ViasMinAnnularWidth = MM(0.1); ds.m_CopperEdgeClearance = MM(0.5)
ds.m_HoleClearance = MM(0.25); ds.m_HoleToHoleMin = MM(0.6)
nc = ds.m_NetSettings.GetDefaultNetclass()
nc.SetClearance(MM(CLEAR)); nc.SetTrackWidth(MM(SIG_W)); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))

b.BuildConnectivity()
b.Save(out)
b = pcbnew.LoadBoard(out)                      # filled once loaded from a file (with its project), like the HeliSR's tools
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print("board", S, "x", S, "J1 pins", JP, "C2", C2_TOP, C2_BOT)
