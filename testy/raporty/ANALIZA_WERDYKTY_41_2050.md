# ANALIZA zlecenia 41_2050 po werdyktach operatora (2026-07-08)

> Pierwsza pelna partia REALNYCH etykiet w projekcie: 63 pozycje x 3 zrodla
> (V3=W-A/B/C, CODEX, W-D prototyp) vs GOTOWE (laser) + werdykty czlowieka.
> Etykiety: 185 wierszy w `nauka/etykiety/etykiety.csv` (zrodlo=czlowiek).
> Zrodlo werdyktow: `\\QNAP-ENERGO\tmp\EKSTRAKTOR_DXF_test\41_2050_test\POROWNANIE_41_2050.xlsx`.

## 1. Ranking PO WERDYKTACH CZLOWIEKA (nie po automacie)

| Zrodlo | OK | BLAD | najwazniejsze bledy |
|---|---|---|---|
| **V3** | ~55 (89%) | 7 | izometryk x2, zlozenie x1, lustro poz2 x1, brak linii giecia skos x2, **ZGUBIONE OTWORY (inny kolor) x1** |
| **CODEX** | ~54 (87%) | 7 | jak V3 (te same pozycje) + brak pliku x1 |
| **W-D** (prototyp 20 min) | 29 (47%) | 33 | **28 = CZYSZCZENIE** (osie/linie srodkowe/zielone linie/linie giecia w dol i pelnej dlugosci), fazowanie x1, izometryk/box x4 |

Kluczowe: **automat (KONTURY_ROZNE vs gotowe) MYLIL SIE NA NIEKORZYSC** - duza czesc
"roznic" to POZNIEJSZE MODYFIKACJE RECZNE w gotowych (poszerzone otwory, naciecia pod
rolki, otwory pod nakladki daszka, dodane/skrocone linie giecia). Werdykt czlowieka:
"generowanie prawidlowe". -> `kontekst/wiedza/gotowe-pozniejsze-modyfikacje-reczne.md`.

## 2. Bledy wspolne V3+CODEX (prawdziwe braki systemu)

1. **SL40062903_p1 - ZGUBIONE OTWORY, otwory innego koloru niz kontur** (2 vs 6).
   W-D je MIAL (UWAGA-pass - dowod metody dwutorowej operatora). Golden:
   `SL40062903_p1_otwory_inny_kolor/`. Fix: UWAGA-pass do produkcji + cross-check
   liczby otworow ze skryptem.
2. **SL40036103_p2 - poz2 jest LUSTREM poz1** (nie wykryte przez zadne zrodlo) +
   p1 brak linii giecia pod skosem. Golden: `SL40036103_lustro_skos_giecia/`.
3. **SL40047020_p1, SL40091010_p1 - IZOMETRYK pobrany.** Sygnal (operator, 2. raz):
   OPIS LINII GIECIA w obrebie konturu wskazuje wlasciwy widok. Odpowiedz czlowieka
   w `SL40047020_p1_izometryk/czlowiek_odpowiedz/`.
4. **SL40033136_p1 - ekstrakcja ze ZLOZENIA dxf = zakaz** (rozjazd wymiaru; V3).
5. **SL10585163_p2 - brak GORNEJ linii giecia przy skosie** -> TRUDNA zasada linii
   giecia (kierunek UP / odwracanie lustra / skracanie):
   `kontekst/wiedza/linie-giecia-kierunek-lustro-skracanie.md`.

## 3. W-D - diagnoza po pierwszym boju

- **Metoda dwutorowa POTWIERDZONA co do zasady:** wygrala tam, gdzie V3 zgubil otwory
  (62903), i miala poprawne gorne linie giecia (10585163_p2 ok).
- **85% bledow W-D = jedna klasa: CZYSZCZENIE** (tor 2 za slaby): osie/linie srodkowe/
  pojedyncze kolorowe linie zostaja; linie giecia w DOL i PELNEJ dlugosci zostawione
  (operator: w dol nie robimy / skracamy); UWAGA-pass wciaga tez luki-osie.
  Operator wprost: "blad czyszczenia po bbox - sprawdzamy kolor/warstwe krawedzi a tu nie".
- Fazowanie: W-D nie dodaje linii fazowania -> wymiar sciety (SL10523531_p2) -
  wpiac `fazowanie.py` do W-D.
- Tor 1 (box z W-A) odziedziczony: izometryki/za duzy obszar/zly detal (4 szt.) -
  znane, adresuje detektor rozwiniecia (WNIOSKI ZUBEHOR) + sygnal tekstowy.

## 4. Co poprawiamy (kolejnosc)

1. **W-D czyszczenie v2** (najwiekszy zysk): filtr osi/linii srodkowych (linetype
   DASHDOT/MITTE + krzyz osi), linie giecia wg TRUDNEJ zasady (UP/lustro/skracanie),
   UWAGA-pass tylko ZAMKNIETE petle (nie luki osi), fazowanie.py w pipeline W-D.
   Test na golden 41_2050 + ZUBEHOR.
2. **UWAGA-pass do produkcji** (V3): kategoria/bramka "otwory innego koloru" -
   cross-check liczby otworow zrodlo-vs-wynik po WSZYSTKICH kolorach (nie tylko
   trybie ekstrakcji). Golden 62903 = test.
3. **Detektor izometryka/rozwiniecia** (adnotacja giecia w konturze, ELLIPSE>0,
   skala niestandardowa) - domyka 4 bledy widoku z tego zlecenia + ZUBEHOR.
4. **Lustro poz-parzysta** (36103_p2): wykrywanie "poz N = lustro poz N-1" takze
   bez adnotacji (identyczny obrys) - eskalacja 🟡 zamiast pominiecia.
5. Nowe typy/cechy: **daszek** (typ + oznaczenie "otwory pod nakladki dorobia sie
   pozniej"), **blindmutter** (flaga 🟡). Zbierac przyklady.

## 5. Stan nauki

- `nauka/etykiety/etykiety.csv`: **185 etykiet czlowieka** (bylo 0). Pierwsze paliwo
  dla destylacji.
- Golden: +3 przypadki (62903 otwory-inny-kolor, 36103 lustro+skos, 47020 izometryk
  z odpowiedzia czlowieka).
- Wiedza: +3 notatki (linie giecia TRUDNA zasada, gotowe-pozniejsze-mody,
  otwory-inny-kolor/daszek/blindmutter).
- Nastepny krok nauki: `nauka/destylacja.py` na swiezych etykietach + propozycje
  zasad (linie giecia, UWAGA-pass) przez testy do produkcji (zasada 8).
