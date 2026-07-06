# Golden: SL10596945 p3/p4 — fasola odseparowana + duble okręgów + gięcie skośne

- **Skąd:** zlecenia/test (2026-07-04), rysunek z serii znanych błędów 54_4867 (SBM, warstwa 53).
- **Silnik W-B (etap 1) generuje 3 BŁĘDY naraz:**
  1. gubi DOLNĄ fasolę 14×30 (cecha odseparowana — klaster po sąsiedztwie jej nie łapie),
  2. zostawia zdublowane okręgi współśrodkowe 2×(Ø13+Ø14,7) — powinien zostać najmniejszy,
  3. gubi linię gięcia POD SKOSEM (kolor 6; bramka 6 flagowała w qc_powody!).
- **Wzorzec:** naprawa region+warstwa (warstwa 53, region z raportu, skala 5.0) —
  282,40×260,24 mm, 2 otwory Ø13, 2 fasole, 1 linia gięcia na warstwie GIECIE.
  KONTURY WEWNĘTRZNE = 4 (bilans PO dedupie okręgów!). Lustro p4 = odbicie z gięciem.
- **Czego pilnuje:** bramka 5 (bilans konturów wewnętrznych) musi wykryć 3≠4;
  UWAGA: bilans na surowych encjach NIE wykrywa (duble okręgów maskują brak fasoli:
  stary=5 „konturów", nowy=4) — liczyć PO dedupie współśrodkowych.
- **Pułapka procesu (2026-07-04):** AI znalazło duble okręgów i uznało kontrolę za
  skończoną — fasolę wskazał dopiero CZŁOWIEK na miniaturach. Jeden znaleziony błąd
  NIE kończy oględzin; werdykt tylko z kartą kontrolną (liczby + render).
