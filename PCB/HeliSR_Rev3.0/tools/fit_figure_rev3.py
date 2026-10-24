# To-scale fit of HeliSR Rev 3.0 in the Huey head: board upright on the rear wall, USB end down, reaching up through
# the slot in the upper box's floor, on four corner screws (HELISR_* in huey_head.py). Box frame from huey_head.py
# (checked against the STLs). usage: fit_figure_rev3.py <out.png>
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, RegularPolygon

out = sys.argv[1]
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
WALLC, SWC, BOARDC, PMC, PLUGC, OK = "#c7cbd1", "#e8a33d", "#3b82c4", "#1e5a8f", "#7c8796", "#2f855a"
REAR, PLUGB, CEIL, XL, XR, ZF = 34.6, 1.8, 67.5, -45.71, 56.29, -2.5
UXL, UXR, UZT, UY = -25.71, 36.29, 117.5, 10.0                     # upper box inside, front of the upper box
SLOT = (-19.5, 30.0, 13.0, REAR)                                   # x0, x1, y0, y1
TOG = {"GOV RPM": (-35.21, 42.5), "LDG LT EXT/RETR": (39.79, 42.0)}
UTOG = {"SL": (-10.21, 93.0), "LDG LT ON": (20.79, 93.0)}
TW, TH, TBODY, TLUG = 14.65, 29.7, 17.5, 26.0
HAT = (3.79, 39.0, 12.0); PB4 = (41.79, 10.0, 10.0); POT = (-28.51, 9.5, 5.0); BTN = [(-7.21, -0.5), (6.79, -0.5)]; BTN_R = 4.75
COLS = [(-43.71, 65.5), (54.29, 65.5), (54.29, -0.5), (-43.71, 24.5)]
UCOLS = [(-23.71, 115.5), (34.29, 115.5), (34.29, 74.5), (-23.71, 74.5)]
FLOOR_OPEN = (-22.0, 15.4)
BL, BW, PMX0, PML, PMC_Y, PMW = 39.3, 33.64, 0.60, 33.02, 16.82, 17.78
BTN_XB, BTN_YB = 37.3, (10.0, 16.82, 23.64)                       # PROG4, RST, PROG1 centres (gen_v3.py)
HOLE_IN, SPACER, NUT_R = 3.2, 4.0, 3.175           # M3 holes; Bivar SRS-4-4MM spacers; M3 nut across corners
TOP = 77.0                                                         # board's top edge, clear of the upper toggles
X0, ZB = -5.0, TOP - BL                                            # HELISR_CORNER: USB plug beside the pot
hx = lambda yb: X0 + yb; hz = lambda xb: ZB + xb                   # J1 side left, USB end down
PLUG_W, PLUG_L, PLUG_L_LONG = 10.5, 20.0, 25.0
PCB_F, PM_B = SPACER + 1.6, SPACER + 1.6 + 8.5 + 2.5   # board's front face, Pro Micro's back face (off the rear wall)
STACK, STACK_PM = PM_B + 1.6 + 2.8, PM_B + 1.6 + 1.2   # USB receptacle, Pro Micro's parts
# throttle pot on the pot holder: POT_ENV in huey_head.py (head frame), a vertical cylinder on the tube axis,
# r 6.5 around y 18.52; head frame -> box frame undoes the 20 degree tilt about (y 0, z -5)
import math
C20, S20 = math.cos(math.radians(20)), math.sin(math.radians(20))
h2b = lambda yh, zh: (yh * C20 + (zh + 5) * S20, -yh * S20 + (zh + 5) * C20 - 5)
POT_X = (-8.48, 4.52)
POT_SIDE = [h2b(yh, zh) for yh, zh in ((12.02, 6.95), (25.02, 6.95), (25.02, 17.0), (12.02, 17.0))]
POT_Z = (min(z for _, z in POT_SIDE), max(z for _, z in POT_SIDE))
POTC = "#8b6fb3"

fig, (a, b) = plt.subplots(1, 2, figsize=(15.5, 9.6), gridspec_kw={"width_ratios": [2.0, 1]})
for ax in (a, b):
    ax.set_aspect("equal"); ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values(): s.set_color(GRID)
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)

