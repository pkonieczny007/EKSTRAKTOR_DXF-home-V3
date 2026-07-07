# Nowe przypadki z 41_2050: otwory INNEGO koloru / typ "daszek" / blindmutter

**Zrodlo:** operator, werdykty 41_2050 (2026-07-08).

## 1. Otwory INNEGO koloru niz kontur (SL40062903_p1) - ZGUBIONE OTWORY w V3+CODEX

Operator: "ZGUBIONE OTWORY! to ten wyjatek ze inny kolor otworow niz kontur. czasami
sie zdarzaja. porownanie z wartoscia ze skryptu i sprawdzenie jeszcze raz pod tym katem."
- V3 i CODEX zgubily otwory (2 vs 6 konturow w gotowym) - ekstrakcja po JEDNYM kolorze
  nie widzi otworow narysowanych innym kolorem.
- **W-D (metoda dwutorowa operatora) OTWORY MIAL** (8 vs 6; nadmiar = nieoczyszczone osie)
  - UWAGA-pass (zamkniete petle INNYCH kolorow wewnatrz obrysu -> dolacz+flaga)
  zadzialal dokladnie tak, jak zaprojektowano. DOWOD metody.
- Do zrobienia: cross-check liczby otworow ze skryptem (bramka 4/5 vs zrodlo-region)
  jako obowiazkowy sygnal "sprawdz jeszcze raz pod tym katem".
- Golden: `testy/golden/SL40062903_p1_otwory_inny_kolor/`.

## 2. Typ "daszek" (SL40051195, SL400521105)

Operator: "ten rysunek to tzw DASZEK. musimy odnajdowac takie daszki, oznaczac
i nakladac otwory w przyszlosci" - otwory pod NAKLADKI dorabiane pozniej recznie
([[gotowe-pozniejsze-modyfikacje-reczne]]); linia giecia skracana. Wykrycie daszka =
kandydat na typ rysunku (config/typy.yaml) + oznaczenie w raporcie (czlowiek wie,
ze otwory dojda).

## 3. Blindmutter (SL41051205_p1)

Pozycja z blindmutter (nakretka wtapiana/nitonakretka) = "do sprawdzenia" - operator
nie werdyktowal automatycznie. Flagowac obecnosc blindmutter (adnotacja/geometria)
jako 🟡 do potwierdzenia. Zebrac wiecej przykladow przed regula.

## 4. Izometryk - potwierdzenie sygnalu tekstowego (SL40091010, SL40047020)

Operator (2. raz, po ZUBEHOR): "patrzcie w takich przypadkach na OPIS LINII GIECIA -
jest w obrebie konturu" - adnotacja giecia WEWNATRZ konturu wskazuje wlasciwy widok
(rozwiniecie), izometryk jej nie ma. Odpowiedzi czlowieka (wlasciwy widok):
`testy/golden/SL40047020_p1_izometryk/czlowiek_odpowiedz/`.
