# -*- coding: utf-8 -*-
"""BRAMKA 5 - bilans konturow wewnetrznych na shapely.polygonize.

Root-fix na szum licznika cyklomatycznego (licznik_konturow.py): ten liczy petle
przez zaokraglenie wezlow do 0,1 mm (round), co na LUSTRACH i przesunieciach daje
OFF-BY-ONE (dwa punkty ktore maja sie pokrywac trafiaja do roznych komorek 0,1 mm),
a na kolnierzach/wymiarach ZAWYZA. Falszywe flagi ucza ignorowania flag (54_4867),
wiec szum bijemy U ZRODLA: prawdziwa topologia przez polygonize + snap koncowek
decydowany REALNA odlegloscia (nie granica komorki round).

Metoda (sprawdzona pomiarowo, prototyp Fable, 7 wzorcow golden + inwarianty):
  1. Encje geometrii (LINE/ARC/LWPOLYLINE/POLYLINE/SPLINE/CIRCLE/ELLIPSE),
     wykluczenie giecia (kolor 6 / warstwa GIECIE - to NIE kontur).
  2. CIRCLE: srodek OCS->WCS (po lustrze CAD extrusion 0,0,-1 surowy odczyt daje
     zla strone!) + dedup wspolsrodkowych PRZED liczeniem (zostaje najmniejszy) -
     duble MASKUJA braki (surowo 5 vs 4 wyglada dobrze, po dedupie 3 vs 4 = brak).
  3. Krzywe dyskretyzowane ezdxf path.flattening(distance=sagitta).
  4. Otwarte lancuchy: snap koncowek hashem przestrzennym (3x3, realna odleglosc
     <= tol) - bez wady granicy komorki jak w round().
  5. shapely: unary_union (nodowanie) -> polygonize_full -> twarze.
     interior = liczba twarzy ZAWARTYCH w powloce innej twarzy (dziala tez dla
     regionow wieloczesciowych; dla pojedynczej czesci = n_twarzy - 1).
  6. dangle/cut/invalid z polygonize_full -> flaga NIEDOMKNIETE (otwarty kontur =
     NIE na laser, bramka 2; liczby przy niepustych flagach = NIEPEWNE, nie po cichu).

FLAGER, nie twarda bramka na liczbie: delta wskazuje GDZIE patrzec, decyzje
podejmuja OCZY (100% flag, od najwiekszych roznic, zasada 6). Twarda jest tylko
flaga NIEDOMKNIETE (otwarty kontur) - ta blokuje laser.

Uzycie:
  python produkcja\\kontrola\\bilans_konturow.py <plik.dxf>              # licznik + detale
  python produkcja\\kontrola\\bilans_konturow.py <region.dxf> <wynik.dxf>  # bilans zrodlo vs wynik
"""
import io
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath

import shapely
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize_full

# Luki gwintu (okrag wiercenia + wspolsrodkowy luk ~270 st) NIE sa konturem ani
# otwartym koncem (bramka 2) - wykluczamy je z zupy segmentow PRZED polygonize,
# jak kolor 6/GIECIE (gwint-okrag-luk-dimension.md; material NIEISTOTNY). gwint.py
# lezy w tym samym katalogu (kontrola), zawsze na sys.path przy imporcie tego modulu.
try:
    from gwint import thread_arcs as _thread_arcs
except ImportError:  # zaimportowane jako pakiet produkcja.kontrola
    from produkcja.kontrola.gwint import thread_arcs as _thread_arcs

GEOM_TYPES = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE", "ELLIPSE"}
EPS_CLOSED = 1e-9          # start==end -> ring zamkniety, nie snapujemy koncowek

# progi flagi (delta = ile cech w zrodle a nie ma w wyniku)
DELTA_KONTURY = 2          # >=2 zgubionych konturow = flaga (zasada karta kontrolna)
DELTA_OKREGI = 1           # >=1 zgubiony okrag = flaga


class EndpointSnapper:
    """Snap koncowek: hash przestrzenny (komorka=tol), kandydaci z 3x3 sasiedztwa,
    decyzja po REALNEJ odleglosci <= tol. Bez wady round(): dwa punkty w odleglosci
    < tol NIGDY nie rozjada sie przez granice komorki. Deterministyczny (kolejnosc
    encji w pliku)."""

    def __init__(self, tol):
        self.tol = tol
        self.cells = {}

    def snap(self, p):
        if self.tol <= 0:
            return p
        cx = math.floor(p[0] / self.tol)
        cy = math.floor(p[1] / self.tol)
        best, bd = None, self.tol
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in self.cells.get((cx + dx, cy + dy), ()):
                    d = math.hypot(p[0] - q[0], p[1] - q[1])
                    if d <= bd:
                        bd, best = d, q
        if best is not None:
            return best
        self.cells.setdefault((cx, cy), []).append(p)
        return p


