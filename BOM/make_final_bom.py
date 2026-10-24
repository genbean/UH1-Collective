# Build Heli_Collective_Final_BOM.xlsx and Heli_Collective_DigiKey.csv: one BOM for the whole collective as it is
# built now: the HeliSR Rev 3.0 board (bare PCB ordered from OSH Park, frozen), the Huey head Rev 4 (Head/Rev4/) and
# the MkIII base Rev 3 (Base/, a concept, not yet printed).
# The board's parts, the cables and the head switches are read from the frozen Rev 3.0 BOM scripts (single source of
# truth), and the board's parts are checked against the ordered board file again. Head and base lines cite the
# README or CAD they come from. Lines sized only from the CAD are highlighted for checking; lines covered by the
# two screw kits (every screw and nut in the head and base) are marked and cost nothing extra.
# Sheets: Final BOM (everything bought), Digi-Key order (the electronics order, linked to the Final BOM), Printed
# parts, Dropped (in earlier lists or carts, not used now), Sources. The CSV is the Digi-Key order for one
# collective, for Digi-Key's cart / BOM upload.
# usage: python make_final_bom.py [out.xlsx]     (any Python 3 with openpyxl)
import ast, csv, math, os, re, sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.properties import CalcProperties

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "Heli_Collective_Final_BOM.xlsx")
CSV_OUT = os.path.join(os.path.dirname(OUT), "Heli_Collective_DigiKey.csv")
R3 = os.path.join(ROOT, "PCB", "HeliSR_Rev3.0")
BOARD_PY, FULL_PY = os.path.join(R3, "tools", "make_board_bom_v3.py"), os.path.join(R3, "tools", "make_bom_v3.py")
BOARD_PCB = os.path.join(R3, "HeliSR_Rev3.0.kicad_pcb")

# ---- pull the HeliSR data out of the frozen scripts without running them ----------------------------------------
def module_parts(path, names=(), funcs=()):
    tree = ast.parse(open(path, encoding="utf-8").read())
    data, ns = {}, {"re": re}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            data[node.targets[0].id] = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name in funcs:
            exec(compile(ast.Module([node], []), path, "exec"), ns)
    return data, ns
bd, bfn = module_parts(BOARD_PY, ("SOLDERED",), ("footprints", "expand"))
fd, _ = module_parts(FULL_PY, ("ORDER",))
fps = bfn["footprints"](BOARD_PCB)
listed = [r for line in bd["SOLDERED"] for r in bfn["expand"](line[0])]
assert sorted(listed) == sorted(fps), sorted(set(fps) ^ set(listed))
by_mpn = {it[4]: it for _, items in fd["ORDER"] for it in items}          # refs, qty, desc, mfr, mpn, dk, unit, notes

BRD = "PCB/HeliSR_Rev3.0 board BOM (checked against the ordered board)"
FULL = "PCB/HeliSR_Rev3.0/HeliSR_Rev3.0_BOM.xlsx (Digi-Key cart)"
HEAD = "Head/Rev4/README.md and Head/Rev3/README.md, Bought"
BASE = "Base/README.md, Bought parts"
BASE1 = "Base/mk3_pivot.py (the Rev 1 parts Rev 3 keeps)"
CAD = "Base/mk3_pivot.py geometry (no size in any list)"
AMZ = "Amazon listing on 2026-10-22 (link you sent)"
KIT = "AvrestYPT screw kit (Amazon B0FMD5TMSH)"
SETKIT = "HIQTRADEBYJJ set screw kit (Amazon B0DG33R714)"
SCREWS = "Head/Rev4 and Base/mk3_rev3.py screw lists; renders/*Screws*.png"
CHECK, INKIT, ORDERED = "check", "kit", "ordered"
FILL = {CHECK: "FCE4D6", INKIT: "E2EFDA", ORDERED: "DDEBF7"}

# line: (where, qty, description, manufacturer, mfr part, supplier, supplier part, pack price USD, pack, status,
#        packs already bought, notes, source)
CHECKED = {"639H/2": 8.47, "637H/2": 8.02, "636H/2": 7.55, "A10SR10SR30K254A": 3.17, "A03SR03SR30K203A": 1.35}   # Digi-Key, 2026-10-22
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
board = [(refs, len(bfn["expand"](refs)), desc, mfr, mpn, "Digi-Key", dkpn, unit, 1, "", 0, notes, BRD)
         for refs, value, fpname, desc, mfr, mpn, dkpn, unit, notes in bd["SOLDERED"]]
