# -*- coding: utf-8 -*-
"""Testy BRAMKI 5 - bilans konturow wewnetrznych (shapely.polygonize).

Brama do produkcji dla produkcja/kontrola/bilans_konturow.py. Sprawdza:
  - dokladne liczby na 7 wzorcach golden (ground truth z opis.md),
  - flagi puste na czystych wzorcach,
  - INWARIANT LUSTRA: scale(-1,1,1) daje te sama liczbe (cyklomatyka tu robi off-by-one),
  - INWARIANT JITTERU: przesuniecie o duzy wektor nie zmienia liczby
    (cyklomatyka round(0,1) gubi kontur - to sedno root-fixu),
  - DEDUP: dolozony okrag wspolsrodkowy nie zmienia bilansu (duble nie maskuja),
  - bilans zrodlo-vs-wynik: identyczne = zielony, brak cechy = zolty.

Uzycie:  python testy\\test_bramka5.py     (exit 0 = PASS)
"""
import io
import sys
from pathlib import Path

import ezdxf
from ezdxf.math import Matrix44

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
sys.path.insert(0, str(HERE.parent / "produkcja" / "kontrola"))
from bilans_konturow import count_interior_contours_shapely, bilans  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# (sciezka wzgledem golden, ground_truth_interior)
WZORCE = [
    ("SL10582608_owal_odseparowany_klaster/wzorzec/SL10582608_p1.dxf", 12),
    ("SL10596945_fasola_odseparowana/wzorzec/SL10596945_p3.dxf", 4),
    ("SL10596945_fasola_odseparowana/wzorzec/SL10596945_p4_LUSTRO_z_p3.dxf", 4),
    ("SL10599245_owal_spline_odseparowany/wzorzec/SL10599245_p1.dxf", 21),
    ("SL10599245_p6p7_skala_ratunkowa/wzorzec/SL10599245_p6.dxf", 1),
    ("SL10599245_p6p7_skala_ratunkowa/wzorzec/SL10599245_p7.dxf", 1),
    ("SL40061302_sloty_odseparowane/wzorzec/SL40061302_p1.dxf", 3),
]


def _msp(f):
    return ezdxf.readfile(f).modelspace()


def _transformed(f, m):
    msp = ezdxf.readfile(f).modelspace()
    for e in msp:
        try:
            e.transform(m)
        except Exception:
            pass
    return msp


def main():
    print("=== TESTY BRAMKA 5 (bilans konturow wewnetrznych, shapely) ===\n")
    for rel, gt in WZORCE:
        f = GOLDEN / rel
        name = f.stem
        n, det = count_interior_contours_shapely(_msp(f))
        check(f"{name} liczba", n == gt, f"kontury={n} != GT={gt}")
        check(f"{name} bez flag", not det["flags"], f"flagi={det['flags']}")

        # inwariant lustra
        nm, _ = count_interior_contours_shapely(_transformed(f, Matrix44.scale(-1, 1, 1)))
        check(f"{name} lustro", nm == n, f"lustro={nm} != oryginal={n} (off-by-one!)")

        # inwariant jitteru (cyklomatyka tu pada)
        nj, _ = count_interior_contours_shapely(
            _transformed(f, Matrix44.translate(55555.55, 44444.45, 0)))
        check(f"{name} jitter", nj == n, f"jitter={nj} != oryginal={n} (off-by-one!)")
        print(f"  {name:38} kontury={n:>3} (GT={gt}) lustro={nm} jitter={nj}  "
              f"{'OK' if n == gt == nm == nj and not det['flags'] else 'FAIL'}")

    # DEDUP: dolozony okrag wspolsrodkowy nie zmienia bilansu ani nie zawyza konturow
    print()
    f = GOLDEN / WZORCE[1][0]        # SL10596945_p3 (GT=4, 2 okregi)
    doc = ezdxf.readfile(f)
    msp = doc.modelspace()
    c0 = next(e for e in msp if e.dxftype() == "CIRCLE")
    msp.add_circle(c0.dxf.center, c0.dxf.radius + 0.85)   # dubel wspolsrodkowy O13->O14.7
    nd, dd = count_interior_contours_shapely(msp)
    check("dedup interior", nd == 4, f"interior={nd} != 4 (dubel zawyzyl/zamaskowal)")
    check("dedup okregi", dd["circles_dedup"] == 2,
          f"circles_dedup={dd['circles_dedup']} != 2 (raw={dd['circles_raw']})")
    print(f"  dedup: p3 + dubel wspolsrodkowy -> interior={nd} (cel 4), "
          f"okregi raw={dd['circles_raw']} dedup={dd['circles_dedup']} (cel 2)")

    # BILANS: identyczne = zielony; brak cechy = zolty
    p3 = GOLDEN / WZORCE[1][0]
    p6 = GOLDEN / WZORCE[4][0]
    b_ok = bilans(_msp(p3), _msp(p3))
    b_brak = bilans(_msp(p3), _msp(p6))       # wynik ma 1 zamiast 4 = zgubione cechy
    check("bilans zielony", b_ok["semafor"] == "zielony",
          f"semafor={b_ok['semafor']} powody={b_ok['powody']}")
    check("bilans zolty", b_brak["semafor"] == "zolty",
          f"semafor={b_brak['semafor']} (delta={b_brak['delta']})")
    print(f"  bilans: p3-vs-p3={b_ok['semafor']}  p3-vs-p6={b_brak['semafor']} "
          f"(delta={b_brak['delta']})")

    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== BRAMKA 5: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== BRAMKA 5: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
