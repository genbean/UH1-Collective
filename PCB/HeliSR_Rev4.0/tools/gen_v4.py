# HeliSR Rev 4.0: Rev 3.0's board (same outline, holes, Pro Micro, shift registers and input connectors) with the
# four analog inputs replaced by four I2C ports for AS5600 sensors. Each AS5600 answers at 0x36, so a PCA9546A
# 4-channel I2C switch (U3, on the back) gives each port its own channel. The Pro Micro's I2C pins (2 = SDA,
# 3 = SCL) drive it; the shift-register lines move off them to pins 14 (data), 15 (clock) and A0 (load), and A1
# drives the switch's /RESET.
#   Front: the Rev 3.0 parts under the Pro Micro; along each long side a 10-pin input header and one 4-pin port
#   (top: J1, AX3; bottom: J2, AX1); across the far end AX4 (J1 side), RST, AX2 (J2 side).
#   Back: U3 with its decoupling cap and upstream pull-ups, and under each port its own pair of 2.2k pull-ups.
#   All the back resistors and C4 are 1206, like the front caps, for hand soldering.
#   Ports (JST SH 4-pin): 1 SDA, 2 GND, 3 VCC, 4 SCL.
# Builds the placed, unrouted board and a DSN for Freerouting.
# Run with KiCad 9's python. usage: gen_v4.py <out.kicad_pcb> <out.dsn> [params.json]
import json, math, os, sys
import pcbnew

out, dsn = sys.argv[1:3]
P = {"row_y": 2.7, "clear": 0.2, "sig_w": 0.2, "pwr_w": 0.3, "hole_in": 3.2, "screw_r": 3.5,
     "nut_clr": 3.75, "row_gap": 0.5, "gap": 6.5, "pmx0": 0.6, "u2_rot": 180,
     "end_y": 10.1,            # far-end ports: centre distance from the long edges
     "u3_x": 30.0,             # U3 (back), on the board's centre line
     "pu_off": 1.0,            # port pull-ups: distance in from the port's centre toward the board
     "c4_dx": 2.4, "c4_dy": 2.6,   # C4 from U3's VCC pin (1206, upright, clear of RN1's last pin)
     "r9_dx": 6.2}             # R9, R10 in from U3's SDA, SCL pins
if len(sys.argv) > 3: P.update(json.loads(open(sys.argv[3]).read()))
FP = os.environ.get("KICAD9_FOOTPRINT_DIR") or os.path.join(os.path.dirname(pcbnew.__file__), "..", "..", "..", "share", "kicad", "footprints")
MM = pcbnew.FromMM; mm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))

# ---- outline: as Rev 3.0 (39.3 x 33.64 mm, the same four holes) ---------------------------------------------
PMX0 = P["pmx0"]
L, W = 39.3, 33.64
ROW_Y = P["row_y"]
Y_J8 = ROW_Y + P["gap"]                      # top socket row (Pro Micro pins 13-24)
Y_J7 = Y_J8 + 15.24                          # bottom socket row (pins 1-12)
assert abs(Y_J7 + P["gap"] + ROW_Y - W) < 0.01
CY = (Y_J8 + Y_J7) / 2
HOLE_IN = P["hole_in"]
X_S = HOLE_IN + P["nut_clr"]
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
def place(lib, name, ref, x, y, rot=0, value="", back=False):
    f = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), name)
    f.Models().clear()
    f.SetReference(ref); f.SetValue(value or name)
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    b.Add(f); f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot)
    if back: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    return f
def connect(f, num, name):
    for p in f.Pads():
        if p.GetNumber() == str(num): p.SetNet(net(name))
def pad_xy(f, num):
    p = [p for p in f.Pads() if p.GetNumber() == str(num)][0]
    return mm(p.GetPosition().x), mm(p.GetPosition().y)

