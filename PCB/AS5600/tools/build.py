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

rows = [["Ref", "Qty per board", "Part", "Manufacturer part", "Digi-Key part", "Package", "Notes"],
        ["U1", 1, "AS5600 magnetic angle sensor", "ams OSRAM AS5600-ASOM", "AS5600-ASOMCT-ND", "SOIC-8", ""],
        ["C1", 1, "100 nF, 50 V, X7R", "Samsung CL31B104KBCNNNC", "1276-1017-1-ND", "1206", "0.85 mm thick"],
        ["C2", 1, "1 uF, 16 V, X7R", "YAGEO CC1206JKX7R7BB105", "311-1924-1-ND", "1206",
         "about 1.15 mm thick: the base's cover is 2.0 mm off the board"],
        ["J1", 1, "JST SH 4-pin vertical header", "JST BM04B-SRSS-TB", "455-BM04B-SRSS-TBCT-ND", "SMD, 1.0 mm",
         "the HeliSR's AX port part"],
        ["Magnet", 1, "Magnet, 6 x 2.5 mm, diametric, N35SH", "Radial Magnets 9049", "469-1075-ND", "",
         "in the base's sensor cover or the head's magnet shaft"],
        ["Cable", 1, "JST SR jumper, 1:N, 6 in", "JST A04SR04SR30K152B", "455-3014-ND", "",
         "1:N (pin n to pin 5-n); a 1:1 cable won't work"]]
with open(os.path.join(OUT, NAME + "_BOM.csv"), "w", newline="") as f: csv.writer(f).writerows(rows)
print("BOM written")
