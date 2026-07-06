# SL40034116_p1 — finalny DXF ZGUBIL ~13 otworow (Langloch) przy zgodnym wymiarze

- **Skad:** zlecenie 38_1847 (gr5), rysunek `SL40034116_1_conv.dxf` (S235JR/S235JRC,
  s=5/12 — NIE Hardox). Znalezione przez fable-advisor 2026-07-07, POTWIERDZONE niezaleznym
  pomiarem (Opus, polygonize).
- **Co testuje:** finalny produkcyjny `wyniki/38_1847/gr5/SL40034116_p1.dxf` (+ blizniak
  `p2_LUSTRO_z_p1`) ma kontur ZAMKNIETY, wymiar zgodny z wykazem (808×842) i przechodzi
  WSZYSTKIE bramki — a mimo to zgubil ~13 realnych otworow wewnetrznych (Langloch:
  LL140×90, LL111×70, 4×LL40×18, 4×Ø12, pary LL30×12/LL26×14 prawej kolumny). Zadna
  bramka nie krzyczala (klasyka 54_4867: zgodny wymiar + domkniety kontur != kompletnosc).
- **Pomiar (dowod liczbowy, dwa niezalezne):**
  - fable: interior finalny=25 vs region-zrodlo(warstwa 51)=38; 13 twarzy bez odpowiednika;
    test symetrii 0/13 (to NIE lustro, realny brak).
  - Opus (polygonize, prec 0.01): finalny faces=**26**, kandydat W-C=**39** (delta 13);
    CIRCLE=7 w obu (okregi sie zgadzaja — brak dotyczy Langlochow, nie okraglych).
  - Dowod trzeci: adnotacje TIF zrodla (`wejscie/dowod_TIF.png`) dokladnie na brakujacych
    cechach.
- **Przyczyna:** historyczny tryb ekstrakcji "(bez warstw, col7/all, gap=8)"
  (`wyniki/38_1847/SL40034116/SL40034116_raport.csv`) — geometria kazdego z 7 widokow
  lezy na WLASNEJ warstwie numerycznej (51/103/54/56/58/110/111) i widoki nachodza bboxami;
  tryb po-kolorze mieszal warstwy i gubil cechy. Dzisiejszy W-C (region_warstwa, tryb
  warstwa_geom) na warstwie 51 daje interior=38, 0 otwartych, wymiar OK.
- **Kandydat naprawy (DO POTWIERDZENIA CZLOWIEKA, zasada 1 — nie zgadujemy):**
  `wejscie/SL40034116_p1_KANDYDAT_do_potwierdzenia.dxf` (W-C warstwa 51: interior=38,
  okr=7, 0 otwartych, 808.0×842.27). NIE jest to jeszcze `wzorzec/` — brakujace otwory
  na drogim/grubym detalu = czlowiek oglada i potwierdza PRZED uznaniem za prawde
  ([[otwarte-kontury-droga-blacha-do-czlowieka]] — tu grube s=12, ta sama ostroznosc).
- **Znany blad ktory ma lapac (safety net):** sweep/nakladka region-vs-finalny MUSI
  oflagowac SL40034116_p1 (pokrycie_zrodla < 100, skupiska brakow w miejscach Langlochow).
  Sam bilans konturow finalnego pliku (bez porownania ze zrodlem) NIE wystarcza — dlatego
  sweep-vs-zrodlo jest OBOWIAZKOWY (jak SL40052110 z 38_1847_gr4).

## Wejscie
- `SL40034116_1_conv.dxf` — rysunek zrodlowy (7 widokow, warstwy 51/103/54/56/58/110/111).
- `SL40034116_p1_FINALNY_zgubione.dxf` — bledny wynik produkcyjny (faces=26).
- `SL40034116_p1_KANDYDAT_do_potwierdzenia.dxf` — kandydat W-C (faces=39) DO OGLEDZIN.
- `dowod_TIF.png` — adnotacje TIF na brakujacych Langlochach.

## Weryfikacja czlowieka (2026-07-07, operator)

Operator naloczyl kandydata na element wyciagniety z rysunku (zaznaczona warstwa 51):
**otwory i kontury wewnetrzne = OK** (kompletnosc Langlochow potwierdzona wzrokowo).
ALE kandydat **nie ma linii giecia** (zmierzone: 0 koloru 6, 0 warstwy GIECIE, wszystko
na warstwie '0'), a zrodlo (warstwa 51) ma **2 linie giecia kolor 6**; brakuje tez lustra
(blizniak p2). To ZNANE ograniczenie W-C (region+warstwa splaszcza do warstwy 0, nie
rozdziela GIECIE — lekcja 24_0417) — domena BRAMKI 7 (giecie), ogolna, nie zalezna od numeru.

=> Kandydat = poprawny wzorzec KOMPLETNOSCI (kontur ciecia + otwory + kontury wewn.),
ale NIE pelny plik produkcyjny: brak passa giecia (2 linie kol.6 -> warstwa GIECIE) + lustra p2.

## Status
CZESCIOWO POTWIERDZONY — kompletnosc konturow OK (czlowiek). Zostaje: (1) pass giecia
(przeniesc 2 linie kol.6 na warstwe GIECIE) + lustro p2 zanim kandydat -> `wzorzec/`
produkcyjny; (2) test safety-net: sweep-vs-zrodlo MUSI oflagowac finalny plik (delta interior).
Do czasu naprawy: pozycja NIE na laser.
