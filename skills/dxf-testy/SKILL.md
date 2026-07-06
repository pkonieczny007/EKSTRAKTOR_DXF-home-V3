---
name: dxf-testy
description: Uruchamia PELNA regresje EKSTRAKTOR_DXF V3 jedna komenda i raportuje wynik. Odpala wszystkie testy (regresja, testy_v2, benchmark_v2, znane bledy XFAIL oraz wszystkie testy/test_*.py) przez runner testy/wszystkie.py, zbiera PASS/FAIL i czasy, a przy FAIL pokazuje ktory test padl i ostatnie linie jego wyjscia. Uzyj gdy uzytkownik prosi "odpal testy", "regresja V3", "sprawdz czy nic sie nie zepsulo", "puść wszystkie testy", przed oddaniem zmiany w produkcja/, albo wywola /dxf-testy.
---

# Skill: dxf-testy

Jedna komenda = cala regresja V3. Logika jest w `testy/wszystkie.py` (ten skill to tylko
procedura + interpretacja wyniku - nie powielaj kodu w prozie).

**Warunek oddania zmiany (zasady 10-11):** po KAZDEJ zmianie w `produkcja/` runner musi
byc PASS na PELNYM zestawie (bez `--szybko`).

## Wywolanie
`/dxf-testy` albo gdy uzytkownik prosi o regresje / uruchomienie testow.
Opcjonalny argument `--szybko` = szybki przebieg (pomija wolne testy silnika/benchmark) —
tylko do iteracji, NIE do oddania zmiany.

## Procedura
1. Uruchom runner z korzenia repo:
   - pelny (domyslny, przed oddaniem zmiany):  `python testy\wszystkie.py`
   - szybki (iteracja robocza):                `python testy\wszystkie.py --szybko`
2. Odczytaj TABELE WYNIKOW z wyjscia (kolumny: nazwa | wynik | czas) i linie
   `PODSUMOWANIE: N/M PASS`. Przekaz ja uzytkownikowi 1:1 (to jest raport).
3. **Gdy wszystko PASS** → zamelduj `N/M PASS` + laczny czas; zmiane mozna oddac.
4. **Gdy jest FAIL:**
   - podaj, KTORE testy padly (z tabeli) i ich kod wyjscia,
   - pokaz sekcje `SZCZEGOLY BLEDOW` (runner sam drukuje ostatnie linie wyjscia
     kazdego padlego testu) — to wskazuje przyczyne,
   - w razie potrzeby uruchom sam padly test bezposrednio po szczegoly, np.
     `python testy\regresja.py`,
   - NIE oddawaj zmiany dopoki nie ma PASS (zasada 10). Napraw przyczyne albo zglos.
5. Jesli przebieg byl `--szybko`, przypomnij GLOSNO, ze pominieto benchmark_v2 /
   test_sweep_54_4867 / test_gr4 i przed oddaniem trzeba odpalic pelny zestaw.

## Uwagi
- `regresja_znane_bledy` jest zielony przy XFAIL (znane, jeszcze-nie-zrobione cele
  silnika) — czerwony tylko przy REGRESJI (cos naprawionego znow padlo). `[XPASS]`
  w jego wyjsciu = przypadek naprawiony → awansuj go do `testy/regresja.py`.
- Runner sam wykrywa nowe `testy/test_*.py` — dodanie testu nie wymaga zmiany skilla.
- Kod wyjscia runnera: 0 = wszystkie uruchomione PASS, 1 = jest FAIL.

## Srodowisko
Windows, Python 3.13 (`ezdxf`, `openpyxl`, `matplotlib`, `pyyaml`, `shapely`).
Pelny zestaw trwa dluzej (benchmark V2 vs V1 na 36 plikach + testy uruchamiajace silnik).