SECTIONS.append(("HeliSR Rev 3.0: the parts you solder to the bare board (Digi-Key)", board))
SECTIONS.append(("HeliSR Rev 3.0: bare PCB and controller", [
    ("PCB", 1, "HeliSR Rev 3.0 bare PCB (no parts fitted), 2 layers, 1.6 mm FR4, 39.3 x 33.64 mm", "OSH Park", "", "OSH Park",
     "", 10.20, 3, ORDERED, 1, "Ordered 2026-10-21: $10.20 for three bare boards, free shipping, due back about "
     "2026-10-29", "OSH Park order confirmation"),
    ("J7, J8", 1, "Pro Micro 5V/16 MHz (ATmega32U4), USB-C, with header pins", "OSOYOO", "", "Amazon", "B0B81FGBLY", 11.99, 1,
     "", 0, "Runs MMJoy2; plugs into the J7/J8 sockets. Comes with three rows of header pins, so no separate headers. "
     "Also sold as 3 for $21.99. Check that its 2 x 12 pins line up with J7/J8 (15.24 mm between rows)", AMZ),
]))
SECTIONS.append(("Wiring", [
    dk("A10SR10SR30K254A", "J1, J2", 1, "Switch loom. The jumper has a connector at each end: cut it in half for the two "
       "board-end pigtails (J1 and J2). Price: check the cart"),
    dk("A03SR03SR30K203A", "J11, J14", 2, "AX1 (collective sensor) and AX4 (throttle sensor); AX2 and AX3 are spare. "
       "Price: check the cart"),
    ("AX1 lead", 1, "3-core cable, 28 AWG, black, 1 m (Digi-Key cut length)", "Tensility", "30-01653", "Digi-Key",
     "839-30-01653-DS-ND", 2.28, 1, CHECK, 0, "Collective sensor lead: from the AS5600 in the base, through the lever's "
     "cable channels and up the 470 mm tube, spliced to an AX1 pigtail. Length is an estimate: measure your run; "
     "Digi-Key sells it by the metre", "Digi-Key cart 2026-10-23; Base/README.md (the 3-core sensor lead)"),
    ("USB", 1, "USB 2.0 cable, USB-A plug to USB-C plug, 2 m (6.56 ft)", "Stewart Connector", "SC-2CAK020M", "Digi-Key",
     "380-SC-2CAK020M-ND", 7.33, 1, "", 0, "Cut it about 15 cm from the USB-C plug. Feed the long piece (USB-A end stays "
     "at the PC) through the device: laid in the lever's open channels, up the tube and in through the head. The cable "
     "cover's spout is a plain 7.5 mm bore. Splice the USB-C stub back on inside the head (red, black, green, white) "
     "and leave the shield wire unconnected. The cut costs about 15 cm of the 2 m: check the run still reaches. The "
     "head's clearances were checked with a micro-USB plug: check the C plug fits the same way",
     "Digi-Key cart 2026-10-23; Head/Rev4/README.md; Base/README.md"),
]))
SECTIONS.append(("Angle sensors", [
    ("AX1, AX4", 2, "AS5600 magnetic encoder module, 23 x 23 mm, with 5 x 2 mm diametric magnet", "WWZMDiB", "", "Amazon",
     "B0CM3C8KFT", 9.99, 4, "", 0, "Sold in fours. AX1: the collective, in the base, programmed with PROG1, DIR to VCC. "
     "AX4: the throttle, in the head, programmed with PROG4, DIR to GND. On each: remove the 0 ohm R1, keep R4", AMZ),
]))
SECTIONS.append(("Huey head: switches", [
    dk("639H/2", "IN3-IN6", notes="LDG LT EXT / RETR and SL ON / STOW. Common to GND. Price: check the cart"),
    dk("637H/2", "IN1, IN2", notes="GOV RPM INCR / DECR. Price: check the cart"),
    dk("636H/2", "IN7", notes="LDG LT ON (one side wired). Price: check the cart"),
    dk("PB4-M-BK-D-67", "IN13", notes="STOP REL"),
    dk("1825910-6", "IN9-IN12, IN14", notes="SEARCH CONT hat (4) and starter trigger (1). IN8, IN15, IN16 are spare"),
]))
SECTIONS.append(("Huey head: hardware", [
    setkit("Tube boss", 1, "M5 x 8 set screw", "From the boss's front (lower panel off): tap the 4.2 mm pilot M5; the tip "
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
         "into the right lug's 2.5 mm pilot (tap it M3 all the way through); the tip stays about 0.9 mm inside the lug",
        HEAD + "; user's choice 2026-10-23", ORDERED),
    setkit("Trigger pull stop", 1, "M3 x 4 set screw", "Through the trigger's arm (tap M3); its tip bears on the mount. Set it "
           "so the starter switch clicks before the stop"),
    kit("Panels", 8, "M3 x 12 countersunk screw (DIN 7991)", "4 per panel, into M3 threads tapped in the box's corner "
        "columns (the pilots run 50 mm deep, so the x 12 has room)"),
    kit("HeliSR board", 4, "M3 x 12 countersunk screw (DIN 7991) + M3 hex nut", "From outside the rear wall through a "
        "spacer and the board"),
    dk("SRS-4-4MM", "HeliSR board", 4, "Between the rear wall and the board", source=HEAD),
    amz("Trigger", 1, "Pen spring, 4 mm OD x 50 mm, 0.4 mm wire, pack of 10", "uxcell", "B0GCZGNBYH", 6.99, 10,
        "Trigger return: cut to about 13 mm", HEAD),
    amz("Head box", 1, "Ballast: lead split shot fishing weights, assorted, 120 pcs", "SANWEAL", "B0H6J3X6GL", 5.99, 1,
        "Only if the gas strut lifts too much: about 48 g for a 45 N strut. Close to the middle of the box. Weigh out what you "
        "need", BASE),
]))
SECTIONS.append(("MkIII base Rev 3 (concept, not yet printed)", [
    ("Pivot", 2, "Deep-groove ball bearing 6006-2RS, 30 x 55 x 13 mm", "BlueStars", "6006-2RS", "Amazon", "B09XTV8XYK",
     8.99, 2, "", 0, "Sold in pairs", AMZ + "; " + BASE1),
    ("Tube", 1, "Carbon fibre tube, 25 mm OD x 23 mm ID, 500 mm, 3K plain weave, wrapped", "MECCANIXITY", "", "Amazon",
     "B0CFFT1B31", 27.49, 2, "", 0, "Sold in pairs. Wrapped, as the base needs (not pultruded). Cut to 483 mm (470 + the head's extra 12.7 mm of bore). Drill the "
     "M4 lock-screw hole 30.5 mm from the bottom end and the head's 5.2 mm cross hole 10 mm below the top end. Check "
     "the socket and head fits with it (coupons)", AMZ + "; " + BASE),
    amz("Socket mouth", 1, "Worm-drive hose clamp, 25-40 mm range, 304 stainless, pack of 25", "MISPIRE", "B0F8QWCFWR", 18.99, 25,
        "Pack of 25 is the smallest 25-40 mm pack found; you need one", BASE1),
    kit("Lever halves", 4, "M4 x 20 countersunk screw + M4 hex nut", "From the top, the heads 16 mm down their counterbores "
        "(a long 2.5 mm hex key helps); the nuts go in the lower half's pockets first"),
    ("Strut", 1, "Gas strut, 6 in (152.4 mm eye to eye), 45 N (sold as 9-12 lb), flat eyelet tabs", "X AUTOHAUX", "",
     "Amazon", "B0CY267GFY", 13.69, 2, "", 0, "Sold in pairs: the spare is the other half", BASE),
    kit("Strut eyes", 2, "M4 x 16 countersunk screw + M4 hex nut", "One per eye: head on +y, nut in the -y cheek's pocket. "
        "The listing gives the strut's eye holes as 4 mm. Snug, then thread-lock: the eye must still turn"),
    kit("Strut collar", 1, "M4 x 12 countersunk screw + M4 hex nut", "Collar clamp: the head sits 2 mm into the -y ear, "
        "the nut in the +y ear's pocket"),
    kit("Down-stops", 2, "M4 x 16 countersunk screw + 2 M4 hex nuts", "Head up: its flat top is the stop. One nut pressed "
        "into the post's top pocket, the second on top of it locks the height that levels the tube"),
    kit("Pillow-block caps", 4, "M4 x 20 countersunk screw + M4 hex nut", "Two per cap, from the top; each nut slides "
        "into a slot in the block's front or back face. Length from the CAD"),
    kit("Side covers", 8, "M3 x 20 countersunk screw", "Four per cover, from its outer face into M3 threads tapped 7 mm "
        "deep in the block and cap. Length from the CAD"),
    kit("Cable plug", 1, "M2 x 12 countersunk screw", "Up from under the cable cover's rim, through a clearance hole, into an "
        "M2 thread tapped in the plug (1.6 mm pilot): pulls the plug that closes the cable's slot down onto the cover's "
        "shoulders. Length from the CAD"),
    setkit("Tube lock", 1, "M4 x 6 set screw", "Tap the socket boss's 3.3 mm pilot M4; the tip goes into the tube's 4 mm "
           "lock hole, 30.5 mm from its bottom end"),
    kit("Friction knob", 1, "M5 x 20 countersunk screw + M5 hex nut", "Glue the head into the printed knob "
        "(Base/stl/friction_knob.stl); the screw goes through the spring and the shoe into the nut, slid into the knob "
        "tower's slot from the front. Length from the CAD"),
    amz("Friction knob", 1, "Compression spring, 10 mm OD, 1.0 mm wire, 15 mm free length, pack of 10", "Amazon", "B09FF6VQ55",
        11.10, 10, "Over the M5 screw, in a 2 mm recess in the shoe; 6.5 mm long when fitted in the CAD. The CAD asked for 1.1 "
        "mm wire and 10-12 mm free length; this is the nearest stock size, so trim a coil if it is too long", CAD, CHECK),
    amz("Friction shoe", 1, "Self-adhesive felt tape, 1.5 mm thick, 3/4 in x 50 ft, black", "FindTape", "B077TCDNYT", 24.98, 1,
        "Lines the shoe against the drum: cut a 95 mm length (19 mm wide, the CAD wants 17 mm). It is the only 1.5 mm felt found "
        "in a usable width, and you need a few cm of the 50 ft", CAD, CHECK),
    kit("Shoe hinge", 1, "M4 x 20 countersunk screw + M4 hex nut", "Hinge pin through both frame lugs and the shoe's eye: "
        "head in the -y lug, nut in the +y lug's pocket (the lugs are 20 mm apart outside). Snug, then thread-lock: the shoe "
        "must still swing"),
    amz("Desk mounting", 4, "Screw, #10 x 1-1/2 in pan head, 304 stainless, pack of 50", "Amazon", "B0F43RY9S6", 8.29, 50,
        "Through the 5.5 mm holes in the frame plate's corners (6 mm plate). Not in the kits: they go into the desk. 1-1/2 in "
        "suits a typical desktop: check yours", CAD, CHECK),
]))
SECTIONS.append(("Kits, consumables and tools", [
    ("Hardware", 1, "Screw kit, 1715 pieces: countersunk hex-socket screws M2-M4 x 8, 12, 16, 20 and M5 x 10, 12, 16, 20, "
     "with hex nuts and washers, hex keys", "AvrestYPT", "", "Amazon", "B0FMD5TMSH", 17.99, "once", ORDERED, 1,
     "Every countersunk screw and nut in the head and base (the green lines). Used: M3 x 12 (12), M3 x 20 (8), M4 x 12 (2),"
     " M4 x 16 (4), M4 x 20 (9), M5 x 20 (1); nuts M3 (4), M4 (17), M5 (1). Your order (link 2026-10-23)",
     "Amazon listing 2026-10-23 (your order)"),
    ("Hardware", 1, "Set screw kit, 500 pieces, 304 stainless: M3 x 3, 4, 5, 6; M4 x 4, 5, 6; M5 x 5, 8; M6 x 6, 10; "
     "M8 x 8; hex keys", "HIQTRADEBYJJ", "", "Amazon", "B0DG33R714", 8.96, "once", ORDERED, 1,
     "The set screws: M5 x 8 (tube, head), M3 x 4 (trigger pull stop), M4 x 6 (tube lock, base). Your "
     "order (link 2026-10-23)",
     "Amazon listing 2026-10-23 (your order)"),
    amz("Assembly", 1, "Cyanoacrylate (CA) super glue gel, 0.14 fl oz", "Loctite", "B0006HUJCQ", 3.82, "once",
        "Magnets into their caps", "Head/Rev4/README.md; Base/README.md"),
    amz("Assembly", 1, "Mini hot glue sticks, 0.27 in, 100 pack", "Surebonder", "B003JZII34", 5.97, "once",
        "AS5600 modules. Mini size: they fit a mini glue gun only. Skip this if you already have glue sticks for your gun",
        "Head/Rev4/README.md; Base/README.md"),
    amz("Assembly", 1, "White lithium grease, 1.5 oz tube", "Permatex", "B000HBNV58", 3.99, "once",
        "Bearing grease (not silicone paste)", "Head/Rev4/README.md; Base/README.md"),
    amz("Assembly", 1, "Silicone faucet grease, waterproof, 0.5 oz", "Danco", "B000DZFUPC", 5.68, "once",
        "For the head's four throttle O-rings (grease them lightly before fitting)", "Head/Rev4/README.md"),
    amz("Assembly", 1, "Threadlocker, blue 242, 6 ml", "Loctite", "B000I1RSNS", 7.03, "once", "Removable, medium strength",
        "Head/Rev4/README.md; Base/README.md"),
    ("Assembly", 1, "Solder paste, low-temperature (Sn42/Bi58, 138 C), syringe", "Chip Quik", "NC191LT10", "Digi-Key",
     "315-NC191LT10-ND", 7.95, "once", "", 0, "For the SMD parts on the board (U1, U2, the 1206 caps, the JST headers, "
     "SW1-SW3). Needs a hot plate or hot air tool and flux. Optional: hand-soldering works too", "Digi-Key cart 2026-10-23"),
    ("Assembly", 1, "Tweezers, 1 mm tip (Olimex CHN-TWZ1MM), for placing the SMD parts", "Olimex", "CHN-TWZ1MM", "Digi-Key",
     "1188-CHN-TWZ1MM-ND", 0.82, "once", "", 0, "Description from Olimex's sibling CHN-TWZ2MM listing: check the tip", "Digi-Key order 102438510"),
    amz("Assembly", 1, "Taps, M3 / M4 / M5 / M6 / M8, 5-piece set", "Amazon", "B0FN49CGJG", 6.49, "once",
        "M3: head panel columns, trigger lug and arm, base side covers. M4: tube lock. M5: tube set screw",
        "Head/Rev4/README.md; Base/README.md"),
    amz("Assembly", 1, "Drill bit, 5.2 mm HSS, 2 pcs", "Amazon", "B0FN3WV6DW", 6.99, "once",
        "The tube's cross hole is 5.2 mm", "Head/Rev4/README.md"),
]))

