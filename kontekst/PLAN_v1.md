# PLAN: aplikacja samodoskonaląca się do ekstrakcji DXF

> Wizja: operator wrzuca folder zlecenia → aplikacja wycina pozycje, sama mierzy
> swoją skuteczność, a każdy wyjątek obsłużony ręcznie w interfejsie **uczy system**.
> Im dłużej działa, tym mniej pyta.

## Pętla samodoskonalenia (rdzeń koncepcji)

```
                 ┌──────────────────────────────────────────────┐
                 │                                              ▼
  rysunki ──► EKSTRAKTOR ──► pewne (OK) ───────────────► DXF do Lantka
  + wykaz        │ profile,                                    ▲
                 │ progi,     ──► niepewne ──► INTERFEJS ──────┘
                 │ reguły                      WYJĄTKÓW
                 ▲                             (człowiek klika)
                 │                                  │
                 │            decyzja = etykieta    │
                 └── TRENING ◄── KORPUS ◄───────────┘
                     (benchmark, auto-progi,        +
                      nowe reguły, profile)    stare zlecenia
                                               (gotowe DXF z Lantka
                                                = darmowe etykiety)
```

Dwa źródła nauki:
1. **Archiwum** — stare zlecenia mają już wycięte finalne DXF: parujemy
   (rysunek + wykaz + finalny DXF) i dostajemy tysiące testów za darmo.
2. **Bieżące wyjątki** — każda korekta w interfejsie (przesunięcie ramki, wybór
   innego widoku, odrzucenie) jest logowana jako przykład treningowy.

---

## Etap 0 — prototyp CLI ✅ ZROBIONE (11-12.06.2026)

- [x] `convert_dwg.py` — DWG→DXF przez GstarCAD wsadowo (wykrywanie po nagłówku)
- [x] `extract_positions.py` — tryb warstwowy (1NN), tryb bez warstw (gap 8→4→2),
      tryb per-kolor (rysunki 1-warstwowe), ranking po domkniętości konturu,
      wchłanianie otworów, linie gięcia → warstwa GIECIE, lustra, rejestr zajętych
      widoków, wyśrodkowanie wyniku, raport CSV
- [x] `testy/regresja.py` — 21 sprawdzeń na 3 rysunkach (3 różne konwencje)
- **Miara**: 19/20 pozycji automatycznie, p1 identyczna encja-po-encji z ręczną robotą

## Etap 1 — konsolidacja do aplikacji (1-2 dni)

Cel: jedno polecenie na całe zlecenie, konfiguracja poza kodem.

- [ ] `src/przetworz_zlecenie.py` — folder zlecenia → znajdź wykaz (najnowszy
      `*lista materiałowa*.xlsx`), wszystkie rysunki `{Zeinr}_{strona}.dxf`,
      konwersja + ekstrakcja wsadowo, scalony raport per zlecenie
- [ ] `config/profile.yaml` — progi (gapy, tolerancje, NICE_SCALES) + profile
      klientów (Lantek-warstwy / SBM-kolory / auto-detekcja) zamiast stałych w kodzie
- [ ] raport **HTML** z miniaturami PNG (wzór: status.html z DXF_cleaner):
      zielone = OK, żółte = LUSTRO/sprawdź, czerwone = do ręki; klik = otwórz DXF
- [ ] nazewnictwo wyjściowe wg wykazu (kolumna NAZWA/Bezeichnung — ustalić schemat)
- **Miara**: całe zlecenie jednym poleceniem, raport czytelny w przeglądarce

## Etap 2 — złoty korpus + benchmark (2-3 dni, fundament treningu)

Cel: system sam wie, jak dobry jest. Bez tego "uczenie" jest ślepe.

- [ ] `korpus/zbuduj_korpus.py` — skan starych zleceń: parowanie
      (rysunek źródłowy ↔ wykaz ↔ finalny DXF z Lantka) po Zeinr+pozycji i wymiarach
- [ ] `korpus/benchmark.py` — przepuść korpus przez ekstraktor, porównaj sygnaturą
      geometryczną (znormalizowane encje, odporne na przesunięcie/kolejność):
      % identycznych / % wymiar-OK / % zgubionych otworów / lista porażek
- [ ] porażki → automatycznie do `testy/przypadki/NNN/` (rysunek + oczekiwany DXF
      + metadane) — bank trudnych przypadków rośnie sam
- [ ] start: jedno stare zlecenie (~100-300 pozycji), potem rozszerzać
- **Miara**: liczba "% sukcesu na korpusie" w raporcie z każdego przebiegu

## Etap 3 — interfejs wyjątków (3-5 dni, web)

Cel: człowiek tylko ZATWIERDZA, nie szuka. Każdy klik = dane treningowe.

- [ ] prosty serwis web (Flask, jak inne narzędzia firmowe na 192.168.13.5):
      kolejka pozycji nie-OK z całego zlecenia
- [ ] widok pozycji: render kandydata + **ramki-kandydaci na podglądzie całego
      rysunku** (pomysł operatora: "zaznacz kwadraty → człowiek sprawdza → wytnij");
      operator: zatwierdź / wybierz inną ramkę / przesuń ramkę / odrzuć (powód)
- [ ] obok renderu **wycinek TIF** tego samego obszaru (TIF istnieje do każdego
      rysunku = "prawda wydrukowana", niezależna od warstw i kolorów)
