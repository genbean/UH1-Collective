# Finish a routed Rev 4.0 board end to end: pours, GND stitching, rules, silk labels, DRC.
# Every step runs in KiCad 9's python (the stitching and label searches use its numpy and PIL).
# usage: finish_all_v4.py <run dir with v4_routed.kicad_pcb> <out dir>
import json, os, shutil, subprocess, sys

run, out = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
KBIN = os.environ.get("KICAD9_BIN") or next(p for p in (r"C:/Program Files/KiCad/9.0/bin",
       os.path.expandvars(r"%LOCALAPPDATA%/Programs/KiCad/9.0/bin")) if os.path.exists(p))
KPY, KCLI = os.path.join(KBIN, "python.exe"), os.path.join(KBIN, "kicad-cli.exe")
NAME = "HeliSR_Rev4.0"

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
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
for f in ("v4_routed.kicad_pcb", "v4_routed.kicad_pro", "v4_layout.json"): shutil.copy(os.path.join(run, f), w)
shutil.copytree(os.path.join(run, "HeliSR.pretty"), os.path.join(w, "HeliSR.pretty"))
j = lambda *p: os.path.join(w, *p)
print(sh([KPY, "-I", os.path.join(HERE, "finish_v4.py"), "pour", j("v4_routed.kicad_pcb"), j("v4_layout.json"), j("poured.kicad_pcb")]))
shutil.copy(j("v4_routed.kicad_pro"), j("poured.kicad_pro"))
# GND stitching first, so every pour island that can be tied to ground gets its via; the labels then go round them.
print(sh([KPY, "-I", os.path.join(HERE, "stitch_v4.py"), j("poured.kicad_pcb"), j("vias.json"), "5.0"]))
sh([KPY, "-I", "-c", "import json,sys,pcbnew;b=pcbnew.LoadBoard(sys.argv[1]);mm=pcbnew.ToMM;"
    "json.dump([{'text':d.GetText(),'new_text':d.GetText(),'side':'F' if d.GetLayer()==pcbnew.F_SilkS else 'B',"
    "'x':mm(d.GetPosition().x),'y':mm(d.GetPosition().y),'size':1.0} for d in b.GetDrawings() if d.GetClass()=='PCB_TEXT'],"
    "open(sys.argv[2],'w'))", j("poured.kicad_pcb"), j("labels0.json")])

def final(full):
    json.dump(full, open(j("full.json"), "w"))
    tmp = j("final")
    if os.path.isdir(tmp): shutil.rmtree(tmp)
    sh([KPY, "-I", os.path.join(HERE, "finish_v4.py"), "final", j("poured.kicad_pcb"), j("vias.json"), j("labels0.json"), tmp, j("full.json")])
    fin = os.path.join(out, "board")
    if os.path.isdir(fin): shutil.rmtree(fin)
    os.makedirs(fin)
    print(sh([KPY, "-I", os.path.join(HERE, "silk_fix_v4.py"), os.path.join(tmp, NAME + ".kicad_pcb"),
              os.path.join(fin, NAME + ".kicad_pcb"), j("silk_preview.png")]).splitlines()[-1])
    shutil.copy(os.path.join(tmp, NAME + ".kicad_dru"), fin)
    pro = json.load(open(j("v4_routed.kicad_pro"))); pro["meta"]["filename"] = NAME + ".kicad_pro"
    json.dump(pro, open(os.path.join(fin, NAME + ".kicad_pro"), "w"), indent=2)
    shutil.copytree(os.path.join(w, "HeliSR.pretty"), os.path.join(fin, "HeliSR.pretty"))
    open(os.path.join(fin, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "HeliSR")(type "KiCad")(uri "${KIPRJMOD}/HeliSR.pretty")(options "")(descr "HeliSR project footprints"))\n)\n')
    return fin, drc(os.path.join(fin, NAME + ".kicad_pcb"))
full, dropped = [], []
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
