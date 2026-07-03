# AUDYT — CLAUDE.md (EKSTRAKTOR_DXF-home-V3)

> Przegląd pliku zasad/routingu projektu V3.
> Data audytu: 04.07.2026 · Audytowany stan dokumentu: 03.07.2026 (faza projektowa).
> Zakres: kompletność zasad, spójność wewnętrzna, ryzyka projektowe i wdrożeniowe.
> Charakter: przegląd dokumentu — NIE przegląd kodu (kodu V3 jeszcze nie ma).

---

## 1. Ocena ogólna

Dokument jest dojrzały i napisany z realnych wpadek, nie z teorii — najlepszy dowód to
zasada 6 (zakaz odrzucania flagi po wielkości różnicy) wyprowadzona wprost z błędu na
54_4867. Governance (bramka testowa jako jedyne wejście do produkcji, regression-first,
awans reguł tylko za potwierdzeniem człowieka) jest wzorowy dla domeny, w której błąd
kosztuje materiał i czas maszyny.

Główne ryzyko NIE leży w projekcie zasad. Leży w **skali względem jednej osoby** i w
**kolejności budowy** — łatwo utknąć w rusztowaniu (cztery systemy + zarządzanie +
warianty) zanim jakakolwiek działająca V3 udowodni benchmarkiem, że jest ≥ V2.

Werdykt: dokument gotowy jako konstytucja projektu. Przed rozbudową rekomendowane
poprawki spójności (rozdz. 3) i decyzja o cienkiej pionowej ścieżce (P1-01).

Legenda priorytetów: **P1** = adresować przed dalszą budową · **P2** = adresować w trakcie ·
**P3** = kosmetyka / dług do spłaty później.

---

## 2. Mocne strony (do zachowania — nie regresować)

- **Zasada 6 jako zakodowana lekcja instytucjonalna.** Największe różnice = najgroźniejsze
  braki; licznik tylko wskazuje GDZIE patrzeć, decyzja zawsze wzrokiem. To jest złoto —
  chroni przed dokładnie tym błędem, który już raz kosztował.
- **Regression-first (zasada 11).** Najpierw przypadek do golden, potem naprawa. Podręcznikowe
  i konsekwentnie powtórzone w kilku miejscach.
- **Bramka vs flager.** Rozróżnienie sygnału czystego (twarda decyzja) od sygnału z szumem
  (licznik konturów) pokazuje realne myślenie o jakości sygnału, nie tylko o kodzie.
  Dyrektywa „szum zwalczać u źródła" (klaster zamiast bbox, polygonize zamiast sklejania
  0,1 mm) jest właściwa.
- **AI może status tylko obniżyć.** Czysta, egzekwowalna granica między determinizmem
  a oceną AI. Nie zostawia miejsca na dryf.
- **Metryka zaufania jako gwiazda polarna.** „Człowiek sprawdza mało i szybko, błędy = zero"
  to dobra, mierzalna definicja sukcesu — lepsza niż abstrakcyjne „dokładność".
- **Modułowość (zasada 8) + nietykalność V1/V2 (zasada 9).** Produkcja odizolowana od
  nauki/zasad/testów; poprzedniki chronione. Redukuje ryzyko regresji przez przypadek.

---

## 3. Ustalenia (findings)

### P1 — adresować przed dalszą budową

**P1-01 · Ryzyko big-design-up-front dla solo-projektu**
- *Obserwacja:* Struktura docelowa to cztery systemy + zarządzanie + framework wariantów +
  7 skilli, w większości status `[plan]`. Roadmap kusi, by budować rusztowanie przed
  udowodnieniem V3 ≥ V2 na choćby jednym realnym zleceniu.
- *Ryzyko:* Utknięcie w infrastrukturze; miesiące pracy bez działającego wyniku; trudność
  utrzymania całości w pojedynkę.
- *Rekomendacja:* Zdefiniować w PLAN.md **cienką pionową ścieżkę**: jeden typ rysunku,
  end-to-end (typowanie → W-C → bramki 1–9 → wynik → sweep), benchmark ≥ V2. Dopiero po
  zielonym benchmarku rozszerzać wszerz (kolejne typy, warianty W-A/W-B, systemy nauki/zasad).
  Reszta systemów jako stub do czasu, aż pionowa ścieżka działa.

**P1-02 · Niezależność wariantów jest założona, nie zagwarantowana**
- *Obserwacja:* Bramka 10 i cała wielowariantowość opierają się na tezie „zgodne ≥2
  NIEZALEŻNE metody = wysoka pewność". Tymczasem W-A (klaster V1) i W-B (kategorie V2)
  mogą dzielić ślepą plamę — dokument sam stwierdza, że klaster gubi cechy odseparowane
  „w każdym trybie".
- *Ryzyko:* Dwa skorelowane silniki zgodnie gubią tę samą cechę → bramka 10 daje FAŁSZYWE
  poczucie pewności i przepuszcza 🟢, choć element ma braki. To dokładnie klasa błędu
  z 54_4867, tylko zamaskowana „zgodnością".
