# EKSTRAKTOR_DXF V3 — produkcyjny system ekstrakcji DXF (skille + skrypty Python)

> Rysunek złożeniowy (DWG/DXF) + wykaz materiałowy (xlsx) → gotowe DXF 1:1 pozycji
> blaszanych do Lantek Expert (nesting + laser). V3 = cztery niezależne systemy
> (**produkcyjny · testowy · tworzenia zasad · nauki**) + **wielowariantowość**
> (kilka wersji pliku → ocena → najlepsza) + **podwójne sprawdzanie** (AI i człowiek)
> + **zarządzanie** skillami i aplikacjami Python.
>
> Narzędzie opiera się na **lokalnych skillach i skryptach Python — AI ich używa,
> nie zastępuje**. Cel: V3 > V2 > V1 (mierzalnie, benchmarkiem).

## Stan (04.07.2026) — SZKIELET ZBUDOWANY, PARYTET Z V2 ZWERYFIKOWANY

Struktura z tego pliku istnieje i działa: silniki przeniesione z V2 (kopie — tam nie
piszemy), **regresja 43/43 PASS, testy_v2 35/35 PASS, benchmark V2≥V1 PASS — w V3**;
orkiestrator V3 (typowanie + delegacja do W-B) przeszedł smoke-test end-to-end.
Etapy i kryteria: `PLAN.md` (etap 0 ✅, etap 1 ✅/do obserwacji, etapy 2–6 ⬜).
Poprzedniki (NIETYKALNE, zasada 9):
- **V1** `C:\Python_CLaude\EKSTRAKTOR_DXF\EKSTRAKTOR_DXF-home` — prototyp CLI + skill `/wyciagnij-dxf`.
- **V2** `C:\Python_CLaude\EKSTRAKTOR_DXF\EKSTRAKTOR_DXF-home-V2` — orkiestrator + kategorie + weryfikator.

**Nowa sesja czyta w kolejności:**
1. Ten plik (zasady + architektura), potem `PLAN.md` (na którym etapie jesteśmy).
2. `kontekst/CLAUDE_v1.md` — wiedza dziedzinowa (konwencje klientów, pułapki 1–8).
3. `excalidraw/kontekst_deploy/CLAUDEv2.md` — architektura V2, pułapki wdrożenia, samodoskonalenie.
4. `kontekst/kategorie_szukania.html` — kategorie szukania: stan i interfejs wtyczek.
5. Lekcje 54_4867: `kontekst/lekcje_54_4867_stan.md`, `kontekst/strategia_kompletnosc_otworow.md`
   (7 warstw obrony), `kontekst/lekcje_54_4867_raport_poprawek.md`.
6. `kontekst/wiedza/MEMORY.md` — indeks notatek z realnych zleceń (recall przed ekstrakcją!).
7. Tablice: `excalidraw/OPIS_PROJEKTU_v3.excalidraw`, `excalidraw/OPIS_system_produkcyjny.excalidraw`.

**Roadmap:** tablica ✅ → prompt ✅ → CLAUDE.md ✅ → PLAN.md ✅ → szkielet systemów ✅
→ działająca V3 (parytet ✅ → etapy 2–3: kompletność + warianty) → udoskonalanie przez testy i naukę.

## Szybki start

```bash
# audyt narzedzi (kazda sesja zaczyna od tego)
python zarzadzanie\audyt.py
python zarzadzanie\deploy_skilli.py            # deploy skilli do ~/.claude/skills + SecondBrain (DRY-RUN; --wykonaj = kopiuje)

# REGRESJA + TESTY — PO KAZDEJ zmianie w produkcja/ (PASS = warunek oddania!)
python testy\regresja.py
python testy\testy_v2.py
python testy\benchmark_v2.py          # V2 >= V1 encja-po-encji (36 plikow)
python testy\benchmark_v3.py          # V3 (warianty) >= V2 (W-B) - warunek defaultu --warianty
python testy\regresja_znane_bledy.py  # XFAIL cele silnika; [XPASS] -> awansuj do regresji
python testy\test_bramka5.py          # bramka 5: bilans konturow (shapely; lustro/jitter/dedup)
python testy\test_sweep.py            # sweep: kontury regionu we wszystkich trybach
python testy\test_nakladka.py         # nakladka wynik-na-zrodlo (pokrycie_zrodla<97 = brak)
python testy\test_sweep_54_4867.py    # sweep lapie realne braki 54_4867 (safety net)
python testy\test_gr4.py              # golden 38_1847 gr4: 2 realne bledy (zwodnicza zielen)
python testy\test_wc.py               # silnik W-C region+warstwa: odtwarza kompletnosc, OCS
python testy\test_warianty.py         # wielowariantowosc: score_variants + warianty_pozycji (W-C>W-A)
python testy\test_raport.py           # raport: merge ocena+raport+pomiar DXF, uwagi_wymiar, technologia, writeback do KOPII wykazu
python testy\test_sprawdz_folder.py   # sprawdzanie AI folderu: nakladka per pozycja -> flaga kompletnosci, auto-obnizenie zielony->zolty
python testy\test_przeglad.py         # przeglad czlowieka: galeria V3 (semafor finalny, probka zielonych) + worklist werdyktow -> etykiety
python testy\test_metryka.py          # metryka zaufania: odsetek do przegladu, rozklad semaforow, trend (replace po data+zeinr)
python testy\test_adnotacje.py        # kategoria 4: babelek nr pozycji -> klaster (filtr wymiarem), hint gespiegelt
python testy\test_korpus.py           # kategoria 5: dopasowanie do archiwum po sygnaturze (n_circ/n_geom); rozjazd=niepewny
python testy\test_typowanie.py        # typowanie: profil_rysunku (progi+podpowiedzi; typ DOSTRAJA nie ogranicza silnikow)
python testy\wszystkie.py             # WSZYSTKIE testy jedna komenda (--szybko pomija wolne)

# EKSTRAKCJA V3 (etap 3: DEFAULT wielowariantowosc W-A/W-B/W-C + ocena; --parytet = sam W-B)
python produkcja\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow> [--parytet]
python produkcja\warianty.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>  # bezposrednio warianty+ocena

# narzedzia pipeline
python produkcja\typowanie.py <rysunek_conv.dxf>          # typ rysunku (baza: config/typy.yaml)
python produkcja\kontrola\bramki.py --lista                # rejestr 10 bramek
python produkcja\kontrola\bramki.py <plik.dxf> <dmax> <dmin>   # kontrola post-hoc (8 bramek W-B)
python produkcja\ocena.py <A.dxf> <B.dxf>                  # zgodnosc wariantow (bramka 10, CLI)
python produkcja\raport.py <folder_wynikow> [<conv.dxf>] [--wykaz <wykaz.xlsx>]  # scal ocen+raportow+pomiar DXF -> podsumowanie.csv; --wykaz=statusy do KOPII (oryginal nietkniety)
python produkcja\silniki\v2\galeria.py <folder_wynikow> [--rysunki <folder>]  # kafelki

# sprawdzanie + nauka + metryka
python sprawdzanie\ai\sprawdz_folder.py <folder_wynikow> <zrodlo_conv.dxf> [--werdykty-ai]  # nakladki + flagi kompletnosci (100% flag; auto-obniza zielony->zolty); --werdykty-ai=WATPLIWOSC zrodlo=ai do etykiet
python sprawdzanie\czlowiek\przeglad.py <folder_wynikow> [--rysunki F] [--probka N]  # galeria przegladu + worklist werdyktow
python sprawdzanie\czlowiek\przeglad.py --werdykty <wypelniony.csv>  # import OK/BLAD -> nauka/etykiety
python sprawdzanie\czlowiek\werdykty.py <plik> OK|BLAD [kategoria] [--kto ai|czlowiek]
python nauka\destylacja.py                                 # korpus+etykiety -> szkic wnioskow
python zarzadzanie\metryka.py <folder_wynikow> [--bez-trendu]  # metryka zaufania: odsetek do przegladu, semafory, trend (glowna miara sukcesu)

# render PNG — ZAWSZE przez ten skrypt (czarne tlo!)
python testy\pretesty\_render_png.py "<folder>/*.dxf"
```

