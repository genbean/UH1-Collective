# Build the AS5600 board end to end: generate it, DRC, check the netlist, then write the Gerbers, the renders and the
# BOM. Runs with the repo's .venv python (or any Python 3); KiCad 9's python and kicad-cli are found by kicad_run.py.
# usage: build.py            (writes into PCB/AS5600)
import csv, json, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kicad_run import KPY, KCLI

OUT = os.path.dirname(HERE)
NAME = "AS5600_Rev1.0"
PCB = os.path.join(OUT, NAME + ".kicad_pcb")

def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    text = "\n".join(l for l in (r.stdout + r.stderr).splitlines()
                     if "swig" not in l and "image handler" not in l and "assert" not in l)
    if check and r.returncode != 0:
        raw = (r.stdout + r.stderr).strip().splitlines()
        raise SystemExit(f"FAILED (exit {r.returncode}) {os.path.basename(args[0])} {args[1:3]}\n{text[-1500:]}\n--- raw tail:\n"
                         + "\n".join(raw[-6:]))
    return text

print(sh([KPY, "-I", os.path.join(HERE, "gen_as5600.py"), PCB]).splitlines()[-1])
pro = os.path.join(OUT, NAME + ".kicad_pro")
if not os.path.exists(pro):
    json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 1}}, open(pro, "w"), indent=2)

rpt = os.path.join(tempfile.gettempdir(), NAME + "_drc.json")
sh([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, PCB], check=False)
j = json.load(open(rpt))
types = {}
for v in j["violations"]:
    types[v["type"]] = types.get(v["type"], 0) + 1
    print("  ", v["severity"], v["type"], "|", v["description"], "|", "; ".join(i["description"] for i in v["items"]))
print("DRC:", len(j.get("unconnected_items", [])), "unconnected,", types or "no violations")
for u in j.get("unconnected_items", []): print("   unconnected:", "; ".join(i["description"] for i in u["items"]))

print(sh([KPY, "-I", os.path.join(HERE, "verify_as5600.py"), PCB]))

tmp = tempfile.mkdtemp(prefix="as5600_")
try:
    g = os.path.join(tmp, "gerbers"); os.makedirs(g)
    sh([KCLI, "pcb", "export", "gerbers", "--layers",
        "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", "-o", g + os.sep, PCB])
    sh([KCLI, "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-zeros-format", "decimal", "--excellon-separate-th", "-o", g + os.sep, PCB])
    with zipfile.ZipFile(os.path.join(OUT, NAME + "_Gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
    print("Gerbers:", sorted(os.listdir(g)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

for side, label in (("top", "Front"), ("bottom", "Back")):
    png = os.path.join(OUT, f"{NAME}_{label}.png")
    sh([KCLI, "pcb", "render", "--side", side, "--width", "1200", "--height", "1200", "--quality", "high",
        "--background", "opaque", "--zoom", "1", "-o", png, PCB])
    print("render", os.path.basename(png))

rows = [["Ref", "Qty per board", "Part", "Manufacturer part", "Package", "Notes"],
        ["U1", 1, "AS5600 magnetic angle sensor", "AS5600-ASOM", "SOIC-8", "lift it off a WWZMDiB module, or buy new"],
        ["C1", 1, "100 nF, 50 V, X7R", "CL31B104KBCNNNC", "1206", "the HeliSR's C1/C2/C4 part; 0.95 mm max tall"],
        ["C2", 1, "1 uF, 16 V, X7R, low profile", "CL31B105KOFNNNE", "1206", "1.25 mm thick: the base's cover is 2.0 mm off the board"],
        ["J1", 1, "JST SH 4-pin vertical header", "BM04B-SRSS-G-TB(LF)(SN)", "SMD, 1.0 mm", "the HeliSR's AX port part"],
        ["Cable", 1, "JST SR jumper, 1:N, 10 in", "A04SR04SR30K254B", "", "1:N (pin n to pin 5-n); a 1:1 cable won't work"]]
with open(os.path.join(OUT, NAME + "_BOM.csv"), "w", newline="") as f: csv.writer(f).writerows(rows)
print("BOM written")
