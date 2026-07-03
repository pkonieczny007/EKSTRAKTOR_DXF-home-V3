# SZKIC SKILLA: wyciagnij-dxf (ekstrakcja pozycji blaszanych z rysunkow warsztatowych)

> Status: szkic po testach na 2 rysunkach (SL10478356_1, SL10524825_1).
> Wynik testow: 17/18 pozycji automatycznie (w tym 1 w trybie bez warstw),
> 1 polautomatycznie (lustro - plik wygenerowany, do zatwierdzenia).

---

## Po co

Zastapic reczny cykl: otworz rysunek w CAD -> znajdz pozycje -> WBLOCK ->
usun wymiary/osie -> przeskaluj -> zapisz pod nazwa -> sprawdz wymiary skanerem.
Wyjscie trafia do Lantek Expert (nesting + laser), wiec kontury MUSZA byc
zamkniete i NIE WOLNO zgubic otworow.

## Wywolanie (docelowo)

```
/wyciagnij-dxf <folder_lub_plik_rysunku> [--wykaz <sciezka.xlsx>]
```

Skill znajduje wykaz sam (najnowszy *.xlsx z "lista materialowa" w folderze
zlecenia), przetwarza wszystkie rysunki i konczy raportem HTML/CSV + PNG.

---

## Pipeline (sprawdzony w testach)

### Krok 1: DWG -> DXF (convert_dwg.py)
- Pliki "rysunki" bywaja DWG ze zmienionym rozszerzeniem na .dxf
  (naglowek binarny `AC1021`). Wykrywamy po naglowku, nie po rozszerzeniu.
- Konwersja: **GstarCAD wsadowo** `gcad.exe plik.dwg /b skrypt.scr`,
  skrypt: `_FILEDIA 0` / `_SAVEAS _DXF 16 "out.dxf"` / `_QUIT _N`.
  Dziala bez interakcji (okno mignie). UNC nie dziala - kopiowac do %TEMP%.
- (dwxconv.exe z GstarCAD nie przyjmuje argumentow CLI - slepa uliczka.)

### Krok 2: wykaz.xlsx
- Pierwsza zakladka. Kolumny: `Zeinr` (nr rysunku), `Posn` (pozycja),
  `ZAKUPY == "BLACHA"` (filtr), `Abmess_1` x `Abmes_2` (wymiary docelowe).
- Wymiary bywaja stringami w formacie niemieckim: `"      2.232,000"`.
- Lista bywa zdublowana (domowienie) - brac pierwszy wpis pozycji.

### Krok 3: ekstrakcja pozycji (extract_positions.py)
Konwencja rysunkow: **warstwa "1NN" = pozycja NN** (101 -> poz. 1).
Dla kazdej warstwy pozycyjnej:

1. **Filtr typow**: zostaw LINE/ARC/CIRCLE/ELLIPSE/SPLINE/POLYLINE;
   wytnij DIMENSION/MTEXT/TEXT/LEADER/POINT/HATCH/INSERT.
2. **Filtr rodzaju linii**: wytnij osie (CENTER/PHANTOM/DASHDOT);
   DASHED/HIDDEN zostaw, ale raportuj (moze byc linia giecia).
3. **Klastrowanie przestrzenne** (union-find po bbox, odstep 8 mm na
   papierze) -> kazdy klaster = jeden widok na rysunku.
4. **Dopasowanie do wykazu**: klaster pasuje, gdy skala dlugosc/szerokosc
   jest ta sama (tolerancja 3%). Ranking kandydatow:
   a) skala "ladna" (1/2/2.5/4/5/8/10/20),
   b) **najmniej otwartych koncow konturu** - to odroznia samodzielny
      widok detalu od tego samego detalu w zlozeniu (krawedzie poprzerywane
      sasiadami, okregi pofragmentowane na luki) i jest warunkiem lasera,
   c) najwiecej geometrii po wchlonieciu wnetrza,
   d) najmniejszy blad proporcji.
5. **KRYTYCZNE - otwory**: po wyborze widoku glownego wchlon WSZYSTKIE
   klastry lezace w calosci wewnatrz jego bbox. Otwor w srodku duzej
   blachy (np. fasolka) jest dalej od konturu niz prog klastrowania
   i bez tego kroku ZNIKA. (Wykryte na poz. 1 SL10478356 - 2 fasolki.)
