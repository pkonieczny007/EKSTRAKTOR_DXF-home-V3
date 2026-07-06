# -*- coding: utf-8 -*-
"""SWEEP KOMPLETNOSCI - obowiazkowe domkniecie zlecenia (CLAUDE.md zasada 7).

Dla WSZYSTKICH pozycji zlecenia liczy kontury wewnetrzne REGIONU ZRODLOWEGO
(widok z rysunku, bbox z raportu) i porownuje z dostarczonym DXF. delta>=prog
-> FLAGA -> OGLEDZINY WZROKIEM 100% (render region vs wynik, zasada 6), od
NAJWIEKSZYCH roznic. Nigdy nie odrzucac flagi po wielkosci (blad 54_4867).

SEDNO (lekcja 54_4867 / SL40061302): geometria bywa na kolorze 2/4/7 albo na
warstwie - tryb col7 NIE widzi slotow na kolorze 2. Liczymy WSZYSTKIE tryby i
bierzemy prawde z trybow CZYSTYCH (n_outer==1); 'all' zawyza (adnotacje/osie)
- nigdy nie jest zrodlem prawdy, tylko diagnostyka.

Liczenie = bramka 5 (bilans_konturow.count_interior_contours_shapely) - odporna
na lustro/jitter (polygonize + snap realna odlegloscia). Dzieki temu prog flagi
= delta>=1 (nie >=2): polygonize zbil szum cyklomatyki u zrodla (zmierzone:
delta_wzorzec=0 na wzorcach golden), a pod zasada 6 nizszy prog moze tylko
DODAC ogledzin, nigdy uja (kompletnosc wazniejsza niz oszczednosc patrzenia).

FLAGER, nie twarda bramka: delta wskazuje GDZIE patrzec, decyduja OCZY (100% flag).
Twarda jest tylko NIEDOMKNIETE (otwarty kontur wyniku = nie na laser, bramka 2).

Rdzen kontury_regionu_zrodla zaprojektowany i zmierzony przez fable-advisor
(scratchpad), zweryfikowany i wpiety przez orkiestratora (etap 2 PLAN.md).

Uzycie:
  python produkcja\\kontrola\\sweep.py <folder_wynikow> <folder_rysunkow> [--prog N]
    folder_wynikow  - <zlecenie>/ z podfolderami <zeinr>/ (raport + dostarczone DXF)
    folder_rysunkow - zrodlowe <zeinr>_1_conv.dxf (albo <zeinr>_1.dxf)
  Raport sweepa -> testy/raporty/sweep_<zlecenie>.csv (+ lista flag na stdout).
"""
import csv
import io
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bilans_konturow import count_interior_contours_shapely, GEOM_TYPES

REPO = HERE.parent.parent
RAPORTY = REPO / "testy" / "raporty"

TRYBY_KOLOR = {"col7": 7, "col2": 2, "col4": 4}
TRYBY_CZYSTE = ("warstwa_geom", "col7", "col2", "col4")  # kandydaci na prawde; priorytet remisu
PROG_DELTA = 1                                           # delta>=1 = flaga (zmierzone: 0 falszywych)


# --- klocki wyboru regionu (replika z region_warstwa.py; tam import ma efekt
#     uboczny OUT.mkdir + zly import - do naprawy przy awansie W-C, etap 2) -------
def center(e):
    try:
        return _bb.extents([e]).center
    except Exception:
        return None


def in_bbox(c, x1, y1, x2, y2, m=1.0):
    return c is not None and x1 - m <= c.x <= x2 + m and y1 - m <= c.y <= y2 + m


def effective_color(e, layer_colors):
    """256=BYLAYER -> kolor warstwy (geometria bywa BYLAYER na kolorowej warstwie)."""
    c = e.dxf.color
    return layer_colors.get(e.dxf.layer, 7) if c == 256 else c


