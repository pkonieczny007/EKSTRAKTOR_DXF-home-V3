# CLAUDE.md — System DXF

Automatyczne tworzenie rysunków DXF detali do cięcia laserowego.

## Cel i zasady nadrzędne

1. **Zero błędnych DXF na produkcji.** Element wypalony błędnie = realny koszt materiału i czasu maszyny. W razie wątpliwości system ma ODRZUCIĆ detal do weryfikacji człowieka, nigdy nie zgadywać.
2. **Szybciej niż ręcznie.** Wygenerowanie + sprawdzenie detalu musi trwać krócej niż narysowanie go od zera. Jeśli weryfikacja trwa dłużej niż rysowanie — system nie spełnia celu.
3. **Deterministycznie, gdzie się da.** Geometria, liczenie konturów, otworów, skala, wymiary = skrypty (ezdxf). AI tylko tam, gdzie skrypt nie wystarcza (interpretacja rysunku referencyjnego, klasyfikacja typu, ocena wizualna).
4. **Modułowość.** Każdy system działa niezależnie. Zmiany w systemie nauki lub tworzenia zasad NIE mogą wpływać na działający system produkcyjny. Nowa zasada trafia do produkcji wyłącznie przez system testowy.

## Struktura projektu

```
dxf-system/
├── CLAUDE.md                  # ten plik — routing i zasady
├── produkcja/                 # SYSTEM PRODUKCYJNY (stabilny, wersjonowany)
│   ├── orkiestrator.py        # wybór sposobu, uruchamianie pipeline
│   ├── sposoby/
│   │   ├── v1/                # sposób V1 (istniejący)
│   │   ├── v2/                # sposób V2 (istniejący)
│   │   └── v3/                # miejsce na nowe sposoby
│   ├── analiza/               # kolor linii, warstwy, typ rysunku
│   ├── kontrola/              # bramki jakości (kontury, otwory, skala, wymiary)
│   └── output/                # gotowe DXF + raport kontroli
├── zasady/                    # SYSTEM TWORZENIA ZASAD
│   ├── reguly/                # zasady per typ rysunku (pliki .md / .yaml)
│   ├── przyklady/             # przykładowe rysunki definiujące typy
│   └── propozycje/            # nowe zasady CZEKAJĄCE na testy (nie działają w produkcji)
├── testy/                     # SYSTEM TESTOWY
│   ├── golden-set/            # pary: DXF wejściowy → poprawny DXF wyjściowy
│   ├── regresja.py            # uruchamia cały golden set, porównuje wyniki
│   └── raporty/               # wyniki testów per wersja zasad
├── nauka/                     # SYSTEM NAUKI
│   ├── etykiety/              # oznaczone wyniki (OK / błąd + typ błędu)
│   ├── porownania/            # nowe wyniki vs. stare wyniki
│   └── wnioski/               # analiza błędów → propozycje zasad
├── weryfikacja/               # interfejs przeglądu (Flask)
│   └── review/                # overlay wejście vs. wyjście, zakreślanie różnic
└── db/
    └── system.sqlite          # historia zleceń, wyniki kontroli, etykiety
```

## Systemy — opis

### 1. System produkcyjny (`produkcja/`)

**Rola:** jedyny system, który tworzy DXF trafiające na laser. Musi być dokładnie określony, zoptymalizowany i przewidywalny.

**Zasady działania:**
- Maksimum skryptów, minimum AI. Każdy krok AI musi mieć skryptową bramkę kontrolną za sobą.
- Pipeline: wejście → określenie typu → orkiestrator wybiera sposób (V1/V2/V3) → generowanie → **bramki kontroli** → decyzja.
- Bramki kontroli (wszystkie deterministyczne, ezdxf):
  - liczba konturów zamkniętych: wejście vs. wyjście (musi się zgadzać),
  - liczba otworów — **w tym nieokrągłych** (polilinie zamknięte, prostokąty, fasole, owale), nie tylko CIRCLE,
  - skala 1:1 i wymiary gabarytowe vs. rysunek referencyjny,
  - brak zdublowanych/otwartych konturów.
- Jeśli detal da się zrobić kilkoma sposobami → orkiestrator uruchamia wszystkie i porównuje wyniki. Zgodność wyników = wysoka pewność. Rozbieżność = automatyczne odrzucenie do weryfikacji.
- Każdy detal dostaje **kategorię trudności**: łatwy / średni / trudny / człowiek. Kategoria decyduje o głębokości kontroli i o tym, czy wynik idzie prosto na laser, czy do przeglądu.
- Wynik zawsze z raportem kontroli (co sprawdzono, jakie liczby, jaka decyzja).
- Wersjonowany w git. Zmiany TYLKO przez merge zasad, które przeszły system testowy.

### 2. System tworzenia zasad (`zasady/`)

**Rola:** definiuje JAK system ma pracować — reguły interpretacji rysunków, typy detali, nowe sposoby generowania.

