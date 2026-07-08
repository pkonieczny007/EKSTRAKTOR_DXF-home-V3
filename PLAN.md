# PLAN wdrożenia V3 — etapy i kryteria przejścia

> Zasady i architektura: `CLAUDE.md` (jedyne źródło zasad). Ten plik = kolejność prac.
> Każdy etap ma KRYTERIUM PRZEJŚCIA — bez jego spełnienia nie zaczynamy następnego.
> Po każdej zmianie w `produkcja/`: `python testy\regresja.py` + `python testy\testy_v2.py` PASS.

## Sesja 08.07 — hardening rankingu + gwint Hardox + deploy (CZYTAJ NA START)

**Zrobione i na `main` (każdy: golden→fix→regresja 43/43 + detektor 24/24 + benchmark_v3 0 regresji; wszystkie --szybko 28/28):**
- ✅ **R1** (silnik-w-a v1.1) — `partition()` krzyż osi kolor-6→axis (test geometryczny, nie długość; fable 84k encji). Golden `R1_kolor6_krzyz_osi_vs_giecie`, `test_r1`. Realnie SL40081914: 48 fałszywych krzyży z GIECIE, 0 zgubionej geometrii.
- ✅ **R3** (v1.2) — awaryjny wybór widoku = największy nie-izometryczny (`_pick_fallback_geo`); naprawia 47020 (40×16→62×53), 652 (22×22→281×44). `test_r3`.
- ✅ **R2** (v1.3) — adnotacja gięcia +2→najbliższy klaster (`_bend_annot_nearest`, detektor); izometryki nietknięte. `test_r2`.
- ✅ **GWINT REDESIGN** (gwint v1.2, raport v1.4, dxf-ekstrakcja v1.2 — **zastępuje** wcześniejszy auto-transform be604ba) — DOMYŚLNIE (każdy materiał) gwint **ZACHOWANY** + oznaczony na ŻÓŁTO (`oznacz_gwinty`, status 🟡, nota „gwint MX", jak fazowanie). Transformacja (łuk out, okrąg+CZERWONY) **TYLKO na żądanie** flagą `--transformuj-gwint`, średnica wg **klasy materiału** (`config/gwinty.yaml`: trudnościeralne M12→**10,6** / zwykłe M12→**10,2**, oba potwierdzone). Nieznana wartość→zostaje ŻÓŁTY. `test_gwint_hardox_transformacja` 27/27, `test_gwint` 28/28, `test_raport` 44/0, benchmark_v3 0 regresji.
- ✅ deploy 7 skilli V3 (14 celów, audyt 0 rozjazdów) · destylacja 185 etykiet (138 OK / 47 BŁĄD; #1=obca_geometria 31, w 90% W-D).
- ✅ audyt ryzyk R1–R4 (`zasady/propozycje/2026-07-08_ryzyka_rankingu_do_naprawy.md`) — R1/R2/R3 ZAMKNIĘTE.
  *(Deploy skilli po redesignie do wykonania: `python zarzadzanie\deploy_skilli.py --wykonaj`.)*
- ✅ **REALNE ZLECENIE e2e: 38_1847_ZUBEHOR** (94 rysunki / 165 pozycji, Hardox) przez cały tor V3, równolegle 6 workerów, **8,4 min**, core 94/94 OK. **Pierwszy punkt metryki zaufania:** 🟢100 / 🟡54 / 🔴11, **39,4% do przeglądu** (trend `metryka_zaufania.csv` → `38_1847_ZUBEHOR_CALE`). Gwint redesign **zwalidowany bojowo**: 23 gwinty/13 rys. zachowane+żółte. 11 czerwonych = poprawnie ODRZUCONE (6 otwarty kontur→człowiek, 5 dyskwalifikacja bramek — zasada 1). AI-oględziny 5 flag sweepa: **wszystkie fałszywe** (nakładka 100%/braki=0). Raport: `wyniki/38_1847_ZUBEHOR_V3/_ZBIORCZE/PODSUMOWANIE_ZLECENIA.md`; driver `scratchpad/run_zubehor.py`.
- 🔎 **Znalezisko → propozycja:** sweep `warstwa_geom` zawyża na rysunkach z wymiarami na warstwie geometrii (5/5 flag fałszywych) — `zasady/propozycje/2026-07-08_sweep_warstwa_geom_wymiary.md`.

**Decyzje:** W-D = **OPT-IN, nie inwestujemy** (UWAGA-pass już w W-C, V3 wygrywa 89%; słabość W-D=czyszczenie pitch-circli/gięć).

**BACKLOG (następna sesja, priorytet):**
0. ⭐ **APLIKACJA SPRAWDZANIA = STANDARD przy tworzeniu DXF** (user 08.07): każde zlecenie ma dostać apkę przeglądu jak `APP_do_porownywania-V2`. Instancja zbudowana i przetestowana: **`C:\Python_CLaude\EKSTRAKTOR_DXF\APP_do_sprawdzania-V3`** (Flask, port 5253) — wiersz=pozycja: **DXF gotowy** (render+otwórz w CAD) · **źródło-region** (conv.dxf przycięty do bboxu, do porównania obok) · **TIF/DWG** (oryginał warsztatowy, otwórz) · **nakładka** wynik-na-źródło · **info z wykazu** (materiał/wymiar wykaz vs DXF/skala/technologia/semafor) · **WERDYKT+UWAGI z autozapisem** do kopii wykazu (`SPRAWDZANIE_*.xlsx`) + backup `werdykty.json` + „Dograj do Excela". Zbudowane: `app.py`, `build_wykaz_sprawdzania.py`, README, start.bat.
   - **Wydajność (naprawione 08.07):** serwer `threaded=True` (otwieranie DXF nie blokuje renderów) + **`python app.py prerender`** (równoległy render WSZYSTKICH miniatur do cache PRZED przeglądem — inaczej trickle-in i zacinanie). start.bat robi prerender automatycznie.
   - **KIERUNEK NA JUTRO (user 08.07): dopracować „sposoby".** App ma **wskazywać FOLDER ZLECENIA**, a nie mieć ścieżki na sztywno w CONFIG → z folderu zlecenia wyprowadzać **stałe lokalne podścieżki** renderów (png gotowego, region, nakładka, tif/dwg) wg konwencji. Czyli: (a) ustalić stały layout folderów renderów per zlecenie, (b) pre-render generuje je tam PRZED przeglądem, (c) app dostaje tylko korzeń zlecenia i resztę składa z konwencji. To krok do uniwersalności + wpięcia jako standard pipeline (przebieg „g") / skill `/dxf-sprawdz`.
   - **DO FORMALIZACJI:** generowanie kopii-wykazu-do-sprawdzania + pre-render + apka jako krok pipeline, uniwersalne (wskaż folder zlecenia). Warunek: user potwierdzi że instancja ZUBEHOR działa dobrze (sprawdza jutro).
1. **Propozycja sweep `warstwa_geom`** (wyklucz wymiary / degraduj gdy nakładka 100%) — golden ZUBEHOR-fałszywa + strażnik 54_4867; awans przez testy.
2. Kalibracja typowania na `zasady/przyklady/<typ>/` (Etap 4.3).
3. Flager pitch-circle (okrąg podziałowy=obca geometria) jako propozycja QC — z lekcji W-D.
4. Infra z runu ZUBEHOR: (a) raport ładuje wykaz RAZ (nie 2× per rysunek); (b) sweep exit-1-na-flagi ≠ FAIL wykonania w `przebieg`; (c) rozważyć `przebieg_zlecenie.py` (parallel+consolidate) na stałe.
5. Deploy skilli po redesignie gwintu (`deploy_skilli.py --wykonaj`) · R4 (INFO) · pre-existing benchmark_v2 FAIL SL10578806_p4 (osobne).

**Zmiany w drzewie nie-nasze (user commit 8072026):** CLAUDE.md/MEMORY.md/archiwum/UWAGI/ — zacommitowane przez usera.

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
   - ⬜ (07.07.2026, OTWARTY) `testy/golden/SL40034116_p1_zgubione_otwory/` — REALNY defekt
     produkcyjny (38_1847 gr5): finalny DXF zgubił ~13 Langlochów przy zgodnym wymiarze
     i domkniętym konturze (żadna bramka nie krzyczała — klasyka 54_4867). Dowód dwustronny:
     fable interior 25 vs 38; Opus polygonize faces 26 vs 39 (delta 13), CIRCLE 7=7. Kandydat
     naprawy (W-C warstwa 51) czeka na POTWIERDZENIE CZŁOWIEKA (gruby s=12). Safety net do
     zrobienia: sweep-vs-źródło MUSI oflagować finalny plik. Przyczyna: stary tryb „bez warstw".

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
5. ✅ (06.07.2026) `produkcja/raport.py` (v1.0): scalenie raportów + oceny w
   `<zeinr>_podsumowanie.csv` + zapis statusów do KOPII wykazu (`--wykaz`). Merge
   ocena.csv (wielowariant) / raport.csv (parytet) + raport silnika + **realny pomiar
   wyjściowego DXF** (ezdxf.extents) vs Abmess (bramka 1, tol=max(1 mm,0.2%)) →
   `uwagi_wymiar`; `technologia` G/GS/S/brak z rysunku (Schweissgruppe + gięcie).
   **Writeback do KOPII `<wykaz>_WYNIKI.xlsx` — oryginał klienta NIETKNIĘTY** (pułapka
   formuł NAZWA/ZAKUPY: openpyxl.save kasuje cache; Excel przelicza kopię przy
   otwarciu, wymiary kontrolne z raportu). Status barwiony semaforem, obcy Zeinr
   pomijany. Test `test_raport.py` (44 sprawdzenia: tolerancja, technologia, merge,
   writeback+nietykalność oryginału).

**Kryterium: na golden zgodność ≥2 silników; każda rozbieżność widoczna w raporcie
z powodem; benchmark V3 ≥ V2.** ✅ — ETAP 3 DOMKNIĘTY (raport.py zamyka przepływ do wykazu).

## Etap 4 — sprawdzanie AI + człowiek, typowanie z bazy 🔨 (w toku)

1. ✅ (06.07.2026) Procedura flag AI — DRIVER: `sprawdzanie/ai/sprawdz_folder.py`
   (v1.0). Dla KAŻDEJ pozycji nakładka wynik-na-źródło → `pokrycie_zrodla` → flaga
   kompletności; 100% flag → PNG do oględzin (zasada 6). Reużywa `raport.scal`
   (semafor+plik) + `raport._index_raporty` (box+skala+lustro). **AUTO-OBNIŻA
   🟢→🟡** gdy `pokrycie_zrodla<97%` (zasada 5, tylko obniża); lustro → box
   bliźniaka (`--lustro`). Wyjście: `sprawdzanie_ai/PNG` + `<zeinr>_sprawdzanie_ai.csv`.
   Werdykty dopisuje człowiek/AI po oględzinach (`werdykty.py`) — driver NIE zgaduje
   (zasada 6). Test `test_sprawdz_folder.py` (25, stub nakładki: flaga/obniżenie/
   lustro/brak-pliku/werdykty-ai). Smoke realny SL10478356: 14 poz, 0 fałszywych flag.
   ✅ (06.07.2026) **Auto-werdykty AI**: `--werdykty-ai` dopisuje `WATPLIWOSC` (źródło=ai)
   dla flag do `nauka/etykiety/` — RECORD wątpliwości AI, NIE zamknięcie flagi (człowiek
   nadal ogląda, zasada 6). ✅ (06.07.2026) **Czerwone zakreślenia braków** (nakladka.py
   v1.1, rdzeń fable-advisor, zweryfikowany niezależnie): `_braki_skupiska` = dual
   `_coverage` (difference źródła z buforem wyniku → klastry niepokrytej geometrii, filtr
   szumu 3·tol) → jaskrawy czerwony okrąg na renderze + pole `braki_bboxy` (bbox+dł,
   malejąco — największe braki pierwsze, zasada 6). Zmierzone na golden: pełny wzorzec
   0 zakreśleń, bez 2 CIRCLE → 2 skupiska dokładnie w środkach źródłowych okręgów. Test
   `test_nakladka.py` (20). `sprawdz_folder` v1.2: skupisko braku flaguje TAKŻE przy
   pokryciu ≥97% (mała cecha zgubiona, czulsze niż sam próg %). **PUNKT 1 DOMKNIĘTY.**
   ✅ (07.07.2026) **ROOT-FIX szumu nakładki** (`nakladka.pick_region_czysty`, rdzeń
   fable-advisor, zweryfikowany niezależnie): na rysunkach typu SL40061302 WSZYSTKO leży
   na warstwie '1' (geometria=kolor 2, adnotacje=30/4/3) → fallback warstwowy wrzucał
   adnotacje do geom → bbox-fit anizotropowy (3.15%), auto-lustro się przełączało, diff
   tonął w FAŁSZYWEJ czerwieni (pokrycie_zrodla **34.2%** na POPRAWNYM wzorcu, 3 fałszywe
   skupiska — „fałszywe flagi uczą ignorowania flag", zasada 6). Fix bierze geometrię
   z trybu CZYSTEGO (per_tryb_detale ze sweepa: col7/col2/col4, n_ents>0, outer==1, 0 flag);
   brak czystego → BEZ ZMIAN (warstwa_geom, golden SL10596945 warstwa 53). Zmierzone:
   34.2%→**100.0%**, anizo 3.15%→**0.00%**, 3 fałszywe skupiska→**0**. Test `test_nakladka`
   (25, +blok SL40061302: tryb=col2/pokrycie≥99/0 skupisk). Regresja+testy_v2+sprawdz_folder+
   sweep 18/18 PASS.
2. ✅ (06.07.2026) Galeria + przegląd człowieka: `sprawdzanie/czlowiek/przeglad.py`
   (v1.0). Kafelki V3 wynik + źródło (zoom + ramka skąd-wycięto) + **nakładka**;
   semafor FINALNY = obniżenie AI ma pierwszeństwo (zasada 5); kolejność 🔴→🟡→🟢
   (najpierw decyzje); 🔴/🟡 obowiązkowo + 🟢 **PRÓBKA** co N-ty (reszta zliczona,
   nie renderowana — czas przeglądu). Worklist `<zeinr>_werdykty_do_wypelnienia.csv`
   → człowiek wpisuje OK/BŁĄD → `--werdykty` importuje do `nauka/etykiety/`
   (`werdykty.py`; każdy BŁĄD → przypomnienie golden PRZED naprawą, zasada 11).
   Reużywa `raport.scal` + `_index_raporty` + galeria V2 (render czarne tło) +
   `werdykty` — spina, nie dubluje. Test `test_przeglad.py` (26, stub render).
   Smoke realny SL10478356: 14🟢, próbka 5 → 3 do przeglądu (21% — metryka zaufania).
3. 🔨 Typowanie z profilem. **DECYZJA usera 06.07: typ DOSTRAJA PROGI + PODPOWIEDZI,
   NIE ogranicza silników** (zawsze W-A/W-B/W-C). ✅ (06.07.2026) `typowanie.profil_rysunku()`
   + `config/typy.yaml` pole `profil` (geom_kolory, giecie_kolor, spodziewane_lustra,
   cechy_odseparowane, prog_sweep_delta, uwaga) scalane z typów na `PROFIL_DOMYSLNY`;
   orkiestrator surface'uje profil informacyjnie (0 zmiany silników). Test
   `test_typowanie.py` (20). ⬜ ZOSTAJE: kalibracja detekcji na `zasady/przyklady/<typ>/`
   (przykłady referencyjne = kuratela człowieka) + konsumpcja progów w bramkach (benchmark).

**Kryterium: jedno zlecenie przechodzi pełny przepływ (pipeline → AI → człowiek →
etykiety) i raport zaufania pokazuje % pozycji wymagających przeglądu.** — infra
gotowa (pipeline→AI→galeria→etykiety→metryka); brakuje realnego zlecenia + typowania.

## Etap 5 — nauka + skille 🔨 (w toku)

1. ⬜ Destylacja po każdym zleceniu: korpus+etykiety → wnioski → (akceptacja człowieka)
   `kontekst/wiedza/` + golden + ewentualna propozycja reguły/typu (`zasady/propozycje/`).
   Skrypt `nauka/destylacja.py` GOTOWY; uruchomienie wymaga etykiet (Twój przegląd).
2. 🔨 Skille: **DECYZJA usera 06.07: `/wyciagnij-dxf` (V1/V2) NIE podmieniany — nowy
   skill V3 OBOK.** ✅ (06.07.2026) `skills/dxf-ekstrakcja/` = pełny tor V3 (recall →
   typowanie → orkiestrator → raport → sprawdź AI → galeria → metryka). ✅ (06.07.2026)
   źródła skilli pomocniczych: `/dxf-testy`, `/dxf-sprawdz`, `/dxf-przeglad`,
   `/dxf-zasada`, `/dxf-nauka`, `/dxf-audyt` — procedury na istniejących skryptach,
   wpisy w rejestrze (v1.0). ✅ `zarzadzanie/deploy_skilli.py` (dry-run, `--wykonaj`).
   ⬜ DEPLOY (operator, jedna komenda: `deploy_skilli.py --wykonaj`) = audyt zgłasza głośno.

**Kryterium: po 3 zleceniach — co najmniej 3 nowe reguły w wiedzy, każda z testem golden;
skille zainstalowane i w rejestrze (audyt PASS).**

## Etap 6 — zarządzanie i metryka zaufania 🔨 (w toku)

1. ✅ `/dxf-audyt` (źródło) + audyt w rytmie (każda sesja zaczyna od `python zarzadzanie\audyt.py`).
2. ✅ (06.07.2026) Metryka zaufania (`zarzadzanie/metryka.py` v1.0): % pozycji do przeglądu,
   rozkład semaforów FINALNYCH, flagi AI, werdykty człowieka; trend w
   `testy/raporty/metryka_zaufania.csv` (replace po data+zeinr, MA maleć). Test
   `test_metryka.py` (14). ⬜ czas sprawdzania/pozycję + błędy NA LASER (uciekłe) —
   wymagają instrumentacji przeglądu i feedbacku po wypaleniu (brak danych — uczciwie).
3. 🔨 Iteracje: kategorie 4–6 (adnotacje, korpus, człowiek) wg `config/kategorie.yaml`.
   ✅ (06.07.2026) **Kategoria 4 (adnotacje)** — `produkcja/silniki/v2/kategorie/adnotacje.py`:
   bąbelek numeru pozycji (`TEXT/MTEXT == nr` lub `Pos./Poz. N`) → najbliższy klaster →
   kandydat, ale TYLKO gdy wymiar pasuje do wykazu (`match_scale` = filtr przed złym
   bąbelkiem); hint `gespiegelt/mirrored` → kandydat NIEPEWNY. Priorytet 2/pewność 0.55.
   Test `test_adnotacje.py` (11). **`wlaczona:false` (opt-in)** — włączenie po benchmarku
   (zasada 10); `zaladuj_kategorie` pomija `false` przed importem → 0 ryzyka dla W-B
   (testy_v2 35/35, regresja 43/43 potwierdzone). Decyzja usera: typ dostraja PROGI, nie
   ogranicza silników.
   ✅ (06.07.2026) **Kategoria 5 (korpus)** — `kategorie/korpus.py`: dopasowanie do
   archiwum po SYGNATURZE (n_circ dedup + n_geom + ratio, lekka bez shapely); zgodna →
   pewność 0.7, rozjazd sygnatury (wymiar OK, inna liczba otworów) → NIEPEWNY 0.35; brak
   korpusu/wpisu → [] (nie zgaduje). `wlaczona:false` (opt-in — włączenie po zasileniu
   korpusu realnymi danymi + benchmark). Test `test_korpus.py` (11). ⬜ kategoria 6 (człowiek).

**Kryterium: metryka liczona automatycznie; 3 kolejne zlecenia bez błędu na laserze
i z malejącym odsetkiem przeglądu.**

---

## Zasady prowadzenia planu

- Odhaczamy ⬜→✅ z datą; nowe zadania dopisujemy do właściwego etapu (nie tworzymy etapu 2b).
- Trudny przypadek z produkcji NIE czeka na swój etap: od razu golden + wpis w
  `kontekst/wiedza/` (zasady żelazne 6, 11).
- Benchmark porównuje ZAWSZE: V3 vs V2 vs V1 (`testy/benchmark_v2.py` + docelowo `benchmark_v3.py`).
