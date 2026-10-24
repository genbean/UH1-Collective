# Independent check of the Rev 3.0 netlist against Rev 2.0 and against the 74HC165 / Pro Micro pinouts. Rev 3.0 is
# the Rev 2.0 circuit plus two programming buttons (PROG1: SW2 + R1 from AX1 to GND; PROG4: SW3 + R2 from AX4 to
# GND); only which pull-up and shift-register input
# each of IN5-IN16 uses may differ. Writes the input map with the shift order.
# Run with KiCad 9's python. usage: verify_netlist_v3.py <rev2.0.kicad_pcb> <rev3.0.kicad_pcb> <input_map.csv out>
import sys, collections
import pcbnew

old, new, csv_out = sys.argv[1:4]
def netmap(path):
    b = pcbnew.LoadBoard(path)
    nets = collections.defaultdict(set)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname(): nets[p.GetNetname()].add((f.GetReference(), p.GetNumber()))
    return nets
A, B = netmap(old), netmap(new)
errors = []
def check(cond, msg):
    if not cond: errors.append(msg)

INS = {f"IN{k}" for k in range(1, 17)}
NEW = {(r, n) for r in ("SW2", "SW3", "R1", "R2") for n in ("1", "2")}
check(set(B) == set(A) | {"PROG1", "PROG4"}, f"net names: {set(A) ^ set(B)}")
for n in sorted(set(A) - INS):
    extra = {p for p in B[n] if p not in A[n]}
    check(A[n] <= B[n] and extra <= NEW, f"{n}: lost {sorted(A[n] - B[n])}, gained {sorted(extra)}")
check(B["PROG1"] == {("R1", "2"), ("SW2", "1")}, f"PROG1 {sorted(B['PROG1'])}")
check(B["PROG4"] == {("R2", "2"), ("SW3", "1")}, f"PROG4 {sorted(B['PROG4'])}")
check(("SW2", "2") in B["GND"] and ("SW3", "2") in B["GND"], "PROG buttons to GND")
U_IN = {"11": "A", "12": "B", "13": "C", "14": "D", "3": "E", "4": "F", "5": "G", "6": "H"}
used, rows = set(), []
for k in range(1, 17):
    n = f"IN{k}"; pads = B[n]
    conn = [p for p in pads if p[0] in ("J1", "J2")]
    rn = [p for p in pads if p[0] in ("RN1", "RN2")]
    u = [p for p in pads if p[0] in ("U1", "U2")]
    check(len(pads) == 3 and len(conn) == 1 and len(rn) == 1 and len(u) == 1, f"{n} pads {sorted(pads)}")
    check(conn == [p for p in A[n] if p[0] in ("J1", "J2")], f"{n} connector pin changed: {conn}")
    check(rn and rn[0][1] in [str(i) for i in range(2, 10)], f"{n} not on a resistor pin 2-9: {rn}")
    check(u and u[0][1] in U_IN, f"{n} not on a 74HC165 input: {u}")
    if u and conn:
        check(u[0] not in used, f"{u[0]} used twice"); used.add(u[0])
        rows.append((n, conn[0], u[0]))
check(len(used) == 16, f"only {len(used)} shift-register inputs used")
check(("RN1", "1") in B["VCC"] and ("RN2", "1") in B["VCC"], "resistor network common pins not on VCC")
for u in ("U1", "U2"):
    check((u, "1") in B["SR_LOAD"] and (u, "2") in B["SR_CLK"] and (u, "8") in B["GND"] and (u, "15") in B["GND"]
          and (u, "16") in B["VCC"], f"{u} control/supply pins")
check(B["SR_CHAIN"] == {("U1", "9"), ("U2", "10")} and ("U1", "10") in B["GND"], "chain U1 QH -> U2 SER, U1 SER low")
check(B["SR_DATA"] == {("U2", "9"), ("J7", "5")}, "U2 QH -> Pro Micro pin 5 ('2', PD1)")
check(("J7", "6") in B["SR_LOAD"] and ("J8", "16") in B["SR_CLK"], "latch on pin 6 ('3', PD0), clock on pin 16 ('15', PB1)")
check(B["RST"] == {("J8", "22"), ("SW1", "1")} and ("SW1", "2") in B["GND"], "reset button")
for k, pin in ((1, "20"), (2, "19"), (3, "18"), (4, "17")):
    want = {(f"J{10 + k}", "2"), ("J8", pin)} | {1: {("R1", "1")}, 4: {("R2", "1")}}.get(k, set())
    check(B[f"AX{k}"] == want, f"AX{k}")
    check((f"J{10 + k}", "1") in B["VCC"] and (f"J{10 + k}", "3") in B["GND"], f"AX{k} supply pins")

order = [("U2", c) for c in "HGFEDCBA"] + [("U1", c) for c in "HGFEDCBA"]
old_order = {}
for n in sorted(INS):
    u = [p for p in A[n] if p[0] in ("U1", "U2")][0]
    old_order[n] = order.index((u[0], U_IN[u[1]])) + 1
with open(csv_out, "w", newline="") as f:
    f.write("Input,Connector,Connector pin,Chip,Chip input,Chip pin,Shift order (1 = first bit read),Rev 2.0 shift order\n")
    for n, (cref, cpin), (uref, upin) in rows:
        ch = U_IN[upin]
        f.write(f"{n},{cref} ({'1-8' if cref == 'J1' else '9-16'}),{cpin},{uref},{ch},{upin},"
                f"{order.index((uref, ch)) + 1},{old_order[n]}\n")
    for k, (jr, pin, a) in enumerate((("J11", "A3", "F4"), ("J12", "A2", "F5"), ("J13", "A1", "F6"), ("J14", "A0", "F7"))):
        f.write(f"AX{k + 1},{jr} (AX{k + 1}),2,Pro Micro,{pin},MMJoy2 {a},,\n")
print("checks failed:", len(errors))
for e in errors: print("  FAIL", e)
for n, c, u in rows:
    new_bit = order.index((u[0], U_IN[u[1]])) + 1
    print(f"  {n:5} {c[0]}.{c[1]:2} -> {u[0]}.{u[1]:2} ({U_IN[u[1]]})  bit {new_bit:2}  (Rev 2.0: {old_order[n]:2}){'  changed' if new_bit != old_order[n] else ''}")