**Zasady działania:**
- Każdy typ rysunku ma: przykłady referencyjne + plik reguł (co jest konturem, co wymiarem, co linią gięcia, jakie warstwy/kolory co oznaczają).
- Nowe zasady i nowe sposoby (V3, V4…) powstają tutaj jako **propozycje** — trafiają do `propozycje/` i NIE działają w produkcji.
- Propozycja zasady musi zawierać: opis problemu, który rozwiązuje, przykładowe rysunki, oczekiwany wynik.
- Ścieżka: propozycja → testy na golden set → jeśli wynik lepszy lub równy i zero nowych błędów → merge do `reguly/` i do produkcji.
- Zasady pisane tak, żeby były czytelne dla człowieka (md/yaml) — Paweł musi móc je audytować bez czytania kodu.

### 3. System testowy (`testy/`)

**Rola:** jedyna brama między propozycją a produkcją. Chroni przed regresją.

**Zasady działania:**
- **Golden set**: zestaw par (rysunek wejściowy → zweryfikowany poprawny DXF wyjściowy). Każdy typ detalu i każdy znany historyczny błąd ma swój przypadek testowy.
- Każdy błąd znaleziony w produkcji lub weryfikacji → OBOWIĄZKOWO dodawany do golden set jako nowy przypadek (błąd nie może się powtórzyć niezauważony).
- `regresja.py` uruchamia pełny pipeline na całym golden set i porównuje geometrycznie (nie wizualnie): kontury, otwory, wymiary, pola powierzchni.
- Raport: ile przypadków OK / ile regresji / ile poprawionych. Merge do produkcji dozwolony tylko przy zerze regresji.
- Testy muszą być szybkie do uruchomienia jedną komendą — inaczej nikt nie będzie ich odpalał.

### 4. System nauki (`nauka/`)

**Rola:** zamienia błędy i wyniki weryfikacji w lepsze zasady. Zamyka pętlę.

**Zasady działania:**
- **Etykietowanie:** każdy wynik weryfikacji (człowiek lub AI-overlay) dostaje etykietę: OK / błąd + kategoria błędu (brak otworu, zły otwór nieokrągły, zła skala, zły wymiar, brak konturu, inne). Etykiety w SQLite.
- **Porównanie ze starymi:** nowe wersje sposobów uruchamiane na historycznych zleceniach → porównanie wyników z tym, co wtedy poszło na laser. Poprawa/pogorszenie mierzalne liczbowo.
- **Analiza wzorców błędów:** okresowy przegląd etykiet → gdzie system myli się najczęściej, jakie typy rysunków są problematyczne → wnioski w `wnioski/`.
- Wnioski NIE zmieniają produkcji bezpośrednio. Generują propozycje zasad → system tworzenia zasad → system testowy → produkcja.
- Metody nauki (do rozwoju): few-shot z etykietowanych przykładów, skills per kategoria detalu, doprecyzowanie promptów VLM na bazie błędnych przypadków.

## Przepływ pracy

### Ścieżka produkcyjna (codzienna)

```
Rysunek DXF (zlecenie)
   ↓
Określenie typu (baza przykładów)
   ↓
Orkiestrator → wybór sposobu; jeśli możliwe kilka → uruchom wszystkie
   ↓
Generowanie konturu (V1 / V2 / V3)
   ↓
BRAMKI KONTROLI (skrypty): kontury zamknięte → otwory (też nieokrągłe!)
→ skala → wymiary → porównanie między sposobami
   ↓
Kategoria trudności + scoring
   ↓
┌─ wszystko zgodne, kategoria łatwa → GOTOWY DXF → laser
├─ drobne wątpliwości → weryfikacja wizualna (overlay, zakreślenie różnic)
└─ rozbieżność sposobów / kategoria "człowiek" → Paweł rysuje/poprawia ręcznie
```

### Pętla uczenia (ciągła, w tle)

```
Wyniki weryfikacji + błędy z produkcji
   ↓
Etykietowanie (system nauki)
   ↓
Analiza wzorców błędów → wnioski
   ↓
Propozycje nowych zasad / nowego sposobu (system tworzenia zasad)
   ↓
Golden set + regresja (system testowy) ← każdy znaleziony błąd dodaje nowy przypadek
   ↓
Zero regresji? → merge do systemu produkcyjnego
```

### Zasada zaufania

Celem pętli jest odbudowa zaufania do systemu: zamiast sprawdzać 100% wyników ręcznie, sprawdzamy tylko to, co bramki kontrolne i porównanie sposobów oznaczyły jako wątpliwe. Odsetek detali wymagających przeglądu człowieka ma z czasem spadać — i to jest główna metryka sukcesu systemu.

## Instrukcje dla Claude w tym projekcie

- Zmiany w `produkcja/` — tylko po przejściu testów regresji. Nigdy nie edytuj produkcji "przy okazji".
- Nowe pomysły → zawsze najpierw `zasady/propozycje/`.
- Po każdym znalezionym błędzie: najpierw dodaj przypadek do `testy/golden-set/`, dopiero potem naprawiaj.
- Kontrola geometrii zawsze skryptem (ezdxf), nigdy oceną AI. AI może dodatkowo oceniać wizualnie, ale nie zastępuje skryptu.
- Odpowiadaj po polsku. Wymiary: milimetry, przecinek dziesiętny w adnotacjach CAD.
