# Build Heli_Collective_Final_BOM.xlsx, the one BOM for the whole collective as it is
# built now: the HeliSR Rev 4.0 board (AS5600s over I2C; not ordered yet), the Huey head Rev 5 (Head/) and
# the MkIII base Rev 4 (Base/). Earlier revisions are gone from the repo (git history has them).
# The board's parts (SOLDERED, below) are checked against its board file; the cables and the head switches come from
# the Rev 3.0 board's Digi-Key cart (ORDER, below). The Digi-Key order placed for
# Rev 3.0 (DK_ORDER) counts as bought: the parts Rev 4.0 shares with it are not ordered again; so do the
# Mouser orders (MOUSER_ORDER). Only parts this build uses are listed. Head and base lines cite the README or CAD they come from. Lines
# sized only from the CAD are highlighted for checking; lines covered by the two screw kits (every screw and nut in
# the head and base) are marked and cost nothing extra.
# Sheets: Final BOM (everything bought: the only parts list), Printed
# parts, Sources.
# usage: python tools/make_bom.py [out.xlsx]     (any Python 3 with openpyxl)
import math, os, re, sys
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "BOM", "Heli_Collective_Final_BOM.xlsx")
R4 = os.path.join(ROOT, "PCB", "HeliSR")
BOARD_PCB = os.path.join(R4, "HeliSR_Rev4.0.kicad_pcb")

# ---- the HeliSR Rev 4.0 board's parts, checked against the board file: every placed part once, with the right
# footprint and value. (refs, value, footprint, description, manufacturer, mfr part, digikey part, unit USD, notes)
SOLDERED = [
    ("U1, U2", "74HC165", "SOIC-16_3.9x9.9mm_P1.27mm", "Shift register, 74HC165, SOIC-16", "Texas Instruments",
     "SN74HC165DR", "296-8250-1-ND", 0.50, "Front, under the Pro Micro: fit before the sockets"),
    ("RN1, RN2", "10k x8 bussed", "R_Array_SIP9", "Resistor network, 8 x 10 kOhm bussed, SIP-9", "Bourns",
     "4609X-101-103LF", "4609X-101-103LF-ND", 0.39, "Pin 1 (dot) is the common pin: it goes in the square pad. Keep upright"),
    ("C1, C2, C4", "100nF", "C_1206_3216Metric", "Capacitor, 100 nF, 50 V, X7R, 1206", "Samsung", "CL31B104KBCNNNC",
     "1276-1017-1-ND", 0.14, "Decoupling: C1 beside U1's VCC pin, C2 beside U2's (front); C4 beside U3's (back)"),
    ("C3", "22uF", "C_1206_3216Metric", "Capacitor, 22 uF, 10 V, X5R, 1206", "Samsung", "CL31A226KPHNNNE",
     "1276-1287-1-ND", 0.47, "Bulk supply capacitor, between U1 and U2"),
    ("U3", "PCA9546A", "SOIC-16_3.9x9.9mm_P1.27mm", "I2C switch, 4 channels, with reset, SOIC-16 (narrow, D package)",
     "Texas Instruments", "PCA9546ADR", "296-21770-1-ND", 1.82,
     "Back. Gives each AS5600 port its own I2C channel (they all answer at 0x36). Not the wide DW package"),
    ("R1-R8", "2.2k", "R_1206_3216Metric", "Resistor, 2.2 kOhm, 1 %, 1/4 W, 1206", "YAGEO", "RC1206FR-072K2L",
     "311-2.20KFRCT-ND", 0.10, "Back: the ports' I2C pull-ups, a pair under each port (R1/R2 AX1, R3/R4 AX2, R5/R6 AX3, "
     "R7/R8 AX4; the odd one SDA, the even one SCL)"),
    ("R9-R11", "10k", "R_1206_3216Metric", "Resistor, 10 kOhm, 1 %, 1/4 W, 1206", "YAGEO", "RC1206FR-0710KL",
     "311-10.0KFRCT-ND", 0.10, "Back: pull-ups on the Pro Micro's SDA (R9) and SCL (R10), and on U3's /RESET (R11). "
     "Any 1 % 1206 10 kOhm resistor will do if this one is out of stock"),
    ("SW1", "TL1015AF160QG", "SW_TL1015AF160QG", "Tactile switch, SMD, 3.9 x 2.9 mm, gull wing", "E-Switch",
     "TL1015AF160QG", "EG4344CT-ND", 0.48, "RST, at the far end between AX4 and AX2. The four ground tabs are left unsoldered"),
    ("J1, J2", None, "JST_SH_BM10B-SRSS-TB_1x10-1MP_P1.00mm_Vertical", "JST SR/SH header, 10-pin, 1.0 mm, SMD, top entry",
     "JST", "BM10B-SRSS-TBT", "455-BM10B-SRSS-TBTCT-ND", 1.19,
     "Switch inputs: J1 IN1-IN8, J2 IN9-IN16. Digi-Key estimates $0.33 tariff each on top"),
    ("J11-J14", None, "JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical", "JST SR/SH header, 4-pin, 1.0 mm, SMD, top entry",
     "JST", "BM04B-SRSS-TBT", "455-BM04B-SRSS-TBTCT-ND", 0.71,
     "AS5600 ports AX1-AX4 (J11-J14): 1 SDA, 2 GND, 3 VCC, 4 SCL. Fit all four, or only the ports you use"),
    ("J7, J8", None, "PinSocket_1x12_P2.54mm_Vertical", "Socket header, female, 1x12, 2.54 mm, through hole", "Sullins",
     "PPTC121LFBN-RC", "S6100-ND", 0.75, "Pro Micro sockets. Fit last"),
]

def footprints(path):
    s = open(path, encoding="utf-8").read()
    out, i = {}, 0
    while (i := s.find("\n\t(footprint ", i)) >= 0:
        d, j, q = 0, i + 1, False
        while True:                                  # find the matching paren, skipping quoted strings
            ch = s[j]
            if q:
                if ch == "\\": j += 1
                elif ch == '"': q = False
            elif ch == '"': q = True
            elif ch == "(": d += 1
            elif ch == ")":
                d -= 1
                if d == 0: break
            j += 1
        fp = s[i + 2:j + 1]; i = j                    # from "(footprint" to its closing paren
        ref = re.search(r'\(property "Reference" "([^"]*)"', fp).group(1)
        if "(exclude_from_bom" in fp or re.search(r"\(attr [^)]*exclude_from_bom", fp): continue
        out[ref] = (re.match(r'\(footprint "(?:[^":]*:)?([^"]+)"', fp).group(1),
                    re.search(r'\(property "Value" "([^"]*)"', fp).group(1))
    return out
def expand(refs):
    r = []
    for part in refs.split(", "):
        m = re.fullmatch(r"([A-Z]+)(\d+)-[A-Z]*(\d+)", part)
        r += [f"{m.group(1)}{k}" for k in range(int(m.group(2)), int(m.group(3)) + 1)] if m else [part]
    return r
fps = footprints(BOARD_PCB)
listed = [r for line in SOLDERED for r in expand(line[0])]
assert sorted(listed) == sorted(fps) and len(set(listed)) == len(listed), sorted(set(fps) ^ set(listed))
for refs, value, fpname, *_ in SOLDERED:
    for ref in expand(refs):
        assert fps[ref][0] == fpname and (value is None or fps[ref][1] == value), (ref, fps[ref], fpname, value)

