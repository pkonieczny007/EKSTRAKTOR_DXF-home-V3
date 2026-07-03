# EKSTRAKTOR_DXF V2 — orkiestrator kategorii szukania + weryfikator

> Rysunek złożeniowy (DWG/DXF) + wykaz materiałowy (xlsx) → gotowe DXF 1:1
> pozycji blaszanych do Lantek Expert. V2 = przebudowa V1 na architekturę:
> orkiestrator → kategorie szukania (wtyczki) → wspólny weryfikator → galeria.

## Start pracy

**Nowa sesja zaczyna od `PROMPT_WDROZENIOWY.md`** — tam misja, kolejność
czytania kontekstu, architektura docelowa i etapy wdrożenia.
Cała wiedza projektowa: `kontekst/` (CLAUDE_v1.md = wiedza dziedzinowa,
kategorie_szukania.html = architektura, metody_sprawdzania.html = weryfikator).

## Stan wdrożenia (03.07.2026, kroki 0–5 DOMKNIĘTE + start samodoskonalenia)

Orkiestrator + kategorie 1–3 + weryfikator (8 bramek) + galeria DZIAŁAJĄ.
Benchmark: **V2 ≥ V1 na wszystkim** (42/42 sprawdzeń, 36/36 plików DXF
identycznych encja-po-encji).

**Pętla samodoskonalenia — krok 1/3 GOTOWY (03.07.2026):** logger zdarzeń
uczących `src/v2/decyzje.py` + flaga `--korpus` w orkiestratorze (domyślnie
WYŁĄCZONA) → `korpus/decyzje.csv`. Folder szkoleniowy `szkolenia/`
(MANUAL UPGRADER) na ręczne wnioski. Regresja/testy/benchmark dalej PASS
(logger jest dodatkowy, nie dotyka geometrii). Patrz sekcja „Samodoskonalenie".
Zostało: krok 2 = recall wiedzy w skillu `wyciagnij-dxf` (READ), krok 3 =
destylacja `decyzje.csv` → `wnioski.md` → `kontekst/wiedza/` (za potwierdzeniem
człowieka). Następne sesje: kategorie 4–6 (adnotacje, korpus, człowiek),
interfejs wyjątków (PLAN_v1 Etap 3–4).

## Szybki start

```bash
# regresja V1 — PUNKT WYJŚCIA I WARUNEK ODDANIA KAŻDEJ ZMIANY (PASS, 43 sprawdzenia)
python testy\regresja.py

# testy modułów V2 + benchmark V2 vs V1 — po każdej zmianie w src/v2/
python testy\testy_v2.py
python testy\benchmark_v2.py

# ZNANE BLEDY (XFAIL) — cele silnika ze zlecenia 54_4867 (wachlarz/tabelka, zgubione
# sloty, podwojne okregi). NIE psuje PASS; [XPASS] = naprawione -> awansuj do regresja.py
python testy\regresja_znane_bledy.py

# ekstrakcja V2 (orkiestrator kategorii; --galeria od razu buduje kafelki)
python src\v2\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow> [--galeria]

# ekstrakcja V2 z logowaniem nauki (produkcja): --korpus -> korpus\decyzje.csv,
# --korpus <plik> -> wlasna sciezka. BEZ flagi logowanie wylaczone (testy czyste)
python src\v2\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow> --korpus

# silnik V1 (działająca kopia — kategorie V2 go opakowują, importują, nie kopiują)
python src\extract_positions.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>

# galeria kafelków (wynik obok źródła z ramką „skąd wycięto", semafor)
python src\v2\galeria.py <folder_wynikow> [--rysunki <folder_rysunkow>]

# weryfikator post-hoc na gotowym DXF (8 bramek QC)
python src\v2\weryfikator.py <plik.dxf> <dim_max> <dim_min>

# render PNG — ZAWSZE przez ten skrypt (czarne tło; na białym jasne linie znikają)
python testy\pretesty\_render_png.py "<folder>/*.dxf"
```

## Zasady żelazne

