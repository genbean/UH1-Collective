# Does the AS5600 sensor board's socket, with the jumper's plug in it, fit in the Huey head Rev 5? The board sits chip
# down in the pod's grooves, so J1 stands up from its back into the pod's open top. Models a block over J1's footprint
# (7.9 mm square, so any way round) for the header and the plug, PLUG_H tall, and the lead above it, LEAD_W square, up
# to LEAD_TOP over the board; then prints its overlap with every part in Head/check_r5.py's model.
# Runs with the repo's .venv python. usage: check_head_fit.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "Head"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "Head", "Hat"))
import huey_head_r5 as h
import check_r5 as c
import hat4_r5

PLUG_H, LEAD_W, LEAD_TOP = 7.0, 5.0, 20.0     # header + mated plug (JST SH: under 7 mm), the lead's bundle, how far up
J1 = 7.9                                       # J1's footprint, its longer side

top = h.BOARD_Z + 1.6                          # the board's back, facing up
plug = h.zprism(h.module_xs(-J1 / 2, J1 / 2, -J1 / 2, J1 / 2), top, top + PLUG_H)
lead = h.zprism(h.module_xs(-LEAD_W / 2, LEAD_W / 2, -LEAD_W / 2, LEAD_W / 2), top + PLUG_H, top + LEAD_TOP)

body = h.body_r5()
lp, _ = hat4_r5.lower_panel()
up, _ = h.upper_panel()
parts = {"body": body, "lower_panel": h.tilt(lp), "upper_panel": h.tilt(up), "trigger": h.trigger()}
sw = {"GOV": c.toggle_body(*h.GOV, 0.0), "LDG_EXT": c.toggle_body(*h.LDG_EXT, 0.0),
      "STOP_REL": h.ycyl(*h.STOP_REL, 12.0, h.PLUG_H, 16.0), "SL": c.toggle_body(*h.SL, h.UY),
      "LDG_ON": c.toggle_body(*h.LDG_ON, h.UY)}
parts.update({k: h.tilt(v) for k, v in sw.items()})
parts.update({k: h.tilt(v) for k, v in c.helisr().items()})
print(f"board back at z {top:.2f}, pod top (BOSS_TOP) at {h.BOSS_TOP:.2f}: {h.BOSS_TOP - top:.2f} mm of pod above the board")
bad = 0
for name, m in parts.items():
    for what, solid in (("socket+plug", plug), ("lead", lead)):
        v = (m ^ solid).volume()
        if v > c.TOL:
            bad += 1; print(f"OVERLAP {what} with {name}: {v:.2f} mm3")
# nearest distance from the socket+plug to each switch, by growing it until it touches
for name in ("GOV", "LDG_EXT", "STOP_REL", "body"):
    for g in (0.5, 1.0, 2.0, 3.0, 5.0):
        grown = h.zprism(h.module_xs(-J1 / 2 - g, J1 / 2 + g, -J1 / 2 - g, J1 / 2 + g), top + 0.01, top + PLUG_H + g)
        if (parts[name] ^ grown).volume() > c.TOL:
            print(f"  socket+plug comes within {g} mm of {name}"); break
    else:
        print(f"  socket+plug is more than 5 mm from {name}")
print("all clear" if not bad else f"{bad} overlap(s)")