# ---- Pro Micro sockets: same pin geometry as Rev 1-3 (pin 1 at the USB end of the bottom row) -------------------
X0 = PMX0 + 2.54
J7 = place("Connector_PinSocket_2.54mm", "PinSocket_1x12_P2.54mm_Vertical", "J7", X0, Y_J7, 90, "Pro Micro pins 1-12")
J8 = place("Connector_PinSocket_2.54mm", "PinSocket_1x12_P2.54mm_Vertical", "J8", X0 + 11 * 2.54, Y_J8, -90, "Pro Micro pins 13-24")
for p in J8.Pads(): p.SetNumber(str(int(p.GetNumber()) + 12))
PM = {int(p.GetNumber()): p for p in list(J7.Pads()) + list(J8.Pads())}
for k, p in PM.items():
    ex = X0 + (k - 1) * 2.54 if k <= 12 else X0 + (24 - k) * 2.54
    ey = Y_J7 if k <= 12 else Y_J8
    assert abs(mm(p.GetPosition().x) - ex) < 0.01 and abs(mm(p.GetPosition().y) - ey) < 0.01, (k, p.GetPosition())
# Socket pin -> Pro Micro pin: 1 TXO, 2 RXI, 3-4 GND, 5 "2", 6 "3", 7 "4" ... 12 "9";
# 13 "10", 14 "16", 15 "14", 16 "15", 17 A0, 18 A1, 19 A2, 20 A3, 21 VCC, 22 RST, 23 GND, 24 RAW.
PIN_NET = {3: "GND", 4: "GND", 23: "GND", 21: "VCC", 22: "RST",
           5: "SDA",         # Pro Micro "2"  = PD1, the 32U4's TWI data
           6: "SCL",         # Pro Micro "3"  = PD0, TWI clock
           16: "SR_CLK",     # Pro Micro "15" = PB1 (SCK) -> 74HC165 CLK
           15: "SR_DATA",    # Pro Micro "14" = PB3 (MISO) <- QH of U2
           17: "SR_LOAD",    # Pro Micro "A0" = PF7 -> 74HC165 SH/LD
           18: "MUX_RST"}    # Pro Micro "A1" = PF6 -> PCA9546A /RESET
for k, n in PIN_NET.items(): PM[k].SetNet(net(n))

# ---- under the Pro Micro (front): Rev 3.0's arrangement, unchanged ---------------------------------------------
RN_X, U1_X, C1_X, U2_X, C2_X, C3_X = (PMX0 + d for d in (3.1, 9.1, 3.2, 24.3, 16.7, 31.0))
U2R = P["u2_rot"]
RN1 = place("Resistor_THT", "R_Array_SIP9", "RN1", RN_X, CY - 5.0, 0, "10k x8 bussed")
RN2 = place("Resistor_THT", "R_Array_SIP9", "RN2", RN_X, CY + 5.0, 0, "10k x8 bussed")
U1 = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U1", U1_X, CY, 90, "74HC165")
U2 = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U2", U2_X, CY, 90 + U2R, "74HC165")
C1 = place("Capacitor_SMD", "C_1206_3216Metric", "C1", C1_X, CY, -90, "100nF")
if U2R:
    C2 = place("Capacitor_SMD", "C_1206_3216Metric", "C2", U2_X + 6.95, CY, 90, "100nF")
    C3 = place("Capacitor_SMD", "C_1206_3216Metric", "C3", C2_X, CY, 0, "22uF")
else:
    C2 = place("Capacitor_SMD", "C_1206_3216Metric", "C2", C2_X, CY, 180, "100nF")
    C3 = place("Capacitor_SMD", "C_1206_3216Metric", "C3", C3_X, CY, 90, "22uF")
for c in (C1, C2, C3): connect(c, 1, "VCC"); connect(c, 2, "GND")
# 74HC165: 1 SH/LD, 2 CLK, 3 E, 4 F, 5 G, 6 H, 7 /QH, 8 GND, 9 QH, 10 SER, 11 A, 12 B, 13 C, 14 D, 15 CLK INH, 16 VCC
CH = {"A": 11, "B": 12, "C": 13, "D": 14, "E": 3, "F": 4, "G": 5, "H": 6}
for u in (U1, U2):
    connect(u, 1, "SR_LOAD"); connect(u, 2, "SR_CLK"); connect(u, 8, "GND"); connect(u, 15, "GND"); connect(u, 16, "VCC")
connect(U1, 10, "GND"); connect(U1, 9, "SR_CHAIN"); connect(U2, 10, "SR_CHAIN"); connect(U2, 9, "SR_DATA")
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

# ---- connectors (front), every pin facing the Pro Micro ----------------------------------------------------------
JST = lambda n: f"JST_SH_BM{n:02d}B-SRSS-TB_1x{n:02d}-1MP_P1.00mm_Vertical"
WIDTH = {"J10": 12.8, "J4": 6.8}
xs, x = [], X_S
for k in ("J10", "J4"):
    xs.append(x + WIDTH[k] / 2); x += WIDTH[k] + P["row_gap"]
