# Writes BOM/Heli_Collective_BOM.xlsx: the parts list for one Heli Collective (HeliSR Rev 4.0 board, SearchHat
# Rev 1.0 board, Huey head Rev 5, MkIII base Rev 4) and the print list.
# The board's parts are checked against PCB/HeliSR/HeliSR_Rev4.0.kicad_pcb (the script stops if they disagree).
# Prices: Mouser, Amazon and OSH Park listings checked 2026-11-11, USD, before shipping. Tariff is the estimate Mouser
# shows for delivery to the US. Buy is the cheapest quantity at the listed price breaks: 10 can cost less than 8.
# usage: python tools/make_bom.py [out.xlsx]     (any Python 3 with openpyxl)
import os, re, shutil, sys, zipfile
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "BOM", "Heli_Collective_BOM.xlsx")
BOARD_PCB = os.path.join(ROOT, "PCB", "HeliSR", "HeliSR_Rev4.0.kicad_pcb")
CHECKED = "2026-11-11"

# ---- parts ------------------------------------------------------------------------------------------------------
# part(where, qty used, description, manufacturer, mfr part, supplier, supplier part, price breaks, tariff, notes)
# Price breaks: [(qty, unit price)]. For Amazon and OSH Park the unit is the pack or order the listing sells (named in
# the description); pack says how many pieces it holds.
def part(where, qty, desc, mfr, mpn, sup, spn, breaks, tariff=0.0, notes="", pack=1):
    return dict(where=where, qty=qty, desc=desc, mfr=mfr, mpn=mpn, sup=sup, spn=spn, breaks=breaks, tariff=tariff,
                notes=notes, pack=pack)
def kit(where, qty, desc, notes=""):
    return part(where, qty, desc, "", "", "Screw kit", "", None, notes=notes)
def setkit(where, qty, desc, notes=""):
    return part(where, qty, desc, "", "", "Set screw kit", "", None, notes=notes)

