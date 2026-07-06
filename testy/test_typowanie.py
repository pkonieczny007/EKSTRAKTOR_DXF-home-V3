# -*- coding: utf-8 -*-
"""Testy TYPOWANIA (Etap 4p3, decyzja usera: progi/podpowiedzi, NIE ograniczaj silnikow):
produkcja/typowanie.py::profil_rysunku + okresl_typy.

A) lantek_1nn (warstwa 101) -> typ wykryty + profil spodziewane_lustra/warstwa_pozycyjna;
B) domyslny (geometria luzem) -> profil = defaulty (spodziewane_lustra False, geom_kolory None);
C) scalanie profili wielu typow (sbm + lantek) - laczy pola, najpewniejszy wygrywa konflikt;
D) PROFIL_DOMYSLNY kompletny.

Uzycie:  python testy\\test_typowanie.py     (exit 0 = PASS)
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "produkcja"))
import typowanie as tp  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _lantek_dxf(path):
    doc = ezdxf.new(dxfversion="AC1021")
    m = doc.modelspace()
    for i in range(12):
        m.add_line((0, i), (100, i), dxfattribs={"layer": "101"})
    doc.saveas(path)


def _plain_dxf(path):
    doc = ezdxf.new(dxfversion="AC1021")
    m = doc.modelspace()
    for i in range(12):
        m.add_line((0, i), (100, i), dxfattribs={"layer": "0"})
    doc.saveas(path)


def test_lantek():
    print("--- A) lantek_1nn: typ + profil ---")
    tmp = Path(tempfile.mkdtemp(prefix="typ_"))
    try:
        f = tmp / "lantek.dxf"
        _lantek_dxf(f)
        typy = tp.okresl_typy(f)
        check("A0 lantek wykryty", any(t["typ"] == "lantek_1nn" for t in typy),
              [t["typ"] for t in typy])
        prof = tp.profil_rysunku(f)
        check("A1 warstwa_pozycyjna", prof["warstwa_pozycyjna"] is True, prof["warstwa_pozycyjna"])
        check("A2 spodziewane_lustra", prof["spodziewane_lustra"] is True, prof["spodziewane_lustra"])
        check("A3 giecie_kolor 6", prof["giecie_kolor"] == 6, prof["giecie_kolor"])
        check("A4 typy w profilu", "lantek_1nn" in prof["typy"], prof["typy"])
        print(f"  typy={prof['typy']} lustra={prof['spodziewane_lustra']} uwaga={prof['uwaga'][:40]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_domyslny():
    print("\n--- B) domyslny: profil = defaulty ---")
    tmp = Path(tempfile.mkdtemp(prefix="typ_d_"))
    try:
        f = tmp / "plain.dxf"
        _plain_dxf(f)
        prof = tp.profil_rysunku(f)
        check("B0 typ domyslny", prof["typy"] == ["domyslny"], prof["typy"])
        check("B1 bez luster", prof["spodziewane_lustra"] is False, prof["spodziewane_lustra"])
        check("B2 geom_kolory None (auto)", prof["geom_kolory"] is None, prof["geom_kolory"])
        check("B3 prog_sweep 1", prof["prog_sweep_delta"] == 1, prof["prog_sweep_delta"])
        print(f"  typy={prof['typy']} defaulty OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_scalanie():
    print("\n--- C) scalanie profili wielu typow ---")
    # najpewniejszy pierwszy (sbm), potem lantek
    typy = [{"typ": "sbm_kolorowa", "pewnosc": "wysoka", "powod": ""},
            {"typ": "lantek_1nn", "pewnosc": "srednia", "powod": ""}]
    prof = tp.profil_rysunku(None, typy=typy)
    check("C0 geom_kolory z sbm", prof["geom_kolory"] == [2, 7], prof["geom_kolory"])
    check("C1 cechy_odseparowane z sbm", prof["cechy_odseparowane"] is True, prof["cechy_odseparowane"])
    check("C2 spodziewane_lustra z lantek", prof["spodziewane_lustra"] is True, prof["spodziewane_lustra"])
    check("C3 oba typy", prof["typy"] == ["sbm_kolorowa", "lantek_1nn"], prof["typy"])
    print(f"  scalone: geom_kolory={prof['geom_kolory']} lustra={prof['spodziewane_lustra']} "
          f"cechy_odsep={prof['cechy_odseparowane']}")


def test_domyslny_kompletny():
    print("\n--- D) PROFIL_DOMYSLNY kompletny ---")
    for k in ("geom_kolory", "giecie_kolor", "warstwa_pozycyjna", "spodziewane_lustra",
              "cechy_odseparowane", "prog_sweep_delta", "uwaga"):
        check(f"D {k}", k in tp.PROFIL_DOMYSLNY, f"brak {k}")


def main():
    print("=== TESTY TYPOWANIA (progi/podpowiedzi) ===\n")
    test_lantek()
    test_domyslny()
    test_scalanie()
    test_domyslny_kompletny()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== TYPOWANIE: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== TYPOWANIE: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
