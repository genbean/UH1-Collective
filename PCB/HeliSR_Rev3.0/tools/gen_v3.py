# HeliSR Rev 3.0: the Pro Micro on the board's centre line, at the USB end, with the shift registers, pull-up
# networks and caps underneath it (as on Rev 2.0). Along each long side one row of connectors: a 10-pin input header
# and two 3-pin analog headers. Top row (Pro Micro pins 13-24 side): J1 (inputs 1-8), AX3, AX4. Bottom row (pins 1-12
# side): J2 (inputs 9-16), AX1, AX2. Past the Pro Micro's far end, between the far corner holes, a column of three
# buttons: PROG4 on the top side, RST in the middle, PROG1 on the bottom side. PROG1 pulls AX1 and PROG4 pulls AX4 to
# GND through 1 k (R1, R2), to program an AS5600's range through its OUT pin (datasheet Option B). Four M3 holes, one
# in each corner. Builds the placed, unrouted board and a DSN for Freerouting.
# Run with KiCad 9's python. usage: gen_v3.py <out.kicad_pcb> <out.dsn> [params.json]
import json, math, os, sys
import pcbnew

out, dsn = sys.argv[1:3]
P = {"row_y": 2.7, "clear": 0.2, "sig_w": 0.2, "pwr_w": 0.3, "hole_in": 3.2, "screw_r": 3.5,
     "nut_clr": 3.75, "row_gap": 0.4, "gap": 6.5, "pmx0": 0.6, "btn_y": 10.0, "btn_dx": 2.0, "u2_rot": 180}
if len(sys.argv) > 3: P.update(json.loads(open(sys.argv[3]).read()))
FP = os.environ.get("KICAD9_FOOTPRINT_DIR") or os.path.join(os.path.dirname(pcbnew.__file__), "..", "..", "..", "share", "kicad", "footprints")
MM = pcbnew.FromMM; mm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))

# ---- outline ------------------------------------------------------------------------------------------
# copper widths along a row (MP pad to MP pad), rows packed with ROW_GAP between the corner nuts
WIDTH = {"J10": 12.8, "J3": 5.8}
ROW = ["J10", "J3", "J3"]
ROW_LEN = sum(WIDTH[k] for k in ROW) + P["row_gap"] * (len(ROW) - 1)
HOLE_IN = P["hole_in"]
X_S = HOLE_IN + P["nut_clr"]                 # each row starts and ends clear of the corner nuts
PMX0 = P["pmx0"]                             # Pro Micro body starts here: its USB end, at the board's edge
PM_END = PMX0 + 33.02
L = round(max(2 * X_S + ROW_LEN, PM_END + 5.5), 2)
ROW_Y = P["row_y"]                           # connector row centres, from each long edge
Y_J8 = ROW_Y + P["gap"]                      # top socket row (Pro Micro pins 13-24)
Y_J7 = Y_J8 + 15.24                          # bottom socket row (pins 1-12)
W = round(Y_J7 + P["gap"] + ROW_Y, 2)
CY = (Y_J8 + Y_J7) / 2                       # Pro Micro centre line = board centre line
SCREW_R = P["screw_r"]
HOLES = [(HOLE_IN, HOLE_IN), (L - HOLE_IN, HOLE_IN), (HOLE_IN, W - HOLE_IN), (L - HOLE_IN, W - HOLE_IN)]

b = pcbnew.BOARD()
b.GetDesignSettings().SetCopperLayerCount(2)
for a, z in (((0, 0), (L, 0)), ((L, 0), (L, W)), ((L, W), (0, W)), ((0, W), (0, 0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1)); s.SetStart(V(*a)); s.SetEnd(V(*z)); b.Add(s)

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    return nets[name]
def place(lib, name, ref, x, y, rot=0, value=""):
    f = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), name)
    f.Models().clear()
    f.SetReference(ref); f.SetValue(value or name)
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    b.Add(f); f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot)
    return f
def connect(f, num, name):
    for p in f.Pads():
        if p.GetNumber() == str(num): p.SetNet(net(name))

# ---- Pro Micro sockets: same pin geometry as Rev 1/2 (pin 1 at the USB end of the bottom row) ------------------
X0 = PMX0 + 2.54
J7 = place("Connector_PinSocket_2.54mm", "PinSocket_1x12_P2.54mm_Vertical", "J7", X0, Y_J7, 90, "Pro Micro pins 1-12")
J8 = place("Connector_PinSocket_2.54mm", "PinSocket_1x12_P2.54mm_Vertical", "J8", X0 + 11 * 2.54, Y_J8, -90, "Pro Micro pins 13-24")
for p in J8.Pads(): p.SetNumber(str(int(p.GetNumber()) + 12))
PM = {int(p.GetNumber()): p for p in list(J7.Pads()) + list(J8.Pads())}
for k, p in PM.items():
    ex = X0 + (k - 1) * 2.54 if k <= 12 else X0 + (24 - k) * 2.54
    ey = Y_J7 if k <= 12 else Y_J8
    assert abs(mm(p.GetPosition().x) - ex) < 0.01 and abs(mm(p.GetPosition().y) - ey) < 0.01, (k, p.GetPosition())
