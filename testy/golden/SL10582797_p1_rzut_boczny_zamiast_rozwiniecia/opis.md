# Golden: system wzial RZUT ZGIETEJ CZESCI zamiast rozwiniecia; czlowiek ZAZNACZYL widok na PNG

**Status:** wejscie + zaznaczenie czlowieka gotowe (wzorzec-DXF NIE istnieje — czlowiek
wskazal widok, nie rysowal; to definiujacy przyklad KATEGORII 6). Znany blad wyboru
widoku (XFAIL dla detektora rozwiniecia; regresyjnie: pozycja MUSI zostac czerwona).
**Zrodlo:** zlecenie 38_1847_ZUBEHOR, SBM SL10582797 "QUERVERBINDUNG MOTORABDECKUNG",
operator 2026-07-06. Pelna analiza pomiarowa: WNIOSKI.md w golden
`SL10582652_p1_widok_z_gieciem/` (wspolny dokument dla serii zlego wyboru widoku).

## Co sie STALO

Rysunek (A4, tabelka 1:5 i 1:10) ma TRZY klastry czesci:
- **ROZWINIECIE do palenia** = warstwa **51** (lewy widok): 14.88x104.93 w zrodle,
  skala 1:5 (dim "527" meas=105.31 -> 5.004; dim "76" meas=15.25 -> 4.984) ->
  ~74.4x524.7 bbox (nominalnie 76x527). Kontur ZAMKNIETY (0 otwartych koncow;
  polygonize: outer + 2 okregi D12), otwory (2x CIRCLE D2.4 -> D12, wyciecie R10/D17
  na haku), **linia giecia kolor 6 Continuous L=6.00 pod katem 59 st.** (giecie
  SKOSNE, "bend up 90"). **OBA wymiary wykazu (527x76) zgodne przy JEDNEJ skali 5
  — wykaz POPRAWNY** (inaczej niz w SL10582652).
- **RZUT ZGIETEJ CZESCI** = warstwa 101, srodkowy: 8.00x101.81 (H = dokladnie dim
  referencyjny "(509)" = dlugosc PO zgieciu w 1:5); 13 ELLIPSE (4 DASHED = ukryte
  otwory), 7 LINE kol.6 DASHED, 0 CIRCLE, 0 linii giecia, otwarty kontur.
- **Poglad "(M / S 1:10)"** = warstwa 101, prawy-dol: 6.56x50.36, 17 ELLIPSE.

System (wA/wB) wzial SRODKOWY rzut zgietej czesci (zgodnosc encja-w-encje ze zlym
plikiem: 36 encji) i naciagnal skale do 5.176 (=527/101.81) -> 41.41x527.00;
szerokosc 41.41 vs wykaz 76 -> "brak zgodnosci proporcji" + otwarty kontur ->
SLUSZNIE czerwony. Blad: rozwiniecie bylo na warstwie 51 obok. Uwaga: adnotacja
"bend up 90" jest na renderze, ale NIE jako TEXT/MTEXT (rozbita na male linie) —
sygnal tekstowy tu niedostepny, musza dzialac sygnaly geometryczne.

## Wejscie
- `wejscie/SL10582797_1_conv.dxf` — zrodlo (A4; + render PNG obok).
- `wejscie/SL10582797_p1_ZLY_WIDOK_system_527x41.dxf` — bledny wynik systemu
  (rzut zgietej czesci x5.176; 13 ELLIPSE; 41.41x527.00).

## Wzorzec (zaznaczenie czlowieka — KATEGORIA 6)
- `czlowiek_zaznaczenie/SL10582797-zaznaczenie.png` — czerwone kolko operatora na
  LEWYM widoku (rozwiniecie). Czlowiek NIE rysowal DXF: wskazal wlasciwy klaster.
  Docelowy mechanizm: pipeline tnie widok z tego bbox silnikiem W-C, skaluje x5
  i przepuszcza przez PELNE bramki.

## Kryterium PASS
1. **Regresyjne (obowiazuje DZIS):** pipeline nie oddaje p1 jako zielony/zolty
   z rzutem zgietej czesci — status czerwony/do czlowieka.
2. **Docelowe (detektor rozwiniecia, wniosek A z WNIOSKI.md):** wybrany klaster =
   warstwa 51 (zamkniety kontur + CIRCLE>0 + linia giecia + oba wymiary wykazu przy
   skali 5.0); klastry z ELLIPSE>0 / otwartym konturem NIE wygrywaja rankingu.
   Wynik 1:1 ~76x527 przechodzi bramke 1 wobec wykazu.
3. **Docelowe (kategoria 6, wniosek C):** po wskazaniu bbox z zaznaczenia PNG
   pipeline oddaje DXF rozwiniecia przechodzacy bramki (zamkniety kontur, otwory,
   linia giecia na warstwie GIECIE) — czlowiek wskazal WIDOK, kontrola zostaje.
