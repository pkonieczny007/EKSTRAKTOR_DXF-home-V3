# -*- coding: utf-8 -*-
"""
RAPORT zlecenia - podsumowanie semaforow i powodow z raportu silnika.

Silnik W-B zapisuje w folderze wynikow <zeinr>_raport.csv per rysunek.
Ten skrypt skleja je w jedno podsumowanie: ile ZIELONY/ZOLTY/CZERWONY,
kazdy nie-zielony z jawnym POWODEM (CLAUDE.md zasada 3).

ETAP 3-4 (PLAN.md): dolozyc wyniki oceny wariantow (ocena.py), werdykty
sprawdzania AI/czlowieka i zapis statusow do wykazu (kolumny jak 54_4867:
status kolorem, uwagi, plik_dxf, technologia, wymiar_dxf_x/y, skala,
uwagi_wymiar=ok gdy X i Y +-1 vs Abmess).

Uzycie: python produkcja\\raport.py <folder_wynikow>
"""
import csv
import sys
from collections import Counter
from pathlib import Path


def wczytaj_raporty(folder):
    wiersze = []
    for p in sorted(Path(folder).glob("*_raport.csv")):
        with open(p, encoding="utf-8-sig", newline="") as f:
            # silnik pisze przez ';' (Excel PL); fallback na ','
            probka = f.read(2048)
            f.seek(0)
            sep = ";" if probka.count(";") >= probka.count(",") else ","
            for w in csv.DictReader(f, delimiter=sep):
                w["_raport"] = p.name
                wiersze.append(w)
    return wiersze


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    wiersze = wczytaj_raporty(argv[0])
    if not wiersze:
        print(f"brak *_raport.csv w {argv[0]}")
        return 1
    klucz_semafor = next((k for k in wiersze[0] if "semafor" in k.lower()), None)
    semafory = Counter((w.get(klucz_semafor) or "?") for w in wiersze) \
        if klucz_semafor else Counter()
    print(f"pozycji w raportach: {len(wiersze)}")
    for kolor, n in semafory.most_common():
        print(f"  {kolor}: {n}")
    if klucz_semafor:
        print("\nnie-zielone (kazde z powodem):")
        for w in wiersze:
            if (w.get(klucz_semafor) or "").upper() not in ("ZIELONY", ""):
                powod = next((w[k] for k in w if "powod" in k.lower() and w[k]), "?")
                print(f"  {w.get('file') or w.get('plik') or w['_raport']}: "
                      f"{w[klucz_semafor]} - {powod}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
