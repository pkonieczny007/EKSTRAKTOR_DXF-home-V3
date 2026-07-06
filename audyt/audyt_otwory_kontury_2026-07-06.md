# AUDYT: sprawdzanie otworów i konturów zamkniętych (2026-07-06)

Zakres: bramka 2 (kontur domknięty), bramka 4 (bilans otworów okrągłych), bramka 5
(bilans konturów wewnętrznych), sweep kompletności, nakładka wynik-na-źródło,
ocena wariantów (R1/R3) i ich wpięcie w pipeline. Metoda: przegląd kodu
(`produkcja/kontrola/`, `produkcja/silniki/v2/weryfikator.py`,
`produkcja/silniki/extract_positions.py`, `produkcja/ocena.py`,
`sprawdzanie/ai/nakladka.py`, `sprawdzanie/ai/sprawdz_folder.py`), przegląd testów
(`testy/test_bramka5.py` i pokrewne) oraz **weryfikacja empiryczna** dwóch hipotez
skryptem (wyniki niżej, sekcja "Dowody").

## WERDYKT OGÓLNY

**Metoda jest dobrze zaprojektowana co do architektury** — wielowarstwowa obrona
(licznik + wizualna + zamknięte kontury), liczenie topologiczne przez
`shapely.polygonize` zamiast kruchej cyklomatyki, dedup okręgów współśrodkowych
PRZED bilansem, kierunek błędów przeważnie bezpieczny (fałszywe żółte, nie fałszywe
zielone). Testy bramki 5 sprawdzają inwarianty lustra/jitteru/dedupu — to rzadko
spotykany poziom rygoru.

**Ale ma 3 istotne luki wykonawcze** (nie architektoniczne), z których jedna jest
potwierdzona empirycznie i uderza w codzienną produkcję:

1. 🔴 **Gwint (okrąg+łuk ~270°) daje fałszywą CZERWIEŃ** — każdy poprawny detal
   z gwintem jest dyskwalifikowany przez R1 (`ocena.py`) i flagowany NIEDOMKNIĘTE.
2. 🟠 **Nakładka ma martwe pole na małe cechy dużych detali** — próg szumu skaluje
   się z przekątną, brakujący otwór Ø12 na blasze 2000×1000 jest odfiltrowany jako jitter.
3. 🟠 **Niespójny próg bramki 5** — `bilans()` flaguje od delta≥2, choć CLAUDE.md,
   sweep i ocena mówią delta≥1; pojedyncza zgubiona fasola przechodzi `bilans()` na zielono.

Żadna luka nie prowadzi wprost do "błędny DXF na laser bez flagi", bo warstwy się
dublują (sweep delta≥1 + ocena wariantów łapią to, co przepuści bilans/nakładka).
Luka gwintu działa w drugą stronę — produkuje **fałszywe czerwienie**, a to jest
dokładnie mechanizm "fałszywe flagi uczą ignorowania flag" (lekcja 54_4867), przed
którym projekt sam się broni.

---

## 1. Co jest zaprojektowane DOBRZE (potwierdzenie)

