# Propozycja: sweep `warstwa_geom` zawyża na rysunkach z wymiarami na warstwie geometrii

- **Data / autor:** 2026-07-08, AI (odkryte na realnym zleceniu 38_1847_ZUBEHOR, 94 rysunki)
- **Status:** 🔴 PROPOZYCJA (nie w produkcji). Wymaga: golden + regresja + benchmark + potwierdzenie.
- **Powiązane:** [[strategia_kompletnosc_otworow]], nota CLAUDE.md „warstwa_geom zawyża na
  kołnierzu/gięciu i źródłach z wymiarami (138/446) — polygonize to naprawił".

## Problem (dowód z 38_1847_ZUBEHOR)

Sweep kompletności zgłosił 5 flag `delta≥1` (tryb `warstwa_geom`). **Wszystkie 5 = fałszywe**
— AI-oględziny nakładek: `pokrycie_zrodla=100%, braki=0` na każdej. delta bierze się stąd,
że tryb `warstwa_geom` liczy **linie wymiarowe (DIMENSION + linie pomocnicze) jako kontury
wewnętrzne**:

| pozycja | delta | warstwa_geom | col7 (realne otwory) | prawda |
|---|---|---|---|---|
| SL10583829_p1 | 12 | 16 | 4 | 4 otwory (komplet) |
| SL10585814_p1 | 9 | 12 | 3 | 3 otwory (komplet) |
| SL10582560_p1 | 6 | 8 | 2 | 2 otwory (komplet) |

Sweep flaguje „ROZBIEZNOSC trybow czystych: warstwa_geom=16 vs col7=4" — traktuje
`warstwa_geom` jako tryb CZYSTY, ale on nie jest czysty, gdy wymiary są na tej samej
warstwie co geometria (typowe u tego klienta / na tym zleceniu).

## Skutek

Fałszywe flagi kompletności uczą ignorowania flag (dokładnie ta pułapka z 54_4867).
Na 165 pozycjach: 5 flag, wszystkie fałszywe → 0% trafności flag sweepa na tym zleceniu.
Prawdziwych braków sweep tu nie miał (nakładka 100% na wszystkich) — ale szum psuje sygnał.

## Propozycja poprawki (do przetestowania, NIE wdrażać bez golden)

Opcja A (preferowana): w `sweep.py` tryb `warstwa_geom` **wyklucza encje wymiarowe**
z liczenia konturów — DIMENSION oraz LINE/segmenty należące do bloków wymiarowych
(albo krótkie linie z grotami/strzałkami). Tak jak bramka 2 wyklucza łuki gwintu.

Opcja B (tańsza, warstwa dodatkowa): gdy nakładka daje `pokrycie_zrodla≥99% i braki=0`,
**degraduj** flagę `warstwa_geom-vs-kolor` z „do oględzin" na „info" (nakładka = ground
truth, ~zero fałszywych — CLAUDE.md). Prawda z trybów kolorowych czystych (col2/4/7),
`warstwa_geom` tylko diagnostyka — analogicznie do „tryb 'all' tylko diagnostyka".

**Ryzyko:** nie osłabić sweepa tak, by przegapił realny brak (54_4867). Dlatego golden
MUSI zawierać: (a) te 3 fałszywe (ZUBEHOR, wymiary→0 flag po fixie) ORAZ (b) realny brak
z 54_4867 (nadal flagowany). 0 regresji na obu = warunek awansu.

## Golden do utworzenia
- `sweep_wymiary_falszywa_flaga/` — SL10583829_p1 (16 vs 4, komplet) → po fixie 0 flag.
- straznik: istniejący `test_sweep_54_4867` (realny brak) MUSI dalej łapać.
