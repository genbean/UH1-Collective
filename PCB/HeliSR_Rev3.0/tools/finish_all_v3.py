# Finish a routed Rev 3.0 board end to end: pours, silk labels, GND stitching, rules, DRC.
# Runs under a Python with shapely (the label and via searches); KiCad steps use KiCad's python.
# usage: finish_all_v3.py <run dir with v3_routed.kicad_pcb> <out dir> <tools dir with silk_*/stitch_* scripts>
import json, os, shutil, subprocess, sys

run, out, tools = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
KPY = r"C:/Program Files/KiCad/9.0/bin/python.exe"
KCLI = r"C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"
PY = sys.executable
NAME = "HeliSR_Rev3.0"

def sh(args, env=None):
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if "swig" not in l and "image handler" not in l]
    if r.returncode != 0: raise SystemExit(f"FAILED {args}\n" + "\n".join(lines[-20:]))
    return "\n".join(lines)
def drc(board):
    rpt = os.path.splitext(board)[0] + "_drc.json"
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, board], capture_output=True)
    return json.load(open(rpt))

if os.path.isdir(out): shutil.rmtree(out)
os.makedirs(out)
w = os.path.join(out, "work"); os.makedirs(w)
for f in ("v3_routed.kicad_pcb", "v3_routed.kicad_pro", "v3_layout.json"): shutil.copy(os.path.join(run, f), w)
shutil.copytree(os.path.join(run, "HeliSR.pretty"), os.path.join(w, "HeliSR.pretty"))
j = lambda *p: os.path.join(w, *p)
print(sh([KPY, "-I", os.path.join(HERE, "finish_v3.py"), "pour", j("v3_routed.kicad_pcb"), j("v3_layout.json"), j("poured.kicad_pcb")]))
shutil.copy(j("v3_routed.kicad_pro"), j("poured.kicad_pro"))
# GND stitching first, ignoring the labels, so every pour island that can be tied to ground gets its via; then the
# labels are placed around the vias.
sh([KPY, "-I", os.path.join(tools, "stitch_export.py"), j("poured.kicad_pcb"), j("stitch.json"), "--keep-islands", "--no-labels"])
env = dict(os.environ, STITCH_TARGET="5.0")
print(sh([PY, "-I", os.path.join(tools, "stitch_place.py"), j("stitch.json"), j("vias.json")], env).splitlines()[0])
sh([KPY, "-I", os.path.join(tools, "silk_export.py"), j("poured.kicad_pcb"), j("silk0.json")])      # labels as placed
s0 = json.load(open(j("silk0.json")))
json.dump([{"text": L["text"], "new_text": L["new_text"], "side": L["side"], "x": L["x"], "y": L["y"], "size": L["h"]}
           for L in s0["labels"]], open(j("labels0.json"), "w"))
sh([KPY, "-I", os.path.join(HERE, "finish_v3.py"), "final", j("poured.kicad_pcb"), j("vias.json"), j("labels0.json"), j("with_vias")])
sh([KPY, "-I", os.path.join(tools, "silk_export.py"), j("with_vias", NAME + ".kicad_pcb"), j("silk.json")])
env = dict(os.environ, SILK_MAXD="3.0")
print(sh([PY, "-I", os.path.join(tools, "silk_place.py"), j("silk.json"), j("labels.json")], env))

def final(full):
    json.dump(full, open(j("full.json"), "w"))
    fin = os.path.join(out, "board")
    if os.path.isdir(fin): shutil.rmtree(fin)
    sh([KPY, "-I", os.path.join(HERE, "finish_v3.py"), "final", j("poured.kicad_pcb"), j("vias.json"), j("labels.json"), fin, j("full.json")])
    pro = json.load(open(j("v3_routed.kicad_pro"))); pro["meta"]["filename"] = NAME + ".kicad_pro"
    json.dump(pro, open(os.path.join(fin, NAME + ".kicad_pro"), "w"), indent=2)
    shutil.copytree(os.path.join(w, "HeliSR.pretty"), os.path.join(fin, "HeliSR.pretty"))
    open(os.path.join(fin, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "HeliSR")(type "KiCad")(uri "${KIPRJMOD}/HeliSR.pretty")(options "")(descr "HeliSR project footprints"))\n)\n')
    return fin, drc(os.path.join(fin, NAME + ".kicad_pcb"))
full = []
dropped = []
for attempt in range(5):
    fin, rep = final(full)
    starved, dangling = [], []
    for v in rep["violations"]:
        if v["type"] == "starved_thermal":
            for i in v["items"]:
                d = i["description"].split()
                if d[0] in ("Pad", "PTH"):          # "Pad 2 [GND] of SW1 on F.Cu" / "PTH pad 3 [GND] of J7"
                    k = d.index("of"); starved.append([d[k + 1], d[2 if d[0] == "PTH" else 1]])
        if v["type"] == "via_dangling":             # a stitching via whose islands both got removed: it joins nothing
            for i in v["items"]:
                if i["description"].startswith("Via [GND]"): dangling.append((round(i["pos"]["x"], 2), round(i["pos"]["y"], 2)))
    new = [s for s in starved if s not in full]
    if dangling:
        vias = json.load(open(j("vias.json")))
        keep = [p for p in vias if (round(p[0], 2), round(p[1], 2)) not in dangling]
        dropped += [p for p in vias if p not in keep]
        json.dump(keep, open(j("vias.json"), "w"))
    if not new and not dangling: break
    full += new
print("stitching vias dropped as dangling:", dropped)
types = {}
for v in rep["violations"]: types[v["type"]] = types.get(v["type"], 0) + 1
print("solid-connected GND pads:", full)
print("DRC:", len(rep["unconnected_items"]), "unconnected,", types or "no violations")