- *Rekomendacja:* (a) W-C (region+warstwa) ZAWSZE obowiązkowy jako jeden z wariantów —
  bo łapie to, co tamte gubią. (b) Bramka 10 musi znać macierz korelacji metod: zgoda
  W-A+W-B (pokrewne) waży mniej niż zgoda W-C+(W-A|W-B). Zapisać wprost w `config/warianty.yaml`
  i w opisie bramki 10, żeby „2 z 3" nie było liczone naiwnie.

**P1-03 · Rysunek wielotypowy — brak strategii łączenia profili**
- *Obserwacja:* „Rysunek może mieć WIĘCEJ NIŻ JEDEN typ; typ → profil ustawień". Nie
  zdefiniowano, co się dzieje, gdy typy dają sprzeczne ustawienia (np. progi bramek,
  które silniki uruchomić, kolor/warstwa geometrii).
- *Ryzyko:* Pierwszy realny rysunek wielotypowy = niezdefiniowane zachowanie; ciche
  nadpisanie profilu albo wybór „ostatni wygrywa" bez śladu.
- *Rekomendacja:* Dopisać regułę rozstrzygania: albo union najostrożniejszych progów
  (bezpieczniej), albo jawna precedencja typów w `config/typy.yaml`. Konflikt profili =
  log + ewentualnie 🟡. Decyzja przed pierwszym takim rysunkiem, nie po.

### P2 — adresować w trakcie budowy

**P2-01 · „0 regresji" ≠ „V3 ≥ V2 w polu" dopóki golden jest cienki**
- *Obserwacja:* Bramą jest benchmark + 0 regresji na golden set. Na starcie golden będzie
  ubogi (kilka przypadków).
- *Ryzyko:* Wczesny PASS daje złudne bezpieczeństwo — system przechodzi na 5 przypadkach
  i pada na nowym typie, którego golden nie pokrywa.
- *Rekomendacja:* Traktować pokrycie golden jako osobną metrykę raportowaną obok benchmarku
  („benchmark PASS przy N=? przypadków, pokrycie typów = ?/?"). Zasada 11 naturalnie zasili
  golden z czasem — warto to zmierzyć, nie zakładać.

**P2-02 · Koszt kontekstu: duplikacja wiedzy w pliku ładowanym co sesję**
- *Obserwacja:* CLAUDE.md jest czytany na starcie KAŻDEJ sesji, a zawiera pełne studium
  54_4867 i „pigułkę" wiedzy dziedzinowej, która duplikuje CLAUDEv1/v2.
- *Ryzyko:* Co sesję płacisz tokenami za wiedzę potrzebną tylko czasem; przy rozroście
  dokumentu rośnie koszt i maleje czytelność rdzenia zasad.
- *Rekomendacja:* Podział: rdzeń (zasady żelazne + routing + struktura + pipeline) ładowany
  zawsze; studium przypadku i pełna pigułka jako recall on-demand (`kontekst/`, `nauka/wiedza/`).
  W CLAUDE.md zostawić 3–4 zdaniowe skróty z linkiem „szczegóły w …".

**P2-03 · Metryka zaufania zdefiniowana, mechanizm decyzyjny nie**
- *Obserwacja:* „Odsetek próbki 🟢 maleje wraz ze wzrostem zaufania" — kierunek jest, ale
  brak progu/wzoru (przy jakiej metryce próbka spada z 1/10 na 1/20?).
- *Ryzyko:* Bez reguły próbkowanie zostanie „na oko" — a to jest miejsce, gdzie może
  przeciekać błąd (za mała próbka 🟢 przy przeszacowanym zaufaniu).
- *Rekomendacja:* Zdefiniować prosty, jawny próg (np. tabela: przedział metryki → odsetek
  próbki), audytowalny jak reszta reguł. Konserwatywnie: próbka nigdy poniżej pewnego minimum.

**P2-04 · Ostateczność „odtworzenie z TIF" — słabe ogniowo pod zasadą 1**
- *Obserwacja:* Pipeline dopuszcza odtworzenie geometrii z TIF (kolor czerwony, do
  sprawdzenia) gdy brak DXF. 
- *Ryzyko:* Zasada 1 mówi „nie zgadujemy geometrii". Odtworzenie z rastra to z definicji
  aproksymacja — ryzyko subtelnego błędu wymiaru/otworu, który przejdzie bbox.
- *Rekomendacja:* Doprecyzować, że pozycja z TIF NIGDY nie może osiągnąć 🟢 automatycznie —
  twardo 🟠/🔴 (człowiek), niezależnie od zgodności bramek. Warto zapisać jako regułę, nie
  tylko kolor „do sprawdzenia".
  Zaznaczenie na tif, ma tylko pomagac w sprawdzeniu. NIGDY nie odtwarzamy nic z TIF tylko mozemy wizualnie sprawdzic szczegóły.
  Dodaj twardą regułe.

### P3 — dług / kosmetyka

**P3-01 · Numeracja bramek vs opisy.** W tabeli bramek jest 10 pozycji, ale pipeline
odwołuje się do „bramek 1–10" i osobno do „flagera kompletności" jako czegoś poza tabelą.
Warto raz ujednolicić: czy nakładka wynik-na-źródło to bramka, flager, czy oba — teraz jest
opisana jako flager „poza" tabelą, ale w pipeline stoi w kroku KONTROLA. Drobne, ale myli.

**P3-02 · Rozproszenie tej samej zasady.** Zasada 6/7 (100% flag, sweep obowiązkowy)
powtarza się w: zasadach żelaznych, bramkach, sprawdzaniu AI i pipeline. To celowe
wzmocnienie, ale przy edycji łatwo zaktualizować jedno miejsce i zapomnieć o reszcie.
Rozważyć „jedno źródło prawdy" dla definicji + odnośniki.

**P3-03 · Status skilla `/wyciagnij-dxf`.** Opisany jako „działa (V1/V2) → do podmiany na
orkiestrator V3". Warto od razu ustalić, czy V3 przejmuje tę samą nazwę slasha (ryzyko
kolizji podczas równoległego istnienia V2 i V3 w `~/.claude/skills`).