6. **Transformacja**: skala do 1:1, **ZAWSZE WYSRODKOWANIE** - srodek bbox
   elementu w (0,0), NIE lewy-dolny rog (wymog operatora 11.06.2026:
   wycentrowane elementy latwiej sie przeglada w CAD - zoom extents
   i obrot dzialaja wokol srodka detalu). Dotyczy tez luster.
   `$EXTMIN/$EXTMAX` przeliczone z geometrii (lekcja z fix_extents.py -
   WBLOCK/konwersje zostawiaja smieci w naglowku).
7. **Zapis**: `{Zeinr}_p{N}.dxf` + PNG podglad.

### Krok 3b: TRYB BEZ WARSTW (fallback - rysunki z jedna warstwa)
Warstwy sa tylko PIERWSZYM filtrem. Gdy pozycja nie ma warstwy 1NN albo
ekstrakcja warstwowa zawiodla, dziala tryb layer-agnostic:
- klastrowanie CALEGO rysunku (wszystkie warstwy naraz) z malejacymi
  progami odstepu **8 -> 4 -> 2 mm** (widoki bywaja narysowane blisko
  siebie i przy 8 mm sie sklejaja - tak bylo z poz. 4 SL10524825),
- kandydaci pasujacy do wymiarow z wykazu, ranking jak w trybie warstwowym,
- **rejestr zajetych widokow**: bbox widoku przypisanego juz innej pozycji
  nie moze byc uzyty drugi raz (inaczej poz. lustrzana o identycznych
  wymiarach ukradlaby widok blizniaka i wyszla NIEzlustrowana!).
Zweryfikowane: poz. 4 SL10524825 (kontur rozrzucony po warstwach 1+103,
rozwiniecie 8 mm od widoku krawedziowego) -> 238.85x150 vs wykaz 239x150.

### Krok 3d: RYSUNKI 1-WARSTWOWE - separacja po KOLORZE (test OPUS, SL10582053)
Niektorzy klienci (np. SBM) rysuja wszystko na jednej warstwie "1":
pojedyncza czesc + ramka A3 + wymiary, skala 1:2. Warstwa nic nie segreguje,
a klastrowanie przestrzenne sklejalo kontur z liniami wymiarowymi (proporcja
psula sie -> NIE ZNALEZIONO). Rozwiazanie: w trybie bez warstw probujemy tez
klastrowac PER KOLOR. Konwencja kolorow tu: kontur=2 (zolty), wymiary=3
(zielony), linia giecia=6 (magenta). Sam kolor konturu daje domkniety obrys
(open_ends=0), ktory ranking premiuje ponad zanieczyszczone klastry.
WAZNE: przy wyborze per-kolor wchlaniamy do wnetrza tylko OTWORY
(CIRCLE/ELLIPSE), nie cala geometrie - inaczej wrocilyby linie wymiarowe.
Wynik: 200x72.05 vs wykaz 200x72, kontur zamkniety, 2 otwory podwojne
Ø18/Ø10 (pogłębienie + przelot) zachowane -> FLAGA: operator decyduje
ktory ciac laserem (typowy przypadek do weryfikacji).

### Krok 3c: linie giecia
Konwencja rysunkow: osie = linetype CENTER, **linia giecia = DASHDOT**.
Linie DASHDOT wewnatrz obrysu widoku glownego trafiaja do wyniku na
osobna warstwe `GIECIE` (kolor 6 magenta - zgodnie z konwencja
DXF_cleaner "linia_giecia_fiolet"). Obecnosc linii giecia oznacza,
ze widok jest ROZWINIECIEM - wymiar zgadza sie z wykazem (potwierdzil
operator). Lantek mapuje warstwe/kolor na trasowanie albo ja ignoruje.

### Krok 4: przypadki specjalne (wykryte w testach)
- **Lustro** ("Pos.003 gespiegelt / mirrored"): pozycja bez wlasnego widoku,
  ale o identycznych wymiarach w wykazie jak pozycja OK -> generuj odbicie
  `_LUSTRO_z_pN.dxf` ze statusem ZWERYFIKUJ. Opcjonalnie: szukaj w MTEXT
  slow `gespiegelt|mirrored` dla potwierdzenia.
- **Pozycja spoza wykazu** (warstwa 122 bez wpisu BLACHA): raport
  "BRAK W WYKAZIE", nic nie zapisujemy.
- **Nic nie pasuje** -> plik `_DO_SPRAWDZENIA` (nie trafi do nestingu)
  albo status NIE ZNALEZIONO. NIE zgadujemy konturu.

