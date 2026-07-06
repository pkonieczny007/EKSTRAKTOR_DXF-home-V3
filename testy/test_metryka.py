# -*- coding: utf-8 -*-
"""Testy METRYKI ZAUFANIA (Etap 6): zarzadzanie/metryka.py.

A) metryka_zlecenia - rozklad semaforow FINALNYCH (obnizenie AI ma pierwszenstwo),
   odsetek do przegladu, flagi AI, werdykty czlowieka dopasowane po zeinr.
B) dopisz_trend - append + replace po kluczu (data, zeinr); sort.

Uzycie:  python testy\\test_metryka.py     (exit 0 = PASS)
"""
import csv
import io
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "zarzadzanie"))
import metryka as mt  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _setup(tmp, zeinr):
    # podsumowanie: p1 zielony, p2 zielony, p3 zolty, p4 czerwony
    with open(tmp / f"{zeinr}_podsumowanie.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=["zeinr", "posn", "semafor"])
        w.writeheader()
        for posn, sem in [(1, "zielony"), (2, "zielony"), (3, "zolty"), (4, "czerwony")]:
            w.writerow(dict(zeinr=zeinr, posn=posn, semafor=sem))
    # sprawdzanie AI: p1 obnizone zielony->zolty (flaga), p2 zielony bez flagi
    with open(tmp / f"{zeinr}_sprawdzanie_ai.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "posn", "semafor_we", "flaga", "semafor_ai"])
        w.writeheader()
        w.writerow(dict(posn=1, semafor_we="zielony", flaga="TAK", semafor_ai="zolty"))
        w.writerow(dict(posn=2, semafor_we="zielony", flaga="nie", semafor_ai="zielony"))
    # etykiety: 1 OK czlowiek, 1 BLAD czlowiek (dla tego zeinr) + 1 obcy zeinr
    etyk = tmp / "etykiety.csv"
    with open(etyk, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "data", "plik", "werdykt", "kategoria_bledu", "kto", "uwagi"])
        w.writeheader()
        w.writerow(dict(data="2026-07-06", plik=f"{zeinr}_p2.dxf", werdykt="OK",
                        kategoria_bledu="", kto="czlowiek", uwagi=""))
        w.writerow(dict(data="2026-07-06", plik=f"{zeinr}_p4.dxf", werdykt="BLAD",
                        kategoria_bledu="brak_otworu", kto="czlowiek", uwagi=""))
        w.writerow(dict(data="2026-07-06", plik="OBCY_p1.dxf", werdykt="BLAD",
                        kategoria_bledu="inne", kto="czlowiek", uwagi=""))
    return etyk


def test_metryka():
    print("--- A) metryka_zlecenia ---")
    zeinr = "SLMET01"
    tmp = Path(tempfile.mkdtemp(prefix="met_"))
    try:
        etyk = _setup(tmp, zeinr)
        m = mt.metryka_zlecenia(tmp, etykiety_csv=etyk)
        check("A0 zeinr", m["zeinr"] == zeinr, m["zeinr"])
        check("A0 n=4", m["n_pozycji"] == 4, m["n_pozycji"])
        # finalne: p1 zolty(AI), p2 zielony, p3 zolty, p4 czerwony -> 1🟢 2🟡 1🔴
        check("A1 zielony=1", m["n_zielony"] == 1, m["n_zielony"])
        check("A2 zolty=2", m["n_zolty"] == 2, m["n_zolty"])
        check("A3 czerwony=1", m["n_czerwony"] == 1, m["n_czerwony"])
        # do przegladu = zolty+czerwony = 3/4 = 75%
        check("A4 odsetek 75", m["odsetek_przegladu_proc"] == 75.0, m["odsetek_przegladu_proc"])
        check("A5 flagi AI=1", m["n_flag_ai"] == 1, m["n_flag_ai"])
        check("A6 obnizone AI=1", m["n_obnizone_ai"] == 1, m["n_obnizone_ai"])
        # werdykty tylko tego zlecenia (OBCY pominiety)
        check("A7 OK czlowiek=1", m["n_werdykt_ok_czl"] == 1, m["n_werdykt_ok_czl"])
        check("A8 BLAD czlowiek=1", m["n_blad_czl"] == 1, m["n_blad_czl"])
        print(f"  {m['n_zielony']}🟢 {m['n_zolty']}🟡 {m['n_czerwony']}🔴  "
              f"przeglad={m['odsetek_przegladu_proc']}%  flagi_ai={m['n_flag_ai']}  "
              f"BLAD={m['n_blad_czl']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_trend():
    print("\n--- B) dopisz_trend (append + replace po data+zeinr) ---")
    tmp = Path(tempfile.mkdtemp(prefix="met_tr_"))
    try:
        trend = tmp / "trend.csv"
        m1 = dict(data="2026-07-06", zeinr="A", n_pozycji=10, odsetek_przegladu_proc=40.0)
        m2 = dict(data="2026-07-06", zeinr="B", n_pozycji=5, odsetek_przegladu_proc=20.0)
        mt.dopisz_trend(m1, trend)
        mt.dopisz_trend(m2, trend)
        rows = list(csv.DictReader(open(trend, encoding="utf-8-sig"), delimiter=";"))
        check("B0 2 wiersze", len(rows) == 2, len(rows))
        # ponowny zapis A tego samego dnia -> REPLACE (nie duplikat)
        m1b = dict(data="2026-07-06", zeinr="A", n_pozycji=10, odsetek_przegladu_proc=30.0)
        mt.dopisz_trend(m1b, trend)
        rows = list(csv.DictReader(open(trend, encoding="utf-8-sig"), delimiter=";"))
        check("B1 nadal 2 wiersze", len(rows) == 2, len(rows))
        a = next(r for r in rows if r["zeinr"] == "A")
        check("B2 A zaktualizowane", a["odsetek_przegladu_proc"] == "30.0",
              a["odsetek_przegladu_proc"])
        # inny dzien -> nowy wiersz (trend)
        m1c = dict(data="2026-07-07", zeinr="A", n_pozycji=10, odsetek_przegladu_proc=25.0)
        mt.dopisz_trend(m1c, trend)
        rows = list(csv.DictReader(open(trend, encoding="utf-8-sig"), delimiter=";"))
        check("B3 3 wiersze (trend A ma 2 daty)", len(rows) == 3, len(rows))
        print(f"  trend: {len(rows)} wierszy, A: 40->30 (replace) -> 25 (nowy dzien)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== TESTY METRYKI ZAUFANIA (Etap 6) ===\n")
    test_metryka()
    test_trend()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== METRYKA: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== METRYKA: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
