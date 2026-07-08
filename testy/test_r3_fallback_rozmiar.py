# -*- coding: utf-8 -*-
"""Test R3 — awaryjny wybor widoku (brak prop-matchu) bierze NAJWIEKSZY nie-izometryczny
klaster, nie sam argmax geo.

Cel (RYZYKO 3, audyt rankingu): w sciezce awaryjnej rankingu (extract_position, gdy ZADEN
klaster nie pasuje proporcja do wykazu) sam argmax geo wybieral DROBNY klaster o wysokim
geo (detal 40x16, symbol 22x22) zamiast prawdziwego rozwiniecia - bo kara open_ends za
wchloniete linie wymiarowe zaniza geo duzej czesci. `_pick_fallback_geo`: sposrod
nie-izometrycznych (geo > PROG_ANTY) wybiera NAJWIEKSZY powierzchnia.

Golden: 4 izometryki (targety z test_detektor_rozwiniecia: target_GOOD = rozwiniecie).
Selekcja jest niezalezna od dims (uzywa geo + pole) -> test podaje dims neutralne.

Uzycie:  python testy\\test_r3_fallback_rozmiar.py     (exit 0 = PASS)
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
D_NEUTRAL = (9999.0, 9999.0)   # geo/pole niezalezne od dims -> neutralne wystarczy


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# (nazwa, plik, target_GOOD (max,min), czy R3 zmienil wybor vs stary argmax-geo)
CASES = [
    ("SL40047020", GOLDEN / "SL40047020_p1_izometryk" / "wejscie" / "SL40047020_1.dxf",
     (61.9, 53.2), True),
    ("SL10582652", GOLDEN / "SL10582652_p1_widok_z_gieciem" / "wejscie" / "SL10582652_1_conv.dxf",
     (281.0, 44.0), True),
    ("SL10582797", GOLDEN / "SL10582797_p1_rzut_boczny_zamiast_rozwiniecia" / "wejscie" / "SL10582797_1_conv.dxf",
     (106.7, 20.6), False),
    ("SL40091010", GOLDEN / "SL40091010_p1_izometryk" / "wejscie" / "SL40091010_1.dxf",
     (194.3, 84.3), False),
]


def _clusters(path):
    doc = ezdxf.readfile(str(path))
    ents = list(doc.modelspace())
    geom, axis, dashed, bend, annot = ep.partition(ents)
    clusters = ep.cluster_entities(geom + dashed)
    bt = det.bend_texts_from_ents(ents)
    return clusters, bt


def _bliski(c, target, tol_rel=0.05):
    cmax, cmin = max(c["w"], c["h"]), min(c["w"], c["h"])
    tmax, tmin = target
    return (abs(cmax - tmax) <= max(tol_rel * tmax, 2.0) and
            abs(cmin - tmin) <= max(tol_rel * tmin, 2.0))


def main():
    for nazwa, path, target, zmienil in CASES:
        clusters, bt = _clusters(path)

        # NOWY wybor - _pick_fallback_geo ma trafic w target_GOOD (rozwiniecie)
        c, geo_c = ep._pick_fallback_geo(clusters, D_NEUTRAL, bt)
        check(f"{nazwa}_wybiera_rozwiniecie", _bliski(c, target),
              f"wybrano {max(c['w'],c['h']):.1f}x{min(c['w'],c['h']):.1f} "
              f"(geo{geo_c:+d}), oczekiwano ~{target[0]}x{target[1]}")

        # STARY argmax-geo - dla 47020/652 mial brac ZLY (dowod ze R3 realne i naprawione)
        kand = [cc for cc in clusters if len(cc["entities"]) >= 8] or clusters[:1]
        stary = max(kand, key=lambda cc: det.score_klastra(cc, clusters, D_NEUTRAL, bt)[0])
        if zmienil:
            check(f"{nazwa}_stary_bral_zly", not _bliski(stary, target),
                  f"stary argmax-geo wzial {max(stary['w'],stary['h']):.1f}x"
                  f"{min(stary['w'],stary['h']):.1f} - mial NIE trafic w target (R3)")
        else:
            check(f"{nazwa}_bez_zmiany", _bliski(stary, target),
                  f"stary tez trafial w target (R3 nie dotyczy) - "
                  f"{max(stary['w'],stary['h']):.1f}x{min(stary['w'],stary['h']):.1f}")

    print(f"CHECKS={CHECKS}  FAILS={len(FAILS)}")
    for f in FAILS:
        print("  FAIL:", f)
    if FAILS:
        print("\n[R3 CZERWONY] — sprawdz _pick_fallback_geo.")
        sys.exit(1)
    print("[R3 ZIELONY] — awaryjny wybor bierze najwiekszy nie-izometryczny (47020+652 naprawione).")
    sys.exit(0)


if __name__ == "__main__":
    main()
