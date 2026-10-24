# Generate, autoroute (Freerouting), import and DRC a set of Rev 3.0 placement variants; report a score for each.
# usage: route_v3.py <work dir> <variants.json> <freerouting.jar> <java.exe> [parallel]
import json, os, re, shutil, subprocess, sys, concurrent.futures as cf

work, vfile, JAR, JAVA = sys.argv[1:5]
PAR = int(sys.argv[5]) if len(sys.argv) > 5 else 4
KPY = r"C:/Program Files/KiCad/9.0/bin/python.exe"
KCLI = r"C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(work, "HeliSR.pretty")

def power_class(dsn_in, dsn_out, pwr_w_um, clr_um=200):
    s = open(dsn_in).read()
    m = re.search(r"\(class kicad_default (.*?)\(circuit", s, re.S)
    names = m.group(1).split()
    rest = [n for n in names if n not in ("GND", "VCC")]
    s = s[:m.start(1)] + " ".join(rest) + "\n      " + s[m.end(1):]
    end = s.index("\n    )\n", m.start()) + len("\n    )\n")         # end of the kicad_default class block
    block = ("    (class power GND VCC\n      (circuit\n        (use_via \"Via[0-1]_600:300_um\")\n      )\n"
             f"      (rule\n        (width {pwr_w_um})\n        (clearance {clr_um})\n      )\n    )\n")
    s = s[:end] + block + s[end:]
    open(dsn_out, "w").write(s)

def run(v):
    tag = v["tag"]; d = os.path.join(work, tag)
    if os.path.isdir(d): shutil.rmtree(d)
    os.makedirs(d); shutil.copytree(LIB, os.path.join(d, "HeliSR.pretty"))
    json.dump(v, open(os.path.join(d, "params.json"), "w"))
    pcb, dsn = os.path.join(d, "v3.kicad_pcb"), os.path.join(d, "v3.dsn")
    g = subprocess.run([KPY, "-I", os.path.join(HERE, "gen_v3.py"), pcb, dsn, os.path.join(d, "params.json")],
                       capture_output=True, text=True, timeout=300)
    if not os.path.exists(dsn): return {**v, "error": "gen: " + g.stdout[-400:] + g.stderr[-400:]}
    power_class(dsn, os.path.join(d, "v3_r.dsn"), int(v.get("pwr_w", 0.3) * 1000), int(round(v.get("clear", 0.2) * 1000)))
    ses = os.path.join(d, "v3.ses")
    try:
        r = subprocess.run([JAVA, "-Djava.awt.headless=true", "-jar", JAR, "-de", os.path.join(d, "v3_r.dsn"), "-do", ses,
                            "-mp", str(v.get("passes", 100)), "-mt", "1", "--gui.enabled=false"],
                           capture_output=True, text=True, timeout=v.get("timeout", 900))
        open(os.path.join(d, "freerouting.log"), "w").write(r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return {**v, "error": "freerouting timeout"}
    if not os.path.exists(ses): return {**v, "error": "no session"}
    routed = os.path.join(d, "v3_routed.kicad_pcb")
    subprocess.run([KPY, "-I", os.path.join(HERE, "imp_v2.py"), pcb, ses, routed], capture_output=True, text=True, timeout=300)
    if v.get("nudges"):                         # small via moves recorded for this routing (see nudge_vias.py)
        raw = os.path.join(d, "v3_routed_freerouting.kicad_pcb"); shutil.copy(routed, raw)
        subprocess.run([KPY, "-I", os.path.join(HERE, "nudge_vias.py"), raw, routed, json.dumps(v["nudges"])],
                       capture_output=True, text=True, timeout=300)
    rpt = os.path.join(d, "drc.json")
    subprocess.run([KCLI, "pcb", "drc", "--format", "json", "--severity-error", "-o", rpt, routed], capture_output=True, timeout=300)
    j = json.load(open(rpt))
    types = {}
    for x in j["violations"]: types[x["type"]] = types.get(x["type"], 0) + 1
    st = subprocess.run([KPY, "-I", "-c",
        "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);mm=pcbnew.ToMM;"
        "L=sum(mm(t.GetLength()) for t in b.GetTracks() if t.GetClass()=='PCB_TRACK');"
        "V=sum(1 for t in b.GetTracks() if t.GetClass()=='PCB_VIA');print('STAT',round(L,1),V)", routed],
        capture_output=True, text=True, timeout=120).stdout
    m = re.search(r"STAT ([\d.]+) (\d+)", st)
    return {**v, "unconnected": len(j.get("unconnected_items", [])), "violations": types,
            "length": float(m.group(1)) if m else None, "vias": int(m.group(2)) if m else None}

variants = json.load(open(vfile))
with cf.ThreadPoolExecutor(PAR) as ex:
    for r in ex.map(run, variants):
        print(json.dumps(r), flush=True)
        with open(os.path.join(work, "results.jsonl"), "a") as f: f.write(json.dumps(r) + "\n")
