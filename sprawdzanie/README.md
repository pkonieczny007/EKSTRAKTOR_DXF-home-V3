# SYSTEM SPRAWDZANIA — dwie warstwy (po bramkach skryptowych)

Kolejność zawsze: **bramki skryptowe → AI → człowiek**. AI może status tylko
OBNIŻYĆ (zasada 5). Każda flaga kompletności = oględziny renderu, nigdy decyzja
po wielkości różnicy (zasada 6 — błąd z 54_4867).

## ai/
- `nakladka.py` — nakładka wynik-na-źródło (strategia #1 kompletności) [szkielet, etap 2].
- Procedura flag: render → AI OGLĄDA → brak potwierdzony = naprawa W-C + golden;
  false-positive = dowód (para PNG) + pozycja do przeglądu człowieka.
- Werdykty AI → `nauka/etykiety/etykiety.csv` (kto=ai) przez `../czlowiek/werdykty.py --kto ai`.

## czlowiek/
- Galeria kafelków: `python produkcja\silniki\v2\galeria.py <folder_wynikow> [--rysunki <folder>]`.
- Przegląd: 🟡/🟠/🔴 obowiązkowo + próbka 🟢 (np. co 10.); człowiek porównuje
  obrazki, nie otwiera CAD.
- Werdykt: `python sprawdzanie\czlowiek\werdykty.py <plik> OK|BLAD [kategoria]`
  → `nauka/etykiety/`. Każdy BŁĄD → NAJPIERW przypadek do `testy/golden/` (zasada 11).
