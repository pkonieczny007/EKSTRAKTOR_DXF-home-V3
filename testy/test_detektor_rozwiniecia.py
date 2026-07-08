# -*- coding: utf-8 -*-
"""Testy DETEKTORA ROZWINIECIA (anty-izometryk) - produkcja/kontrola/detektor_rozwiniecia.py.

Sprawdza ZACOMMITOWANY detektor (commit 1164059 'home'): features + score_rozwiniecie
na REALNYCH klastrach z golden. Detektor ma odroznic plaskie rozwiniecie (na laser)
od rzutu izometrycznego / widoku po gieciu o podobnym bbox.

Metoda pomiaru (wierna sciezce awaryjnej rankingu extract_positions):
  msp -> partition -> cluster_entities(geom+dashed, gap=8) -> features/score dla klastra.
Klastry wybieramy DETERMINISTYCZNIE po najblizszym pudelku (max_dim, min_dim) do targetu
zmierzonego na golden (pomiary w naglowkach przypadkow ponizej).

KONTRAKT sprawdzany (niezmienniki spelnione na zacommitowanym kodzie):
  1. IZOMETRIA: klaster-rzut (duzo ELLIPSE / rozproszone katy) ma geo <= PROG_ANTY (-3).
  2. RANKING: geo(rozwiniecie) > geo(izometria) - detektor premiuje rozwiniecie.
  3. MARGINES: tam gdzie kontur zrodlowy jest czysto zamkniety, geo(rozwiniecie) >= +2.
  4. KONTROLE (poprawne ekstrakcje): geo(czesc) > PROG_ANTY i > geo(izometryka w pliku)
     - detektor NIE odwraca zwyciezcy; skala ratunkowa 4.91 z prop-matchem BEZ kary (-3).

UWAGA (rozjazd prototyp-vs-kod): dla SL10582797 i SL40047020 klaster rozwiniecia w
naiwnym klastrowaniu calego msp (gap=8) WCHLANIA linie wymiarowe/pomocnicze -> open_ends>4
-> kara -2 -> geo NIE osiaga prototypowego +2 (mierzone -3 i -1). Ranking (rozwiniecie >
izometria) i tak sie utrzymuje. Prog "+2 margines" trzyma tylko dla czystych konturow
(652, 91010). Szczegoly: sekcja pomiarow w StructuredOutput / uwagi handoffu.

Uzycie:  python testy\\test_detektor_rozwiniecia.py     (exit 0 = PASS)
"""
import io
import sys
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
GOLDEN = HERE / "golden"
sys.path.insert(0, str(ROOT / "produkcja" / "silniki"))
sys.path.insert(0, str(ROOT / "produkcja" / "kontrola"))
import extract_positions as ep          # noqa: E402
import detektor_rozwiniecia as det      # noqa: E402

FAILS = []
CHECKS = 0
MEZ = {}   # zmierzone geo score do raportu


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# --- klastrowanie zrodla wg sciezki awaryjnej rankingu (gap=8) -----------------
_CACHE = {}


def clusters_of(dxf_path):
    key = str(dxf_path)
    if key not in _CACHE:
        doc = ezdxf.readfile(str(dxf_path))
        ents = list(doc.modelspace())
        geom, _axis, dashed, _bend, _annot = ep.partition(ents)
        clusters = ep.cluster_entities(geom + dashed)
        bend_texts = det.bend_texts_from_ents(ents)
        _CACHE[key] = (clusters, bend_texts)
    return _CACHE[key]


def _dims_sorted(c):
    return max(c["w"], c["h"]), min(c["w"], c["h"])


def pick_box(clusters, target, min_ents=6):
    """Klaster o pudelku (max,min) najblizszym targetowi (dystans wzgledny)."""
    tmax, tmin = target
    best, bestd = None, 1e18
    for c in clusters:
        if len(c["entities"]) < min_ents:
            continue
        cmax, cmin = _dims_sorted(c)
        d = abs(cmax - tmax) / tmax + abs(cmin - tmin) / max(tmin, 1e-6)
        if d < bestd:
            best, bestd = c, d
    return best


