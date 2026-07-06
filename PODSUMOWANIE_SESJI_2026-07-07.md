# Podsumowanie sesji 2026-07-07 (kontynuacja jutro)

> Handoff: co zbudowane, jakie lekcje z przeglądu realnych detali, plan na jutro.
> Wszystko przez system testowy (zasada 8). Reguły OGÓLNE, goldeny tylko testują.

## Zbudowane i zielone (18/18 testów PASS, zero regresji)

1. **`testy/test_marker_wykazu.py`** (22 sprawdzenia) — luka zasady 8/11 zamknięta
   (`produkcja/kontrola/marker_wykazu.py` był w produkcji BEZ testu). Pokrywa: nietykalność
   oryginału wykazu, append kolumn za `max_column+1` (bug nachodzenia na formuły NAZWA),
   per-zeinr scoping, UWAGI ok/sprawdz, formuły jako tekst, barwienie.
2. **nakladka root-fix** `sprawdzanie/ai/nakladka.py::pick_region_czysty` — na rysunkach
   typu SL40061302 (wszystko na warstwie '1', geom=kolor 2) fallback warstwowy wrzucał
   adnotacje do geom → fałszywa czerwień (pokrycie_zrodla **34%** na POPRAWNYM wzorcu,
   3 fałszywe skupiska). Fix: geometria z trybu CZYSTEGO (per_tryb_detale). Zmierzone:
   34%→**100%**, anizo 3.15%→0.00%, 3→**0**. `test_nakladka` rozszerzony (+blok SL40061302).
3. **`zasady/reguly/` 0→6 plików** (było PUSTE — luka audytu): `_INDEKS.md` (mapa
   klasa-błędu→mechanizm→bramka→golden→status) + `kompletnosc-konturow` + `giecie-warstwa-GIECIE`
   + `fazowanie-technologia` + `ocs-srodek-okregu` + `region-tryb-czysty`. Statusy 2 propozycji
   (fazowanie, OCS) → "wdrożona". Etap 5 kryterium "≥3 reguły z golden" SPEŁNIONE.

## Nowe goldeny (zasada 11)

- **`SL40034116_p1_zgubione_otwory`** — REALNY defekt produkcyjny: finalny DXF zgubił ~13
  Langlochów przy zgodnym wymiarze i domkniętym konturze (26 vs 39 konturów; żadna bramka
  nie krzyczała — klasyka 54_4867). Człowiek POTWIERDZIŁ kompletność kandydata W-C
  (nałożenie warstwy 51). ZOSTAJE: pass gięcia (2 linie kol.6→GIECIE) + lustro p2 zanim
  kandydat→wzorzec; test safety-net sweep-vs-źródło.
- **`SL10582652_p1_widok_z_gieciem`** — wykaz-DŁUGOŚĆ BŁĘDNA (720 vs realne 560; żadna skala
  nie godzi 720 z klastrem) + zły widok (izometria). Wzorzec=detal człowieka 560×84.
- **`SL10582797_p1_rzut_boczny_zamiast_rozwiniecia`** — rzut zgiętej części zamiast
  rozwinięcia; wykaz OK (527×76); człowiek ZAZNACZYŁ widok na PNG (kategoria 6).
- **`WNIOSKI.md`** (fable) w folderze SL10582652 — 5 wniosków całej serii ZUBEHOR.

## Lekcje z przeglądu (części gięte, zlecenie 38_1847_ZUBEHOR)

**Wspólny rdzeń (zmierzony):** na rysunkach SBM **rozwinięcie do palenia leży na warstwie 5N;
warstwa pozycyjna 1NN ma widoki poglądowe/zgięte** → kategoria 1 (1NN) kieruje w zły widok.

**Sygnały wyboru widoku (koniunkcja, NIGDY pojedynczy):**
- Rozwinięcie = zamknięty kontur + otwory + linia gięcia (kol.6) wewnątrz + **skala STANDARDOWA**
  z tabelki godząca wykaz.
