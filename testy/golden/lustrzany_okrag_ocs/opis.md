# Golden: lustrzany okrąg OCS (fertzing) — fix OCS→WCS w W-C

- **Skąd:** syntetyczny (2026-07-05), do propozycji `zasady/propozycje/2026-07-05_ocs_center_okregow_lustro.md` (ZAAKCEPTOWANA). Zasada 11: golden PRZED korzyścią z naprawy.
- **Co testuje:** okrąg współśrodkowy (fertzing = przelot Ø11 + pogłębienie Ø18.4)
  gdzie WIĘKSZY okrąg ma `extrusion=(0,0,-1)` (odbity lustrzanie w CAD).
- **Pułapka:** surowy `e.dxf.center` większego okręgu = **(-100, 50)** (zła strona, x
  odwrócony przez OCS), a `e.ocs().to_wcs()` = **(100, 50)** (poprawnie, współśrodkowy
  z mniejszym r=5.5).
- **Błąd który łapie:** dedup współśrodkowych po SUROWYM środku daje 2 grupy
  → fertzing zostaje ZDUBLOWANY (dwa przepalenia na laser, zła średnica). Dedup po
  OCS→WCS daje 1 grupę → zostaje najmniejszy (r=5.5). Patrz
  `kontekst/wiedza/otwory-wspolsrodkowe-zdublowane.md`.
- **Czego pilnuje:** W-C (`produkcja/silniki/region_warstwa.py`) czyta środki okręgów
  ZAWSZE przez OCS→WCS (dedup przed i po transformacji). Test: `testy/test_wc.py` (T5).
- **Zmierzone:** raw=(-100,50), OCS→WCS=(100,50), extrusion=(0,0,-1); dedup-WCS = 1 grupa,
  zostaje r=5.5. ezdxf po `transform(translate@scale)` ZACHOWUJE extrusion (0,0,-1).