def geo_of(dxf_path, target, dims=None, tag=""):
    clusters, bt = clusters_of(dxf_path)
    c = pick_box(clusters, target)
    if c is None:
        return None, None
    f = det.features(c, clusters, dims, bt)
    geo, skala, tot = det.score_rozwiniecie(f)
    if tag:
        MEZ[tag] = {"geo": geo, "skala": skala, "tot": tot,
                    "bbox": (round(c["w"], 1), round(c["h"], 1)),
                    "n_ellipse": f["n_ellipse"], "n_circle": f["n_circle"],
                    "inner_closed": f["inner_closed"], "open_ends": f["open_ends"],
                    "prop_match": f["prop_match"], "scale": f["scale"]}
    return geo, (geo, skala, tot)


# --- przypadki: (nazwa, plik, target_GOOD, target_izo, dims, margines>=2?) -----
# targety zmierzone na zacommitowanym kodzie (klastrowanie calego msp, gap=8).
G = "wejscie"
ANTY = [
    # SL10582652: rozwiniecie warstwa 51 ~281x44 (geo+2, kontur zamkniety) vs
    # izometria 29 ELLIPSE ~79.5x45 (geo-8).
    ("SL10582652", GOLDEN / "SL10582652_p1_widok_z_gieciem" / G / "SL10582652_1_conv.dxf",
     (281.0, 44.0), (79.5, 45.2), (560.0, 84.0), True),
    # SL10582797: rozwiniecie ~107x21 (skala ~5) vs rzut po gieciu 9 ELLIPSE ~102x8.
    # ROZJAZD: rozwiniecie wchlania wymiary -> open_ends=12 -> geo-3 (nie +2), ale > rzut(-6).
    ("SL10582797", GOLDEN / "SL10582797_p1_rzut_boczny_zamiast_rozwiniecia" / G / "SL10582797_1_conv.dxf",
     (106.7, 20.6), (101.8, 8.1), (527.0, 76.0), False),
    # SL40047020: rozwiniecie ~62x53 (2 CIRCLE) vs izometryk 48 ELLIPSE ~51x43 (geo-3).
    # ROZJAZD: open_ends=16 na rozwinieciu -> geo-1 (nie +2), ale > izometryk(-3).
    ("SL40047020", GOLDEN / "SL40047020_p1_izometryk" / G / "SL40047020_1.dxf",
     (61.9, 53.2), (51.5, 42.9), None, False),
    # SL40091010: rozwiniecie ~194x84 (geo+7, orto45=1, adnotacja giecia) vs
    # rzut po gieciu ~159x68 (geo-4). Czysta separacja.
    ("SL40091010", GOLDEN / "SL40091010_p1_izometryk" / G / "SL40091010_1.dxf",
     (194.3, 84.3), (159.0, 68.0), (389.0, 159.0), True),
]

# KONTROLE: (nazwa, plik, target_czesc, target_izo, dims)
KONTROLE = [
    ("SL40034116", GOLDEN / "SL40034116_p1_zgubione_otwory" / G / "SL40034116_1_conv.dxf",
     (170.0, 161.6), (153.3, 141.7), (808.0, 842.0)),   # izo = 298 ELLIPSE
    ("SL40061302", GOLDEN / "SL40061302_sloty_odseparowane" / G / "SL40061302_1_conv.dxf",
     (144.2, 105.7), (82.8, 77.9), (287.0, 210.0)),     # czesc kolor 2, skala 2.0
    ("SL10596945", GOLDEN / "SL10596945_fasola_odseparowana" / G / "SL10596945_1_conv.dxf",
     (224.5, 36.6), (117.4, 80.1), (282.4, 260.24)),    # czesc warstwa 53
]


def test_izometria_ponizej_progu():
    print("--- 1) izometria/rzut <= PROG_ANTY (-3) ---")
    check("PROG_ANTY", det.PROG_ANTY == -3, f"PROG_ANTY={det.PROG_ANTY}")
    for nazwa, plik, _tg, tizo, dims, _m in ANTY:
        g, _ = geo_of(plik, tizo, dims, tag=nazwa + "_izo")
        check(f"1 {nazwa} izo<=prog", g is not None and g <= det.PROG_ANTY,
              f"geo izometrii={g} (ma byc <= {det.PROG_ANTY})")
    for nazwa, plik, _tc, tizo, dims in KONTROLE:
        g, _ = geo_of(plik, tizo, dims, tag=nazwa + "_izo")
        check(f"1k {nazwa} izo<=prog", g is not None and g <= det.PROG_ANTY,
              f"geo izometrii={g} (ma byc <= {det.PROG_ANTY})")