# ---- the Rev 3.0 board's Digi-Key cart, the source for the cables, head switches and module lines.
# (refs, qty, description, manufacturer, mfr part, digikey part, unit USD, notes)
ORDER = [
    ("Controller", [
        ("Module", 1, "Pro Micro 5V/16 MHz, ATmega32U4", "SparkFun", "12640", "1568-12640-ND", 23.99,
         "Runs MMJoy2"),
        ("Module", 2, "Pin header, male, 1x12, 2.54 mm", "Sullins", "PRPC012SAAN-RC", "35-PRPC012SAAN-RC-ND", 0.24,
         "Soldered to the Pro Micro"),
    ]),
    ("Board components", [
        ("J7, J8", 2, "Socket header, female, 1x12, 2.54 mm", "Sullins", "PPTC121LFBN-RC", "S6100-ND", 0.75,
         "Pro Micro sockets"),
        ("U1, U2", 2, "74HC165 shift register, SOIC-16", "Texas Instruments", "SN74HC165DR", "296-8250-1-ND", 0.50,
         "Fit before the sockets. They sit under the Pro Micro"),
        ("RN1, RN2", 2, "Resistor network, 8 x 10 kOhm bussed, SIP-9", "Bourns", "4609X-101-103LF",
         "4609X-101-103LF-ND", 0.39, "Pin 1 (dot) is the common pin. It goes in the square pad"),
        ("C1, C2", 2, "Capacitor, 100 nF, 50 V, X7R, 1206", "Samsung", "CL31B104KBCNNNC", "1276-1017-1-ND", 0.14,
         "Shift register decoupling. C3 (22 uF) lies between U1 and U2; C1 and C2 sit at the chips' outer ends"),
        ("C3", 1, "Capacitor, 22 uF, 10 V, X5R, 1206", "Samsung", "CL31A226KPHNNNE", "1276-1287-1-ND", 0.47,
         "Bulk supply capacitor"),
        ("J1, J2", 2, "JST SR/SH header, 10-pin, 1.0 mm, SMD top entry", "JST", "BM10B-SRSS-TBT",
         "455-BM10B-SRSS-TBTCT-ND", 1.19, "Switch inputs 1-8 and 9-16. Price: cart on 2026-10-22, plus $0.33 estimated tariff each"),
        ("J11-J14", 4, "JST SR/SH header, 3-pin, 1.0 mm, SMD top entry", "JST", "BM03B-SRSS-TBT",
         "455-BM03B-SRSS-TBTCT-ND", 0.68, "Analog inputs AX1-AX4. Price: cart on 2026-10-22, plus $0.26 estimated tariff "
         "each. That cart had 3: enough for the three inputs the Huey head uses, one short of all four footprints"),
        ("SW1-SW3", 3, "Tactile switch, SMD 3.9 x 2.9 mm, gull wing", "E-Switch", "TL1015AF160QG", "EG4344CT-ND", 0.48,
         "SW1 RST, SW2 PROG1 (AX1), SW3 PROG4 (AX4). Footprint SW_TL1015AF160QG (4.15 mm pad centres). Their four ground tabs are left unsoldered"),
        ("R1, R2", 2, "Resistor, 1 kOhm, 1 %, 1/8 W, 0805", "YAGEO", "RC0805FR-071KL", "311-1.00KCRCT-ND", 0.10,
         "In series with the PROG buttons: each pulls its AS5600's OUT pin low through 1 k to program it"),
    ]),
    ("Cables", [
        ("J1, J2", 2, "JST SR jumper, 10-pin, 10 in, 30 AWG, pin 1 to pin 1", "JST", "A10SR10SR30K254A",
         "455-3671-ND", None, "Switch looms. Quantity and price: check the cart"),
        ("J11-J14", 4, "JST SR jumper, 3-pin, 8 in, 30 AWG, pin 1 to pin 1", "JST", "A03SR03SR30K203A",
         "455-3627-ND", None, "One per sensor or pot. Quantity and price: check the cart"),
    ]),
    ("Sensors", [
        ("AX1 (MkII base)", 1, "Linear Hall sensor, ratiometric, TO-92, A4 (lowest sensitivity)", "Texas Instruments",
         "DRV5055A4QLPGM", "296-DRV5055A4QLPGMCT-ND", 0.77,
         "Only for the original MkII base. The MkIII base uses an AS5600 module (see below). Pinout VCC / GND / OUT, same as SS49E"),
        ("AX1 (MkII base, alt)", 1, "Linear Hall sensor, ratiometric, TO-92, A2 (higher sensitivity)", "Texas Instruments",
         "DRV5055A2QLPGM", "296-DRV5055A2QLPGMCT-ND", 1.11,
         "Try this one if the A4 uses too little of the axis range"),
        ("AX1 cap (MkII base)", 1, "Capacitor, 100 nF, 50 V, X7R, axial", "KEMET", "C410C104K5R5TA91707200",
         "399-13734-1-ND", 0.77, "Solder across VCC and GND at the Hall sensor"),
        ("AX2, AX3", 2, "Potentiometer, 5 kOhm linear, 9 mm, 6 mm knurled shaft", "TT Electronics/BI",
         "P0915N-QC20BR5K", "987-1278-ND", 2.41, "Throttle (AX2, in the spline adaptor) and head knob (AX3)"),
    ]),
    ("Head switches (15 of the 16 inputs)", [
        ("2 inputs each", 2, "Toggle switch, SPDT, ON-OFF-ON, M12 bushing, solder lug", "APEM", "639H/2",
         "679-1223-ND", None, "LDG LT EXT / RETR and SL ON / STOW. Common to GND. Price: check the cart"),
        ("2 inputs", 1, "Toggle switch, SPDT, (ON)-OFF-(ON), M12 bushing, solder lug", "APEM", "637H/2",
         "679-1219-ND", None, "GOV INCR / DECR. Price: check the cart"),
        ("1 input", 1, "Toggle switch, SPDT, ON-ON, M12 bushing, solder lug", "APEM", "636H/2",
         "679-1217-ND", None, "LDG LT ON / OFF (one side wired). Price: check the cart"),
        ("1 input", 1, "Push button, large, SPST-NO momentary, M12", "Same Sky", "PB4-M-BK-D-67",
         "2223-PB4-M-BK-D-67-ND", 2.52, "STOP REL"),
        ("1 input each", 2, "Push button, small, SPST-NO momentary, 7.2 mm cutout", "E-Switch", "PS1024ABLK",
         "EG2011-ND", 1.66, "The two buttons on the lower panel"),
        ("1 input each", 5, "Tactile switch, 6 x 6 mm, 5 mm high, THT", "TE Connectivity", "1825910-6",
         "450-1650-ND", 0.13, "SEARCH CONT 4-way hat (4) and starter trigger (1)"),
    ]),
    ("PCB mounting", [
        ("H1-H4", 4, "Round spacer, unthreaded, for M3, 4 mm long, 6.4 mm OD, PVC, self-retaining", "Bivar",
         "SRS-4-4MM", "SRS-4-4MM-ND", 0.10, "Between the Huey head's rear wall and the board. Screws and nuts not in the order (see below)"),
    ]),
]
by_mpn = {it[4]: it for _, items in ORDER for it in items}          # refs, qty, desc, mfr, mpn, dk, unit, notes

BRD = "PCB/HeliSR/HeliSR_Rev4.0.kicad_pcb (parts checked against the board file)"
NEW = "Digi-Key listing 2026-10-27"
FULL = "The Rev 3.0 board's Digi-Key cart (ORDER in tools/make_bom.py)"
HEAD = "Head/README.md, Bought"
BASE = "Base/README.md, Bought parts"
BASE1 = "Base/mk3_pivot.py and Base/mk3_rev3.py (the parts Rev 4 keeps)"
CAD = "Base/mk3_rev4.py geometry (no size in any list)"
AMZ = "Amazon listing on 2026-10-22 (listing)"
KIT = "AvrestYPT screw kit (Amazon B0FMD5TMSH)"
SETKIT = "HIQTRADEBYJJ set screw kit (Amazon B0DG33R714)"
SCREWS = "Head and Base/mk3_rev4.py screw lists; Head/renders and Base/renders screw maps"
CHECK, INKIT, ORDERED = "check", "kit", "ordered"
FILL = {CHECK: "FCE4D6", INKIT: "E2EFDA", ORDERED: "DDEBF7"}

