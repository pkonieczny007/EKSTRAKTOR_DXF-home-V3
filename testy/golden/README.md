# GOLDEN SET — pary: wejście → zweryfikowany poprawny wynik

Każdy przypadek = podfolder:

```
testy/golden/<nazwa_przypadku>/
├── opis.md          # skąd (zlecenie/pozycja), co testuje, znany błąd który łapie
├── wejscie/         # rysunek *_conv.dxf (+ wykaz lub wycinek wykazu)
└── wzorzec/         # poprawny DXF zweryfikowany przez człowieka
```

Zasady (CLAUDE.md 11): każdy błąd znaleziony w produkcji/sprawdzaniu/przeglądzie
trafia tu NAJPIERW (przed naprawą). Porównanie GEOMETRYCZNE (kontury, otwory,
wymiary), nie wizualne.

Stan startowy: rolę golden pełnią `testy/rysunki/` + OCZEKIWANE w `testy/regresja.py`
(43 sprawdzenia) oraz `testy/wzorce/` (referencja operatora). Nowe przypadki — w tym
8 pozycji z brakami z 54_4867 (PLAN etap 2) — dodawać już w powyższym formacie.
