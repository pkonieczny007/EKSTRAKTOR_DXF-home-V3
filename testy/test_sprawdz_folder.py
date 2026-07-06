# -*- coding: utf-8 -*-
"""Testy SPRAWDZANIA AI folderu (Etap 4): sprawdzanie/ai/sprawdz_folder.py.

Nakladka wstrzykiwana STUBEM (szybko, deterministycznie) - testujemy LOGIKE flag,
nie renderowanie (nakladka ma wlasny test_nakladka.py).

A) _twin_posn / _obniz - jednostki.
B) sprawdz_folder na syntetycznym folderze:
   p1 zielony + pokrycie_zrodla 99 -> BEZ flagi;
   p2 zolty + 99 -> flaga (nie-zielony), status bez zmian;
   p3 czerwony bez pliku -> flaga, powod "brak DXF";
   p4 zielony + pokrycie_zrodla 90 (<97) -> flaga + AUTO-OBNIZENIE do zoltego (zasada 5);
   p5 LUSTRO z poz.1 (brak wlasnego boxa) -> box wziety z blizniaka, lustro=True.

Uzycie:  python testy\\test_sprawdz_folder.py     (exit 0 = PASS)
"""
import csv
import io
import re
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "sprawdzanie" / "ai"))
import sprawdz_folder as sf  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _rect_dxf(path, w=100.0, h=50.0):
    doc = ezdxf.new()
    doc.modelspace().add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)
    doc.saveas(path)


# stub nakladki: rejestruje wywolania, zwraca sterowane pokrycie_zrodla
CALLS = []


def _stub_nakladka(wynik, zrodlo, box, png, scale=None, lustro=False):
    posn = int(re.search(r"_p(\d+)\.dxf", str(wynik)).group(1))
    CALLS.append(dict(posn=posn, box=box, scale=scale, lustro=lustro))
    Path(png).write_text("x")           # ślad pliku (driver zapisuje tylko nazwe)
    pz = 90.0 if posn == 4 else 99.0     # p4 = ponizej progu -> MOZLIWY BRAK
    return dict(align_info={}, pokrycie=95.0, pokrycie_zrodla=pz, uwagi=[], png=str(png))


def test_jednostki():
    print("--- A) _twin_posn / _obniz ---")
    check("A1 twin", sf._twin_posn("LUSTRO z poz. 1 - ZWERYFIKUJ") == 1)
    check("A2 twin brak", sf._twin_posn("OK (TRYB BEZ WARSTW)") is None)
    check("A3 obniz zielony", sf._obniz("zielony") == "zolty")
    check("A4 obniz zolty", sf._obniz("zolty") == "zolty")
    check("A5 obniz czerwony", sf._obniz("czerwony") == "czerwony")


def _setup(tmp, zeinr):
    box1 = (10.0, 10.0, 60.0, 40.0)
    # ocena.csv
    with open(tmp / f"{zeinr}_ocena.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "zeinr", "posn", "zwyciezca", "semafor", "pewnosc", "zrodlo_prawda",
            "warianty", "interior", "plik_produkcyjny", "powod"])
        w.writeheader()
        for posn, sem, plik, zw in [
                (1, "zielony", f"{zeinr}_p1.dxf", "W-C"),
                (2, "zolty", f"{zeinr}_p2.dxf", "W-B"),
                (3, "czerwony", "-", "-"),
                (4, "zielony", f"{zeinr}_p4.dxf", "W-C"),
                (5, "zolty", f"{zeinr}_p5.dxf", "LUSTRO(p1)")]:
            w.writerow(dict(zeinr=zeinr, posn=posn, zwyciezca=zw, semafor=sem,
                            pewnosc="-", zrodlo_prawda=0, warianty="", interior="",
                            plik_produkcyjny=plik, powod="test"))
    # raport silnika bazowego (box + skala + status LUSTRO)
    wA = tmp / "warianty" / "wA"
    wA.mkdir(parents=True, exist_ok=True)
    with open(wA / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "posn", "scale", "src_x1", "src_y1", "src_x2", "src_y2", "status",
            "n_bend", "wykaz_w", "wykaz_h", "file"])
        w.writeheader()
        for posn, st in [(1, "OK"), (2, "OK"), (3, "OK"), (4, "OK")]:
            w.writerow(dict(posn=posn, scale=5.0, src_x1=box1[0], src_y1=box1[1],
                            src_x2=box1[2], src_y2=box1[3], status=st, n_bend=0,
                            wykaz_w=250.0, wykaz_h=150.0, file=f"{zeinr}_p{posn}.dxf"))
        # p5 lustro: brak wlasnego boxa (puste), status LUSTRO z poz.1
        w.writerow(dict(posn=5, scale="", src_x1="", src_y1="", src_x2="", src_y2="",
                        status="LUSTRO z poz. 1", n_bend=0, wykaz_w=250.0, wykaz_h=150.0,
                        file=""))
    for posn in (1, 2, 4, 5):
        _rect_dxf(tmp / f"{zeinr}_p{posn}.dxf")
    # zrodlo (dowolny dxf - stub go nie czyta)
    _rect_dxf(tmp / f"{zeinr}_conv.dxf")
    return box1