# line: (where, qty, description, manufacturer, mfr part, supplier, supplier part, pack price USD, pack, status,
#        packs already bought, notes, source)
CHECKED = {"639H/2": 8.47, "637H/2": 8.02, "636H/2": 7.55, "A10SR10SR30K254A": 3.17, "A03SR03SR30K203A": 1.35,   # Digi-Key, 2026-10-22
           "PCA9546ADR": 1.88, "BM04B-SRSS-TBT": 0.73, "RC1206FR-072K2L": 0.10, "RC1206FR-0710KL": 0.10}       # 2026-10-27
# the Rev 3.0 Digi-Key order (2026-10-23), placed for Rev 3.0: quantity bought of each part, one collective's worth
DK_ORDER = {"296-8250-1-ND": 2, "4609X-101-103LF-ND": 2, "1276-1017-1-ND": 2, "1276-1287-1-ND": 1, "311-1.00KCRCT-ND": 2,
            "EG4344CT-ND": 3, "455-BM10B-SRSS-TBTCT-ND": 2, "455-BM03B-SRSS-TBTCT-ND": 4, "S6100-ND": 2, "455-3671-ND": 1,
            "455-3627-ND": 2, "839-30-01653-DS-ND": 1, "380-SC-2CAK020M-ND": 1, "679-1223-ND": 2, "679-1219-ND": 1,
            "679-1217-ND": 1, "2223-PB4-M-BK-D-67-ND": 1, "450-1650-ND": 5, "SRS-4-4MM-ND": 4, "315-NC191LT10-ND": 1,
            "1188-CHN-TWZ1MM-ND": 1}
def dk(mpn, where=None, qty=None, notes=None, source=FULL):
    refs, q, desc, mfr, mpn_, dkpn, unit, n = by_mpn[mpn]
    notes = (notes or n).replace("Price: check the cart", "Price from Digi-Key, 2026-10-22")
    return (where or refs, q if qty is None else qty, desc, mfr, mpn_, "Digi-Key", dkpn, CHECKED.get(mpn, unit), 1, "", 0, notes, source)
def kit(where, qty, desc, notes=""):
    return (where, qty, desc, "AvrestYPT", "", "Amazon", "B0FMD5TMSH", 0, 1, INKIT, 0, ("In the screw kit. " + notes).strip(),
            KIT + "; " + SCREWS)
def setkit(where, qty, desc, notes=""):
    return (where, qty, desc, "HIQTRADEBYJJ", "", "Amazon", "B0DG33R714", 0, 1, INKIT, 0,
            ("In the set screw kit. " + notes).strip(), SETKIT + "; " + SCREWS)
def amz(where, qty, desc, brand, asin, price, pack, notes, source, status=""):
    return (where, qty, desc, brand, "", "Amazon", asin, price, pack, status, 1 if status == ORDERED else 0, notes,
            source + "; Amazon listing 2026-10-23")
def any_(where, qty, desc, notes, source, status="", pack=1):
    return (where, qty, desc, "", "", "any", "", None, pack, status, 0, notes, source)

SECTIONS = []
board = [(refs, len(expand(refs)), desc, mfr, mpn, "Digi-Key", dkpn, CHECKED.get(mpn, unit), 1, "", 0, notes, BRD)
         for refs, value, fpname, desc, mfr, mpn, dkpn, unit, notes in SOLDERED]
