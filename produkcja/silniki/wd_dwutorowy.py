# -*- coding: utf-8 -*-
"""Silnik W-D "dwutorowy" - V3 (zywy, importowalny, opt-in czwarty wariant).

Metoda operatora (propozycja 2026-07-08, boj na 41_2050): dwa tory.
  TOR 1 (geometria): box + skala PRZYCHODZA Z ZEWNATRZ (jak w W-C region+warstwa) -
     hojna siatka zbierania po bbox (nic nie odrzucamy za wczesnie).
  TOR 2 (czyszczenie): dopiero tu kontur zewnetrzny (polygonize -> pierscien),
     kolor bazowy Z KRAWEDZI OBRYSU, przynaleznosc otworow = point-in-polygon
     (NIE odleglosc/gap - cechy odseparowane nie wypadaja), UWAGA-pass na otwory
     INNEGO koloru, klasyfikacja gietc, fazowanie, dedup.

Root-fix vs W-A/W-B (klaster po gap): cechy odseparowane >gap wypadaly (54_4867,
SL40034116 -13 Langlochow). Root-fix vs W-C (jeden tryb koloru): pojedynczy otwor
INNEGO koloru wypadal (SL40062903: 2 vs 6) - W-D lapie go UWAGA-passem.

Czyszczenie v2 (poprawki wg werdyktow operatora 41_2050, 85% bledow W-D v1 = jedna
klasa "czyszczenie"):
  A) filtr osi: linetype osiowe (CENTER/PHANTOM/MITTE) NIE wchodza do polygonize ani
     do wyniku; encje spoza pierscieni (strzalki, promienie, osie Continuous) odpadaja
     przez klasyfikacje per-encja na ZAAKCEPTOWANYCH pierscieniach (exterior + wyspy).
     UWAGA-pass strukturalnie tylko ZAMKNIETE petle (interiors) - luk-os nie wchodzi.
  B) giecia (kol.6 / warstwa GIECIE / DASHDOT): klasyfikacja
     - koniec dalej niz TOL_BEND od obrysu -> OS (krzyz/os symetrii) -> out;
     - przechodzi przez srodek okregu -> OS -> out;
     - adnotacja 'n.unten/bend down' (najblizsza) -> out + flaga (w dol nie robimy);
       przy is_pl=True (para P/L) DOWN ZOSTAJE (na lustrze kierunek sie odwraca);
     - lt CENTER pozioma/pionowa bez adnotacji kierunku -> OS -> out;
     - reszta (UP / DASHDOT / skos) -> ZOSTAJE PELNA DLUGOSC + flaga skracania
       (>300 mm; konwencja skracania NIEjednoznaczna: stuby 19-159 mm, 6-36%).
  C) fazowanie: chord dzielacy obrys NIE gubi wymiaru (solid = unia faces, nie
     najwiekszy face); linie-kandydaci (konce na obrysie, srodek w materiale)
     rozstrzyga produkcja/kontrola/fazowanie.py (IMPORT) na wyniku 1:1 -> faza
     zostaje pozolcona (kolor 2) + technologia=fazowanie.
  D) fallback bez ringu: filtr A-lite (lt osiowe + promienie LINE-koniec=centrum ARC),
     flaga OTWARTY_OBRYS (W-D nie zgaduje - uczciwie pasuje jak W-C fallback).
  Dedup: identyczne CIRCLE (srodek+promien) i identyczne encje usuwane - duble
     MASKUJA braki (surowo 5 vs 4 wyglada dobrze, po dedupie 3 vs 4 = brak).

Wlasnosci V3 (port z prototypu scratchpad wd.py v2 - zrodlo prawdy):
  1. IMPORT bramek zamiast kopii: bilans_konturow (bramka 5) + fazowanie z ../kontrola.
  2. TOR 1 z zewnatrz: box+skala parametrem (bez QNAP/wykazu/orkiestracji 41_2050 -
     to warstwa warianty.py/orkiestrator.py, nie silnik).
  3. ZERO efektow ubocznych na imporcie: bez mkdir/sciezek zlecen; IO tylko w save_result().
  4. Interfejs WYMIENNY z W-C: extract_wd(src_msp, box, scale, is_pl=False, ...) ->
     (ezdxf.Drawing, info_dict) z 'interior'/'wymiar_x'/'wymiar_y' jak W-C.
  5. GLOSNE logowanie (zasada 15): transform-fail -> flaga, nie znika po cichu.

Interfejs:
  extract_wd(src_msp, box, scale, is_pl=False, margin=1.0, sagitta=0.05,
             snap_tol=0.10, dedup_tol=0.10) -> (ezdxf.Drawing, info_dict)
  save_result(doc, path)

CLI:
  python produkcja\\silniki\\wd_dwutorowy.py <zrodlo.dxf> <x1> <y1> <x2> <y2> <scale> <out.dxf> [--pl]
"""
import io
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import bbox as ezbbox
from ezdxf import path as ezpath
from ezdxf.math import Matrix44

