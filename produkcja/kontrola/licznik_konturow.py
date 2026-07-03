# -*- coding: utf-8 -*-
"""Licznik ZAMKNIETYCH KONTUROW WEWNETRZNYCH (otwory+sloty+wyciecia).
Topologicznie: petle = liczba cyklomatyczna grafu krawedzi (E-V+C) + samozamkniete
(CIRCLE/ELLIPSE/zamknieta LWPOLYLINE/SPLINE). Wewnetrzne = petle - 1 (kontur zewn.)."""
import ezdxf

def _endpoints(e):
    t = e.dxftype()
    if t == "LINE": return [e.dxf.start, e.dxf.end]
    if t == "ARC": return [e.start_point, e.end_point]
    if t == "SPLINE" and not e.closed:
        pts = list(e.control_points)
        return [pts[0], pts[-1]] if pts else []
    return []

def count_interior_contours(msp, layers=None):
    edges = []          # (kluczA, kluczB)
    isolated = 0        # samozamkniete petle
    def key(p): return (round(p[0], 1), round(p[1], 1))
    for e in msp:
        if layers is not None and e.dxf.layer not in layers: continue
        if e.dxf.layer == "GIECIE" or e.dxf.color == 6: continue   # linie giecia to nie kontur
        t = e.dxftype()
        if t in ("CIRCLE", "ELLIPSE"):
            isolated += 1
        elif t in ("LWPOLYLINE", "POLYLINE"):
            closed = getattr(e, "closed", False) or (e.dxf.hasattr("flags") and e.dxf.flags & 1)
            try: pts = list(e.get_points("xy")) if t == "LWPOLYLINE" else [v.dxf.location for v in e.vertices]
            except Exception: pts = []
            if closed and len(pts) >= 3:
                isolated += 1
            else:
                for a, b in zip(pts, pts[1:]): edges.append((key(a), key(b)))
        elif t == "SPLINE" and e.closed:
            isolated += 1
        else:
            ep = _endpoints(e)
            if len(ep) == 2: edges.append((key(ep[0]), key(ep[1])))
    # graf: V, E, C (union-find)
    nodes = set()
    for a, b in edges: nodes.add(a); nodes.add(b)
    parent = {n: n for n in nodes}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    C = len({find(n) for n in nodes}) if nodes else 0
    V = len(nodes); E = len(edges)
    cyclomatic = E - V + C          # niezalezne petle z krawedzi
    total_loops = cyclomatic + isolated
    interior = max(total_loops - 1, 0)   # minus kontur zewnetrzny
    return interior, dict(circle=isolated, cyclomatic=cyclomatic, loops=total_loops)

if __name__ == "__main__":
    import sys
    from pathlib import Path
    DEL = Path(__file__).resolve().parent / "wyniki_rysowanie" / "_DXF_gotowe"
    tgt = sys.argv[1:] or [p.stem for p in sorted(DEL.glob("*.dxf"))]
    for nm in tgt:
        f = DEL / (nm + ".dxf")
        if not f.exists(): continue
        d = ezdxf.readfile(f)
        n, det = count_interior_contours(d.modelspace())
        print(f"{nm:26} kontury_wewn={n:3}  (okregi={det['circle']}, petle-z-krawedzi={det['cyclomatic']})")
