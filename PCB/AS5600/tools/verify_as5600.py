# Check the AS5600 board pad by pad against tables written here by hand from the AS5600 datasheet (ams v1-06, page 3,
# "Pin Description") and the HeliSR Rev 4.0 AX port's pinout, not from gen_as5600.py. Also checks that the front parts
# stay inside the area that's clear in both mounts, and the outline and holes.
# Run with KiCad 9's python. usage: verify_as5600.py <board.kicad_pcb>
import sys
try:                                           # KiCad's internal checks (wx asserts) log instead of opening a dialog
    import wx; wx.DisableAsserts()
except Exception:
    pass
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
for f in b.GetFootprints(): f.BuildCourtyardCaches()
bad = []
P = {}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNumber(): P.setdefault((f.GetReference(), p.GetNumber()), set()).add(p.GetNetname())
def want(ref, num, name):
    got = P.get((ref, str(num)))
    if got != {name}: bad.append(f"{ref} pad {num}: {got}, want {name!r}")

# AS5600 SOIC-8: 1 VDD5V, 2 VDD3V3, 3 OUT (to its test pad only), 4 GND, 5 PGO, 6 SDA, 7 SCL, 8 DIR
for n, name in {1: "VCC", 2: "VDD3V3", 3: "OUT", 4: "GND", 5: "", 6: "SDA", 7: "SCL", 8: "GND"}.items():
    want("U1", n, name)
# test pads on the front, by value (their label)
tp = {f.GetValue(): f for f in b.GetFootprints() if f.GetReference().startswith("TP")}
for label, name in {"5V": "VCC", "GND": "GND", "3V3": "VDD3V3", "SCL": "SCL", "SDA": "SDA", "OUT": "OUT"}.items():
    f = tp.get(label)
    if f is None: bad.append(f"no test pad {label}"); continue
    want(f.GetReference(), 1, name)
    if f.IsFlipped(): bad.append(f"test pad {label} on the back")
if len(tp) != 6: bad.append(f"{len(tp)} test pads, want 6")
# HeliSR AX port: 1 SDA, 2 GND, 3 VCC, 4 SCL; the A04SR04SR30K254B jumper is 1:N, so the far end sees pin n as 5 - n
port = {1: "SDA", 2: "GND", 3: "VCC", 4: "SCL"}
for n in range(1, 5): want("J1", n, port[5 - n])
want("J1", "MP", "GND")
for ref, pair in (("C1", {"VCC", "GND"}), ("C2", {"VDD3V3", "GND"})):
    got = P.get((ref, "1"), set()) | P.get((ref, "2"), set())
    if got != pair: bad.append(f"{ref}: {got}, want {pair}")
val = {"U1": "AS5600", "C1": "100nF", "C2": "1uF"}
for ref, v in val.items():
    f = b.FindFootprintByReference(ref)
    if f.GetValue() != v: bad.append(f"{ref} value {f.GetValue()}")
    if f.IsFlipped(): bad.append(f"{ref} on the back")
if not b.FindFootprintByReference("J1").IsFlipped(): bad.append("J1 on the front")

# outline 23.24 square, centre; front parts inside +-7 mm of the centre; J1 centred
bb = b.GetBoardEdgesBoundingBox()
w, h = mm(bb.GetWidth()) - 0.1, mm(bb.GetHeight()) - 0.1                 # less the 0.1 mm edge line
cx, cy = mm(bb.Centre().x), mm(bb.Centre().y)
if abs(w - 23.24) > 0.005 or abs(h - 23.24) > 0.005: bad.append(f"outline {w:.3f} x {h:.3f}")
for ref in ("U1", "C1", "C2"):
    c = b.FindFootprintByReference(ref).GetCourtyard(pcbnew.F_CrtYd).BBox()
    ext = max(abs(mm(c.GetX()) - cx), abs(mm(c.GetRight()) - cx), abs(mm(c.GetY()) - cy), abs(mm(c.GetBottom()) - cy))
    if ext > 7.0: bad.append(f"{ref} reaches {ext:.2f} mm from the centre")
u = b.FindFootprintByReference("U1").GetPosition()
if abs(mm(u.x) - cx) > 0.001 or abs(mm(u.y) - cy) > 0.001: bad.append("U1 not on the centre")
jc = b.FindFootprintByReference("J1").GetCourtyard(pcbnew.B_CrtYd).BBox().Centre()
if abs(mm(jc.x) - cx) > 0.001 or abs(mm(jc.y) - cy) > 0.001: bad.append("J1 not centred")
holes = sorted((round(mm(p.GetPosition().x) - cx, 3), round(mm(p.GetPosition().y) - cy, 3), round(mm(p.GetDrillSize().x), 2))
               for f in b.GetFootprints() if f.GetReference().startswith("H") for p in f.Pads())
want_holes = sorted((sx * 8.0, sy * 8.0, 2.4) for sx in (-1, 1) for sy in (-1, 1))      # a 16 mm square
if holes != want_holes: bad.append(f"holes {holes}")
print(f"{len(P)} pads checked")
if bad:
    print("\n".join(bad)); raise SystemExit(f"{len(bad)} errors")
print("netlist and placement OK")