YT, YB = ROW_Y, W - ROW_Y
XE = L - ROW_Y                                # far-end column
PORT_PIN = {"SDA": 1, "GND": 2, "VCC": 3, "SCL": 4}
def inputs(ref, x, y, rot, base):
    f = place("Connector_JST", JST(10), ref, x, y, rot, "Inputs 1-8" if base == 0 else "Inputs 9-16")
    connect(f, 1, "GND"); connect(f, 10, "GND"); connect(f, "MP", "GND")
    for i in range(8): connect(f, i + 2, f"IN{base + i + 1}")
def port(ref, ax, x, y, rot):
    f = place("Connector_JST", JST(4), ref, x, y, rot, ax + " (I2C)")
    connect(f, PORT_PIN["SDA"], ax + "_SDA"); connect(f, PORT_PIN["SCL"], ax + "_SCL")
    connect(f, PORT_PIN["GND"], "GND"); connect(f, PORT_PIN["VCC"], "VCC"); connect(f, "MP", "GND")
    return f
inputs("J1", xs[0], YT, 0, 0)
inputs("J2", xs[0], YB, 180, 8)
PORTS = {"AX3": port("J13", "AX3", xs[1], YT, 0),          # top row
         "AX1": port("J11", "AX1", xs[1], YB, 180),        # bottom row
         "AX4": port("J14", "AX4", XE, P["end_y"], -90),   # far end, J1 side
         "AX2": port("J12", "AX2", XE, W - P["end_y"], -90)}
for ax, f in PORTS.items():                   # every pin toward the board's middle, MP pads toward the edge
    sig = [pad_xy(f, n) for n in (1, 4)]; mp = [pad_xy(f, "MP")]
    d = lambda q: math.hypot(q[0] - L / 2, q[1] - W / 2)
    assert max(d(q) for q in sig) < d(mp[0]), ax

# ---- RST button: far end, between AX4 and AX2 ----------------------------------------------------------------------
lib = os.path.join(os.path.dirname(os.path.abspath(out)), "HeliSR.pretty")
SW1 = pcbnew.FootprintLoad(lib, "SW_TL1015AF160QG")
SW1.SetReference("SW1"); SW1.SetValue("TL1015AF160QG"); b.Add(SW1)
SW1.SetPosition(V(XE + 0.3, CY)); SW1.SetOrientationDegrees(90)
connect(SW1, 1, "RST"); connect(SW1, 2, "GND")

# ---- back: the PCA9546A I2C switch --------------------------------------------------------------------------------
# PCA9546A (SOIC-16): 1 A0, 2 A1, 3 /RESET, 4 SD0, 5 SC0, 6 SD1, 7 SC1, 8 GND, 9 SD2, 10 SC2, 11 SD3, 12 SC3,
# 13 A2, 14 SCL, 15 SDA, 16 VCC. A0-A2 to GND: address 0x70. Flipped onto the back, pins 1-8 face the far end
# (pin 1 at the top) and pins 9-16 the USB end (pin 16 at the top), so the channels go to the nearest ports:
# 0 -> AX4 and 1 -> AX2 (far end), 2 -> AX1 (bottom row), 3 -> AX3 (top row).
CHANNEL = {0: "AX4", 1: "AX2", 2: "AX1", 3: "AX3"}
UX = P["u3_x"]
U3 = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U3", UX, CY, 0, "PCA9546A", back=True)
for k, n in ((1, "GND"), (2, "GND"), (13, "GND"), (8, "GND"), (16, "VCC"), (3, "MUX_RST"), (15, "SDA"), (14, "SCL")):
    connect(U3, k, n)
for ch, ax in CHANNEL.items():
    connect(U3, 4 + 2 * ch if ch < 2 else 9 + 2 * (ch - 2), ax + "_SDA")
    connect(U3, 5 + 2 * ch if ch < 2 else 10 + 2 * (ch - 2), ax + "_SCL")
