---
name: dxf-audyt
description: Audyt narzedzi i metryka zaufania EKSTRAKTOR_DXF V3. Porownuje rejestr narzedzi (zarzadzanie/rejestr.yaml) z rzeczywistoscia (pliki, instalacje skilli, testy) i - dla zlecenia - liczy metryke zaufania (odsetek pozycji do przegladu, rozklad semaforow, flagi AI, trend). Uzyj gdy uzytkownik prosi "audyt narzedzi", "sprawdz rejestr", "metryka zaufania", "ile do przegladu", "czy skille sa zainstalowane", albo wywola /dxf-audyt. Kazda sesja zaczyna od audytu.
---

# Skill: dxf-audyt

Dwa pomiary zdrowia systemu: audyt rejestru + metryka zaufania. Logika w
`zarzadzanie/audyt.py` i `zarzadzanie/metryka.py` - skill to procedura.

## Wywolanie
`/dxf-audyt` (sam audyt rejestru) albo `/dxf-audyt <folder_wynikow>` (+ metryka zlecenia).
KAZDA sesja zaczyna od audytu (CLAUDE.md "Szybki start").

## Procedura
1. Audyt rejestru z korzenia repo:
   `python zarzadzanie\audyt.py`
   Odczytaj: `wpisow | rozjazdy | ostrzezenia`. Zglos KAZDY rozjazd (plik nie
   istnieje / skill nie zainstalowany / test nie przechodzi / wersja niezgodna).
   Znany rozjazd: skill `dxf-testy` niezdeployowany do ~/.claude/skills + SecondBrain
   (deploy = krok operatora) - odnotuj, nie alarmuj.
2. Metryka zaufania (gdy podano folder wynikow):
   `python zarzadzanie\metryka.py <folder_wynikow>`
   Odczytaj: ODSETEK DO PRZEGLADU (%), rozklad 🟢/🟡/🔴, flagi AI, ile AI obnizylo,
   werdykty czlowieka OK/BLAD. Wynik dopisany do `testy/raporty/metryka_zaufania.csv`
   (trend). `--bez-trendu` = tylko podglad, bez zapisu.
3. Interpretacja trendu (glowna miara sukcesu): odsetek do przegladu i bledy
   czlowieka MAJA maleC z kolejnymi zleceniami. Wzrost = regres zaufania -> zbadac.

## Uwagi
- Kazda zmiana narzedzia = podbicie `wersja` + wpis w rejestrze (zasada 13) - audyt
  to wychwyci (wersja/test/plik).
- "czas sprawdzania/pozycje" i "bledy NA LASER" (uciekly do produkcji) nie sa jeszcze
  instrumentowane - metryka raportuje bledy WYKRYTE w przegladzie (uczciwie).
