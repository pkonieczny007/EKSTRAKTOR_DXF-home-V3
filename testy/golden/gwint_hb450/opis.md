# gwint_hb450 — golden: luk gwintu ~270 st to NIE otwarty kontur (bramka 2/5)

Para wejscie→wzorzec dowodzaca, ze **luk gwintu (~270 st, wspolsrodkowy z mniejszym
okregiem wiercenia) NIE moze byc liczony jako otwarty koniec** przez bramke 2 /
bilans_konturow (bramka 5) — na **kazdym materiale**. Zasada: `gwint-okrag-luk-dimension.md`.

- **Skad:** zlecenie `38_1847_ZUBEHOR`, pozycja SL10582645 poz. 5. Material **HB450**
  (trudnoscieralny — `Blech s=8 HB450`), 8 gwintow **M12**.
- **Uklad:**
  - `wejscie/SL10582645_1_conv.dxf` — rysunek zrodlowy (traceability; nie uzywany
    wprost w asercji — detekcja gwintu dziala na plikach 1:1, nie w skali zrodla).
  - `wzorzec/SL10582645_p5.dxf` — wynik 1:1 (8× gwint M12: okrag wiercenia +
    wspolsrodkowy luk ~270 st).

## Ground truth (zmierzone: gwint.thread_arcs + bilans_konturow po wpieciu gwintu)

| plik | gwinty | M | bramka2 surowo | bramka2 bez gwintow | bilans5 flags |
|---|---|---|---|---|---|
| wzorzec SL10582645_p5 | 8 | M12 (×8) | 16 | 0 | brak (interior=8, cuts 8→0) |

## Co lapie (rdzen tego golden)

1. **PRZED wpieciem gwintu do bramki 5:** kazdy z 8 lukow gwintu daje `cut` w
   polygonize → flaga **NIEDOMKNIETE** (cuts=8) → wynik NIEPEWNY, mimo ze part jest
   poprawny. Falszywa czerwien (falszywe flagi ucza ignorowania flag — 54_4867).
2. **PO wpieciu gwintu (bilans_konturow wyklucza thread_arcs PRZED polygonize):**
   `thread_skipped=8`, cuts 8→0, **flags puste**, interior=8 bez zmian. Luk gwintu
   przestaje generowac flage **u ZRODLA** (nie post-filtrem). Okregi wiercenia
   ZOSTAJA (nie sa wykluczane — otwory swiete).
3. **Straznik golden SL40852200_p1 (w `38_1847_gr4/`):** 1 gwint M10, bramka2 2→0 —
   ta sama falszywa czerwien znika. Materialy ZWYKLE bez gwintu (SL40061302,
   SL40034116) BEZ zmian (thread_skipped=0).

Uwaga: to golden dla **bramki 2/5 (kompletnosc/domkniecie)**, NIE dla transformacji
gwintu na trudnoscieralnych (ta jest opcjonalna, sterowana `config/gwinty_hardox.yaml`
i modulem `gwint.transformuj` — tu wzorzec zachowuje gwint jak jest: okrag+luk).
