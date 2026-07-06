# Golden OTWARTY: pipeline wzial widok ZLOZENIOWY zamiast DO PALENIA

**Status:** wejscie gotowe, WZORZEC = widok do palenia (prawy). Do zatwierdzenia po przegladzie.
**Zrodlo:** zlecenie 38_1847 gr6, korekta operatora 2026-07-07 (moja pierwsza diagnoza
"separacja giecia" byla BLEDNA - to nie giecie).

## Co sie STALO (diagnoza po korekcie operatora)

Rysunek SL10585238 (SBM) ma na jednym arkuszu DWA widoki tej samej pozycji p1:
- **widok ZLOZENIOWY** (gora-lewo, bbox zrodla ~54.6,216.9-162.6,262.9): czesc L z 8 slotami
  ORAZ **dospawywanymi elementami** narysowanymi kolorem 6 (magenta) - 2 poziome elementy
  stykajace sie z czescia. To NIE sa linie giecia i NIE nalezy ich ciac.
- **widok DO PALENIA** (gora-prawo, bbox ~255-398 x 216-263): TA SAMA czesc CZYSTA, bez
  dospawien - 8 slotow + stopien + fazowanie na rogu. **To jest wzorzec na laser.**

Pipeline sklastrowal LEWY (zlozeniowy) widok (oba na warstwie 101, te same wymiary 540x230
-> ranking wybral lewy). Skutek: W-C wciagnal 2 dospawienia jako ciete prostokaty
(interior=11), W-A/W-B je pominely (interior=9). Rozbieznosc -> 🟡 do czlowieka.

**Sygnal diagnostyczny:** rozbieznosc wariantow (9 vs 11) sama w sobie sygnalizuje, ze
zlapano widok zlozeniowy (dospawienia liczone niejednolicie). Na widoku do palenia
wszystkie warianty by sie zgodzily.

## Wejscie
- `wejscie/SL10585238_1.dxf`, pozycja p1, warstwa 101, skala 5.0.
- `wynikow_biezacy/_CALY_SL10585238.png` - uklad arkusza (oba widoki).
- `wynikow_biezacy/_WIDOK_DO_PALENIA_p1.png` - poprawny widok (prawy).
- `wynikow_biezacy/SL10585238_p1.dxf` + `.png` - BLEDNY wynik (widok zlozeniowy, z dospawieniami).

## Wzorzec docelowy (po naprawie wyboru widoku)
- Pipeline wybiera widok DO PALENIA (prawy): 8 slotow + stopien + fazowanie, BEZ dospawien.
- Warianty zgodne (W-A=W-B=W-C) -> 🟢/🟡.
- Fazowanie na rogu wykryte i oznaczone jako technologia (patrz propozycja fazowania).

## Kryterium PASS testu (po awansie)
Zwyciezca nie zawiera 2 poziomych elementow koloru-6 dospawien; bbox zrodla po stronie
prawego widoku (x>250); interior spojny miedzy wariantami.
