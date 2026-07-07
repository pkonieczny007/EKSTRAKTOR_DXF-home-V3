# Benchmark V3 vs V2

V3 (warianty W-A/W-B/W-C + ocena) vs V2 (sam W-B), te same rysunki co regresja.
V3 >= V2 gdy zwyciezca nie gubi konturow, nie oddaje otwartego konturu i
produkuje kazda pozycje (bramki 2+5). Poprawa (wiecej konturow) = OK.

- pozycje: **42**, V3 lepsze: **1**, rowne: **35**, regresje: **0**
- werdykt: **V3 >= V2 (PASS)**

| rysunek | poz | W-B interior | V3 interior | werdykt |
|---|---|---|---|---|
| SL10478356 | 1 | 5 | 5 | rowne |
| SL10478356 | 2 | 0 | 0 | rowne |
| SL10478356 | 3 | 0 | 0 | rowne |
| SL10478356 | 4 | 16 | 16 | rowne |
| SL10478356 | 5 | 0 | 0 | rowne |
| SL10478356 | 6 | 2 | 2 | rowne |
| SL10478356 | 7 | 0 | 0 | rowne |
| SL10478356 | 8 | 0 | 0 | rowne |
| SL10478356 | 9 | 0 | 0 | rowne |
| SL10478356 | 10 | 0 | 0 | rowne |
| SL10478356 | 11 | 0 | 0 | rowne |
| SL10478356 | 12 | 0 | 0 | rowne |
| SL10478356 | 13 | 4 | 4 | rowne |
| SL10478356 | 14 | 2 | 2 | rowne |
| SL10478356 | 22 | - | - | V2 brak - pomijam |
| SL10524825 | 1 | 4 | 4 | rowne |
| SL10524825 | 2 | 1 | 1 | rowne |
| SL10524825 | 3 | 1 | 1 | rowne |
| SL10524825 | 4 | 0 | 0 | rowne |
| SL10582053 | 1 | 2 | 2 | rowne |
| SL40081914 | 1 | 10 | 10 | rowne |
| SL40081914 | 2 | - | - | V2 brak - pomijam |
| SL40081914 | 3 | - | - | V2 brak - pomijam |
| SL40081914 | 4 | 3 | 3 | rowne |
| SL40081914 | 5 | 3 | 3 | rowne |
| SL10578701 | 1 | 20 | 20 | rowne |
| SL10578701 | 2 | 20 | 20 | rowne |
| SL10578699 | 1 | - | - | V2 brak - pomijam |
| SL10578699 | 2 | 2 | 2 | rowne |
| SL10578699 | 3 | 0 | 0 | rowne |
| SL40052144 | 1 | 15 | 15 | rowne |
| SL40852311 | 1 | 86 | 86 | rowne |
| SL400521100 | 1 | 15 | 15 | rowne |
| SL400521100 | 2 | 15 | 15 | rowne |
| SL40052423 | 1 | 9 | 9 | rowne |
| SL40071940 | 1 | 85 | 85 | rowne |
| SL10578806 | 4 | 0 | 0 | rowne |
| SL10578806 | 51 | - | - | V2 brak - pomijam |
| SL10578806 | 55 | - | - | V2 brak - pomijam |
| SL40885240 | 1 | 7 | 7 | rowne |
| SL10584235 | 1 | 7 | 8 | LEPSZE (+1, zw=W-C) |
| SL10584244 | 1 | 7 | 7 | rowne |

Uruchomienie: `python testy\benchmark_v3.py` (kod wyjscia 0 = PASS).
