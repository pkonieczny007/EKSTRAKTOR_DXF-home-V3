# -*- coding: utf-8 -*-
"""Silnik W-C "region+warstwa" - V3 (zywy, importowalny, OCS-poprawny).

Root-fix na cechy ODSEPAROWANE (fasole/sloty/wyspy niepolaczone z konturem, ktore
klaster po sasiedztwie W-A/W-B gubi): bierzemy WSZYSTKIE encje TRYBU GEOMETRII w
bbox widoku (nie spojny klaster), transformujemy translate(-cx,-cy) @ scale(scale),
czyscimy, srodkujemy 1:1. Zwalidowany: odtwarza kompletnosc wzorcow golden
(SL10596945 fasola=4, SL40061302 sloty=3 na kolorze 2, SL10582608 owal=12).

Wlasnosci V3 (port z martwego skryptu V2):
  1. IMPORT: licznik konturow = bramka 5 (../kontrola/bilans_konturow.py,
     count_interior_contours_shapely) - poprzedni '_licznik_konturow' nie istnial w V3.
  2. ZERO efektow ubocznych na imporcie: bez mkdir, bez sciezek V2 'wyniki_rysowanie',
     bez czytania raportow. Czysty interfejs extract_region_warstwa(); IO tylko w save_result().
  3. FIX OCS (propozycja zaakceptowana 2026-07-05): srodek CIRCLE zawsze OCS->WCS
     (e.ocs().to_wcs(e.dxf.center)). Po lustrze w CAD okrag ma extrusion (0,0,-1) i
     surowy e.dxf.center lezy po ZLEJ stronie (x odwrocony) -> dedup wspolsrodkowych
     nie grupuje, fertzing (przelot+poglebienie, patrz kontekst/wiedza/) zostaje
     ZDUBLOWANY = dwa przepalenia na laser. Zmierzone (golden lustrzany_okrag_ocs):
     surowo (-100,50) vs WCS (100,50). ezdxf po transform() ZACHOWUJE extrusion, wiec
     dedup PO transformacji tez czyta OCS->WCS; okregi w wyniku normalizowane do WCS.
  4. WYBOR TRYBU GEOMETRII jak sweep.kontury_regionu_zrodla: geometria bywa na kolorze
     2/4/7 (SL40061302 = kolor 2, ZERO koloru 7 w bbox!). Kandydaci warstwa_geom/col7/
     col2/col4; czysty = n_outer==1; wybor: max interior (kompletnosc), remis -> najmniej
     dangles+cuts (smieci), remis -> priorytet. 'all' NIGDY (adnotacje/osie wpuscilyby
     smieci do WYNIKU na laser - zasada 1).
  5. GLOSNE logowanie (zasada 15): encje nieprzetransformowane -> info['transform_failed']
     + uwaga, nie znikaja po cichu.

Interfejs:
  extract_region_warstwa(src_msp, box, scale, is_pl=False, geom_layer=None)
      -> (ezdxf.Drawing, info_dict)
  save_result(doc, path)

CLI:
  python produkcja\\silniki\\region_warstwa.py <zrodlo.dxf> <x1> <y1> <x2> <y2> <scale> <out.dxf> [--pl]
"""
import io
import math
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb
from ezdxf import path as ezpath
from ezdxf.math import Matrix44

from shapely.geometry import LineString, Point, MultiLineString
from shapely.ops import unary_union, polygonize_full

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "kontrola"))
from bilans_konturow import count_interior_contours_shapely, EndpointSnapper  # noqa: E402

GEOM_TYPES = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE", "ELLIPSE"}
TRYBY_KOLOR = {"col7": 7, "col2": 2, "col4": 4}
PRIORYTET_TRYBOW = ("warstwa_geom", "col7", "col2", "col4")

# --- stale UWAGA-pass (otwory INNEGO koloru niz kontur; jak wd_dwutorowy) ---
AXIS_LT = {"CENTER", "CENTER2", "CENTERX2", "PHANTOM", "PHANTOM2", "MITTE"}
SAGITTA_UP = 0.1     # dyskretyzacja krzywych [mm papieru]
SNAP_UP = 0.1        # snap koncowek otwartych lancuchow [mm papieru]
TOL_ON_UP = 0.15     # przynaleznosc probki do petli wewnetrznej [mm papieru]


# ------------------------------ klocki pomocnicze ------------------------------

def _center(e):
    """Srodek bbox encji w WCS (ezdxf.bbox liczy przez path -> OCS-poprawne)."""
    try:
        return _bb.extents([e]).center
    except Exception:
        return None


