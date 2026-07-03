---
name: cechy-odseparowane-region-warstwa
description: "Klastrowanie po sasiedztwie gubi cechy odseparowane od konturu (fasole, otwory wewnetrzne) i lapie tabelke zamiast rozwiniecia; ratunek = ekstrakcja po REGIONIE+WARSTWIE + liczniki kompletnosci"
metadata:
  type: project
---

Zlecenie 54_4867. Dwie awarie tego samego korzenia - **union-find po sasiedztwie
bboxow** (silnik sklejal w widok tylko encje, ktore sie stykaja/sa blisko):

1. **Zgubione cechy**: slot podluzny ("fasola" 14x30) albo otwor stojacy samotnie
   na srodku blachy = "wyspa" odseparowana od konturu -> osobny klaster/odfiltrowana
   -> WYPADA z wyniku. SL10596945_p3P mial 1 z 2 fasol; SL400521106_p1 mial 4 z 8
   slotow. Wymiar zewnetrzny sie zgadza, wiec kontrola wymiaru NIE lapie.
2. **Tabelka zamiast rozwiniecia**: ramka rysunku laczy wszystko w mega-klaster;
   dimension-match wybral TABELKE (~ten sam rozmiar co czesc). SL10600635_p1
   (wachlarz 481x170) - silnik zlapal tabelke 480x170.

**ROOT FIX (metoda region+warstwa)**: bierz WSZYSTKIE encje warstwy geometrii
(kolor konturu, np. 51/53/103 - nie warstwa wymiarow '1', nie os kolor 4) w bbox
widoku, niezaleznie czy sie stykaja. Transformacja jak kontur:
`translate(-cx,-cy) @ scale(1/skala_rys)`, cx,cy=srodek bbox, skala z raportu.
Cechy odseparowane nie uciekaja; tabelka odpada bo jest na innej warstwie/regionie.

**Bramki QC kompletnosci** (wymiar to za malo - patrz [[sbm-okragle-niewyciagalne]]):
- **Nakladka wynik-na-zrodlo** (galeria) = najpewniejsze, wzrokowe, zero falszywych.
- **Licznik okregow** zrodlo vs wynik = czysty automat (CIRCLE bez warstwy dim/osi).
- **Licznik zamknietych konturow wewnetrznych** (`_licznik_konturow.py`: cyklomatyka
  E-V+C + samozamkniete, minus kontur zewn.) = lapie fasole/perforacje/nietypowe.
  UWAGA: to FLAGER, nie bramka - region-vs-wynik przelicza (balony poz., sasiedzi),
  rownosc blizniakow P/L ma off-by-one (sklejanie koncow po odbiciu). Kazda flaga =
  2 s wzrokiem. Docelowo shapely.polygonize -> dokladne petle, czysta bramka.

**Why:** niepelny DXF idzie na laser jako brakujacy otwor/slot = detal do wyrzucenia.
**How to apply:** gdy licznik/nakladka wykryje brak -> przelacz ekstrakcje na
region+warstwa dla tej pozycji. Uzyte recznie: SL10600635_p1, SL400521106_p1,
fasola SL10596945_p3P. Patrz [[otwory-wspolsrodkowe-zdublowane]].
