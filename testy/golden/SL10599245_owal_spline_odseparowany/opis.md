# SL10599245_p1 — zamknięty SPLINE (owal ~225×245) odseparowany, gubiony przez klaster

- Skąd: zlecenie test2 (2026-07-04, ekstrakcja SONNET), rysunek `SL10599245_1_conv.dxf`,
  wykaz `test2.xlsx` (poz. 1, 1150×1130, blacha 5 mm S235JRC).
- Co testuje: silnik W-B (po-kolorze-7, gap=8) zwrócił poz. 1 bez zamkniętego SPLINE
  (owal ~Ø225, wyspa na środku blachy, niepołączona z konturem) — znany przypadek
  z 54_4867 i notatki MEMORY „bliźniaki asymetryczne”. Bramka wymiaru ZIELONA
  (owal wewnątrz — bbox bez zmian); brak wykrył licznik konturów wewnętrznych:
  region kolor 7 = 21 wewn. vs wynik = 20 (delta 1 = zamknięty SPLINE 22.5×24.5 w skali 10).
- Asymetria bliźniaków POTWIERDZONA: p2 (ten sam obrys 1150×1130) w źródle NIE MA owalu
  (54 vs 55 encji kolor 7 w regionie) — to dwie różne części, NIE lustro. p2 = 20/20 OK.
- Wzorzec: wynik W-B + dołożony brakujący SPLINE transformacją silnika
  (mapowanie bbox regionu kolor 7 → bbox wyniku, skala ×10). Po naprawie: 21 = 21,
  wymiar 1150×1130.47 bez zmian, bramki post-hoc ZIELONE, render zgodny ze źródłem.
- Znany błąd który łapie: bilans konturów wewnętrznych (bramka 5) na cechach
  odseparowanych typu zamknięty SPLINE; kontrola wymiaru tego NIE łapie.