## Problemy V1/V2 → root-fixy V3

| Problem | Root-fix w V3 |
|---|---|
| Gubi otwory **NIEokrągłe** (fasole, sloty, kwadraty) → element bez otworów na laser | Silnik W-C „region+warstwa" (wszystkie encje warstwy geometrii w bbox widoku — sprawdzony ręcznie na 54_4867) + **bramka 5: bilans konturów wewnętrznych** (shapely.polygonize, nie tylko CIRCLE) + nakładka wynik-na-źródło |
| Cechy odseparowane (wyspa na środku blachy) wypadają, a wymiar zewnętrzny się zgadza — **kontrola wymiaru ≠ kontrola kompletności** | Kontrola **kompletności** zamiast samego bbox: bilans konturów + nakładka + sprawdzanie AI z zakreślaniem różnic na czerwono |
| **Fałszywe flagi uczą ignorowania flag** (54_4867: różnice 17/22/64/128 odrzucone bez oględzin jako „szum bbox" — były REALNYMI brakami całych bloków otworów) | Liczniki liczone **w klastrze części, nie w prostokątnym bbox** (mniej szumu) + żelazna zasada 6: 100% flag oglądanych wzrokiem, zamknięcie flagi tylko z dowodem PNG |
| Sprawdzanie za długie; gdy silnik się myli → brak zaufania → kontrola 100% (zabija zysk) | **Wielowariantowość**: zgodność 2–3 niezależnych metod = pewność bez człowieka; semafor z jawnym POWODEM; człowiek ogląda tylko 🟡/🔴 + próbkę 🟢; galeria obrazków zamiast otwierania CAD |

### Studium: zlecenie 54_4867 (SBM, 98 pozycji, 43 rysunki) — dowód na projekt V3

Największy dotąd test bojowy V2 — źródło większości root-fixów V3:
- **8 pozycji z realnymi brakami** naprawionych metodą region+warstwa (kontury: 9→26,
  6→17, 33→67, 54→68, 20→21, 7→8, 4→8, 0→3) — bloki wentylacji, kolumny slotów,
  wielki owal Ø225 (spline niepołączony z konturem), kwadratowe otwory.
- Bilans „71 zielonych" był **za optymistyczny** — część zielonych miała zgubione cechy;
  wymiar się zgadzał, więc nic nie alarmowało.
- Klaster gubi cechy odseparowane **w każdym trybie** (col7/col2/col4/all/geometria);
  geometria bywa na nieoczekiwanym kolorze (SL40061302: kolor 2, nie 7) — sweep nie może
  zakładać koloru.
- Domykający **sweep kompletności** (region vs dostarczone, wszystkie pozycje i tryby)
  znalazł braki, których lista flag nie miała (SL10599171_p1, SL40061302_p1).
- Bliźniaki bywają **asymetryczne** (SL10599245: p1 z owalem, p2 bez — dwie różne części
  o tym samym obrysie, NIE lustro) → nie zakładać symetrii, asymetria = 🟡 do potwierdzenia.
- Podział pracy: operator sam masowo konwertuje DWG→DXF w GstarCAD (łatwe dla człowieka,
  mozolne dla AI) — pipeline przyjmuje gotowe `_conv.dxf`.

## Zasady żelazne

1. **Zero błędnych DXF na produkcji.** Element wypalony błędnie = koszt materiału i maszyny.
   Wątpliwość = `_DO_SPRAWDZENIA` (człowiek). **Nie zgadujemy geometrii.**
2. **Otwory święte** (także nieokrągłe), kontur zamknięty, skala 1:1, wynik wyśrodkowany (0,0).
   Detal gotowy przechodzi TRZY kontrole (liczbowa bilans konturów/otworów + wizualne
   porównanie + ZAWSZE na końcu ZAMKNIĘTE KONTURY = 0 otwartych końców, bramka laserowa)
   — patrz „KONTROLA DETALU GOTOWEGO". **Zgodny wymiar NIE dowodzi kompletności** (można
   zgubić otwór/owal przy dobrym bbox); **otwarty kontur = NIE na laser, nawet gdy otwory OK.**
