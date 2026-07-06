# Szkolenie: test SL10596945 — AI przegapiło fasolę mimo znalezienia dubli okręgów

- **Data / zlecenie:** 2026-07-04, `zlecenia/test` (rysunek SBM z serii 54_4867, warstwa 53).
- **Przebieg:** pipeline V3 (etap 1, parytet W-B) wyciągnął p3 282,4×260,24 — wymiar OK,
  QC ŻÓŁTY. AI w podsumowaniu wskazało duble okręgów, fasolę zbyło „prawdopodobnie
  brakuje" i NIE przeczytało qc_powodów (bramka 6 flagowała zgubione gięcie).
- **Wykrycie:** OPERATOR porównał miniatury p4_LUSTRO vs p4_zrodlo i wskazał brak
  dolnej fasoli + pokazał metodę ręczną (cała warstwa 53 z regionu / zaznacz białe →
  dodaj gięcia → skaluj).
- **Naprawa:** region+warstwa (auto-warstwa 53, region z raportu, skala 5.0) →
  2 fasole, 2×Ø13, gięcie na GIECIE, kontury wewn. 4=źródło. Dowód wzrokowy PASS.
- **Materiał:** wejście+wzorzec w `testy/golden/SL10596945_fasola_odseparowana/`;
  księgowość naprawy w `wyniki/test/SL10596945/POPRAWKA_region_warstwa.md`.