# Hardware, kits, consumables and tools the user supplies themselves (2026-10-23): left off the BOM
USER_SUPPLIED = {"B0006HUJCQ", "B003JZII34", "B000I1RSNS", "B0FN49CGJG", "B0FN3WV6DW", "B077TCDNYT", "B0F8QWCFWR",
                 "B09FF6VQ55", "B0F43RY9S6"}
SECTIONS = [(t, [l for l in lines if l[6] not in USER_SUPPLIED]) for t, lines in SECTIONS]

# The Digi-Key order was placed 2026-10-23 (order 102438510): every Digi-Key line is bought
def _ordered(l):
    if l[5] != "Digi-Key": return l
    l = list(l); l[10] = 1 if l[8] == "once" else math.ceil(l[1] / l[8])
    if l[9] == "": l[9] = ORDERED
    return tuple(l)
SECTIONS = [(t, [_ordered(l) for l in lines]) for t, lines in SECTIONS]

# Amazon orders already delivered (checked against the user's order screen, 2026-10-23)
AMAZON_BOUGHT = {"B0CFFT1B31", "B0CM3C8KFT", "B0B81FGBLY", "B09XTV8XYK", "B0FMD5TMSH", "B0CY267GFY", "B0BWWBTL4N", "B000HBNV58", "B000DZFUPC"}
def _delivered(l):
    if l[6] not in AMAZON_BOUGHT or l[7] == 0: return l
    l = list(l); l[10] = 1 if l[8] == "once" else math.ceil(l[1] / l[8])
    if l[9] == "": l[9] = ORDERED
    return tuple(l)
