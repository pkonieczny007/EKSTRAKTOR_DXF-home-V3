---
name: dxf-ekstrakcja
description: Pelny pipeline produkcyjny EKSTRAKTOR_DXF V3 na zleceniu - wielowariantowosc + kontrola kompletnosci + galeria + metryka. Recall wiedzy -> typowanie (profil) -> orkiestrator (W-A/W-B/W-C + ocena) -> sprawdzanie AI (nakladki, flagi) -> galeria czlowieka -> metryka zaufania. To WERSJA V3 obok istniejacego /wyciagnij-dxf (V1/V2) - nie podmienia go (decyzja usera). Uzyj gdy uzytkownik chce przepuscic zlecenie przez pelny tor V3, "ekstrakcja V3", "zrob zlecenie wariantami + sprawdzanie", albo wywola /dxf-ekstrakcja.
---

# Skill: dxf-ekstrakcja (V3)

Pelny tor produkcyjny V3 na jednym zleceniu. Logika w skryptach repo - ten skill to
PROCEDURA + recall wiedzy przed dzialaniem (nie powielaj kodu w prozie).

To NOWY skill V3 OBOK `/wyciagnij-dxf` (V1/V2, dziala) - decyzja usera 06.07: nie
podmieniac dzialajacego skilla produkcyjnego. Roznica: V3 = wielowariantowosc +
kontrola kompletnosci (bramka 5/sweep/nakladka) + metryka zaufania.

## Zasady wiazace
Zero blednych DXF na laser (1). Otwory swiete, kontur zamkniety, 1:1 (2). AI moze
status tylko OBNIZYC (5). KAZDA flaga = ogledziny wzrokowe (6). Sweep domyka zlecenie (7).

## Wywolanie
`/dxf-ekstrakcja <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>` (operator dostarcza
gotowe `_conv.dxf` - konwersja DWG->DXF to jego krok, zasada 15).

## Procedura (z korzenia repo)
1. **RECALL WIEDZY** przed ekstrakcja: przeczytaj `kontekst/wiedza/MEMORY.md` +
   `kontekst/` pasujace do klienta/prefiksu rysunku i STOSUJ reguly (konwencje, pulapki).
2. **Audyt** narzedzi: `python zarzadzanie\audyt.py` (kazda sesja od tego).
3. **Typowanie + profil** (informacyjnie; typ DOSTRAJA progi, NIE ogranicza silnikow):
   `python produkcja\typowanie.py <rysunek_conv.dxf>` - odczytaj typ + profil
   (geom_kolory, spodziewane_lustra, cechy_odseparowane, uwaga).
4. **EKSTRAKCJA (wielowariantowosc)**:
   `python produkcja\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>`
   (default = W-A/W-B/W-C + ocena wybiera zwyciezce; `--parytet` = sam W-B do debug).
   -> `<zeinr>_ocena.csv` + wyjsciowe DXF + `warianty/`.
5. **RAPORT + wykaz**: `python produkcja\raport.py <folder_wynikow> <rysunek_conv.dxf>
   --wykaz <wykaz.xlsx>` -> `<zeinr>_podsumowanie.csv` + KOPIA wykazu ze statusami
   (oryginal nietkniety). **GWINT - DOMYSLNIE ZACHOWANY (kazdy material)**: wykryty
   gwint (okrag+luk ~270 st) zostaje, koloruje sie na ZOLTO + nota 'gwint MX', status
   pozycji obniza do 🟡 (jak fazowanie - do decyzji operatora, nie zgadujemy srednicy
   palenia). **Transformacja TYLKO na wyrazne zadanie**: dodaj flage
   `--transformuj-gwint` -> luk usuniety, okrag powiekszony na CZERWONO wg KLASY
   materialu (`config/gwinty.yaml`: trudnoscieralne HB4xx M12=10.6 / zwykle S235/S355
   M12=10.2; klasa z Bezeichnung, wymaga --wykaz). Nieznana wartosc -> zostaje ZOLTY.
6. **SPRAWDZANIE AI** (kompletnosc): `python sprawdzanie\ai\sprawdz_folder.py
   <folder_wynikow> <rysunek_conv.dxf>` -> nakladki + flagi. **OBEJRZYJ 100% flag**
   (`sprawdzanie_ai/*_nakladka.png`) od najwiekszych roznic - zakreslenia czerwone
   pokazuja GDZIE brak. AI moze tylko OBNIZYC status.
7. **GALERIA CZLOWIEKA**: `python sprawdzanie\czlowiek\przeglad.py <folder_wynikow>
   --rysunki <folder>` -> `przeglad.html` + worklist. 🔴/🟡 obowiazkowo + probka 🟢.
   Werdykty OK/BLAD -> `--werdykty <csv>` (BLAD -> golden PRZED naprawa, zasada 11).
8. **METRYKA ZAUFANIA**: `python zarzadzanie\metryka.py <folder_wynikow>` -> odsetek do
   przegladu, semafory, trend. Cel: odsetek i bledy MALEJA w czasie.
9. **NAUKA** (po zleceniu): `/dxf-nauka` - destylacja etykiet -> wnioski (za akceptacja).

## Reguly domenowe (recall - NIE ucz od nowa)
- `.dxf` bywa DWG w przebraniu (naglowek AC1021) - operator konwertuje.
- Linia giecia = kolor 6 (magenta); geometria bywa na kolorze 2/4/7/warstwie - nie zakladac 7.
- Lustra P/L: druga poz. o tych samych wymiarach = para (odbijaj); asymetria = 🟡.
- Otwory wspolsrodkowe (fertzing) = 1 cecha; gwint = okrag + luk ~270 (nie dedup, nie otwarty).
- Gwint DOMYSLNIE zachowany (okrag+luk) + ZOLTY 'do decyzji' na KAZDYM materiale (nie
  zgadujemy srednicy palenia). Transformacja (luk out, okrag +czerwony) TYLKO na zadanie
  operatora (--transformuj-gwint), srednica wg klasy: Hardox/HB4xx M12->10.6, zwykla M12->10.2.
- Zgodny wymiar NIE dowodzi kompletnosci (sweep-vs-zrodlo obowiazkowy).

## Uwagi
- Nic 🟢 bez TRZECH kontroli (liczbowa bilans + wizualna + zamkniete kontury na koncu).
- Watpliwosc => `_DO_SPRAWDZENIA` (czlowiek), nigdy zgadywanie.
- `wyniki/` nie commitowac; PNG zawsze czarne tlo.