# HeliSR Rev 4.0: (refs, value, footprint) as in the board file, then what to buy
BOARD = [
    (("U1, U2", "74HC165", "SOIC-16_3.9x9.9mm_P1.27mm"),
     part("U1, U2", 2, "Shift register, 74HC165, SOIC-16", "onsemi", "MC74HC165ADR2G", "Mouser", "863-MC74HC165ADR2G",
          [(1, 0.40), (10, 0.351)], 0, "Front, under the Pro Micro: solder before the sockets")),
    (("RN1, RN2", "10k x8 bussed", "R_Array_SIP9"),
     part("RN1, RN2", 2, "Resistor network, 8 x 10 kOhm bussed, SIP-9", "Bourns", "4609X-101-103LF", "Mouser",
          "652-4609X-1LF-10K", [(1, 0.29), (10, 0.194)], 0.21, "Pin 1 (dot) is the common pin: square pad")),
    (("C1, C2, C4", "100nF", "C_1206_3216Metric"),
     part("C1, C2, C4", 3, "Capacitor, 100 nF, 50 V, X7R, 1206", "Samsung", "CL31B104KBCNNNC", "Mouser",
          "187-CL31B104KBCNNNC", [(1, 0.14), (10, 0.08)], 0.12, "C1, C2 front; C4 back")),
    (("C3", "22uF", "C_1206_3216Metric"),
     part("C3", 1, "Capacitor, 22 uF, 10 V, X5R, 1206", "Samsung", "CL31A226KPHNNNE", "Mouser", "187-CL31A226KPHNNNE",
          [(1, 0.47), (10, 0.283)], 0.12, "Front, between U1 and U2")),
    (("U3", "PCA9546A", "SOIC-16_3.9x9.9mm_P1.27mm"),
     part("U3", 1, "I2C switch, 4 channels, SOIC-16 (narrow)", "Texas Instruments", "PCA9546ADR", "Mouser",
          "595-PCA9546ADR", [(1, 1.84), (10, 1.36)], 0, "Back")),
    (("R1-R8", "2.2k", "R_1206_3216Metric"),
     part("R1-R8", 8, "Resistor, 2.2 kOhm, 1 %, 1/4 W, 1206", "YAGEO", "RC1206FR-072K2L", "Mouser",
          "603-RC1206FR-072K2L", [(1, 0.10), (10, 0.025), (100, 0.017)], 0.08, "Back: I2C pull-ups, a pair per port")),
    (("R9-R11", "10k", "R_1206_3216Metric"),
     part("R9-R11", 3, "Resistor, 10 kOhm, 1 %, 1/4 W, 1206", "YAGEO", "RC1206FR-0710KL", "Mouser",
          "603-RC1206FR-0710KL", [(1, 0.10), (10, 0.025), (100, 0.017)], 0.08, "Back")),
    (("SW1", "TL1015AF160QG", "SW_TL1015AF160QG"),
     part("SW1", 1, "Tactile switch, SMD, 3.9 x 2.9 mm (reset)", "E-Switch", "TL1015AF160QG", "Mouser", "612-TL1015AF",
          [(1, 0.47), (10, 0.417)], 0.30, "Leave its four ground tabs unsoldered")),
    (("J1, J2", None, "JST_SH_BM10B-SRSS-TB_1x10-1MP_P1.00mm_Vertical"),
     part("J1, J2", 2, "JST SH header, 10 pins, 1.0 mm, SMD, top entry", "JST", "BM10B-SRSS-TB(LF)(SN)", "Mouser",
          "306-BM10BSRSSTBLFSN", [(1, 0.93), (10, 0.793)], 0.30, "Switch inputs IN1-IN8, IN9-IN16")),
    (("J11-J14", None, "JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical"),
     part("J11-J14", 4, "JST SH header, 4 pins, 1.0 mm, SMD, top entry", "JST", "BM04B-SRSS-G-TB(LF)(SN)", "Mouser",
          "306-4BSRSSGTBLP", [(1, 0.63), (10, 0.546)], 0.30, "Sensor ports AX1-AX4: 1 SDA, 2 GND, 3 VCC, 4 SCL")),
    (("J7, J8", None, "PinSocket_1x12_P2.54mm_Vertical"),
     part("J7, J8", 2, "Socket header, female, 1 x 12, 2.54 mm, through hole", "Harwin", "M20-7821246", "Mouser",
          "855-M20-7821246", [(1, 1.63), (10, 1.33)], 0.30, "Pro Micro sockets: solder last")),
]

