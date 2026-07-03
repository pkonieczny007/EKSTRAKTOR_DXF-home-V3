# -*- coding: utf-8 -*-
"""
DESTYLACJA - z surowych zdarzen (korpus + etykiety) do KANDYDATOW na wnioski.

Czyta nauka/korpus/decyzje.csv (logger --korpus silnika W-B; kolumny: zeinr, posn,
status, qc_semafor, qc_powody, kategoria, technika, pewnosc, n_kandydatow,
wykaz_w, wykaz_h, out_w, out_h, file, powod_logu) oraz nauka/etykiety/etykiety.csv
(werdykty przegladu) i agreguje wzorce: gdzie system myli sie najczesciej.

Wynik = SZKIC wnioskow (format nauka/szkolenia/_szablon/wnioski.md) do reki
czlowieka. Destylacja NICZEGO nie zmienia sama (CLAUDE.md zasada 12):
awans do reguly/wiedzy ZAWSZE za potwierdzeniem czlowieka ->
kontekst/wiedza/<name>.md + linia w kontekst/wiedza/MEMORY.md + przypadek golden.

Deterministycznie, zero LLM - agregacja statystyczna. Interpretacje i propozycje
regul dopisuje AI/czlowiek w sesji, czytajac ten szkic.

Uzycie: python nauka\\destylacja.py [--korpus plik.csv] [--etykiety plik.csv]
"""
import csv
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
KORPUS = HERE / "korpus" / "decyzje.csv"
ETYKIETY = HERE / "etykiety" / "etykiety.csv"


def wczytaj(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main(argv):
    korpus_p, etykiety_p = KORPUS, ETYKIETY
    if "--korpus" in argv:
        korpus_p = Path(argv[argv.index("--korpus") + 1])
    if "--etykiety" in argv:
        etykiety_p = Path(argv[argv.index("--etykiety") + 1])

    korpus = wczytaj(korpus_p)
    etykiety = wczytaj(etykiety_p)
    if not korpus and not etykiety:
        print(f"brak danych ({korpus_p} i {etykiety_p} puste/nieobecne)\n"
              "korpus zbiera flaga --korpus w orkiestratorze; etykiety zbiera\n"
              "sprawdzanie/czlowiek/werdykty.py")
        return 1

    print(f"# Szkic wnioskow (destylacja) - korpus: {len(korpus)} zdarzen, "
          f"etykiety: {len(etykiety)} werdyktow\n")
    if korpus:
        print("## Korpus: powody zdarzen uczacych")
        for powod, n in Counter(w.get("powod_logu", "?") for w in korpus).most_common():
            print(f"- {powod}: {n}")
        print("\n## Korpus: zdarzenia per prefiks rysunku (konwencja klienta)")
        for pref, n in Counter(
                (w.get("zeinr") or "?")[:4] for w in korpus).most_common(10):
            print(f"- {pref}*: {n}")
        print("\n## Korpus: techniki przy zdarzeniach (gdzie szukanie niepewne)")
        for tech, n in Counter(
                w.get("technika") or "?" for w in korpus).most_common(10):
            print(f"- {tech}: {n}")
    if etykiety:
        print("\n## Etykiety: werdykty przegladu")
        for (werdykt, kat), n in Counter(
                (w.get("werdykt", "?"), w.get("kategoria_bledu", ""))
                for w in etykiety).most_common():
            print(f"- {werdykt} {kat}: {n}")
    print("\n## Nastepny krok (czlowiek + AI w sesji)")
    print("- najczestszy wzorzec -> propozycja reguly wg nauka/szkolenia/_szablon/wnioski.md")
    print("- po akceptacji: kontekst/wiedza/<name>.md + MEMORY.md + przypadek do testy/golden/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
