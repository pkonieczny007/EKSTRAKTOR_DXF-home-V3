# -*- coding: utf-8 -*-
"""Testy KATEGORII 5 (korpus/archiwum): produkcja/silniki/v2/kategorie/korpus.py.

Dopasowanie pozycji do archiwum po SYGNATURZE geometrycznej (n_circ dedup, n_geom,
ratio). Konserwatywna: [] gdy brak korpusu/wpisu; rozjazd sygnatury = NIEPEWNY.

A) sygnatura zgodna (n_circ + n_geom) -> kandydat korpus-zgodny, pewnosc 0.7;
B) rozjazd sygnatury (inny n_circ) -> kandydat NIEPEWNY, pewnosc 0.35;
C) dopasowanie po WYMIARACH gdy brak klucza zeinr+posn;
D) brak korpusu / brak wpisu -> [].

Uzycie:  python testy\\test_korpus.py     (exit 0 = PASS)
"""
import csv
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "produkcja" / "silniki"))
from v2 import wspolne  # noqa: E402
from v2.kategorie import korpus  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _doc():
    """Prostokat 100x50 + 2 okregi (jeden z dublem wspolsrodkowym) -> n_circ=2, n_geom=4."""
    doc = ezdxf.new(dxfversion="AC1021")
    m = doc.modelspace()
    m.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
    m.add_circle((25, 25), 5)
    m.add_circle((25, 25), 6)      # wspolsrodkowy dubel -> dedup do 1
    m.add_circle((75, 25), 5)
    return wspolne.Geometria(doc)


def _korpus_csv(path, n_circ=2, n_geom=4, zeinr="Z", posn=7):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";",
                           fieldnames=["zeinr", "posn", "dim_max", "dim_min", "n_circ", "n_geom"])
        w.writeheader()
        w.writerow(dict(zeinr=zeinr, posn=posn, dim_max=500, dim_min=250,
                        n_circ=n_circ, n_geom=n_geom))


def test_zgodna():
    print("--- A) sygnatura zgodna ---")
    tmp = Path(tempfile.mkdtemp(prefix="korp_"))
    try:
        kc = tmp / "sygnatury.csv"
        _korpus_csv(kc, n_circ=2, n_geom=4)
        geo = _doc()
        res = korpus.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0), "zeinr": "Z"},
                            profil={"korpus": str(kc)})
        check("A0 kandydat", len(res) == 1, f"n={len(res)}")
        if res:
            check("A1 zgodny", res[0].technika == "korpus-zgodny", res[0].technika)
            check("A2 pewnosc 0.7", abs(res[0].pewnosc - 0.7) < 1e-6, res[0].pewnosc)
            check("A3 nie niepewny", res[0].niepewny is False, res[0].niepewny)
            print(f"  {res[0].technika} pewnosc={res[0].pewnosc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_rozjazd():
    print("\n--- B) rozjazd sygnatury (inny n_circ) -> niepewny ---")
    tmp = Path(tempfile.mkdtemp(prefix="korp_r_"))
    try:
        kc = tmp / "sygnatury.csv"
        _korpus_csv(kc, n_circ=5, n_geom=4)      # archiwum ma 5 okregow, rysunek 2
        geo = _doc()
        res = korpus.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0), "zeinr": "Z"},
                            profil={"korpus": str(kc)})
        check("B0 kandydat", len(res) == 1, f"n={len(res)}")
        if res:
            check("B1 rozjazd technika", "rozjazd" in res[0].technika, res[0].technika)
            check("B2 niepewny", res[0].niepewny is True, res[0].niepewny)
            check("B3 pewnosc niska", res[0].pewnosc < 0.5, res[0].pewnosc)
            print(f"  {res[0].technika} niepewny={res[0].niepewny}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_po_wymiarach():
    print("\n--- C) dopasowanie po wymiarach (bez klucza) ---")
    tmp = Path(tempfile.mkdtemp(prefix="korp_w_"))
    try:
        kc = tmp / "sygnatury.csv"
        _korpus_csv(kc, n_circ=2, n_geom=4, zeinr="Z", posn=7)
        geo = _doc()
        # inny zeinr/posn, ale wymiar pasuje -> match po wymiarach
        res = korpus.znajdz(geo, {"posn": 99, "dims": (500.0, 250.0), "zeinr": "INNY"},
                            profil={"korpus": str(kc)})
        check("C dopasowanie po wymiarach", len(res) == 1, f"n={len(res)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_brak():
    print("\n--- D) brak korpusu / brak wpisu -> [] ---")
    geo = _doc()
    # brak korpusu (sciezka nieistniejaca)
    r1 = korpus.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0), "zeinr": "Z"},
                       profil={"korpus": "C:/nie/ma/takiego.csv"})
    check("D0 brak korpusu -> []", r1 == [], f"n={len(r1)}")
    # korpus jest, ale wymiar nie pasuje do zadnego wpisu
    tmp = Path(tempfile.mkdtemp(prefix="korp_b_"))
    try:
        kc = tmp / "sygnatury.csv"
        _korpus_csv(kc)
        r2 = korpus.znajdz(geo, {"posn": 3, "dims": (9999.0, 8888.0), "zeinr": "X"},
                           profil={"korpus": str(kc)})
        check("D1 brak wpisu -> []", r2 == [], f"n={len(r2)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("  brak korpusu i brak wpisu -> [] (kategoria milczy)")


def main():
    print("=== TESTY KATEGORII 5 (korpus) ===\n")
    test_zgodna()
    test_rozjazd()
    test_po_wymiarach()
    test_brak()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== KORPUS: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== KORPUS: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
