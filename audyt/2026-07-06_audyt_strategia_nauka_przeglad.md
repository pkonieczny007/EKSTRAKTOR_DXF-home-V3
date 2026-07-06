# AUDYT EKSTRAKTOR_DXF V3 — skuteczność tworzenia DXF · nauka metod · przegląd człowieka

**Data:** 2026-07-06 · **Zleceniodawca:** operator (prompt w `audyt/prompt`)
**Zakres:** (A) strategia doskonalenia skuteczności tworzenia nowych DXF, (B) nauka nowych
metod i wyjątków, (C) sposoby sprawdzania DXF przez człowieka + **nowy sposób porównywania**
(inspiracja: `C:\Python_CLaude\EKSTRAKTOR_DXF\APP_do_sprawdzania` oraz
`\\QNAP-ENERGO\...\UPGRADE_SKANER_DXF` — tylko ulepszając, nie kopiując).
**Metoda:** przegląd kodu (sprawdzanie/, nauka/, zasady/, produkcja/, zarzadzanie/),
danych z 4 zleceń produkcyjnych (`wyniki/`), planu (`PLAN.md`), wiedzy (`kontekst/wiedza/`)
i obu aplikacji-inspiracji. Liczby podane niżej pochodzą z plików `ocena.csv`/`raport.csv`
i struktur na dysku — ścieżki przy każdym ustaleniu.

---

## 0. Streszczenie zarządcze

1. **Silnik ekstrakcji jest dobry i mierzalnie się poprawił** — 4 zlecenia (~228 pozycji
   rozstrzygniętych, ~1179 DXF-kandydatów), deklarowane „błędy na laser: 0". W-C (region+warstwa)
   wygrywa ~71% pozycji. Wielowariantowość + bramki działają.
2. **Cały aparat POMIARU istnieje w kodzie, ale nie w danych.** `metryka_zaufania.csv` nie
   istnieje, `nauka/etykiety/` puste (0 werdyktów), `*_sprawdzanie_ai.csv` nigdy nie powstał
   na produkcji, sweep nie odpalony na żadnym zleceniu. Wiemy „że działa" z ręcznej prozy
   (`ANALIZA_*.md`), nie z liczb.
3. **Pętla nauki domyka się wyłącznie ręcznym torem** (obserwacja → notatka wiedzy →
   propozycja → golden → kod; 3 pełne przejazdy: fasola/bramka 5, OCS, fazowanie).
   Zaprojektowany tor automatyczny (korpus → destylacja → reguły) nigdy nie zadziałał:
   korpus = 11 wierszy testowych, `zasady/reguly/` = 0 plików, `zasady/przyklady/` = 0.
4. **Główny ból — przegląd człowieka — ma jasno zlokalizowaną przyczynę:** galeria
   `przeglad.py` to statyczny HTML **bez ani jednej linii JavaScriptu**, 3 obrazki po
   165 px wysokości, werdykt = ręczna edycja osobnego CSV, łańcuch min. 3 komend
   odpalanych ręcznie. Wszystko, czego potrzebuje szybki przegląd (pokrycia, skupiska
   braków, semafory), system JUŻ liczy — ale nie podaje tego człowiekowi w użytecznej formie.
5. **Rozwiązanie nie wymaga nowej technologii** — `APP_do_sprawdzania` (Flask, interaktywna,
   z zapisem stanu) już istnieje i jest dobrą bazą; `UPGRADE_SKANER_DXF/IDEA_PRZYSPIESZENIE.md`
   zawiera sprawdzony wzorzec „trybu prowadzonego" (jedna pozycja na ekran, klawiatura,
   auto-advance). Projekt nowego sposobu porównywania — **„Tryb decyzji" z porównaniem
   trójtrybowym i kolejką braków** — w sekcji 4.3.
6. Wnioski i pomysły do poprawy — sekcja 6 (na końcu, zgodnie z zamówieniem).

---

## 1. Stan faktyczny w liczbach

### 1.1 Zlecenia produkcyjne i skuteczność silników

| Zlecenie | Pozycje | 🟢 | 🟡 | 🔴 | do przeglądu | przegląd człowieka |
|---|---|---|---|---|---|---|
| 24_0417 (pilotaż) | 14 (13 rozstrzygnięte, 1 nieznaleziona) | 7 | 3 | 3 | ~50% | TAK — proza `ANALIZA_24_0417.md` |
| 61_7227 | 42 | 28 | 8 | 6 | 33% | **NIE** — `_remark.log` pusty, brak MD |
| 38_1847 (gr1–5 stary tor) | 86 zrobione /136 | 48 | 32 | 29 | ~56% | TAK — proza `ANALIZA_CALOSCI.md` |
| 38_1847_ZUBEHOR | 165 | 103 | 28 | 34 | 38% | częściowy — `PODSUMOWANIE_ZUBEHOR.md` |