3. **Szybciej niż ręcznie**: generowanie + sprawdzenie < narysowanie od zera. Człowiek
   porównuje obrazki, nie otwiera CAD; każdy status 🟡/🔴 ma jawny powód.
4. **Deterministycznie, gdzie się da**: geometria, liczenie konturów/otworów, skala, wymiary
   = skrypty (ezdxf/shapely). AI tylko tam, gdzie skrypt nie wystarcza (typowanie rysunku,
   ocena wizualna, destylacja wniosków) — i każdy krok AI ma skryptową bramkę za sobą.
5. **AI może status wyniku tylko OBNIŻYĆ (🟢→🟡), nigdy podnieść.** Kontrola geometrii
   zawsze skryptem; ocena AI jest warstwą dodatkową, nie zamiennikiem.
6. **KAŻDA flaga kompletności = oględziny wzrokowe** (render region vs wynik). **NIGDY nie
   odrzucać flagi po wielkości różnicy** — największe różnice = najgroźniejsze braki
   (błąd weryfikacji z 54_4867: „brak 128" uznany za szum był realnym brakiem bloku
   perforacji). Licznik tylko wskazuje GDZIE patrzeć; decyzja zawsze wzrokiem, 100% flag.
   Zamknięcie flagi jako false-positive wymaga DOWODU (para PNG w raporcie).
7. **Zlecenie domyka sweep kompletności**: region+warstwa vs dostarczone dla WSZYSTKICH
   pozycji i WSZYSTKICH trybów ekstrakcji (geometria bywa na kolorze 2/4/7/warstwie —
   nie zakładać!). Bez sweepa zlecenie nie jest skończone.
8. **Modułowość**: systemy nauki/zasad/testów NIE dotykają produkcji bezpośrednio. Nowa
   zasada/sposób wchodzi do produkcji WYŁĄCZNIE przez system testowy (0 regresji)
   i za potwierdzeniem człowieka.
9. **V1 i V2 nietykalne** — do `EKSTRAKTOR_DXF-home` i `EKSTRAKTOR_DXF-home-V2` nie piszemy
   NIC. V3 ma własne kopie silników w `produkcja/silniki/` (przeniesione raz, potem żyją tu).
10. Po każdej zmianie w `produkcja/`: `testy/regresja.py` PASS + `testy/benchmark.py`
    (V3 ≥ V2) — **warunek oddania każdej zmiany**.
11. Każdy znaleziony błąd (produkcja, sprawdzanie, przegląd): **NAJPIERW** przypadek do
    `testy/golden/`, **POTEM** naprawa. Błąd nie może się powtórzyć niezauważony.
12. **Uczenie = jawne reguły** (md/yaml czytelne dla człowieka — audyt bez czytania kodu),
    nie czarna skrzynka. Awans obserwacji do reguły ZAWSZE za potwierdzeniem człowieka.
13. Każda zmiana skilla lub aplikacji = podbicie wersji + wpis w `zarzadzanie/rejestr.yaml`.
14. PNG podglądowe ZAWSZE na czarnym tle (jasne linie na białym znikają). `wyniki/` nie
    commitować. Dokumentacja po polsku (w `.py` bez ogonków), nazwy funkcji po angielsku.
15. Etap łatwy-ale-mozolny (masowa konwersja DWG→DXF) może zrobić operator ręcznie —
    pipeline przyjmuje gotowe `_conv.dxf`; AI nie pali czasu na to, co człowiek robi
    szybciej. Pominięte/nieudane pliki logować GŁOŚNO (nigdy cicho — WinError 32!).

## Struktura projektu (zbudowana 04.07.2026; [etap N] = do zrobienia wg PLAN.md)

