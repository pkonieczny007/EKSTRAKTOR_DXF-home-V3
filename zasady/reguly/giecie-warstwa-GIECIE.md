# REGUŁA: Źródło ma linie gięcia (kolor 6) → wynik MUSI mieć warstwę GIECIE

**Status:** częściowo wdrożona — bramka 7 działa dla W-A/W-B (weryfikator);
**ZNANA LUKA: silnik W-C spłaszcza wszystko do warstwy 0 i gubi gięcia** —
pass gięcia dla W-C = propozycja, jeszcze NIE egzekwowana kodem.
**Klasa błędu, której zapobiega:** rozwinięcie części giętej wysłane na laser bez
linii gięcia (operator krawędziarki nie wie, gdzie giąć) albo z linią gięcia
WCIĘTĄ w kontur cięcia (laser by ją przepalił).

## Zasada (ogólna, niezależna od numeru rysunku)

Linia gięcia = kolor 6 (magenta) na rozwinięciu, niezależnie od linetype
(DASHDOT/PHANTOM/MITTE). To **NIE kontur cięcia**:
1. przy LICZENIU konturów/kompletności — WYKLUCZAĆ (bramka 5 wyklucza kolor 6
   i warstwę GIECIE ze źródła i wyniku);
2. przy ZAPISIE wyniku — jeśli widok źródłowy ma linie gięcia, wynik musi je
   odwzorować na osobnej warstwie **GIECIE** (nanosić wg reguły P/L-lub-skos:
   pary lustrzane oraz gięcie pod skosem >5°; przy lustrze linie gięcia odbijane
   RAZEM z konturem).

UWAGA: kolor 6 ma więcej znaczeń (dospawywany element, geometria kontekstu na
widoku złożeniowym) — semantykę rozstrzyga typ widoku, nie sama encja:
`kontekst/wiedza/magenta-kolor6-semantyka.md`. Wspólny mianownik: **magenta nigdy
nie jest cięta**.

## Mechanizm wykrywania + egzekwowanie

- **Bramka 7 (gięcie):** źródło ma encje koloru 6 w regionie widoku → wynik musi
  mieć encje na warstwie GIECIE. Realizacja: `produkcja/silniki/v2/weryfikator.py`
  (rejestr: `produkcja/kontrola/bramki.py`). Próg: liczba gięć źródło vs wynik
  (brak odwzorowania = powód w `qc_powody`).
- **Wykluczenie z liczenia:** `produkcja/kontrola/bilans_konturow.py` (kolor 6 /
  warstwa GIECIE odfiltrowane przed polygonize) + `produkcja/kontrola/sweep.py`.

## Znane ograniczenie (zmierzone, uczciwie)

Silnik **W-C (region+warstwa)** spłaszcza wynik do warstwy 0 i NIE rozdziela
GIECIE. Pomiar (kandydat SL40034116_p1, 2026-07-07): wynik W-C = 0 encji koloru 6,
0 warstwy GIECIE — a źródło (warstwa 51) ma 2 linie gięcia kol. 6. To samo na
24_0417 (SL10217818: W-A/W-B rozdzielają 6 gięć poprawnie, W-C nie). Wniosek
operacyjny: **wynik W-C na części GIĘTEJ wymaga passa gięcia (+ lustra dla
bliźniaka P/L), zanim stanie się plikiem produkcyjnym**; do czasu wdrożenia passa
dla giętych preferować W-A/W-B, a wynik W-C bez GIECIE przy gięciu w źródle = 🟡
z jawnym powodem (bramka 7).

## Golden-testy (dowód)

- `testy/golden/SL40034116_p1_zgubione_otwory/` — kandydat W-C: kompletność OK
  (potwierdzona przez człowieka), ale 0/2 linii gięcia → NIE jest wzorcem
  produkcyjnym, dopóki nie przejdzie passa gięcia + lustra (opis.md, sekcja
  „Weryfikacja człowieka").
- Wiedza: `kontekst/wiedza/lekcje-24_0417-kolory-giete-przeglad.md`,
  `kontekst/wiedza/giecie-phantom-kolor6.md`,
  `kontekst/wiedza/giecie-kiedy-nanosic-pl-skos.md`.

## Powiązane

Bramka 1 dla giętych (wykaz to BAZA, rozjazd wymiaru łagodzony additive, nie
kasowany): propozycja `zasady/propozycje/2026-07-07_bramka1_giete_wyjatek_additive.md`.
