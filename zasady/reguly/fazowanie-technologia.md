# REGUŁA: Linia równoległa przy krawędzi z T-złączami = FAZOWANIE, nie otwarty kontur

**Status:** wdrożona (2026-07-07; flager `produkcja/kontrola/fazowanie.py`).
**Klasa błędu, której zapobiega:** (a) mylący powód „2 otwarte końce" na poprawnym
detalu — fałszywa flaga bramki 2 ucząca ignorowania flag; (b) potraktowanie
znacznika obróbki krawędzi jako konturu cięcia.

## Zasada (ogólna — sygnatura geometryczna, nie numer rysunku)

Fazowanie (chamfer) na rysunku = linia w kolorze GEOMETRII (kol. 7, NIE magenta),
RÓWNOLEGŁA do krawędzi konturu zewnętrznego, blisko niej, na długości tej krawędzi,
tworząca T-złącza z bokami konturu. Deterministyczna sygnatura:

    OBA końce linii leżą NA pierścieniu zewnętrznym części (T-złącza),
    a ŚRODEK linii leży ściśle WEWNĄTRZ, w odległości ~d od pierścienia.

To odróżnia fazowanie od: otworu/slotu (zamknięta pętla), dospawienia (końce nie
na obrysie), linii gięcia (kolor 6 — odfiltrowana), dubla konturu (środek NA
pierścieniu). Działanie: linii fazowania NIE liczyć jako konturu cięcia ani jako
otwartych końców; pozycję oznaczyć **technologia = „fazowanie"** + jawny powód;
linię ZOSTAWIĆ, przekolorować na żółto (kolor 2) + komentarz w wykazie (decyzja
operatora 2026-07-07). Status zostaje 🟡 do potwierdzenia — FLAGER, nie podnosi
statusu (zasada 5).

## Bramka / skrypt / progi

- `produkcja/kontrola/fazowanie.py` — progi: odstęp od krawędzi `D_MIN=1.0` …
  `D_MAX=10.0` mm (typowo ~5), równoległość `ANGLE_TOL_DEG=2.0°`, koniec na
  pierścieniu `TOL_RING=0.05` mm, min długość `MIN_LEN=5.0` mm.
- Zmierzone: 3 pozytywy (SL10585238_p2, SL10585242_p2, SL10583062_p2),
  **0 fałszywych trafień na 260 DXF**.

## Golden-test (dowód)

- `testy/golden/fazowanie_linia_przy_krawedzi/` + `testy/test_fazowanie.py`.
- Wiedza: `kontekst/wiedza/fazowanie-linia-przy-krawedzi.md`.
- Propozycja źródłowa: `zasady/propozycje/2026-07-07_wykrywanie_fazowania.md`.