```
EKSTRAKTOR_DXF-home-V3/
├── CLAUDE.md                  ← ten plik: routing + zasady (jedyne źródło zasad)
├── PLAN.md                    ← etapy wdrożenia 0–6 + kryteria przejścia
├── requirements.txt           ← ezdxf, openpyxl, matplotlib, pyyaml (+shapely w etapie 2)
├── excalidraw/                ← tablice projektowe + kontekst_deploy/ (oryginały CLAUDE v1/v2)
├── kontekst/                  ← wiedza przeniesiona z V2: CLAUDE_v1.md, kategorie_szukania.html,
│   │                            lekcje_54_4867_*.md, strategia_kompletnosc_otworow.md, PLAN_v1.md
│   └── wiedza/                ← JEDEN magazyn notatek z realnych zleceń (10 reguł) + MEMORY.md;
│                                tu trafiają destylaty za potwierdzeniem człowieka
├── config/
│   ├── typy.yaml              ← baza typów rysunków (lantek_1nn, sbm_kolorowa, niemiecka_blokowa…)
│   ├── kategorie.yaml         ← rejestr kategorii szukania (1–3 włączone, 4–6 [etap 6])
│   └── warianty.yaml          ← silniki W-A/W-B/W-C + progi zgodności wariantów
├── produkcja/                 SYSTEM PRODUKCYJNY
│   ├── orkiestrator.py        ← WEJŚCIE V3: typowanie + delegacja do W-B (parytet);
│   │                            warianty→ocena [etap 3]
│   ├── typowanie.py           ← heurystyki typu z bazy typów (działa; kalibracja [etap 4])
│   ├── silniki/               ← KOPIE z V1/V2 (tam nie piszemy!) — patrz silniki/README.md:
│   │   ├── extract_positions.py   W-A (V1: klaster+ranking) — regresja 43/43
│   │   ├── v2/                    W-B (kategorie 1–3 + weryfikator 8 bramek + galeria.py)
│   │   ├── region_warstwa.py      W-C (region+warstwa z 54_4867; silnik pełnoprawny [etap 2])
│   │   └── convert_dwg.py         konwersja DWG→DXF (GstarCAD)
│   ├── kontrola/
│   │   ├── bramki.py          ← rejestr 10 bramek + delegacja kontroli post-hoc do W-B
│   │   ├── licznik_konturow.py ← FLAGER konturów wewn. (szum: off-by-one luster → [etap 2] shapely)
│   │   └── sweep.py           ← sweep kompletności = domknięcie zlecenia [etap 2]
│   ├── ocena.py               ← sygnatura + zgodność wariantów (bramka 10; CLI działa, pipeline [etap 3])
│   └── raport.py              ← podsumowanie semaforów; zapis do wykazu [etap 3–4]
├── sprawdzanie/               SYSTEM SPRAWDZANIA (README: procedura flag!)
│   ├── ai/nakladka.py         ← nakładka wynik-na-źródło [etap 2]
│   └── czlowiek/werdykty.py   ← werdykty przeglądu → nauka/etykiety/ (działa)
├── testy/                     SYSTEM TESTOWY — jedyna brama do produkcji
│   ├── regresja.py            ← 43 sprawdzenia na rysunkach testowych (PASS w V3)
│   ├── testy_v2.py            ← testy modułów W-B (35 sprawdzeń, PASS w V3)
│   ├── regresja_znane_bledy.py ← XFAIL; [XPASS] = naprawione → awans do regresji
│   ├── benchmark_v2.py        ← V2 ≥ V1 encja-po-encji (PASS w V3); benchmark_v3 [etap 3]
│   ├── rysunki/ wzorce/       ← 20 rysunków testowych + wykazy + referencja operatora
│   ├── pretesty/_render_png.py ← render PNG na CZARNYM tle (jedyny słuszny)
│   ├── golden/                ← pary wejście→wzorzec (format: golden/README.md; zasila [etap 2])
│   └── raporty/               ← wyniki testów i metryka zaufania per wersja
├── zasady/                    SYSTEM TWORZENIA ZASAD (README + szablon propozycji)
│   ├── reguly/  propozycje/  przyklady/
├── nauka/                     SYSTEM NAUKI
│   ├── korpus/                ← decyzje.csv (logger --korpus; poza gitem)
│   ├── etykiety/              ← etykiety.csv — werdykty człowieka i AI (werdykty.py)
│   ├── szkolenia/             ← MANUAL UPGRADER (szablon + projekt 54_4867 z V2)
│   └── destylacja.py          ← korpus+etykiety → szkic wniosków (zero LLM; działa)
├── zarzadzanie/               ZARZĄDZANIE SKILLAMI I APLIKACJAMI
│   ├── rejestr.yaml           ← 23 wpisy: skille + aplikacje (wersja, status, test)
│   └── audyt.py               ← rejestr vs rzeczywistość (PASS; każda sesja od tego zaczyna)
├── skills/                    ← źródła skilli (README; migracja /wyciagnij-dxf [etap 5])
├── zlecenia/                  ← SKRZYNKA WEJŚCIOWA: <NN_XXXX>/ z wykazem + dokumentacja/
│                                (DWG/DXF/TIF od klienta; format: zlecenia/README.md; poza gitem)
└── wyniki/                    ← wyjścia per zlecenie (wyniki/<NN_XXXX>/, finalne _DXF_gotowe/)
```

## Pipeline produkcyjny (przepływ codzienny)

```
ZLECENIE — dokumentacja od klienta: pliki DWG/TIFF + wykaz.xlsx (pierwsza zakładka)
   ↓
KONWERSJA DWG→DXF   GstarCAD wsadowo; UNC nie działa → %TEMP%; błąd bywa przejściowy → RETRY;
                    ALBO ręczna konwersja wsadowa przez operatora (łatwa w GstarCAD grupowo) —
                    pipeline przyjmuje gotowe _conv.dxf; pominięcia logować GŁOŚNO;
                    ostateczność = odtworzenie z TIF (kolor czerwony, do sprawdzenia)
   ↓
TYPOWANIE           określenie typu rysunku z bazy typów (config/typy.yaml + zasady/przyklady/);
                    rysunek może mieć WIĘCEJ NIŻ JEDEN typ; typ → profil ustawień pipeline'u.
                    Baza typów rośnie przez system nauki.
   ↓
SZUKANIE POZYCJI    kategorie-wtyczki (każda zwraca kandydatów z pewnością i metrykami):
                    1. po strukturze rysunku (warstwa 1NN, kolor SBM, bloki INSERT)
                    2. po wymiarach z wykazu (bbox 1:1, bbox ze skalą, obwód płaszcza)
                    3. po cechach geometrii (czysty kontur, otwarte końce, filtr śmieci)
                    4. po adnotacjach tekstowych (gespiegelt, nr pozycji w dymku, tabele wariantowe)
                    5. z bazy / korpusu (elementy1.xlsx, sygnatura geometryczna, profil klienta)
                    6. pomoc człowieka (wybór z kandydatów na PNG, zaznaczenie ramki)
   ↓
WARIANTY            dla znalezionego widoku 2–3 NIEZALEŻNE silniki ekstrakcji (W-A/W-B/W-C
                    wg config/warianty.yaml) → kilka wersji pliku
   ↓
KONTROLA            bramki 1–10 na KAŻDYM wariancie (patrz niżej)
   ↓
OCENA WARIANTÓW     scoring + zgodność geometryczna między wariantami:
                    zgodne ≥2 niezależne metody = wysoka pewność · rozbieżność = do człowieka
   ↓
KATEGORIA TRUDNOŚCI 🟢 łatwy (auto→laser) · 🟡 średni · 🟠 trudny (przegląd) · 🔴 człowiek rysuje
   ↓
WYJŚCIE             DXF 1:1 wyśrodkowany (nazwa produkcyjna z kolumny NAZWA wykazu roboczego)
                    + PNG czarne tło (różnice/wątpliwości zakreślone NA CZERWONO)
                    + raport kontroli (co sprawdzono, liczby, decyzja, POWÓD statusu)
                    + zapis statusów w wykazie (status kolorem, uwagi, plik_dxf, technologia,
                      wymiar_dxf_x/y, skala, uwagi_wymiar=ok gdy X,Y ±1 vs Abmess)
   ↓
SPRAWDZANIE AI      nakładka wynik-na-źródło + ocena wizualna 100% flag (może tylko obniżyć status)
   ↓
SWEEP KOMPLETNOŚCI  domknięcie zlecenia: region+warstwa vs dostarczone dla WSZYSTKICH pozycji
                    i trybów (kolor 2/4/7/warstwa); flagi delta≥1 → oględziny 100% (zasada 6-7)
                    [delta≥1 od bramki 5/polygonize: szum zbity u źródła, 0 fałszywych na
                    wzorcach → niższy próg tylko dodaje oględzin; dawne ≥2 = tolerancja szumu
                    cyklomatyki. Prawda z trybów CZYSTYCH n_outer==1, 'all' tylko diagnostyka]
   ↓
SPRAWDZANIE CZŁOWIEK galeria: 🟡/🟠/🔴 obowiązkowo + próbka 🟢; werdykty → etykiety
   ↓
NAUKA               etykiety + korpus → wnioski → propozycje zasad → testy → produkcja (pętla)
```