from shapely.geometry import LineString, Polygon, Point, MultiLineString
from shapely.ops import unary_union, polygonize_full

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))                       # extract_positions (ten sam katalog)
sys.path.insert(0, str(_HERE.parent / "kontrola"))   # bilans_konturow, fazowanie
import extract_positions as WA                        # noqa: E402
from bilans_konturow import count_interior_contours_shapely, EndpointSnapper  # noqa: E402
import fazowanie as FAZ                               # noqa: E402  (IMPORT, nie kopia)

GEOM_TYPES = WA.GEOM_TYPES

# --- progi (papierowe [mm], chyba ze zaznaczono 1:1) - z prototypu v2 ---
SAGITTA_PAPER = 0.05      # dyskretyzacja na papierze [mm]
SNAP_PAPER = 0.10         # snap koncowek na papierze [mm]
TOL_ON = 0.15            # przynaleznosc probki do krawedzi ringu [mm papieru]
MARGIN = 1.0             # hojny margines bbox [mm papieru]
TOL_BEND = 1.0          # koniec giecia "na obrysie" [mm papieru]
TOL_AXIS_CIRC = 0.3     # os przechodzi przez srodek okregu [mm papieru]
DEDUP_TOL = 0.10         # identyczne okregi (srodek i promien) [mm papieru]
BEND_LONG_REAL = 300.0   # [mm 1:1] flaga: operator takie skraca (stub 19-159)
AXIS_LT = {"CENTER", "CENTER2", "CENTERX2", "PHANTOM", "PHANTOM2", "MITTE"}

RX_UP = re.compile(r"n\.?\s*oben|bend\s*up", re.I)
RX_DOWN = re.compile(r"n\.?\s*unten|bend\s*down", re.I)


# ------------------------------ klocki pomocnicze ------------------------------

def eff_color(e, doc):
    """Kolor efektywny: 0/256 (BYBLOCK/BYLAYER) -> kolor warstwy. Geometria bywa
    BYLAYER na kolorowej warstwie."""
    c = e.dxf.color
    if c in (0, 256):
        try:
            return abs(doc.layers.get(e.dxf.layer).color)
        except Exception:
            return 7
    return c


def is_bend(e, doc):
    lt = (e.dxf.linetype or "").upper()
    return (eff_color(e, doc) == 6 or e.dxf.layer.upper() == "GIECIE"
            or lt in WA.BEND_LINETYPES)


def is_axis_lt(e):
    return (e.dxf.linetype or "").upper() in AXIS_LT


def flatten_pts(e, sagitta=SAGITTA_PAPER):
    p = ezpath.make_path(e)
    return [(v.x, v.y) for v in p.flattening(distance=sagitta)]