def test_sprawdz_folder():
    print("\n--- B) sprawdz_folder (stub nakladki) ---")
    CALLS.clear()
    zeinr = "SLAI0001"
    tmp = Path(tempfile.mkdtemp(prefix="sf_"))
    try:
        box1 = _setup(tmp, zeinr)
        zz, wiersze = sf.sprawdz_folder(tmp, tmp / f"{zeinr}_conv.dxf",
                                        nakladka_fn=_stub_nakladka)
        check("B0 zeinr", zz == zeinr, zz)
        check("B0 5 pozycji", len(wiersze) == 5, len(wiersze))
        po = {w["posn"]: w for w in wiersze}
        # p1 zielony + 99 -> bez flagi
        check("B1 p1 bez flagi", po[1]["flaga"] == "nie", po[1]["flaga"])
        check("B1 p1 zielony", po[1]["semafor_ai"] == "zielony", po[1]["semafor_ai"])
        # p2 zolty -> flaga (nie-zielony), bez obnizenia
        check("B2 p2 flaga", po[2]["flaga"] == "TAK", po[2]["flaga"])
        check("B2 p2 zolty", po[2]["semafor_ai"] == "zolty", po[2]["semafor_ai"])
        # p3 czerwony bez pliku -> flaga, powod brak DXF
        check("B3 p3 flaga", po[3]["flaga"] == "TAK")
        check("B3 p3 brak DXF", "brak wyjsciowego DXF" in po[3]["powod_ai"], po[3]["powod_ai"])
        # p4 zielony + 90 -> flaga + AUTO-OBNIZENIE
        check("B4 p4 flaga", po[4]["flaga"] == "TAK")
        check("B4 p4 obnizony do zoltego", po[4]["semafor_ai"] == "zolty", po[4]["semafor_ai"])
        check("B4 p4 powod brak cechy", "MOZLIWY BRAK" in po[4]["powod_ai"], po[4]["powod_ai"])
        # p5 lustro: box z blizniaka (p1), lustro=True
        call5 = next((c for c in CALLS if c["posn"] == 5), None)
        check("B5 p5 nakladka wywolana", call5 is not None)
        check("B5 p5 box z blizniaka", call5 and call5["box"] == box1, call5 and call5["box"])
        check("B5 p5 lustro=True", call5 and call5["lustro"] is True)
        # nie wolamy nakladki dla p3 (brak pliku)
        check("B6 p3 bez nakladki", all(c["posn"] != 3 for c in CALLS))
        # CSV powstaje
        csvp = tmp / f"{zeinr}_sprawdzanie_ai.csv"
        check("B7 csv istnieje", csvp.exists())
        print(f"  flagi: {sum(1 for w in wiersze if w['flaga']=='TAK')}/5; "
              f"obnizone: {[w['posn'] for w in wiersze if w['semafor_ai']!=w['semafor_we']]}; "
              f"nakladek wywolanych: {len(CALLS)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_werdykty_ai():
    print("\n--- C) werdykty AI (WATPLIWOSC, zrodlo=ai) do etykiet ---")
    CALLS.clear()
    zeinr = "SLAI0002"
    tmp = Path(tempfile.mkdtemp(prefix="sf_ai_"))
    stara = sf.werdykty.ETYKIETY
    try:
        sf.werdykty.ETYKIETY = tmp / "etykiety.csv"    # monkeypatch: nie brudz repo
        _setup(tmp, zeinr)
        sf.sprawdz_folder(tmp, tmp / f"{zeinr}_conv.dxf",
                          nakladka_fn=_stub_nakladka, werdykty_ai=True)
        check("C0 etykiety powstaly", sf.werdykty.ETYKIETY.exists())
        rows = list(csv.DictReader(
            open(sf.werdykty.ETYKIETY, encoding="utf-8-sig"), delimiter=";"))
        # flagowane = p2(zolty), p3(bez pliku), p4(pokrycie90), p5(lustro zolty) = 4
        check("C1 4 werdykty AI", len(rows) == 4, len(rows))
        check("C2 wszystkie WATPLIWOSC ai",
              all(r["werdykt"] == "WATPLIWOSC" and r["kto"] == "ai" for r in rows), rows)
        # p1 (bez flagi) NIE ma werdyktu
        check("C3 p1 bez werdyktu",
              not any(f"{zeinr}_p1.dxf" == r["plik"] for r in rows))
        print(f"  zapisano {len(rows)} WATPLIWOSC (zrodlo=ai) dla flag; nieflagowany p1 pominiety")
    finally:
        sf.werdykty.ETYKIETY = stara
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== TESTY SPRAWDZANIA AI FOLDERU (Etap 4) ===\n")
    test_jednostki()
    test_sprawdz_folder()
    test_werdykty_ai()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== SPRAWDZ-AI: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== SPRAWDZ-AI: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
