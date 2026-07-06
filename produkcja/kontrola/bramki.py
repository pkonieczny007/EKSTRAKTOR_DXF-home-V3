# -*- coding: utf-8 -*-
"""
BRAMKI KONTROLI V3 - rejestr 10 bramek + uruchomienie kontroli post-hoc.

Bramki 1-4 i 6-9 REALIZUJE weryfikator silnika W-B (8 bramek QC z V2) -
ten modul go wola, nie kopiuje. Bramki 5 i 10 to nowosc V3: bramka 5 dziala
(kontrola/bilans_konturow.py, shapely.polygonize); bramka 10 = etap 3.

Zasada (CLAUDE.md): bramka = twarda decyzja automatu (sygnal czysty);
flager = sygnal z szumem (licznik_konturow.py) - wskazuje GDZIE patrzec,
decyzje podejmuja oczy; 100% flag, nigdy po wielkosci roznicy (zasada 6).

Uzycie:
  python produkcja\\kontrola\\bramki.py --lista
  python produkcja\\kontrola\\bramki.py <plik.dxf> <dim_max> <dim_min>   # bramki W-B
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WERYFIKATOR_WB = HERE.parent / "silniki" / "v2" / "weryfikator.py"

BRAMKI = [
    (1, "wymiar dwustopniowy",          "dziala",  "silniki/v2/weryfikator.py (zgrubna <=3% przed zapisem, scisla po zapisie)"),
    (2, "kontur domkniety",             "dziala",  "silniki/v2/weryfikator.py (0 otwartych koncow)"),
    (3, "filtr smieci",                 "dziala",  "silniki/v2/weryfikator.py (statystyka encji)"),
    (4, "bilans otworow okraglych",     "dziala",  "silniki/v2/weryfikator.py (TODO etap 2: liczyc w KLASTRZE czesci, nie bbox)"),
    (5, "bilans konturow wewnetrznych", "dziala",  "kontrola/bilans_konturow.py (shapely.polygonize; odporny na lustro/jitter/dedup; test: testy/test_bramka5.py)"),
    (6, "izometria",                    "dziala",  "silniki/v2/weryfikator.py (rozklad dlugosci linii)"),
    (7, "giecie kolor 6",               "dziala",  "silniki/v2/weryfikator.py (zrodlo ma giecie -> wynik ma warstwe GIECIE)"),
    (8, "rejestr widokow",              "dziala",  "silniki/v2/orkiestrator.py (zaden widok 2x)"),
    (9, "sanity 1:1 wysrodkowanie",     "dziala",  "silniki/v2/weryfikator.py (srodek bbox w (0,0))"),
    (10, "zgodnosc wariantow",          "czesciowo", "produkcja/ocena.py (CLI dziala; wpiecie w pipeline = etap 3)"),
]


def lista():
    print(f"{'#':>2}  {'bramka':<28} {'status':<10} realizacja")
    for nr, nazwa, status, gdzie in BRAMKI:
        print(f"{nr:>2}  {nazwa:<28} {status:<10} {gdzie}")


def main(argv):
    if not argv or argv[0] == "--lista":
        lista()
        return 0
    if len(argv) != 3:
        print(__doc__)
        return 2
    # kontrola post-hoc gotowego DXF -> delegacja do weryfikatora W-B (8 bramek)
    return subprocess.call([sys.executable, str(WERYFIKATOR_WB), *argv])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
