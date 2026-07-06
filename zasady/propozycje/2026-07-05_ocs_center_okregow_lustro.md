# Propozycja zasady: srodek CIRCLE czytac OCS->WCS (lustro CAD)

- **Data / autor:** 2026-07-05, AI (fable-advisor) — znalezione przy budowie bramki 5
- **Status:** **wdrozona (2026-07-05)** — ZAAKCEPTOWANA przez człowieka → poprawka w
  `produkcja/silniki/region_warstwa.py` (dedup po WCS), golden `testy/golden/lustrzany_okrag_ocs/`,
  test `testy/test_wc.py` (T5). Regula: `zasady/reguly/ocs-srodek-okregu.md`.

## Problem, ktory rozwiazuje
`e.dxf.center` encji CIRCLE jest w ukladzie **OCS** (Object Coordinate System).
Gdy okrag zostal w CAD odbity lustrzanie, encja dostaje `extrusion = (0,0,-1)` i
surowy odczyt `e.dxf.center` zwraca srodek po **ZLEJ stronie osi** (X odwrocony).

Skutki zmierzone (prototyp bramki 5, `licznik_shapely_proto.py`):
- W liczniku konturow bez korekty OCS owal spline SL10599245_p1 dawal **17 zamiast 21**
  twarzy — dopoki nie zamieniono na `e.ocs().to_wcs(e.dxf.center)`.
- Ta sama pulapka siedzi w [region_warstwa.py](../../produkcja/silniki/region_warstwa.py)
  ~linia 125: dedup okregow wspolsrodkowych grupuje po `ne.dxf.center` (surowy OCS).
  Na rysunku z lustrzanymi okregami od klienta dedup pogrupuje ZLE srodki → moze
  zostawic duble (maskuja braki) albo skasowac niewlasciwy okrag.

Bramka 5 (`bilans_konturow.py`) juz czyta poprawnie (OCS->WCS) — problem dotyczy
**silnika W-C**, ktory produkuje wynik, nie licznika, ktory go sprawdza.

## Tresc zasady (czytelna dla czlowieka)
Kiedy czytasz **srodek okregu** (CIRCLE) do liczenia / dedupu / transformacji →
ZAWSZE `e.ocs().to_wcs(e.dxf.center)`, nigdy surowy `e.dxf.center`. Dotyczy takze
ELLIPSE i ARC (punkty w OCS). Powod: extrusion (0,0,-1) po lustrze odwraca uklad.

## Przykladowe rysunki
- `testy/golden/SL10599245_owal_spline_odseparowany/wzorzec/SL10599245_p1.dxf` (owal, 21 wewn.).
- Potrzebny NOWY przypadek: rysunek zrodlowy z **lustrzanymi okregami** (extrusion -1)
  + wzorzec — do `testy/golden/` (obecne golden nie maja lustrzanych CIRCLE w W-C).

## Oczekiwany wynik
Po poprawce `region_warstwa.py`: dedup okregow grupuje po srodku WCS; na detalu z
lustrzanym okregiem liczba okregow po dedupie i ich pozycje = jak w rysunku zrodlowym
(brak dubli, brak przesunietych srodkow).

## Test
1. NAJPIERW golden: rysunek z lustrzanym okregiem → wzorzec (zasada 11).
2. Rozszerzyc `testy/test_bramka5.py` albo `regresja_znane_bledy.py` o pomiar dedupu
   na tym przypadku PRZED poprawka (XFAIL) i PO (XPASS → regresja).
3. `python testy\regresja.py` + `testy\testy_v2.py` PASS (0 regresji) — warunek merge.

## Decyzja czlowieka
- [x] ZAAKCEPTOWANA (2026-07-05) → poprawka `region_warstwa.py` (OCS->WCS w dedupie) + golden
- [ ] odrzucona, powod: <...>