a.set_title("Front view through the open front (to scale, mm)", color=INK, fontsize=11, loc="left")
a.add_patch(Polygon([(XL, CEIL), (XR, CEIL), (XR, ZF), (-41.58, ZF), (-41.58, 14.83), (XL, 18.96)], closed=True, fill=False, ec=MUTED, lw=1.2))
a.add_patch(Rectangle((UXL, CEIL + 2.5), UXR - UXL, UZT - CEIL - 2.5, fill=False, ec=MUTED, lw=1.2))
a.add_patch(Rectangle((XL, CEIL), XR - XL, 2.5, fc=WALLC, ec=MUTED, lw=0.6))
a.add_patch(Rectangle((SLOT[0], CEIL), SLOT[1] - SLOT[0], 2.5, fc="white", ec=OK, lw=1.0, hatch="////"))
a.annotate("slot in the upper box's floor,\n21.6 mm deep from the rear wall", (27.5, CEIL + 1.25), (37.5, 61.5), fontsize=7, color=OK,
           ha="center", va="center", arrowprops=dict(arrowstyle="-", color=OK, lw=0.8))
a.add_patch(Rectangle((FLOOR_OPEN[0], ZF - 3), FLOOR_OPEN[1] - FLOOR_OPEN[0], 3, fc="white", ec=MUTED, lw=0.8, hatch="\\\\"))
a.text(sum(FLOOR_OPEN) / 2, ZF - 6.5, "floor opening into the neck channel", ha="center", fontsize=8, color=MUTED)
for x, z in COLS + UCOLS: a.add_patch(Circle((x, z), 3.2, fc=WALLC, ec=MUTED, lw=0.8))
for name, (x, z) in list(TOG.items()) + list(UTOG.items()):
    a.add_patch(Rectangle((x - TW / 2, z - TH / 2), TW, TH, fc=SWC, ec="#a86b12", lw=1, alpha=0.85))
    a.text(x, z, f"{name}\ntoggle", ha="center", va="center", fontsize=7.5)
a.add_patch(Circle(HAT[:2], HAT[2], fc="#f3d9a8", ec="#a86b12", lw=1, ls="--", alpha=0.6))
a.add_patch(Circle(PB4[:2], PB4[2], fc=SWC, ec="#a86b12", lw=1, alpha=0.85)); a.text(*PB4[:2], "STOP REL", ha="center", va="center", fontsize=7)
a.add_patch(Circle(POT[:2], POT[2], fc=SWC, ec="#a86b12", lw=1, alpha=0.85)); a.text(*POT[:2], "pot", ha="center", va="center", fontsize=7)
for x, z in BTN: a.add_patch(Circle((x, z), BTN_R, fc=SWC, ec="#a86b12", lw=1, alpha=0.85))
a.add_patch(Rectangle((POT_X[0], POT_Z[0]), POT_X[1] - POT_X[0], POT_Z[1] - POT_Z[0], fc=POTC, ec="#5b4380", lw=1, ls="--", alpha=0.35))
a.text(sum(POT_X) / 2, POT_Z[1] - 3.2, "throttle\npot", ha="center", va="center", fontsize=7, color="#3d2c57")
a.add_patch(Rectangle((X0, ZB), BW, BL, fc=BOARDC, ec="#1e3a5f", lw=1.2, alpha=0.5))
for xb in (HOLE_IN, BL - HOLE_IN):                                  # M3 nuts, one in each corner
    for yb in (HOLE_IN, BW - HOLE_IN):
        a.add_patch(RegularPolygon((hx(yb), hz(xb)), 6, radius=NUT_R, fc="#b08d57", ec=INK, lw=0.6))