def kontury_regionu_zrodla(src_msp, box, sagitta=0.1, snap_tol=0.1, margin=1.0):
    """Kontury wewnetrzne REGIONU ZRODLOWEGO (bbox widoku) we wszystkich trybach.

    src_msp: modelspace ezdxf zrodlowego rysunku; box: (x1,y1,x2,y2) w ukladzie ZRODLA.
    Zwraca dict: per_tryb, zrodlo_prawda, tryb_znaleziony, diag (uwagi GLOSNE).
    """
    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"bbox zdegenerowany: {box}")

    layer_colors = {}
    doc = getattr(src_msp, "doc", None)
    if doc is not None:
        for ly in doc.layers:
            layer_colors[ly.dxf.name] = ly.dxf.color

    picked, bends = [], 0
    for e in src_msp:
        if e.dxftype() not in GEOM_TYPES:
            continue
        c = center(e)
        if not in_bbox(c, x1, y1, x2, y2, margin):
            continue
        ec = effective_color(e, layer_colors)
        if ec == 6 or e.dxf.layer.upper() == "GIECIE":
            bends += 1
            continue
        picked.append((e, ec))

    kolory = Counter(ec for _, ec in picked)
    uwagi = []
    if not picked:
        uwagi.append("BRAK GEOMETRII W REGIONIE - sprawdz bbox/zrodlo/uklad (GLOSNO!)")
        per_tryb = {t: 0 for t in ("col7", "col2", "col4", "all", "warstwa_geom")}
        return dict(per_tryb=per_tryb, zrodlo_prawda=0, tryb_znaleziony=None,
                    diag=dict(n_ents_bbox=0, bends=bends, kolory_geom={},
                              warstwa_geom=None, warstwa_fallback=False,
                              per_tryb_detale={}, uwagi=uwagi))

    # warstwa geometrii: najczestsza warstwa GEOM koloru 7; brak koloru 7 -> fallback
    cnt7 = Counter(e.dxf.layer for e, ec in picked if ec == 7)
    if cnt7:
        geom_layer, warstwa_fallback = cnt7.most_common(1)[0][0], False
    else:
        geom_layer = Counter(e.dxf.layer for e, _ in picked).most_common(1)[0][0]
        warstwa_fallback = True
        uwagi.append(f"detect_geom_layer: zero koloru 7 w bbox -> fallback warstwa "
                     f"GEOM = '{geom_layer}' (geometria na nietypowym kolorze - "
                     f"SL40061302 = kolor 2)")

    listy = {name: [e for e, ec in picked if ec == kol] for name, kol in TRYBY_KOLOR.items()}
    listy["all"] = [e for e, _ in picked]
    listy["warstwa_geom"] = [e for e, _ in picked if e.dxf.layer == geom_layer]

    per_tryb, detale = {}, {}
    for name, ents in listy.items():
        if not ents:
            per_tryb[name] = 0
            detale[name] = dict(n_ents=0, interior=0, circles_dedup=0, outer=0,
                                dangles=0, cuts=0, flags=["brak encji w trybie"])
            continue
        n, det = count_interior_contours_shapely(ents, sagitta=sagitta, snap_tol=snap_tol)
        per_tryb[name] = n
        detale[name] = dict(n_ents=len(ents), interior=n, circles_dedup=det["circles_dedup"],
                            outer=det["outer"], dangles=det["dangles"], cuts=det["cuts"],
                            flags=det["flags"])

    # zrodlo_prawda: z trybow CZYSTYCH tylko te z n_outer==1 (jedna czesc = jedna
    # twarz zewn.); 'all' NIGDY (zawyza przez adnotacje/osie). remis -> priorytet TRYBY_CZYSTE.
    czyste = [t for t in TRYBY_CZYSTE if detale[t]["n_ents"] > 0 and detale[t]["outer"] == 1]
    if czyste:
        zrodlo_prawda = max(per_tryb[t] for t in czyste)
        tryb_znaleziony = next(t for t in TRYBY_CZYSTE if t in czyste and per_tryb[t] == zrodlo_prawda)
        rozne = {t: per_tryb[t] for t in czyste if per_tryb[t] != zrodlo_prawda and per_tryb[t] > 0}
        if rozne:
            uwagi.append(f"ROZBIEZNOSC trybow czystych: {tryb_znaleziony}={zrodlo_prawda} "
                         f"vs {rozne} -> ogladac render (zasada 6)")
    else:
        zrodlo_prawda = max(per_tryb[t] for t in TRYBY_CZYSTE)
        tryb_znaleziony = next(t for t in TRYBY_CZYSTE if per_tryb[t] == zrodlo_prawda)
        uwagi.append(f"ZADEN tryb czysty nie ma n_outer==1 (outer: "
                     f"{ {t: detale[t]['outer'] for t in TRYBY_CZYSTE} }) -> "
                     f"prawda={zrodlo_prawda} NIEPEWNA, obowiazkowe ogledziny")

    if per_tryb["all"] > zrodlo_prawda:
        uwagi.append(f"tryb 'all' zawyza: {per_tryb['all']} vs prawda {zrodlo_prawda} "
                     f"(+{per_tryb['all'] - zrodlo_prawda}) - adnotacje/ramki/osie LUB "
                     f"geometria na nietypowym kolorze (histogram: {dict(kolory)})")
    dw = detale[tryb_znaleziony]
    if dw["outer"] > 1:
        uwagi.append(f"tryb {tryb_znaleziony}: n_outer={dw['outer']}>1 - region lapie "
                     f"sasiadow albo czesc wieloczesciowa (ogladac render!)")

    return dict(per_tryb=per_tryb, zrodlo_prawda=zrodlo_prawda, tryb_znaleziony=tryb_znaleziony,
                diag=dict(n_ents_bbox=len(picked), bends=bends, kolory_geom=dict(kolory),
                          warstwa_geom=geom_layer, warstwa_fallback=warstwa_fallback,
                          per_tryb_detale=detale, uwagi=uwagi))


