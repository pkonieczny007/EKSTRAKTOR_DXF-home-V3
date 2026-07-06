# REGUŁA: Środek CIRCLE/ARC/ELLIPSE czytać ZAWSZE OCS→WCS (lustro CAD)

**Status:** wdrożona (2026-07-05; W-C `region_warstwa.py` + bramka 5).
**Klasa błędu, której zapobiega:** źle pogrupowany dedup okręgów współśrodkowych
po lustrze CAD → zdublowany otwór na laserze (dwa przepalenia, zła średnica) albo
duble maskujące realny brak; zaniżony licznik konturów (owal liczony po złej stronie).

## Zasada (ogólna — mechanizm układu współrzędnych, nie numer rysunku)

`e.dxf.center` encji CIRCLE (i punkty ARC/ELLIPSE) są w układzie **OCS**. Encja
odbita lustrzanie w CAD dostaje `extrusion=(0,0,-1)` i surowy odczyt zwraca środek
po **złej stronie osi** (X odwrócony). Każdy odczyt środka do liczenia / dedupu /
transformacji = `e.ocs().to_wcs(e.dxf.center)`, nigdy surowe pole. Uwaga: ezdxf po
`transform()` ZACHOWUJE extrusion (0,0,-1) — problem nie znika po przeskalowaniu.

## Bramka / skrypt / pomiar

- `produkcja/silniki/region_warstwa.py` (W-C) — dedup współśrodkowych po środku WCS.
- `produkcja/kontrola/bilans_konturow.py` (bramka 5) — OCS→WCS od początku.
- Zmierzone: bez korekty owal SL10599245_p1 dawał 17 zamiast 21 twarzy; syntetyczny
  fertzing: raw=(-100,50) vs WCS=(100,50) → dedup-raw 2 grupy (dubel!), dedup-WCS
  1 grupa (zostaje najmniejszy r=5.5).

## Golden-test (dowód)

- `testy/golden/lustrzany_okrag_ocs/` + `testy/test_wc.py` (T5).
- Propozycja źródłowa (ZAAKCEPTOWANA): `zasady/propozycje/2026-07-05_ocs_center_okregow_lustro.md`.
- Wiedza: `kontekst/wiedza/otwory-wspolsrodkowe-zdublowane.md`.
