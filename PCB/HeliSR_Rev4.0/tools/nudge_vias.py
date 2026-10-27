# Move routed vias by small amounts (with the track ends attached to them), e.g. to open up hole-to-hole spacing the
# router left at the minimum. Run with KiCad 9's python.
# usage: nudge_vias.py <in.kicad_pcb> <out.kicad_pcb> '<json list of [net, x, y, dx, dy]>'
import json, sys
import pcbnew

src, dst, moves = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
b = pcbnew.LoadBoard(src)
MM, mm = pcbnew.FromMM, pcbnew.ToMM
tracks = list(b.GetTracks())
for net, x, y, dx, dy in moves:
    vias = [t for t in tracks if t.GetClass() == "PCB_VIA" and t.GetNetname() == net
            and abs(mm(t.GetPosition().x) - x) < 0.01 and abs(mm(t.GetPosition().y) - y) < 0.01]
    assert len(vias) == 1, (net, x, y, len(vias))
    v = vias[0]
    old = v.GetPosition()
    new = pcbnew.VECTOR2I(old.x + MM(dx), old.y + MM(dy))
    n = 0
    for t in tracks:
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        if t.GetStart() == old: t.SetStart(new); n += 1
        if t.GetEnd() == old: t.SetEnd(new); n += 1
    v.SetPosition(new)
    print(f"{net} via ({x}, {y}) moved by ({dx}, {dy}); {n} track ends followed")
b.Save(dst)