**P3-04 · `wyniki/` nie commitować — brak `.gitignore` w strukturze.** Zasada 14 tego
wymaga; struktura docelowa nie pokazuje `.gitignore`. Drobiazg, ale łatwo przeoczyć
i wrzucić ciężkie PNG/DXF do repo.

---

## 4. Weryfikacja spójności zasad żelaznych

| # | Zasada | Ocena spójności |
|---|---|---|
| 1 | Zero błędnych DXF, wątpliwość = _DO_SPRAWDZENIA | Spójna. Uwaga: ścieżka TIF ją napina (P2-04). |
| 2 | Otwory święte, kontur zamknięty, 1:1, (0,0) | Spójna z bramkami 2/4/5/9. |
| 3 | Szybciej niż ręcznie, człowiek ogląda obrazki | Spójna; zależna od metryki zaufania (P2-03). |
| 4 | Determinizm gdzie się da, AI z bramką za sobą | Spójna, dobrze wyegzekwowana w rozdz. sprawdzania. |
| 5 | AI może tylko obniżyć status | Spójna, kluczowa, powtórzona. |
| 6 | Każda flaga = oględziny, nigdy po wielkości | Spójna; najlepsza zasada w dokumencie. |
| 7 | Sweep domyka zlecenie (wszystkie tryby/kolory) | Spójna; kosztowna — patrz P1-01 (najpierw wąsko). |
| 8 | Modułowość, produkcja odizolowana | Spójna. |
| 9 | V1/V2 nietykalne | Spójna; V3 ma własne kopie silników. |
| 10 | Po zmianie: regresja PASS + benchmark ≥ V2 | Spójna; siła zależna od golden (P2-01). |
| 11 | Najpierw golden, potem naprawa | Spójna, egzekwowalna. |
| 12 | Uczenie = jawne reguły, awans za człowiekiem | Spójna. |
| 13 | Zmiana = wersja + wpis w rejestrze | Spójna; wymaga dyscypliny (audyt.py pomaga). |
| 14 | PNG na czarnym, wyniki bez commita, PL/EN | Spójna; brak .gitignore w strukturze (P3-04). |
| 15 | DWG→DXF może robić operator, pominięcia głośno | Spójna; dobra realistyczna granica człowiek/AI. |

Konfliktów wprost między zasadami nie stwierdzono. Napięcia (nie sprzeczności): zasada 1
vs ścieżka TIF; zasada 3 vs niezdefiniowany próg próbkowania.

---

## 5. Rekomendowana kolejność działań

1. **P1-01** — rozpisać cienką pionową ścieżkę w PLAN.md (jeden typ, end-to-end, benchmark).
2. **P1-02** — W-C obowiązkowy w każdym zestawie wariantów + macierz korelacji w bramce 10.
3. **P1-03** — reguła rozstrzygania profili dla rysunku wielotypowego.
4. **P2-04** — twarda reguła: pozycja z TIF nigdy nie 🟢 auto.
5. **P2-02** — podział dokumentu (rdzeń zawsze / szczegóły on-demand) — obniża koszt sesji.
6. **P2-01 / P2-03** — pokrycie golden jako metryka; próg próbkowania 🟢 jako tabela.
7. **P3-*** — spłata przy najbliższej edycji dokumentu.

---

## 6. Podsumowanie jednym zdaniem

Konstytucja projektu jest solidna i uczciwie wyprowadzona z realnych błędów; największym
zagrożeniem nie jest jakość zasad, lecz pokusa zbudowania całego rusztowania zanim jedna
wąska ścieżka udowodni benchmarkiem, że V3 > V2.