def subsample(pts, n=24):
    if len(pts) <= n:
        return pts
    step = max(1, len(pts) // n)
    out = pts[::step]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def densify(pts, max_step=2.0):
    """Dogeszcza proste segmenty do probkowania klasyfikacji. Bez tego LINE ma tylko
    KONCE - os/chord konczacy sie na obrysie liczyl sie jako obrys (bug fazowania
    SL10523531_p2 i osi continuous 40045202)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(d // max_step)
        for i in range(1, k + 1):
            t = i / (k + 1)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        out.append(b)
    return out


def _kier_texts(msp, gbox):
    """Adnotacje kierunku giecia (UP/DOWN) w boxie: [(kier, (cx, cy))]."""
    out = []
    for e in msp:
        t = e.dxftype()
        if t not in ("TEXT", "MTEXT"):
            continue
        b = WA.ent_bbox(e)
        if not b or not (b[0] >= gbox[0] and b[1] >= gbox[1]
                         and b[2] <= gbox[2] and b[3] <= gbox[3]):
            continue
        try:
            s = e.dxf.text if t == "TEXT" else e.plain_text()
        except Exception:
            continue
        if not s:
            continue
        kier = "UP" if RX_UP.search(s) else ("DOWN" if RX_DOWN.search(s) else "")
        if kier:
            out.append((kier, ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)))
    return out


def _is_radius_line(e, arcs_centers, tol=0.5):
    """LINE z koncem w SRODKU jakiegos luku = znacznik promienia (nie geometria)."""
    if e.dxftype() != "LINE":
        return False
    s, en = e.dxf.start, e.dxf.end
    for cx, cy in arcs_centers:
        if (math.hypot(s.x - cx, s.y - cy) < tol
                or math.hypot(en.x - cx, en.y - cy) < tol):
            return True
    return False


def _classify_bend(e, pts, ring_ext, circles, texts, is_pl=False):
    """Zwraca ('OS'|'DOWN'|'KEEP', powod). Reguly z werdyktow 41_2050:
    - DOWN (najblizsza adnotacja) -> out ('w dol nie robimy'); przy is_pl=True
      ZOSTAJE (para P/L: kierunek odwraca sie na lustrze);
    - lt CENTER/MITTE = domyslnie OS otworu/symetrii, chyba ze linia konczy sie na
      obrysie ORAZ (adnotacja UP lub skos >1st) - wtedy giecie;
    - inne lt (DASHDOT/DASHED/PHANTOM/Continuous kol.6) = giecie, zostaje
      (zrodla bywaja ze skroconymi liniami -> nie wymagamy koncow na ringu)."""
    ls = LineString(pts)
    mid = ls.interpolate(0.5, normalized=True)
    kier, dmin = "", None
    for k, (tx, ty) in texts:
        dt = math.hypot(mid.x - tx, mid.y - ty)
        if dmin is None or dt < dmin:
            dmin, kier = dt, k
    if kier == "DOWN" and not is_pl:
        return "DOWN", "adnotacja n.unten"
    lt = (e.dxf.linetype or "").upper()
    if lt in ("CENTER", "MITTE", "CENTER2", "CENTERX2"):
        p0, p1 = Point(pts[0]), Point(pts[-1])
        if max(ring_ext.distance(p0), ring_ext.distance(p1)) > TOL_BEND:
            return "OS", "CENTER: koniec daleko od obrysu"
        for (cx, cy), r in circles:
            if r >= 0.5 and ls.distance(Point(cx, cy)) <= TOL_AXIS_CIRC:
                return "OS", "CENTER: przechodzi przez srodek okregu"
        if kier == "UP":
            return "KEEP", "adnotacja n.oben"
        if e.dxftype() == "LINE":
            s, en = e.dxf.start, e.dxf.end
            ang = math.degrees(math.atan2(en.y - s.y, en.x - s.x)) % 90.0
            if min(ang, 90.0 - ang) <= 1.0:
                return "OS", "CENTER prosto bez adnotacji n.oben"
        return "KEEP", "kierunek nieznany"
    if kier == "UP":
        return "KEEP", "adnotacja n.oben"
    return "KEEP", "kierunek nieznany"


def _dedup_circles(kept, dedup_tol=DEDUP_TOL):
    """Usun IDENTYCZNE okregi (srodek+promien w dedup_tol). Preferuj 1. egzemplarz.
    Zwraca (kept2, n_usunietych). Wspolsrodkowe o ROZNYCH r NIE ruszane (pierscien!)."""
    seen = []
    out = []
    n = 0
    for e, rola in kept:
        if e.dxftype() != "CIRCLE":
            out.append((e, rola))
            continue
        c = e.ocs().to_wcs(e.dxf.center)
        r = float(e.dxf.radius)
        dup = any(math.hypot(c.x - sx, c.y - sy) <= dedup_tol
                  and abs(r - sr) <= dedup_tol for sx, sy, sr in seen)
        if dup:
            n += 1
            continue
        seen.append((c.x, c.y, r))
        out.append((e, rola))
    return out, n


def _dedup_generic(kept):
    """Usun encje o IDENTYCZNEJ geometrii (fingerprint z dyskretyzacji 0.05). Duble
    maskuja braki i podwajaja ciecie. Zwraca (kept2, n)."""
    seen = set()
    out = []
    n = 0
    for e, rola in kept:
        try:
            pts = flatten_pts(e)
            key = tuple(sorted([(round(x, 1), round(y, 1)) for x, y in
                                (pts[:1] + pts[len(pts) // 2:len(pts) // 2 + 1]
                                 + pts[-1:])]))
            fp = (e.dxftype(), key, round(LineString(pts).length, 1)
                  if len(pts) >= 2 else 0)
        except Exception:
            out.append((e, rola))
            continue
        if fp in seen:
            n += 1
            continue
        seen.add(fp)
        out.append((e, rola))
    return out, n


# --------------------------------- ekstrakcja ----------------------------------

def extract_wd(src_msp, box, scale, is_pl=False, margin=MARGIN,
               sagitta=SAGITTA_PAPER, snap_tol=SNAP_PAPER, dedup_tol=DEDUP_TOL):
    """Ekstrakcja W-D (dwutorowa) jednego widoku -> (ezdxf.Drawing, info_dict).

    src_msp: modelspace ZRODLA; box=(x1,y1,x2,y2) w ukladzie zrodla (TOR 1 z zewnatrz);
    scale z raportu. is_pl: pozycja P/L (lustro) -> giecia DOWN nie usuwamy (kierunek
    odwraca sie na lustrze). Bez zapisu na dysk (save_result()). Wynik: 1:1,
    wysrodkowany (0,0), okregi po dedupie, giecia na warstwie GIECIE kolor 6.

    info: kolor_bazowy, uwaga_pass, flagi[], n_kept, n_bend, n_dropped, n_osie,
          n_bend_out, n_dedup, fallback, technologia, faza_ids, wymiar_x, wymiar_y,
          interior, interior_detale, otwarte_konce (analogicznie do W-C).
    """
    doc = getattr(src_msp, "doc", None)
    info = dict(kolor_bazowy=None, uwaga_pass=0, flagi=[], n_bend=0,
                n_kept=0, n_dropped=0, fallback=False, n_osie=0, n_bend_out=0,
                n_dedup=0, technologia="", faza_ids=set())
    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"bbox zdegenerowany: {box}")
    gbox = (x1 - margin, y1 - margin, x2 + margin, y2 + margin)

    # TOR 1: hojne zbieranie po bbox (nic nie odrzucamy za wczesnie)
    cands, bends = [], []
    for e in src_msp:
        if e.dxftype() not in GEOM_TYPES:
            continue
        b = WA.ent_bbox(e)
        if not b or not (b[0] >= gbox[0] and b[1] >= gbox[1]
                         and b[2] <= gbox[2] and b[3] <= gbox[3]):
            continue
        (bends if is_bend(e, doc) else cands).append(e)
    if not cands:
        raise ValueError(f"brak geometrii w bbox {box} (GLOSNO - sprawdz bbox/zrodlo)")
    texts = _kier_texts(src_msp, gbox)

    # --- A) osie po linetype odpadaja PRZED polygonize ---
    solid_cands = []
    for e in cands:
        if is_axis_lt(e):
            info["n_osie"] += 1
            continue
        solid_cands.append(e)

    flat = {}
    open_chains, closed_rings = [], []
    for e in solid_cands:
        try:
            pts = flatten_pts(e, sagitta)
        except Exception:
            info["flagi"].append(f"flatten-fail:{e.dxftype()}")
            continue
        if len(pts) < 2:
            continue
        flat[id(e)] = pts
        d = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        if d < 1e-9 or bool(getattr(e, "closed", False)):
            if d >= 1e-9:
                pts = pts + [pts[0]]
            if len(pts) >= 4:
                closed_rings.append(pts)
        else:
            open_chains.append((id(e), pts))

    snap = EndpointSnapper(snap_tol)
    snapped = []
    for eid, pts in open_chains:
        a = snap.snap(pts[0])
        b = snap.snap(pts[-1])
        npts = [a] + pts[1:-1] + [b]
        flat[eid] = npts
        snapped.append(npts)

    lines = [LineString(p) for p in snapped + closed_rings if len(p) >= 2]
    solid = None
    inner_rings = []
    if lines:
        merged = unary_union(lines)
        polys, dangles, cuts, invalids = polygonize_full([merged])
        faces = [g for g in polys.geoms if g.area > 0]
        if faces:
            # C-fix (fazowanie SL10523531_p2): EXTERIOR z UNII faces - chord (linia
            # fazowania) dzielacy material na 2 faces nie gubi wymiaru. v1 bral
            # najwiekszy face -> obrys "sciety".
            uni = unary_union(faces)
            comps = list(uni.geoms) if uni.geom_type == "MultiPolygon" else [uni]
            main = max(comps, key=lambda p: p.area)
            mb = main.bounds
            if (mb[2] - mb[0]) >= 0.5 * (x2 - x1) and (mb[3] - mb[1]) >= 0.5 * (y2 - y1):
                solid = main
                # petle WEWNETRZNE = exteriors faces scisle wewnatrz main, NIE
                # dotykajace jego exterioru (otwory, wyspy; chord-faces materialu
                # dotykaja exterioru -> odpadaja; UWAGA-pass strukturalnie dostaje
                # tylko ZAMKNIETE petle)
                ext_buf = main.exterior.buffer(TOL_ON / 2)
                for f in faces:
                    fx = f.exterior
                    if (main.contains(f.representative_point())
                            and not fx.within(ext_buf)
                            and not fx.intersects(main.exterior)):
                        inner_rings.append(fx)

    if solid is None:
        # --- D) FALLBACK: filtry A-lite zanim oddamy bbox ---
        info["fallback"] = True
        info["flagi"].append("OTWARTY_OBRYS-fallback-bbox")
        arcs_centers = [(a.dxf.center.x, a.dxf.center.y)
                        for a in cands if a.dxftype() == "ARC"]
        kept = []
        for e in cands:
            if is_axis_lt(e):
                info["n_osie"] += 1
                continue
            if _is_radius_line(e, arcs_centers):
                info["n_dropped"] += 1
                info["flagi"].append("promien-R usuniety (koniec=centrum luku)")
                continue
            kept.append((e, "fallback"))
        bend_keep = bends
        faz_cands = []
    else:
        ring_ext = solid.exterior
        acc_union = MultiLineString(
            [LineString(r.coords) for r in inner_rings]) if inner_rings else None
        kept = []
        votes = defaultdict(float)
        faz_cands = []
        for e in solid_cands:
            pts = flat.get(id(e))
            if not pts:
                info["n_dropped"] += 1
                continue
            smp = subsample(densify(pts))
            d_out = [ring_ext.distance(Point(p)) for p in smp]
            n_on_out = sum(1 for d in d_out if d <= TOL_ON)
            if n_on_out >= 0.6 * len(smp):
                kept.append((e, "obrys"))
                ln = LineString(pts).length if len(pts) >= 2 else 0.0
                votes[eff_color(e, doc)] += ln
                continue
            if acc_union is not None:
                n_on_in = sum(1 for p in smp
                              if acc_union.distance(Point(p)) <= TOL_ON)
                if n_on_in >= 0.6 * len(smp):
                    kept.append((e, "wnetrze"))
                    continue
            # C) kandydat fazowania: LINE, oba konce na obrysie, srodek w materiale
            if e.dxftype() == "LINE" and len(pts) >= 2:
                p0, p1 = Point(pts[0]), Point(pts[-1])
                mid = LineString(pts).interpolate(0.5, normalized=True)
                if (ring_ext.distance(p0) <= TOL_ON and ring_ext.distance(p1) <= TOL_ON
                        and solid.buffer(TOL_ON).contains(mid)):
                    faz_cands.append(e)
                    continue
            info["n_dropped"] += 1     # os continuous / strzalka / promien / wymiar

        base = max(votes, key=votes.get) if votes else None
        info["kolor_bazowy"] = base

        # dedupy (duble maskuja braki) - PRZED UWAGA-pass
        kept, n_dc = _dedup_circles(kept, dedup_tol)
        kept, n_dg = _dedup_generic(kept)
        info["n_dedup"] = n_dc + n_dg
        if info["n_dedup"]:
            info["flagi"].append(f"DEDUP: {info['n_dedup']} identycznych encji usunieto")

        # UWAGA-pass: tylko petle ZAMKNIETE (interiors/wyspy) obcego koloru
        obce_kolory = set()
        for e, rola in kept:
            if rola == "wnetrze" and base is not None and eff_color(e, doc) != base:
                info["uwaga_pass"] += 1
                obce_kolory.add(eff_color(e, doc))
        if info["uwaga_pass"]:
            info["flagi"].append(
                f"UWAGA-pass: {info['uwaga_pass']} encji petli koloru {sorted(obce_kolory)}"
                f" (bazowy={base}) - DOLACZONE, ogledziny")

        # --- B) giecia wg werdyktow (UP zostaje / DOWN i osie out) ---
        circles = [((e.ocs().to_wcs(e.dxf.center).x, e.ocs().to_wcs(e.dxf.center).y),
                    float(e.dxf.radius))
                   for e, _ in kept if e.dxftype() == "CIRCLE"]
        bend_keep = []
        n_down = 0
        for e in bends:
            try:
                pts = flatten_pts(e, sagitta)
            except Exception:
                bend_keep.append(e)
                continue
            if len(pts) < 2:
                continue
            smp = subsample(pts)
            ins = sum(1 for p in smp if solid.buffer(TOL_ON).covers(Point(p)))
            if ins < 0.5 * len(smp):
                info["n_bend_out"] += 1
                continue
            wyn, powod = _classify_bend(e, pts, ring_ext, circles, texts, is_pl)
            if wyn == "OS":
                info["n_osie"] += 1
                info["n_bend_out"] += 1
                continue
            if wyn == "DOWN":
                n_down += 1
                info["n_bend_out"] += 1
                continue
            L_real = LineString(pts).length * scale
            if powod == "kierunek nieznany":
                info["flagi"].append(
                    f"GIECIE_KIERUNEK_NIEZNANY (L={L_real:.0f}mm) - zostawione, ogledziny")
            if L_real > BEND_LONG_REAL:
                info["flagi"].append(
                    f"GIECIE_DLUGIE {L_real:.0f}mm pelne - operator skraca "
                    f"(stub 19-159mm; konwencja niejednoznaczna)")
            bend_keep.append(e)
        if n_down:
            info["flagi"].append(
                f"GIECIA n.unten x{n_down} USUNIETE (w dol nie robimy; "
                f"skos w dol = rozwaz lustro)")
        bend_keep, n_db = _dedup_generic([(e, "g") for e in bend_keep])
        bend_keep = [e for e, _ in bend_keep]
        info["n_dedup"] += n_db

    # --- budowa wyniku 1:1, wysrodkowanie ---
    nd = ezdxf.new(dxfversion="AC1021")
    if bend_keep:
        nd.layers.add("GIECIE", color=6)
    nmsp = nd.modelspace()
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    m = Matrix44.translate(-cx, -cy, 0) @ Matrix44.scale(scale, scale, 1)
    for e, _rola in kept:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            info["flagi"].append(f"transform-fail:{e.dxftype()}")
            continue
        ne.dxf.layer = "0"
        nmsp.add_entity(ne)
        info["n_kept"] += 1
    for e in bend_keep:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            info["flagi"].append(f"transform-fail-GIECIE:{e.dxftype()}")
            continue
        ne.dxf.layer = "GIECIE"
        ne.dxf.color = 6
        nmsp.add_entity(ne)
        info["n_bend"] += 1

    # --- C) fazowanie: kandydatow rozstrzyga fazowanie.py na wyniku 1:1 ---
    if faz_cands:
        added = []
        for e in faz_cands:
            ne = e.copy()
            try:
                ne.transform(m)
            except Exception:
                continue
            ne.dxf.layer = "0"
            nmsp.add_entity(ne)
            added.append(ne)
        try:
            kand = FAZ.wykryj_fazowanie(nmsp)
        except Exception as ex:
            kand = []
            info["flagi"].append(f"fazowanie-blad:{ex}")
        matched = set()
        for k in kand:
            for ne in added:
                if id(ne) in matched:
                    continue
                if FAZ._te_same_konce(ne, k["t_zlacza"], tol=0.2):
                    matched.add(id(ne))
        for ne in added:
            if id(ne) in matched:
                ne.dxf.color = FAZ.ZOLTY
                info["n_kept"] += 1
                info["faza_ids"].add(id(ne))
            else:
                nmsp.delete_entity(ne)
                info["n_dropped"] += 1
        if matched:
            info["technologia"] = "fazowanie"
            info["flagi"].append(
                f"FAZOWANIE: {len(matched)} linii zostawiono (zolte), "
                f"{FAZ.komentarz(kand)}")

    ext = ezbbox.extents(nmsp)
    if ext.has_data:
        mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2,
                                -(ext.extmin.y + ext.extmax.y) / 2, 0)
        for e in nmsp:
            try:
                e.transform(mv)
            except Exception:
                pass
        ext = ezbbox.extents(nmsp)
        nmsp.reset_extents((ext.extmin.x, ext.extmin.y, 0),
                           (ext.extmax.x, ext.extmax.y, 0))
        info["wymiar_x"] = round(ext.size.x, 2)
        info["wymiar_y"] = round(ext.size.y, 2)
    else:
        info["wymiar_x"] = info["wymiar_y"] = 0.0
        info["flagi"].append("PUSTY_WYNIK")

    # --- metryki wyniku (analogicznie do W-C): kontury wewn. + otwarte konce ---
    ents = list(nmsp)
    interior, det = count_interior_contours_shapely(ents)
    geom_nb = [e for e in ents
               if e.dxftype() in GEOM_TYPES and e.dxf.layer.upper() != "GIECIE"
               and e.dxf.color != 6 and id(e) not in info["faza_ids"]]
    oe = WA.open_ends(geom_nb, tol=0.05)
    info["interior"] = interior
    info["interior_detale"] = det
    info["otwarte_konce"] = oe
    if det["flags"]:
        info["flagi"].extend(f"bilans:{f}"[:120] for f in det["flags"])
    return nd, info


def save_result(doc, path):
    """Cienki helper zapisu (jedyne IO poza importem). Tworzy folder docelowy."""
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
    doc, info = extract_wd(msp, box, scale, is_pl=is_pl)
    save_result(doc, out)
    print(f"{out.name}: baza={info['kolor_bazowy']} "
          f"wymiar={info['wymiar_x']}x{info['wymiar_y']} interior={info['interior']} "
          f"otw_konce={info['otwarte_konce']} giecia={info['n_bend']} "
          f"uwaga_pass={info['uwaga_pass']} osie={info['n_osie']} dedup={info['n_dedup']}")
    for u in info["flagi"]:
        print(f"  ! {u}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
