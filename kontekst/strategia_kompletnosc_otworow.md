# Strategia: jak unikać ZGUBIONYCH CECH (otworów / slotów-"fasol") w ekstrakcji

## Problem (przykład: SL10596945_p3P)
Silnik klastruje widok po sąsiedztwie (union-find po bbox z odstępem). Cecha
**odseparowana** od głównego konturu — slot podłużny ("fasola"), otwór wewnętrzny,
wycięcie — trafia do osobnego klastra albo zostaje odfiltrowana w `partition()`
i **wypada z wyniku**. Rozwinięcie 282×260 miało 2 fasole 14×30, w DXF była 1.

## Dlaczego kontrola WYMIARU tego nie łapie
Brak cechy WEWNĘTRZNEJ nie zmienia bbox → X-DXF/Y-DXF się zgadzają → `uwagi_wymiar=ok`.
**Kontrola wymiaru ≠ kontrola kompletności.** Potrzebna osobna bramka.

## Strategia — warstwy obrony (od najpewniejszej)

### 1. NAKŁADKA wynik-na-źródło w galerii  ← najpewniejsze, wzrokowe, zero fałszywych trafień
Zamiast samej ramki "skąd wycięto", rysuj wyekstrahowany kontur (czerwony/półprzezroczysty)
NA źródłowym widoku, w tej samej skali i pozycji. Operator w 1 s widzi, że fasola
jest w źródle a nie ma jej w nałożonym wyniku. **Jedyna metoda odporna na WSZYSTKIE
typy braków** (sloty prostokątne, splajny, wycięcia, otwory). Wdrożyć w `galeria.py`.

### 2. Licznik OTWORÓW źródło↔wynik  ← automat, czysty sygnał
Policz `CIRCLE` (bez warstwy wymiarów '1', bez osi kolor 4) w klastrze części
źródła vs w wyniku. Różnica → ŻÓŁTY "sprawdź otwory (źródło N / wynik M)".
Okręgi są jednoznaczne — mało szumu. Łapie zgubione okrągłe otwory.

### 3. Licznik ZAMKNIĘTYCH KONTURÓW WEWNĘTRZNYCH (otwory + fasole + wycięcia)  ← wdrożone: _licznik_konturow.py
Topologicznie: liczba pętli = liczba cyklomatyczna grafu krawędzi `E−V+C` + samozamknięte
(CIRCLE / zamknięta LWPOLYLINE / SPLINE). Wewnętrzne = pętle − 1 (kontur zewn.).
Łapie WSZYSTKO zamknięte, nie tylko okręgi (fasole, perforacje prostokątne, nietypowe).
Zweryfikowane: p3P=4 (2 otw.+2 fasole), SL10596953_p1=67 (4 otw.+63 perforacje), SL400521106=8 slotów.

Zastosowania:
- **Absolutny opis części** (ile cech ma detal) — wiarygodne.
- **Flager kandydatów** (region↔wynik, bliźniaki P/L, duplikaty) — patrz niżej.

DWA ŹRÓDŁA SZUMU (dlatego to FLAGER, nie automatyczna bramka — każda flaga = 2 s wzrokiem):
  a) region↔wynik: prostokątny bbox łapie „balony" pozycji (003/004) i sąsiednie cechy → PRZELICZA.
  b) bliźniaki P/L: tolerancja sklejania końców (0,1 mm) → po odbiciu długi slot bywa nie-domknięty
     → OFF-BY-ONE (p4P=3 vs p5L=4 przy IDENTYCZNEJ geometrii). Poprawa: shapely.polygonize
     albo większa tolerancja sklejania.
Mimo szumu: to najlepszy AUTOMATYCZNY sygnał — wyłapał realny brak 4 slotów w SL400521106.

### 4. P/L i duplikaty = IDENTYCZNA liczba cech
Lustra i kopie muszą mieć tyle samo otworów/slotów. Rozbieżność = flaga.
(Warstwa pomocnicza — nie łapie, gdy OBA bliźniaki zgubiły to samo.)

### 5. ROOT FIX w silniku: ekstrakcja po REGIONIE+WARSTWIE, nie po klastrze sąsiedztwa
Bierz WSZYSTKIE encje warstwy geometrii (kolor konturu, np. 51/53) w bbox widoku
— jak zrobiliśmy ręcznie przy wachlarzu SL10600635 — zamiast tylko spójnego klastra
union-find. Cechy odseparowane nie wypadają. **Usuwa przyczynę.** Do wdrożenia jako
tryb "region" w orkiestratorze, przełączany gdy #1/#2 wykryją brak.

### 6. Liczenie tylko w KLASTRZE części, nie w prostokątnym bbox
Skan bbox-owy ma FAŁSZYWE trafienia: prostokąt obejmuje sąsiednie widoki i perforację
liczoną podwójnie (flat + widok 3D). Dlatego liczniki #2/#3 rób na encjach faktycznie
przypisanych do klastra pozycji, nie na wszystkim co wpada w prostokąt.

### 7. Zamykaj pliki DXF w podglądzie przed passem
Otwarty plik → WinError 32 (blokada zapisu), pozycja zostaje niezaktualizowana
(np. SL10596945_p4L). Driver pomija i loguje — ale zamknij przed generowaniem.

## Wynik skanu bbox (54_4867) — ilustracja szumu i realnych trafień
REALNE (małe różnice, do sprawdzenia nakładką #1):
  SL10596945_p3  brak 2   = potwierdzona fasola (NAPRAWIONE)
  SL10585490_p3  brak 7   | SL10585490_p6 brak 2 | SL10599171_p1 brak 8 | SL400521106_p1 brak 8
FAŁSZYWE (duże różnice = bbox obejmuje 2 widoki / perforację):
  SL10596954_p1 "brak 128", SL40071953_p1 "brak 64", SL40051182_p1 "brak 22"

## Rekomendacja
Priorytet: **#1 (nakładka) + #2 (licznik otworów)** jako bramki QC w weryfikatorze V2.
Docelowo **#5 (tryb region)** w silniku jako auto-fallback, gdy #1/#2 wykryją brak.
#1 daje ~90% pewności przy zerowym ryzyku fałszywych trafień.
