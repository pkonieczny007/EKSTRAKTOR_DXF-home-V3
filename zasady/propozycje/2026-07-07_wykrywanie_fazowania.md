# Propozycja zasady: wykrywanie FAZOWANIA (chamfer) i oznaczanie jako technologia

- **Data / autor:** 2026-07-07, operator (prosba na 38_1847 gr6) + AI (spisanie)
- **Status:** **wdrozona (2026-07-07)** — flager `produkcja/kontrola/fazowanie.py`
  (3 pozytywy, 0 falszywych na 260 DXF), golden `testy/golden/fazowanie_linia_przy_krawedzi/`,
  test `testy/test_fazowanie.py`. Regula: `zasady/reguly/fazowanie-technologia.md`.
- (historycznie: propozycja → golden (p2 SL10585238/SL10585242) → prototyp (fable-advisor) →
  testy → merge (flager fazowania + kolumna technologia w raporcie/wykazie))

## Problem, ktory rozwiazuje

Detale bywaja FAZOWANE (sfazowana krawedz - przygotowanie pod spaw / estetyka). Fazowanie
NIE jest cieciem lasera - to obrobka krawedzi. Na rysunku widac je jako:
- **linia rownolegla do krawedzi konturu**, blisko niej (np. ~5 mm), na dlugosci krawedzi,
  w kolorze geometrii (kol. 7) - NIE magenta;
- potwierdzenie na **rzucie bocznym (obok)**: sfazowany profil krawedzi (skos).

Dzis pipeline traktuje te linie jako element konturu -> tworzy T-zlacza (bramka 2:
"2 otwarte konce") i pozycja idzie w 🟡 bez wyjasnienia. Operator: takie p2 gdy zolte to
sprawdzi i sa OK - ale **chce, zeby pipeline WYLAPAL fazowanie** (oznaczyl, nie zgadywal).

Przyklady: SL10585238 p2, SL10585242 p2 (linia pelnej szerokosci ~5 mm od gornej krawedzi).

## Tresc zasady (czytelna dla czlowieka)

1. **Flager fazowania:** linia (LINE / segment LWPOLYLINE) w kolorze geometrii, ROWNOLEGLA
   do krawedzi konturu zewnetrznego, w odleglosci d (typowo 1-10 mm), o dlugosci ~= dlugosc
   tej krawedzi, tworzaca T-zlacza z bokami (a nie zamkniety otwor) -> KANDYDAT na fazowanie.
2. **Potwierdzenie rzutem (opcjonalne, mocniejsze):** obok widoku jest cienki rzut boczny
   z krawedzia skosna -> podnosi pewnosc.
3. **Dzialanie:** NIE traktowac linii fazowania jako konturu ciecia (nie liczyc jej
   T-zlacz jako "otwarte konce"). Kontur ciecia = sam obrys zewnetrzny (domkniety).
   Fazowanie zapisac jako **technologia = "fazowanie"** (kolumna technologia w raporcie /
   wykazie, obok G/S/GS) + `uwaga`. Pozycje zostawic 🟡 do potwierdzenia (bezpiecznie),
   ale z JAWNYM powodem "wykryto fazowanie" zamiast mylacego "2 otwarte konce".
4. **Nie zdejmowac fazowania z rysunku wynikowego** bez decyzji - operator moze chciec je
   zachowac jako znacznik. Domyslnie: kontur ciecia osobno, linia fazowania oznaczona.

## Przyklady referencyjne (golden)

- `wyniki/38_1847/gr6/_REGION_SL10585238_p2.png`, `_REGION_SL10585242_p2.png` - zrodlo z
  linia fazowania; wyniki `SL10585238_p2.dxf` / `SL10585242_p2.dxf` (dzis T-zlacza).
- Do golden: para (zrodlo, oczekiwanie: technologia=fazowanie, kontur zewn. domkniety).

## Uwaga wdrozeniowa

Geometria (rownoleglosc, T-zlacza, korelacja z rzutem bocznym) = kandydat do
[[fable-advisor-trudne-problemy]]. Ryzyko falszywych trafien (realna cecha vs fazowanie) -
flager, nie bramka: wskazuje i oznacza, decyzje potwierdza czlowiek (zasada 6).