PIN_NET = {3: "GND", 4: "GND", 23: "GND", 21: "VCC", 22: "RST",
           5: "SR_DATA",     # Pro Micro "2"  = PD1 (MMJoy2 D1) <- QH of U2
           6: "SR_LOAD",     # Pro Micro "3"  = PD0 (MMJoy2 D0) -> SH/LD
           16: "SR_CLK",     # Pro Micro "15" = PB1 (MMJoy2 B1, SCK) -> CLK
           20: "AX1", 19: "AX2", 18: "AX3", 17: "AX4"}   # A3, A2, A1, A0
for k, n in PIN_NET.items(): PM[k].SetNet(net(n))

# ---- under the Pro Micro: the Rev 2.0 arrangement, positions taken relative to the Pro Micro ------------------
RN_X, U1_X, C1_X, U2_X, C2_X, C3_X = (PMX0 + d for d in (3.1, 9.1, 3.2, 24.3, 16.7, 31.0))
U2R = P["u2_rot"]                            # 0: as Rev 2.0; 180: U2 turned round (its QH at the USB end)
RN1 = place("Resistor_THT", "R_Array_SIP9", "RN1", RN_X, CY - 5.0, 0, "10k x8 bussed")
RN2 = place("Resistor_THT", "R_Array_SIP9", "RN2", RN_X, CY + 5.0, 0, "10k x8 bussed")
U1 = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U1", U1_X, CY, 90, "74HC165")
U2 = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U2", U2_X, CY, 90 + U2R, "74HC165")
C1 = place("Capacitor_SMD", "C_1206_3216Metric", "C1", C1_X, CY, -90, "100nF")   # VCC pad beside U1 pin 16
if U2R:   # U2's VCC pin is now at its far end, beside C3; C2 moves there too, across U2's end
    C2 = place("Capacitor_SMD", "C_1206_3216Metric", "C2", U2_X + 6.95, CY, 90, "100nF")
    C3 = place("Capacitor_SMD", "C_1206_3216Metric", "C3", C2_X, CY, 0, "22uF")
else:
    C2 = place("Capacitor_SMD", "C_1206_3216Metric", "C2", C2_X, CY, 180, "100nF")   # VCC pad toward U2 pin 16
    C3 = place("Capacitor_SMD", "C_1206_3216Metric", "C3", C3_X, CY, 90, "22uF")
for c in (C1, C2, C3): connect(c, 1, "VCC"); connect(c, 2, "GND")
# 74HC165: 1 SH/LD, 2 CLK, 3 E, 4 F, 5 G, 6 H, 7 /QH, 8 GND, 9 QH, 10 SER, 11 A, 12 B, 13 C, 14 D, 15 CLK INH, 16 VCC
CH = {"A": 11, "B": 12, "C": 13, "D": 14, "E": 3, "F": 4, "G": 5, "H": 6}
for u in (U1, U2):
    connect(u, 1, "SR_LOAD"); connect(u, 2, "SR_CLK"); connect(u, 8, "GND"); connect(u, 15, "GND"); connect(u, 16, "VCC")
connect(U1, 10, "GND"); connect(U1, 9, "SR_CHAIN"); connect(U2, 10, "SR_CHAIN"); connect(U2, 9, "SR_DATA")
# Inputs follow the geometry so nothing crosses. J1 (top row, pins left to right) feeds RN1 and the chips' top-row
# inputs; J2 sits in the bottom row turned round, so its pins run right to left (IN16 leftmost), and feeds RN2 and the
# chips' bottom-row inputs. U1's top row reads D C B A left to right and its bottom row E F G H; U2 the same, or with
# U2 turned round, H G F E along the top and A B C D along the bottom.
top_u2 = ["H", "G", "F", "E"] if U2R else ["D", "C", "B", "A"]
bot_u2 = ["A", "B", "C", "D"] if U2R else ["E", "F", "G", "H"]
INPUT_PIN = {}
for k, ch in enumerate([("U1", c) for c in "DCBA"] + [("U2", c) for c in top_u2]):
    INPUT_PIN[k + 1] = ch
for k, ch in enumerate([("U1", c) for c in "EFGH"] + [("U2", c) for c in bot_u2]):
    INPUT_PIN[16 - k] = ch
for n, (u, ch) in INPUT_PIN.items():
    connect(U1 if u == "U1" else U2, CH[ch], f"IN{n}")
connect(RN1, 1, "VCC"); connect(RN2, 1, "VCC")
for i in range(8):
    connect(RN1, i + 2, f"IN{i + 1}")
    connect(RN2, i + 2, f"IN{16 - i}")

# ---- connector rows: every pin facing the Pro Micro ----------------------------------------------------------
JST = lambda n: f"JST_SH_BM{n:02d}B-SRSS-TB_1x{n:02d}-1MP_P1.00mm_Vertical"
xs, x = [], X_S
for k in ROW:
    xs.append(x + WIDTH[k] / 2); x += WIDTH[k] + P["row_gap"]
