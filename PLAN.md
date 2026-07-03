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

1. **Bramka 5**: bilans konturów wewnętrznych przez `shapely.polygonize`
   (w KLASTRZE części, nie bbox; bez off-by-one sklejania 0,1 mm na lustrach).
   Do `requirements.txt` wchodzi `shapely`.
2. **Nakładka wynik-na-źródło** (`sprawdzanie/ai/nakladka.py`) — render pary + overlay;
   wejście dla oględzin AI (100% flag, od największych różnic, dowód PNG).
3. **Sweep kompletności** (`produkcja/kontrola/sweep.py`) — wszystkie pozycje,
   wszystkie tryby (col7/col2/col4/all/warstwa-geometria); raport do `testy/raporty/`.
4. **Integracja W-C**: `region_warstwa.py` jako pełnoprawny silnik (interfejs jak W-A/W-B),
   auto-fallback gdy bramka 5 / nakładka wykryją brak.
5. Przypadki 54_4867 (8 pozycji z realnymi brakami) → `testy/golden/` jako testy bramki 5.

**Kryterium: bramka 5 + sweep wykrywają WSZYSTKIE braki z 54_4867 (golden),
zero regresji na dotychczasowych testach.**

## Etap 3 — wielowariantowość + ocena (bramka 10) ⬜

1. Orkiestrator generuje warianty wg `config/typy.yaml` (`silniki` per typ)
   do `wyniki/<zlecenie>/warianty/{poz}__w?.dxf`.
2. `produkcja/ocena.py` wpięta w pipeline: macierz zgodności, wybór zwycięzcy,
   `ocena.csv`; rozbieżność = eskalacja (nigdy cichy wybór); przegrane warianty zostają.
3. `produkcja/raport.py`: scalenie raportów silników + oceny; zapis statusów do wykazu
   (kolumny jak 54_4867: status kolorem, uwagi, plik_dxf, technologia, wymiar_dxf_x/y,
   skala, uwagi_wymiar).

**Kryterium: na golden zgodność ≥2 silników na pozycjach zielonych;
każda rozbieżność widoczna w raporcie z powodem; benchmark V3 ≥ V2.**

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