SECTIONS = [(t, [_delivered(l) for l in lines]) for t, lines in SECTIONS]

PRINTED = [
    ("Head", "Head/Rev4/stl/HueyHeadR4-GripBearingCoupons.stl", 1, "Flat, labels up. Optional: checks the head's 25.2 mm "
     "tube bore on the carbon tube (the grip now rides on O-rings)"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-ORingCoupon.stl", 1, "Upright. A slice of the grip's bore with one O-ring groove: "
     "fit a greased 24 x 2 O-ring and slide it on the carbon tube before printing the grip (about 2 g)"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-SensorSeatCoupon.stl", 1, "The same way round as in the head on its rear wall. "
     "Optional: slide the AS5600 module through it first"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-Body.stl", 1, "One piece: box, neck, faux friction knob, boss, sensor pod and "
     "trigger mount. On its rear wall, with tree supports under the neck, knob and tube bore; then ream the bore to a "
     "press fit on the tube"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-LowerPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-UpperPanel-Black.stl + -WhiteText.stl", 1, "Front face down, two colours"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-Trigger.stl", 1, "On either flat side"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-SearchHat.stl", 1, "On its flat bottom ring"),
    ("Head", "MkII original: 4way_Cover.stl, Bezel.stl, StickRetainer.stl, one ThumbStick-*.stl", 1, "The 4-way hat's parts, from the Thingiverse 5226353 head files (not in this folder). The ThumbStick comes in 4.5 to 5.8 mm, set by the switch's height: the TE 1825910-6 is 5.0 mm to the top of its button (datasheet), so print the 4.8 and the 5.3 and keep the one that clicks cleanly with no preload"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-ThrottleGrip.stl", 1, "Upright, bottom end down; no supports"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-FrictionCollar.stl", 1, "Bottom face down, O-ring groove up"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-Pinion.stl", 1, "Flat; the magnet shaft presses into its hex"),
    ("Head", "Head/Rev4/stl/HueyHeadR4-MagnetShaft.stl", 1, "Cap face down, pin up"),
    ("Base", "Base/stl/coupons/coupon_trunnion.stl, coupon_bearing_seat.stl, coupon_tube_socket.stl", 1,
     "Fit-test coupons: print first and tune mk3_pivot.py (the socket with the carbon tube)"),
    ("Base", "Base/stl/frame.stl", 1, "Plate down"),
    ("Base", "Base/stl/lever_lower.stl", 1, "On its joint face"),
    ("Base", "Base/stl/lever_upper.stl", 1, "On its joint face"),
    ("Base", "Base/stl/cap_left.stl, cap_right.stl", 1, "One each"),
    ("Base", "Base/stl/cover_cable.stl, cover_sensor.stl", 1, "One each"),
    ("Base", "Base/stl/cable_plug.stl", 1, "On a long flat face. Fills the cable cover's slot once the USB cable is in"),
    ("Base", "Base/stl/sensor_carrier.stl", 1, ""),
    ("Base", "Base/stl/shoe.stl", 1, ""),
    ("Base", "Base/stl/strut_collar.stl", 1, "Standing on one end"),
    ("Base", "Base/stl/friction_knob.stl", 1, "Top face down; glue the M5 x 20's head into it"),
]
DROPPED = [
    ("Glue, thread-lock, taps, drill bit, felt tape, hose clamp, 10 mm spring, #10 desk screws", 0,
     "You supply these yourself", "User, 2026-10-23"),
    ("Fgruh M3 and M4 socket-cap screw kits, M3 x 10 / M4 x 30 / M5 x 40 countersunk packs, M6 x 25 and M6 x 30 bolts, M6 and "
     "M4 nyloc nuts, uxcell M5 x 5 set screws, heat-set inserts and insert tips", 0, "Every screw and nut now comes from the "
     "AvrestYPT and set screw kits (2026-10-23): the CAD was changed to suit them", "User, 2026-10-23"),
    ("MkII-AdjustKnob.stl (friction knob)", 1, "Took an M6 hex head; the base now prints its own knob for the M5 x 20",
     "Base/mk3_pivot.py"),
    ("SparkFun Pro Micro 12640 (Digi-Key 1568-12640-ND)", 1, "Replaced by the OSOYOO USB-C Pro Micro from Amazon", FULL),
    ("Sullins PRPC012SAAN-RC male headers (Digi-Key 35-PRPC012SAAN-RC-ND)", 2, "The OSOYOO Pro Micro comes with header pins", FULL),
    ("Assmann AK67421-2 USB A to micro-B cable", 1, "The OSOYOO Pro Micro is USB-C", FULL),
    ("E-Switch PS1024ABLK push button (EG2011-ND)", 2, "The head removed the two lower-panel push buttons", FULL),
    ("TT P0915N-QC20BR5K 5 k pot (987-1278-ND)", 2, "No head-knob pot any more; the throttle is read by an AS5600", FULL),
    ("Knob for a 6 mm knurled shaft (Cliff FC7257)", 1, "Went with the head-knob pot", FULL),
    ("TI DRV5055A4 / A2 Hall sensors, KEMET axial 100 nF", 3, "MkII base only; the MkIII base uses an AS5600", FULL),
    ("APEM MJTP1230A / G / F tactile switches (Digi-Key 679-2429-ND, 679-2435-ND, 679-2434-ND)", 3, "The TE 1825910-6 covers "
     "all five tactile inputs", "Digi-Key cart, 2026-10-22"),
    ("Keystone 941 micro-B plug (Digi-Key 36-941-ND)", 1, "The Pro Micro is USB-C", "Digi-Key cart, 2026-10-22"),
    ("Samsung CL10B104KB8WPNC 0.1 uF 0603 cap (Digi-Key 1276-6854-1-ND)", 1, "The board uses 1206 caps", "Digi-Key cart, 2026-10-22"),
    ("Qualtek 3021017-10 USB-A to open-end cable, 10 ft (Digi-Key Q369-ND)", 1, "The Stewart A-to-C cable, cut and spliced, "
     "replaces it", "Digi-Key cart, 2026-10-22"),
    ("USB-C male plug (loose) and hookup wire", 1, "The plug comes on the Stewart cable; you already have hookup wire, "
     "heat-shrink and solder", "Earlier BOM draft"),
    ("TE 2495152-1 USB-C plug", 1, "Board-edge part with no solder cups: needs its own PCB", "User question, 2026-10-23"),
    ("JST SR 3-pin jumpers beyond 2", 2, "The full BOM had 4 (one per AX connector); only AX1 and AX4 are wired now", FULL),
    ("JST BM03B-SRSS-TBT: the cart has 3", 0, "A note, not dropped: the board has 4 footprints (J11-J14); this BOM orders 4",
     "Digi-Key cart, 2026-10-22"),
    ("MkII collective hardware (base, head bolts, springs, magnets)", 0, "The MkII base is replaced by the MkIII Rev 3",
     "HeliSR_Rev3.0_BOM.xlsx, sheet 2"),
    ("25 x 1 mm aluminium tube, 358 mm", 1, "Replaced by the base's 470 mm carbon tube", "Head/README.md (before)"),
    ("Ballast bucket, lid, ~0.95 kg ballast, 4 x M4 bucket bolts + inserts, lid M3 screws + inserts", 0,
     "Base Rev 3 balances with the gas strut", BASE),
    ("Quadrant stop block, thumb knob, M5 x 16 stop bolt + nut, M6 striker + insert", 0, "Base Rev 3 has a fixed 32 deg stop", BASE),
    ("Rev 1 centre down-stop screw, nut and insert", 0, "Base Rev 3 uses two down-stop posts beside the strut", "Base/mk3_rev3.py"),
]
SOURCES = [
    ("HeliSR Rev 3.0 board", "PCB/HeliSR_Rev3.0", "Bare PCB ordered from OSH Park on 2026-10-21; folder frozen and read-only"),
    ("Huey head", "Head/Rev4", "Current head design: Rev 4, one piece (Rev 3 with its neck block and trigger mount built "
     "back into the box). Rev 3 (Head/Rev3) is the same head in three parts, with no supports; Rev 2 (Head/) is superseded"),
    ("MkIII base Rev 3", "Base (Base/mk3_rev3.py imports Base/mk3_pivot.py)", "Concept, nothing printed yet: check the orange lines"),
    ("Prices", "Digi-Key cart 2026-10-19 (JST headers 2026-10-22); Amazon listings 2026-10-22; OSH Park order 2026-10-21",
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
def link(cell, supplier, spn):
    url = {"Digi-Key": "https://www.digikey.com/en/products/result?keywords=", "Amazon": "https://www.amazon.com/dp/",
           "OSH Park": "https://oshpark.com/"}.get(supplier)
    if url and (spn or supplier == "OSH Park"): cell.hyperlink = url + spn; cell.font = F(color="0563C1", underline="single")

wb = Workbook(); wb.calculation = CalcProperties(fullCalcOnLoad=True)
ws = wb.active; ws.title = "Final BOM"
COLS = ["#", "Where", "Qty per collective", "Pack", "Packs needed", "Packs bought", "Packs to order", "Description",
        "Manufacturer", "Mfr part number", "Supplier", "Supplier part number", "Pack price", "To spend", "Notes", "Source"]
NC = len(COLS)
setup(ws, "Heli Collective - final BOM",
      "Everything bought for one collective: the HeliSR Rev 3.0 board (the bare PCB is ordered from OSH Park; every part "
      "on it comes from Digi-Key), the Huey head and the MkIII base Rev 3 (a concept, not yet printed). Blue line: "
      "already ordered. Green: covered by a kit or pack priced on another line. Orange: size taken from the base's CAD, not from a parts list, so check "
      "before ordering. Prices are pack prices: Digi-Key cart (2026-10-23), Amazon listings "
      "(2026-10-22 and 2026-10-23) and the OSH Park order, before shipping and tariff. The "
      "Digi-Key order sheet lists the electronics to order from Digi-Key.", NC, 58)
ws["A3"] = "Collectives to build"; ws["A3"].font = F(bold=True); ws.merge_cells("A3:B3")
ws["C3"] = 1; ws["C3"].font = F(bold=True, color="0000FF"); ws["C3"].fill = PatternFill("solid", fgColor="FFFF00")
ws["C3"].alignment = centre; ws["C3"].border = box
ws["D3"] = ("Edit the yellow cells: collectives to build here, and Packs bought for anything you already have. Packs "
            "round up; lines marked once are one per order, however many you build.")
ws["D3"].font = F(italic=True, color="595959"); ws.merge_cells(start_row=3, start_column=4, end_row=3, end_column=NC)
HR = 5; header(ws, COLS, [4, 15, 9, 6, 8, 8, 8, 36, 13, 16, 9, 21, 9, 10, 46, 28], HR)
r, n, subtotals, rows = HR, 0, [], []
for title, lines in SECTIONS:
    r += 1; section(ws, r, title, NC); first = r + 1
    for where, qty, desc, mfr, mpn, sup, spn, unit, pack, status, bought, notes, source in lines:
        r += 1; n += 1
        need = f"=IF($C$3>0,C{r},0)" if pack == "once" else f"=ROUNDUP(C{r}*$C$3/D{r},0)"   # once: one per order
        vals = [n, where, qty, "once" if pack == "once" else pack, need, bought, f"=MAX(0,E{r}-F{r})", desc, mfr, mpn, sup, spn,
                unit, f'=IF(M{r}="","",G{r}*M{r})', ("CHECK: " if status == CHECK else "") + notes, source]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
            if status in FILL: cell.fill = PatternFill("solid", fgColor=FILL[status])
        for c in (1, 3, 4, 5, 6, 7): ws.cell(r, c).alignment = centre
        ws.cell(r, 6).font = F(color="0000FF")
        if status not in FILL: ws.cell(r, 6).fill = PatternFill("solid", fgColor="FFFFCC")
        for c in (13, 14): ws.cell(r, c).number_format = USD
        link(ws.cell(r, 12), sup, spn)
        rows.append((r, where, qty, desc, mfr, mpn, sup, spn, unit, pack, bought, notes))
    r += 1
    ws.cell(r, 13, "Subtotal").font = F(bold=True)
    ws.cell(r, 14, f"=SUM(N{first}:N{r - 1})").font = F(bold=True); ws.cell(r, 14).number_format = USD
    subtotals.append(r)
last_item = r
r += 2
ws.cell(r, 13, "Still to buy").font = F(bold=True)
ws.cell(r, 14, "=" + "+".join(f"N{s}" for s in subtotals)).font = F(bold=True); ws.cell(r, 14).number_format = USD
r += 1
ws.cell(r, 13, "Whole build").font = F(bold=True)
ws.cell(r, 14, f"=SUMPRODUCT(E{HR + 1}:E{last_item},M{HR + 1}:M{last_item})").font = F(bold=True)
ws.cell(r, 14).number_format = USD
r += 1
ws.cell(r, 13, "Unpriced lines").font = F(bold=True)
ws.cell(r, 14, f'=COUNTIFS(A{HR + 1}:A{last_item},">0",M{HR + 1}:M{last_item},"")').font = F(bold=True)
r += 1
ws.cell(r, 1, "Still to buy counts the packs to order; whole build counts every pack needed, bought or not. Both leave "
        "out the unpriced lines: generic hardware and wire.").font = F(italic=True, color="595959")
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
ws.freeze_panes = f"C{HR + 1}"; ws.print_title_rows = f"{HR}:{HR}"

# Digi-Key order: every Digi-Key line, its quantity linked to the Final BOM
wd = wb.create_sheet("Digi-Key order")
DCOLS = ["#", "Digi-Key part number", "Quantity", "Mfr part number", "Description", "Customer reference", "Unit price",
         "Ext. price", "Notes"]
setup(wd, "Heli Collective - Digi-Key order", "Every line to buy from Digi-Key. Quantities come from the Final BOM's "
      "Packs to order, so they follow the collectives to build and anything marked as bought. "
      "Heli_Collective_DigiKey.csv holds the same order for one collective (part number, quantity, customer reference), "
      "for Digi-Key's cart or BOM upload.", len(DCOLS))
header(wd, DCOLS, [4, 25, 9, 20, 40, 16, 10, 10, 50], 4)
d, dk_rows = 4, []
for (fr, where, qty, desc, mfr, mpn, sup, spn, unit, pack, bought, notes) in rows:
    if sup != "Digi-Key": continue
    d += 1
    vals = [d - 4, spn, f"='Final BOM'!G{fr}", mpn, desc, where, f"='Final BOM'!M{fr}",
            f"=IF('Final BOM'!M{fr}=\"\",\"\",C{d}*G{d})", notes]
    for c, v in enumerate(vals, 1):
        cell = wd.cell(d, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
    for c in (1, 3): wd.cell(d, c).alignment = centre
    for c in (7, 8): wd.cell(d, c).number_format = USD
    link(wd.cell(d, 2), sup, spn)
    dk_rows.append((spn, max(0, (1 if pack == "once" else math.ceil(qty / pack)) - bought), where))
d += 1
wd.cell(d, 7, "Total").font = F(bold=True)
wd.cell(d, 8, f"=SUM(H5:H{d - 1})").font = F(bold=True); wd.cell(d, 8).number_format = USD
wd.cell(d + 1, 1, f"All {d - 5} Digi-Key lines are priced (checked 2026-10-23), before shipping and tariff.").font = F(
    italic=True, color="595959")
wd.merge_cells(start_row=d + 1, start_column=1, end_row=d + 1, end_column=len(DCOLS))
wd.freeze_panes = "A5"

ws2 = wb.create_sheet("Printed parts")
setup(ws2, "Heli Collective - printed parts", "The print set for the Huey head and the MkIII base Rev 3, with the "
      "orientation each README gives. Print the coupons first. Paths are from the repository root.", 5)
header(ws2, ["#", "Assembly", "File", "Qty", "Print"], [4, 10, 70, 6, 70], 4)
for i, (asm, f, q, note) in enumerate(PRINTED, 1):
    for c, v in enumerate([i, asm, f, q, note], 1):
        cell = ws2.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
        if note.startswith("CHECK"): cell.fill = PatternFill("solid", fgColor=FILL[CHECK])
    ws2.cell(4 + i, 1).alignment = ws2.cell(4 + i, 4).alignment = centre
ws2.freeze_panes = "A5"

ws3 = wb.create_sheet("Dropped")
setup(ws3, "Heli Collective - dropped from earlier BOMs", "Lines in the Rev 3.0 board's full BOM, the Digi-Key cart or "
      "earlier head and base revisions that this build doesn't use. Take them out of the cart if they're still in it.", 5)
header(ws3, ["#", "Item", "Qty", "Why", "Was in"], [4, 50, 6, 60, 40], 4)
for i, (item, q, why, src) in enumerate(DROPPED, 1):
    for c, v in enumerate([i, item, q or "", why, src], 1):
        cell = ws3.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box
    ws3.cell(4 + i, 1).alignment = ws3.cell(4 + i, 3).alignment = centre

ws4 = wb.create_sheet("Sources")
setup(ws4, "Heli Collective - sources", "Where each part of this BOM comes from. Regenerate with BOM/make_final_bom.py.", 3)
header(ws4, ["Part", "Folder or document", "Status"], [22, 70, 60], 4)
for i, row in enumerate(SOURCES, 1):
    for c, v in enumerate(row, 1):
        cell = ws4.cell(4 + i, c, v); cell.font = F(); cell.alignment = wrap; cell.border = box

wb.save(OUT)
with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Digi-Key Part Number", "Quantity", "Customer Reference"])
    for spn, q, where in dk_rows: w.writerow([spn, q, where])
print(f"{len(fps)} board parts checked; {n} BOM lines ({len(dk_rows)} Digi-Key), {len(PRINTED)} printed-part lines, "
      f"{len(DROPPED)} dropped; wrote {OUT} and {CSV_OUT}")