SECTIONS.append(("HeliSR Rev 4.0: the parts you solder to the bare board", board))
SECTIONS.append(("HeliSR Rev 4.0: bare PCB and controller", [
    ("PCB", 1, "HeliSR Rev 4.0 bare PCB (no parts fitted), 2 layers, 1.6 mm FR4, 39.3 x 33.64 mm", "OSH Park", "", "OSH Park",
     "", 10.20, 3, "", 0, "Not ordered yet: upload PCB/HeliSR/HeliSR_Rev4.0_Gerbers.zip. Priced as Rev 3.0's "
     "order: $10.20 for three bare boards, free shipping", "PCB/HeliSR/README.md; OSH Park order for Rev 3.0"),
    ("J7, J8", 1, "Pro Micro 5V/16 MHz (ATmega32U4), USB-C, with header pins", "OSOYOO", "", "Amazon", "B0B81FGBLY", 11.99, 1,
     "", 0, "Runs the HeliSR firmware (its Rev 4.0 build); plugs into the J7/J8 sockets. Comes with three rows of header "
     "pins, so no separate headers. Also sold as 3 for $21.99. Check that its 2 x 12 pins line up with J7/J8 (15.24 mm "
     "between rows)", AMZ),
]))
SECTIONS.append(("Wiring", [
    dk("A10SR10SR30K254A", "J1, J2", 1, "Switch loom. The jumper has a connector at each end: cut it in half for the two "
       "board-end pigtails (J1 and J2). Price: check the cart"),
    ("J11, J14", 2, "JST SR jumper, 4 positions, socket to socket (reversed), 8 in (203 mm)", "JST", "A04SR04SR30K203A",
     "Digi-Key", "455-3633-ND", 1.52, 1, "", 0, "AX1 (collective sensor) and AX4 (throttle sensor); AX2 and AX3 are spare. "
     "Cut each in half for a board-end pigtail. The plug is keyed but the wires may all be one colour: find pin 1 (SDA) "
     "with a meter. Ports: 1 SDA, 2 GND, 3 VCC, 4 SCL", NEW + "; PCB/HeliSR/README.md"),
    ("AX1 lead", 1, "Ribbon cable, flat, 4 conductors, 24 AWG", "KYOCERA AVX", "902220736004000", "Mouser",
     "581-902220736004000", 3.35, 1, ORDERED, 1, "Collective sensor lead: from the AS5600 in the base, through the "
     "lever's cable channels and up the 470 mm tube, spliced to an AX1 pigtail. Keep the port's order across the ribbon "
     "(SDA, GND, VCC, SCL), so GND and VCC sit between SDA and SCL. Check it reaches and lies flat in the channels",
     "Mouser invoice  (2026-11-03); Base/README.md (the 4-core sensor lead)"),
    ("USB", 1, "USB 2.0 cable, USB-A plug to USB-C plug, 2 m (6.56 ft)", "Stewart Connector", "SC-2CAK020M", "Digi-Key",
     "380-SC-2CAK020M-ND", 7.33, 1, "", 0, "Cut it about 15 cm from the USB-C plug. Feed the long piece (USB-A end stays "
     "at the PC) through the device: laid in the lever's open channels, up the tube and in through the head. The cable "
     "cover's spout is a plain 7.5 mm bore. Splice the USB-C stub back on inside the head (red, black, green, white) "
     "and leave the shield wire unconnected. The cut costs about 15 cm of the 2 m: check the run still reaches. "
     "Head/check_r5.py checks the C plug (a 12 x 7 x 25 mm overmold, its end 5.4 mm into the tube) and its "
     "cable into the tube: a 12 x 7 overmold up to 38 mm long fits, 14 x 8 up to 35 mm. Measure yours",
     "Digi-Key cart 2026-10-23; Head/README.md (collision check); Base/README.md"),
]))
SECTIONS.append(("Angle sensors", [
    ("AX1, AX4", 2, "AS5600 magnetic encoder module, 23 x 23 mm, with 5 x 2 mm diametric magnet", "WWZMDiB", "", "Amazon",
     "B0CM3C8KFT", 9.99, 4, "", 0, "Sold in fours. AX1: the collective, in the base, DIR to VCC. AX4: the throttle, in "
     "the head, DIR to GND. Read over I2C; the firmware sets each range, nothing is burnt. On each: remove the 0 ohm R1 "
     "and R4 (1 kOhm, PGO to GND), check for about 1 uF from VDD3V3 to GND, and measure the pull-ups (see "
     "PCB/HeliSR/README.md, AS5600 modules)", AMZ + "; PCB/HeliSR/README.md"),
]))
SECTIONS.append(("Huey head: switches", [
    dk("639H/2", "IN3-IN6", notes="LDG LT EXT / RETR and SL ON / STOW. Common to GND. Price: check the cart"),
    dk("637H/2", "IN1, IN2", notes="GOV RPM INCR / DECR. Price: check the cart"),
    dk("636H/2", "IN7", notes="LDG LT ON (one side wired). Price: check the cart"),
    dk("PB4-M-BK-D-67", "IN13", notes="STOP REL"),
    dk("1825910-6", "IN14", 1, notes="Starter trigger. (The SEARCH CONT hat's Rev 1-3 used four more: Rev 4 uses the ALPS "
       "stick below.) IN8, IN15, IN16 are spare"),
    ("IN9-IN12 (+ IN15)", 1, "8-direction stick switch with centre push, 11 x 11 mm body, 2.2 mm metal stick, THT",
     "ALPS Alpine", "RKJXM1015004", "Mouser", "688-RKJXM1015004", None, 1, "", 0, "SEARCH CONT hat Rev 4, on the "
     "SearchHat breakout board (SW1). Directions A-D to IN9-IN12 (EXT, RETR, L, R); the centre push (CTR) to the spare "
     "IN15 if you want it. Price: check Mouser", "Head/Hat/README.md; PCB/SearchHat/README.md"),
]))
SECTIONS.append(("SearchHat Rev 1.0: the SEARCH CONT hat's breakout board (hat Rev 4)", [
    ("PCB", 1, "SearchHat Rev 1.0 bare PCB (no parts fitted), 2 layers, 1.6 mm FR4, 22 x 29 mm", "OSH Park", "", "OSH Park",
     "", 4.95, 3, "", 0, "Not ordered yet: upload PCB/SearchHat/SearchHat_Rev1.0_Gerbers.zip. OSH Park's $5 per "
     "square inch for three boards (0.99 sq in)", "PCB/SearchHat/README.md"),
    ("J1", 1, "JST SH 1.0 mm header, 6 pins, side entry, SMD", "JST", "SM06B-SRSS-TB(LF)(SN)", "Mouser", "", None, 1, "", 0,
     "On the board's back. Leave it off if you solder the wires to the J2 pads instead. Price: check Mouser (or Digi-Key "
     "with the switch's order)", "PCB/SearchHat/README.md"),
    ("J1 lead", 1, "JST SH jumper, 6 positions, socket to socket, about 150 mm", "JST", "A06SR06SR30K152A", "Mouser", "",
     None, 1, "", 0, "Cut in half: one end plugs into J1, the other's wires go to the HeliSR's J2 loom (GND, IN9-IN12, and "
     "IN15 for the centre push). Check pin 1 with a meter. Not needed if you solder to J2. Price: check Mouser",
     "PCB/SearchHat/README.md"),
]))
SECTIONS.append(("Huey head: hardware", [
    setkit("Tube boss", 1, "M5 x 8 set screw", "From the boss's front (lower panel off), into its printed M5 thread; the tip "
           "pins the tube through the front wall of its 5.2 mm cross hole, 10 mm below the tube's top. Replaces the M5 x 40 "
           "bolt and nut (the kit's M5s stop at 20 mm)"),
    kit("Friction collar", 1, "M4 x 12 countersunk screw + M4 hex nut", "Pinch screw: the head sits 2 mm into the +y ear, "
        "the nut in the -y ear's pocket"),
    amz("Throttle grip", 4, "O-ring, 24 mm ID x 28 mm OD x 2 mm, nitrile (NBR 70A), pack of 50", "FOCMKEAS", "B0BWWBTL4N",
        6.89, 50, "The grip floats on these: two in grooves in its bore (its bearings on the tube), one in the friction "
        "collar's groove and one in the ceiling's groove round the tube. Grease them lightly with silicone grease", HEAD),
    amz("Trigger pivot", 1, "M3 countersunk hex socket screws, 10.9 black oxide, M3 x 20 / 25 / 30 / 35 / 40, 100 pcs", "Amazon",
        "B0BYXS4BTF", 9.99, "once", "Ordered 2026-10-23. Uses the M3 x 25 (ISO 10642 / DIN 7991); the kits stop at "
         "20 mm. Head in the countersink in the mount's left lug, through the trigger, then about 8 mm "
         "into the right lug's printed M3 thread; the tip stays about 0.9 mm inside the lug",
        HEAD + "; user's choice 2026-10-23", ORDERED),
    setkit("Trigger pull stop", 1, "M3 x 4 set screw", "Through the trigger's arm (printed M3 thread); its tip bears on the mount. Set it "
           "so the starter switch clicks before the stop"),
    kit("Trigger pull stop seat", 1, "M2 x 8 countersunk screw", "Flush in a countersunk, M2-tapped hole (1.6 mm pilot) in the mount's face under the spring pocket, so the pull stop's tip bears on steel and not on plastic"),
    kit("Search hat (Rev 4) board", 4, "M2 x 8 countersunk screw", "From behind, through the SearchHat board's 2.2 mm "
        "holes into the 1.6 mm pilots in the lower panel's four bosses; each cuts its own thread"),
    kit("Panels", 8, "M3 x 16 countersunk screw (DIN 7991)", "4 per panel, into the M3 threads printed 20 mm deep in the "
        "box's corner columns (a kit M3 x 20 fits too)"),
    kit("HeliSR board", 4, "M3 x 12 countersunk screw (DIN 7991) + M3 hex nut", "From outside the rear wall through a "
        "spacer and the board"),
    dk("SRS-4-4MM", "HeliSR board", 4, "Between the rear wall and the board", source=HEAD),
    amz("Trigger", 1, "Pen spring, 4 mm OD x 50 mm, 0.4 mm wire, pack of 10", "uxcell", "B0GCZGNBYH", 6.99, 10,
        "Trigger return: cut to about 13 mm", HEAD),
    amz("Head box", 1, "Ballast: lead split shot fishing weights, assorted, 120 pcs", "SANWEAL", "B0H6J3X6GL", 5.99, 1,
        "Only if the gas strut lifts too much: the base balances a 45 N strut; a 50 N one needs about 42 g, the top of "
        "the range (53 N) about 68 g. Close to the middle of the box. Weigh out what you need", BASE),
]))
SECTIONS.append(("MkIII base Rev 4", [
    ("Pivot", 2, "Thin-section ball bearing 6808-2RS, 40 x 52 x 7 mm, double sealed", "", "6808-2RS", "Amazon",
     "B012BIHBTQ", None, 2, CHECK, 0, "2-pack listing found 2026-11-08: price not checked, and any 6808-2RS fits (SKF "
     "61808-2RS1, VXB, WJB and others sell it). Pressed onto the 40.1 mm trunnions, in 52.0 mm seats split between the frame and the shell. "
     "Print the 6808 coupons first", "Amazon search 2026-11-08; " + BASE),
    ("Tube", 1, "Carbon fibre tube, 25 mm OD x 23 mm ID, 500 mm, 3K plain weave, wrapped", "MECCANIXITY", "", "Amazon",
     "B0CFFT1B31", 27.49, 2, "", 0, "Sold in pairs. Wrapped, as the base needs (not pultruded). Used whole, 500 mm, uncut (470 + the head's extra 12.7 mm of bore + 17.3 mm down in the base's socket). Drill the "
     "head's 5.2 mm cross hole 10 mm below the top end and file a 13 mm wide notch, 4+ mm deep, in each side of the bottom end for the cables. Check "
     "the socket and head fits with it (coupons)", AMZ + "; " + BASE),
    amz("Socket mouth", 1, "Worm-drive hose clamp, 25-40 mm range, 304 stainless, pack of 25", "MISPIRE", "B0F8QWCFWR", 18.99, 25,
        "Pack of 25 is the smallest 25-40 mm pack found; you need one", BASE1),
    amz("Lever halves, shell, brake hinge", 9, "Socket head cap screws M4 x 30 / 35 / 40 / 45 / 50, 12.9 black oxide, 10 of each, with 50 M4 nuts, "
        "flat and lock washers and a hex key (200 pieces)", "HELIFOUNER", "B0CDSKK7V1", 9.99, "once",
        "Uses 4 x M4 x 35 and 5 x M4 x 50, with 9 of its M4 nuts. Lever halves (split on the tube's plane): four "
        "M4 x 35 along the pivot axis through the hub, behind the bearings, two from each end, heads in 7.5 mm "
        "counterbores, nuts in hex pockets in the other half's end face; printed hollow dowels round them locate the "
        "halves. Screw the halves up before pressing the bearings on. Shell: four M4 x 50, two each side, from the top down 13 mm "
        "counterbores in its side walls, each centred on the joint, into nuts slid into the pillow blocks from "
        "their outer faces, under the side covers. Brake strap: one M4 x 50 is its hinge "
        "pin, through the pillow blocks, the webs inside them and the strut clevis's rib, head in a counterbore on the +y "
        "side, nut in a hex pocket "
        "on the -y side", BASE, ORDERED),
    ("Strut", 1, "Gas strut, 6 in (152.4 mm eye to eye), 45 N (sold as 9-12 lb), flat eyelet tabs", "X AUTOHAUX", "",
     "Amazon", "B0CY267GFY", 13.69, 2, "", 0, "Sold in pairs: the spare is the other half. The anchor is placed so the "
     "45 N strut as bought balances the lever. Fit it cylinder down: the cylinder (0.475 in) on the anchor clevis, "
     "the rod on the collar", BASE),
    kit("Strut eyes", 2, "M4 x 16 countersunk screw + M4 hex nut", "One per eye: head on +y, nut in the -y cheek's pocket. "
        "The listing gives the strut's eye holes as 4 mm. Snug, then thread-lock: the eye must still turn"),
    kit("Strut collar", 2, "M4 x 12 countersunk screw + M4 hex nut", "Collar clamp, two 20 mm apart: each head sits 2 mm into the -y ear, "
        "its nut in the +y ear's pocket"),
    kit("Side covers", 8, "M3 x 12 countersunk screw", "Four per cover, from its outer face into M3 threads tapped right "
        "through the pillow block and the shell's 9 mm side wall"),
    any_("Brake", 1, "M5 x 35 hex-head bolt (ISO 4017 / DIN 933), zinc or stainless", "Not in the screw kits (they "
         "have only countersunk heads): any hardware store. Its head sits on the floor of the hex pocket in the printed "
         "knob (Base/stl/friction_knob.stl: the MkII knob, its floor 11 mm up), so the knob turns it; it runs down "
         "through the knob's seat in the shell's top, leaning 30 deg forward, into the M5 nut in the brake strap's head. "
         "35 mm keeps the nut's full thread with or without the optional spring",
         "Base/README.md, Brake", CHECK),
    kit("Brake", 1, "M5 hex nut", "Dropped into the slot in the brake strap's head from its +y side; the bolt holds it. "
        "A nyloc nut fits the slot too, if you want the knob to stay put"),
    amz("Brake (optional)", 1, "Compression spring, 10 mm OD, 1.0 mm wire, 15 mm free length, pack of 10", "Amazon",
        "B09FF6VQ55", 11.10, 10, "Optional. It sits in the 10.6 mm, 7 mm deep pocket in the knob's underside and pushes "
        "the knob off its seat, so the knob sets the brake through the spring: a soft range of about 10 turns up to "
        "the spring's 20 N or so, then firm once the knob is down on its seat. Without it the knob sits on the seat "
        "and the brake goes from free to firm within about a turn. Any spring up to 10 mm OD (over the 5 mm bolt), "
        "0.8-1.0 mm wire, 10-15 mm free length, fits", CAD, CHECK),
    amz("Brake strap", 1, "Self-adhesive felt tape, 1.5 mm thick, 3/4 in x 50 ft, black", "FindTape", "B077TCDNYT", 24.98, 1,
        "Lines the brake strap's curved face: cut a 51 mm length and trim it to 16 mm wide. It is the only 1.5 mm felt "
        "found in a usable width, and you need a few cm of the 50 ft", CAD, CHECK),
    amz("Desk mounting", 4, "Screw, #10 x 1-1/2 in pan head, 304 stainless, pack of 50", "Amazon", "B0F43RY9S6", 8.29, 50,
        "Through the 5.5 mm holes in the frame plate's corners (8 mm plate). Not in the kits: they go into the desk. "
        "1-1/2 in suits a typical desktop: check yours", CAD, CHECK),
]))
def _kit_used():
    """what the kit lines above take out of the screw kit, by size"""
    import collections
    scr, nuts = collections.Counter(), collections.Counter()
    for _, lines in SECTIONS:
        for l in lines:
            if l[6] != "B0FMD5TMSH" or l[9] != INKIT:
                continue
            m_ = re.match(r"(M\d) x (\d+) countersunk", l[2])
            if m_:
                scr[(m_.group(1), int(m_.group(2)))] += l[1]
            n_ = re.search(r"(M\d) hex nut", l[2])
            if n_:
                nuts[n_.group(1)] += l[1]
    return ", ".join(f"{d} x {L} ({q})" for (d, L), q in sorted(scr.items())) + "; nuts " + ", ".join(
        f"{d} ({q})" for d, q in sorted(nuts.items()))