SECTIONS = [
    ("HeliSR Rev 4.0 board", [p for _, p in BOARD] + [
        part("PCB", 1, "HeliSR Rev 4.0 bare PCB, 2 layers, 1.6 mm, 39.3 x 33.6 mm (OSH Park makes 3)", "", "", "OSH Park",
             "", [(1, 10.20)], 0, "Upload PCB/HeliSR/HeliSR_Rev4.0_Gerbers.zip"),
        part("J7, J8", 1, "Pro Micro 5 V / 16 MHz (ATmega32U4), USB-C, with header pins", "OSOYOO", "", "Amazon",
             "B0B81FGBLY", [(1, 11.99)], 0, "Plugs into J7/J8; runs the HeliSR firmware"),
    ]),
    ("SearchHat Rev 1.0 board (SEARCH CONT hat)", [
        part("SW1", 1, "8-direction stick switch with centre push", "ALPS Alpine", "RKJXM1015004", "Mouser",
             "688-RKJXM1015004", [(1, 10.07), (10, 9.47)], 0, "Directions to IN9-IN12, centre push to IN15"),
        part("J1", 1, "JST SH header, 6 pins, 1.0 mm, SMD, side entry", "JST", "SM06B-SRSS-TB(LF)(SN)", "Mouser",
             "306-M06BSRSSTBLFSNPP", [(1, 0.68), (10, 0.579)], 0.30, "Back of the board"),
        part("PCB", 1, "SearchHat Rev 1.0 bare PCB, 2 layers, 1.6 mm, 22 x 29 mm (OSH Park makes 3)", "", "", "OSH Park",
             "", [(1, 4.95)], 0, "Upload PCB/SearchHat/SearchHat_Rev1.0_Gerbers.zip"),
    ]),
    ("Wiring", [
        part("J1, J2", 1, "JST SR jumper, 10 positions, 12 in (305 mm)", "JST", "A10SR10SR30K305A", "Mouser",
             "306-A10SR10SR30K305A", [(1, 3.45), (10, 3.03)], 0, "Cut in half: one pigtail for J1, one for J2"),
        part("AX1, AX4", 2, "JST SR jumper, 4 positions, 10 in (254 mm)", "JST", "A04SR04SR30K254B", "Mouser",
             "306-A04SR04SR30K254B", [(1, 1.63), (10, 1.39)], 0, "Cut in half for the board-end pigtails"),
        part("AX1 lead", 1, "Flat ribbon cable, 4 conductors, 24 AWG, 1 m", "KYOCERA AVX", "902220736004000", "Mouser",
             "581-902220736004000", [(1, 3.35), (5, 2.99)], 0.26,
             "Base sensor to the AX1 pigtail. Keep the order SDA, GND, VCC, SCL"),
        part("SearchHat J1", 1, "JST SR jumper, 6 positions, 8 in (203 mm)", "JST", "A06SR06SR30K203A", "Mouser",
             "306-A06SR06SR30K203A", [(1, 1.85), (10, 1.57)], 0, "Cut in half; one end to J1, the wires to J2's loom"),
        part("USB", 1, "USB 2.0 cable, USB-A to USB-C, 2 m", "Stewart Connector", "SC-2CAK020M", "Mouser",
             "530-SC-2CAK020M", [(1, 7.33), (10, 6.24)], 0.08,
             "Cut about 15 cm from the C plug; splice it back on inside the head"),
    ]),
    ("Angle sensors", [
        part("AX1, AX4", 2, "AS5600 magnetic encoder module with magnet, pack of 4", "WWZMDiB", "", "Amazon",
             "B0CM3C8KFT", [(1, 9.99)], 0, "AX1 in the base, AX4 in the head. Prepare them as PCB/HeliSR/README.md says",
             pack=4),
    ]),
    ("Huey head: switches", [
        part("IN3-IN6", 2, "Toggle switch, SPDT, ON-OFF-ON, M12 bushing", "APEM", "639H/2", "Mouser", "642-639H2",
             [(1, 7.86), (10, 6.87)], 0, "LDG LT EXT / RETR, SL ON / STOW"),
        part("IN1, IN2", 1, "Toggle switch, SPDT, (ON)-OFF-(ON), M12 bushing, sealed", "APEM", "637NH/2", "Mouser",
             "642-637NH2", [(1, 16.27), (10, 15.06)], 0, "GOV RPM INCR / DECR"),
        part("IN7", 1, "Toggle switch, ON-ON, M12 bushing", "APEM", "636H/2", "Mouser", "642-636H2",
             [(1, 7.55), (10, 6.52)], 0, "LDG LT ON"),
        part("IN13", 1, "Push button, 12 mm, SPST-NO momentary, black", "Same Sky", "PB4-M-BK-D-67", "Mouser",
             "179-PB4-M-BK-D-67", [(1, 2.52), (10, 2.07)], 0.20, "STOP REL"),
        part("IN14", 1, "Tactile switch, 6 x 6 mm, 5 mm high, through hole", "TE Connectivity", "1825910-6", "Mouser",
             "650-1825910-6", [(1, 0.12), (10, 0.106)], 0.30, "Starter trigger"),
    ]),
    ("Huey head: hardware", [
        part("HeliSR board", 4, "Spacer, M3, 4 mm, PVC", "Bivar", "SRS-4-4MM", "Mouser", "749-SRS-4-4MM",
             [(1, 0.10), (10, 0.059)], 0.15, "Between the rear wall and the board"),
        kit("HeliSR board", 4, "M3 x 12 countersunk screw + M3 nut"),
        kit("Panels", 8, "M3 x 16 countersunk screw", "4 per panel"),
        kit("SearchHat board", 4, "M2 x 8 countersunk screw", "Self-tapping into the lower panel's bosses"),
        kit("Friction collar", 1, "M4 x 12 countersunk screw + M4 nut"),
        kit("Trigger pull stop seat", 1, "M2 x 8 countersunk screw"),
        setkit("Tube boss", 1, "M5 x 8 set screw", "Pins the tube in the head"),
        setkit("Trigger pull stop", 1, "M3 x 4 set screw"),
        part("Trigger pivot", 1, "M3 countersunk screws, M3 x 20 to 40 assortment, 100 pcs", "", "", "Amazon",
             "B0BYXS4BTF", [(1, 9.99)], 0, "Uses one M3 x 25"),
        part("Throttle grip", 4, "O-ring, 24 mm ID x 2 mm, nitrile, pack of 50", "FOCMKEAS", "", "Amazon", "B0BWWBTL4N",
             [(1, 6.89)], 0, "Grease lightly with silicone grease", pack=50),
        part("Trigger", 1, "Pen spring, 4 mm OD x 50 mm, pack of 10", "uxcell", "", "Amazon", "B0GCZGNBYH",
             [(1, 6.99)], 0, "Cut to about 13 mm", pack=10),
        part("Head box", 1, "Split shot lead weights, assorted (optional ballast)", "SANWEAL", "", "Amazon", "B0H6J3X6GL",
             [(1, 5.99)], 0, "Only if a stronger strut lifts the lever"),
    ]),
    ("MkIII base Rev 4", [
        part("Pivot", 2, "Ball bearing 6808-2RS, 40 x 52 x 7 mm, pack of 2", "", "6808-2RS", "Amazon", "B012BIHBTQ",
             None, 0, "Any 6808-2RS fits; price varies", pack=2),
        part("Tube", 1, "Carbon fibre tube, wrapped, 25 mm OD x 23 mm ID x 500 mm, pack of 2", "MECCANIXITY", "",
             "Amazon", "B0CFFT1B31", [(1, 27.49)], 0, "Used whole, uncut", pack=2),
        part("Strut", 1, "Gas strut, 6 in eye to eye, 45 N, pack of 2", "X AUTOHAUX", "", "Amazon", "B0CY267GFY",
             [(1, 13.69)], 0, "Cylinder end on the anchor", pack=2),
        part("Lever, shell, brake hinge", 9, "M4 socket head screws, M4 x 30 to 50, with nuts (200 pcs)", "HELIFOUNER",
             "", "Amazon", "B0CDSKK7V1", [(1, 9.99)], 0, "Uses 4 x M4 x 35 and 5 x M4 x 50, with 9 nuts"),
        part("Socket mouth", 1, "Hose clamp, worm drive, 25-40 mm, pack of 25", "MISPIRE", "", "Amazon", "B0F8QWCFWR",
             [(1, 18.99)], 0, "", pack=25),
        part("Brake", 1, "M5 x 35 hex-head bolt", "", "", "Hardware store", "", None, 0, "Not in the kits"),
        kit("Brake", 1, "M5 nut"),
        part("Brake (optional)", 1, "Compression spring, 10 mm OD, 1.0 mm wire, 15 mm long, pack of 10", "", "",
             "Amazon", "B09FF6VQ55", [(1, 11.10)], 0, "Softens the brake knob", pack=10),
        part("Brake strap", 1, "Felt tape, self-adhesive, 1.5 mm, 3/4 in x 50 ft", "FindTape", "", "Amazon",
             "B077TCDNYT", [(1, 24.98)], 0, "Cut 51 x 16 mm"),
        kit("Strut eyes", 2, "M4 x 16 countersunk screw + M4 nut"),
        kit("Strut collar", 2, "M4 x 12 countersunk screw + M4 nut"),
        kit("Side covers", 8, "M3 x 12 countersunk screw"),
        part("Desk mounting", 4, "#10 x 1-1/2 in pan head wood screw, pack of 50", "", "", "Amazon", "B0F43RY9S6",
             [(1, 8.29)], 0, "", pack=50),
    ]),
    ("Screw kits, supplies and tools", [
        part("Screw kit", 1, "Countersunk hex socket screw kit, M2-M5, with nuts (1715 pcs)", "AvrestYPT", "", "Amazon",
             "B0FMD5TMSH", [(1, 17.99)], 0, "Every countersunk screw and nut marked Screw kit"),
        part("Set screw kit", 1, "Set screw kit, M3-M8 (500 pcs)", "HIQTRADEBYJJ", "", "Amazon", "B0DG33R714",
             [(1, 8.96)], 0, "Both set screws"),
        part("Board", 1, "Solder paste, low temperature (Sn42/Bi57.6/Ag0.4), 15 g syringe", "Chip Quik", "SMDLTLFP",
             "Mouser", "910-SMDLTLFP", [(1, 15.95)], 0, "Optional: the board can be hand soldered"),
        part("Bearings", 1, "White lithium grease, 1.5 oz", "Permatex", "", "Amazon", "B000HBNV58", [(1, 3.99)]),
        part("O-rings", 1, "Silicone grease, 0.5 oz", "Danco", "", "Amazon", "B000DZFUPC", [(1, 5.68)]),
        part("Magnets", 1, "Super glue gel, 0.14 fl oz", "Loctite", "", "Amazon", "B0006HUJCQ", [(1, 3.82)]),
        part("AS5600 modules", 1, "Mini hot glue sticks, 100 pack", "Surebonder", "", "Amazon", "B003JZII34",
             [(1, 5.97)], 0, "For a mini glue gun"),
        part("Screws", 1, "Threadlocker, blue 242, 6 ml", "Loctite", "", "Amazon", "B000I1RSNS", [(1, 7.03)]),
        part("Base", 1, "Tap set, M3 / M4 / M5 / M6 / M8", "", "", "Amazon", "B0FN49CGJG", [(1, 6.49)], 0,
             "M3: the side cover holes"),
        part("Tube", 1, "Drill bit, 5.2 mm HSS, 2 pcs", "", "", "Amazon", "B0FN3WV6DW", [(1, 6.99)], 0,
             "The tube's cross hole"),
    ]),
]

