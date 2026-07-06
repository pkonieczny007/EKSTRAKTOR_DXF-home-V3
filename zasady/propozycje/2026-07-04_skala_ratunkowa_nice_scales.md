# Propozycja zasady: kandydat ratunkowy tylko w „ładnej" skali (NICE_SCALES)

- **Data / autor:** 2026-07-04, AI (sesja test2 — porównanie 4 modeli)
- **Status:** propozycja → (po testach i akceptacji) → reguła w `zasady/reguly/` + zmiana w `produkcja/silniki/v2/kategorie/geometria.py`

## Problem, który rozwiązuje

Zlecenie test2, SL10599245 p6/p7: ścieżka ścisła dopasowania odpadła o włos
(klaster skleił część 60.0×62.28 z ~2 mm osi → rozjazd skal x/y 3.28% > SCALE_TOL 3%),
więc wszedł kandydat ratunkowy z luźną tolerancją, który policzył skalę jako
średnią osi = **4.9109** — skalę rysunkowo NIEISTNIEJĄCĄ (rysunek jest podpisany
„M / S 1:5"). Wynik: 305.87×294.67 zamiast 300×311.4 — geometria zbliżona do
oryginału w złej skali, czyli najgroźniejszy typ błędu (trudny do wyłapania okiem).
Bramka 1 dała CZERWONY i `_DO_SPRAWDZENIA`, ale preferencja operatora jest jasna:
**lepiej nie narysować wcale, niż narysować prawie-dobrze w złej skali.**

Mechanizm w kodzie: `v1.match_scale` (ścieżka ścisła) MA przyciąganie do
`NICE_SCALES = [1, 2, 2.5, 4, 5, 8, 10, 20]` przy odchyłce < 2%, ale
`_match_luzny` w `geometria.py` tego przyciągania NIE MA — mimo że 4.9109
leży 1.8% od 5.0, czyli w zasięgu snapa.

## Treść zasady (czytelna dla człowieka)

Gdy kandydat pochodzi z kategorii ratunkowej (`geometria`, luźna tolerancja):

1. **Snap:** jeżeli policzona skala leży ≤ 2% od którejś z NICE_SCALES → użyj
   dokładnie tej ładnej skali (jak w ścieżce ścisłej) i PONOWNIE sprawdź wymiar
   bramką ścisłą max(1 mm, 0.2%). PASS → kandydat może zostać (nadal `niepewny`,
   priorytet 3). FAIL → punkt 2.
2. **Odrzucenie brzydkiej skali:** jeżeli skala po snapie nadal nie jest ładna
   (żadna NICE_SCALE w ≤ 2%) → kandydata ODRZUCIĆ (nie zapisywać DXF nawet jako
   `_DO_SPRAWDZENIA` z geometrią; pozycję raportować jako 🔴 BRAK DOPASOWANIA
   z powodem „skala ratunkowa X.XX poza NICE_SCALES"). Skale typu 4.91 nie
   istnieją na rysunkach technicznych — to zawsze artefakt złego bbox klastra.
3. **Podpowiedź z adnotacji (etap 6, kategoria 4):** tekst `M 1:N` / `S 1:N` /
   `(M / S 1:N)` w pobliżu widoku = twarda podpowiedź skali N; kandydat ratunkowy
   ze skalą sprzeczną z podpisem → odrzucić. (Ten przypadek jest gotowym
   przykładem referencyjnym: „(M / S 1:5)" nad widokiem p6/p7.)

Dotyczy wszystkich typów rysunków (kategoria ratunkowa jest wspólna).

## Przykładowe rysunki

- `testy/golden/SL10599245_p6p7_skala_ratunkowa/wejscie/SL10599245_1_conv.dxf`
  (poz. 6 i 7 wykazu `test2.xlsx`, wspólny widok, podpis „(M / S 1:5)").

## Oczekiwany wynik

- p6/p7: DXF w skali **5.0**, wymiar 300.01×311.42 (vs wykaz 311×300 po
  normalizacji osi — odchyłki 0.42/0.01 mm, bramka wymiaru PASS), 1 kontur
  wewnętrzny, 1 okrąg, wyśrodkowany; status najwyżej 🟡 (kandydat ratunkowy
  zawsze niepewny).
- ALBO (gdy snap się nie uda): brak pliku + 🔴 z jawnym powodem. NIGDY plik
  305.87×294.67 w skali 4.9109.

## Test

- `testy/golden/SL10599245_p6p7_skala_ratunkowa/` (wejście + wzorzec z naprawy
  FABLE ×5.0 — wzorzec do potwierdzenia przez człowieka).
- Po zmianie w silniku: `testy/regresja.py` 43/43 PASS + `testy/testy_v2.py`
  35/35 PASS + `testy/benchmark_v2.py` PASS (0 regresji) — warunek merge.

## Decyzja człowieka

- [ ] zaakceptowana → merge do reguł + golden + zmiana `geometria.py` (pkt 1–2); pkt 3 → backlog kategorii 4 (etap 6)
- [ ] odrzucona, powód: <...>