| Element | Ocena | Dlaczego |
|---|---|---|
| `bilans_konturow.py` — polygonize zamiast cyklomatyki | ✅ | prawdziwa topologia; `EndpointSnapper` decyduje REALNĄ odległością, nie granicą komórki round(); root-fix off-by-one na lustrach potwierdzony testem inwariantów |
| Dedup okręgów współśrodkowych PRZED liczeniem | ✅ | duble maskują braki (5vs4 "wygląda dobrze", po dedupie 3vs4 = brak); jest test (`test_bramka5.py` — dołożony dubel nie zmienia bilansu); zostaje najmniejszy promień = średnica wiercenia (zgodne z wiedzą Ø13+Ø14.7) |
| CIRCLE: środek OCS→WCS | ✅ | lustro CAD (extrusion 0,0,-1) obsłużone w `bilans_konturow.py:115`; bez tego okrąg po lustrze liczyłby się po złej stronie |
| Flager vs bramka (delta wskazuje GDZIE, decydują oczy) | ✅ | konsekwentnie w sweep, nakładce, sprawdz_folder; twarda tylko NIEDOMKNIĘTE |
| Sweep: prawda z trybów CZYSTYCH (n_outer==1), 'all' tylko diagnostyka | ✅ | rozwiązuje "geometria na kolorze 2/4/7" (SL40061302); rozbieżności trybów logowane GŁOŚNO |
| Nakładka: dwa kierunki pokrycia + auto-lustro + zakreślanie skupisk braków | ✅ | `pokrycie_zrodla` to właściwa miara kompletności (cecha bez czerwonej nakładki); skupiska sortowane malejąco = zasada 6 (największe różnice pierwsze) |
| Ocena wariantów: R1 dyskwalifikacja laserowa, R4 zwycięzca wymaga potwierdzenia | ✅ | delta>0 zwycięzcy → żółty z jawnym powodem; nigdy cichy wybór |
| AI może tylko obniżyć status | ✅ | `sprawdz_folder.py` obniża zielony→żółty, nigdy odwrotnie |
| Testy: inwarianty lustro/jitter/dedup na 7 wzorcach golden | ✅ | testują dokładnie te własności, które w V2 zawodziły |

Architektura "trzy niezależne kontrole + sweep domykający" jest poprawna:
pojedyncza słabość jednej warstwy nie przechodzi do lasera, bo inna warstwa liczy
tę samą własność inną metodą.

---

## 2. USTALENIA (od najgroźniejszych)

### U1 🔴 Gwint = fałszywa czerwień na każdym detalu z gwintem (POTWIERDZONE EMPIRYCZNIE)

Wiedza projektu (`kontekst/wiedza/gwint-okrag-luk-dimension.md`) mówi wprost: łuk
gwintu ~270° NIE jest wadą konturu i "bramka 2 / bilans_konturow ma być świadoma
gwintu". **Kod tego nie robi** — grep po "gwint" trafia tylko dokumentację, żaden
moduł kontroli nie wyklucza łuku gwintu.

Dowód (detal 100×100 + okrąg Ø8.5 + współśrodkowy łuk R5/270°, syntetyczny):

```
bilans_konturow: interior=1, cuts=1, flags=['NIEDOMKNIETE: ... (bramka 2)']
open_ends (bramka 2 W-B): 2
```

Skutki kaskadowe (wszystkie ścieżki naraz):
- `bilans()` → semafor **czerwony** ("NIE na laser") dla poprawnego wyniku;
- `ocena.zmierz_wariant` → `niedomkniete=True` → **R1 dyskwalifikuje KAŻDY wariant**,
  który poprawnie zostawił łuk gwintu (zgodnie z wiedzą "zostaw OBA");
  jeśli wszystkie warianty mają gwint → "WSZYSTKIE warianty mają otwarty kontur → czerwony, człowiek";
- `sweep` → semafor czerwony na pozycji;
- bramka 2 W-B → ZOLTY "2 otwarte końce".

To jest anty-wzorzec, przed którym projekt sam ostrzega: fałszywa czerwień na
POPRAWNEJ geometrii uczy operatora klikać "OK" bez patrzenia. Dodatkowo tworzy
presję, by silnik "naprawiał" detal przez usunięcie łuku gwintu — a wtedy ginie
informacja technologiczna (M10 → wiercenie 8.5).

**Brakuje też testu**: `regresja_znane_bledy.py` (XFAIL) nie ma przypadku gwintu,
mimo że przypadek bojowy istnieje (38_1847 / SL40852200).

**Rekomendacja** (ścieżką projektową, zasady 8+11):
1. NAJPIERW golden: `testy/golden/gwint_okrag_luk_270/` z SL40852200_p1 + wpis
   XFAIL w `regresja_znane_bledy.py` (cel: NIEDOMKNIĘTE nie flaguje łuku gwintu,
   interior liczy okrąg wiercenia, dedup NIE skleja okrąg+łuk).