assert pad_xy(U3, 1)[0] > UX and pad_xy(U3, 1)[1] < CY and pad_xy(U3, 16)[0] < UX, "U3 orientation"
R = lambda ref, x, y, rot, val: place("Resistor_SMD", "R_1206_3216Metric", ref, x, y, rot, val, back=True)
v16 = pad_xy(U3, 16)
C4 = place("Capacitor_SMD", "C_1206_3216Metric", "C4", v16[0] - P["c4_dx"], v16[1] + P["c4_dy"], 90, "100nF", back=True)
cp = sorted(C4.Pads(), key=lambda p: math.hypot(mm(p.GetPosition().x) - v16[0], mm(p.GetPosition().y) - v16[1]))
cp[0].SetNet(net("VCC")); cp[1].SetNet(net("GND"))        # VCC on the pad nearer pin 16
# upstream pull-ups (SDA, SCL; the Pro Micro side) and /RESET's, beside U3
s15, s14 = pad_xy(U3, 15), pad_xy(U3, 14)
R9 = R("R9", s15[0] - P["r9_dx"], s15[1] + 0.4, 0, "10k"); R10 = R("R10", s14[0] - P["r9_dx"], s14[1] + 1.55, 0, "10k")
r3 = pad_xy(U3, 3)
R11 = R("R11", r3[0] + 2.45, r3[1] + 0.4, 90, "10k")
def pullup(r, sig):
    ps = list(r.Pads())
    # VCC on the pad nearer the board's edge (the port's VCC pin is on the edge side of its signal pins)
    ps.sort(key=lambda p: min(mm(p.GetPosition().x), L - mm(p.GetPosition().x), mm(p.GetPosition().y), W - mm(p.GetPosition().y)))
    ps[0].SetNet(net("VCC")); ps[1].SetNet(net(sig))
pullup(R9, "SDA"); pullup(R10, "SCL"); pullup(R11, "MUX_RST")
# the ports' pull-ups, 2.2k, a pair under each port: identical circuits on all four
RP = {}
k = 1
for ax in ("AX1", "AX2", "AX3", "AX4"):
    f = PORTS[ax]; fx, fy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    if ax in ("AX3", "AX1"):                  # long sides: the pair side by side along the row, upright
        dy = P["pu_off"] if ax == "AX3" else -P["pu_off"]
        ra = R(f"R{k}", fx - 1.2, fy + dy, 90, "2.2k"); rb = R(f"R{k + 1}", fx + 1.2, fy + dy, 90, "2.2k")
    else:                                     # far end: one above the other, lying along x
        ra = R(f"R{k}", fx - P["pu_off"], fy - 1.2, 0, "2.2k"); rb = R(f"R{k + 1}", fx - P["pu_off"], fy + 1.2, 0, "2.2k")
    pullup(ra, ax + "_SDA"); pullup(rb, ax + "_SCL")
    RP[ax] = (ra.GetReference(), rb.GetReference()); k += 2

# ---- mounting holes and their keepouts ----------------------------------------------------------------------
SCREW_R = P["screw_r"]
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

# ---- design rules (same cheap-fab rules as Rev 1-3) -----------------------------------------------------------
ds = b.GetDesignSettings()
ds.m_MinClearance = MM(0.127); ds.m_TrackMinWidth = MM(0.127); ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.3); ds.m_ViasMinAnnularWidth = MM(0.1); ds.m_CopperEdgeClearance = MM(0.5)
ds.m_HoleClearance = MM(0.2); ds.m_HoleToHoleMin = MM(0.6)
nc = ds.m_NetSettings.GetDefaultNetclass()
nc.SetClearance(MM(P["clear"])); nc.SetTrackWidth(MM(P["sig_w"])); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))

b.BuildConnectivity()
b.Save(out)
fp = lambda f: [round(mm(f.GetPosition().x), 3), round(mm(f.GetPosition().y), 3)]
json.dump({"L": L, "W": W, "CY": CY, "PMX0": PMX0, "Y_J8": Y_J8, "Y_J7": Y_J7, "YT": YT, "YB": YB, "XE": XE,
           "row_x": xs, "holes": HOLES, "u2_rot": U2R, "channel": CHANNEL, "port_pullups": RP,
           "parts": {f.GetReference(): fp(f) + ["B" if f.IsFlipped() else "F"] for f in b.GetFootprints()},
           "input_pin": {str(k): v for k, v in INPUT_PIN.items()}},
          open(os.path.splitext(out)[0] + "_layout.json", "w"), indent=1)
print("dsn", pcbnew.ExportSpecctraDSN(b, dsn), "board", L, "x", W)
