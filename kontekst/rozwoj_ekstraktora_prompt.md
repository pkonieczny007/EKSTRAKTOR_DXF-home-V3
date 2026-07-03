---
opis: Rozwija ekstraktor w orkiestrator doboru metod z weryfikacją 100% wyników
---

# Prompt: rozwój ekstraktora DXF — orkiestrator metod

> Prompt do wklejenia w nową sesję AI (Claude) pracującą nad projektem
> `C:\Python_CLaude\EKSTRAKTOR_DXF-home`. Zawiera opis aplikacji, kierunek
> rozwoju (z tablicy METODY) i konkretne zadanie.

---

## 1. Opis aplikacji (kontekst)

**EKSTRAKTOR_DXF** — narzędzie CLI (Python 3.13, ezdxf), które z rysunku
złożeniowego DWG/DXF + wykazu materiałowego (xlsx) automatycznie wycina
pojedyncze pozycje blaszane jako gotowe pliki DXF w skali 1:1, prosto do
Lantek Expert (nesting + cięcie laserem).

Pipeline dzisiaj:

1. `src/convert_dwg.py` — konwersja DWG→DXF (GstarCAD wsadowo; pliki `.dxf`
   od klientów bywają DWG w przebraniu — wykrywanie po nagłówku binarnym).
2. `src/extract_positions.py` — serce: klastrowanie geometrii w widoki,
   dopasowanie widoku do wymiarów z wykazu, ranking kandydatów (najmniej
   otwartych końców), wchłanianie otworów, linie gięcia → warstwa GIECIE,
   lustra P/L, rejestr zajętych widoków, wyśrodkowanie wyniku, raport CSV.
3. `testy/regresja.py` — 21 sprawdzeń na 3 rysunkach (3 różne konwencje
   klientów); **PASS obowiązkowy po każdej zmianie w src/**.

Skuteczność: ~19/20 pozycji automatycznie, reszta półautomatycznie.
Różni klienci = różne konwencje rysowania (Lantek: warstwa `1NN` = pozycja;
SBM: jedna warstwa, znaczenie niesie KOLOR; niemiecka blokowa: geometria
w INSERT-ach, linetypy DE). Wizja długoterminowa (PLAN.md): aplikacja
**samodoskonaląca się** — złoty korpus ze starych zleceń, benchmark,
interfejs wyjątków, każda ręczna korekta operatora uczy system.

## 2. Kierunek rozwoju (z tablicy METODY)

Dziś `extract_positions.py` to jeden algorytm z fallbackami (tryb warstwowy
→ bez warstw → per-kolor). Docelowo: **orkiestrator-ekstrakcji**, który dla
każdej pozycji **dobiera odpowiednią metodę** — a nie przepycha wszystko
jedną ścieżką:

```
orkiestrator-ekstrakcji ──► dobór odpowiedniej metody ──► METODY:
                                                          1. ekstrakcja zgrubna
                                                          2. ekstrakcja płaskich
                                                          3. ekstrakcja prawych i lewych
                                                          4. pomoc człowieka
                            + WERYFIKACJA (100% pewności, nic błędnego nie przechodzi)
```

**Metody:**

1. **Ekstrakcja zgrubna** — szybka ścieżka dla prostych elementów, gdzie
   wymiary z wykazu zgadzają się wprost z bbox jednego widoku. Wysoka
   pewność, minimum obróbki.
2. **Ekstrakcja płaskich** — detale bez gięcia: jeden widok = gotowy kontur,
   bez rozstrzygania rozwinięcie/rzut.
3. **Ekstrakcja prawych i lewych** — pary P/L (`gespiegelt`, kolumna INDEX
   w wykazie roboczym): lustro generowane z bliźniaka, linie gięcia MUSZĄ
   zostać i odbić się razem z konturem, rejestr zajętych widoków (lustro nie
   może ukraść widoku bliźniaka).
4. **Pomoc człowieka** — gdy żadna metoda nie daje pewności: **zaznaczanie
   na screenie** — operator dostaje podgląd całego rysunku z ramkami-
   kandydatami i klika/rysuje właściwą ramkę. Każda decyzja logowana jako
   etykieta treningowa do korpusu (PLAN.md Etap 3).

**Warstwa nadrzędna — weryfikacja:** sposób na sprawdzanie, żeby mieć
**100% pewności, że nie przepuścimy błędnych** wyników na laser. QC po
samym bbox to za mało (fałszywe trafienia: „pierścień" z ~230 krótkich
odcinków, widok izometryczny o pasującym bbox, <3 encje). Weryfikator
liczy dodatkowo: liczbę encji, średnią długość LINE, otwarte końce,
domkniętość konturu, obecność otworów. Wynik niepewny = sufiks
`_DO_SPRAWDZENIA` i kolejka do człowieka — nigdy cichy przelot.

**Powiązane pomysły z tablicy:**

- pre-test: szybkie sprawdzenie działania na zleceniu przed pełnym
  przebiegiem (karta-1);
- druga miniatura PNG **surowego rysunku** obok wyniku + ramka wziętego
  widoku — weryfikacja bez otwierania CAD-a (karta-2; demo już działa:
  `testy/pretesty/_demo_porownanie.py`).

## 3. Zadanie

1. Przeczytaj: `CLAUDE.md`, `PLAN.md`, `docs/SKILL_szkic_wyciagnij-dxf.md`,
   `src/extract_positions.py`.
2. Zaproponuj refaktoryzację `extract_positions.py` w architekturę
   **orkiestrator + metody**:
   - wspólny interfejs metody: wejście = geometria (msp po rozbiciu bloków)
     + wiersz wykazu; wyjście = kandydat (encje) + poziom pewności + metryki QC;
   - jawne reguły doboru metody (profil klienta, obecność gięcia, para P/L,
     prostota elementu) — reguły, nie czarna skrzynka;
   - **weryfikator jako osobny moduł** — każdy wynik każdej metody przechodzi
     przez ten sam QC; do Lantka trafiają tylko pewne;
   - ścieżka „pomoc człowieka" jako pierwszy krok pod interfejs wyjątków
     (PLAN.md Etap 3): na razie wystarczy status + PNG z ramkami kandydatów.
3. Plan wdrożenia małymi krokami — po każdym kroku `python testy/regresja.py`
   musi być PASS zanim przejdziesz dalej.

## 4. Zasady niezmienne (nie łamać)

1. Regresja przed wszystkim — żadna zmiana bez PASS na starych przypadkach.
2. Nie zgadujemy geometrii — niepewne = do człowieka. Złom kosztuje więcej niż klik.
3. Otwory są święte. Kontur musi być zamknięty. Wynik wyśrodkowany (środek bbox w (0,0)).
4. Uczenie = jawne reguły + progi + profile (wyjaśnialne), nie czarna skrzynka.
5. Każda ręczna decyzja zostawia ślad w korpusie — inaczej uczenie nie ma paliwa.
6. PNG renderować wyłącznie przez `testy/pretesty/_render_png.py` (czarne tło).