### Krok 5: weryfikacja (zamiast recznego skanera)
Raport CSV/HTML na koncu zawiera dla kazdej pozycji:
- wymiar DXF vs wymiar z wykazu (logika jak w update_SKANER_DXF),
- skale, liczbe otworow, liczbe linii kreskowanych (giecie?),
- status: OK / LUSTRO-ZWERYFIKUJ / DO_SPRAWDZENIA / BRAK.
Operator oglada TYLKO miniatury PNG i pozycje nie-OK. Czas weryfikacji
~minuta na rysunek zamiast rysowania od nowa.

---

## Struktura wyniku

```
wyniki/
  SL10478356_p1.dxf ... p14.dxf     <- gotowe na nesting (1:1, zamkniete kontury)
  SL10478356_p*.png                 <- podglady do szybkiej weryfikacji
  SL10478356_raport.csv             <- wymiary vs wykaz, statusy
  SL10524825_p3_LUSTRO_z_p2.dxf     <- polautomat: do zatwierdzenia
  SL10524825_p3_DO_SPRAWDZENIA.dxf  <- automat niepewny: do reki
```

## Czego skill NIE robi (swiadomie)
- Nie zgaduje rozwiniec gietych detali (ryzyko zlomu > oszczednosc czasu).
- Nie podmienia nazwy na nazwe z wykazu NAZWA/Bezeichnung - do ustalenia
  konwencja (mozna dodac w 1 linii, gdy operator potwierdzi schemat).
- Nie usuwa linii gietia (DASHED) z widoku glownego - Lantek/operator
  decyduje; jest flaga w raporcie.

## EWENTUALNOSCI na wypadek bledow automatu (pomysly operatora, 11.06.2026)

### A) Weryfikacja wizualna przez pliki TIF
Do kazdego rysunku zawsze istnieje plik TIF (zeskanowany/wyplotowany arkusz).
Pomysl: raport HTML pokazuje obok siebie:
  - render PNG wycietej pozycji (z naszego DXF),
  - wyciety fragment TIF-a z obszaru, z ktorego pochodzi widok
    (znamy bbox klastra na papierze -> przeliczenie na piksele TIF
    po dopasowaniu ramki arkusza).
Czlowiek poteguje roznice wzrokiem w ulamku sekundy. Mozna tez dodac
automatyczne porownanie (overlay/diff pikselowy) jako pre-filtr.
Zaleta: TIF to "prawda wydrukowana" - niezalezna od warstw i kolorow DXF.

### B) Tryb polautomatyczny: "zaznacz kwadraty -> czlowiek sprawdza -> wytnij"
Odwrocenie kolejnosci wzgledem pelnego automatu:
  1. Skrypt sam ZAZNACZA kandydatow: rysuje prostokaty (bbox) wokol
     wykrytych widokow na kopii rysunku (osobna warstwa/kolor)
     albo na podgladzie PNG/TIF - po jednym kwadracie na pozycje,
     z etykieta "poz. N, skala 1:X, wymiar -> AxB".
  2. Czlowiek przeglada JEDEN obrazek na rysunek i poprawia/zatwierdza
     (ew. przesuwa kwadrat na wlasciwy widok, np. w GstarCAD lub
     prostym podgladzie HTML z klikaniem).
  3. Skrypt wycina dokladnie z zatwierdzonych kwadratow (jak WBLOCK),
     dalej standardowo: czyszczenie, skala, raport.
Zastosowanie: rysunki lamiace konwencje warstw (jak poz. 4 SL10524825),
rysunki bez warstw numerycznych, stare rysunki.
To w praktyce most miedzy komenda EP z DXF_cleaner (czlowiek klika 2 punkty)
a pelnym automatem (zero klikania): czlowiek tylko ZATWIERDZA, nie szuka.

## Otwarte pytania przed wdrozeniem
1. Czy linie giecia maja zostac w DXF (kolor/warstwa specjalna), czy wyleciec?
2. Docelowa nazwa pliku: `{Zeinr}_p{N}` czy `NAZWA` z wykazu?
3. Co z pozycjami na stronach _2, _3 rysunku (multi-page)? Petla po plikach
   `{Zeinr}_*.dxf` i scalenie raportu per Zeinr.
4. Prog "ladnych" skal - czy dopuszczamy 1:2.5 i 1:8? (na razie tak)

## Pliki
- `wyniki/convert_dwg.py`        - DWG->DXF przez GstarCAD /b
- `wyniki/extract_positions.py`  - ekstrakcja + raport (serce skilla)
- `wyniki/_dev/`                 - skrypty analityczne z sesji testowej
