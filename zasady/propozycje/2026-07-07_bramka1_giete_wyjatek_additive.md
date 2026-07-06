# Propozycja: bramka 1 - wykaz to BAZA, dla gietych DODATKOWA metoda (nie zamiast)

- **Data / autor:** 2026-07-07, operator (zasada "wykaz to baza") + AI (spisanie)
- **Status:** propozycja → golden (SL10602713) → testy → merge do `ocena.py` / `raport.py`

## Zasada nadrzedna (operator 07.07)

**"Musimy porownywac z wymiarem z wykazu. Czasami sa wyjatki, wiec mozemy zrobic
dodatkowe metody. Ale nie mozemy zrezygnowac z wykazu, bo to baza."**

=> Bramka 1 (wymiar_dxf vs Abmess wykazu, tol=max(1mm,0.2%)) **ZOSTAJE bez zmian jako
baza**. Wynik wykazu jest ZAWSZE liczony i raportowany. Wyjatki obsluguje warstwa
DODATKOWA, ktora NIE usuwa bazy - tylko lagodzi twardy werdykt tam, gdzie wiadomo, ze
wykaz bywa nominalny/blledny. Analogia: zasada 5 (AI dokłada, nie zastepuje).

## Problem, ktory rozwiazuje

Czesci giete (G/GS) maja w wykazie wymiar ZLOZONY / nominalny (operator mierzy do osi lub
promienia giecia), a laser potrzebuje ROZWINIECIA - inny wymiar. Dzis bramka 1 daje
twardy rozjazd -> ocena dyskwalifikuje (🔴), choc rozwiniecie moze byc poprawne.
Dowod: SL10602713 (G) - W-A interior=4 = reczny wzorzec, ale wymiar 421.65 vs wykaz 417
-> 🔴. Rozjazd wynika z natury giecia, nie z bledu ekstrakcji.

## Tresc zasady (dodatkowa metoda, additive)

1. Bramka 1 liczy jak dziś (baza): `uwagi_wymiar = ok | ROZJAZD (max/min ...)`. Zawsze.
2. **Detekcja wyjatku "gieta":** pozycja ma giecie (n_bend>0 z raportu / warstwa GIECIE /
   technologia G|GS). 
3. **Gdy ROZJAZD wymiaru I pozycja gieta:** NIE dyskwalifikowac twardo (🔴). Degradowac do
   🟡 z powodem "gieta: wymiar_dxf X vs wykaz Y - wykaz bywa do osi/promienia, sprawdz
   rozwiniecie". Werdykt wykazu (ROZJAZD) zostaje w raporcie - baza nienaruszona.
4. **(Opcjonalnie, mocniejsza metoda) porownanie z rozwinieciem:** jesli na rysunku jest
   zaznaczone rozwiniecie (rzut z linia giecia + opisem), porownac wymiar_dxf z nim jako
   DRUGIM zrodlem prawdy. Zgodnosc z rozwinieciem -> 🟡 pewniejszy; brak -> 🟡 do reki.
   To metoda geometryczna (znalezienie rzutu rozwiniecia) - kandydat do
   [[fable-advisor-trudne-problemy]].
5. Pozycja gieta z rozjazdem NIGDY nie staje sie 🟢 automatem - zawsze co najmniej 🟡
   (czlowiek potwierdza), bo wykaz sie nie zgadza (baza). Flager nie podnosi statusu.

## Przyklad referencyjny (golden)

SL10602713 p1 (24_0417): G, W-A interior=4=wzorzec, wymiar 421.65 vs wykaz 417 (rozjazd
~5mm z natury giecia). Wejscie: dok_conv/SL10602713_1.dxf; wzorzec reczny
8_S355_SL10602713_p1_1st_G_0417_[L/P].dxf (406.5x219.5). Oczekiwanie po zmianie:
🟡 "gieta - sprawdz rozwiniecie", nie 🔴.

## Kryterium awansu (zasada 8/10/11)

Golden SL10602713 -> zmiana w ocena.py (degradacja 🔴->🟡 tylko dla gietych z rozjazdem,
baza wykazu raportowana) -> regresja.py + benchmark_v3 0 regresji (pozycje niegiete bez
zmian!) -> potwierdzenie operatora -> merge. Ryzyko: nie osłabic bramki dla NIE-gietych.
