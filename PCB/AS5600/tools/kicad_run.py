# Run a script with KiCad 9's python, or kicad-cli, from any python (e.g. the repo's .venv), so commands stay in the repo.
# usage: kicad_run.py py <script.py> [args...]   |   kicad_run.py cli [kicad-cli args...]
import os, subprocess, sys

KBIN = os.environ.get("KICAD9_BIN") or next(p for p in (r"C:/Program Files/KiCad/9.0/bin",
       os.path.expandvars(r"%LOCALAPPDATA%/Programs/KiCad/9.0/bin")) if os.path.exists(p))
KPY, KCLI = os.path.join(KBIN, "python.exe"), os.path.join(KBIN, "kicad-cli.exe")

if __name__ == "__main__":
    kind, rest = sys.argv[1], sys.argv[2:]
    cmd = [KPY, "-I"] + rest if kind == "py" else [KCLI] + rest
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = [l for l in (r.stdout + r.stderr).splitlines() if "swig" not in l and "image handler" not in l]
    print("\n".join(out))
    sys.exit(r.returncode)
