# -*- coding: utf-8 -*-
"""
FLAGER FAZOWANIA (chamfer) - kontrola/oznaczanie. Etap 4, wpiety 2026-07-07.

Fazowanie na rysunku = linia w kolorze geometrii, ROWNOLEGLA do krawedzi konturu
zewnetrznego, blisko niej (1-10 mm), o dlugosci ~= dlugosc tej krawedzi, tworzaca
T-zlacza z bokami konturu. Sygnatura geometryczna (deterministyczna):

    OBA konce linii leza NA pierscieniu zewnetrznym czesci (T-zlacza),
    a SRODEK linii lezy scisle WEWNATRZ (w odleglosci ~d od pierscienia).

Odroznia fazowanie od: otworu/slotu (zamknieta petla, konce nie na obrysie),
dospawienia (prostokat wewnatrz, konce nie na obrysie), linii giecia (kolor 6 /
warstwa GIECIE - odfiltrowane), dubli konturu (srodek NA pierscieniu).

FLAGER: wskazuje i OZNACZA (technologia=fazowanie, jawny powod), nie decyduje o
statusie w gore (zasada 5). Decyzja operatora: pozycja zostaje 🟡 do potwierdzenia.

Obsluga wg operatora (24_0417 / 38_1847, 2026-07-07): linie fazowania ZOSTAWIC jak
sa, ale POKOLOROWAC na ZOLTO (kolor 2) + KOMENTARZ w wykazie (technologia+uwagi).
Laser jej nie usuwa - operator widzi ze to faza, nie ciecie.

Rdzen zweryfikowany (fable-advisor + niezalezny pomiar Opus): 3 pozytywy
(SL10585238_p2, SL10585242_p2, SL10583062_p2) wykryte, 0 falszywych na 260 DXF.
Golden: testy/golden/fazowanie_linia_przy_krawedzi/. Po zmianie: python testy/test_fazowanie.py.
"""
import math

import ezdxf
import shapely
from ezdxf import path as ezpath
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union, polygonize

# ---------------------------------------------------------------- parametry
D_MIN = 1.0          # mm - minimalny odstep linii fazowania od krawedzi
D_MAX = 10.0         # mm - maksymalny odstep (typowo ~5 mm)
ANGLE_TOL_DEG = 2.0  # rownoleglosc linia vs krawedz
TOL_RING = 0.05      # mm - "koniec lezy na pierscieniu"
MIN_LEN = 5.0        # mm - min dlugosc kandydata
MIN_EDGE_LEN = 5.0   # mm - min dlugosc krawedzi referencyjnej
RATIO_MIN, RATIO_MAX = 0.6, 1.4      # dlugosc linii / dlugosc krawedzi
RATIO_GOOD = (0.85, 1.15)            # zakres "pewny" (bonus pewnosci)
FLATTEN_SAGITTA = 0.05               # dyskretyzacja lukow
SNAP_GRID = 0.001    # mm - snapping wezlow przed polygonize (float-drift lukow bez
                     #      tego nie skleja sie w GEOS; cechy >=3mm -> topologia bez zmian)
ZOLTY = 2            # kolor ACI zolty (znacznik fazowania w wyniku)


def _iter_entities(src):
    if hasattr(src, "modelspace"):
        return list(src.modelspace())
    return list(src)


def _is_bend(e):
    try:
        if int(e.dxf.color) == 6:
            return True
    except Exception:
        pass
    lay = str(getattr(e.dxf, "layer", "")).upper()
    return "GIECIE" in lay or "BEND" in lay


def _entity_linestring(e):
    t = e.dxftype()
    if t not in ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE",
                 "SPLINE", "ELLIPSE"):
        return None
    try:
        p = ezpath.make_path(e)
        pts = [(v.x, v.y) for v in p.flattening(FLATTEN_SAGITTA)]
    except Exception:
        return None
    if len(pts) < 2:
        return None
    ls = LineString(pts)
    if ls.length < 1e-6:
        return None
    return ls


def _ang_of(p0, p1):
    return math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0