Zwycięstwa silników (z `*_ocena.csv`, 228 pozycji rozstrzygniętych wariantowo):

| Silnik | Zwycięstwa | Udział | Komentarz |
|---|---|---|---|
| **W-C** (region+warstwa) | 163 | ~71% | dominuje; przy remisie zapisywany jako zwycięzca |
| LUSTRO (odbicie bliźniaka) | 12 | ~5% | refinement z etapu 3 działa |
| **W-B** (kategorie+weryfikator) | 10 | ~4% | wchodzi, gdy W-C zdyskwalifikowany (brud/bramka 2) |
| **W-A** (klaster+ranking V1) | **0** | **0%** | nie wygrał ANI RAZU |
| „–" (wszystkie warianty 🔴) | 43 | ~19% | prawdziwa granica systemu — patrz 2.2 |

Czas maszyny: ~3 min na 5 rysunków (24_0417, `_run_all.log` 11:14:33–11:17:13).
Wygenerowane artefakty do obejrzenia: **~407 PNG** (zwycięzcy) na 4 zlecenia.

### 1.2 Pętla nauki — stan liczników

| Element pętli | Ścieżka | Stan |
|---|---|---|
| Notatki wiedzy | `kontekst/wiedza/` | **16 notatek** + MEMORY.md (żywe, rosną z każdym zleceniem) |
| Propozycje zasad | `zasady/propozycje/` | **5** (2 de facto wdrożone: OCS, fazowanie; 0 formalnie zamkniętych) |
| Golden | `testy/golden/` | **9 przypadków** |
| Reguły per typ | `zasady/reguly/` | **0 — puste** (meta pętli nigdy nie zasilona) |
| Przykłady referencyjne typów | `zasady/przyklady/` | **0 — puste** (typowanie bez kalibracji) |
| Etykiety (werdykty) | `nauka/etykiety/` | **0 wierszy** — `etykiety.csv` nigdy nie powstał |
| Korpus decyzji | `nauka/korpus/decyzje.csv` | 11 wierszy — wyłącznie fikstury testowe, 0 z produkcji |
| Destylacja | `nauka/destylacja.py` | działa, ale tylko drukuje na stdout; **żaden wynik nie zapisany** |
| Metryka zaufania | `testy/raporty/metryka_zaufania.csv` | **nie istnieje** — 0 punktów trendu |

### 1.3 Aparat pomiarowy: istnieje w kodzie, nie w danych

Na żadnym zleceniu produkcyjnym NIE powstały: `*_podsumowanie.csv` (raport.py),
`*_sprawdzanie_ai.csv` + nakładki (sprawdz_folder.py), `sweep_<zlecenie>.csv` (sweep.py),
`przeglad.html` + worklist werdyktów (przeglad.py), wpis metryki. Przyczyna: **orkiestrator
kończy pracę na wariantach+ocenie** (`produkcja/orkiestrator.py:54-66`), a dalsze kroki to
osobne komendy, których w praktyce nikt nie odpala. Skill `dxf-ekstrakcja` opisuje pełny
tor, ale każdy krok pozostaje ręczny.

### 1.4 Galeria/przegląd — stan techniczny (sedno skargi)

- `sprawdzanie/czlowiek/przeglad.py` generuje **statyczny HTML bez JS** (grep za
  `<script|onclick|keydown` w repo: 0 trafień). Kafelek = 3 obrazki `height:165px`
  (przeglad.py:227) — na ~180 px szerokości zgubiona fasola jest niewidoczna.
- Werdykt = ręczna edycja `<zeinr>_werdykty_do_wypelnienia.csv` w Excelu (parowanie
  wzrokiem `posn` między HTML a CSV) **albo** kopiowanie komendy CLI z kafelka; potem
  import (`--werdykty`). Min. **3 ręczne komendy + 1 ręczna edycja CSV** na sesję.
