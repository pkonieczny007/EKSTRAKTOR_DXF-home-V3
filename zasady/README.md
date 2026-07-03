# SYSTEM TWORZENIA ZASAD (CLAUDE.md: "System tworzenia zasad")

- `reguly/` — AKTYWNE reguły per typ rysunku (`<typ>.md` / `.yaml`), czytelne dla
  człowieka (audyt bez czytania kodu). Wchodzą tu WYŁĄCZNIE przez testy (0 regresji)
  i za potwierdzeniem człowieka.
- `propozycje/` — nowe zasady/sposoby CZEKAJĄCE na testy — NIE działają w produkcji.
  Format: `_szablon_propozycji.md`.
- `przyklady/` — rysunki referencyjne definiujące typy (`<typ>/*.dxf` + notatka);
  kalibracja `produkcja/typowanie.py` = PLAN etap 4.

Ścieżka awansu: propozycja → golden set + regresja + benchmark → wynik lepszy/równy
i 0 nowych błędów → potwierdzenie człowieka → `reguly/` (+ wpis w `config/typy.yaml`,
gdy zasada definiuje typ).

Powiązany magazyn wiedzy dziedzinowej (notatki z realnych zleceń): `kontekst/wiedza/`.
Reguła ≠ notatka: notatka opisuje zjawisko, reguła mówi systemowi CO ROBIĆ.
