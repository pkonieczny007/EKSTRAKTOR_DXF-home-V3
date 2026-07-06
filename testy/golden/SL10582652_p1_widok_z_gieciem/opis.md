# Golden: system wzial IZOMETRIE zamiast rozwiniecia z linia giecia (+ bledny wykaz)

**Status:** wejscie + wzorzec CZLOWIEKA gotowe. Znany blad wyboru widoku (XFAIL dla
detektora rozwiniecia; regresyjnie: pozycja MUSI zostac czerwona/do czlowieka).
**Zrodlo:** zlecenie 38_1847_ZUBEHOR, SBM SL10582652 "HALTERUNG FUR MOTOR ABDECKUNG",
korekta operatora 2026-07-06. Pelna analiza pomiarowa: `WNIOSKI.md` (obok).

## Co sie STALO

Rysunek (A3, tabelka 1:2 i 1:5) ma DWA widoki czesci + przekroj:
- **ROZWINIECIE do palenia** = warstwa **51**: 280.00x41.98 w zrodle, skala 1:2
  (dim "560" meas=280.0; dim "84" meas=41.98) -> **560.00x83.96** 1:1. Kontur
  ZAMKNIETY (0 otwartych koncow), 5 konturow wewn. (2 okregi D12 + 3 sloty),
  **1 czysta linia giecia** (kolor 6, DASHDOT, L=280, konce dokladnie na krawedziach
  konturu) + MTEXT "90 st. n.oben k. | bend up 90" WEWNATRZ konturu.
- **IZOMETRIA** = warstwa **101**: 79.50x45.07, 29 ELLIPSE, 0 CIRCLE, otwarty kontur,
  katy linii 25/95/140/160 st. (ortho_frac=0.25), adnotacja "(M / S 1:5)".

System (wA/wB) gonil wykazowa dlugosc **720 (BLEDNA — realne rozwiniecie 560,
liczba 720 nie wystepuje na rysunku w zadnym DIMENSION)**: wzial klaster warstwy
pozycyjnej 101 (izometrie) i naciagnal skale do 9.053 -> 719.73x408.31, otwarty
kontur (50 koncow), "brak zgodnosci proporcji" -> SLUSZNIE czerwony (nic nie poszlo
na laser). Blad: wlasciwym wynikiem bylo rozwiniecie 560x84 z warstwy 51 —
czlowiek narysowal je recznie.

## Wejscie
- `wejscie/SL10582652_1_conv.dxf` — zrodlo (A3; + render PNG obok).
- `wejscie/SL10582652_p1_ZLY_WIDOK_system.dxf` — bledny wynik systemu
  (izometria x9.05; 29 ELLIPSE + 23 LINE + 3 LINE kol.6; 719.73x408.31).

## Wzorzec
- `wzorzec/SL10582652_p1_CZLOWIEK_560x84.dxf` — reczny detal operatora:
  **560.00x83.96**, 31 encji (16 LINE + 12 ARC + 2 CIRCLE kol.7 + 1 LINE kol.6),
  identyczny encja-w-encje z warstwa 51 zrodla przeskalowana x2.

## Kryterium PASS
1. **Regresyjne (obowiazuje DZIS):** pipeline nie oddaje p1 jako zielony/zolty
   z widokiem o otwartym konturze/zlych proporcjach — status czerwony/do czlowieka.
2. **Docelowe (detektor rozwiniecia, wniosek A/B z WNIOSKI.md):** wybrany klaster =
   warstwa 51; wynik po skali 2.0 zgodny ze wzorcem w tolerancji 0.5 mm
   (560.00x83.96), 5 konturow wewn., 1 linia giecia na warstwie GIECIE,
   0 otwartych koncow; raport z powodem "wykaz podejrzany: 720 nieobecne na
   rysunku, 84 zgodne przy 1:2" — pozycja NIE zielona automatem (wykaz to baza).