PRINTED = [
    ("Head", "Head/stl/HueyHeadR5-GripBearingCoupons.stl", 1, "Optional fit test: flat, labels up"),
    ("Head", "Head/stl/HueyHeadR5-ORingCoupon.stl", 1, "Fit test for the grip's O-rings: upright"),
    ("Head", "Head/stl/HueyHeadR5-SensorSeatCoupon.stl", 1, "Optional fit test for the AS5600 module"),
    ("Head", "Head/stl/HueyHeadR5-Body.stl", 1, "On its rear wall, tree supports under the neck, knob and tube bore"),
    ("Head", "Head/stl/HueyHeadR5-LowerPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours"),
    ("Head", "Head/stl/HueyHeadR5-UpperPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours"),
    ("Head", "Head/stl/HueyHeadR5-Trigger.stl", 1, "On either flat side"),
    ("Head", "Head/stl/HueyHeadR5-Hat-Cap.stl", 1, "Base down"),
    ("Head", "Head/stl/HueyHeadR5-ThrottleGrip.stl", 1, "Upright, bottom end down, no supports"),
    ("Head", "Head/stl/HueyHeadR5-FrictionCollar.stl", 1, "Bottom face down"),
    ("Head", "Head/stl/HueyHeadR5-Pinion.stl", 1, "Shoulder up"),
    ("Head", "Head/stl/HueyHeadR5-MagnetShaft.stl", 1, "Cap face down"),
    ("Base", "Base/stl/coupons/ (all four)", 1, "Fit tests: print these first"),
    ("Base", "Base/stl/frame.stl", 1, "Plate down"),
    ("Base", "Base/stl/shell.stl", 1, "Top down; support only the knob's seat"),
    ("Base", "Base/stl/lever_sensor.stl", 1, "On its joint face; support only the up-stop lug"),
    ("Base", "Base/stl/lever_cable.stl", 1, "On its joint face; support only the up-stop lug"),
    ("Base", "Base/stl/lever_dowel.stl", 4, "Standing on end"),
    ("Base", "Base/stl/cover_cable.stl, cover_sensor.stl", 1, "One each, outer face down"),
    ("Base", "Base/stl/strap.stl", 1, "On its side, nut slot up, no supports"),
    ("Base", "Base/stl/strut_collar.stl", 1, "Standing on one end"),
    ("Base", "Base/stl/friction_knob.stl", 1, "Underside down"),
]

