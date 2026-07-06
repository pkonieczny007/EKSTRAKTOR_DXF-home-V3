# PLAN wdrożenia V3 — etapy i kryteria przejścia

> Zasady i architektura: `CLAUDE.md` (jedyne źródło zasad). Ten plik = kolejność prac.
> Każdy etap ma KRYTERIUM PRZEJŚCIA — bez jego spełnienia nie zaczynamy następnego.
> Po każdej zmianie w `produkcja/`: `python testy\regresja.py` + `python testy\testy_v2.py` PASS.

## Etap 0 — szkielet projektu ✅ (04.07.2026)

Struktura katalogów wg CLAUDE.md; kopie silników z V2 (`produkcja/silniki/` = W-A + W-B,
`region_warstwa.py` = baza W-C); testy + rysunki + wzorce przeniesione; wiedza w `kontekst/`;
config (typy/kategorie/warianty); rejestr narzędzi + audyt; szkielety modułów V3.
**Kryterium: regresja 43/43, testy_v2 35/35, benchmark V2≥V1 PASS — w strukturze V3.** ✅

## Etap 1 — parytet produkcyjny ✅ (04.07.2026, do obserwacji)

`produkcja/orkiestrator.py` = typowanie (informacyjne) + delegacja 1:1 do W-B.
**Kryterium: wynik V3 == wynik V2 na rysunkach testowych (benchmark PASS) ✅ +
jedno realne zlecenie przepuszczone przez orkiestrator V3 bez różnic vs V2.** ⬜

## Etap 2 — kontrola kompletności (root-fix lekcji 54_4867) ⬜

1. ✅ (05.07.2026) **Bramka 5**: bilans konturów wewnętrznych przez `shapely.polygonize`
   — `produkcja/kontrola/bilans_konturow.py` (snap koncówek realną odległością zamiast
   `round` 0,1 → brak off-by-one na lustrach/jitterze; dedup okręgów OCS→WCS;
   flaga NIEDOMKNIETE = otwarty kontur). Test: `testy/test_bramka5.py` (32 sprawdzenia:
   7 wzorców golden + inwarianty lustro/jitter/dedup). `shapely` w `requirements.txt`.
   Zmierzone: cyklomatyka gubi kontur na jitterze (11≠12), shapely stabilny.
   Znaleziono przy okazji bug OCS w `region_warstwa.py` → `zasady/propozycje/2026-07-05_ocs_...md`.
2. ✅ (05.07.2026) **Nakładka wynik-na-źródło** (`sprawdzanie/ai/nakladka.py`) — wynik
   czerwony (alpha) na regionie źródła, czarne tło; alignment bbox-fit (s_fit=1/scale)
   + auto-lustro P/L (pokrycie obu wariantów); `pokrycie_zrodla<97%` = geometria źródła
   BEZ czerwieni = MOZLIWY BRAK CECHY (strategia #1, zwalidowane wizualnie: zgubiona
   fasola świeci na biało). FLAGER (decydują oczy). Test: `testy/test_nakladka.py`
   (13 sprawdzeń). Reużywa `sweep.kontury_regionu_zrodla` + bramkę 5.
3. ✅ (05.07.2026) **Sweep kompletności** (`produkcja/kontrola/sweep.py`) — wszystkie
   pozycje, wszystkie tryby (col7/col2/col4/all/warstwa-geometria); prawda z trybów
   CZYSTYCH (n_outer==1), 'all' tylko diagnostyka; delta≥1 = flaga (bramka 5 zbiła
   szum → 0 fałszywych na wzorcach; próg niższy niż CLAUDE.md delta≥2 — DO POTWIERDZENIA
   przez człowieka); braki źródła GŁOŚNO (zasada 15); raport do `testy/raporty/sweep_*.csv`.
   Test: `testy/test_sweep.py` (19 sprawdzeń). Zmierzone: SL40061302 sloty widzi tylko col2.
4. **Integracja W-C** — Stage 1 ✅ (05.07.2026): `region_warstwa.py` sportowany do V3 —
   martwy skrypt (import `_licznik_konturow` nie istniał, mkdir na module, ścieżka V2)
   → żywy importowalny silnik: `extract_region_warstwa(src_msp, box, scale, is_pl)`,
   licznik = bramka 5, **fix OCS→WCS** (fertzing lustrzany, propozycja zaakceptowana),
   wybór trybu geometrii bez zakładania koloru 7 (SL40061302=col2). Odtwarza kompletność
   wzorców (fasola 4, sloty 3, owal 12). Golden `lustrzany_okrag_ocs/`. Test `test_wc.py`
   (28 sprawdzeń). **Stage 2 ⬜: auto-fallback w orkiestratorze (gdy sweep/nakładka wykryją
   brak → W-C na tym widoku) + benchmark V3≥V2.**
5. ✅ (05.07.2026) Realne braki → `testy/golden/` jako testy sweepa/bramki 5:
   - `testy/test_sweep_54_4867.py` — silnik na źródłach 54_4867 (SL400521106 sloty 8→4,
     SL10596945 fasola 4→3), sweep MUSI oflagować (safety net, 7 sprawdzeń).
   - `testy/golden/38_1847_gr4/` + `testy/test_gr4.py` (człowiek, zasada 11) — 10 pozycji
     realnej partii: 8🟢 + 2 REALNE błędy. HEADLINE **SL40052110_p1 = ZWODNICZA ZIELEŃ**:
     wynik sam przechodzi bramkę 5 (interior=4, kontur domknięty, wymiar co do mm), a
     dopiero sweep-vs-źródło ujawnia stratę 8 cech (delta=8); stary licznik cyklomatyczny
     to przepuścił (źródło zaśmiecone 176 wymiarami) — **dowód, że sweep-vs-źródło jest
     OBOWIĄZKOWY**. SL40852200 = otwarty kontur → czerwony (bramka 2). 51 sprawdzeń, PASS.

