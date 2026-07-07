# Propozycja: Hardoxy (HB400/HB450, trudnoscieralne) - transformacja GWINTOW przy ekstrakcji

- **Data / autor:** 2026-07-08, operator (plan podany wprost) + AI (spisanie)
- **Status:** propozycja -> prototyp (fable) -> golden gwint_hb450 -> testy -> merge
  (produkcja/kontrola/gwint.py + tablica config/gwinty_hardox.yaml)
- **Doprecyzowuje:** [[otwarte-kontury-droga-blacha-do-czlowieka]] (wczesniejsza decyzja
  "otwarty kontur na Hardoxie -> czlowiek" zostaje TYLKO dla realnie otwartych obrysow;
  gwinty przestaja byc powodem czerwieni) oraz [[gwint-okrag-luk-dimension]].

## Plan operatora (verbatim)

> "Plan na Hardoxy, HB400, HB450 i inne trudno scieralne. **Wyciagaj jak normalne.**
> Tylko w miejscu gdzie gwint (czyli okrag i luk): **luk usuwamy, a okrag powiekszamy
> wg tablic i zaznaczamy na CZERWONO gdy zmienione. Jezeli nie znasz wartosci,
> zostawiasz luk i okrag** - wtedy ja wiem, ze musze poprawic okrag."

## Tresc zasady

1. **Rozpoznanie materialu:** gatunek trudnoscieralny z wykazu/Bezeichnung
   (regex `HB\s*4\d\d|HARDOX|XAR|RAEX` - zmierzone przez fable na 38_1847_ZUBEHOR:
   "HB 450" w Bezeichnung, 12 rysunkow).
2. **Ekstrakcja NORMALNA** - pelny pipeline, zadnego kierowania calosci do czlowieka.
3. **Detekcja gwintu:** sygnatura geometryczna (prototyp fable, 0 falszywych na 88
   plikach): ARC span 200-330 stopni wspolsrodkowy (<=0.3 mm) z CIRCLE o mniejszym R,
   ratio R_luk/R_okr w [1.08, 1.30]. Rozmiar gwintu M z NOMINALU luku (luk rysowany
   na srednicy nominalnej, np. luk o6 = M6); tekst DIMENSION "M.." u tego klienta
   NIE wystepuje (zmierzone 0/12) - geometria jest zrodlem prawdy.
4. **Transformacja (tylko material trudnoscieralny):**
   - luk gwintu USUN;
   - okrag POWIEKSZ wg tablicy `config/gwinty_hardox.yaml` (M -> srednica palenia);
   - zmieniony okrag na **CZERWONO (kolor 1)** - operator widzi zmiane;
   - wpis do raportu/wykazu: `gwint MX -> oY (zmieniony)`.
5. **Brak wartosci w tablicy (albo M nierozpoznane):** ZOSTAW luk + okrag bez zmian
   (kotwica bezpieczenstwa operatora: "wtedy ja wiem, ze musze poprawic okrag").
   Status pozycji minimum ZOLTY z powodem "gwint MX bez wartosci w tablicy".
6. **Material zwykly (nie-Hardox):** bez zmian - obowiazuje [[gwint-okrag-luk-dimension]]
   (zostaw OBA, opisz M w wykazie). Luk gwintu NIE liczy sie do otwartych koncow
   (bramka 2) na ZADNYM materiale - to zamyka ~62% falszywych czerwieni ZUBEHOR.

## Tablica srednic (config/gwinty_hardox.yaml)

Struktura: `M6: <mm>, M8: <mm>, ...` - **wartosci wpisuje OPERATOR** (zasada 1: nie
zgadujemy). Startowo tablica PUSTA => kazdy gwint "bez wartosci" => luk+okrag zostaja
(bezpieczny default). Po uzupelnieniu przez operatora transformacja dziala.

## Przyklady referencyjne (golden)

- `wyniki/38_1847_ZUBEHOR/_all/warianty/wB/SL10582645_p1.dxf` (fable #1: gwinty=4,
  otwarte_surowe=8, po wykluczeniu=0) + zrodla HB450: SL10582645, SL10584288,
  SL10585126 (179 gwintow!) i in.
- Test: detekcja gwintow, transformacja z tablica testowa, default bez tablicy,
  material zwykly nietkniety, bramka 2 bez falszywych flag.

## Kryterium awansu (zasada 8/10/11)

Prototyp -> golden gwint_hb450 -> test_gwint.py -> regresja+benchmark 0 regresji
(materialy zwykle NIETKNIETE, wyniki bez gwintow identyczne) -> potwierdzenie operatora
(w tym wartosci tablicy) -> merge.
