# -*- coding: utf-8 -*-
"""
NAKLADKA wynik-na-zrodlo - najpewniejsza kontrola kompletnosci (CLAUDE.md).

Rysuje wyekstrahowany kontur (polprzezroczysty, czerwony) NA zrodlowym widoku,
w tej samej skali i pozycji. Operator/AI w 1 s widzi ceche obecna w zrodle,
a nieobecna w wyniku (fasola, slot, blok perforacji). Jedyna metoda odporna
na WSZYSTKIE typy brakow - strategia #1 z kontekst/strategia_kompletnosc_otworow.md.

Render ZAWSZE na czarnym tle (testy/pretesty/_render_png.py - jasne linie
na bialym znikaja).

PROCEDURA FLAGI (CLAUDE.md "Sprawdzanie przez AI"):
  render pary -> AI OGLADA (nie rozumuje o wielkosci roznicy!) ->
  brak potwierdzony -> naprawa W-C + golden; false-positive -> DOWOD (para PNG)
  + pozycja do przegladu czlowieka. Od NAJWIEKSZYCH roznic.

ETAP 2 (PLAN.md): implementacja na bazie galeria.py (ramka "skad wycieto"
juz dziala) + render_into z testy/pretesty/_demo_porownanie.py.

Uzycie (docelowe):
  python sprawdzanie\\ai\\nakladka.py <wynik.dxf> <zrodlo_conv.dxf> <out.png>
      [--region x1 y1 x2 y2] [--skala S]
"""
import sys


def main(argv):
    print(__doc__)
    print("STATUS: szkielet - implementacja = PLAN.md etap 2")
    return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
