# Check the Rev 4.0 netlist pad by pad.
#   - The parts carried over from Rev 3.0 (J1, J2, U1, U2, RN1, RN2, C1-C3, SW1's RST/GND) must be on the same nets as
#     in the ordered Rev 3.0 board, read from ../HeliSR_Rev3.0. Only the shift-register lines' names to the Pro Micro
#     are allowed to differ, and they are checked below.
#   - Every other pad is checked against the table written out here by hand from the PCA9546A datasheet and the
#     Pro Micro pinout (not from gen_v4.py).
#   - Every net must join at least two pads, and every pad of a part must be on a net, except the Pro Micro's
#     unused pins.
# With a third argument, also writes the input map: Rev 3.0's IN1-IN16 rows (HeliSR_Rev3.0_Input_Map.csv, next to its
# board), less its Rev 2.0 column, which hold for Rev 4.0 only because the check above finds the inputs' parts on the
# same nets; then a row for each AS5600 port with its PCA9546A channel.
# Run with KiCad 9's python. usage: verify_netlist_v4.py <rev4.kicad_pcb> <rev3.kicad_pcb> [out Input_Map.csv]
import sys
import pcbnew

b4, b3 = (pcbnew.LoadBoard(p) for p in sys.argv[1:3])
def pads(b):
    out = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNumber(): out.setdefault((f.GetReference(), p.GetNumber()), set()).add(p.GetNetname())
    return {k: (v.pop() if len(v) == 1 else tuple(sorted(v))) for k, v in out.items()}
P4, P3 = pads(b4), pads(b3)
bad = []
def want(ref, num, netname):
    got = P4.get((ref, str(num)))
    if got != netname: bad.append(f"{ref} pad {num}: {got!r}, want {netname!r}")

# ---- carried over from Rev 3.0 -----------------------------------------------------------------------------
for (ref, num), n3 in P3.items():
    if ref in ("J1", "J2", "U1", "U2", "RN1", "RN2", "C1", "C2", "C3") or (ref == "SW1"):
        want(ref, num, n3)

# ---- Pro Micro sockets (J7 pins 1-12, J8 pins 13-24) ------------------------------------------------------------
PM = {3: "GND", 4: "GND", 23: "GND", 21: "VCC", 22: "RST",
      5: "SDA", 6: "SCL",                          # "2" = PD1 SDA, "3" = PD0 SCL
      16: "SR_CLK", 15: "SR_DATA", 17: "SR_LOAD",  # "15" PB1, "14" PB3, A0 PF7
      18: "MUX_RST"}                               # A1 PF6
for k in range(1, 25):
    want("J7" if k <= 12 else "J8", k, PM.get(k, ""))

# ---- PCA9546A (U3): datasheet pinout; channel n -> port -------------------------------------------------------
CH = {0: "AX4", 1: "AX2", 2: "AX1", 3: "AX3"}
U3 = {1: "GND", 2: "GND", 3: "MUX_RST", 8: "GND", 13: "GND", 14: "SCL", 15: "SDA", 16: "VCC",
      4: CH[0] + "_SDA", 5: CH[0] + "_SCL", 6: CH[1] + "_SDA", 7: CH[1] + "_SCL",
      9: CH[2] + "_SDA", 10: CH[2] + "_SCL", 11: CH[3] + "_SDA", 12: CH[3] + "_SCL"}
for k, n in U3.items(): want("U3", k, n)

# ---- ports: JST SH 4-pin, 1 SDA, 2 GND, 3 VCC, 4 SCL; mounting pads to GND -------------------------------------
for ref, ax in (("J11", "AX1"), ("J12", "AX2"), ("J13", "AX3"), ("J14", "AX4")):
    for k, n in ((1, ax + "_SDA"), (2, "GND"), (3, "VCC"), (4, ax + "_SCL"), ("MP", "GND")): want(ref, k, n)

# ---- resistors and C4: each a two-terminal part between the nets given (either way round) --------------------------
TWO = {"C4": ("GND", "VCC"), "R9": ("SDA", "VCC"), "R10": ("SCL", "VCC"), "R11": ("MUX_RST", "VCC")}
for i, ax in enumerate(("AX1", "AX2", "AX3", "AX4")):
    TWO[f"R{2 * i + 1}"] = (ax + "_SDA", "VCC"); TWO[f"R{2 * i + 2}"] = (ax + "_SCL", "VCC")
for ref, nn in TWO.items():
    got = tuple(sorted((P4.get((ref, "1")), P4.get((ref, "2")))))
    if got != tuple(sorted(nn)): bad.append(f"{ref}: {got}, want {tuple(sorted(nn))}")
VAL = {"U3": "PCA9546A", "C4": "100nF", "R9": "10k", "R10": "10k", "R11": "10k", **{f"R{k}": "2.2k" for k in range(1, 9)}}
for ref, v in VAL.items():
    f = b4.FindFootprintByReference(ref)
    if f is None or f.GetValue() != v: bad.append(f"{ref}: value {None if f is None else f.GetValue()!r}, want {v!r}")
    elif not f.IsFlipped(): bad.append(f"{ref} is on the front, want the back")
for ref in ("J1", "J2", "J11", "J12", "J13", "J14", "SW1", "J7", "J8", "U1", "U2", "RN1", "RN2", "C1", "C2", "C3"):
    if b4.FindFootprintByReference(ref).IsFlipped(): bad.append(f"{ref} is on the back, want the front")

# ---- nothing extra: every part checked, every net joins two or more pads ----------------------------------------
known = {"J1", "J2", "U1", "U2", "RN1", "RN2", "C1", "C2", "C3", "SW1", "J7", "J8", "U3", "J11", "J12", "J13", "J14",
         "H1", "H2", "H3", "H4", *TWO}
extra = {r for r, _ in P4} - known
if extra: bad.append(f"unexpected parts: {sorted(extra)}")
count = {}
for (ref, num), n in P4.items():
    if n: count[n] = count.get(n, 0) + 1
for n, c in sorted(count.items()):
    if c < 2: bad.append(f"net {n} has only {c} pad")
print(f"{len(P4)} pads, {len(count)} nets checked")
if bad:
    print("\n".join(bad)); raise SystemExit(f"{len(bad)} netlist errors")
print("netlist OK")
if len(sys.argv) > 3:
    import csv, os
    src = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), "HeliSR_Rev3.0_Input_Map.csv")
    rows = list(csv.reader(open(src, newline="")))
    assert rows[0][-1] == "Rev 2.0 shift order", rows[0]
    rows = [r[:-1] for r in rows if r[0] == "Input" or r[0].startswith("IN")]     # Rev 3.0's analog AX rows don't apply
    assert len(rows) == 17
    rows[0][-1] = "Shift order (1 = first bit read) / I2C channel"
    for ax, ref in (("AX1", "J11"), ("AX2", "J12"), ("AX3", "J13"), ("AX4", "J14")):
        ch = [c for c, a in CH.items() if a == ax][0]
        sd, sc = [k for k, n in U3.items() if n == ax + "_SDA"][0], [k for k, n in U3.items() if n == ax + "_SCL"][0]
        rows.append([ax, f"{ref} ({ax})", "1 SDA / 4 SCL", "U3 (PCA9546A)", f"SD{ch} / SC{ch}", f"{sd} / {sc}", f"channel {ch}"])
    with open(sys.argv[3], "w", newline="") as f: csv.writer(f).writerows(rows)
    print("wrote", sys.argv[3], len(rows) - 1, "rows")