- [ ] każda decyzja → `korpus/decyzje.csv` (rysunek, pozycja, kandydaci, wybór,
      powód, cechy klastrów) — to są etykiety do treningu
- [ ] zatwierdzone → normalny zapis DXF jak w automacie
- **Miara**: czas obsługi wyjątku < 30 s; zero wyjątków obsługiwanych w CAD

## Etap 4 — trening właściwy (ciągły, nocne przebiegi)

Cel: system z każdym zleceniem pyta rzadziej.

- [ ] **auto-strojenie progów**: grid search (gapy × tolerancje × skale) po korpusie,
      wybór konfiguracji maksymalizującej % sukcesu; zapis do `config/profile.yaml`
- [ ] **statystyka konwencji**: skan korpusu → tabela konwencji per klient/prefiks
      rysunku (warstwy? kolory? linetypes gięcia?) → automatyczne profile
- [ ] **analiza decyzji operatora** (jak `analyze_log.py` z DXF_cleaner): wzorce
      "w 95% przypadków typu X operator wybiera Y" → propozycja nowej reguły
      (człowiek zatwierdza regułę, nie każdy przypadek)
- [ ] opcjonalnie (gdy ręczny ranking zacznie przegrywać): drzewo decyzyjne sklearn
      na cechach klastrów (open_ends, n_encji, rel_err, % łuków, ładna skala...)
      z etykietami z korpusu — w pełni wyjaśnialne, przepisywalne na reguły
- [ ] po każdym treningu: `testy/regresja.py` + benchmark — nowa konfiguracja
      wchodzi TYLKO gdy nie psuje niczego starego
- **Miara**: malejący % wyjątków na zlecenie (wykres w czasie)

## Etap 5 — produkcja (po okrzepnięciu 1-4)

- [ ] watcher folderu zleceń albo przycisk w istniejącym flow technologów
- [ ] integracja z bazą elementów (elementy1.xlsx / LANTEK SQL — jak skill
      sprawdz-dxf-w-bazie): nie wycinaj tego, co już jest w bazie
- [ ] opcjonalnie wersja serwerowa (docker na Ubuntu — istnieje gotowy skill
      przenoszenia, GstarCAD zostaje na Windows jako mikro-usługa konwersji
      albo konwersja przez ODA File Converter w kontenerze)
- [ ] dashboard: % automatu per zlecenie, oszczędzony czas

---

## Wydajność (opcjonalne — wdrożyć GDY rysunki/zlecenia urosną)

> Na 3 rysunkach testowych nieodczuwalne. Koszt rośnie **kwadratowo** z liczbą encji
> i **liniowo** z liczbą pozycji, więc duże zlecenie (setki pozycji, gęsty rysunek)
> to odsłoni. Kolejność wg zysk/ryzyko. Każda zmiana: `testy/regresja.py` musi być PASS.

- [ ] **cache bbox per encja** (największy zysk, najmniejsze ryzyko): `ent_bbox`
      (`extract_positions.py:81`) liczy bbox tej samej encji wielokrotnie — w
      klastrowaniu, `interior_clusters`, `inside_bbox`, dla każdego progu osobno.
      Policzyć raz, trzymać w dict po `id(e)`.
- [ ] **bucket encji po warstwie raz na starcie**: `all_on_layer = [e for e in msp ...]`
      (`:334`) przebiega CAŁY modelspace raz na pozycję → O(pozycje × encje). Zbudować
      `dict{layer: [encje]}` jeden raz w `main()`. To samo `extract_fallback` robi
      `list(msp)` od nowa (`:388`).
- [ ] **klastrowanie O(n²) → sweep-line / grid**: podwójna pętla `for i… for j…`
      w `cluster_entities` (`:111`). W trybie bez warstw odpalana do **12× na pozycję**
      (4 zbiory kolorów × 3 progi gap, `:411`). Sortowanie bboxów po x + łączenie
      sąsiadów w oknie (albo siatka przestrzenna) schodzi do ~O(n log n).
- [ ] **batch konwersji DWG**: `convert_dwg.py` startuje osobny proces `gcad.exe`
      na każdy plik (~kilka s narzutu/plik). Jedna sesja GstarCAD z pętlą po plikach
      w jednym `.scr` tnie narzut przy wsadowym przetwarzaniu zlecenia (Etap 1).
- **Miara**: czas przetworzenia największego realnego zlecenia przed/po; regresja PASS.

---

## Zasady niezmienne (z doświadczeń)

1. **Regresja przed wszystkim** — żadna zmiana nie wchodzi bez PASS na starych przypadkach.
2. **Nie zgadujemy geometrii** — niepewne = do człowieka. Złom kosztuje więcej niż klik.
3. **Uczenie = reguły + progi + profile** (wyjaśnialne, debugowalne), nie czarna skrzynka.
4. **Każda ręczna decyzja musi zostawić ślad w korpusie** — inaczej uczenie nie ma paliwa.
5. Otwory są święte. Kontur musi być zamknięty. Wynik wyśrodkowany.

## Kolejny krok (proponowany)

Etap 1: `przetworz_zlecenie.py` + `config/profile.yaml` + raport HTML.
Równolegle wskazać jedno stare zlecenie z kompletem (rysunki + wykaz + finalne DXF)
pod budowę pierwszego korpusu (Etap 2).
