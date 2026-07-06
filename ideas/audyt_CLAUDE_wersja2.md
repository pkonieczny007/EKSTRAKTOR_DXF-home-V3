# AUDYT v2 — CLAUDE.md (EKSTRAKTOR_DXF-home-V3)

> Przegląd delta po zmianie stanu: FAZA PROJEKTOWA → **SZKIELET ZBUDOWANY + PARYTET Z V2**.
> Data audytu: 04.07.2026 · Audytowany stan dokumentu: 04.07.2026.
> Nawiązuje do: `AUDYT_CLAUDE_md.md` (v1, 04.07.2026). Sekcja 2 rozlicza tamte ustalenia.
> Charakter: przegląd dokumentu i deklarowanego stanu — NIE przegląd kodu (kodu nie widziałem;
> statusy typu „43/43 PASS" przyjmuję jako deklarację, nie zweryfikowałem uruchomieniem).

---

## 1. Ocena ogólna

Duży, dobry ruch. Powstał szkielet, PLAN.md z etapami 0–6, sekcja „Szybki start" z realnymi
komendami, `audyt.py` uruchamiany na starcie sesji, `.gitignore` na `wyniki/`. Widać, że
poprzednie uwagi zostały wzięte pod uwagę — zwłaszcza P1-01 (cienka pionowa ścieżka:
orkiestrator robi teraz tylko typowanie + delegację do W-B, reszta rozłożona na etapy).

Jedno zastrzeżenie do samego opisu stanu, ważne dla planowania (nie usterka, lecz kwestia
interpretacji) — rozwinięte w **N-01**: „PARYTET Z V2 ZWERYFIKOWANY" jest prawdą, ale przy
obecnej architekturze jest prawdą **prawie z definicji** i nie dotyka jeszcze trudnej części.
Trzeba to nazwać wprost, żeby nie powstało wrażenie, że walidacja V3 jest za nami.

Werdykt: dokument nadal solidny, stan realnie posunięty. Przed etapem 2–3 rekomendowane:
zbudować benchmark_v3 zanim cokolwiek zmieni wyjście (N-02), i domknąć trzy stare P1/P2,
które etapy 2–3 zaraz uczynią pilnymi (niezależność wariantów, profil wielotypowy, ścieżka TIF).

---

## 2. Status ustaleń z audytu v1

| Id | Ustalenie (skrót) | Status | Komentarz |
|---|---|---|---|
| P1-01 | Big-design vs cienka pionowa ścieżka | ✅ **zaadresowane** | Orkiestrator = typowanie + delegacja do W-B (parytet); W-C [etap 2], warianty [etap 3]. PLAN.md 0–6. Dokładnie ta ścieżka. |
| P1-02 | Niezależność wariantów założona, nie gwarantowana | 🟡 **otwarte / pilne** | `warianty.yaml` wspomina „progi zgodności", ale ślepej plamy W-A↔W-B nadal nie zaadresowano. Staje się PILNE w etapie 3 (patrz N-03). |
| P1-03 | Rysunek wielotypowy — brak reguły łączenia profili | 🟡 **otwarte** | `typowanie.py` „działa; kalibracja [etap 4]". Reguła rozstrzygania sprzecznych profili wciąż niezdefiniowana. |
| P2-01 | „0 regresji" ≠ „V3 ≥ V2" dopóki golden cienki | 🟡 **częściowo** | `golden/` istnieje z README, „zasila [etap 2]". Pokrycie nadal cienkie; dochodzi drift nazewnictwa (patrz N-04). |
| P2-02 | Koszt kontekstu / duplikacja wiedzy co sesję | 🔴 **otwarte (pogłębione)** | Dokument urósł (Szybki start). Studium 54_4867 + pigułka nadal w pliku ładowanym zawsze. |
| P2-03 | Próg próbkowania 🟢 niezdefiniowany | 🟡 **otwarte** | Nadal „np. co 10." bez tabeli progów. |
| P2-04 | Ścieżka TIF napina zasadę 1 | 🟡 **otwarte** | Nadal „odtworzenie z TIF (do sprawdzenia)"; brak twardej reguły „TIF nigdy nie 🟢 auto". |
| P3-01 | Numeracja bramek vs flager (nakładka) | 🟡 **otwarte** | Bez zmian. |
| P3-02 | Rozproszenie tej samej zasady | 🟡 **otwarte** | Bez zmian. |
| P3-03 | Kolizja slasha `/wyciagnij-dxf` V2↔V3 | 🟡 **otwarte** | Migracja [etap 5]; kolizja podczas równoległego istnienia wciąż nierozstrzygnięta. |
| P3-04 | Brak `.gitignore` na `wyniki/` | ✅ **zaadresowane** | „nie commitować, w .gitignore". |

Podsumowanie: 2 zamknięte (P1-01, P3-04), 1 pogłębione (P2-02), reszta otwarta. Trzy otwarte
(P1-02, P1-03, P2-04) awansują na pilne, bo etapy 2–3 zaraz ich dotkną.

---

## 3. Nowe ustalenia (stan: szkielet + parytet)

### P1 — adresować przed etapem 2/3

**N-01 · „Parytet z V2" jest tautologiczny przy obecnej architekturze — nazwać to wprost**
- *Obserwacja:* Orkiestrator V3 = typowanie + **delegacja do W-B**. Zdane testy (regresja 43/43,
  testy_v2 35/35, benchmark **V2≥V1**) to testy V2 uruchomione na przeniesionych kopiach silników.
- *Co to REALNIE dowodzi:* przeniesienie kodu do V3 jest czyste, zero regresji z samego przenosin,
  orkiestrator opakowuje W-B nie psując go. To jest wartościowy kamień milowy (czysty szkielet).
- *Czego NIE dowodzi:* że V3 daje lepszy/równy wynik niż V2 na realnym zleceniu — bo pod
  spodem V3 **jest** V2. Cała wartość dodana (W-C, sweep kompletności, wielowariantowość)
  jest dopiero przed Tobą, w etapach 2–3. Tam V3 albo pobije V2, albo nie.
- *Ryzyko:* Etykieta „PARYTET ZWERYFIKOWANY" może sugerować, że trudna walidacja jest za nami.
  Jest odwrotnie — dopiero się zaczyna.
- *Rekomendacja:* W nagłówku stanu dopisać jedno zdanie: *„parytet = wierność przeniesienia
  (V3 pod spodem = W-B); walidacja wartości dodanej V3 następuje w etapach 2–3 przez
  benchmark_v3"*. Konkretny dowód parytetu: uruchomić orkiestrator V3 na **54_4867** i
  zdiffować wyjście z V2 encja-po-encji (nie tylko smoke-test na syntetyku).

**N-02 · benchmark_v3 musi powstać ZANIM cokolwiek zmieni wyjście (sekwencja vs zasada 10/11)**
- *Obserwacja:* Istnieje `benchmark_v2.py` (V2≥V1). `benchmark_v3` jest `[etap 3]`. Zasada
  żelazna 10 wymaga „`testy/benchmark.py` (V3 ≥ V2)" jako warunku oddania KAŻDEJ zmiany
  w `produkcja/`.
- *Ryzyko:* W etapie 2 (W-C jako pełny silnik, sweep, shapely) i etapie 3 (warianty, ocena)
  zmienisz wyjście produkcji — a narzędzia, które miałoby to porównać z V2 (benchmark_v3),
  jeszcze nie ma. Wtedy zasada 10 jest niewykonalna w momencie, gdy jest najbardziej potrzebna.
- *Rekomendacja:* Zbudować **benchmark_v3 jako pierwszy krok etapu 2**, przed dotknięciem
  wyjścia. Musi umieć: wziąć historyczne zlecenie (54_4867), przepuścić przez V2 i V3,
  porównać statusy/wymiary/otwory/kontury encja-po-encji, i pokazać per-pozycja „lepiej/gorzej/
  bez zmian". To spina zasadę 10 (bramka benchmarku) z zasadą 11 (golden-first) w jedną
  operacyjną całość. Dopóki go nie ma — żadnej zmiany wyjścia w `produkcja/`.

### P2 — adresować w trakcie etapu 2/3

**N-03 · (eskalacja P1-02) Macierz korelacji metod potrzebna, zanim wielowariantowość ruszy**
- *Obserwacja:* Etap 3 uruchamia wielowariantowość i bramkę 10 (zgodność ≥2 metod = 🟢 możliwe).
  Twoje własne studium mówi: „klaster gubi cechy odseparowane **w każdym trybie**". W-A (klaster
  V1) i W-B (kategorie V2, też oparty o klaster) mogą dzielić tę ślepą plamę.