YT, YB = ROW_Y, W - ROW_Y
def inputs(ref, x, y, rot, base):
    f = place("Connector_JST", JST(10), ref, x, y, rot, "Inputs 1-8" if base == 0 else "Inputs 9-16")
    connect(f, 1, "GND"); connect(f, 10, "GND"); connect(f, "MP", "GND")
    for i in range(8): connect(f, i + 2, f"IN{base + i + 1}")
def analog(ref, ax, x, y, rot):
    f = place("Connector_JST", JST(3), ref, x, y, rot, ax)
    connect(f, 1, "VCC"); connect(f, 2, ax); connect(f, 3, "GND"); connect(f, "MP", "GND")
inputs("J1", xs[0], YT, 0, 0)                # top row: J1, AX3, AX4
analog("J13", "AX3", xs[1], YT, 0)
analog("J14", "AX4", xs[2], YT, 0)
inputs("J2", xs[0], YB, 180, 8)              # bottom row, turned round so the pins face up: J2, AX1, AX2
analog("J11", "AX1", xs[1], YB, 180)
analog("J12", "AX2", xs[2], YB, 180)

# ---- buttons past the Pro Micro's far end, between the far corner holes (terminals along y) -------------------
lib = os.path.join(os.path.dirname(os.path.abspath(out)), "HeliSR.pretty")
BX = L - P["btn_dx"]
def switch(ref, y, n1):
    sw = pcbnew.FootprintLoad(lib, "SW_TL1015AF160QG")
    sw.SetReference(ref); sw.SetValue("TL1015AF160QG"); b.Add(sw)
    sw.SetPosition(V(BX, y)); sw.SetOrientationDegrees(90)
    connect(sw, 1, n1); connect(sw, 2, "GND")
    return sw
switch("SW1", CY, "RST")                      # RST in the middle
switch("SW2", W - P["btn_y"], "PROG1")        # PROG1 (AX1) on the J2 / pins 1-12 side
switch("SW3", P["btn_y"], "PROG4")            # PROG4 (AX4) on the J1 / pins 13-24 side
R_X = BX - 1.5 - 0.99 - 0.3                   # each resistor just inside its button, toward the Pro Micro
R1 = place("Resistor_SMD", "R_0805_2012Metric", "R1", R_X, W - P["btn_y"], 90, "1k")
connect(R1, 1, "AX1"); connect(R1, 2, "PROG1")
R2 = place("Resistor_SMD", "R_0805_2012Metric", "R2", R_X, P["btn_y"], 90, "1k")
connect(R2, 1, "AX4"); connect(R2, 2, "PROG4")

# ---- mounting holes and their keepouts ----------------------------------------------------------------------
for i, (hx, hy) in enumerate(HOLES):
    place("MountingHole", "MountingHole_3.2mm_M3", f"H{i + 1}", hx, hy, 0, "M3")
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName("SCREW_HEAD")
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for k in range(32):
        a = 2 * math.pi * k / 32; o.Append(MM(hx + SCREW_R * math.cos(a)), MM(hy + SCREW_R * math.sin(a)))
    b.Add(z)
# routing keepout: 0.5 mm copper-free border (removed after routing)
E = 0.5
for pts in ([(0, 0), (L, 0), (L, E), (0, E)], [(0, W - E), (L, W - E), (L, W), (0, W)],
            [(0, 0), (E, 0), (E, W), (0, W)], [(L - E, 0), (L, 0), (L, W), (L - E, W)]):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName("ROUTE_KEEPOUT")
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for px, py in pts: o.Append(MM(px), MM(py))
    b.Add(z)

# ---- design rules (same cheap-fab rules as Rev 1/2) -----------------------------------------------------------
ds = b.GetDesignSettings()
ds.m_MinClearance = MM(0.127); ds.m_TrackMinWidth = MM(0.127); ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.3); ds.m_ViasMinAnnularWidth = MM(0.1); ds.m_CopperEdgeClearance = MM(0.5)
ds.m_HoleClearance = MM(0.2); ds.m_HoleToHoleMin = MM(0.6)
nc = ds.m_NetSettings.GetDefaultNetclass()
nc.SetClearance(MM(P["clear"])); nc.SetTrackWidth(MM(P["sig_w"])); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))

b.BuildConnectivity()
b.Save(out)
json.dump({"L": L, "W": W, "CY": CY, "PMX0": PMX0, "Y_J8": Y_J8, "Y_J7": Y_J7, "YT": YT, "YB": YB, "row_x": xs,
           "btn": [BX, P["btn_y"], CY, W - P["btn_y"]], "r": [R_X, P["btn_y"], W - P["btn_y"]], "holes": HOLES, "u2_rot": U2R,
           "parts": {f.GetReference(): [mm(f.GetPosition().x), mm(f.GetPosition().y)] for f in (U1, U2, C1, C2, C3, RN1, RN2)},
           "input_pin": {str(k): v for k, v in INPUT_PIN.items()}},
          open(os.path.splitext(out)[0] + "_layout.json", "w"), indent=1)
print("dsn", pcbnew.ExportSpecctraDSN(b, dsn), "board", L, "x", W, "PMX0", PMX0)