KIT_USED = _kit_used()
SECTIONS.append(("Kits, consumables and tools", [
    ("Hardware", 1, "Screw kit, 1715 pieces: countersunk hex-socket screws M2-M4 x 8, 12, 16, 20 and M5 x 10, 12, 16, 20, "
     "with hex nuts and washers, hex keys", "AvrestYPT", "", "Amazon", "B0FMD5TMSH", 17.99, "once", ORDERED, 1,
     "Every countersunk screw and nut in the head and base (the green lines). Used: " + KIT_USED + ". Order "
     "(link 2026-10-23)",
     "Amazon listing 2026-10-23 (the order)"),
    ("Hardware", 1, "Set screw kit, 500 pieces, 304 stainless: M3 x 3, 4, 5, 6; M4 x 4, 5, 6; M5 x 5, 8; M6 x 6, 10; "
     "M8 x 8; hex keys", "HIQTRADEBYJJ", "", "Amazon", "B0DG33R714", 8.96, "once", ORDERED, 1,
     "The set screws: M5 x 8 (tube, head), M3 x 4 (trigger pull stop). Your "
     "order (link 2026-10-23)",
     "Amazon listing 2026-10-23 (the order)"),
    amz("Assembly", 1, "Cyanoacrylate (CA) super glue gel, 0.14 fl oz", "Loctite", "B0006HUJCQ", 3.82, "once",
        "Magnets into their caps", "Head/README.md; Base/README.md"),
    amz("Assembly", 1, "Mini hot glue sticks, 0.27 in, 100 pack", "Surebonder", "B003JZII34", 5.97, "once",
        "AS5600 modules. Mini size: they fit a mini glue gun only. Skip this if you already have glue sticks for your gun",
        "Head/README.md; Base/README.md"),
    amz("Assembly", 1, "White lithium grease, 1.5 oz tube", "Permatex", "B000HBNV58", 3.99, "once",
        "Bearing grease (not silicone paste)", "Head/README.md; Base/README.md"),
    amz("Assembly", 1, "Silicone faucet grease, waterproof, 0.5 oz", "Danco", "B000DZFUPC", 5.68, "once",
        "For the head's four throttle O-rings (grease them lightly before fitting)", "Head/README.md"),
    amz("Assembly", 1, "Threadlocker, blue 242, 6 ml", "Loctite", "B000I1RSNS", 7.03, "once", "Removable, medium strength",
        "Head/README.md; Base/README.md"),
    ("Assembly", 1, "Solder paste, low-temperature (Sn42/Bi58, 138 C), syringe", "Chip Quik", "NC191LT10", "Digi-Key",
     "315-NC191LT10-ND", 7.95, "once", "", 0, "For the SMD parts on the board (U1-U3, the 1206 parts, the JST headers, "
     "SW1). Needs a hot plate or hot air tool and flux; with parts on both sides, do the back first. Optional: hand-soldering works too", "Digi-Key cart 2026-10-23"),
    ("Assembly", 1, "Tweezers, 1 mm tip (Olimex CHN-TWZ1MM), for placing the SMD parts", "Olimex", "CHN-TWZ1MM", "Digi-Key",
     "1188-CHN-TWZ1MM-ND", 0.82, "once", "", 0, "Description from Olimex's sibling CHN-TWZ2MM listing: check the tip", "the Rev 3.0 Digi-Key order"),
    amz("Assembly", 1, "Taps, M3 / M4 / M5 / M6 / M8, 5-piece set", "Amazon", "B0FN49CGJG", 6.49, "once",
        "M3: the base's side-cover holes (8, through the walls) and back-plate holes (6). The head's threads (M3 and "
        "up) are printed",
        "Head/README.md; Base/README.md"),
    amz("Assembly", 1, "Drill bit, 5.2 mm HSS, 2 pcs", "Amazon", "B0FN3WV6DW", 6.99, "once",
        "The tube's cross hole is 5.2 mm", "Head/README.md"),
]))