2. Propozycja w `zasady/propozycje/`: detekcja kandydata gwintu wg wiedzy
   (CIRCLE+ARC współśrodkowe tol 0.5 mm, R_łuku>R_okręgu, rozpiętość <360°,
   opcjonalnie potwierdzenie DIMENSION `M\s?\d+`) → łuk wykluczony z testu
   NIEDOMKNIĘTE/open_ends, ale ZOSTAJE w geometrii wyniku. Wykrycie bez
   potwierdzenia tekstem = 🟡 (nie cicho zielony).
3. Projekt poprawki to zadanie dla fable-advisor (tak przypisano w wiedzy).

### U2 🟠 Nakładka: martwe pole na małe cechy dużych detali (tol ∝ przekątna)

`nakladka.py:259`: `tol = max(0.006*diag, ...)`, a filtr szumu skupisk braku
odrzuca skupiska o długości < `3*tol` (`PROG_SZUM_BRAKU`). Progi kalibrowano na
golden SL10596945 (mały detal, skala 1/5) — tam działają. Ale skalują się z
przekątną detalu:

| Detal | diag | tol | próg skupiska (3·tol) | zgubiony otwór Ø12 (obwód 37.7 mm) |
|---|---|---|---|---|
| 400×200 | 447 | 2.7 | 8.0 | wykryty (37.7 > 8.0) ✅ |
| 1000×500 | 1118 | 6.7 | 20.1 | wykryty ✅ |
| 2000×1000 | 2236 | 13.4 | **40.2** | **ODFILTROWANY jako jitter** ❌ |

Przy dużym detalu zawodzi też druga linia: spadek `pokrycie_zrodla` o ~0.4–0.5%
nie przebija progu 97%. Czyli **obie** miary nakładki są ślepe na mały otwór
dużej blachy — a nakładka jest opisana jako "najpewniejsza metoda, ~0 fałszywych"
i jest rdzeniem sprawdzania AI (`sprawdz_folder.py` flaguje właśnie po
`pokrycie_zrodla` + `braki_bboxy`).

Łagodzenie w systemie: bilans konturów/okręgów (delta≥1 w sweep i ocenie) liczy
sztuki niezależnie od długości — zgubiony okrąg złapie. Ale cecha, którą liczniki
potrafią zgubić w szumie (np. przy rozjeździe trybów), na dużym detalu nie ma już
siatki bezpieczeństwa w nakładce.

**Rekomendacja**: dołożyć górny CAP na tol w jednostkach rzeczywistych detalu
(np. `tol ≤ max(2 mm, 1.5·s)` po przeliczeniu skali) albo skalować `PROG_SZUM_BRAKU`
odwrotnie do rozmiaru; NAJPIERW golden: duży detal (≥1500 mm) z wyciętym małym
otworem — obecny kod ma na nim pokazać brak flagi (XFAIL), poprawka ma go zapalić.

### U3 🟠 Niespójny próg bramki 5: `DELTA_KONTURY=2` vs deklarowane delta≥1

- CLAUDE.md (KONTROLA DETALU GOTOWEGO): "delta ≥1 konturu lub ≥1 okrąg = FLAGA";
  pipeline: "flagi delta≥1 od bramki 5/polygonize".
