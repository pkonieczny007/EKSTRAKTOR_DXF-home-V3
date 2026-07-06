# -*- coding: utf-8 -*-
"""
PROTOTYP: flager FAZOWANIA (chamfer) dla EKSTRAKTOR_DXF V3.

Fazowanie na rysunku = linia w kolorze geometrii, ROWNOLEGLA do krawedzi konturu
zewnetrznego, blisko niej (1-10 mm), o dlugosci ~= dlugosc tej krawedzi, tworzaca
T-zlacza z bokami konturu. Sygnatura geometryczna (deterministyczna):

    OBA konce linii leza NA pierscieniu zewnetrznym czesci (T-zlacza),
    a SRODEK linii lezy scisle WEWNATRZ (w odleglosci ~d od pierscienia).

To odroznia fazowanie od:
  (a) otworu/slotu/cechy wewnetrznej -> zamknieta petla; konce NIE leza na obrysie,
  (b) dospawienia -> zamkniety prostokat WEWNATRZ, konce nie na obrysie, d >> 10 mm,
  (c) linii giecia -> kolor 6 / warstwa GIECIE, odfiltrowane na wejsciu,
  (d) linii konturu / dubli konturu -> srodek lezy NA pierscieniu.

Flager: WSKAZUJE (technologia=fazowanie, jawny powod), nie decyduje. Pozycja
zostaje zolta do potwierdzenia przez czlowieka.
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
TOL_RING = 0.05      # mm - "konzec lezy na pierscieniu" (spojne ze snappingiem 0.05)
MIN_LEN = 5.0        # mm - min dlugosc kandydata (cechy >= 3 mm, krawedzie dluzsze)
MIN_EDGE_LEN = 5.0   # mm - min dlugosc krawedzi referencyjnej
RATIO_MIN, RATIO_MAX = 0.6, 1.4      # dlugosc linii / dlugosc krawedzi (twardy zakres)
RATIO_GOOD = (0.85, 1.15)            # zakres "pewny" (bonus pewnosci)
FLATTEN_SAGITTA = 0.05               # dyskretyzacja lukow
SNAP_GRID = 0.001    # mm - snapping wezlow przed polygonize (float-drift lukow/luster
                     #      ~1e-15..1e-9 nie skleja sie w GEOS bez tego; cechy >=3mm,
                     #      wiec 0.001 mm nie zmienia topologii czesci)


def _iter_entities(src):
    """Przyjmij modelspace / dokument / liste encji."""
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
    """Encja -> shapely LineString (luki dyskretyzowane). None gdy nie-geometria."""
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
    """Pierscien (LinearRing) -> lista maksymalnych PROSTYCH krawedzi
    [(P0, P1, dlugosc, kat_deg)] po scaleniu kolinearnych segmentow.
    Luki (dyskretyzowane, kat segmentow ~11 deg) NIE sklejaja sie w krawedzie."""
    pts = list(ring.coords)[:-1]
    n = len(pts)
    if n < 3:
        return []
    angs = [_ang_of(pts[i], pts[(i + 1) % n]) for i in range(n)]
    # znajdz narozzik jako punkt startu (ring moze zaczynac sie w srodku krawedzi)
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
    """Uklad krawedzi: s wzdluz, t prostopadle. Zwraca funkcje world->(s,t)."""
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
      t_zlacza: [(x,y),(x,y)], pas_pusty: bool, pewnosc}]
    Pusta lista = brak fazowania. Flager - nie zmienia geometrii ani statusu w gore.
    """
    ents = [e for e in _iter_entities(entities_lub_msp) if not _is_bend(e)]

    geoms = []          # (encja, LineString)
    for e in ents:
        ls = _entity_linestring(e)
        if ls is not None:
            geoms.append((e, ls))
    if not geoms:
        return []

    # planarny podzial: polygonize po znodowaniu + snapping do siatki 0.001 mm
    # (bez snapu polygonize gubi sciany: koncowki dyskretyzowanych lukow maja
    #  float-drift ~1e-15 i GEOS nie skleja wezlow -> SL10585238_p2 dawal 1 sciane)
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
        # (1) srodek NIE lezy na pierscieniu (odpada kontur i jego duble)
        if mid.distance(ring) <= tol_ring:
            continue
        # (2) srodek wewnatrz czesci
        if not solid.buffer(tol_ring).contains(mid):
            continue
        # (3) T-zlacza: OBA konce na pierscieniu zewnetrznym
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
            if abs(abs(t0) - abs(t1)) > 0.5:     # nie-rownolegle w praktyce
                continue
            lo, hi = min(s0, s1), max(s0, s1)
            overlap = min(hi, L_edge) - max(lo, 0.0)
            if overlap < 0.5 * L_edge:           # linia musi lezec wzdluz krawedzi
                continue
            ratio = L_line / L_edge
            if not (RATIO_MIN <= ratio <= RATIO_MAX):
                continue
            if best is None or d < best[0]:
                best = (d, (p0, p1), L_edge, ratio, overlap)
        if best is None:
            continue
        d, edge_pts, L_edge, ratio, overlap = best

        # (4) pas miedzy linia a krawedzia = cienka scianka polygonize o polu ~ d*L
        pas_pusty = False
        # sonda: srodek linii przesuniety o d/2 w strone krawedzi
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


# ------------------------------------------------------------------ BONUS:
# korelacja z rzutem bocznym w ZRODLE (skos krawedzi obok widoku glownego).
# Zaimplementowane dla krawedzi POZIOMYCH/PIONOWYCH (oba goldeny poziome);
# uogolnienie na dowolny kat = TODO (obrot ukladu wg kierunku krawedzi).

def potwierdz_rzutem_bocznym(src_entities, view_bbox, layer,
                             t_line_src, t_edge_src, axis="y",
                             search_mult=3.0, tol=0.3):
    """Szuka w zrodle malego skosu (25-65 deg) na tej samej warstwie, obok bboxu
    widoku, ktorego zasieg wzdluz osi prostopadlej ~= [t_line_src, t_edge_src].
    axis='y': krawedz fazowana pozioma (skos w rzucie z boku, lewo/prawo).
    Zwraca dict z linia skosu albo None."""
    x0, y0, x1, y1 = view_bbox
    w = x1 - x0
    h = y1 - y0
    lo, hi = sorted((t_line_src, t_edge_src))
    for e in src_entities:
        if e.dxftype() != "LINE":
            continue
        if str(e.dxf.layer) != str(layer):
            continue
        sx, sy = e.dxf.start.x, e.dxf.start.y
        ex, ey = e.dxf.end.x, e.dxf.end.y
        ang = _ang_of((sx, sy), (ex, ey))
        if not (25.0 <= ang <= 65.0 or 115.0 <= ang <= 155.0):
            continue
        if axis == "y":
            # skos poza widokiem w X, w pasie Y widoku
            mx = (sx + ex) / 2.0
            if x0 - search_mult * w <= mx <= x1 + search_mult * w and not (x0 <= mx <= x1):
                pass
            elif not (x0 <= mx <= x1):
                continue
            else:
                continue
            tlo, thi = sorted((sy, ey))
        else:
            my = (sy + ey) / 2.0
            if y0 - search_mult * h <= my <= y1 + search_mult * h and not (y0 <= my <= y1):
                pass
            else:
                continue
            tlo, thi = sorted((sx, ex))
        if abs(tlo - lo) <= tol and abs(thi - hi) <= tol:
            return {"skos": ((round(sx, 3), round(sy, 3)),
                             (round(ex, 3), round(ey, 3))),
                    "kat_deg": round(ang, 1)}
    return None
