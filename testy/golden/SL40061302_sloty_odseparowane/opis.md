# SL40061302_p1 — 3 sloty (fasole) odseparowane gubione przez klaster

- Skąd: zlecenie test2 (2026-07-04, ekstrakcja SONNET), rysunek `SL40061302_1_conv.dxf`,
  wykaz `test2.xlsx` (poz. 1, 287×210, blacha 5 mm S235JRC).
- Co testuje: silnik W-B (technika po-kolorze-2, gap=8) zwrócił kontur zewnętrzny
  + linie gięcia, ale ZGUBIŁ 3 fasole (sloty) na środku blachy — cechy odseparowane
  od konturu (znany root-cause z 54_4867; ta sama pozycja wymieniona w CLAUDE.md
  jako znaleziona sweepem). Bramki 1–3/6/9 dały ZIELONY — wymiar się zgadzał!
  Brak wykrył dopiero licznik konturów wewnętrznych (region kolor 2: 3 wewn. vs wynik: 0).
- Wzorzec: region+warstwa (wszystkie encje koloru 2 w bbox widoku 50.83,136.99–194.3,241.99,
  skala ×2, wyśrodkowane) + 4 linie GIECIE z wyniku W-B. Kontrola: wymiar 286.94×210 OK,
  3 kontury wewnętrzne, bramki post-hoc ZIELONE, render zgodny ze źródłem
  (para PNG: `wyniki/test2/SONNET/SL40061302_p1_DOWOD_region_zrodlo.png` vs `SL40061302_p1.png`).
- Znany błąd który łapie: bilans konturów wewnętrznych (bramka 5) — wynik bez slotów
  ma 0 wewn., wzorzec 3. Uwaga: geometria na KOLORZE 2, nie 7 (notatka MEMORY: SL40061302).