## Wielowariantowość — kilka wersji pliku i ich ocena

- Każda pozycja może być wygenerowana przez **2–3 niezależne silniki** (jeśli typ na to
  pozwala — `config/warianty.yaml`): `wyniki/<zlecenie>/warianty/{Zeinr}_p{N}__wA.dxf`, `__wB`, `__wC`.
- Wszystkie warianty przechodzą przez **te same bramki kontroli**; wynik w `ocena.csv`
  (wariant × bramki × metryki × score).
- **Zgodność wariantów** (sygnatura geometryczna: liczba encji, kontury, otwory, wymiary
  z tolerancją) to bramka 10: zgodne ≥2 niezależne metody = wysoka pewność (🟢 możliwe);
  rozbieżność = automatyczna eskalacja do przeglądu (nigdy cichy wybór).
- Zwycięski wariant kopiowany pod nazwę produkcyjną (kolumna `NAZWA`); przegrane warianty
  ZOSTAJĄ w `warianty/` — to materiał dla systemu nauki (porównania, etykiety).
- Zasada z tablicy: *„jeżeli jest możliwość zrobienia na 3 sposoby — robimy 3 sposoby
  i oceniamy"*. Koszt CPU jest tani; błędny DXF na laserze drogi.

## Bramki kontroli (deterministyczne, skrypt — `produkcja/kontrola/`)

| # | Bramka | Co sprawdza |
|---|---|---|
| 1 | Wymiar (dwustopniowa) | zgrubna ≤3% przed zapisem + ścisła max(1 mm, 0.2%) z realnych extents PO zapisie; nieudany zapis KASUJE plik |
| 2 | Kontur domknięty | 0 otwartych końców (laser wymaga zamkniętych) |
| 3 | Filtr śmieci | statystyka encji (liczba, śr. długość LINE, % łuków) — wycina fałszywe trafiki o pasującym bbox |
| 4 | Bilans otworów okrągłych | liczba okręgów wynik vs źródło (po dedupie współśrodkowych) — nie może zniknąć; liczone W KLASTRZE części, nie w prostokątnym bbox |
| 5 | **Bilans konturów wewnętrznych** *(nowa)* | shapely.polygonize (bez off-by-one sklejania 0,1 mm na lustrach): liczba zamkniętych konturów WEWNĘTRZNYCH (fasole, sloty, kwadraty, wyspy) wynik vs widok źródłowy; W KLASTRZE części (bbox łapie sąsiadów → fałszywe flagi); bliźniaki P/L i duplikaty MUSZĄ mieć identyczną liczbę cech |
| 6 | Izometria | odrzuca rzut 3D o pasującym bbox (rozkład długości linii) |
| 7 | Gięcie | źródło ma linie gięcia (kolor 6 magenta) → wynik ma je odwzorować (warstwa GIECIE) |
| 8 | Rejestr widoków | żaden widok użyty 2× — lustro nie ukradnie widoku bliźniaka |
| 9 | Sanity 1:1 | wynik wyśrodkowany (środek bbox w (0,0)), niezerowy |
| 10 | **Zgodność wariantów** *(nowa)* | sygnatury niezależnych silników zgodne / rozbieżne → eskalacja |

Dodatkowo **nakładka wynik-na-źródło** (flager kompletności — najpewniejsza metoda,
~zero fałszywych trafień; wejście dla sprawdzania AI). Semafor: 🟢 wszystko OK ·
🟡 niepewne (każde z jawnym powodem) · 🔴 bramka twarda (wymiar/rejestr/bilanse) =
NIE zapisujemy jako OK. Żaden wariant nie omija QC.

### KONTROLA DETALU GOTOWEGO — TRZY kontrole (OBOWIĄZKOWO, nie do pominięcia)

> **Powód (2026-07-04/05, zlecenie 38_1847):** (a) silnik dał SL10582608 poz. 1/2 status
> ZIELONY/ŻÓŁTY, wymiar zgadzał się co do mm — a na środku blachy ZGUBIŁ duży owal.
> Zieleń silnika ≠ kompletność (pułapka 54_4867 i test2/SL40061302). (b) Wiele detali
> serii SL4 wyszło z KONTUREM OTWARTYM (SL40852200, SL40034116…) — otwarty kontur = NIE
> na laser, nawet gdy otwory się zgadzają. **Wymiar OK nie zwalnia z kontroli konturów.**