def _in_bbox(c, x1, y1, x2, y2, m=1.0):
    return c is not None and x1 - m <= c.x <= x2 + m and y1 - m <= c.y <= y2 + m


def _effective_color(e, layer_colors):
    """256=BYLAYER -> kolor warstwy (geometria bywa BYLAYER na kolorowej warstwie)."""
    c = e.dxf.color
    return layer_colors.get(e.dxf.layer, 7) if c == 256 else c


def _wcs_center(circle):
    """Srodek CIRCLE w WCS. NIGDY surowy dxf.center: po lustrze CAD extrusion
    (0,0,-1) trzyma srodek w OCS (x odwrocony) - fix OCS, zmierzony."""
    return circle.ocs().to_wcs(circle.dxf.center)


def is_skos(e, tol_deg=5.0):
    """Linia gieca pod skosem = kat > tol od poziomu/pionu (nie-LINE: zostaw)."""
    if e.dxftype() != "LINE":
        return True
    dx = e.dxf.end.x - e.dxf.start.x
    dy = e.dxf.end.y - e.dxf.start.y
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return False
    ang = math.degrees(math.atan2(abs(dy), abs(dx)))
    return min(ang, abs(90 - ang)) > tol_deg


# --------------------------- wybor trybu geometrii -----------------------------

def zbierz_region(src_msp, box, margin=1.0):
    """Encje GEOM w bbox: (picked=[(e, kolor_eff)], bends=[e], layer_colors)."""
    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"bbox zdegenerowany: {box}")
    layer_colors = {}
    doc = getattr(src_msp, "doc", None)
    if doc is not None:
        for ly in doc.layers:
            layer_colors[ly.dxf.name] = ly.dxf.color

    picked, bends = [], []
    for e in src_msp:
        if e.dxftype() not in GEOM_TYPES:
            continue
        c = _center(e)
        if not _in_bbox(c, x1, y1, x2, y2, margin):
            continue
        ec = _effective_color(e, layer_colors)
        if ec == 6 or e.dxf.layer.upper() == "GIECIE":
            bends.append(e)
        else:
            picked.append((e, ec))
    return picked, bends, layer_colors


def detect_geom_layer(picked):
    """Warstwa geometrii: najczestsza warstwa encji koloru 7; brak koloru 7 ->
    fallback najczestsza warstwa w ogole (geometria na nietypowym kolorze -
    SL40061302 = kolor 2). Zwraca (layer|None, fallback:bool)."""
    cnt7 = Counter(e.dxf.layer for e, ec in picked if ec == 7)
    if cnt7:
        return cnt7.most_common(1)[0][0], False
    cnt = Counter(e.dxf.layer for e, _ in picked)
    if cnt:
        return cnt.most_common(1)[0][0], True
    return None, True


def wybierz_tryb(picked, geom_layer, sagitta=0.1, snap_tol=0.1):
    """Wybor listy encji geometrii sposrod trybow (warstwa_geom/col7/col2/col4).

    Czysty tryb = n_outer==1 (jedna czesc = jedna twarz zewnetrzna). Wybor:
    max interior (kompletnosc - otwory swiete), remis -> najmniej dangles+cuts
    (smieci to otwarte lancuchy), remis -> PRIORYTET_TRYBOW. Zaden czysty ->
    max interior ogolem + uwaga NIEPEWNE (obowiazkowe ogledziny).
    Zwraca (nazwa_trybu, encje, diag_dict).
    """
    listy = {}
    if geom_layer is not None:
        listy["warstwa_geom"] = [e for e, _ in picked if e.dxf.layer == geom_layer]
    for name, kol in TRYBY_KOLOR.items():
        listy[name] = [e for e, ec in picked if ec == kol]

    metryki, uwagi = {}, []
    for name in PRIORYTET_TRYBOW:
        ents = listy.get(name, [])
        if not ents:
            metryki[name] = dict(n_ents=0, interior=-1, outer=0, brud=0, flags=[])
            continue
        n, det = count_interior_contours_shapely(ents, sagitta=sagitta, snap_tol=snap_tol)
        metryki[name] = dict(n_ents=len(ents), interior=n, outer=det["outer"],
                             brud=det["dangles"] + det["cuts"] + det["invalid"],
                             circles_dedup=det["circles_dedup"], flags=det["flags"])

    czyste = [t for t in PRIORYTET_TRYBOW
              if metryki[t]["n_ents"] > 0 and metryki[t]["outer"] == 1]
    if czyste:
        best_interior = max(metryki[t]["interior"] for t in czyste)
        kandydaci = [t for t in czyste if metryki[t]["interior"] == best_interior]
        min_brud = min(metryki[t]["brud"] for t in kandydaci)
        kandydaci = [t for t in kandydaci if metryki[t]["brud"] == min_brud]
        tryb = next(t for t in PRIORYTET_TRYBOW if t in kandydaci)
        rozne = {t: metryki[t]["interior"] for t in czyste
                 if metryki[t]["interior"] not in (best_interior, 0, -1)}
        if rozne:
            uwagi.append(f"ROZBIEZNOSC trybow czystych: {tryb}={best_interior} vs "
                         f"{rozne} -> ogladac render (zasada 6)")
    else:
        dostepne = [t for t in PRIORYTET_TRYBOW if metryki[t]["n_ents"] > 0]
        if not dostepne:
            raise ValueError("brak encji geometrii w regionie (GLOSNO - sprawdz bbox/zrodlo)")
        best_interior = max(metryki[t]["interior"] for t in dostepne)
        tryb = next(t for t in dostepne if metryki[t]["interior"] == best_interior)
        uwagi.append(f"ZADEN tryb czysty (outer: "
                     f"{ {t: metryki[t]['outer'] for t in dostepne} }) -> tryb={tryb} "
                     f"NIEPEWNY, obowiazkowe ogledziny (zasada 6)")

    return tryb, listy[tryb], dict(metryki=metryki, uwagi=uwagi)