# ---- check the board's parts against the board file -------------------------------------------------------------
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
    for p in refs.split(", "):
        m = re.fullmatch(r"([A-Z]+)(\d+)-[A-Z]*(\d+)", p)
        r += [f"{m.group(1)}{k}" for k in range(int(m.group(2)), int(m.group(3)) + 1)] if m else [p]
    return r
fps = footprints(BOARD_PCB)
listed = [r for (refs, _, _), _ in BOARD for r in expand(refs)]
assert sorted(listed) == sorted(fps) and len(set(listed)) == len(listed), sorted(set(fps) ^ set(listed))
for (refs, value, fpname), p in BOARD:
    assert p["qty"] == len(expand(refs)), refs
    for ref in expand(refs):
        assert fps[ref][0] == fpname and (value is None or fps[ref][1] == value), (ref, fps[ref], fpname, value)

# ---- how many to buy: the cheapest quantity at the price breaks ---------------------------------------------------
def buy(p):
    if not p["breaks"]: return None, None
    if p["sup"] != "Mouser": return -(-p["qty"] // p["pack"]), p["breaks"][0][1]     # whole packs
    unit = lambda n: [u for q, u in p["breaks"] if q <= n][-1]
    best = min([p["qty"]] + [q for q, _ in p["breaks"] if q > p["qty"]], key=lambda n: (n * unit(n), n))
    return best, unit(best)

# ---- spreadsheet -------------------------------------------------------------------------------------------------
F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
thin = Side(style="thin", color="BFBFBF"); box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap, centre = Alignment(wrap_text=True, vertical="top"), Alignment(horizontal="center", vertical="top")
USD, USD3, PCT = '"$"#,##0.00', '"$"#,##0.00#', "0%"
NAVY, SECT = "1F3864", "D9E1F2"
LINKS = {"Mouser": "https://www.mouser.com/ProductDetail/", "Amazon": "https://www.amazon.com/dp/",
         "OSH Park": "https://oshpark.com/"}

def header(ws, cols, widths, row):
    for c, (h, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row, c, h); cell.font = F(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(vertical="center", wrap_text=True); cell.border = box
        ws.column_dimensions[cell.column_letter].width = w
    ws.row_dimensions[row].height = 30
def title(ws, text, note, ncol):
    ws["A1"] = text; ws["A1"].font = F(bold=True, size=14)
    ws["A2"] = note; ws["A2"].font = F(italic=True, color="595959"); ws["A2"].alignment = wrap
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncol); ws.row_dimensions[2].height = 40
    ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
def section(ws, r, text, ncol):
    ws.cell(r, 1, text).font = F(bold=True)
    for c in range(1, ncol + 1): ws.cell(r, c).fill = PatternFill("solid", fgColor=SECT); ws.cell(r, c).border = box
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)