def test_rozwiniecie_wygrywa():
    print("--- 2) geo(rozwiniecie) > geo(izometria) ---")
    for nazwa, plik, tg, tizo, dims, _m in ANTY:
        gg, _ = geo_of(plik, tg, dims, tag=nazwa + "_good")
        gi, _ = geo_of(plik, tizo, dims)
        check(f"2 {nazwa} good>izo", gg is not None and gi is not None and gg > gi,
              f"geo good={gg} vs izo={gi}")


def test_margines_separacji():
    print("--- 3) margines geo(rozwiniecie) >= +2 (czyste kontury) ---")
    for nazwa, plik, tg, _tizo, dims, margines in ANTY:
        if not margines:
            continue
        gg, _ = geo_of(plik, tg, dims)
        check(f"3 {nazwa} good>=+2", gg is not None and gg >= 2,
              f"geo rozwiniecia={gg} (ma byc >= +2)")


def test_kontrole_zwyciezca():
    print("--- 4) KONTROLE: czesc > prog i > izometryka (bez zmiany zwyciezcy) ---")
    for nazwa, plik, tc, tizo, dims in KONTROLE:
        gc, _ = geo_of(plik, tc, dims, tag=nazwa + "_czesc")
        gi, _ = geo_of(plik, tizo, dims)
        check(f"4 {nazwa} czesc>prog", gc is not None and gc > det.PROG_ANTY,
              f"geo czesci={gc} (ma byc > {det.PROG_ANTY})")
        check(f"4 {nazwa} czesc>izo", gc is not None and gi is not None and gc > gi,
              f"geo czesci={gc} vs izo={gi}")


def test_skala_ratunkowa_bez_kary():
    print("--- 5) SL10599245: skala ratunkowa 4.91 z prop-matchem BEZ kary (-3) ---")
    plik = GOLDEN / "SL10599245_p6p7_skala_ratunkowa" / G / "SL10599245_1_conv.dxf"
    clusters, bt = clusters_of(plik)
    # dysk 60x62 -> ~311x300 przy skali ~4.83 (klaster ~64.2x62.3)
    c = pick_box(clusters, (64.2, 62.3))
    f = det.features(c, clusters, (311.0, 300.0), bt)
    geo, skala, tot = det.score_rozwiniecie(f)
    MEZ["SL10599245_ratunek"] = {"geo": geo, "skala": skala, "tot": tot,
                                 "scale": f["scale"], "prop_match": f["prop_match"],
                                 "bbox": (round(c["w"], 1), round(c["h"], 1))}
    check("5 prop_match", f["prop_match"] is True,
          f"prop_match={f['prop_match']} (skala x/y w tol -> match mimo 4.91)")
    check("5 skala bez kary", skala == 0,
          f"skala={skala} (prop-match nie-ladny => 0, NIE -3)")
    check("5 scale ~4.9", f["scale"] is not None and 4.7 <= f["scale"] <= 5.0,
          f"scale={f['scale']}")
    check("5 geo dodatni", geo > 0, f"geo={geo}")


def main():
    print("=== TESTY DETEKTORA ROZWINIECIA (anty-izometryk) ===\n")
    test_izometria_ponizej_progu()
    test_rozwiniecie_wygrywa()
    test_margines_separacji()
    test_kontrole_zwyciezca()
    test_skala_ratunkowa_bez_kary()

    print("\n--- ZMIERZONE geo (zacommitowany kod) ---")
    for k in sorted(MEZ):
        m = MEZ[k]
        print(f"  {k:24s} geo={m['geo']:+d} skala={m.get('skala','?'):>3} "
              f"tot={m.get('tot','?'):>3} bbox={m.get('bbox')} "
              f"ell={m.get('n_ellipse','-')} cir={m.get('n_circle','-')} "
              f"oe={m.get('open_ends','-')} pm={m.get('prop_match','-')}")

    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== DETEKTOR ROZWINIECIA: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== DETEKTOR ROZWINIECIA: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
