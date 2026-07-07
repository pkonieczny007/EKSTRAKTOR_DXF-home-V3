# SL40062903_p1 - ZGUBIONE OTWORY: otwory INNEGO koloru niz kontur (41_2050)

- Skad: zlecenie 41_2050, werdykt operatora 2026-07-08 ("ZGUBIONE OTWORY! to ten
  wyjatek ze inny kolor otworow niz kontur. czasami sie zdarzaja").
- Blad: V3 i CODEX zgubily otwory (kontury wewn. 2 vs 6 w gotowym) - ekstrakcja po
  jednym kolorze nie widzi otworow innego koloru. **W-D (dwutorowa, UWAGA-pass)
  otwory MIAL** (8 vs 6; nadmiar = nieoczyszczone osie) - dowod metody.
- Wejscie: SL40062903_1.dxf (conv) + bledny V3 + W-D z otworami. Wzorzec: gotowe
  (2_oc_SL40062903_p1_2st_G_2050_.dxf) - UWAGA: gotowe bywa modyfikowane pozniej.
- Test docelowy: ekstrakcja MUSI oddac 6 konturow wewn. (cross-check otworow po
  wszystkich kolorach); wiedza: otwory-inny-kolor-daszek-blindmutter.md.
