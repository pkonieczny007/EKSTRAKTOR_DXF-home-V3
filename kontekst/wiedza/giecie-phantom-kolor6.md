---
name: giecie-phantom-kolor6
description: "Na czesci rysunkow linia giecia to PHANTOM kolor 6 (magenta), a silnik myli PHANTOM z osia i ja usuwa"
metadata: 
  node_type: memory
  type: project
  originSessionId: 968ce1f5-7363-4270-b157-e1aba3716d08
---

W extract_positions.py: AXIS_LINETYPES zawiera PHANTOM (traktowane jak os ->
USUWANE), a BEND_LINETYPES tylko DASHDOT. Ale u czesci klientow (np. zlecenie
59_6940, Übergabeschurre SL10372141) **linia giecia jest narysowana jako PHANTOM,
kolor 6 (magenta)** - silnik ja wtedy wyrzuca i giecie znika z wyniku.

Niezawodny wyznacznik giecia = **kolor 6 (magenta)**, niezaleznie od linetype
(magenta to konwencja warstwy GIECIE, patrz CLAUDE.md). Przy recznym dobieraniu
pozycji (zwlaszcza par P/L) brac LINE/ARC color==6 w obrysie i kłasc na warstwe
GIECIE.

WAZNE dla par prawy/lewy (P/L = gespiegelt): linie giecia MUSZA zostac - bez nich
nie wiadomo gdzie i w ktora strone giac, a to jedyne co rozni P od L. p4(L) =
lustro p3(P) razem z liniami giecia. Patrz [[sbm-legenda-lustro]].

## SBM: ZLOZENIE vs ROZWINIECIE (zlecenie 24_0417, SL10602713)
SBM rysuje na jednym arkuszu **rzut boczny + ROZWINIECIE**; rozwiniecie ma linie
giecia zaznaczone na SZARO (kolor 251) i FIOLETOWO/magenta (kolor 6), czesto DASHED.
- Tryb warstwowy (1NN) potrafi zlapac WIDOK ZLOZENIOWY (koniec ramienia = wciecie
  pasujace do sasiada), a nie rozwiniecie. Rozwiniecie ma pelny detal (np. OKO/tuleja
  z magentowymi lukami giecia). Brac widok z magenta+szaro = rozwiniecie.
- Silnik wyrzuca DASHED (idzie do `dashed`, nie do wyniku) -> giecie magenta-DASHED
  GINIE. Dobierac recznie `color==6` z okna rozwiniecia na warstwe GIECIE.
- Kontur = kolor 7 (bialy); osie = kolor 4 CENTER (pomijac); ramka = 251 (pomijac).

## NAJPIERW znajdz ROZWINIECIE (nie zloz.), dopiero potem ew. DO_SPRAWDZENIA
Na 24_0417 dwa razy wzialem zly widok (zlozenie), bo nie sprawdzilem WSZYSTKICH
rzutow. SBM daje kilka rzutow tej samej czesci - trzeba wybrac ROZWINIECIE:
- ma linie giecia (magenta 6 / szare 251), holes z osiami, konturem 1:skala.
- SL10602713: rozwiniecie = PRAWY widok (411, kontur ZOLTY kolor 2, +magenta giecie
  przy lokciu), NIE lewy (438) ani widok z okiem. Wymiar 417x211.
- SL10602716: rozwiniecie = gorny plaski PASEK "kapeluszowy" z 3 otworami (kontur
  BIALY 7, wys. ~y189-196 = 33mm), NIE rura 3D ani pas boczny pod nim. Wymiar 550x33.
Najlepiej: RENDEROWAC caly rysunek + poprosic uzytkownika o screen z zaznaczeniem,
gdy jest kilka podobnych rzutow. Kontur bywa 2(zolty)/7(bialy); osie=4 CENTER (pomin),
ramka=251 (pomin). Skalowac po dluzszym boku do wykazu.

`_DO_SPRAWDZENIA` + reka TYLKO gdy naprawde brak rozwiniecia plaskiego (tylko forma
zgieta/3D). Patrz [[sbm-okragle-niewyciagalne]].
