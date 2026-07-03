---
name: giecie-kiedy-nanosic-pl-skos
description: "Linie giecia nanosimy TYLKO gdy pozycja ma warianty prawy/lewy (P/L) albo gdy giecie jest pod skosem; dla nie-P/L z gieciem prostym nie rysujemy"
metadata:
  type: feedback
---

Doprecyzowanie reguly linii giecia (zlecenie 54_4867, operator SBM). Wczesniej
nanieslismy magentowe linie giecia na KAZDA gieta pozycje - operator to poprawil:

**Linie giecia (kolor 6 magenta, warstwa GIECIE) nanosimy TYLKO gdy:**
1. pozycja ma warianty **prawy/lewy (P/L)** - regex `_p\d+[PL]` w nazwa_rysowanie
   (bez linii giecia nie wiadomo ktora reka, to jedyne co rozni P od L), LUB
2. **giecie jest pod skosem** - linia giecia nie rownolegla do osi X/Y (odchylenie
   >5 stopni; np. wspornik gniety po przekatnej).

Dla pozycji **nie-P/L z gieciem prostym** (poziom/pion) linii giecia NIE rysujemy.

**Why:** operator na plaskim, prostym gieciu nie potrzebuje linii - wie z wymiaru;
nadmiar linii smieci rozwiniecie. Ale przy P/L i skosach linia jest konieczna.

**How to apply:** przy budowie DXF: is_PL = hand P/L w nazwie; has_skos = jakas linia
kolor6 w zrodle ma odchylenie >5deg od osi. Rysuj giecia gdy `is_PL or has_skos`.
UWAGA: technologia (G/GS) i tak zalezy czy czesc JEST gieta (linie kolor6 w zrodle),
niezaleznie czy je RYSUJEMY. Linie bierzemy ze zrodlowego DWG (kolor 6 CENTER w bbox
widoku), nie z TIF. Patrz [[giecie-phantom-kolor6]], [[sbm-legenda-lustro]].
