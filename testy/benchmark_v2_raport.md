# Benchmark V2 vs V1

Te same rysunki testowe (zlecenia 35, 43 i realne 46_2998) i te same
oczekiwania co `testy/regresja.py`. V2 wygrywa dopiero gdy >= V1
na kazdym sprawdzeniu, a pliki sa geometrycznie zgodne.

- sprawdzenia: V1 **42/42**, V2 **42/42**
- pliki DXF identyczne encja-po-encji (V1 vs V2): **36**
- pliki rozne: **0**, brakujace w V2: **0**
- werdykt: **V2 >= V1 (PASS)**

| rysunek | V1 | V2 | pliki |
|---|---|---|---|
| SL10478356 | 15/15 | 15/15 | 14 identycznych |
| SL10524825 | 4/4 | 4/4 | 4 identycznych |
| SL10582053 | 1/1 | 1/1 | 1 identycznych |
| SL40081914 | 5/5 | 5/5 | 3 identycznych |
| SL10578701 | 2/2 | 2/2 | 2 identycznych |
| SL10578699 | 3/3 | 3/3 | 2 identycznych |
| SL40052144 | 1/1 | 1/1 | 1 identycznych |
| SL40852311 | 1/1 | 1/1 | 1 identycznych |
| SL400521100 | 2/2 | 2/2 | 2 identycznych |
| SL40052423 | 1/1 | 1/1 | 1 identycznych |
| SL40071940 | 1/1 | 1/1 | 1 identycznych |
| SL10578806 | 3/3 | 3/3 | 1 identycznych |
| SL40885240 | 1/1 | 1/1 | 1 identycznych |
| SL10584235 | 1/1 | 1/1 | 1 identycznych |
| SL10584244 | 1/1 | 1/1 | 1 identycznych |

Uruchomienie: `python testy\benchmark_v2.py` (kod wyjscia 0 = PASS).
