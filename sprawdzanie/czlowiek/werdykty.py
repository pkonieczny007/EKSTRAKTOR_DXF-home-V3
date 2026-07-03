# -*- coding: utf-8 -*-
"""
WERDYKTY przegladu - zbieranie etykiet od czlowieka (i AI) do systemu nauki.

Kazdy werdykt = 1 wiersz w nauka/etykiety/etykiety.csv (separator ';', BOM raz
dla Excela - konwencja jak korpus/decyzje.csv). Werdykt BLAD obliguje do
dodania przypadku do testy/golden/ PRZED naprawa (CLAUDE.md zasada 11).

Kategorie bledow (CLAUDE.md "Sprawdzanie przez czlowieka"):
  brak_otworu | otwor_nieokragly_zgubiony | zla_skala | zly_wymiar |
  kontur_otwarty | zle_lustro | obca_geometria | inne

Uzycie:
  python sprawdzanie\\czlowiek\\werdykty.py <plik_dxf> OK [--kto czlowiek|ai] [--uwagi "..."]
  python sprawdzanie\\czlowiek\\werdykty.py <plik_dxf> BLAD <kategoria> [--kto ...] [--uwagi "..."]
  python sprawdzanie\\czlowiek\\werdykty.py --podsumowanie
"""
import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ETYKIETY = HERE.parents[1] / "nauka" / "etykiety" / "etykiety.csv"
POLA = ["data", "plik", "werdykt", "kategoria_bledu", "kto", "uwagi"]
KATEGORIE = ["brak_otworu", "otwor_nieokragly_zgubiony", "zla_skala",
             "zly_wymiar", "kontur_otwarty", "zle_lustro", "obca_geometria", "inne"]


def dopisz_werdykt(plik, werdykt, kategoria="", kto="czlowiek", uwagi=""):
    if werdykt == "BLAD" and kategoria not in KATEGORIE:
        raise ValueError(f"kategoria '{kategoria}' spoza listy: {', '.join(KATEGORIE)}")
    ETYKIETY.parent.mkdir(parents=True, exist_ok=True)
    nowy = not ETYKIETY.exists()
    with open(ETYKIETY, "a", newline="", encoding="utf-8") as f:
        if nowy:
            f.write("﻿")
        w = csv.DictWriter(f, fieldnames=POLA, delimiter=";")
        if nowy:
            w.writeheader()
        w.writerow({"data": date.today().isoformat(), "plik": Path(plik).name,
                    "werdykt": werdykt, "kategoria_bledu": kategoria,
                    "kto": kto, "uwagi": uwagi})
    if werdykt == "BLAD":
        print("PAMIETAJ (zasada 11): NAJPIERW przypadek do testy/golden/, POTEM naprawa!")


def podsumowanie():
    if not ETYKIETY.exists():
        print("brak etykiet (nauka/etykiety/etykiety.csv nie istnieje)")
        return
    with open(ETYKIETY, encoding="utf-8-sig", newline="") as f:
        wiersze = list(csv.DictReader(f, delimiter=";"))
    print(f"etykiet: {len(wiersze)}")
    for (werdykt, kat), n in Counter(
            (w["werdykt"], w["kategoria_bledu"]) for w in wiersze).most_common():
        print(f"  {werdykt} {kat}: {n}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--podsumowanie":
        podsumowanie()
        return 0
    kto, uwagi = "czlowiek", ""
    if "--kto" in argv:
        i = argv.index("--kto")
        kto = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if "--uwagi" in argv:
        i = argv.index("--uwagi")
        uwagi = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2:
        print(__doc__)
        return 2
    plik, werdykt = argv[0], argv[1].upper()
    kategoria = argv[2] if len(argv) > 2 else ""
    dopisz_werdykt(plik, werdykt, kategoria, kto, uwagi)
    print(f"zapisano: {plik} {werdykt} {kategoria} ({kto})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