# Hardware, kits, consumables and tools the user supplies themselves (2026-10-23): left off the BOM
USER_SUPPLIED = {"B0006HUJCQ", "B003JZII34", "B000I1RSNS", "B0FN49CGJG", "B0FN3WV6DW", "B077TCDNYT", "B0F8QWCFWR",
                 "B09FF6VQ55", "B0F43RY9S6"}
SECTIONS = [(t, [l for l in lines if l[6] not in USER_SUPPLIED]) for t, lines in SECTIONS]

# What the Rev 3.0 Digi-Key order already bought counts as bought; a line it covers in full is marked ordered
def _ordered(l):
    if l[5] != "Digi-Key" or l[6] not in DK_ORDER: return l
    need = 1 if l[8] == "once" else math.ceil(l[1] / l[8])
    l = list(l); l[10] = DK_ORDER[l[6]]
    if l[9] == "" and l[10] >= need: l[9] = ORDERED
    return tuple(l)
SECTIONS = [(t, [_ordered(l) for l in lines]) for t, lines in SECTIONS]

# Amazon orders already delivered (checked against the order screen, 2026-10-23)
AMAZON_BOUGHT = {"B0CFFT1B31", "B0CM3C8KFT", "B0B81FGBLY", "B09XTV8XYK", "B0FMD5TMSH", "B0CY267GFY", "B0BWWBTL4N", "B000HBNV58", "B000DZFUPC"}
def _delivered(l):
    if l[6] not in AMAZON_BOUGHT or l[7] == 0: return l
    l = list(l); l[10] = 1 if l[8] == "once" else math.ceil(l[1] / l[8])
    if l[9] == "": l[9] = ORDERED
    return tuple(l)
SECTIONS = [(t, [_delivered(l) for l in lines]) for t, lines in SECTIONS]

# Mouser orders  (2026-11-01, invoice ) and  (2026-11-05, invoice ): the parts this
# build uses. Keyed by the line's mfr part: (mfr part bought, Mouser part, unit USD, qty bought, description or None)
MOUSER_ORDER = {
    "PCA9546ADR": ("PCA9546ADR", "595-PCA9546ADR", 1.84, 1, None),
    "RC1206FR-072K2L": ("RC1206FR-072K2L", "603-RC1206FR-072K2L", 0.025, 10, None),
    "RC1206FR-0710KL": ("RC1206FR-0710KL", "603-RC1206FR-0710KL", 0.025, 10, None),
    "BM04B-SRSS-TBT": ("BM04B-SRSS-TB(LF)(SN)", "306-BM04BSRSSTBLFSN", 0.53, 4, None),
    "A04SR04SR30K203A": ("A04SR04SR30K254B", "306-A04SR04SR30K254B", 1.63, 2,
                         "JST SR jumper, 4 positions, socket to socket, 10 in (254 mm)"),
    "RKJXM1015004": ("RKJXM1015004", "688-RKJXM1015004", 10.07, 1, None),
    "SM06B-SRSS-TB(LF)(SN)": ("SM06B-SRSS-TB(LF)(SN)", "306-M06BSRSSTBLFSNPP", 0.68, 1, None),
    "A06SR06SR30K152A": ("A06SR06SR30K203A", "306-A06SR06SR30K203A", 1.85, 1,
                         "JST SH jumper, 6 positions, socket to socket, 8 in (203 mm)"),
}
MOUSER = "Mouser invoices  (2026-11-03) and  (2026-11-05)"
MOUSER_EXTRA = {"CL31B104KBCNNNC": 10}       # bought from Mouser on top of the Digi-Key order (187-CL31B104KBCNNNC)
def _mouser(l):
    l = list(l)
    if l[4] in MOUSER_ORDER:
        mpn, spn, unit, q, desc = MOUSER_ORDER[l[4]]
        l[4], l[5], l[6], l[7], l[8], l[10], l[9] = mpn, "Mouser", spn, unit, 1, q, ORDERED
        if desc: l[2] = desc
        l[11] = l[11].replace(" Price: check Mouser", "").replace("Price: check Mouser", "").strip()
        l[12] = MOUSER + "; " + l[12]
    elif l[4] in MOUSER_EXTRA:
        l[10] += MOUSER_EXTRA[l[4]]; l[9] = ORDERED
        l[11] += f". {l[10]} bought: {l[10] - MOUSER_EXTRA[l[4]]} from Digi-Key, {MOUSER_EXTRA[l[4]]} from Mouser"
        l[12] += "; " + MOUSER
    return tuple(l)
SECTIONS = [(t, [_mouser(l) for l in lines]) for t, lines in SECTIONS]

