# -*- coding: utf-8 -*-
"""Testy PRZEGLADU CZLOWIEKA (Etap 4): sprawdzanie/czlowiek/przeglad.py.

Rendery wstrzykiwane STUBEM (bez matplotlib w petli) - testujemy LOGIKE spiecia:
semafor finalny (obnizenie AI), probkowanie zielonych, worklist werdyktow, import.

A) _twin_posn / _final_semafor / zaznacz_probke - jednostki.
B) zbuduj_pozycje - merge raport.scal + sprawdzanie_ai (AI obniza zielony->zolty),
   box zrodla z raportu; powody scalone.
C) generuj_przeglad (stub render) - HTML + worklist; probka zielonych (co N-ty),
   reszta zielonych pominieta; worklist tylko pozycje do przegladu.
D) wczytaj_werdykty_csv - wypelniony worklist -> nauka/etykiety (monkeypatch sciezki);
   OK/BLAD liczone, pusty werdykt pomijany, BLAD wymaga kategorii.

Uzycie:  python testy\\test_przeglad.py     (exit 0 = PASS)
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
sys.path.insert(0, str(HERE.parent / "sprawdzanie" / "czlowiek"))
import przeglad as pr  # noqa: E402

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


# ---- stub render: zapisuje placeholder PNG, rejestruje wywolania ----
R_WYNIK = []
R_ZRODLO = []


def _stub_render_wynik(dxf_path, out_png):
    R_WYNIK.append(Path(dxf_path).name)
    Path(out_png).write_text("x")


def _stub_render_zrodla(conv, pozycje, out_dir, zeinr):
    R_ZRODLO.append(zeinr)
    mapa = {}
    for posn, box in pozycje:
        z = f"{zeinr}_p{posn}_zrodlo.png"
        c = f"{zeinr}_p{posn}_zrodlo_caly.png"
        (Path(out_dir) / z).write_text("x")
        (Path(out_dir) / c).write_text("x")
        mapa[str(posn)] = (z, c)
    return mapa


def test_jednostki():
    print("--- A) jednostki ---")
    check("A1 twin", pr._twin_posn("LUSTRO z poz. 3") == 3)
    check("A2 twin brak", pr._twin_posn("OK") is None)
    # AI obniza: final = semafor_ai gdy jest
    check("A3 final z AI", pr._final_semafor({"semafor": "zielony"},
                                             {"semafor_ai": "zolty"}) == "zolty")
    check("A4 final bez AI", pr._final_semafor({"semafor": "zielony"}, None) == "zielony")
    # probkowanie: 4 zielone, prog=2 -> co 2-gi (1,3) = 2 probki; 2 pominiete
    poz = [dict(posn=i, semafor="zielony") for i in range(1, 5)]
    poz += [dict(posn=9, semafor="czerwony"), dict(posn=8, semafor="zolty")]
    pr.zaznacz_probke(poz, 2)
    zg = [p for p in poz if p["semafor"] == "zielony"]
    check("A5 probka zielonych 2", sum(1 for p in zg if p["probka"]) == 2,
          [p["probka"] for p in zg])
    check("A6 nie-zielone zawsze przeglad",
          all(p["przeglad"] for p in poz if p["semafor"] != "zielony"))


def _setup(tmp, zeinr):
    box1 = (10.0, 10.0, 60.0, 40.0)
    with open(tmp / f"{zeinr}_ocena.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "zeinr", "posn", "zwyciezca", "semafor", "pewnosc", "zrodlo_prawda",
            "warianty", "interior", "plik_produkcyjny", "powod"])
        w.writeheader()
        for posn, sem in [(1, "zielony"), (2, "zolty"), (3, "czerwony"),
                          (4, "zielony"), (5, "zielony"), (6, "zielony"), (7, "zielony")]:
            plik = "-" if posn == 3 else f"{zeinr}_p{posn}.dxf"
            w.writerow(dict(zeinr=zeinr, posn=posn, zwyciezca="W-C", semafor=sem,
                            pewnosc="-", zrodlo_prawda=0, warianty="", interior="",
                            plik_produkcyjny=plik, powod=f"powod p{posn}"))
    wA = tmp / "warianty" / "wA"
    wA.mkdir(parents=True, exist_ok=True)
    with open(wA / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "posn", "scale", "src_x1", "src_y1", "src_x2", "src_y2", "status",
            "n_bend", "wykaz_w", "wykaz_h", "file"])
        w.writeheader()
        for posn in (1, 2, 3, 4, 5, 6, 7):
            w.writerow(dict(posn=posn, scale=5.0, src_x1=box1[0], src_y1=box1[1],
                            src_x2=box1[2], src_y2=box1[3], status="OK", n_bend=0,
                            wykaz_w=250.0, wykaz_h=150.0,
                            file=("" if posn == 3 else f"{zeinr}_p{posn}.dxf")))
    # sprawdzanie AI: p1 obnizone przez AI zielony->zolty (z nakladka)
    with open(tmp / f"{zeinr}_sprawdzanie_ai.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "zeinr", "posn", "semafor_we", "pokrycie", "pokrycie_zrodla", "flaga",
            "semafor_ai", "powod_ai", "uwagi_wymiar", "png"])
        w.writeheader()
        w.writerow(dict(zeinr=zeinr, posn=1, semafor_we="zielony", pokrycie=95.0,
                        pokrycie_zrodla=90.0, flaga="TAK", semafor_ai="zolty",
                        powod_ai="pokrycie_zrodla 90%<97% = MOZLIWY BRAK", uwagi_wymiar="ok",
                        png=f"{zeinr}_p1_nakladka.png"))
    for posn in (1, 2, 4, 5, 6, 7):
        _rect_dxf(tmp / f"{zeinr}_p{posn}.dxf")
    # rysunek zrodlowy dla znajdz_rysunek
    rys = tmp / "rysunki"
    rys.mkdir(exist_ok=True)
    _rect_dxf(rys / f"{zeinr}_1_conv.dxf")
    # katalog nakladek (sprawdz_folder normalnie go tworzy)
    (tmp / "sprawdzanie_ai").mkdir(exist_ok=True)
    (tmp / "sprawdzanie_ai" / f"{zeinr}_p1_nakladka.png").write_text("x")
    return box1, rys


def test_zbuduj_i_przeglad():
    print("\n--- B/C) zbuduj_pozycje + generuj_przeglad (stub render) ---")
    R_WYNIK.clear()
    R_ZRODLO.clear()
    zeinr = "SLPRZ01"
    tmp = Path(tempfile.mkdtemp(prefix="prz_"))
    try:
        box1, rys = _setup(tmp, zeinr)
        # B) zbuduj_pozycje: p1 obnizone AI do zoltego, box z raportu
        zz, poz = pr.zbuduj_pozycje(tmp)
        po = {p["posn"]: p for p in poz}
        check("B0 7 pozycji", len(poz) == 7, len(poz))
        check("B1 p1 final zolty (AI)", po[1]["semafor"] == "zolty", po[1]["semafor"])
        check("B2 p2 zolty", po[2]["semafor"] == "zolty")
        check("B3 p1 box z raportu", po[1]["box"] == box1, po[1]["box"])
        check("B4 p1 powod ma AI", "AI:" in po[1]["powod"], po[1]["powod"])
        check("B5 p1 nakladka", po[1]["nakladka"] == f"{zeinr}_p1_nakladka.png")

        # C) generuj_przeglad z prog_probka=2
        html_p, csv_p, poz2 = pr.generuj_przeglad(
            tmp, rys, prog_probka=2,
            render_wynik_fn=_stub_render_wynik, render_zrodla_fn=_stub_render_zrodla)
        check("C0 html powstal", html_p and Path(html_p).exists())
        check("C1 worklist powstal", csv_p and Path(csv_p).exists())
        # zielone: p4,p5,p6,p7 (p1 stalo sie zolte). prog=2 -> probka 2 z 4
        zielone = [p for p in poz2 if p["semafor"] == "zielony"]
        probki = [p for p in zielone if p["probka"]]
        check("C2 zielonych 4", len(zielone) == 4, len(zielone))
        check("C3 probka 2 z 4", len(probki) == 2, len(probki))
        do_przegl = [p for p in poz2 if p["przeglad"]]
        # do przegladu: czerwony(p3) + zolte(p1,p2) + 2 probki zielone = 5
        check("C4 do przegladu 5", len(do_przegl) == 5, len(do_przegl))
        # worklist ma dokladnie pozycje do przegladu
        with open(csv_p, encoding="utf-8-sig", newline="") as f:
            wl = list(csv.DictReader(f, delimiter=";"))
        check("C5 worklist = do przegladu", len(wl) == 5, len(wl))
        check("C6 worklist werdykt pusty", all(r["werdykt"] == "" for r in wl))
        # render wywolany tylko dla pozycji do przegladu z plikiem (p1,p2,p4/p6 - nie p3)
        check("C7 render wyniku bez p3", all("p3" not in n for n in R_WYNIK), R_WYNIK)
        # nakladka p1 pokazana w HTML
        tekst = Path(html_p).read_text(encoding="utf-8")
        check("C8 html ma nakladke p1", f"{zeinr}_p1_nakladka.png" in tekst)
        check("C9 html ma PROBKA badge", "PROBKA" in tekst)
        print(f"  do przegladu={len(do_przegl)}/7 (probka zielonych {len(probki)}/4), "
              f"render_wyniku={len(R_WYNIK)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_werdykty_import():
    print("\n--- D) wczytaj_werdykty_csv -> etykiety ---")
    tmp = Path(tempfile.mkdtemp(prefix="prz_w_"))
    stara = pr.werdykty.ETYKIETY
    try:
        pr.werdykty.ETYKIETY = tmp / "etykiety.csv"    # monkeypatch: nie brudz repo
        csv_path = tmp / "werdykty.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=pr.POLA_WERDYKT, delimiter=";")
            w.writeheader()
            w.writerow(dict(zeinr="Z", posn=1, plik_dxf="Z_p1.dxf", semafor="zolty",
                            sugestia="", werdykt="OK", kategoria="", uwagi="ok wizualnie"))
            w.writerow(dict(zeinr="Z", posn=3, plik_dxf="Z_p3.dxf", semafor="czerwony",
                            sugestia="", werdykt="BLAD", kategoria="brak_otworu", uwagi="zgubiony"))
            w.writerow(dict(zeinr="Z", posn=5, plik_dxf="Z_p5.dxf", semafor="zielony",
                            sugestia="", werdykt="", kategoria="", uwagi=""))  # pusty - pomin
        n = pr.wczytaj_werdykty_csv(csv_path, kto="czlowiek")
        check("D0 zaimportowano 2", n == 2, n)
        check("D1 etykiety powstaly", pr.werdykty.ETYKIETY.exists())
        with open(pr.werdykty.ETYKIETY, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
        check("D2 2 wiersze etykiet", len(rows) == 2, len(rows))
        check("D3 jest BLAD brak_otworu",
              any(r["werdykt"] == "BLAD" and r["kategoria_bledu"] == "brak_otworu" for r in rows))
        print(f"  zaimportowano {n} (OK+BLAD), pusty werdykt pominiety")
    finally:
        pr.werdykty.ETYKIETY = stara
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== TESTY PRZEGLADU CZLOWIEKA (Etap 4) ===\n")
    test_jednostki()
    test_zbuduj_i_przeglad()
    test_werdykty_import()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== PRZEGLAD: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== PRZEGLAD: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
