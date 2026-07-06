# -*- coding: utf-8 -*-
"""Testy KATEGORII 4 (adnotacje tekstowe): produkcja/silniki/v2/kategorie/adnotacje.py.

Wtyczka szukania po dymkach numeru pozycji + hint lustra. Konserwatywna: kandydat
tylko gdy wymiar klastra pasuje do wykazu (filtr chroni przed zlym babelkiem).

A) babelek "7" -> najblizszy klaster, skala z wykazu, kategoria adnotacje;
B) zly wymiar wykazu -> BRAK kandydata (filtr wymiarem);
C) brak dymka pozycji -> [];
D) format "Pos. 7" tez lapie;
E) adnotacja gespiegelt -> kandydat NIEPEWNY (do potwierdzenia).

Uzycie:  python testy\\test_adnotacje.py     (exit 0 = PASS)
"""
import io
import sys
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "produkcja" / "silniki"))
from v2 import wspolne  # noqa: E402
from v2.kategorie import adnotacje  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _doc(tekst_babelka, pt_babelka=(50, 60), extra_teksty=None):
    """Doc: prostokat 100x50 (widok) + TEXT dymka; opcjonalne dodatkowe teksty."""
    doc = ezdxf.new(dxfversion="AC1021")
    m = doc.modelspace()
    m.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
    if tekst_babelka is not None:
        m.add_text(tekst_babelka).set_placement(pt_babelka)
    for t, p in (extra_teksty or []):
        m.add_text(t).set_placement(p)
    return doc


def test_babelek_trafia():
    print("--- A) babelek numeru -> klaster + skala ---")
    geo = wspolne.Geometria(_doc("7"))
    # prostokat 100x50 na papierze, wykaz 500x250 -> skala 5
    res = adnotacje.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0)})
    check("A0 jeden kandydat", len(res) == 1, f"n={len(res)}")
    if res:
        k = res[0]
        check("A1 skala ~5", abs(k.skala - 5.0) < 0.05, f"skala={k.skala}")
        check("A2 kategoria adnotacje", k.kategoria == "adnotacje", k.kategoria)
        check("A3 technika babelek", k.technika.startswith("babelek-poz7"), k.technika)
        check("A4 nie niepewny", k.niepewny is False, k.niepewny)
        print(f"  kandydat: skala={k.skala} technika={k.technika} pewnosc={k.pewnosc}")


def test_filtr_wymiarem():
    print("\n--- B) zly wymiar wykazu -> filtr (brak kandydata) ---")
    geo = wspolne.Geometria(_doc("7"))
    res = adnotacje.znajdz(geo, {"posn": 7, "dims": (9999.0, 12.0)})  # nie pasuje
    check("B brak kandydata przy zlym wymiarze", res == [], f"n={len(res)}")
    print(f"  zly wymiar -> {len(res)} kandydatow (filtr dziala)")


def test_brak_babelka():
    print("\n--- C) brak dymka pozycji -> [] ---")
    geo = wspolne.Geometria(_doc("99"))          # dymek innej pozycji
    res = adnotacje.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0)})
    check("C brak kandydata bez dymka poz.7", res == [], f"n={len(res)}")
    print(f"  dymek '99' dla poz.7 -> {len(res)} kandydatow")


def test_format_pos():
    print("\n--- D) format 'Pos. 7' ---")
    geo = wspolne.Geometria(_doc("Pos. 7"))
    res = adnotacje.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0)})
    check("D 'Pos. 7' lapie", len(res) == 1, f"n={len(res)}")


def test_lustro_hint():
    print("\n--- E) adnotacja gespiegelt -> niepewny ---")
    geo = wspolne.Geometria(_doc("7", extra_teksty=[("gespiegelt", (10, 70))]))
    res = adnotacje.znajdz(geo, {"posn": 7, "dims": (500.0, 250.0)})
    check("E kandydat jest", len(res) == 1, f"n={len(res)}")
    if res:
        check("E niepewny (lustro)", res[0].niepewny is True, res[0].niepewny)
        check("E technika gespiegelt", "gespiegelt" in res[0].technika, res[0].technika)
        print(f"  technika={res[0].technika} niepewny={res[0].niepewny}")


def main():
    print("=== TESTY KATEGORII 4 (adnotacje) ===\n")
    test_babelek_trafia()
    test_filtr_wymiarem()
    test_brak_babelka()
    test_format_pos()
    test_lustro_hint()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== ADNOTACJE: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== ADNOTACJE: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