1. Po każdej zmianie w `src/`: `python testy\regresja.py` → musi być PASS.
2. **V1 nietykalny**: do `c:\Python_CLaude\EKSTRAKTOR_DXF-home` nie piszemy NIC.
3. Nie zgadujemy geometrii — niepewne = `_DO_SPRAWDZENIA`, do człowieka.
4. Otwory święte, kontur zamknięty, wynik wyśrodkowany (0,0), skala 1:1.
5. Sprawdzanie < rysowanie od zera: człowiek porównuje obrazki, nie otwiera CAD-a;
   każdy żółty status ma jawny powód.
6. Orkiestrator nie zna środka kategorii; nowa kategoria = nowy plik
   w `src/v2/kategorie/` + wpis w `config/kategorie.yaml` — zero zmian w silniku.
7. Komentarze/dokumentacja po polsku (w .py bez ogonków), nazwy funkcji po angielsku.
8. Nowy trudny przypadek ⇒ sprawdzenie w `testy/regresja.py` + rysunek do `testy/rysunki/`.
9. `wyniki/` nie commitować.

## Wiedza dziedzinowa

NIE ucz się od nowa — wszystko w `kontekst/CLAUDE_v1.md` (konwencje klientów,
linie gięcia = kolor 6 magenta, lustra P/L, DWG w przebraniu, bloki INSERT,
zera wiodące, pułapki algorytmiczne 1–8) oraz `kontekst/wiedza/*.md`
(notatki z realnych zleceń).

## Samodoskonalenie (szkolenia + korpus) — jeden magazyn wiedzy, dwie strony

Cel: każde trudne zlecenie zostawia trwałą regułę, którą ekstraktor i następna
sesja będą znać. Magazyn wiedzy = `kontekst/wiedza/*.md` (zasila pułapki niżej,
kategorie, regresję). Dwie strony pętli:

- **READ („przechodzi przez szkolenia"):** przed ekstrakcją przypomnij notatki
  pasujące do klienta/prefiksu (SBM → `sbm-legenda-lustro`, magenta →
  `giecie-phantom-kolor6`) i STOSUJ reguły. *(Krok 2 — do wpięcia w skill
  `wyciagnij-dxf`.)*
- **WRITE („samodoskonalenie"):** `--korpus` → `src/v2/decyzje.py` dopisuje do
  `korpus/decyzje.csv` jeden wiersz na każde ZDARZENIE UCZĄCE (pozycja niepewna,
  bramka QC ZOLTY/CZERWONY, brak widoku, lustro do weryfikacji, brak w wykazie).
  Deterministycznie, zero LLM — to surowy ślad, nie reguła.

**Dwa wejścia dzielą magazyn:** produkcja (`wyciagnij-dxf` + `--korpus`) oraz
ręczne `szkolenia/` (MANUAL UPGRADER — wrzucasz zlecenie/wykaz z kolumnami
`SZKOLENIE`+`OPIS`, patrz `szkolenia/README.md`).

**Awans do reguły ZAWSZE za potwierdzeniem człowieka** (zasada: „uczenie =
jawne reguły, nie czarna skrzynka"). Destylacja: AI czyta `decyzje.csv` →
proponuje `wnioski.md` (format `szkolenia/_szablon/wnioski.md`) → człowiek
akceptuje → kopia do `kontekst/wiedza/<name>.md` + linia w `wiedza/MEMORY.md`
+ nowy trudny przypadek do `testy/regresja.py`. Bez auto-awansu surowego
zdarzenia. `korpus/*.csv` jest poza gitem; wersjonuje się destylat w `wiedza/`.

## Pułapki wykryte przy wdrożeniu V2 (okupione debuggingiem)

1. **Szybki bbox przeszacowuje SPLINE** (`bbox.extents(fast=True)` liczy po
   punktach kontrolnych): bbox klastra × skala ≠ realny wymiar wyniku
   (379.7 vs 374.68 mm na SL10524825 p2). Dlatego bramka wymiaru jest
   DWUSTOPNIOWA: zgrubna (błąd proporcji ≤3%) przed zapisem, ścisła
   (max(1 mm, 0.2%)) z realnych extents PO zapisie. Nieudana próba zapisu
   musi skasować plik (bez sufiksu poszedłby do nestingu!).
2. **Remis rankingu kandydatów**: przy identycznych metrykach V1 zostawia
   pierwszego (zbiór „all" iterowany przed per-kolor). Kandydat per-kolor
   wchłania tylko OKRĄGŁE otwory, więc przy remisie gubi kwadratowe wycięcia
   (sito SL40852311 = 680 różnic). Pole `tie` w `Kandydat` odwzorowuje
   kolejność V1; pilnuje tego benchmark (porównanie sygnatur plików).
3. **`testy/regresja.py` przy imporcie podmienia `sys.stdout`** na wrapper
   UTF-8 — skrypt, który go importuje (benchmark), nie może wrapować drugi
   raz (GC starego wrappera zamyka wspólny bufor → „I/O on closed file").
4. Po każdej zmianie w `src/v2/`: `testy_v2.py` + `benchmark_v2.py`
   (benchmark = regresja V2: statusy, wymiary, otwory ORAZ zgodność plików
   z V1 sygnaturą encja-po-encji).

### Pułapki ze zlecenia 54_4867 (SBM, 03.07.2026) — patrz `kontekst/wiedza/`

5. **Klaster po sąsiedztwie gubi CECHY ODSEPAROWANE** (fasola/slot, otwór-wyspa
   na środku blachy) — wypadają z wyniku, a wymiar zewnętrzny się zgadza (nie
   wykrywa!). Ten sam korzeń: silnik łapie TABELKĘ zamiast rozwinięcia, gdy ramka
   scala kartę w mega-klaster (SL10600635 = wachlarz 481×170 vs tabelka 480×170).
   ROOT-FIX = **ekstrakcja region+warstwa** (wszystkie encje warstwy geometrii w
   bbox widoku, transform jak kontur). QC kompletności: nakładka wynik-na-źródło,
   licznik okręgów, licznik konturów wewnętrznych (`_licznik_konturow.py` — flager,
   nie bramka; docelowo shapely.polygonize). → `cechy-odseparowane-region-warstwa`.
6. **Podwójne/zdublowane okręgi** — otwór jako Ø13+Ø14.7 (przelot+pogłębienie)
   albo ten sam okrąg 2× (SL10596945 p3/p4, SL10602681). Zostaw **najmniejszy** na
   środek, resztę skasuj. → `otwory-wspolsrodkowe-zdublowane`.
7. **Linie gięcia — kiedy nanosić**: TYLKO gdy P/L (`_p\d+[PL]`) albo gięcie pod
   skosem (>5° od osi). Nie-P/L z gięciem prostym — bez linii. Technologia i tak
   z obecności kolor6 w źródle. → `giecie-kiedy-nanosic-pl-skos`.
8. **Auto-technologia z DWG**: spaw = tekst "Schweissgruppe" w conv.dxf (nie
   boilerplate "Welding seams"!), gięcie = kolor6 → GS/G/S/brak. Obróbka i
   pojedyncze spawy symbolem = z TIF. → `technologia-schweissgruppe-auto`.
9. **Konwersja GstarCAD w batchu bywa przejściowa** (retry naprawia, nie „.bak
   lepszy"). **Odtworzenie z TIF** = ostateczność, kolor czerwony + czerwono w
   wykazie, do sprawdzenia. → `konwersja-gstarcad-retry-tif-czerwono`.

Zlecenia „RYSOWANIE" (wykaz z kolumną `nazwa_rysowanie`): wypełniamy status kolorem
(zielony/żółty/czerwony), uwagi, plik_dxf (tak/nie), technologia, wymiar_dxf_x/y,
skala, kontrola wymiarów (kolumny wg `tablica/pomysł/kontekst/3.2.2 - dxf_reader.py`:
`uwagi_wymiar=ok` gdy X i Y ±1 z Abmess). Szkolenie: `szkolenia/projekty/2026-07-03_54_4867_ekstrakcja_SBM/`.

## Środowisko

Windows 11, Python 3.13 (ezdxf, openpyxl, matplotlib — requirements.txt).
GstarCAD 2022 (`C:\Program Files\Gstarsoft\GstarCAD2022\`) tylko do konwersji
DWG; UNC nie działa — kopiować do %TEMP%. Dane produkcyjne: `\\QNAP-ENERGO\`.