# Tick boxes: classic form checkboxes (VML), which OpenOffice, LibreOffice and every Excel open. Each is linked to a
# hidden cell past the last column (TRUE when ticked); a conditional format strikes the line through.
TICKS = {}
def tick(ws, r, ncol):
    col = get_column_letter(ncol + 1)
    ws.cell(r, ncol + 1, False); ws.column_dimensions[col].hidden = True
    TICKS.setdefault(ws.title, []).append((r, f"'{ws.title}'!${col}${r}"))
def strike_when_ticked(ws, r0, r1, ncol):
    ws.conditional_formatting.add(f"A{r0}:{get_column_letter(ncol)}{r1}", FormulaRule(
        formula=[f"${get_column_letter(ncol + 1)}{r0}=TRUE"], stopIfTrue=False, font=Font(strike=True, color="808080")))
def add_checkboxes(path, sheetnames):
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
                       f'<x:Anchor>0, 12, {r - 1}, 2, 0, 36, {r - 1}, 19</x:Anchor><x:SizeWithCells/>'
                       '<x:AutoFill>False</x:AutoFill><x:AutoLine>False</x:AutoLine><x:TextVAlign>Top</x:TextVAlign>'
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
                continue                                       # written below
            zout.writestr(item, data)
        for sheet, (k, ticks) in sheets.items():
            zout.writestr(f"xl/drawings/vmlDrawing{k}.vml", vml(k, ticks))
            rels = sheet.replace("worksheets/", "worksheets/_rels/") + ".rels"
            t = (zin.read(rels).decode("utf-8") if rels in names else
                 '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.'
                 'openxmlformats.org/package/2006/relationships"></Relationships>')
            zout.writestr(rels, t.replace("</Relationships>", f'<Relationship Id="rIdTick" Type="{REL}/vmlDrawing" '
                                          f'Target="../drawings/vmlDrawing{k}.vml"/></Relationships>'))
        for rels in names:
            if rels.startswith("xl/worksheets/_rels/") and rels.replace("_rels/", "")[:-5] not in sheets:
                zout.writestr(rels, zin.read(rels))
    shutil.move(tmp, path)