def _is_bend(e):
    return e.dxf.layer.upper() == "GIECIE" or e.dxf.color == 6


def _flatten(e, sagitta):
    p = ezpath.make_path(e)
    return [(v.x, v.y) for v in p.flattening(distance=sagitta)]


def count_interior_contours_shapely(msp, layers=None, sagitta=0.1, snap_tol=0.1,
                                    dedup_center_tol=0.3):
    """Zwraca (interior:int, detale:dict). Deterministyczna.

    interior = liczba zamknietych twarzy zawartych w innej twarzy (otwory, fasole,
    sloty, kwadraty, wyspy - takze odseparowane). msp: modelspace ezdxf albo lista encji.
    layers: jesli podane, licz tylko encje z tych warstw.
    """
    circles = []
    open_chains = []
    closed_rings = []
    skipped_bend = 0
    skipped_thread = 0
    failed = []

    # uchwyty lukow gwintu (~270 st, wspolsrodkowe z mniejszym okregiem) - dangle
    # luku gwintu przestaje generowac flage NIEDOMKNIETE u ZRODLA (nie post-filtrem).
    try:
        thread_handles, _thr = _thread_arcs(msp)
    except Exception:
        thread_handles = frozenset()

    for e in msp:
        t = e.dxftype()
        if t not in GEOM_TYPES:
            continue
        if layers is not None and e.dxf.layer not in layers:
            continue
        if _is_bend(e):
            skipped_bend += 1
            continue
        if getattr(e.dxf, "handle", None) in thread_handles:
            skipped_thread += 1
            continue
        if t == "CIRCLE":
            c = e.ocs().to_wcs(e.dxf.center)      # OCS->WCS (lustro!)
            circles.append(((c.x, c.y), float(e.dxf.radius)))
            continue
        try:
            pts = _flatten(e, sagitta)
        except Exception as ex:
            failed.append(f"{t}: {ex}")
            continue
        if len(pts) < 2:
            continue
        d_ends = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        explicit_closed = bool(getattr(e, "closed", False))
        if d_ends < EPS_CLOSED or explicit_closed:
            if d_ends >= EPS_CLOSED:
                pts.append(pts[0])
            if len(pts) >= 4:
                closed_rings.append(pts)
        else:
            open_chains.append(pts)

    # dedup okregow wspolsrodkowych (zostaje najmniejszy)
    csnap = EndpointSnapper(dedup_center_tol)
    groups = {}
    for center, r in circles:
        key = csnap.snap(center)
        groups.setdefault(key, []).append(r)
    circles_raw = len(circles)
    circles_dedup = len(groups)
    for key, radii in sorted(groups.items()):
        r = min(radii)
        n = max(int(math.ceil(math.pi / math.acos(max(1.0 - sagitta / r, -1.0)))), 8) \
            if r > sagitta else 8
        ring = [(key[0] + r * math.cos(2 * math.pi * i / n),
                 key[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        ring.append(ring[0])
        closed_rings.append(ring)

    # snap koncowek otwartych lancuchow
    if snap_tol > 0:
        esnap = EndpointSnapper(snap_tol)
        snapped = []
        for pts in open_chains:
            a = esnap.snap(pts[0])
            b = esnap.snap(pts[-1])
            snapped.append([a] + pts[1:-1] + [b])
        open_chains = snapped

    lines = [LineString(pts) for pts in open_chains + closed_rings if len(pts) >= 2]
    if not lines:
        return 0, dict(interior=0, faces=0, outer=0, dangles=0, cuts=0, invalid=0,
                       circles_raw=circles_raw, circles_dedup=circles_dedup,
                       bend_skipped=skipped_bend, thread_skipped=skipped_thread,
                       failed=failed, flags=["brak geometrii"])

    merged = unary_union(lines)
    polys, dangles, cuts, invalids = polygonize_full([merged])
    faces = [g for g in polys.geoms if g.area > 0]
    n_dangles = len(dangles.geoms)
    n_cuts = len(cuts.geoms)
    n_invalid = len(invalids.geoms)

    # twarz wewnetrzna = rep-point wewnatrz POWLOKI innej twarzy.
    # GEOS zwraca twarz zewnetrzna z JUZ wycietymi otworami -> test po exterior shell.
    shells = [Polygon(f.exterior) for f in faces]
    reps = [f.representative_point() for f in faces]
    n_interior = 0
    for i in range(len(faces)):
        if any(j != i and shells[j].contains(reps[i]) for j in range(len(faces))):
            n_interior += 1
    n_outer = len(faces) - n_interior

    flags = []
    if n_dangles or n_cuts or n_invalid:
        flags.append(f"NIEDOMKNIETE: dangles={n_dangles} cuts={n_cuts} invalid={n_invalid}"
                     " -> mozliwy otwarty kontur, wynik NIEPEWNY (bramka 2)")
    if n_outer != 1:
        flags.append(f"n_outer={n_outer} (oczekiwane 1 dla pojedynczej czesci)")
    if failed:
        flags.append(f"encje nieprzetworzone: {failed}")

    detale = dict(interior=n_interior, faces=len(faces), outer=n_outer,
                  dangles=n_dangles, cuts=n_cuts, invalid=n_invalid,
                  circles_raw=circles_raw, circles_dedup=circles_dedup,
                  bend_skipped=skipped_bend, thread_skipped=skipped_thread,
                  failed=failed, flags=flags)
    return n_interior, detale


def bilans(region, wynik, layers_region=None, layers_wynik=None, **kw):
    """Bramka 5: bilans konturow wewnetrznych ZRODLO (region) vs WYNIK.

    region / wynik: modelspace albo lista encji. Zwraca dict z semaforem:
      - 'czerwony' gdy WYNIK ma flage NIEDOMKNIETE (otwarty kontur = nie na laser),
      - 'zolty'    gdy delta konturow >= 2 LUB zgubiony okrag (FLAGA -> ogledziny 100%),
      - 'zielony'  gdy bilans sie zgadza.
    Decyzje o zoltym podejmuja OCZY (flager) - nie zamykac po wielkosci roznicy.
    """
    ri, rdet = count_interior_contours_shapely(region, layers=layers_region, **kw)
    wi, wdet = count_interior_contours_shapely(wynik, layers=layers_wynik, **kw)
    delta = ri - wi
    delta_okr = rdet["circles_dedup"] - wdet["circles_dedup"]

    powody = []
    if wdet["flags"]:
        for fl in wdet["flags"]:
            if fl.startswith("NIEDOMKNIETE"):
                powody.append(f"WYNIK {fl}")
    if delta >= DELTA_KONTURY:
        powody.append(f"zgubione kontury: zrodlo={ri} wynik={wi} (delta={delta})")
    if delta_okr >= DELTA_OKREGI:
        powody.append(f"zgubione okregi (po dedupie): zrodlo={rdet['circles_dedup']} "
                      f"wynik={wdet['circles_dedup']}")

    if any(p.startswith("WYNIK NIEDOMKNIETE") for p in powody):
        semafor = "czerwony"
    elif powody:
        semafor = "zolty"
    else:
        semafor = "zielony"

    return dict(semafor=semafor, interior_zrodlo=ri, interior_wynik=wi, delta=delta,
                delta_okregi=delta_okr, powody=powody, zrodlo=rdet, wynik=wdet)


def _load(f):
    return ezdxf.readfile(f).modelspace()


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if len(argv) == 1:
        n, det = count_interior_contours_shapely(_load(argv[0]))
        print(f"{Path(argv[0]).name}: kontury_wewnetrzne={n}")
        for k, v in det.items():
            print(f"  {k}: {v}")
        return 0 if not det["flags"] else 1
    b = bilans(_load(argv[0]), _load(argv[1]))
    sem = {"zielony": "OK", "zolty": "FLAGA (ogledziny 100%)", "czerwony": "NIE na laser"}
    print(f"BILANS  zrodlo={b['interior_zrodlo']} wynik={b['interior_wynik']} "
          f"delta={b['delta']}  -> {b['semafor'].upper()} ({sem[b['semafor']]})")
    for p in b["powody"]:
        print(f"  ! {p}")
    return {"zielony": 0, "zolty": 1, "czerwony": 2}[b["semafor"]]


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
