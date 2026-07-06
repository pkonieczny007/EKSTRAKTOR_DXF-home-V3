# -*- coding: utf-8 -*-
"""Test end-to-end: SWEEP KOMPLETNOSCI lapie realne braki z lekcji 54_4867.

DOWOD siatki bezpieczenstwa: silnik W-A (extract_positions) na REALNYCH zrodlach
54_4867 gubi cechy ODSEPAROWANE (sloty/fasole niepolaczone z konturem) - dokladnie
katastrofa 54_4867. Sweep (kontury regionu zrodla vs dostarczone, bramka 5) MUSI
te braki oflagowac (delta>=1), inaczej poszlyby na laser niezauwazone.

To NIE dubluje regresja_znane_bledy.py: tamto testuje SILNIK (XFAIL - ze gubi);
to testuje ze SWEEP to WYLAPUJE (safety net dziala mimo bledu silnika).

Uzycie:  python testy\\test_sweep_54_4867.py     (exit 0 = PASS)
Zrodla:  testy/rysunki/<zeinr>_1_conv.dxf + testy/rysunki/wykaz_54_4867.xlsx
"""
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
RYSUNKI = HERE / "rysunki"
WYKAZ = RYSUNKI / "wykaz_54_4867.xlsx"
SILNIK = HERE.parent / "produkcja" / "silniki" / "extract_positions.py"
sys.path.insert(0, str(HERE.parent / "produkcja" / "kontrola"))
from sweep import sweep_zlecenie  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# (zeinr, posn, min_zrodlo, max_wynik, opis) - cechy ODSEPAROWANE ktore silnik gubi,
# a sweep MUSI oflagowac (semafor != zielony, delta = zrodlo - wynik >= 1).
CASES = [
    ("SL400521106", 1, 8, 4, "8 slotow odseparowanych, silnik gubi 4"),
    ("SL10596945", 3, 4, 3, "2 fasole + 2 otwory, silnik gubi dolna fasole"),
]


def _run_engine(zeinr, outdir):
    subprocess.run([sys.executable, str(SILNIK), str(RYSUNKI / f"{zeinr}_1_conv.dxf"),
                    str(WYKAZ), str(outdir)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    print("=== SWEEP lapie realne braki 54_4867 (end-to-end) ===\n")
    tmp = Path(tempfile.mkdtemp(prefix="sweep5447_"))
    try:
        rys = tmp / "rys"
        rys.mkdir()
        for zeinr, *_ in CASES:
            shutil.copy(RYSUNKI / f"{zeinr}_1_conv.dxf", rys / f"{zeinr}_1_conv.dxf")
            wyn = tmp / "wyn" / zeinr
            wyn.mkdir(parents=True)
            _run_engine(zeinr, wyn)

        wiersze, braki = sweep_zlecenie(tmp / "wyn", rys)
        check("brak nieoczekiwanych brakow zrodla", not braki, f"braki={braki}")
        by = {(w["zeinr"], str(w["posn"])): w for w in wiersze}

        for zeinr, posn, min_zr, max_wy, opis in CASES:
            w = by.get((zeinr, str(posn)))
            if w is None:
                check(f"{zeinr} p{posn} obecny w sweep", False,
                      f"brak pozycji w wynikach sweep (klucze={list(by)})")
                continue
            check(f"{zeinr} p{posn} zrodlo>={min_zr}", (w["zrodlo"] or 0) >= min_zr,
                  f"zrodlo={w['zrodlo']} < {min_zr}")
            check(f"{zeinr} p{posn} wynik<={max_wy}",
                  w["wynik"] is not None and w["wynik"] <= max_wy,
                  f"wynik={w['wynik']} > {max_wy}")
            check(f"{zeinr} p{posn} OFLAGOWANY", w["semafor"] != "zielony",
                  f"semafor={w['semafor']} delta={w['delta']} - BRAK PRZESZEDL NIEZAUWAZONY!")
            print(f"  {zeinr}_p{posn:<2} zrodlo={w['zrodlo']} wynik={w['wynik']} "
                  f"delta={w['delta']} -> {w['semafor'].upper()}  ({opis})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== SWEEP 54_4867: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== SWEEP 54_4867: PASS (siatka bezpieczenstwa lapie braki silnika) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