wb = Workbook(); wb.calculation = CalcProperties(fullCalcOnLoad=True)
ws = wb.active; ws.title = "BOM"
COLS = ["Done", "Where", "Qty used", "Part", "Manufacturer", "Mfr part number", "Supplier", "Supplier part number",
        "Buy", "Unit price", "Tariff", "Total", "Notes"]
NC = len(COLS)
title(ws, "Heli Collective - bill of materials",
      f"Everything to buy for one collective. Prices checked {CHECKED}, USD, before shipping; Amazon and OSH Park prices "
      "are per pack or order. Buy is the cheapest quantity (10 can cost less than 8). Tariff is Mouser's estimate for "
      "US delivery; Total includes it. Screws marked Screw kit or Set screw kit come from those kits. Tick Done to "
      "strike a line through.", NC)
HR = 4; header(ws, COLS, [6, 18, 7, 44, 15, 22, 13, 22, 6, 9, 7, 10, 40], HR)
r, first_item = HR, HR + 1
for sec, items in SECTIONS:
    r += 1; section(ws, r, sec, NC)
    for p in items:
        r += 1
        n, unit = buy(p)
        vals = ["", p["where"], p["qty"], p["desc"], p["mfr"], p["mpn"], p["sup"], p["spn"], n, unit,
                p["tariff"] if p["sup"] == "Mouser" else None,
                f"=I{r}*J{r}*(1+K{r})" if n else None, p["notes"]]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
        for c in (1, 3, 9, 11): ws.cell(r, c).alignment = centre
        ws.cell(r, 10).number_format = USD3; ws.cell(r, 12).number_format = USD; ws.cell(r, 11).number_format = PCT
        url = LINKS.get(p["sup"])
        if url and (p["spn"] or p["sup"] == "OSH Park"):
            cell = ws.cell(r, 8 if p["spn"] else 7); cell.hyperlink = url + p["spn"]
            cell.font = F(color="0563C1", underline="single")
        tick(ws, r, NC)
last = r
strike_when_ticked(ws, first_item, last, NC)
r += 2
ws.cell(r, 11, "Total").font = F(bold=True)
ws.cell(r, 12, f"=SUM(L{first_item}:L{last})").font = F(bold=True); ws.cell(r, 12).number_format = USD
ws.cell(r, 1, "The 6808 bearings and the M5 bolt are unpriced: buy them anywhere.").font = F(italic=True, color="595959")
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
ws.freeze_panes = f"C{HR + 1}"; ws.print_title_rows = f"{HR}:{HR}"

ws2 = wb.create_sheet("Printed parts")
title(ws2, "Heli Collective - printed parts", "Print the fit-test coupons first. Paths are from the repository root. "
      "Tick Done to strike a line through.", 5)
header(ws2, ["Done", "Assembly", "File", "Qty", "How to print"], [6, 10, 62, 6, 60], 4)
for i, (asm, f, q, note) in enumerate(PRINTED, 1):
    for c, v in enumerate(["", asm, f, q, note], 1):
        cell = ws2.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
    ws2.cell(4 + i, 4).alignment = centre
    tick(ws2, 4 + i, 5)
strike_when_ticked(ws2, 5, 4 + len(PRINTED), 5)
ws2.freeze_panes = "A5"

wb.save(OUT)
add_checkboxes(OUT, wb.sheetnames)
print(f"{len(fps)} board parts checked; {sum(len(i) for _, i in SECTIONS)} BOM lines; wrote {OUT}")