- Anty-sygnały złego widoku: **ELLIPSE>0** (najsilniejszy: 29/13 w izometrii vs 0 w rozwinięciu),
  otwarty kontur, kąty nie-ortho, **skala niestandardowa** (9.05/5.18 = naciąganie do złego wymiaru).
- **Sygnał tekstowy (kat.4):** adnotacja "alle Kantungen 90°/bend up/n.oben k." WEWNĄTRZ konturu
  = element gięty + ten klaster to rozwinięcie (bywa rozbita na linie — additive).

**Reguły statusu (POTWIERDZONE przez operatora — wiążące):**
- **Rozjazd wymiaru (niezgodność z bazą=wykazem) → 🔴 + sprawdzenie.** Człowiek przegląda
  WSZYSTKIE takie. NIE zmiękczać do 🟡. gięte-additive = tylko RAPORTUJ powód przy 🔴
  (część gięta, rozwinięcie≠nominał, np. SL40687710 1259.7 vs 1255). Status pozostaje 🔴.
- **Otwarty kontur z NACIĘĆ / kołnierzy** (geometria KOMPLETNA, cecha cięta/gięta, wymiar OK)
  → **🟡 minimum** (człowiek potwierdza), NIGDY 🟢 auto, NIE twardy 🔴. „Nacięcia wypalamy."
- **Realny brak fragmentu obrysu** (nie znika przy tolerancji) → 🔴.

**Klasy fałszywych 🔴 bramki 2** (kandydaci na flager jak fazowanie.py):
łuk gwintu ~270° (HB450), fazowanie, kołnierz „bend up", **nacięcia**.

## Projekty fable gotowe do budowy (przez testy)

- **`gwint.py` flager** (fable #1) — odblokowuje ~62% fałszywie czerwonych HB450 (0 FP na
  88 plikach). Marker gatunku HB400/HB450 w Bezeichnung. Prototyp: scratchpad `gwint_flager.py`.
- **Tryb decyzji** przeglądarka DXF (fable #2) — diff 3-kolor (szare/czerwone=brak/niebieskie=obce)
  + miganie (0 px rozjazdu) + kolejka braków z auto-zoomem, werdykt klawiszem→etykiety+metryka.
  Rozbudowa `APP_do_sprawdzania` na wzór QNAP `//QNAP-ENERGO/Technologia/Python/SKANER_DXF/`.
  Prototyp: scratchpad `przeglad_diff_prototyp.py` + demo/. **Root-fix nakladki (pkt 2 wyżej)
  był prerekwizytem — ZROBIONY.**
- **Detektor rozwinięcia + kategoria 6** (fable #3, WNIOSKI.md) — 5 wniosków ogólnych.

## Plan na jutro (priorytety)

- **P0:** `produkcja/przebieg.py` — jedna komenda/zlecenie (orkiestrator→raport→sprawdz_folder→
  sweep→metryka), pominięcia GŁOŚNO. To przyczyna ucieczki SL40034116_p1 (sweep nigdy nie
  odpalony na realnym zleceniu). + deploy skilli (`deploy_skilli.py --wykonaj`).
- **P1:** Tryb decyzji (przegląd — główna dźwignia czasu, projekt+prototyp gotowe).
- **P2 (każde przez golden+benchmark):** flager fałszywych 🔴 bramki 2 (nacięcia/kołnierze/gwint
  → 🟡/wyklucz z bramki 2); detektor rozwinięcia (ELLIPSE anty-sygnał + skala standardowa +
  5N/tekst); kategoria 6 (człowiek zaznacza widok na PNG → bbox → cięcie); W-C pass gięcia.
- **SEDNO:** pierwsze realne zlecenie PEŁNYM torem → pierwsze etykiety + pierwszy punkt
  metryki zaufania (dziś: etykiety=0, metryka=0 punktów — aparat w kodzie, nie w danych).

## Stan agentów
Wszystkie 3 fable ZWRÓCONE (zakończone): #1 gwint/otwarte kontury, #2 Tryb decyzji,
#3 wnioski widoków+kategoria 6. Prototypy w scratchpadzie, wnioski/goldeny w repo.
Nic nie commitowane (czeka na Twoją decyzję).