Każdy detal (także 🟢 z silnika) MUSI przejść **wszystkie trzy** kontrole, zanim status
może być 🟢. Kolejność: liczbowa → wizualna → **ZAWSZE na końcu zamknięte kontury**:

1. **LICZBOWA — bilans konturów/otworów region vs wynik** (bramka 4+5): kontury wewnętrzne
   + okręgi **PO DEDUPIE współśrodkowych** w REGIONIE źródłowym (bbox widoku / klaster,
   cała geometria oprócz gięcia kol.6 i osi) vs w WYNIKU. delta ≥1 konturu **lub** ≥1
   okrąg = FLAGA. Bramka 5 = `produkcja/kontrola/bilans_konturow.py` (shapely.polygonize)
   — zbiła szum u źródła (odporna na lustro/jitter; 0 fałszywych flag na wzorcach golden),
   więc próg spadł z ≥2 (tolerancja szumu) do ≥1. HISTORYCZNIE licznik cyklomatyczny
   ZAWYŻAŁ na kołnierzu/gięciu i źródłach z wymiarami (138/446) — polygonize to naprawił;
   sweep bierze prawdę z trybów CZYSTYCH (n_outer==1), 'all' tylko diagnostyka.
2. **WIZUALNA — porównanie obrazów** (niezależna od liczb — łapie to, co licznik przeoczy,
   i odsiewa fałszywe flagi): render `region-źródło vs wynik` na CZARNYM tle → OCZY
   porównują cecha-po-cesze. Brak cechy = 🔴, nawet gdy licznik nie flagował.
3. **ZAMKNIĘTE KONTURY — na KOŃCU, ZAWSZE, dla KAŻDEGO detalu gotowego** (twarda bramka 2,
   laserowa): liczba wierzchołków nieparzystego stopnia = 0 (kontur domknięty). **>0
   otwartych końców = 🔴, NIE na laser** — niezależnie od tego, że otwory/wymiar się
   zgadzają. Ręczna naprawa region+warstwa domyka proste detale, ale ZOSTAWIA otwarty
   kontur na złożonych z kołnierzem → wtedy 🔴 DO_SPRAWDZENIA (człowiek rysuje).

Zasady wiążące: (a) **żaden detal nie jest 🟢 bez WSZYSTKICH trzech**; (b) flagę zamyka OKO,
nie rozumowanie o wielkości różnicy (zasada 6); (c) największe różnice oglądać pierwsze;
(d) status z kontroli można tylko OBNIŻYĆ (zasada 5). Narzędzia (robocze, sprawdzone
bojowo na 38_1847, do awansu przez testy do `produkcja/kontrola/`):
`wyniki/38_1847/kontrola_kompletnosci.py` (liczbowa), `render_region.py` (wizualna),
`triage_gr.py` (liczbowa + zamknięte kontury zbiorczo dla grupy); docelowo `sweep.py` (etap 2).

**Bramka vs flager**: bramka = sygnał czysty (twarda decyzja automatu); flager = sygnał
z szumem (licznik konturów) — wskazuje GDZIE patrzeć, decyzję podejmują oczy (AI/człowiek),
100% flag, nigdy po wielkości różnicy (zasada 6). Szum flagera zwalczać u źródła
(klaster zamiast bbox, polygonize zamiast sklejania 0,1 mm) — bo fałszywe flagi uczą
ignorowania flag.

## Sprawdzanie przez AI (`sprawdzanie/ai/`)

