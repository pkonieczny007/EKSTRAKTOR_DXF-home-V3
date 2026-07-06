---
name: dxf-sprawdz
description: Sprawdzanie AI folderu wynikow EKSTRAKTOR_DXF V3 - kontrola kompletnosci. Dla kazdej wyekstrahowanej pozycji generuje nakladke wynik-na-zrodlo, liczy pokrycie_zrodla i flaguje MOZLIWY BRAK CECHY (100% flag do ogledzin, zasada 6); auto-obniza zielony->zolty gdy pokrycie<97 (zasada 5, AI tylko obniza). Opcjonalnie zapisuje WATPLIWOSC (zrodlo=ai) do etykiet. Uzyj gdy uzytkownik prosi "sprawdz wyniki AI", "kontrola kompletnosci folderu", "zrob nakladki", "oflaguj braki", albo wywola /dxf-sprawdz.
---

# Skill: dxf-sprawdz

Sprawdzanie AI folderu wynikow. Logika w `sprawdzanie/ai/sprawdz_folder.py`
(+ `nakladka.py`) - ten skill to procedura + interpretacja flag, nie powielaj kodu.

**Zasady wiazace:** AI moze status tylko OBNIZYC (5). KAZDA flaga = ogledziny
wzrokowe (6) - driver PRODUKUJE material (PNG + miary), decyzje podejmuja OCZY.
Driver NIE zamyka flagi zielono. Od NAJWIEKSZYCH roznic (najgrozniejsze braki).

## Wywolanie
`/dxf-sprawdz <folder_wynikow> <zrodlo_conv.dxf>` albo gdy uzytkownik prosi o kontrole
kompletnosci wynikow. `<folder_wynikow>` musi miec `<zeinr>_ocena.csv` (wielowariant)
lub `<zeinr>_raport.csv` (parytet) + wyjsciowe DXF.

## Procedura
1. Uruchom z korzenia repo:
   `python sprawdzanie\ai\sprawdz_folder.py <folder_wynikow> <zrodlo_conv.dxf>`
   (dodaj `--werdykty-ai`, jesli maja powstac etykiety WATPLIWOSC zrodlo=ai).
2. Odczytaj `<zeinr>_sprawdzanie_ai.csv` i wyjscie: liczba flag do ogledzin,
   ktore pozycje AI obnizylo (zielony->zolty), `pokrycie_zrodla` per pozycja.
3. **Dla KAZDEJ flagi (100%!):** otworz `sprawdzanie_ai/<zeinr>_p{N}_nakladka.png`
   i OBEJRZYJ - geometria zrodla (szara) BEZ czerwonej nakladki = MOZLIWY BRAK CECHY.
   Kolejnosc oględzin: od najnizszego `pokrycie_zrodla` (najwieksze braki).
4. Werdykt z OGLEDZIN (nie z rozumowania o wielkosci roznicy, zasada 6):
   - brak potwierdzony wzrokiem -> pozycja do naprawy (silnik W-C region+warstwa) +
     NOWY przypadek do `testy/golden/` PRZED naprawa (zasada 11),
   - false-positive -> wymaga DOWODU (para PNG) i idzie do galerii czlowieka.
5. Nie podnos statusu zadnej pozycji (zasada 5). Rozstrzyga skrypt albo czlowiek.

## Uwagi
- `pokrycie_zrodla < 97%` = sygnal (FLAGER, nie wyrok) - decyduja oczy.
- Pozycje `czerwony` bez pliku (brak wyjsciowego DXF) = czlowiek rysuje.
- Lustra: nakladka uzywa boxa blizniaka + auto-wykrycia odbicia (P/L).
- Nastepny krok po sprawdzaniu: `/dxf-przeglad` (galeria czlowieka + werdykty).