# ------------------------------ UWAGA-pass (W-C) -------------------------------
# Otwory narysowane INNYM kolorem niz kontur wypadaja z jednego trybu W-C
# (SL40062903_p1: kontur kol.2, otwory kol.4). UWAGA-pass DOKLADA (ADDITIVE)
# zamkniete petle innego koloru SCISLE wewnatrz obrysu bazowego. Status moze przez
# to tylko SPASC na 🟡 (ogledziny 100%, zasada 6) - NIGDY nie podnosi (zasada 5).
# Port sprawdzonego rdzenia z W-D (wd_dwutorowy), test: testy/test_uwaga_pass.py.

def _up_is_axis_lt(e):
    return (e.dxf.linetype or "").upper() in AXIS_LT


def _up_flatten(e, sagitta=SAGITTA_UP):
    p = ezpath.make_path(e)
    return [(v.x, v.y) for v in p.flattening(distance=sagitta)]


def _up_subsample(pts, n=24):
    if len(pts) <= n:
        return pts
    step = max(1, len(pts) // n)
    out = pts[::step]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def _up_densify(pts, max_step=2.0):
    """Dogeszcza proste segmenty - inaczej LINE ma tylko KONCE (bug osi/chordu
    liczonych jako obrys, wd densify)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(d // max_step)
        for i in range(1, k + 1):
            t = i / (k + 1)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        out.append(b)
    return out


def _up_build_solid(base_ents, sagitta=SAGITTA_UP, snap=SNAP_UP):
    """Obrys bazowy (main solid) z geometrii wybranego trybu. Unia faces ->
    najwiekszy komponent (chord/fazowanie nie sciety). Zwraca shapely Polygon
    albo None (brak obrysu -> UWAGA-pass pominiety, nic nie dokladamy)."""
    open_chains, closed = [], []
    for e in base_ents:
        if e.dxftype() == "CIRCLE":
            c = e.ocs().to_wcs(e.dxf.center)
            r = float(e.dxf.radius)
            n = max(int(math.ceil(math.pi / math.acos(max(1.0 - sagitta / r, -1.0)))), 8) \
                if r > sagitta else 8
            ring = [(c.x + r * math.cos(2 * math.pi * i / n),
                     c.y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
            ring.append(ring[0])
            closed.append(ring)
            continue
        try:
            pts = _up_flatten(e, sagitta)
        except Exception:
            continue
        if len(pts) < 2:
            continue
        d = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        if d < 1e-9 or bool(getattr(e, "closed", False)):
            if d >= 1e-9:
                pts = pts + [pts[0]]
            if len(pts) >= 4:
                closed.append(pts)
        else:
            open_chains.append(pts)
    snapper = EndpointSnapper(snap)
    snapped = []
    for pts in open_chains:
        a = snapper.snap(pts[0])
        b = snapper.snap(pts[-1])
        snapped.append([a] + pts[1:-1] + [b])
    lines = [LineString(p) for p in snapped + closed if len(p) >= 2]
    if not lines:
        return None
    merged = unary_union(lines)
    polys, _d, _c, _i = polygonize_full([merged])
    faces = [g for g in polys.geoms if g.area > 0]
    if not faces:
        return None
    uni = unary_union(faces)
    comps = list(uni.geoms) if uni.geom_type == "MultiPolygon" else [uni]
    return max(comps, key=lambda p: p.area)


def _up_eff_color(e, layer_colors):
    c = e.dxf.color
    return layer_colors.get(e.dxf.layer, 7) if c == 256 else c


def uwaga_pass(base_ents, other_cands, layer_colors=None,
               tol_on=TOL_ON_UP, sagitta=SAGITTA_UP, snap=SNAP_UP):
    """UWAGA-pass ADDITIVE: zamkniete petle INNEGO koloru SCISLE wewnatrz obrysu
    bazowego (otwory innego koloru niz kontur).

    base_ents:   geometria wybranego trybu W-C (kontur + otwory tego koloru).
    other_cands: encje geometrii w regionie SPOZA base (juz bez gieca - zbierz_region
                 wydziela giecia). layer_colors: mapa warstwa->kolor (do raportu).
    Zwraca (add_circles, add_others, info):
       add_circles - CIRCLE do dolozenia (ida do dedupu wspolsrodkowych W-C),
       add_others  - niekolowe encje petli wewnetrznych do dolozenia,
       info: uwaga_pass=N, n_axis_skip, obce_kolory(set), solid(bool), powody[].
    """
    info = dict(uwaga_pass=0, n_axis_skip=0, obce_kolory=set(), solid=False, powody=[])
    main = _up_build_solid(base_ents, sagitta, snap)
    if main is None:
        info["powody"].append("brak obrysu bazowego (polygonize) -> UWAGA-pass pominiety")
        return [], [], info
    info["solid"] = True
    ext_buf = main.exterior.buffer(tol_on / 2)

    # (3) osie po linetype odpadaja PRZED polygonize
    cands = []
    for e in other_cands:
        if _up_is_axis_lt(e):
            info["n_axis_skip"] += 1
            continue
        cands.append(e)

    def _mark(e):
        if layer_colors is not None:
            info["obce_kolory"].add(_up_eff_color(e, layer_colors))
        else:
            info["obce_kolory"].add(e.dxf.color)

    # (4) CIRCLE innego koloru = zamkniety; srodek SCISLE w main, caly nie dotyka obrysu
    add_circles, noncirc = [], []
    for e in cands:
        if e.dxftype() == "CIRCLE":
            c = e.ocs().to_wcs(e.dxf.center)
            r = float(e.dxf.radius)
            p = Point(c.x, c.y)
            if main.contains(p) and not main.exterior.buffer(tol_on).intersects(p.buffer(r)):
                add_circles.append(e)
                _mark(e)
            continue
        noncirc.append(e)

    # (5) niekolowe: polygonize -> faces SCISLE wewnatrz main -> zachowaj encje na petlach
    flat, open_chains, closed = {}, [], []
    for e in noncirc:
        try:
            pts = _up_flatten(e, sagitta)
        except Exception:
            continue
        if len(pts) < 2:
            continue
        flat[id(e)] = pts
        d = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        if d < 1e-9 or bool(getattr(e, "closed", False)):
            if d >= 1e-9:
                pts = pts + [pts[0]]
            if len(pts) >= 4:
                closed.append(pts)
        else:
            open_chains.append(pts)
    snapper = EndpointSnapper(snap)
    snapped = []
    for pts in open_chains:
        a = snapper.snap(pts[0])
        b = snapper.snap(pts[-1])
        snapped.append([a] + pts[1:-1] + [b])
    lines = [LineString(p) for p in snapped + closed if len(p) >= 2]
    add_others = []
    if lines:
        merged = unary_union(lines)
        polys, _d, _c, _i = polygonize_full([merged])
        faces = [g for g in polys.geoms if g.area > 0]
        inner_rings = []
        for f in faces:
            fx = f.exterior
            if (main.contains(f.representative_point())
                    and not fx.within(ext_buf)
                    and not fx.intersects(main.exterior)):
                inner_rings.append(fx)
        acc = MultiLineString([LineString(r.coords) for r in inner_rings]) if inner_rings else None
        if acc is not None:
            for e in noncirc:
                pts = flat.get(id(e))
                if not pts:
                    continue
                smp = _up_subsample(_up_densify(pts))
                on = sum(1 for p in smp if acc.distance(Point(p)) <= tol_on)
                if on >= 0.6 * len(smp):
                    add_others.append(e)
                    _mark(e)

    info["uwaga_pass"] = len(add_circles) + len(add_others)
    return add_circles, add_others, info


# --------------------------------- ekstrakcja ----------------------------------

def extract_region_warstwa(src_msp, box, scale, is_pl=False, geom_layer=None,
                           margin=1.0, sagitta=0.1, snap_tol=0.1, dedup_tol=0.3):
    """Ekstrakcja region+warstwa jednego widoku -> (ezdxf.Drawing, info_dict).

    src_msp: modelspace ZRODLA; box=(x1,y1,x2,y2) w ukladzie zrodla; scale z raportu.
    is_pl: pozycja P/L (lustro) -> linie giecia zostaja wszystkie; inaczej tylko skos>5st.
    geom_layer: wymuszenie warstwy geometrii (None = auto: kolor 7 -> fallback).
    Bez zapisu na dysk - zapis przez save_result(). Wynik: 1:1, wysrodkowany (0,0),
    okregi po dedupie wspolsrodkowych (zostaje najmniejszy, srodek WCS), giecia na
    warstwie GIECIE kolor 6.
    """
    picked, bends_all, layer_colors = zbierz_region(src_msp, box, margin)
    if not picked:
        raise ValueError(f"brak geometrii w bbox {box} (GLOSNO - sprawdz bbox/zrodlo)")

    if geom_layer is None:
        det_layer, warstwa_fallback = detect_geom_layer(picked)
    else:
        det_layer, warstwa_fallback = geom_layer, False
    tryb, geom_ents, diag = wybierz_tryb(picked, det_layer, sagitta, snap_tol)
    uwagi = list(diag["uwagi"])
    if warstwa_fallback:
        uwagi.append(f"detect_geom_layer: zero koloru 7 w bbox -> fallback warstwa "
                     f"'{det_layer}' (geometria na nietypowym kolorze - SL40061302=kolor 2)")

    # UWAGA-pass: dolóż zamkniete petle INNEGO koloru SCISLE wewnatrz obrysu (otwory
    # narysowane innym kolorem niz kontur - jeden tryb W-C by je zgubil, SL40062903).
    geom_ids = {id(e) for e in geom_ents}
    other_cands = [e for e, _ec in picked if id(e) not in geom_ids]
    up_circles, up_others, up_info = uwaga_pass(geom_ents, other_cands, layer_colors)
    if up_info["uwaga_pass"]:
        uwagi.append(
            f"UWAGA-pass: dolozono {up_info['uwaga_pass']} petli INNEGO koloru "
            f"{sorted(up_info['obce_kolory'])} wewnatrz obrysu (otwory innego koloru "
            f"niz kontur) -> NIEPEWNE, ogledziny 100% (zasada 6), status moze tylko "
            f"SPASC do zoltego (zasada 5)")

    # giecia tylko z warstw wybranej geometrii + warstw GIECIE (osie kol.6 z
    # obcych warstw nie wchodza)
    warstwy_geom = {e.dxf.layer for e in geom_ents}
    bends = [e for e in bends_all
             if e.dxf.layer in warstwy_geom or e.dxf.layer.upper() == "GIECIE"]

    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    m = Matrix44.translate(-cx, -cy, 0) @ Matrix44.scale(scale, scale, 1)

    new = ezdxf.new(dxfversion="AC1021")
    new.layers.add("GIECIE", color=6)
    nmsp = new.modelspace()
    transform_failed = []

    # kontur + otwory (+ UWAGA-pass: okregi innego koloru ADDITIVE; wpadaja do tego
    # samego dedupu wspolsrodkowych ponizej, wiec fertzing innego koloru tez sie zredukuje)
    circles = []
    for e in list(geom_ents) + list(up_circles):
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception as ex:
            transform_failed.append(f"{e.dxftype()} handle={e.dxf.handle}: {ex}")
            continue
        ne.dxf.layer = "0"
        ne.dxf.color = 7
        if ne.dxftype() == "CIRCLE":
            circles.append(ne)
        else:
            nmsp.add_entity(ne)
    # niekolowe petle UWAGA-pass (sloty/fasole innego koloru wewnatrz obrysu)
    for e in up_others:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception as ex:
            transform_failed.append(f"UWAGA {e.dxftype()} handle={e.dxf.handle}: {ex}")
            continue
        ne.dxf.layer = "0"
        ne.dxf.color = 7
        nmsp.add_entity(ne)

    # dedup okregow wspolsrodkowych (fertzing: przelot+poglebienie -> NAJMNIEJSZY).
    # Srodek ZAWSZE OCS->WCS: ezdxf po transform() ZACHOWUJE extrusion (0,0,-1)
    # i center w OCS - surowe grupowanie by nie sparowalo (fix OCS).
    grupy = []  # [(wcs_center(Vec3), [circle,...])]
    for ne in circles:
        c = _wcs_center(ne)
        for gc, lst in grupy:
            if math.hypot(c.x - gc.x, c.y - gc.y) <= dedup_tol:
                lst.append(ne)
                break
        else:
            grupy.append((c, [ne]))
    circ_raw, circ_dedup = len(circles), len(grupy)
    for gc, lst in grupy:
        best = min(lst, key=lambda c: c.dxf.radius)
        best.dxf.center = (gc.x, gc.y, 0)     # normalizacja do WCS (okrag symetryczny)
        best.dxf.extrusion = (0, 0, 1)
        nmsp.add_entity(best)

    # linie giecia: P/L -> wszystkie; inaczej tylko skos>5st (proste osiowe out)
    bends_kept = 0
    for e in bends:
        if not (is_pl or is_skos(e)):
            continue
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception as ex:
            transform_failed.append(f"GIECIE {e.dxftype()} handle={e.dxf.handle}: {ex}")
            continue
        ne.dxf.layer = "GIECIE"
        ne.dxf.color = 6
        nmsp.add_entity(ne)
        bends_kept += 1

    if transform_failed:
        uwagi.append(f"transform_failed={len(transform_failed)} encji NIE weszlo do "
                     f"wyniku (GLOSNO, zasada 15): {transform_failed}")

    if len(nmsp) == 0:
        raise ValueError("wynik pusty po transformacji (GLOSNO)")

    # wysrodkowanie 1:1 na (0,0)
    ext = _bb.extents(nmsp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2.0,
                            -(ext.extmin.y + ext.extmax.y) / 2.0, 0)
    for e in nmsp:
        e.transform(mv)
    ext = _bb.extents(nmsp)
    nmsp.reset_extents((ext.extmin.x, ext.extmin.y, 0), (ext.extmax.x, ext.extmax.y, 0))

    # raport interior WYNIKU = bramka 5 (GIECIE/kolor 6 wykluczone w liczniku)
    interior, det = count_interior_contours_shapely(
        list(nmsp), sagitta=sagitta, snap_tol=snap_tol, dedup_center_tol=dedup_tol)

    info = dict(
        tryb=tryb, geom_layer=det_layer, warstwa_fallback=warstwa_fallback,
        n_picked=len(picked), n_geom=len(geom_ents),
        circ_raw=circ_raw, circ_dedup=circ_dedup,
        bends_src=len(bends), bends_kept=bends_kept,
        interior=interior, interior_detale=det,
        wymiar_x=round(ext.size.x, 2), wymiar_y=round(ext.size.y, 2),
        transform_failed=transform_failed,
        uwaga_pass=up_info["uwaga_pass"],
        uwaga_kolory=sorted(up_info["obce_kolory"]),
        uwaga_axis_skip=up_info["n_axis_skip"],
        tryby_metryki=diag["metryki"], uwagi=uwagi,
    )
    return new, info


def save_result(doc, path):
    """Cienki helper zapisu (jedyne IO; poza importem). Tworzy folder docelowy."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path


# ------------------------------------ CLI --------------------------------------

def main(argv):
    if len(argv) < 7:
        print(__doc__)
        return 2
    src, out = Path(argv[0]), Path(argv[6])
    box = tuple(float(v) for v in argv[1:5])
    scale = float(argv[5])
    is_pl = "--pl" in argv[7:]
    msp = ezdxf.readfile(src).modelspace()
    doc, info = extract_region_warstwa(msp, box, scale, is_pl=is_pl)
    save_result(doc, out)
    print(f"{out.name}: tryb={info['tryb']} warstwa={info['geom_layer']} "
          f"wymiar={info['wymiar_x']}x{info['wymiar_y']} interior={info['interior']} "
          f"okregi={info['circ_raw']}->{info['circ_dedup']} giecia={info['bends_kept']}")
    for u in info["uwagi"]:
        print(f"  ! {u}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