- *Ryzyko:* Zgoda W-A+W-B na brakującą cechę → bramka 10 daje FAŁSZYWE 🟢. To ta sama klasa
  błędu co 54_4867, tylko ubrana w „zgodność wariantów".
- *Rekomendacja:* W `warianty.yaml` zapisać, że (a) **W-C jest obowiązkowy** w każdym zestawie
  wariantów dla typów, gdzie cechy odseparowane są możliwe; (b) bramka 10 waży zgodność wg
  niezależności: zgoda W-A+W-B (pokrewne, wspólna ślepa plama) NIE wystarcza do 🟢 — potrzeba
  zgody z udziałem W-C. Zaprojektować to teraz, wdrożyć w etapie 3.

**N-04 · Drift nazewnictwa testów między „Szybki start"/strukturą a sekcją „System testowy"**
- *Obserwacja:* Konkret: `regresja.py`, `testy_v2.py`, `benchmark_v2.py`, `regresja_znane_bledy.py`.
  Sekcja prozą „System testowy" mówi jeszcze starym słownikiem: „`regresja.py` — pełny pipeline
  na **golden**", „`znane_bledy.py`", „`benchmark.py`". Dodatkowo `regresja.py` w strukturze to
  „43 sprawdzenia na **rysunkach testowych**", a `golden/` to osobny byt „zasila [etap 2]".