PRINTED = [
    ("Head", "Head/stl/HueyHeadR5-GripBearingCoupons.stl", 1, "Flat, labels up. Optional: checks the head's 25.2 mm "
     "tube bore on the carbon tube (the grip now rides on O-rings)"),
    ("Head", "Head/stl/HueyHeadR5-ORingCoupon.stl", 1, "Upright. A slice of the grip's bore with one O-ring groove: "
     "fit a greased 24 x 2 O-ring and slide it on the carbon tube before printing the grip (about 2 g)"),
    ("Head", "Head/stl/HueyHeadR5-SensorSeatCoupon.stl", 1, "The same way round as in the head on its rear wall. "
     "Optional: slide the AS5600 module through it first"),
    ("Head", "Head/stl/HueyHeadR5-Body.stl", 1, "One piece: box, neck, faux friction knob, boss, sensor pod and "
     "trigger mount. On its rear wall, with tree supports under the neck, knob and tube bore; then ream the bore to a "
     "press fit on the tube"),
    ("Head", "Head/stl/HueyHeadR5-LowerPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours, no "
     "supports. The SEARCH CONT hat Rev 4's panel: the hat's four bosses grow straight up off its back"),
    ("Head", "Head/stl/HueyHeadR5-UpperPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours"),
    ("Head", "Head/stl/HueyHeadR5-Trigger.stl", 1, "On either flat side"),
    ("Head", "Head/stl/HueyHeadR5-Hat-Cap.stl", 1, "Base down, as exported: the stick's socket opens on the bed. "
     "Push it onto the switch's stick last"),
    ("Head", "Head/stl/HueyHeadR5-ThrottleGrip.stl", 1, "Upright, bottom end down; no supports"),
    ("Head", "Head/stl/HueyHeadR5-FrictionCollar.stl", 1, "Bottom face down, O-ring groove up"),
    ("Head", "Head/stl/HueyHeadR5-Pinion.stl", 1, "As exported, shoulder up; fit it shoulder down. The magnet shaft presses into its hex"),
    ("Head", "Head/stl/HueyHeadR5-MagnetShaft.stl", 1, "Cap face down, pin up"),
    ("Base", "Base/stl/coupons/coupon_trunnion_6808.stl, coupon_bearing_seat_6808.stl, coupon_dowel_hole.stl, "
     "coupon_tube_socket.stl", 1,
     "Fit-test coupons: the trunnion's and the seat's 0 fitted (2026-11-08), and the tube socket (Rev 3's) fits; print "
     "the dowel-hole coupon first and tune DOWEL_CLR in mk3_rev4.py"),
    ("Base", "Base/stl/frame.stl", 1, "Plate down"),
    ("Base", "Base/stl/shell.stl", 1, "Top down: the bearing half-seats, the slot and the brake strap's bay open "
     "upward. The knob's seat is sunk into the top, on the bed, and its floor slopes 30 deg: support it from the bed, "
     "in the seat only"),
    ("Base", "Base/stl/lever_sensor.stl", 1, "On its joint face, trunnion up. Support only the up-stop lug's "
     "inner face"),
    ("Base", "Base/stl/lever_cable.stl", 1, "On its joint face, trunnion up. Support only the up-stop lug's "
     "inner face"),
    ("Base", "Base/stl/lever_dowel.stl", 4, "Standing on end"),
    ("Base", "Base/stl/cover_cable.stl, cover_sensor.stl", 1, "One each, on the outer face"),
    ("Base", "Base/stl/strap.stl", 1, "On its side, the nut's slot up: its bending then runs along the layers. "
     "No supports"),
    ("Base", "Base/stl/strut_collar.stl", 1, "Standing on one end. The same part as Rev 3's"),
    ("Base", "Base/stl/friction_knob.stl", 1, "The MkII knob with an M5 hex pocket, its floor 11 mm up, and a "
     "pocket in its underside for the optional spring. Underside down, hex pocket open at the top"),
]
SOURCES = [
    ("HeliSR Rev 4.0 board", "PCB/HeliSR (parts checked against HeliSR_Rev4.0.kicad_pcb)",
     "Designed and checked, not ordered yet"),
    ("HeliSR Rev 3.0 board", "Its Digi-Key cart (ORDER in tools/make_bom.py)", "Replaced by Rev 4.0 and removed from the repo. Bare PCB ordered "
     "from OSH Park on 2026-10-21, and its parts in the Rev 3.0 Digi-Key order; its order data still supplies the cables and "
     "head switches"),
    ("SearchHat Rev 1.0 board", "PCB/SearchHat (tools/gen_searchhat.py)", "The SEARCH CONT hat Rev 4's breakout: "
     "designed and checked (DRC clean), not ordered yet"),
    ("Huey head", "Head", "Current head design: Rev 5, cut to the real UH-1 panels' dimensions, with printed "
     "threads and the SEARCH CONT hat on the SearchHat board"),
    ("MkIII base Rev 4", "Base (mk3_rev4.py, on the shared library Base/mk3_rev3.py and Base/mk3_pivot.py)",
     "Current base, 73 mm wide; its first frame, shell and lever were printed and built 2026-11-08: check the orange lines"),
    ("Prices", "Digi-Key cart 2026-10-19 (JST headers 2026-10-22; Rev 4.0's new parts and cables 2026-10-27); Amazon "
     "listings 2026-10-22; OSH Park order 2026-10-21",
     "Pack prices, before shipping and tariff"),
]

# ---- workbook ---------------------------------------------------------------------------------------------------
F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
thin = Side(style="thin", color="BFBFBF"); box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap, centre = Alignment(wrap_text=True, vertical="top"), Alignment(horizontal="center", vertical="top")
USD = '"$"#,##0.00;-"$"#,##0.00;"-"'
NAVY, SECT = "1F3864", "D9E1F2"
def header(ws, cols, widths, row):
    for c, (h, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row, c, h); cell.font = F(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(vertical="center", wrap_text=True); cell.border = box
        ws.column_dimensions[cell.column_letter].width = w
    ws.row_dimensions[row].height = 30
def setup(ws, title, note, ncol, h=44):
    ws["A1"] = title; ws["A1"].font = F(bold=True, size=14)
    ws["A2"] = note; ws["A2"].font = F(italic=True, color="595959"); ws["A2"].alignment = wrap
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncol); ws.row_dimensions[2].height = h
    ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
def section(ws, r, title, ncol):
    ws.cell(r, 1, title).font = F(bold=True)
    for c in range(1, ncol + 1): ws.cell(r, c).fill = PatternFill("solid", fgColor=SECT); ws.cell(r, c).border = box
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)
# Tick boxes: classic form checkboxes (VML, the kind Excel 2007 wrote), which OpenOffice, LibreOffice and every Excel
# open. openpyxl can't write them, so tick() notes each one and add_checkboxes() adds them after saving. Each box is
# linked to a hidden cell past the last column (TRUE when ticked); a conditional format strikes the line through.
TICKS = {}                                                     # sheet title -> [(row, linked cell)]
def tick(ws, r, ncol):
    col = get_column_letter(ncol + 1)
    ws.cell(r, ncol + 1, False); ws.column_dimensions[col].hidden = True
    TICKS.setdefault(ws.title, []).append((r, f"'{ws.title}'!${col}${r}"))
def strike_when_ticked(ws, r0, r1, ncol):
    col = get_column_letter(ncol + 1)
    ws.conditional_formatting.add(f"A{r0}:{get_column_letter(ncol)}{r1}", FormulaRule(
        formula=[f"${col}{r0}=TRUE"], stopIfTrue=False, font=Font(strike=True, color="808080")))
def add_checkboxes(path, sheetnames):
    import shutil, zipfile
    REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    def vml(k, ticks):
        out = ['<xml xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" '
               'xmlns:x="urn:schemas-microsoft-com:office:excel">',
               f'<o:shapelayout v:ext="edit"><o:idmap v:ext="edit" data="{k}"/></o:shapelayout>',
               '<v:shapetype id="_x0000_t201" coordsize="21600,21600" o:spt="201" path="m,l,21600r21600,l21600,xe">'
               '<v:stroke joinstyle="miter"/><v:path shadowok="f" o:extrusionok="f" strokeok="f" fillok="f" '
               'o:connecttype="rect"/><o:lock v:ext="edit" shapetype="t"/></v:shapetype>']
        for j, (r, ref) in enumerate(ticks):
            out.append(f'<v:shape id="_x0000_s{k * 1024 + 1 + j}" type="#_x0000_t201" style="position:absolute;'
                       'margin-left:0;margin-top:0;width:24pt;height:14pt;z-index:1;visibility:visible" filled="f" '
                       'fillcolor="window [65]" stroked="f" strokecolor="windowText [64]" o:insetmode="auto">'
                       '<v:textbox style="mso-direction-alt:auto" o:singleclick="f"><div style="text-align:left"></div>'
                       '</v:textbox><x:ClientData ObjectType="Checkbox">'
                       f'<x:Anchor>0, 12, {r - 1}, 2, 0, 36, {r - 1}, 19</x:Anchor><x:SizeWithCells/><x:AutoFill>False</x:AutoFill>'
                       '<x:AutoLine>False</x:AutoLine><x:TextVAlign>Top</x:TextVAlign>'
                       f'<x:FmlaLink>{ref}</x:FmlaLink><x:NoThreeD/></x:ClientData></v:shape>')
        out.append("</xml>")
        return "\n".join(out)
    sheets = {f"xl/worksheets/sheet{i + 1}.xml": (i + 1, TICKS[t]) for i, t in enumerate(sheetnames) if t in TICKS}
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        names = zin.namelist()
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in sheets:
                data = data.decode("utf-8").replace("</worksheet>", f'<legacyDrawing xmlns:r="{REL}" r:id="rIdTick"/>'
                                                    "</worksheet>").encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                data = data.decode("utf-8").replace("</Types>", '<Default Extension="vml" ContentType="application/'
                                                    'vnd.openxmlformats-officedocument.vmlDrawing"/></Types>').encode("utf-8")
            elif item.filename.startswith("xl/worksheets/_rels/"):
                continue                                       # rewritten below
            zout.writestr(item, data)
        for sheet, (k, ticks) in sheets.items():
            zout.writestr(f"xl/drawings/vmlDrawing{k}.vml", vml(k, ticks))
            rels = sheet.replace("worksheets/", "worksheets/_rels/") + ".rels"
            t = (zin.read(rels).decode("utf-8") if rels in names else
                 f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.'
                 'openxmlformats.org/package/2006/relationships"></Relationships>')
            zout.writestr(rels, t.replace("</Relationships>", f'<Relationship Id="rIdTick" Type="{REL}/vmlDrawing" '
                                          f'Target="../drawings/vmlDrawing{k}.vml"/></Relationships>'))
        for rels in names:
            if rels.startswith("xl/worksheets/_rels/") and rels.replace("_rels/", "")[:-5] not in sheets:
                zout.writestr(rels, zin.read(rels))
    shutil.move(tmp, path)
