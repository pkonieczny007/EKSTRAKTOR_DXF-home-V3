# SL10599245_p6/p7 — kandydat ratunkowy z „brzydką" skalą 4.9109 zamiast 5.0

- Skąd: zlecenie test2 (2026-07-04, przebieg 4 modeli), rysunek `SL10599245_1_conv.dxf`,
  wykaz `test2.xlsx` (poz. 6 blacha 5 mm i poz. 7 blacha 3 mm — ta sama geometria
  311×300, wspólny widok źródłowy; dysk z otworem i wypustem).
- Co testuje: silnik W-B nie dopasował widoku ścieżką ścisłą (klaster gap=8 skleił
  część 60.0×62.28 z ~2 mm osi/adnotacji → bbox 62.13×62.29 → rozjazd skal x/y
  3.28% > SCALE_TOL 3%) i spadł do kategorii ratunkowej (`geometria`,
  czysty-kontur-luzna-tol 4.5%), która policzyła skalę jako średnią osi = **4.9109**
  → wynik 305.87×294.67 vs wykaz 311×300 (−5.1/−5.3 mm), bramka 1 CZERWONA,
  plik `_DO_SPRAWDZENIA`.
- Kluczowe fakty:
  - Na rysunku nad widokiem stoi tekst **„(M / S 1:5)"** — jawna skala 1:5,
    silnik jej nie czyta (kategoria 4 „adnotacje" = etap 6).
  - `_match_luzny` (geometria.py) NIE MA przyciągania do NICE_SCALES, choć 4.9109
    leży 1.8% od 5.0 (< próg snapa 2% ze ścieżki ścisłej).
  - Przy skali 5.0 realny kontur części daje 300.01×311.42 vs wykaz 311×300
    (po normalizacji osi: odchyłki 0.42 i 0.01 mm — bramka wymiaru PASS).
- Wzorzec: `wzorzec/SL10599245_p6.dxf`, `wzorzec/SL10599245_p7.dxf` — naprawa
  z przebiegu FABLE (region widoku przeskalowany ×5.0, wyśrodkowany; kontury 1=1,
  okręgi 1=1, bramki post-hoc ZIELONE). **UWAGA: wzorzec pochodzi z naprawy AI —
  wymaga potwierdzenia człowieka przed użyciem jako twarda referencja regresji.**
- Znany błąd który łapie: „skala ratunkowa" nieistniejąca rysunkowo (4.91) dająca
  geometrię zbliżoną do oryginału w złej skali — najgroźniejszy typ błędu do
  przeoczenia. Test ma pilnować, że pipeline dla p6/p7 zwraca wynik w skali 5.0
  (wymiar 300×311.4 ±1 mm) ALBO w ogóle nie zapisuje pliku — nigdy 305.87×294.67.
- Powiązana propozycja: `zasady/propozycje/2026-07-04_skala_ratunkowa_nice_scales.md`.