- *Ryzyko:* Sprzeczność „regresja na golden" vs „regresja na rysunkach testowych" myli następną
  sesję: nie wiadomo, co jest źródłem prawdy regresji dziś, a co dopiero powstanie.
- *Rekomendacja:* Ujednolicić sekcję „System testowy" z rzeczywistymi nazwami plików i rozdzielić
  wprost: **dziś** regresja biegnie na `rysunki/`+`wzorce/` (20 szt.); `golden/` (pary
  wejście→wzorzec) zasila regresję dopiero od etapu 2. Jedno zdanie o tej różnicy zamyka temat.

**N-05 · Status etapu 1 „✅/do obserwacji" bez kryterium zamknięcia**
- *Obserwacja:* „etap 1 ✅/do obserwacji". Nie wiadomo, co jest obserwowane ani co zamyka obserwację.
- *Rekomendacja:* Dopisać w PLAN.md jednolinijkowe kryterium wyjścia z obserwacji etapu 1
  (np. „N zleceń przez orkiestrator V3 bez rozjazdu z W-B" albo konkretny dowód z 54_4867 z N-01).

### P3 — dług / kosmetyka (bez zmian od v1, przypomnienie)

- **P2-02** wraca jako realny koszt: dokument rośnie, a jest ładowany co sesję. Przy najbliższej
  edycji rozważyć wydzielenie studium 54_4867 i pigułki do `kontekst/` z 3-zdaniowym skrótem tu.
- **P3-01/02/03** i **P2-03/2-04** — jak w audycie v1; żadne nie blokuje etapu 2, ale P2-04
  (twarda reguła „TIF nigdy nie 🟢") warto dodać przy okazji pisania bramek etapu 2.

---

## 4. Rekomendowana kolejność (spięta z PLAN.md)

1. **N-01** — dopisać jedno zdanie prostujące znaczenie „parytetu" + zrobić diff V3 vs V2 na 54_4867.
2. **N-02** — zbudować `benchmark_v3.py` jako PIERWSZY krok etapu 2 (przed zmianą wyjścia).
3. **N-03 / P1-02** — zaprojektować macierz niezależności wariantów w `warianty.yaml` (przed etapem 3).
4. **P1-03** — reguła profilu dla rysunku wielotypowego (potrzebna do kalibracji typowania, etap 4).
5. **P2-04** — twarda reguła „pozycja z TIF nigdy nie 🟢 auto" przy pisaniu bramek etapu 2.
6. **N-04 / N-05** — ujednolicić nazwy w „System testowy"; dopisać kryterium zamknięcia etapu 1.
7. **P2-02, P3-*** — spłata przy najbliższej większej edycji dokumentu.

---

## 5. Podsumowanie jednym zdaniem

Szkielet i „parytet" to czysty, realny kamień milowy — ale parytet jest dziś prawdziwy z
definicji (V3 pod spodem = W-B), więc cała walidacja wartości dodanej V3 jest wciąż przed Tobą;
warunkiem wejścia w nią jest benchmark_v3 zbudowany zanim jakakolwiek zmiana ruszy wyjście.
