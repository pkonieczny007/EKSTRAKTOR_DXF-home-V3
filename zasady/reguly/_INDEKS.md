# INDEKS REGUŁ — mapa: klasa błędu → co ją łapie (audyt bez czytania kodu)

Cel: w 30 sekund widać, KTÓRY mechanizm łapie KTÓRĄ klasę błędu, gdzie jest kod
i który golden to dowodzi. Reguła = MECHANIZM OGÓLNY (geometryczny); numerowany
golden to tylko TEST regresji, nigdy treść reguły — następny rysunek z tym samym
problemem ma inny numer.

## Zasada nadrzędna (reguła #1)

**Zgodny wymiar + domknięty kontur ≠ KOMPLETNOŚĆ.** Sam plik wyniku może być
wewnętrznie spójny i zielony, a mimo to zgubić cechy — ujawnia to DOPIERO
porównanie ze ŹRÓDŁEM (bilans konturów region vs wynik + nakładka), obowiązkowe
per pozycja. Szczegóły: [kompletnosc-konturow.md](kompletnosc-konturow.md).

## Mapa klas błędów

| Klasa błędu | Mechanizm wykrywający | Bramka / skrypt | Golden / test | Status |
|---|---|---|---|---|
| **Zgubione otwory/cechy wewn.** (fasole, sloty, perforacja, wyspy) przy dobrym wymiarze | bilans konturów wewn. REGION-ŹRÓDŁA vs WYNIK (polygonize) + nakładka wynik-na-źródle; delta≥1 / pokrycie_zrodla<97% = flaga → OCZY | bramka 5 `produkcja/kontrola/bilans_konturow.py`; `produkcja/kontrola/sweep.py`; `sprawdzanie/ai/nakladka.py` → reguła [kompletnosc-konturow.md](kompletnosc-konturow.md) | `SL40034116_p1_zgubione_otwory` (delta 13), `38_1847_gr4` SL40052110 (delta 8), `SL10596945`, `SL40061302`, `SL10582608`, `SL10599245`; `test_bramka5/test_sweep/test_nakladka/test_gr4` | wdrożona |
| **Fałszywe flagi / ślepota na kolor** (geometria na kol. 2/4, „all" zawyża) | prawda z trybu CZYSTEGO n_outer==1; „all" = tylko diagnostyka | `sweep.py` (TRYBY_CZYSTE), `nakladka.py` (pick_region_czysty) → reguła [region-tryb-czysty.md](region-tryb-czysty.md) | `SL40061302_sloty_odseparowane`, `38_1847_gr4` (0 fałszywych); `test_sweep`, `test_gr4` | wdrożona |
| **Otwarty kontur** (nie na laser, nawet gdy otwory OK) | 0 wierzchołków nieparzystego stopnia; polygonize: dangle/cut = NIEDOMKNIĘTE (twarda) | bramka 2 `silniki/v2/weryfikator.py` + flaga NIEDOMKNIETE w `bilans_konturow.py` | `38_1847_gr4` SL40852200 (🔴); `test_gr4`, `test_bramka5` | wdrożona (routing „droga blacha → DO_CZLOWIEKA" = propozycja `2026-07-07_otwarte_kontury...`) |
| **Brak linii gięcia w wyniku** (rozwinięcie bez GIECIE) | źródło ma kolor 6 w regionie → wynik musi mieć warstwę GIECIE | bramka 7 `silniki/v2/weryfikator.py` → reguła [giecie-warstwa-GIECIE.md](giecie-warstwa-GIECIE.md) | `SL40034116_p1_zgubione_otwory` (kandydat W-C 0/2 gięć) | częściowo: W-A/W-B tak; **W-C spłaszcza do warstwy 0 — pass gięcia NIEwdrożony (luka)** |
| **Zdublowany/przesunięty otwór po lustrze CAD** (extrusion 0,0,-1) | środek CIRCLE zawsze OCS→WCS przed dedupem/liczeniem | `silniki/region_warstwa.py`, `bilans_konturow.py` → reguła [ocs-srodek-okregu.md](ocs-srodek-okregu.md) | `lustrzany_okrag_ocs`; `test_wc.py` (T5) | wdrożona |
| **Duble maskujące braki** (okręgi współśrodkowe Ø13+Ø14.7) | dedup współśrodkowych PRZED liczeniem (zostaje najmniejszy) | `bilans_konturow.py`, `region_warstwa.py`; karta kontrolna (liczby PO dedupie) | `lustrzany_okrag_ocs`; wiedza `otwory-wspolsrodkowe-zdublowane.md` | wdrożona |
| **Fazowanie liczone jako otwarty kontur** (mylące „2 otwarte końce") | linia równoległa do krawędzi, końce NA obrysie, środek WEWNĄTRZ (T-złącza) → technologia=fazowanie | `produkcja/kontrola/fazowanie.py` → reguła [fazowanie-technologia.md](fazowanie-technologia.md) | `fazowanie_linia_przy_krawedzi`; `test_fazowanie.py` (0 fałszywych / 260 DXF) | wdrożona |
| **Zły wymiar / zła skala wyniku** | wymiar z wykazu = BAZA: zgrubna ≤3% przed zapisem + ścisła max(1 mm, 0.2%) po zapisie; kontrola operatora tol ±1, orientacja-agnostycznie | bramka 1 `silniki/v2/weryfikator.py`; `produkcja/kontrola/kontrola_wymiaru.py` | `regresja.py`, `test_kontrola_wymiaru.py` | wdrożona |
| — wyjątek: **części gięte** (wykaz nominalny, rozwinięcie inne) | additive: baza raportowana, rozjazd degraduje do 🟡 z powodem (nie 🔴) | propozycja `2026-07-07_bramka1_giete_wyjatek_additive.md` | SL10602713 (do golden) | propozycja |
| — **skala „nieładna"** (kandydat ratunkowy ze skalą 4.91) | kandydat ratunkowy tylko w NICE_SCALES | propozycja `2026-07-04_skala_ratunkowa_nice_scales.md` | `SL10599245_p6p7_skala_ratunkowa` | propozycja |
| **Złe lustro / widok ukradziony bliźniakowi** | rejestr widoków (żaden widok 2×); bliźniaki bywają ASYMETRYCZNE → weryfikacja ze źródłem, nie założenie symetrii | bramka 8 `silniki/v2/orkiestrator.py`; nakładka (auto-P/L: próba obu wariantów) | `test_wc.py`, `test_nakladka.py`; wiedza `sbm-legenda-lustro.md`, `lantek1nn-poz-parzysta-lustro` | wdrożona |
| **Złapany widok ZŁOŻENIOWY zamiast do palenia** (dospawienia kol. 6 w wyniku) | preferencja widoku czystego; magenta = nie ciąć (semantyka wg typu widoku) | propozycja `2026-07-07_widok_zlozeniowy_vs_do_palenia.md`; wiedza `magenta-kolor6-semantyka.md` | `SL10585238_p1_widok_zlozeniowy` | propozycja |
| **Śmieci o pasującym bbox / rzut 3D** | statystyka encji; rozkład długości linii (izometria) | bramki 3 i 6 `silniki/v2/weryfikator.py` | `regresja.py`, `testy_v2.py` | wdrożona |
| **Rozbieżność niezależnych silników** (cichy wybór złego wariantu) | sygnatury W-A/W-B/W-C zgodne/rozbieżne → eskalacja, nigdy cichy wybór | bramka 10 `produkcja/ocena.py` + `produkcja/warianty.py` | `test_warianty.py` | wdrożona |
| **Gwint flagowany jako otwarty kontur** (łuk ~270°) | okrąg + współśrodkowy łuk + DIMENSION „M nn" = gwint; zostawić OBA | wiedza `kontekst/wiedza/gwint-okrag-luk-dimension.md` (obsługa w przeglądzie) | — | wiedza (bez dedykowanego flagera) |

## Jak czytać statusy

- **wdrożona** — mechanizm działa w kodzie produkcyjnym, ma test; reguła = dokumentacja.
- **częściowo** — mechanizm działa w części ścieżek; luka opisana JAWNIE w regule.
- **propozycja** — spisane w `zasady/propozycje/`, NIE egzekwowane kodem; wchodzi
  wyłącznie ścieżką propozycja → golden → testy → potwierdzenie człowieka (README).

## Powiązane dokumenty

- CLAUDE.md: „KONTROLA DETALU GOTOWEGO" (trzy kontrole), „Bramki kontroli" (rejestr 1–10),
  zasady żelazne 2/6/7. Rejestr bramek w kodzie: `produkcja/kontrola/bramki.py --lista`.
- Notatki zjawisk (nie-reguły): `kontekst/wiedza/` + indeks `MEMORY.md`.
  Reguła ≠ notatka: notatka opisuje zjawisko, reguła mówi systemowi CO ROBIĆ i CO TO EGZEKWUJE.
