# REGUŁA: Prawda o źródle z trybów CZYSTYCH (n_outer==1); „all" tylko diagnostyka

**Status:** wdrożona (etap 2 sweep; root-fix nakładki 2026-07-07).
**Klasa błędu, której zapobiega:** dwa przeciwstawne rodzaje szumu flagera:
(a) tryb po jednym kolorze (np. col7) NIE WIDZI cech na innym kolorze (SL40061302:
sloty na kolorze 2) → fałszywe „OK"; (b) tryb „all" łapie adnotacje/osie/wymiary
i sąsiadów w bbox → fałszywe flagi, które uczą ignorowania flag.

## Zasada (ogólna — mechanizm selekcji, nie numer rysunku)

Geometria pozycji bywa na RÓŻNYCH kolorach (2/4/7) albo na własnej warstwie
numerycznej (widok = warstwa 51/103/…) — nigdy nie zakładać koloru 7. Dlatego
region źródłowy liczy się we WSZYSTKICH trybach (per kolor, warstwa_geom, all),
a za PRAWDĘ uznaje tryb **CZYSTY**: taki, w którym region ma dokładnie
**jeden kontur zewnętrzny (n_outer==1)** — jedna część = jedna powłoka; wtedy
tryb nie miesza sąsiadów ani adnotacji. Przy kilku czystych trybach bierzemy
maksimum konturów wewnętrznych (rozbieżność czystych trybów = uwaga w raporcie).
Tryb „all" NIGDY nie jest źródłem prawdy — tylko diagnostyka.

## Bramka / skrypty, które to egzekwują

- `produkcja/kontrola/sweep.py` — `TRYBY_CZYSTE`, wybór `zrodlo_prawda` z trybów
  o `outer==1`; brak trybu czystego = głośna uwaga (nie ciche zero).
- `sprawdzanie/ai/nakladka.py` — `pick_region_czysty()` (root-fix szumu nakładki):
  region do nakładki z tego samego trybu czystego co sweep, zamiast całego bbox.
- Konsument: reguła [kompletnosc-konturow.md](kompletnosc-konturow.md) — dzięki
  czystemu trybowi próg flagi sweepa mógł zejść do delta≥1 (0 fałszywych na golden).

## Golden-testy (dowód)

- `testy/golden/SL40061302_sloty_odseparowane/` — geometria na kolorze 2, nie 7.
- `testy/golden/38_1847_gr4/` — 8×delta=0 (zero fałszywych flag) + 2 realne błędy.
- Testy: `testy/test_sweep.py`, `testy/test_sweep_54_4867.py`, `testy/test_gr4.py`,
  `testy/test_nakladka.py`.