1. Wejście: para PNG (wynik + widok źródłowy z ramką „skąd wycięto") + nakładka.
2. AI ogląda i **zakreśla na czerwono** podejrzaną/brakującą geometrię na PNG
   (brak otworu, przesunięcie, obca geometria) + werdykt `OK / WĄTPLIWOŚĆ` z powodem.
3. Werdykt AI zapisywany do raportu i `nauka/etykiety/` (etykieta źródło=AI).
4. **AI nie zastępuje bramek skryptowych** — może status tylko obniżyć (🟢→🟡), nigdy
   podnieść; rozstrzyga zawsze skrypt albo człowiek.

**Procedura obsługi flagi kompletności** (wprost z błędu na 54_4867):
- Każda flaga → render `region-źródło vs wynik` → AI OGLĄDA obrazy (nigdy nie
  rozstrzyga rozumowaniem o wielkości/przyczynie różnicy!).
- Brak potwierdzony → naprawa (silnik W-C region+warstwa) → ponowna pełna kontrola
  bramek → nowy przypadek do `testy/golden/`.
- Flaga uznana za false-positive → wymaga DOWODU (para PNG w raporcie) i wpada do
  galerii przeglądu człowieka jako pozycja do potwierdzenia.
- Kolejność oględzin: od NAJWIĘKSZYCH różnic (najgroźniejsze braki), nie od najmniejszych.

**KARTA KONTROLNA — werdykt AI dopiero po wypełnieniu wszystkich pól LICZBAMI**
(wpadka z 2026-07-04: AI znalazło duble okręgów i przestało patrzeć — brak fasoli
wskazał człowiek; szczegóły: `kontekst/wiedza/kontrola-karta-kontrolna-jeden-blad.md`):
1. Kontury wewnętrzne źródło-region vs wynik — **PO DEDUPIE okręgów współśrodkowych**
   (duble MASKUJĄ braki: surowo 5 vs 4 wygląda dobrze, po dedupie 3 vs 4 = brak!).
2. Okręgi: raw → po dedupie (ile grup współśrodkowych).
3. Gięcia: encje koloru 6 w źródle vs encje na warstwie GIECIE w wyniku.
4. `qc_powody` z raportu PRZECZYTANE (bramka 6 flagowała zgubione gięcie — powód
   nie jest dekoracją).
5. Oględziny renderu wynik-vs-źródło — dopiero PO liczbach.
**Jeden znaleziony błąd NIE kończy karty.** Zakaz „prawdopodobnie" w werdykcie:
albo liczby+render, albo `DO_SPRAWDZENIA`. Przed sesją sprawdzania: kalibracja oczu
na 1–2 znanych parach z golden (AI musi wskazać brak; nie wskaże → STOP sesji).

## Sprawdzanie przez człowieka (`sprawdzanie/czlowiek/`)

1. **Galeria kafelków**: wynik obok źródła + ramka skąd wycięto + semafor + powód +
   czerwone zakreślenia AI. Człowiek porównuje obrazki — nie otwiera CAD.
2. Zakres przeglądu: 🟡/🟠/🔴 obowiązkowo; 🟢 próbkowane (np. co 10.), odsetek próbki
   maleje wraz ze wzrostem zaufania (metryka niżej).
3. Werdykt jednym kliknięciem/wpisem: `OK` / `BŁĄD` + kategoria (brak otworu, zgubiony
   otwór nieokrągły, zła skala, zły wymiar, kontur otwarty, złe lustro, obca geometria,
   inne) + opcjonalne zakreślenie na czerwono.
4. Werdykty → `nauka/etykiety/` (etykieta źródło=człowiek). Każdy BŁĄD → obowiązkowo
   przypadek do `testy/golden/` (zasada żelazna 11).
5. Pozycje 🔴 „człowiek rysuje" → rysowane ręcznie; gotowy plik trafia do golden
   jako wzorzec (przyszły trening).

## System testowy (`testy/`) — jedyna brama do produkcji

- **Golden set**: pary (rysunek+wykaz → zweryfikowany DXF). Każdy typ rysunku i każdy
  historyczny błąd ma swój przypadek.
- `regresja.py` — pełny pipeline na golden, porównanie GEOMETRYCZNE (kontury, otwory,
  wymiary, pola), nie wizualne. PASS = warunek oddania zmiany.
- `znane_bledy.py` — cele silnika jako XFAIL (nie psują PASS); [XPASS] = naprawione →
  awans do regresji.
- `benchmark.py` — V3 vs V2 vs V1 na tych samych wejściach: statusy, wymiary, otwory,
  zgodność encja-po-encji. **Merge do produkcji tylko przy 0 regresji.**
- Testy jedną komendą, szybkie — inaczej nikt ich nie odpali.

## System tworzenia zasad (`zasady/`)

- Każdy **typ rysunku** ma: przykłady referencyjne (`przyklady/<typ>/`) + plik reguł
  (`reguly/<typ>.yaml|md`): co jest konturem, wymiarem, linią gięcia; jakie warstwy/kolory
  co znaczą; które silniki wariantów uruchamiać; progi bramek.
- Nowe zasady i sposoby (W-D, W-E…) powstają jako **propozycje** (`propozycje/`) —
  NIE działają w produkcji. Propozycja zawiera: opis problemu, przykładowe rysunki,
  oczekiwany wynik.
- Ścieżka awansu: propozycja → golden set + regresja + benchmark → wynik lepszy/równy
  i 0 nowych błędów → potwierdzenie człowieka → merge do `reguly/` i produkcji.
- Reguły czytelne dla człowieka (audyt bez czytania kodu).

## System nauki (`nauka/`) — zamyka pętlę

- **Korpus**: `--korpus` → logger dopisuje 1 wiersz na ZDARZENIE UCZĄCE do
  `korpus/decyzje.csv` (pozycja niepewna, bramka 🟡/🔴, brak widoku, lustro, rozbieżność
  wariantów, werdykt przeglądu). Deterministycznie, zero LLM — surowy ślad, nie reguła.
- **Etykiety**: werdykty człowieka i AI z przeglądów + wyniki porównań wariantów.
- **Szkolenia** (MANUAL UPGRADER): ręcznie wrzucone zlecenie/wykaz z kolumnami
  `SZKOLENIE`+`OPIS` → materiał do destylacji.
- **Destylacja** (`nauka/destylacja.py`): agregacja korpus+etykiety → szkic wniosków
  (co zadziałało, co zawiodło, dlaczego; propozycje) → **człowiek akceptuje** →
  `kontekst/wiedza/<name>.md` + linia w `kontekst/wiedza/MEMORY.md` + nowy przypadek
  golden + ewentualna propozycja reguły/typu. Jeden magazyn wiedzy dla całego systemu.
- **Porównanie ze starymi**: nowe wersje silników na historycznych zleceniach vs to,
  co poszło na laser — poprawa/pogorszenie liczbowo (wejście do benchmarku).
- **Baza typów rośnie przez naukę**: nowy wzorzec rysunku zaobserwowany w zleceniach →
  propozycja typu (przykłady + reguły) → testy → `config/typy.yaml`.
- Wnioski NIE zmieniają produkcji bezpośrednio — zawsze przez zasady → testy → merge.

### Metryka zaufania (główna miara sukcesu)

Odsetek pozycji wymagających przeglądu człowieka oraz czas sprawdzania na pozycję
**mają z czasem spadać** — raportowane per zlecenie w `testy/raporty/`. System jest
dobry wtedy, gdy człowiek sprawdza mało i szybko, a błędy na laser = zero.

## Zarządzanie skillami i aplikacjami (`zarzadzanie/`)

- `rejestr.yaml` — JEDEN rejestr wszystkich narzędzi. Wpis: nazwa, typ (skill/aplikacja),
  wersja, status (działa/plan/archiwum), wejście→wyjście, komenda testu, gdzie
  zainstalowane, data ostatniego audytu.
- `audyt.py` — porównuje rejestr z rzeczywistością: skill zainstalowany w `~/.claude/skills`
  i SecondBrain? test przechodzi? wersja zgodna? → raport rozjazdów.
- Źródła skilli w `skills/` w repo (jedno źródło prawdy); deploy = kopia do
  `~/.claude/skills` + `\\Qnap-energo\baza\.data\SecondBrain\03_Zasoby\Skille`.
- Każda zmiana = podbicie wersji + wpis w rejestrze (zasada żelazna 13).

### Skille V3 (docelowe)

| Skill | Rola | Status |
|---|---|---|
| `/wyciagnij-dxf` | produkcja: pełny pipeline na zleceniu (recall wiedzy → ekstrakcja → raport) | działa (V1/V2) → do podmiany na orkiestrator V3 |
| `/dxf-testy` | regresja + znane błędy + benchmark jedną komendą, raport | plan |
| `/dxf-sprawdz` | sprawdzanie AI folderu wyników (nakładki, czerwone zakreślenia, werdykty) | plan |
| `/dxf-przeglad` | sesja przeglądu człowieka (galeria → werdykty → etykiety → golden) | plan |
| `/dxf-zasada` | obserwacja/przypadek → propozycja reguły w poprawnym formacie | plan |
| `/dxf-nauka` | destylacja korpus+etykiety → wnioski → (za akceptacją) wiedza | plan |
| `/dxf-audyt` | audyt rejestru skilli i aplikacji | plan |

Skille używają skryptów z tego repo — logika w Pythonie, skill = procedura + recall
wiedzy (`nauka/wiedza/` + `kontekst/`) przed działaniem.

## Wiedza dziedzinowa — NIE UCZ SIĘ TEGO OD NOWA

Pełna wiedza: `kontekst/CLAUDE_v1.md` + notatki `kontekst/wiedza/*.md` (indeks: `MEMORY.md`). Pigułka:

- Pliki `.dxf` od klienta bywają **DWG w przebraniu** (nagłówek `AC1021`) — wykrywać po
  nagłówku. Konwersja GstarCAD wsadowo; **UNC nie działa** → kopiować do `%TEMP%`;
  błędy przejściowe → retry.
- **Rysunki blokowe (INSERT-only)**: rozbić `virtual_entities()` PRZED czymkolwiek.
- **Zera wiodące**: wykaz `55648` vs plik `055648.dxf` — mapować po końcówce.
- **Linia gięcia = kolor 6 (magenta)** niezależnie od linetype (DASHDOT/PHANTOM/MITTE);
  odróżniać od krzyża osi otworu po długości. Obecność gięcia ⇒ widok jest rozwinięciem.
- **Lustra P/L**: adnotacja `gespiegelt/mirrored` lub kolumna `INDEX`; linie gięcia MUSZĄ
  zostać odbite razem z konturem. Linie gięcia nanosić TYLKO gdy P/L albo gięcie pod skosem (>5°).
- **Otwory współśrodkowe/zdublowane** (Ø13+Ø14.7): zostaw najmniejszy, resztę skasuj.
- **Gwint = okrąg + współśrodkowy ŁUK** większego Ø (~270°) + `DIMENSION` z tekstem
  „M 10" (nie MTEXT!): zostaw OBA (nie dedup jak okrąg+okrąg), opisz w wykazie `M10`+gwint,
  średnica wiercenia wg tabeli (M10→8.5). **Łuk gwintu ~270° to NIE otwarty kontur** —
  bramka 2 nie może go flagować jako NIEDOMKNIĘTE (`kontekst/wiedza/gwint-okrag-luk-dimension.md`).
- **Geometria pozycji bywa na RÓŻNYCH kolorach/warstwach** (kolor 2/4/7, warstwa 53/107) —
  auto-wykrycie warstwy geometrii (najczęstsza linia w bbox widoku), nigdy nie zakładać koloru 7.
- **Bliźniaki bywają asymetryczne** (p1 z owalem Ø225, p2 bez — dwie różne części o tym
  samym obrysie, NIE lustro) — weryfikować ze źródłem, asymetria = 🟡 do potwierdzenia.
- **Otwarte pliki blokują zapis** (DXF w podglądzie, wykaz w Excelu → WinError 32) —
  pozycja bywa po cichu niezaktualizowana; pominięcia logować głośno, zamykać przed passem.
- Konwencje klientów (Lantek 1NN, SBM kolorowa, niemiecka blokowa, łamana) — tabela w CLAUDEv1.
- Wykaz: pierwsza zakładka, `ZAKUPY=blacha` bez `propozycji`, wymiary niemieckie
  (`parse_dim`), duble = pierwszy wpis. **`NAZWA`/`ZAKUPY` bywają FORMUŁAMI** —
  `openpyxl.save` kasuje cache formuł → wartości czytać przez Excel COM (`keep_vba=True`).
- Render PNG wyłącznie skryptem z czarnym tłem (`facecolor="black"`).

## Środowisko

- Windows 11, Python 3.13 (`ezdxf`, `openpyxl`, `matplotlib`, `shapely` — requirements.txt).
- GstarCAD 2022 (`C:\Program Files\Gstarsoft\GstarCAD2022\`) — tylko konwersja DWG.
- Dane produkcyjne: `\\QNAP-ENERGO\` (UNC) — do konwersji CAD kopiować lokalnie.
- Skille: `~/.claude/skills` + `\\Qnap-energo\baza\.data\SecondBrain\03_Zasoby\Skille`.

## Instrukcje dla Claude w tym projekcie

- Odpowiadaj po polsku. Wymiary w milimetrach, przecinek dziesiętny w adnotacjach CAD.
- Zmiany w `produkcja/` — tylko po PASS regresji i benchmarku. Nigdy „przy okazji".
- Nowe pomysły → zawsze najpierw `zasady/propozycje/`; nowy trudny przypadek →
  najpierw `testy/golden/`.
- Kontrola geometrii zawsze skryptem; AI ocenia dodatkowo i może tylko obniżyć status.
- Przed ekstrakcją: recall wiedzy (`kontekst/wiedza/MEMORY.md` + `kontekst/`) pasującej
  do klienta/prefiksu rysunku — i STOSUJ reguły.
- Niepewność ⇒ `_DO_SPRAWDZENIA`, nigdy zgadywanie.