a.annotate("M3 nuts on 4 mm\nspacers (4)", (hx(BW - HOLE_IN) + 2.5, hz(BL - HOLE_IN) + 1.5), (47.0, 77.0), fontsize=7, ha="center",
           va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
a.add_patch(Rectangle((hx(PMC_Y - PMW / 2), hz(PMX0)), PMW, PML, fc=PMC, ec="#0f2a44", lw=1, alpha=0.8))
a.text(hx(PMC_Y), hz(PMX0 + PML / 2), "Pro Micro", ha="center", va="center", fontsize=8, color="white")
a.text(hx(2.2), hz(19), "J1  AX3  AX4", ha="center", va="center", fontsize=7, color=INK, rotation=90)
a.text(hx(BW - 2.2), hz(19), "J2  AX1  AX2", ha="center", va="center", fontsize=7, color=INK, rotation=90)
for yb, nm in zip(BTN_YB, ("PROG4", "RST", "PROG1")):               # buttons at the top end, in the upper box
    a.add_patch(Rectangle((hx(yb) - 1.45, hz(BTN_XB) - 1.95), 2.9, 3.9, fc="#d1d5db", ec=INK, lw=0.7))
    a.text(hx(yb), hz(BTN_XB) - 2.6, nm, ha="center", va="top", fontsize=5.5, color=INK)
px = hx(PMC_Y); pz = hz(PMX0) - PLUG_L
a.add_patch(Rectangle((px - PLUG_W / 2, pz), PLUG_W, PLUG_L, fc=PLUGC, ec=INK, lw=1, alpha=0.85))
a.add_patch(Rectangle((px - PLUG_W / 2, hz(PMX0) - PLUG_L_LONG), PLUG_W, PLUG_L_LONG - PLUG_L, fill=False, ec=INK, lw=0.8, ls=":"))
a.plot([px, px, 13.0, 13.0], [pz, 16, 10, ZF - 3], color=INK, lw=3.2, alpha=0.6, solid_joinstyle="round")
a.annotate("USB plug (20 mm; dotted 25 mm);\nthe cable has room to bend\nbefore the floor opening", (px - 5.5, pz + 6), (-17.0, 21.0),
           fontsize=8, ha="center", va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
def dim(x0, z, x1, label, dz=1.4):
    a.annotate("", (x0, z), (x1, z), arrowprops=dict(arrowstyle="<->", color=OK, lw=0.9))
    a.text((x0 + x1) / 2, z + dz, label, ha="center", fontsize=7.5, color=OK)
gx = TOG["GOV RPM"][0] + TW / 2; lx = TOG["LDG LT EXT/RETR"][0] - TW / 2
dim(gx, 50, X0, f"{X0 - gx:.1f}"); dim(X0 + BW, 50, lx, f"{lx - X0 - BW:.1f}")
utz = UTOG["SL"][1] - TH / 2
a.annotate("", (X0 + 3, TOP), (X0 + 3, utz), arrowprops=dict(arrowstyle="<->", color=OK, lw=0.9))
a.text(X0 + 4, (TOP + utz) / 2 + 1.2, f"{utz - TOP:.2f} to the upper toggles", fontsize=7.5, color=OK)
pz_long = hz(PMX0) - PLUG_L_LONG                                   # the plug comes down beside the pot, not over it
a.annotate("", (POT_X[1], POT_Z[1] - 1.5), (px - PLUG_W / 2, POT_Z[1] - 1.5), arrowprops=dict(arrowstyle="<->", color=OK, lw=0.9))
a.text((POT_X[1] + px - PLUG_W / 2) / 2, POT_Z[1] + 0.2, f"{px - PLUG_W / 2 - POT_X[1]:.2f}", ha="center", fontsize=7.5, color=OK)
a.set_xlim(XL - 4, XR + 4); a.set_ylim(ZF - 12, UZT + 6)
a.set_xlabel("x (mm)", color=MUTED, fontsize=8); a.set_ylabel("z (mm)", color=MUTED, fontsize=8)

b.set_title("Side view over the board (projected along x)", color=INK, fontsize=11, loc="left")
Y = lambda off: REAR - off
b.add_patch(Rectangle((-2.5, ZF), 2.5, CEIL + 2.5 - ZF, fc=WALLC, ec=MUTED, lw=0.8)); b.text(-1.25, 12, "lower panel", rotation=90, ha="center", va="center", fontsize=7)
b.add_patch(Rectangle((0, ZF), PLUGB, CEIL - ZF, fc="#dde0e4", ec=MUTED, lw=0.6))
b.add_patch(Rectangle((UY - 2.5, CEIL + 2.5), 2.5, UZT - CEIL, fc=WALLC, ec=MUTED, lw=0.8)); b.text(UY - 1.25, 100, "upper panel", rotation=90, ha="center", va="center", fontsize=7)
b.add_patch(Rectangle((UY, CEIL + 2.5), PLUGB, UZT - CEIL - 2.5, fc="#dde0e4", ec=MUTED, lw=0.6))
b.add_patch(Rectangle((REAR, ZF), 2.5, UZT + 2.5 - ZF, fc=WALLC, ec=MUTED, lw=0.8)); b.text(REAR + 1.25, 30, "rear wall", rotation=90, ha="center", va="center", fontsize=7.5)
b.add_patch(Rectangle((-2.5, CEIL), SLOT[2] + 2.5, 2.5, fc=WALLC, ec=MUTED, lw=0.8))
b.add_patch(Polygon([(UY, CEIL + 2.5), (SLOT[2], CEIL + 2.5), (SLOT[2], CEIL + 5.0), (UY, CEIL + 5.0)], fc=WALLC, ec=MUTED, lw=0.8))
b.text(UY + 1.5, CEIL + 6.3, "rib", fontsize=7, ha="center")
b.add_patch(Rectangle((SLOT[2], CEIL), REAR - SLOT[2], 2.5, fc="white", ec=OK, lw=1.0, hatch="////"))
b.add_patch(Rectangle((UY + PLUGB - 1.8, utz), TBODY, TH, fc=SWC, ec="#a86b12", lw=1, alpha=0.85)); b.text(UY + 8, utz + TH / 2, "upper\ntoggles", ha="center", va="center", fontsize=7)
b.add_patch(Rectangle((PLUGB, 27.65), TBODY, TH, fc=SWC, ec="#a86b12", lw=1, alpha=0.5)); b.text(PLUGB + 8.5, 33, "lower toggles\n(beside the board)", ha="center", va="center", fontsize=6.5)
b.add_patch(Polygon(POT_SIDE, closed=True, fc=POTC, ec="#5b4380", lw=1, ls="--", alpha=0.35))
b.text(sum(y for y, _ in POT_SIDE) / 4 + 1, sum(z for _, z in POT_SIDE) / 4, "throttle\npot", ha="center", va="center", fontsize=6.5, color="#3d2c57")
for zh in (hz(HOLE_IN), hz(BL - HOLE_IN)):           # spacers behind the board, nuts on its front
    b.add_patch(Rectangle((Y(SPACER), zh - 3.2), SPACER, 6.4, fc="#9aa3ad", ec=INK, lw=0.6))
    b.add_patch(Rectangle((Y(PCB_F + 2.4), zh - 2.75), 2.4, 5.5, fc="#b08d57", ec=INK, lw=0.6))
b.add_patch(Rectangle((Y(PCB_F), ZB), 1.6, BL, fc=BOARDC, ec="#1e3a5f", lw=0.8))
b.add_patch(Rectangle((Y(PCB_F + 8.5), hz(PMX0 + 1.27)), 8.5, PML - 2.54, fc="#2b2f36", ec=INK, lw=0.5, alpha=0.75))
b.add_patch(Rectangle((Y(PM_B + 1.6), hz(PMX0)), 1.6, PML, fc=PMC, ec="#0f2a44", lw=0.8))
b.add_patch(Rectangle((Y(STACK), hz(PMX0)), 2.8, 3.0, fc="#555", ec=INK, lw=0.5))
b.add_patch(Rectangle((Y(PM_B + 1.6 + 1.4 + 3.75), pz), 7.5, PLUG_L, fc=PLUGC, ec=INK, lw=1, alpha=0.85))
b.annotate("", (SLOT[2], CEIL + 1.25), (Y(STACK_PM), CEIL + 1.25), arrowprops=dict(arrowstyle="<->", color=OK, lw=0.9))
b.text(Y(STACK_PM) - 1, CEIL - 3.5, f"{Y(STACK_PM) - SLOT[2]:.1f} to the slot's front edge", fontsize=7, color=OK, ha="right")
b.set_xlim(-4, REAR + 4); b.set_ylim(ZF - 12, UZT + 6)
b.set_xlabel("y: panel back -> rear wall (mm)", color=MUTED, fontsize=8)

fig.suptitle("HeliSR Rev 3.0 in the Huey head: upright on the rear wall, USB end down, reaching up through the slot", fontsize=13, color=INK, x=0.01, ha="left", y=0.99)
fig.text(0.01, 0.012, "Box frame from huey_head.py, checked against the STLs. Toggles: APEM 600H 14.65 x 29.7 mm (upper ones with lugs bent flat).\n"
         "Throttle pot: the envelope in huey_head.py. Stack: 4 mm spacer (Bivar SRS-4-4MM) + board + socket + header + Pro Micro = 19.4 mm (21 mm at the USB receptacle). Micro-USB overmold 10.5 x 7.5 mm, 20-25 mm long.",
         fontsize=7.2, color=MUTED, va="bottom")
fig.tight_layout(rect=(0, 0.04, 1, 0.97)); fig.savefig(out, dpi=150, facecolor="white")
print(f"board x {X0:.2f}..{X0 + BW:.2f}, z {ZB:.1f}..{TOP:.1f}; slot margins {X0 - SLOT[0]:.2f} / {SLOT[1] - X0 - BW:.2f}")
print(f"to GOV {X0 - gx:.1f}, to LDG {lx - X0 - BW:.1f}, top to upper toggles {utz - TOP:.2f}, Pro Micro to slot front edge {Y(STACK_PM) - SLOT[2]:.1f}")
print(f"pot x {POT_X}, z {POT_Z[0]:.2f}..{POT_Z[1]:.2f}, side {[(round(y, 2), round(z, 2)) for y, z in POT_SIDE]}")
print(f"plug x {px - PLUG_W / 2:.2f}..{px + PLUG_W / 2:.2f} ({px - PLUG_W / 2 - POT_X[1]:.2f} beside the pot), plug end z {pz:.1f} (25 mm plug: {pz - 5:.1f}); upper columns inner edges {UCOLS[0][0] + 3.2:.1f} / {UCOLS[1][0] - 3.2:.1f}")