# ------------------------------- SWEEP ZLECENIA -------------------------------

def _znajdz_zrodlo(folder_rysunkow, zeinr):
    for nm in (f"{zeinr}_1_conv.dxf", f"{zeinr}_1.dxf", f"{zeinr}_conv.dxf", f"{zeinr}.dxf"):
        p = folder_rysunkow / nm
        if p.exists():
            return p
    return None


def sweep_zlecenie(folder_wynikow, folder_rysunkow, prog_delta=PROG_DELTA):
    """Sweep calego zlecenia. Zwraca (wiersze, braki_zrodla). Loguje braki GLOSNO."""
    folder_wynikow = Path(folder_wynikow)
    folder_rysunkow = Path(folder_rysunkow)
    wiersze, braki = [], []

    raporty = sorted(folder_wynikow.glob("*/*_raport.csv"))
    if not raporty:
        print(f"[SWEEP] BRAK raportow w {folder_wynikow} (wzorzec: <zeinr>/<zeinr>_raport.csv)")
        return wiersze, braki

    for rap in raporty:
        zeinr = rap.stem.replace("_raport", "")
        src = _znajdz_zrodlo(folder_rysunkow, zeinr)
        if src is None:
            print(f"[SWEEP] !! BRAK ZRODLA dla {zeinr} w {folder_rysunkow} "
                  f"- pozycje NIEDOMKNIETE (GLOSNO, zasada 15)")
            braki.append(zeinr)
            continue
        src_msp = ezdxf.readfile(src).modelspace()
        with open(rap, encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f, delimiter=";") if r.get("src_x1")]

        for r in rows:
            posn = r.get("posn", "?")
            try:
                box = tuple(float(r[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
            except (ValueError, KeyError):
                continue
            try:
                res = kontury_regionu_zrodla(src_msp, box)
            except ValueError as e:
                print(f"[SWEEP] {zeinr} p{posn}: {e} - pomijam (GLOSNO)")
                continue

            wyn_path = folder_wynikow / zeinr / r["file"] if r.get("file") else None
            if wyn_path and wyn_path.exists():
                wi, wdet = count_interior_contours_shapely(ezdxf.readfile(wyn_path).modelspace())
                niedomkniete = any(fl.startswith("NIEDOMKNIETE") for fl in wdet["flags"])
            else:
                wi, wdet, niedomkniete = None, None, False
                print(f"[SWEEP] {zeinr} p{posn}: brak pliku wyniku {r.get('file')} (GLOSNO)")

            delta = None if wi is None else res["zrodlo_prawda"] - wi
            if niedomkniete:
                semafor = "czerwony"
            elif delta is not None and delta >= prog_delta:
                semafor = "zolty"
            elif wi is None:
                semafor = "zolty"          # brak wyniku = do sprawdzenia
            else:
                semafor = "zielony"

            powod = ""
            if niedomkniete:
                powod = "WYNIK otwarty kontur (NIE na laser)"
            elif delta is not None and delta >= prog_delta:
                powod = (f"zgubione kontury: zrodlo={res['zrodlo_prawda']} wynik={wi} "
                         f"(delta={delta}, tryb={res['tryb_znaleziony']})")
            elif wi is None:
                powod = "brak pliku wyniku"
            if res["diag"]["uwagi"]:
                powod = (powod + " | " if powod else "") + " ; ".join(res["diag"]["uwagi"])

            wiersze.append(dict(
                zeinr=zeinr, posn=posn, file=r.get("file", ""),
                zrodlo=res["zrodlo_prawda"], tryb=res["tryb_znaleziony"], wynik=wi,
                delta=delta, semafor=semafor,
                col7=res["per_tryb"]["col7"], col2=res["per_tryb"]["col2"],
                col4=res["per_tryb"]["col4"], all=res["per_tryb"]["all"],
                warstwa_geom=res["per_tryb"]["warstwa_geom"], powod=powod))

    return wiersze, braki


def _zapisz_raport(wiersze, zlecenie):
    RAPORTY.mkdir(parents=True, exist_ok=True)
    out = RAPORTY / f"sweep_{zlecenie}.csv"
    pola = ["zeinr", "posn", "file", "zrodlo", "tryb", "wynik", "delta", "semafor",
            "col7", "col2", "col4", "all", "warstwa_geom", "powod"]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pola, delimiter=";")
        w.writeheader()
        for r in wiersze:
            w.writerow(r)
    return out


def main(argv):
    if len(argv) < 2 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    folder_wynikow, folder_rysunkow = argv[0], argv[1]
    prog = PROG_DELTA
    if "--prog" in argv:
        prog = int(argv[argv.index("--prog") + 1])

    zlecenie = Path(folder_wynikow).name
    wiersze, braki = sweep_zlecenie(folder_wynikow, folder_rysunkow, prog)
    if not wiersze:
        print("[SWEEP] brak pozycji do oceny")
        return 3

    out = _zapisz_raport(wiersze, zlecenie)
    flagi = [w for w in wiersze if w["semafor"] != "zielony"]
    # od NAJWIEKSZYCH roznic (zasada 6): czerwony przed zoltym, potem delta malejaco
    flagi.sort(key=lambda w: (w["semafor"] != "czerwony", -(w["delta"] or 0)))

    print(f"\n=== SWEEP {zlecenie}: {len(wiersze)} pozycji, {len(flagi)} flag, "
          f"{len(braki)} braki zrodla ===")
    print(f"Raport: {out}")
    print(f"Prog flagi: delta>={prog} konturow (+ NIEDOMKNIETE=czerwony)\n")
    print(f"{'semafor':>8}  {'pozycja':22} {'zrodlo':>6} {'wynik':>5} {'delta':>5}  powod")
    for w in flagi:
        print(f"{w['semafor']:>8}  {w['zeinr']+'_p'+str(w['posn']):22} {w['zrodlo']:>6} "
              f"{'' if w['wynik'] is None else w['wynik']:>5} "
              f"{'' if w['delta'] is None else w['delta']:>5}  {w['powod'][:90]}")
    if not flagi:
        print("  (brak flag - wszystkie pozycje zielone)")
    return 1 if flagi or braki else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
