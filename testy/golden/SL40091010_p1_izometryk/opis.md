# SL40091010_p1 - rzut PO GIECIU zamiast rozwiniecia (41_2050)

- Skad: zlecenie 41_2050 (werdykt 2026-07-08), rysunek `SL40091010_1.dxf` (conv),
  wykaz roboczy `wykaz_41_2050.xlsx` (poz.1 blacha, dims 389 x 159).
- Blad: silnik oddal WIDOK PO GIECIU (rzut boczny) zamiast plaskiego rozwiniecia -
  `3_S235_SL40091010_p1_2st_G_2050_ZLY_rzut_po_gieciu.dxf` (159.1 x 68.0, geo detektora
  ~ -4: elipsy jako okregi rzutowane, kontur czesciowo otwarty). Poprawny widok
  rozwiniecia to klaster 194.3 x 84.3 (skala 2.0, orto45=1.0, 4 okregi + adnotacja
  giecia -> geo detektora ~ +7).
- Co testuje: DETEKTOR ROZWINIECIA (produkcja/kontrola/detektor_rozwiniecia.py) -
  score_rozwiniecie musi PREMIOWAC rozwiniecie (194x84, geo ~+7) i KARAC rzut
  po gieciu (159x68, geo ~-4 <= prog anty-rozwiniecia). Sciezka awaryjna rankingu
  (brak prop-matchu strzalowego) wybiera argmax geo = rozwiniecie, nie rzut.
- Wzorzec docelowy: plaskie rozwiniecie 389 x 159 (skala 2.0), wysrodkowane 1:1,
  z otworami i liniami giecia na warstwie GIECIE.