- Nakładka (najpewniejsza metoda, strategia #1 z `kontekst/strategia_kompletnosc_otworow.md`)
  pojawia się w galerii TYLKO gdy wcześniej ręcznie odpalono `sprawdz_folder.py` z podaniem
  źródła. Bez tego: „brak nakladki".
- Liczone-ale-niepokazywane: `pokrycie`/`pokrycie_zrodla` (tylko w CSV), współrzędne skupisk
  braków `braki_bboxy` (nakladka.py:112-149) **nie są zapisywane do CSV** — istnieją tylko
  jako narysowane okręgi na PNG; ostrzeżenia alignmentu tylko w nieczytelnym tytule PNG.
- Próbka zielonych: renderowany co N-ty, reszta **w ogóle nie renderowana** — bez ponownego
  przebiegu nie da się „dorenderować" kolejnej próbki.
- Rozjazdy dokumentacji: `sprawdzanie/README.md:14` kieruje do starej galerii V2;
  CLAUDE.md obiecuje „werdykt jednym kliknięciem" (nie istnieje); skille `/dxf-sprawdz`,
  `/dxf-przeglad` w tabeli CLAUDE.md mają status „plan", w rejestrze „działa".

---

## 2. Obszar A — skuteczność tworzenia nowych DXF

### 2.1 Co działa i czego nie ruszać

- **W-C region+warstwa** — root-fix z 54_4867 potwierdzony bojowo (71% zwycięstw; kompletność
  fasol/slotów/owali). **Bramka 5** (shapely.polygonize) zbiła szum liczników. **Sweep** +
  **nakładka** wykrywają to, czego bramki nie widzą (zwodnicza zieleń SL40052110 z 38_1847
  złapana dopiero sweep-vs-źródło).
- **Wielowariantowość z bramką 10**: rozbieżność wariantów poprawnie eskaluje (widok
  złożeniowy SL10585238 p1: interior 9 vs 9 vs 11 = sygnał złego widoku). Refinement LUSTRO
  naprawił realne regresje.
- **Pipeline przyjmuje `_conv.dxf` od operatora** (zasada 15) — podział pracy się sprawdza.

### 2.2 Główne źródła strat (gdzie uciekają pozycje)

Z 228 pozycji wariantowych **43 (~19%) kończą bez zwycięzcy** („–", wszystkie warianty 🔴).
Struktura przyczyn (z ocena.csv + prozy):

1. **Otwarte kontury na złożonych detalach z kołnierzem** — największy pojedynczy zbiornik
   strat: sam rysunek `SL40034116` dał 28×🔴 w 38_1847. W-C nie domyka kołnierzy.
2. **Części gięte: wymiar w wykazie bywa „do osi/promienia"** (SL10602713) — twarda
   dyskwalifikacja bramką 1, choć rozwinięcie na rysunku jest poprawne. Propozycja
   `2026-07-07_bramka1_giete_wyjatek_additive.md` czeka (wykaz = BAZA, wyjątek additive).
3. **Fałszywe 🔴 z linii gięcia pod skosem** — SL10217818: 1 otwarty koniec (linia gięcia)
   → twardy 🔴; operator obniżył do 🟡 i wydał. Analogiczny mechanizm jak fazowanie
   (już naprawione: `produkcja/kontrola/fazowanie.py` + wpięcie w raport.py).
4. **Widok złożeniowy vs do palenia** — pipeline może wziąć widok z dospawieniami; dziś
   ratuje eskalacja rozbieżności (🟡), preferencja czystszego widoku nie wdrożona
   (propozycja `2026-07-07_widok_zlozeniowy_vs_do_palenia.md`, golden OTWARTY).
5. **Pozycje „nieznajdowalne" automatem** (SL10602716 — pasek spawany do rury): słusznie
   do ręki; kategoria 6 (człowiek wskazuje ramkę) nie istnieje.

Dodatkowo dwie obserwacje o wariantach:
- **W-A = 0 zwycięstw / 228.** Nie kasować (zasada „3 sposoby"; głos zgodności w bramce 10
  ma wartość), ale dziś jego wkład jest **niewidoczny** — remis zapisywany jako W-C.
- **`warianty/wC/` w 24_0417 puste** przy 8 zwycięstwach W-C (raporty wariantów tylko
  wA/wB) — niespójność zapisu do wyjaśnienia (drobiazg, ale psuje audytowalność).

### 2.3 Strategia doskonalenia skuteczności

**Zasada nadrzędna (bez zmian):** baza deterministyczna + warstwy dodatkowe; wyjątki
obsługiwane ADDITIVE (nigdy zamiana bazy) — decyzja operatora z 07.07, spójna z zasadą 5.

1. **Domknąć 3 otwarte propozycje wyjątków** (gięte-additive, widok złożeniowy, otwarte
   kontury kołnierzy) torem: golden → test → kod → benchmark. To adresuje ~połowę strat „–".
   Dla kołnierzy (SL40034116) — zadanie dla fable-advisora (topologia domykania).
2. **Wpiąć warstwę kompletności w codzienny przebieg** (patrz P0 w sekcji 5): sweep +
   sprawdz_folder mają działać na KAŻDYM zleceniu automatycznie, nie „gdy ktoś pamięta".
   Bez tego zasada 7 („zlecenie domyka sweep") jest deklaracją.
3. **Ujawnić wkład zgodności wariantów**: w ocena.csv zapisywać `zgodnosc=3/3|2/3|1/3`
   zamiast tylko zwycięzcy. Pozycja 3/3 + sweep 0 + pokrycie ≥99% = kandydat na
   „🟢 bez oglądania" (dźwignia skrócenia przeglądu — sekcja 4).
4. **Kalibracja typowania na przykładach** (`zasady/przyklady/<typ>/` — dziś puste):
   typ dostraja progi (decyzja usera), więc każdy typ musi mieć 2–3 rysunki referencyjne.
   Nowa wiedza „geometria biała LUB żółta(2) = rozwinięcie" (24_0417) → do profilu typu.
5. **Zasilić kategorię 5 (korpus)** bazą `elementy1.xlsx` (już istnieje w firmie — używa jej
   skill /sprawdz-dxf-w-bazie); włączenie po benchmarku, zgodnie z opt-in.

---

## 3. Obszar B — nauka nowych metod i wyjątków

### 3.1 Pętla formalna vs rzeczywista

Zaprojektowano: `korpus → destylacja → wnioski → propozycja → golden+testy → reguły → produkcja`.
Rzeczywistość (3 udane przejazdy: bramka 5, OCS, fazowanie) idzie TOREM BOCZNYM:
`obserwacja operatora → notatka kontekst/wiedza/ → propozycja → golden → KOD wprost`.

- Tor boczny **działa i jest szybki** (fazowanie: obserwacja → działający kod w 1 dzień,
  z niezależną weryfikacją prototypu i 0 fałszywych trafień na 260 DXF).
- Tor formalny **nie ma paliwa**: bez werdyktów (etykiety=0) destylacja nie ma czego
  agregować; bez destylacji reguły nie powstają; `reguly/` puste = cel „audyt bez czytania
  kodu" niespełniony.

### 3.2 Wąskie gardła

1. **Etykiety = 0**, bo wpisywanie werdyktów jest za drogie (ręczna edycja CSV) — to TEN SAM
   problem co przegląd (sekcja 4). Naprawa przeglądu naprawia i naukę.
2. **Destylacja nie utrwala wyników** (tylko stdout) — nawet uruchomiona, nie zostawia śladu.
3. **Statusy propozycji nieaktualizowane** (fazowanie „propozycja" mimo wdrożenia; OCS
   zaakceptowany, ale wisi w propozycje/) — bałagan formalny podważa zaufanie do rejestru.
4. **Wiedza rośnie, ale nie konwertuje się na reguły maszynowe** — 16 notatek md czyta
   człowiek/AI przed zleceniem (recall), lecz progi/kolory/wyjątki z notatek nie trafiają
   do `config/typy.yaml` ani `zasady/reguly/`.

### 3.3 Strategia nauki

1. **Uznać tor boczny za OFICJALNY szybki tor** (obserwacja → wiedza → propozycja → golden
   → kod) i tylko go zdyscyplinować: każda propozycja w nagłówku ma pole
   `status: otwarta|zaakceptowana|wdrożona (data, commit)`; wdrożone przenosić do
   `zasady/reguly/<temat>.md` jako czytelną regułę (fazowanie i OCS od razu — 30 min pracy).
2. **Paliwo dla toru formalnego zbierać PRZY OKAZJI przeglądu** — werdykty z nowej
   przeglądarki (sekcja 4.3) spływają do `etykiety.csv` bez dodatkowej pracy operatora.
   Po 2–3 zleceniach destylacja będzie miała na czym pracować.
3. **destylacja.py: zapisywać szkic** do `nauka/szkolenia/analiza/<data>_szkic.md`
   (jedna zmiana), rytm: po każdym zleceniu, razem z metryką.
4. **Reguła = wiedza skompilowana**: przy każdym awansie notatki wiedzy do kodu dopisywać
   wpis do `zasady/reguly/` (co jest konturem/gięciem/fazowaniem dla danego typu, progi).
   Cel z kryterium etapu 5: „po 3 zleceniach ≥3 reguły z testem golden" — osiągalny od razu,
   bo 3 wdrożenia już SĄ (brakuje tylko plików reguł).

---

## 4. Obszar C — sprawdzanie przez człowieka (główny ból)

### 4.1 Dlaczego sprawdzanie bywa dłuższe niż narysowanie od nowa

Rozkład kosztu na dziś (na podstawie kodu przeglad.py + APP + prozy z 24_0417/38_1847):

| Krok | Koszt | Przyczyna |
|---|---|---|
| Odpalenie łańcucha (orkiestrator → raport → sprawdz_folder → przeglad) | wysoki, per zlecenie | 4 osobne komendy z argumentami; w praktyce pomijane → brak nakładek w galerii |
| Obejrzenie kafelka | wysoki, per pozycja | 3 obrazki × 165 px; każde powiększenie = nowa karta przeglądarki; brak zoom/pan |
| Znalezienie różnicy | **najwyższy** | człowiek skanuje CAŁY detal oczami, choć system ZNA skupiska braków (braki_bboxy) i ich nie podaje |
| Werdykt | wysoki | przełączenie HTML→Excel, odszukanie wiersza po posn, wpisanie OK/BLAD/kategorii |
| Import werdyktów + golden | średni | kolejna komenda + ręczne kroki |

Do tego 🔴 bez zwycięzcy **nie mają PNG** — człowiek i tak otwiera źródłowy rysunek w CAD.
Sumarycznie: pozycja flagowana kosztuje szacunkowo 60–120 s samego „obsłużenia", zanim
zacznie się właściwa ocena — a narysowanie prostej blachy w CAD to często 2–3 min.

### 4.2 Inspiracje — co brać, czego nie powtarzać

**`APP_do_sprawdzania`** (Flask :6070, już dopasowana do struktury wyników V3):
- BRAĆ: architektura (Flask + JSON API + inline HTML/JS, stan w `przeglad_stan.json`
  z zapisem atomowym), filtry (do sprawdzenia/kolory/problem/sprawdzone), checkboxy +
  notatka z zapisem natychmiastowym, lightbox, lazy-load, render na żywo z cache
  (thread-safe, mtime-aware), link do DXF.
- ULEPSZYĆ: brak panelu nakładki (2 obrazki zamiast 3), brak klawiatury, brak kolejki
  braków, semafor liczony ze STAREGO statusu (nie finalny post-AI), świadomie nie zapisuje
  do etykiet — przez co werdykty przepadają dla nauki.

**`UPGRADE_SKANER_DXF`** (Flask :6061, aktywnie używany — log z dziś):
- BRAĆ wzorce: **tryb prowadzony wiersz-po-wierszu** (IDEA_PRZYSPIESZENIE.md — jedna karta,
  duża, tylko bieżąca pozycja; skróty klawiszowe; auto-advance po sukcesie; szacowany zysk
  ~50 s/element), watchdog/odświeżanie na żywo, pomysł parowania P/L z ROADMAP,
  decyzje projektowe („plain JSON, nie SQLite; vanilla JS, nie framework; per-projekt
  deployment").
- NIE powtarzać: tabela z dziesiątkami kolumn i miniaturami 90×60 px (ROADMAP pkt 2 sam
  przyznaje, że UI nieczytelne); polling co 3 s tam, gdzie nic się nie zmienia.

### 4.3 NOWY SPOSÓB PORÓWNYWANIA — „Tryb decyzji” (projekt)

Rozbudowa `APP_do_sprawdzania` (nie nowa aplikacja): obok istniejącej planszy kafelków
drugi widok `/decyzja` — **pełnoekranowa kolejka decyzji**, wzorzec z IDEA_PRZYSPIESZENIE
przeniesiony z rysowania na sprawdzanie.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ SL10217547 · poz. 2   🟡 interior 4<16     [12/47]  ⏱ 0:41   sesja 18 min  │
│ powód: W-C zdyskwalifikowany (brud=16), zwycięzca W-B; sweep delta=2       │
│                                                                            │
│   ┌──────────────────────────────────────────────┐  brak 1/3: 14×30 (fasola)│
│   │                                              │  ↑↓ = następny brak     │
│   │        [ WIDOK GŁÓWNY — duży, ~80% ekranu ]  │                         │
│   │        tryb: NAKŁADKA · MIGANIE · OBOK       │  wymiar: 212×52 ✔ wykaz │
│   │        (Tab przełącza, scroll = zoom,        │  otwory: 4  gięcia: 2   │
│   │         auto-zoom na bieżący brak)           │  zgodność wariantów 2/3 │
│   └──────────────────────────────────────────────┘  pokrycie źródła 94.2%  │
│                                                                            │
│  [O] OK   [B] BŁĄD→kategoria 1-8   [K] KWADRAT=do ręki   [N] notatka       │
│  [L] werdykt też dla lustra p3     [←] cofnij   [Enter] następna pozycja   │
└────────────────────────────────────────────────────────────────────────────┘
```

**Trzy tryby porównania w jednym viewporcie (klawisz Tab):**

1. **NAKŁADKA KLASYFIKOWANA** — rozwinięcie dzisiejszej nakładki do diffu trójkolorowego:
   geometria wspólna = szara · **jest w źródle, brak w wyniku = CZERWONA** (zgubiona cecha)
   · **jest w wyniku, brak w źródle = NIEBIESKA** (obca geometria / dospawienie z widoku
   złożeniowego). Oba kierunki `_coverage` już są liczone w nakladka.py — brakuje tylko
   klasyfikowanego renderu. Czerwone okręgi skupisk braków zostają.
2. **MIGANIE (blink comparator)** — źródło-region i wynik renderowane w IDENTYCZNYM
   viewporcie (alignment bbox-fit + auto-lustro już jest w nakladka.py), przełączane
   w miejscu spacją albo automatycznie ~2 Hz. Różnice „skaczą” do oka — najszybsza znana
   metoda spot-the-difference (astronomia używa jej od stulecia). Zero nowej geometrii,
   tylko 2 PNG i toggle w JS.
3. **OBOK SIEBIE** — dzisiejszy układ wynik | źródło-zoom, ale z synchronicznym zoomem/pan.

**Kolejka braków (serce pomysłu):** `braki_bboxy` (liczone, sortowane malejąco — nakladka.py)
zapisywać do CSV/JSON i w UI **auto-zoomować na kolejne skupisko** (klawisze ↑↓). Człowiek
nie skanuje arkusza — patrzy tylko tam, gdzie system widzi różnicę, od największej
(żelazna zasada 6 zaimplementowana w UI, nie w procedurze do pamiętania).

**Werdykt jednym klawiszem, zapis podwójny:** natychmiast do `przeglad_stan.json` (jak dziś
w APP) **oraz** na koniec sesji eksport do `etykiety.csv` przez istniejące `werdykty.py`
(nie dublować logiki; kategorie błędów 1–8 z werdykty.py; werdykt `K` = konwencja operatora
KWADRAT „do ręki” z 24_0417, mapowany na kategorię `inne/do-reki`). To jednym ruchem domyka
pętlę nauki (dziś 0 etykiet) — bez ŻADNEJ dodatkowej pracy operatora.

**Pomiar czasu za darmo:** timestampy między werdyktami → `czas_na_pozycje` w metryce
(dziś pole zawsze puste — „brak instrumentacji”). Sesja przeglądu = automatyczny punkt
trendu w `metryka_zaufania.csv`.

**Kolejka pozycji:** 🔴 → 🟡 → próbka 🟢 (logika przeglad.py), w obrębie koloru sortowanie
po liczbie/wielkości braków malejąco. Bliźniak/lustro: po werdykcie pozycji bazowej
propozycja „ten sam werdykt dla p_N?” (1 klawisz) — ale NIGDY auto (bliźniaki bywają
asymetryczne — lekcja 54_4867).

**Czego ten projekt świadomie NIE robi:** nie zastępuje bramek skryptowych (zasada 4),
niczego nie podnosi (zasada 5 — UI może werdyktem tylko potwierdzić/obniżyć), nie dotyka
`produkcja/` (APP żyje obok; jedyne zmiany w repo V3: zapis braki_bboxy do CSV +
klasyfikowany render w nakladka.py — obie za testami test_nakladka/test_sprawdz_folder).

### 4.4 Porównywarka DXF↔DXF (drugi tor: wynik vs ręczny wzorzec)

Osobny, mniejszy przypadek użycia: porównanie DWÓCH plików DXF (wynik pipeline vs ręczny
DXF operatora / archiwalny z bazy). Dziś robione ad-hoc (`porownaj_golden.py` w
wyniki/24_0417 — 43 sprawdzenia). Awansować do stałego narzędzia
`testy/porownaj_dxf.py <A.dxf> <B.dxf>`:
- sygnatura bramki 10 (ocena.py — reuse) + wyrównanie i diff klasyfikowany (nakladka — reuse),
- werdykt liczbowy: `IDENTYCZNE / LUZ MONTAŻOWY (~2 mm, oba wymiary, cechy=) / ROZJAZD`,
  z wbudowaną wiedzą z `luz-montazowy-minus-2mm.md` (ignorowanie odpiętych encji —
  bbox największego klastra),
- zastosowania: walidacja golden po każdym zleceniu, nauka luzów/wyjątków z ręcznych
  wzorców, porównanie „nowa wersja silnika vs to, co poszło na laser” (wejście benchmarku).

### 4.5 Szacunek zysku czasowego

| Pozycja | Dziś | Po „Trybie decyzji” |
|---|---|---|
| 🟢 z próbki | ~30–60 s (otwieranie kart, brak pewności gdzie patrzeć) | ~5 s (miganie: brak ruchu = OK, Enter) |
| 🟡 flagowana | ~60–120 s + Excel | ~15–30 s (auto-zoom na braki, werdykt 1 klawisz) |
| 🔴 bez PNG | otwarcie CAD | bez zmian (to praca kreślarska, nie przeglądowa) |
| werdykty do nauki | nie powstają (0 etykiet) | powstają same |
| metryka czasu | brak | sama się liczy |

Dla zlecenia 61_7227 (42 poz.: 28🟢/8🟡/6🔴): dziś ~40–60 min → po zmianie **~10–15 min**,
z wpisami do etykiet i punktem metryki gratis. Przy rosnącym zaufaniu (metryka!) próbka
zielonych maleje — koszt przeglądu spada dalej.

---

## 5. Plan działań wg priorytetów

**P0 — domknięcie przepływu (warunek: zanim wejdzie następne zlecenie).** Nakład: ~1 dzień.
1. `produkcja/przebieg.py` (albo rozszerzenie orkiestratora): JEDNA komenda na zlecenie =
   orkiestrator → raport.py → sprawdz_folder.py → przeglad/APP → metryka.py. Pominięcia
   GŁOŚNO. Bez tego warstwy pomiarowe nadal będą omijane (dowód: 4 zlecenia bez śladu).
2. `sprawdz_folder.py`: zapisywać `braki_bboxy` do CSV (paliwo dla kolejki braków);
   testy test_sprawdz_folder/test_nakladka rozszerzyć.
3. Higiena statusów (30 min): propozycja fazowania → `wdrożona`; OCS → reguła + archiwum;
   `sprawdzanie/README.md` → przeglad.py; tabela skilli w CLAUDE.md; deploy skilli
   `--wykonaj` (operator).

**P1 — nowy przegląd (główna dźwignia czasu).** Nakład: 2–3 sesje, etapami jak
IDEA_PRZYSPIESZENIE (każdy etap niezależnie wartościowy):
4. APP v2 etap 1: widok `/decyzja` (kolejka, duży viewport, klawiatura O/B/K/N/Enter,
   semafor FINALNY z raport.scal zamiast starego statusu, zapis stanu jak dziś).
5. APP v2 etap 2: MIGANIE + nakładka klasyfikowana (render 2 klatek w jednym viewporcie;
   zmiana w nakladka.py za testami) + kolejka braków z auto-zoomem.
6. APP v2 etap 3: eksport werdyktów sesji → `werdykty.py`/etykiety.csv + timestampy →
   metryka (`czas_na_pozycje`). Od tej chwili pętla nauki dostaje paliwo z każdej sesji.
7. `testy/porownaj_dxf.py` (awans porownaj_golden) — porównywarka DXF↔DXF z werdyktem
   LUZ/ROZJAZD.

**P2 — skuteczność silników i nauka.** Nakład: rozłożony, każde za golden+benchmarkiem:
8. Propozycja gięte-additive (bramka 1 nie dyskwalifikuje twardo G/GS; degradacja do 🟡
   z powodem) — golden SL10602713.
9. Widok złożeniowy: preferencja czystszego widoku przy rozbieżności interior — golden
   SL10585238 (OTWARTY → domknąć).
10. Otwarte kontury kołnierzy (SL40034116, 28×🔴) — zadanie badawcze dla fable-advisora.
11. `ocena.csv`: kolumna `zgodnosc` (3/3, 2/3...) + status „🟢 pewny” (zgodność 3/3 + sweep 0
    + pokrycie ≥99%) → mniejsza próbka przeglądu (kalibrować metryką).
12. Reguły: przenieść 3 wdrożone wyjątki do `zasady/reguly/`; destylacja zapisuje szkice;
    po 24_0417+2 kolejnych zleceniach — pierwsza destylacja z realnych etykiet.
13. Feedback „po laserze”: jedno pole w wykazie wyników (`uciekło_na_laser: tak/nie/uwagi`)
    wypełniane przy odbiorze — jedyne brakujące ogniwo do prawdziwego „błędy na laser = 0”.

---

## 6. WNIOSKI I POMYSŁY — co możemy poprawić

### Wnioski (co audyt ustalił na twardo)

1. **Silnik jest lepszy niż jego obudowa.** Ekstrakcja (W-C + bramki + warianty) osiąga
   ~81% pozycji z wynikiem (🟢+🟡) i 0 znanych błędów na laserze — ale przegląd, nauka
   i metryka nie nadążają, więc zysk silnika zjada ręczna obsługa reszty procesu.
2. **Wszystko, czego potrzebuje szybki przegląd, system już liczy** (pokrycia, skupiska
   braków, powody, zgodność wariantów) — tylko nie pokazuje tego człowiekowi w formie,
   w której oko podejmuje decyzję w sekundy. To problem PREZENTACJI, nie geometrii.
3. **Pomiar nie istnieje w danych.** Bez metryki i etykiet nie da się dowieść, że
   „sprawdzamy coraz mniej i szybciej” — a to jest główna miara sukcesu projektu.
4. **Nauka działa, ale na piechotę** — 3 wyjątki przeszły od obserwacji do kodu w dni,
   co jest dobrym wynikiem; tor automatyczny stoi z braku paliwa (werdyktów), nie z braku
   kodu. Naprawa przeglądu naprawia jednocześnie naukę — to jedna inwestycja, dwa zwroty.
5. **W-A nigdy nie wygrywa, W-C dominuje** — wielowariantowość pełni dziś rolę
   „W-C + fallback W-B + sygnał rozbieżności”. To jest OK (koszt CPU tani), ale wkład
   zgodności powinien być jawny w danych, bo to on daje prawo do „🟢 bez oglądania”.
6. **Fałszywe twarde 🔴 mają wspólny wzorzec** (linia gięcia pod skosem, fazowanie,
   kołnierze): pojedyncza cecha rysunkowa interpretowana jako defekt konturu. Fazowanie
   już naprawione — pozostałe dwa idą tym samym, sprawdzonym torem additive.

### Pomysły (od najwyższego zwrotu)

1. **„Tryb decyzji” w APP_do_sprawdzania** (sekcja 4.3): pełny ekran, klawiatura,
   **porównanie trójtrybowe** (nakładka klasyfikowana / **MIGANIE** / obok siebie),
   **kolejka braków z auto-zoomem**, werdykt 1 klawiszem z eksportem do etykiet
   i pomiarem czasu. Szacunkowo 3–4× szybszy przegląd + paliwo dla nauki + metryka gratis.
2. **Jedna komenda na zlecenie** (`przebieg.py`): koniec z pomijaniem sweep/nakładek/metryki.
   Zasada 7 przestaje być deklaracją.
3. **Diff trójkolorowy** jako standard porównania wszędzie (galeria, porownaj_dxf, golden):
   szare=wspólne, czerwone=zgubione, niebieskie=obce. Jeden język wizualny w całym systemie.
4. **„🟢 pewny” = zgodność 3/3 + sweep 0 + pokrycie ≥99%** → na laser bez oglądania,
   próbka malejąca wraz z trendem metryki. To jest właściwa odpowiedź na „sprawdzanie
   trwa dłużej niż rysowanie”: nie oglądać szybciej, tylko **oglądać mniej — z dowodem**.
5. **Mapa cieplna zlecenia**: jeden ekran startowy sesji — wszystkie pozycje jako małe
   kafelki w kolorach semafora z licznikiem braków; klik = skok do pozycji w trybie
   decyzji. Ogląd całości w 5 sekund, zero scrollowania.
6. **Werdykt dziedziczony dla par P/L** (za potwierdzeniem 1 klawiszem, nigdy auto) +
   pomysł parowania z ROADMAP skanera (regex `_L/_P`) w porownaj_dxf.
7. **Feedback po wypaleniu** (1 pole): domyka pętlę jakości i czyni „0 błędów na laser”
   metryką, nie deklaracją.
8. **Dziennik zlecenia auto-generowany**: dzisiejsza ręczna proza `ANALIZA_*.md` powstaje
   w 80% z danych, które są w ocena.csv/metryce — szablonować (sekcja liczb auto,
   sekcja wniosków dla człowieka).
9. **Reguły jako artefakt wdrożenia**: „kod wpięty” ⇒ obowiązkowy plik w `zasady/reguly/`
   (checklist w propozycji). Audyt merytoryczny bez czytania Pythona — jak chciał projekt.
10. **Docelowo (po ustabilizowaniu przeglądu): tryb „sprawdzanie na żywo”** — watchdog na
    folderze wyników (wzorzec ze skanera): pozycja gotowa → od razu pojawia się w kolejce
    decyzji, operator sprawdza równolegle z pracą maszyny zamiast sesją na końcu.

**Kolejny krok (rekomendacja):** P0.1–P0.3 przed następnym zleceniem; następne zlecenie
przepuścić pełnym torem (z metryką i sesją w APP, nawet obecnym UI) — to da pierwszy punkt
trendu i baseline czasu, wobec którego zmierzymy „Tryb decyzji”.

---
*Źródła szczegółowe: kod `sprawdzanie/czlowiek/przeglad.py`, `sprawdzanie/ai/{sprawdz_folder,nakladka}.py`,
`produkcja/{orkiestrator,raport,ocena}.py`, `zarzadzanie/metryka.py`, `nauka/*`, `zasady/*`;
dane `wyniki/{24_0417,61_7227,38_1847,38_1847_ZUBEHOR}` (ocena.csv, ANALIZA/PODSUMOWANIE md, logi);
`PLAN.md`; `kontekst/wiedza/` (16 notatek); aplikacje: `APP_do_sprawdzania` (app.py, render.py,
zlecenia.py, stan.py, README), `UPGRADE_SKANER_DXF` (README, ROADMAP, IDEA_PRZYSPIESZENIE).*
