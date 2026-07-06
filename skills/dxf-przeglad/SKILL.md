---
name: dxf-przeglad
description: Sesja przegladu czlowieka EKSTRAKTOR_DXF V3 - galeria kafelkow (wynik obok zrodla z ramka skad-wycieto obok nakladki) + semafor finalny + worklist werdyktow. 🔴/🟡 obowiazkowo, 🟢 probka co N-ty. Czlowiek wpisuje OK/BLAD do worklisty, import do nauka/etykiety (BLAD -> golden PRZED naprawa). Uzyj gdy uzytkownik prosi "przeglad wynikow", "galeria do sprawdzenia", "chce ocenic pozycje", "zbierz werdykty", albo wywola /dxf-przeglad.
---

# Skill: dxf-przeglad

Galeria przegladu czlowieka + zbieranie werdyktow. Logika w
`sprawdzanie/czlowiek/przeglad.py` (reuzywa raport.scal + galeria V2 + werdykty).
Ten skill to procedura - nie powielaj kodu w prozie.

**Zasada 3:** czlowiek porownuje OBRAZKI, nie otwiera CAD. **Zasada 11:** kazdy BLAD
= przypadek do `testy/golden/` PRZED naprawa. Semafor FINALNY = obnizenie AI ma
pierwszenstwo (zasada 5).

## Wywolanie
`/dxf-przeglad <folder_wynikow>` (opcjonalnie `--rysunki <folder>` `--probka <N>`).
Najlepiej PO `/dxf-sprawdz` (wtedy kafelki maja nakladki i obnizenia AI).

## Procedura
1. Zbuduj galerie z korzenia repo:
   `python sprawdzanie\czlowiek\przeglad.py <folder_wynikow> [--rysunki F] [--probka N]`
   -> `przeglad.html` + `<zeinr>_werdykty_do_wypelnienia.csv`.
2. Otworz `przeglad.html`. Kolejnosc kafelkow: 🔴 -> 🟡 -> 🟢. Przejrzyj:
   - **🔴/🟡: OBOWIAZKOWO wszystkie** (kazdy z jawnym powodem),
   - **🟢: tylko PROBKA** (badge PROBKA; reszta zielonych zliczona, nie renderowana).
   Kazdy kafelek: wynik | zrodlo (zoom, klik=caly arkusz z ramka) | nakladka.
3. Dla kazdej ocenionej pozycji wpisz do `<zeinr>_werdykty_do_wypelnienia.csv`
   kolumne `werdykt` = `OK` albo `BLAD`, przy BLAD `kategoria` z listy
   (brak_otworu | otwor_nieokragly_zgubiony | zla_skala | zly_wymiar |
   kontur_otwarty | zle_lustro | obca_geometria | inne) + opcjonalnie `uwagi`.
4. Zaimportuj werdykty do systemu nauki:
   `python sprawdzanie\czlowiek\przeglad.py --werdykty <wypelniony.csv>`
   -> dopisze do `nauka/etykiety/etykiety.csv`; kazdy BLAD przypomni o golden.
5. Dla kazdego BLAD: NAJPIERW przypadek do `testy/golden/`, POTEM naprawa (zasada 11).

## Uwagi
- Odsetek probki zielonych maleje ze wzrostem zaufania (metryka `/dxf-audyt`).
- Pozycje 🔴 "czlowiek rysuje" -> gotowy plik trafia do golden jako wzorzec.
- Po przegladzie: `/dxf-nauka` (destylacja etykiet -> wnioski).
