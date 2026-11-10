# Build HeliSR_Rev3.0_BOM.xlsx: the Digi-Key order, parts bought elsewhere, and the MkII collective hardware.
# Rev 3.0 adds two PROG buttons with their 1 k resistors and a fourth mounting hole to the Rev 2.0 list.
# usage: make_bom_v3.py <out.xlsx>
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

DK = "https://www.digikey.com/en/products/result?keywords="
PRICE_DATE = "2026-10-19"         # Rev 2.0 cart; the R1/R2 price is the catalogue price on 2026-10-20

# Digi-Key order, matching the cart. (refs, qty, description, manufacturer, mfr part, digikey part, unit USD, notes)
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

# Needed for the build but not in the Digi-Key order. (refs, qty, description, source, notes)
ELSEWHERE = [
    ("AX1 (MkIII base)", 1, "AS5600 magnetic encoder module, 23 x 23 mm, with 5 x 2 mm diametric magnet",
     "WWZMDiB, Amazon B0CM3C8KFT", "Collective axis. Remove its 0 ohm R1 for 5 V; keep R4 (PGO to GND). Wire DIR to VCC"),
    ("AX4 (option)", 1, "AS5600 magnetic encoder module, as AX1", "WWZMDiB, Amazon B0CM3C8KFT",
     "Second AS5600 (throttle), programmed with PROG4. As AX1, except DIR: see Head/README.md"),
    ("AX3", 1, "Knob for a 6 mm knurled shaft", "e.g. Cliff FC7257 (Digi-Key 4654-FC7257-ND)",
     "Check the spline matches the pot's knurl"),
    ("USB", 1, "USB cable, A to micro-B", "e.g. Assmann AK67421-2 (Digi-Key AE10342-ND)", "If you don't have one"),
    ("H1-H4", 4, "Machine screw, M3 x 12, countersunk (ISO 10642 / DIN 7991)", "Any hardware supplier",
     "From outside the Huey head's rear wall, through the spacer and the board"),
    ("H1-H4", 4, "Hex nut, M3 (ISO 4032 / DIN 934, 5.5 mm across flats)", "Any hardware supplier", "On the board's front"),
]

# Collective mechanical parts from the original project (MkII base). The MkIII base has its own list in
# Base/README.md. (part, qty, description, notes)
MECHANICAL = [
    ("Base", 1, "Aluminium tube, 25 mm OD x 1 mm wall, 300 mm long", ""),
    ("Base", 2, "Magnet, 5 x 5 x 5 mm cube, neodymium", "For the Hall sensor"),
    ("Base", 2, "Bolt, M4 x 15-20 mm", "Brake shoe fixing"),
    ("Base", 1, "Bolt, M6 x 20 mm, 10 mm hex head", "Friction adjuster"),
    ("Base", 2, "Bolt, M3 x 10 mm", "Side cover"),
    ("Base", 2, "Bolt, M3 x 15 mm", "Spring fixing"),
    ("Base", 1, "Tension spring, about 8.5 mm OD, 0.9 mm wire, 17 mm closed", "Adjust to taste"),
    ("Base", 2, "Velcro, loop side only, 20 mm wide x 60 mm", ""),
    ("Head", 2, "Bolt, M3 x 20 mm", "Head to shaft fixing"),
    ("Head", 6, "Countersunk screw, #4 (4g) x 10-12 mm", ""),
    ("Consumable", 1, "Bearing grease (not silicone paste), CA glue, hot glue", ""),
]

thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")
centre = Alignment(horizontal="center", vertical="top")
head_fill = PatternFill("solid", fgColor="1F3864")
sect_fill = PatternFill("solid", fgColor="D9E1F2")
link = Font(color="0563C1", underline="single")
USD = '"$"#,##0.00'


def sheet(ws, title, note, head, width):
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = note
    ws["A2"].font = Font(italic=True, color="595959")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(head))
    for c, (h, w) in enumerate(zip(head, width), 1):
        cell = ws.cell(4, c, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = box
        ws.column_dimensions[cell.column_letter].width = w
    ws.freeze_panes = "A5"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "4:4"
    return 4


def section(ws, r, name, ncol):
    ws.cell(r, 1, name).font = Font(bold=True)
    for c in range(1, ncol + 1):
        ws.cell(r, c).fill = sect_fill
        ws.cell(r, c).border = box
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)


def row(ws, r, vals):
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.alignment = wrap
        cell.border = box


wb = Workbook()

# Sheet 1: Digi-Key order
ws = wb.active
ws.title = "Digi-Key order"
HEAD = ["#", "Reference", "Qty", "Description", "Manufacturer", "Mfr part number", "Digi-Key part number",
        "Unit price", "Ext. price", "Notes"]
r = sheet(ws, "HeliSR Rev 3.0 - Digi-Key order",
          f"Matches the Digi-Key cart. Prices are from the cart on {PRICE_DATE} (the JST headers: 2026-10-22), before "
          "shipping and tariff; the cable and some head-switch lines are still to be priced from the cart. "
          "Digi-Key part numbers link to Digi-Key.", HEAD, [5, 15, 6, 46, 18, 24, 28, 10, 10, 56])
n, first_item = 0, None
for name, items in ORDER:
    r += 1
    section(ws, r, name, len(HEAD))
    for refs, qty, desc, mfr, mpn, dk, unit, notes in items:
        r += 1
        n += 1
        first_item = first_item or r
        row(ws, r, [n, refs, qty, desc, mfr, mpn, dk, unit, f"=C{r}*H{r}", notes])
        ws.cell(r, 1).alignment = ws.cell(r, 3).alignment = centre
        ws.cell(r, 7).hyperlink = DK + dk
        ws.cell(r, 7).font = link
        for c in (8, 9):
            ws.cell(r, c).number_format = USD
r += 2
ws.cell(r, 8, "Subtotal").font = Font(bold=True)
ws.cell(r, 9, f"=SUM(I{first_item}:I{r - 2})").font = Font(bold=True)
ws.cell(r, 9).number_format = USD

r += 2
section(ws, r, "Not in the Digi-Key order", len(HEAD))
for refs, qty, desc, source, notes in ELSEWHERE:
    r += 1
    n += 1
    row(ws, r, [n, refs, qty, desc, source, "", "", "", "", notes])
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=9)
    ws.cell(r, 1).alignment = ws.cell(r, 3).alignment = centre

# Sheet 2: collective hardware
ws = wb.create_sheet("MkII collective hardware")
r = sheet(ws, "HeliSR - MkII collective hardware", "From the original project's parts list, for the MkII base. Hardware "
          "store items. The MkIII base's parts are listed in Base/README.md.",
          ["#", "Part", "Qty", "Description", "Notes"], [5, 14, 6, 60, 30])
for i, (part, qty, desc, notes) in enumerate(MECHANICAL, 1):
    r += 1
    row(ws, r, [i, part, qty, desc, notes])
    ws.cell(r, 1).alignment = ws.cell(r, 3).alignment = centre

wb.save(sys.argv[1])
print("order lines", sum(len(i) for _, i in ORDER))
