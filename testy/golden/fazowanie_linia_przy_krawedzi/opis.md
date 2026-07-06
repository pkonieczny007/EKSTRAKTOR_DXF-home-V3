# Golden: wykrywanie FAZOWANIA (chamfer) - linia rownolegla do krawedzi

**Status:** WPIETE (2026-07-07). Flager `produkcja/kontrola/fazowanie.py`; test
`testy/test_fazowanie.py`. Operator POTWIERDZIL 3. przypadek (SL10583062_p2). Obsluga:
linie fazy ZOSTAWIC, POKOLOROWAC na ZOLTY (kol.2) + KOMENTARZ w wykazie; pozycja 🟡.

## Przypadki POZYTYWNE (3 - wszystkie wykryte, d=5.0, ratio=1.0, pewnosc=1.0)
- SL10585238 p2: bbox zrodla (267.62,117.09)-(311.62,123.09) skala 5.0 warstwa 102.
  Pasek 220x30, linia fazowania pelnej szerokosci ~5 mm od gornej krawedzi (kol.7).
- SL10585242 p2: bbox zrodla (271.03,107.9)-(300.03,113.9) skala 5.0 warstwa 102.
  Pasek 145x30, T-zlacza w (+-72.5, 10) [wsp. wyniku mm].
- SL10583062 p2 (POTWIERDZONY operator 07.07): pasek 302x30, linia 5 mm od gornej
  krawedzi, T-zlacza (+-151,10). Znaleziony przez sweep flagera (260 DXF), byl PRZEOCZONY.

## Negatywy (0 kandydatow): SL10584847_p2 (sloty), SL10409233_p1 (sloty+okregi),
SL10585238_p1 (DOSPAWIENIA - nie faza). Sweep 260 DXF: 0 falszywych.

## Kryterium PASS (test_fazowanie.py)
3 pozytywy -> >=1 kandydat, d in [1,10], ratio in [0.6,1.4]; negatywy -> 0; oznacz_w_pliku
koloruje linie na ZOLTY (2), idempotentne, geometria (extents) bez zmian; komentarz niepusty.