def _ang_diff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def _merge_ring_edges(ring, angle_tol=0.8, min_edge_len=MIN_EDGE_LEN):
    """Pierscien -> lista maksymalnych PROSTYCH krawedzi [(P0,P1,dlugosc,kat)]."""
    pts = list(ring.coords)[:-1]
    n = len(pts)
    if n < 3:
        return []
    angs = [_ang_of(pts[i], pts[(i + 1) % n]) for i in range(n)]
    start = 0
    for i in range(n):
        if _ang_diff(angs[i - 1], angs[i]) > angle_tol:
            start = i
            break
    edges = []
    run_start = start
    run_ang = angs[start]
    for k in range(1, n + 1):
        i = (start + k) % n
        if k == n or _ang_diff(angs[i], run_ang) > angle_tol:
            p0 = pts[run_start]
            p1 = pts[i]
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if L >= min_edge_len:
                edges.append((p0, p1, L, _ang_of(p0, p1)))
            if k < n:
                run_start = i
                run_ang = angs[i]
    return edges


def _edge_frame(p0, p1):
    ux = p1[0] - p0[0]
    uy = p1[1] - p0[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L

    def to_frame(p):
        dx, dy = p[0] - p0[0], p[1] - p0[1]
        return (dx * ux + dy * uy, -dx * uy + dy * ux)

    return to_frame, L


def wykryj_fazowanie(entities_lub_msp,
                     d_min=D_MIN, d_max=D_MAX,
                     angle_tol=ANGLE_TOL_DEG, tol_ring=TOL_RING,
                     min_len=MIN_LEN):
    """Zwraca liste kandydatow fazowania:
    [{edge, dystans_mm, dlugosc_mm, dlugosc_krawedzi_mm, ratio,
      t_zlacza:[(x,y),(x,y)], pas_pusty, pewnosc}]. Pusta = brak.
    NIE zmienia geometrii ani statusu w gore (flager)."""
    ents = [e for e in _iter_entities(entities_lub_msp) if not _is_bend(e)]

    geoms = []
    for e in ents:
        ls = _entity_linestring(e)
        if ls is not None:
            geoms.append((e, ls))
    if not geoms:
        return []

    merged = unary_union([g for _, g in geoms])
    merged = shapely.set_precision(merged, SNAP_GRID)
    faces = list(polygonize(merged))
    if not faces:
        return []
    solid = unary_union(faces)
    if isinstance(solid, MultiPolygon):
        solid = max(solid.geoms, key=lambda p: p.area)
    if not isinstance(solid, Polygon) or solid.area <= 0:
        return []
    ring = solid.exterior
    edges = _merge_ring_edges(ring)

    out = []
    for e, ls in geoms:
        if e.dxftype() != "LINE":
            continue  # znacznik fazowania = prosta linia
        (x0, y0), (x1, y1) = ls.coords[0], ls.coords[-1]
        L_line = ls.length
        if L_line < min_len:
            continue
        mid = ls.interpolate(0.5, normalized=True)
        if mid.distance(ring) <= tol_ring:
            continue
        if not solid.buffer(tol_ring).contains(mid):
            continue
        if Point(x0, y0).distance(ring) > tol_ring:
            continue
        if Point(x1, y1).distance(ring) > tol_ring:
            continue
        a_line = _ang_of((x0, y0), (x1, y1))

        best = None
        for (p0, p1, L_edge, a_edge) in edges:
            if _ang_diff(a_line, a_edge) > angle_tol:
                continue
            to_frame, _ = _edge_frame(p0, p1)
            s0, t0 = to_frame((x0, y0))
            s1, t1 = to_frame((x1, y1))
            d = (abs(t0) + abs(t1)) / 2.0
            if not (d_min <= d <= d_max):
                continue
            if abs(abs(t0) - abs(t1)) > 0.5:
                continue
            lo, hi = min(s0, s1), max(s0, s1)
            overlap = min(hi, L_edge) - max(lo, 0.0)
            if overlap < 0.5 * L_edge:
                continue
            ratio = L_line / L_edge
            if not (RATIO_MIN <= ratio <= RATIO_MAX):
                continue
            if best is None or d < best[0]:
                best = (d, (p0, p1), L_edge, ratio, overlap)
        if best is None:
            continue
        d, edge_pts, L_edge, ratio, overlap = best

        pas_pusty = False
        ex = (edge_pts[0][0] + edge_pts[1][0]) / 2.0
        ey = (edge_pts[0][1] + edge_pts[1][1]) / 2.0
        vx, vy = ex - mid.x, ey - mid.y
        vn = math.hypot(vx, vy) or 1.0
        probe = Point(mid.x + vx / vn * d / 2.0, mid.y + vy / vn * d / 2.0)
        for f in faces:
            if f.contains(probe):
                expected = d * L_line
                if 0.6 * expected <= f.area <= 1.4 * expected:
                    pas_pusty = True
                break

        pewnosc = 0.6
        if RATIO_GOOD[0] <= ratio <= RATIO_GOOD[1] and overlap >= 0.85 * L_edge:
            pewnosc += 0.2
        if pas_pusty:
            pewnosc += 0.2
        out.append({
            "edge": (tuple(edge_pts[0]), tuple(edge_pts[1])),
            "dystans_mm": round(d, 3),
            "dlugosc_mm": round(L_line, 3),
            "dlugosc_krawedzi_mm": round(L_edge, 3),
            "ratio": round(ratio, 3),
            "t_zlacza": [(round(x0, 3), round(y0, 3)),
                         (round(x1, 3), round(y1, 3))],
            "pas_pusty": pas_pusty,
            "pewnosc": round(min(pewnosc, 1.0), 2),
        })
    return out


def komentarz(kandydaci):
    """Zwiezly komentarz do wykazu z listy kandydatow (pusty gdy brak)."""
    if not kandydaci:
        return ""
    czesci = []
    for k in kandydaci:
        czesci.append(f"d={k['dystans_mm']:.0f}mm/L={k['dlugosc_mm']:.0f}mm")
    n = len(kandydaci)
    return f"fazowanie x{n} ({'; '.join(czesci)})" if n > 1 \
        else f"fazowanie ({czesci[0]})"


def _te_same_konce(e, t_zlacza, tol=0.05):
    """Czy LINE ma konce zgodne z para t_zlacza (dowolna kolejnosc)."""
    s, en = e.dxf.start, e.dxf.end
    a, b = t_zlacza
    pa = (abs(s.x - a[0]) <= tol and abs(s.y - a[1]) <= tol and
          abs(en.x - b[0]) <= tol and abs(en.y - b[1]) <= tol)
    pb = (abs(s.x - b[0]) <= tol and abs(s.y - b[1]) <= tol and
          abs(en.x - a[0]) <= tol and abs(en.y - a[1]) <= tol)
    return pa or pb


def oznacz_w_pliku(dxf_path):
    """Wykrywa fazowanie w wyjsciowym DXF, koloruje linie fazowania na ZOLTY (kol.2)
    i ZAPISUJE plik (tylko gdy cos zmieniono - idempotentne). Zwraca (n, komentarz).
    Geometria bez zmian (tylko kolor) - wymiar/kontury nietkniete. Bledy = GLOSNO,
    zwraca (0, '')."""
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"[FAZOWANIE] nie wczytano {dxf_path} ({e}) - pomijam (GLOSNO)")
        return (0, "")
    msp = doc.modelspace()
    kand = wykryj_fazowanie(msp)
    if not kand:
        return (0, "")
    zmieniono = 0
    for k in kand:
        for e in msp:
            if e.dxftype() != "LINE":
                continue
            if int(e.dxf.color) == ZOLTY:
                continue
            if _te_same_konce(e, k["t_zlacza"]):
                e.dxf.color = ZOLTY
                zmieniono += 1
    if zmieniono:
        try:
            doc.saveas(str(dxf_path))
        except Exception as e:
            print(f"[FAZOWANIE] nie zapisano {dxf_path} ({e}) (GLOSNO)")
    return (len(kand), komentarz(kand))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    n, kom = oznacz_w_pliku(argv[0])
    print(f"{argv[0]}: kandydatow fazowania = {n}" + (f" | {kom}" if kom else ""))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