**Kryterium: bramka 5 + sweep wykrywają braki z 54_4867/38_1847 (golden),
zero regresji.** ✅ — potwierdzone na REALNEJ partii produkcyjnej.

## Etap 3 — wielowariantowość + ocena (bramka 10) ✅ (06.07.2026; raport.py→etap 4)

1. ✅ `produkcja/warianty.py` generuje W-A/W-B/W-C per pozycja do `warianty/wA|wB|wC/`;
   `zrodlo_prawda` = sweep (trzecia niezależna miara). Opt-in: `orkiestrator --warianty`
   (default = parytet W-B do czasu benchmarku, zasada 10).
2. ✅ `produkcja/ocena.py::score_variants` wybiera zwycięzcę (bramki 1/2/5/10, R1-R5),
   `ocena.csv`; rozbieżność = eskalacja (nigdy cichy wybór); przegrane zostają w `warianty/`.
   Test `test_warianty.py` (17: 6 brzegów + W-C>W-A realny + is_pl). Smoke end-to-end na
   golden: p3 W-C wygrywa (kompletny), p4 lustro+skala ratunkowa → W-C dyskwalifikowany
   wymiarem (bezpiecznie) → W-B, flaga niekompletności. **Kluczowy pomiar: W-A przechodzi
   bramkę wymiaru CO DO SETNYCH identycznie z W-C (braki wewnętrzne) — rozjazd łapie tylko
   `interior` w sygnaturze bramki 10.**
3. ✅ (06.07.2026) `benchmark_v3.py` — V3 (warianty) vs V2 (W-B) na rysunkach regresji:
   42 pozycje, **0 regresji, V3 ≥ V2 PASS** (V3 nie gubi konturów, nie oddaje otwartego
   konturu, produkuje każdą pozycję). **Default orkiestratora sflipowany na
   wielowariantowość** (`--parytet` = opt-out). Zasada 10 spełniona.
4. ✅ (06.07.2026) Refinement lustra: pozycja `LUSTRO z poz. N` → zwycięzca = **odbicie
   zwycięzcy bliźniaka** (zachowuje kompletność twina; naprawił 2 regresje benchmarku +
   p4 golden z W-B/3 na LUSTRO/4). Bliźniaki asymetryczne → zawsze 🟡 do potwierdzenia.
5. ⬜ `produkcja/raport.py`: scalenie raportów + oceny; zapis statusów do wykazu (etap 3-4).

**Kryterium: na golden zgodność ≥2 silników; każda rozbieżność widoczna w raporcie
z powodem; benchmark V3 ≥ V2.** ✅ — spełnione (raport.py = domknięcie w etapie 4).

## Etap 4 — sprawdzanie AI + człowiek, typowanie z bazy ⬜

1. Procedura flag w praktyce: sprawdzanie AI (nakładki, zakreślenia na czerwono,
   werdykt z powodem) → `nauka/etykiety/` (źródło=ai).
2. Galeria + przegląd człowieka: werdykty (`sprawdzanie/czlowiek/werdykty.py`),
   próbkowanie zielonych, każdy BŁĄD → golden PRZED naprawą.
3. Kalibracja typowania na `zasady/przyklady/<typ>/` (rysunki referencyjne
   z realnych zleceń); typ wybiera silniki i progi (przestaje być informacyjny).

**Kryterium: jedno zlecenie przechodzi pełny przepływ (pipeline → AI → człowiek →
etykiety) i raport zaufania pokazuje % pozycji wymagających przeglądu.**

## Etap 5 — nauka + skille ⬜

1. Destylacja po każdym zleceniu: korpus+etykiety → wnioski → (akceptacja człowieka)
   `kontekst/wiedza/` + golden + ewentualna propozycja reguły/typu (`zasady/propozycje/`).
2. Skille: `/wyciagnij-dxf` podmieniony na orkiestrator V3 (recall wiedzy przed ekstrakcją);
   nowe: `/dxf-testy`, `/dxf-sprawdz`, `/dxf-przeglad`, `/dxf-zasada`, `/dxf-nauka`.
   Źródła w `skills/`, deploy do `~/.claude/skills` + SecondBrain, wpisy w rejestrze.

**Kryterium: po 3 zleceniach — co najmniej 3 nowe reguły w wiedzy, każda z testem golden;
skille zainstalowane i w rejestrze (audyt PASS).**

## Etap 6 — zarządzanie i metryka zaufania ⬜

1. `/dxf-audyt` + audyt w rytmie (każda sesja zaczyna od `python zarzadzanie\audyt.py`).
2. Metryka zaufania per zlecenie w `testy/raporty/`: % pozycji do przeglądu,
   czas sprawdzania/pozycję, błędy na laser (cel: 0). Trend musi SPADAĆ.
3. Iteracje: kategorie 4–6 (adnotacje, korpus, człowiek) wg `config/kategorie.yaml`.

**Kryterium: metryka liczona automatycznie; 3 kolejne zlecenia bez błędu na laserze
i z malejącym odsetkiem przeglądu.**

---

## Zasady prowadzenia planu

- Odhaczamy ⬜→✅ z datą; nowe zadania dopisujemy do właściwego etapu (nie tworzymy etapu 2b).
- Trudny przypadek z produkcji NIE czeka na swój etap: od razu golden + wpis w
  `kontekst/wiedza/` (zasady żelazne 6, 11).
- Benchmark porównuje ZAWSZE: V3 vs V2 vs V1 (`testy/benchmark_v2.py` + docelowo `benchmark_v3.py`).