def link(cell, supplier, spn):
    url = {"Digi-Key": "https://www.digikey.com/en/products/result?keywords=", "Amazon": "https://www.amazon.com/dp/",
           "OSH Park": "https://oshpark.com/", "Mouser": "https://www.mouser.com/c/?q="}.get(supplier)
    if url and (spn or supplier == "OSH Park"): cell.hyperlink = url + spn; cell.font = F(color="0563C1", underline="single")

wb = Workbook(); wb.calculation = CalcProperties(fullCalcOnLoad=True)
ws = wb.active; ws.title = "Final BOM"
COLS = ["Done", "#", "Where", "Qty per collective", "Pack", "Packs needed", "Packs bought", "Packs to order",
        "Description", "Manufacturer", "Mfr part number", "Supplier", "Supplier part number", "Pack price", "To spend",
        "Notes", "Source"]
NC = len(COLS)
setup(ws, "Heli Collective - final BOM",
      "Everything bought for one collective: the HeliSR Rev 4.0 board (the bare PCB from OSH Park, its parts from "
      "Digi-Key and Mouser), the Huey head Rev 5 and the MkIII base Rev 4. Packs bought counts what's already "
      "ordered: the Digi-Key order placed for Rev 3.0 (Rev 4.0 shares most of its parts) and the Mouser orders of 2026-11-01 and 2026-11-05. Blue line: "
      "already ordered. Green: covered by a kit or pack priced on another line. Orange: size taken from the base's CAD, not from a parts list, so check "
      "before ordering. Prices are pack prices: Digi-Key cart (2026-10-23), Mouser invoices, Amazon listings "
      "(2026-10-22 and 2026-10-23) and the OSH Park order, before shipping and tariff. Tick Done to strike a line "
      "through.", NC, 58)
ws["A3"] = "Collectives to build"; ws["A3"].font = F(bold=True); ws.merge_cells("A3:C3")
ws["D3"] = 1; ws["D3"].font = F(bold=True, color="0000FF"); ws["D3"].fill = PatternFill("solid", fgColor="FFFF00")
ws["D3"].alignment = centre; ws["D3"].border = box
ws["E3"] = ("Edit the yellow cells: collectives to build here, and Packs bought for anything you already have. Packs "
            "round up; lines marked once are one per order, however many you build.")
ws["E3"].font = F(italic=True, color="595959"); ws.merge_cells(start_row=3, start_column=5, end_row=3, end_column=NC)
HR = 5; header(ws, COLS, [6, 4, 15, 9, 6, 8, 8, 8, 36, 13, 16, 9, 21, 9, 10, 46, 28], HR)
r, n, subtotals, rows = HR, 0, [], []
for title, lines in SECTIONS:
    r += 1; section(ws, r, title, NC); first = r + 1
    for where, qty, desc, mfr, mpn, sup, spn, unit, pack, status, bought, notes, source in lines:
        r += 1; n += 1
        need = f"=IF($D$3>0,D{r},0)" if pack == "once" else f"=ROUNDUP(D{r}*$D$3/E{r},0)"   # once: one per order
        vals = ["", n, where, qty, "once" if pack == "once" else pack, need, bought, f"=MAX(0,F{r}-G{r})", desc, mfr,
                mpn, sup, spn, unit, f'=IF(N{r}="","",H{r}*N{r})', ("CHECK: " if status == CHECK else "") + notes, source]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
            if status in FILL: cell.fill = PatternFill("solid", fgColor=FILL[status])
        for c in (1, 2, 4, 5, 6, 7, 8): ws.cell(r, c).alignment = centre
        tick(ws, r, NC)
        ws.cell(r, 7).font = F(color="0000FF")
        if status not in FILL: ws.cell(r, 7).fill = PatternFill("solid", fgColor="FFFFCC")
        for c in (14, 15): ws.cell(r, c).number_format = USD
        link(ws.cell(r, 13), sup, spn)
        rows.append((r, where, qty, desc, mfr, mpn, sup, spn, unit, pack, bought, notes))
    r += 1
    ws.cell(r, 14, "Subtotal").font = F(bold=True)
    ws.cell(r, 15, f"=SUM(O{first}:O{r - 1})").font = F(bold=True); ws.cell(r, 15).number_format = USD
    subtotals.append(r)
last_item = r
strike_when_ticked(ws, HR + 1, last_item, NC)
r += 2
ws.cell(r, 14, "Still to buy").font = F(bold=True)
ws.cell(r, 15, "=" + "+".join(f"O{s}" for s in subtotals)).font = F(bold=True); ws.cell(r, 15).number_format = USD
r += 1
ws.cell(r, 14, "Whole build").font = F(bold=True)
ws.cell(r, 15, f"=SUMPRODUCT(F{HR + 1}:F{last_item},N{HR + 1}:N{last_item})").font = F(bold=True)
ws.cell(r, 15).number_format = USD
r += 1
ws.cell(r, 14, "Unpriced lines").font = F(bold=True)
ws.cell(r, 15, f'=COUNTIFS(B{HR + 1}:B{last_item},">0",N{HR + 1}:N{last_item},"")').font = F(bold=True)
r += 1
ws.cell(r, 1, "Still to buy counts the packs to order; whole build counts every pack needed, bought or not. Both leave "
        "out the unpriced lines: generic hardware and wire.").font = F(italic=True, color="595959")
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
ws.freeze_panes = f"D{HR + 1}"; ws.print_title_rows = f"{HR}:{HR}"

ws2 = wb.create_sheet("Printed parts")
setup(ws2, "Heli Collective - printed parts", "The print set for the Huey head Rev 5 and the MkIII base Rev 4, with the "
      "orientation each README gives. Print the coupons first. Paths are from the repository root. Tick Done to "
      "strike a line through.", 6)
header(ws2, ["Done", "#", "Assembly", "File", "Qty", "Print"], [6, 4, 10, 70, 6, 70], 4)
for i, (asm, f, q, note) in enumerate(PRINTED, 1):
    for c, v in enumerate(["", i, asm, f, q, note], 1):
        cell = ws2.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
        if note.startswith("CHECK"): cell.fill = PatternFill("solid", fgColor=FILL[CHECK])
    ws2.cell(4 + i, 2).alignment = ws2.cell(4 + i, 5).alignment = centre
    tick(ws2, 4 + i, 6)
strike_when_ticked(ws2, 5, 4 + len(PRINTED), 6)
ws2.freeze_panes = "A5"

ws4 = wb.create_sheet("Sources")
setup(ws4, "Heli Collective - sources", "Where each part of this BOM comes from. Regenerate with tools/make_bom.py.", 3)
header(ws4, ["Part", "Folder or document", "Status"], [22, 70, 60], 4)
for i, row in enumerate(SOURCES, 1):
    for c, v in enumerate(row, 1):
        cell = ws4.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box

wb.save(OUT)
add_checkboxes(OUT, wb.sheetnames)
print(f"{len(fps)} board parts checked; {n} BOM lines, {len(PRINTED)} printed-part lines; "
      f"wrote {OUT}")