- `sweep.py`: `PROG_DELTA = 1` ✅; `ocena.py`: każde delta>0 zwycięzcy → żółty ✅.
- **`bilans_konturow.py:50`: `DELTA_KONTURY = 2`** ❌ (komentarz "zasada karta
  kontrolna" — nieaktualny, karta mówi ≥1).

Skutek: `bilans()` (CLI dwuplikowe i każdy przyszły import) daje **zielony** przy
JEDNEJ zgubionej fasoli/slocie — czyli dokładnie w klasie błędu, dla której V3
powstała (otwory nieokrągłe są niewidzialne dla `delta_okregi`). Dziś w pipelinie
ratują to sweep i ocena, ale moduł nazwany "BRAMKA 5" z progiem niezgodnym ze
specyfikacją to pułapka na każdego, kto go wepnie w nowe miejsce.

**Rekomendacja**: `DELTA_KONTURY = 1` + test w `test_bramka5.py` (bilans p3 vs
p3-minus-jedna-fasola = żółty). Zmiana w `produkcja/` → regresja + benchmark
(zasada 10); kierunek bezpieczny (może tylko DODAĆ oględzin, jak przy sweepie).

### U4 🟡 Bramka 2 (W-B `open_ends`): trzy znane słabości metody parzystości na siatce

`extract_positions.py:157`: końcówki kwantowane `round(p/tol)` i liczone parzystością:

1. **Granica komórki** — dwa końce w odległości 0.01 mm mogą trafić do różnych
   komórek (fałszywe 2 otwarte końce), a końce 0.09 mm od siebie w jednej komórce
   się "sparują". To ta sama wada, którą `bilans_konturow` naprawił
   `EndpointSnapper`-em — ale twarda bramka laserowa nadal używa starej metody.
2. **Parzystość maskuje** — zdublowana linia (częste w CAD) nad realną dziurą
   w konturze daje parzystą liczbę końców w węźle → 0 otwartych końców mimo
   przerwy; T-junction (koniec linii na środku innej) daje fałszywy 1.
3. **Niespójna surowość** — otwarty kontur w W-B to ZOLTY, w bilansie/ocenie
   czerwony/dyskwalifikacja. W trybie `--parytet` (sam W-B) `open_ends` jest
   JEDYNĄ kontrolą domknięcia — najsłabsza metoda tam, gdzie nie ma redundancji.

W trybie domyślnym (warianty) ryzyko niskie — NIEDOMKNIĘTE z polygonize (dangles/
cuts po nodowaniu unary_union) jest odporniejsze i działa równolegle.

**Rekomendacja**: docelowo bramka 2 = delegacja do `bilans_konturow` (dangles+cuts
na encjach konturu) zamiast osobnej implementacji; do tego czasu udokumentować, że
`--parytet` ma słabszą kontrolę domknięcia. Uwaga: poprawka MUSI iść razem z U1
(inaczej polygonize przeniesie fałszywą czerwień gwintu także do W-B).

### U5 🟡 Bramka 4 (`policz_otwory`): łuk eliptyczny liczony jako otwór (POTWIERDZONE)

`weryfikator.py:98`: `getattr(e, "closed", True)` — **ezdxf ELLIPSE nie ma
atrybutu `closed`** (dowód niżej), więc każdy ŁUK eliptyczny (niepełna elipsa)
liczy się jako otwór. Kierunek groźny to maskowanie: łuk eliptyczny w wyniku
podbija licznik i może skompensować zgubiony okrąg (warunek `wynik >= zrodlo`
przejdzie). Prawdopodobieństwo niskie, ale naprawa jednolinijkowa:
`abs((e.dxf.end_param - e.dxf.start_param) % (2π)) < eps` lub porównanie
parametrów do pełnego obiegu. Dodatkowo: źródłowe `n_otworow` nadal liczone w
prostokątnym bbox widoku, nie w klastrze — TODO z `bramki.py:28` wciąż otwarte
(bbox łapie okręgi sąsiada → fałszywe żółte; kierunek bezpieczny, ale to szum).

### U6 🟡 Sweep: ciche pomijanie pozycji bez `src_x1` (zasada 15)

`sweep.py:202`: `rows = [r for r in csv.DictReader(...) if r.get("src_x1")]` —
pozycje bez boxa źródła (czyli te, których ekstrakcja w ogóle nie znalazła —
najbardziej ryzykowne!) znikają ze sweepa **bez logu**. Narusza zasadę 7
("WSZYSTKIE pozycje") i 15 ("pominięcia logować GŁOŚNO"); `sprawdz_folder.py`
robi to poprawnie ("brak boxa zrodla ... GLOSNO"). Naprawa: logować + wiersz
z semaforem żółtym "brak boxa źródła" w raporcie sweepa.

### U7 🔵 Osie koloru 7 przecinające otwory zawyżają interior źródła (do pomiaru)

`bilans_konturow` filtruje tylko gięcie (kolor 6 / warstwa GIECIE); linii osi
o kolorze 7 i linetype CENTER/DASHDOT nie filtruje niczym (V1 `partition`
odfiltrowywał DASHED/HIDDEN). Oś przecinająca otwór dzieli po nodowaniu jego
twarz na 2–4 twarze wewnętrzne → zawyżone `zrodlo_prawda` → fałszywe żółte na
każdej pozycji z osiami na warstwie geometrii. Kierunek bezpieczny, ale to
systematyczny szum (a szum flagera "zwalczać u źródła"). Na 7 wzorcach golden
zmierzono 0 fałszywych flag — wzorce mogą po prostu nie mieć osi w regionie.
**Rekomendacja**: golden z osiami krzyżowymi na kolorze 7 + ewentualny filtr
linetype (CENTER/DASHDOT/PHANTOM o długości < progu) w liczeniu regionu.

### U8 🔵 Drobne

- `bilans()` flaguje tylko delta>0; nadmiar konturów w wyniku (obca geometria)
  nie daje flagi w bilansie — łapie go dopiero ocena wariantów (klasa 1) i
  `pokrycie` nakładki. Spójne z filozofią, ale warto dopisać do docstringa.
- `licznik_konturow.py` (stary, cyklomatyczny) wciąż w repo bez banera
  DEPRECATED w kodzie — ryzyko przypadkowego importu zamiast bramki 5.
- Nakładka: alignment bbox-fit nie próbuje rotacji 90° — jeśli kiedyś silnik
  zapisze wynik obrócony względem widoku, pokrycie spadnie (fałszywa flaga,
  kierunek bezpieczny).

---

## 3. Dowody (weryfikacja empiryczna, 2026-07-06)

Skrypt syntetyczny (ezdxf, bez plików produkcyjnych):

```
ELLIPSE ma attr closed: False
getattr(e_full,'closed',True) = True      # pelna elipsa: przypadkiem dobrze
getattr(e_arc ,'closed',True) = True      # LUK eliptyczny: liczony jako otwor (BLAD)

GWINT (kontur 100x100 + okrag r=4.25 + luk r=5.0, 270 st):
  bilans_konturow: interior=1, dangles=0, cuts=1,
                   flags=['NIEDOMKNIETE: ... -> mozliwy otwarty kontur (bramka 2)']
  open_ends (W-B): 2
```

Pozostałe ustalenia z przeglądu kodu (ścieżki i numery linii w treści ustaleń).

## 4. Podsumowanie priorytetów

| # | Ustalenie | Ryzyko | Kierunek błędu | Pierwszy krok |
|---|---|---|---|---|
| U1 | gwint → fałszywa czerwień (potwierdzone) | wysokie | fałszywe 🔴 uczą ignorowania flag + kasują dobre warianty | golden SL40852200 + XFAIL, potem fable-advisor |
| U2 | nakładka ślepa na małe cechy dużych detali | średnie | fałszywe 🟢 w warstwie "najpewniejszej" | golden: duży detal − mały otwór (XFAIL) |
| U3 | próg bilans() =2 zamiast =1 | średnie | fałszywe 🟢 na 1 fasoli (poza pipeline) | DELTA_KONTURY=1 + test + regresja |
| U4 | open_ends: siatka+parzystość | niskie (parytet: średnie) | oba kierunki | delegacja do polygonize PO naprawie U1 |
| U5 | ELLIPSE bez `closed` → łuk = otwór | niskie | możliwe maskowanie | 1-liniowa poprawka + test |
| U6 | sweep cicho gubi pozycje bez boxa | niskie | ciche pominięcie | log + żółty wiersz w raporcie |
| U7 | osie kol. 7 zawyżają interior | niskie | fałszywe 🟡 (szum) | golden z osiami, pomiar |

Wszystkie poprawki wyłącznie ścieżką projektową: golden → propozycja → regresja
43/43 + benchmark ≥ V2 → potwierdzenie człowieka (zasady 8, 10, 11).
