# Write the fab and preview outputs for a finished board (Rev 2.0 on; this copy for Rev 4.0): <name>_Gerbers.zip (Gerbers with Protel
# extensions, X2 attributes and a job file, plus separate PTH / NPTH Excellon drill files in mm), and the two board
# renders, <name>_Top.png and <name>_Bottom_mirrored.png. The renders are KiCad SVG plots in the default layer
# colours (top: Edge.Cuts, F.Cu, F.Mask, F.Silkscreen; bottom, mirrored: Edge.Cuts, B.Cu, B.Mask, B.Silkscreen) drawn
# 1460 px wide with a 20 px white border, rasterised by Microsoft Edge in headless mode.
# Runs under any Python 3 (standard library only). usage: export_v4.py <board.kicad_pcb> <out dir>
import os, shutil, subprocess, sys, tempfile, time, zipfile

board, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
NAME = os.path.splitext(os.path.basename(board))[0]
KBIN = os.environ.get("KICAD9_BIN") or next(p for p in (r"C:/Program Files/KiCad/9.0/bin",
       os.path.expandvars(r"%LOCALAPPDATA%/Programs/KiCad/9.0/bin")) if os.path.exists(p))
KCLI = os.path.join(KBIN, "kicad-cli.exe")
EDGE = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
VIEWS = {"Top": "Edge.Cuts,F.Cu,F.Mask,F.Silkscreen", "Bottom_mirrored": "Edge.Cuts,B.Cu,B.Mask,B.Silkscreen"}

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(f"FAILED {args}\n{r.stdout[-800:]}{r.stderr[-800:]}")
def wait_for(path, timeout=60):                    # msedge returns at once; a child process writes the PNG
    last, t0 = -1, time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(path):
            n = os.path.getsize(path)
            if n > 0 and n == last: return
            last = n
        time.sleep(0.5)
    raise SystemExit("timed out waiting for " + path)

os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp(prefix="export_v4_")
try:
    g = os.path.join(tmp, "gerbers"); os.makedirs(g)
    sh([KCLI, "pcb", "export", "gerbers", "--layers", LAYERS, "-o", g + os.sep, board])
    sh([KCLI, "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-zeros-format", "decimal", "--excellon-separate-th", "-o", g + os.sep, board])
    zp = os.path.join(out, NAME + "_Gerbers.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
    print("wrote", zp, sorted(os.listdir(g)))
    for view, layers in VIEWS.items():
        svg, html, png = (os.path.join(tmp, view + e) for e in (".svg", ".html", ".png"))
        sh([KCLI, "pcb", "export", "svg", "--mode-single", "--layers", layers, "--page-size-mode", "2",
            "--exclude-drawing-sheet", "--drill-shape-opt", "2", "-o", svg, board] + (["--mirror"] if view != "Top" else []))
        open(html, "w").write('<!doctype html><html><body style="margin:0;background:#fff"><img src="%s.svg" '
                              'style="display:block;width:1460px;height:1177px;margin:20px"></body></html>' % view)
        fwd = lambda p: p.replace("\\", "/")
        subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--user-data-dir=" + fwd(os.path.join(tmp, "edge")), "--window-size=1500,1217",
                        "--default-background-color=ffffffff", "--screenshot=" + fwd(png), "file:///" + fwd(html)],
                       capture_output=True)
        wait_for(png)
        dst = os.path.join(out, f"{NAME}_{view}.png"); shutil.copy(png, dst); print("wrote", dst)
finally:
    time.sleep(2)                                    # let Edge's background processes release the profile
    shutil.rmtree(tmp, ignore_errors=True)
