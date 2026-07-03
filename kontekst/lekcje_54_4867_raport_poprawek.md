# Raport poprawek region+warstwa — 54_4867 (03.07.2026)

Metoda: `_region_warstwa.py` — bierze WSZYSTKIE encje warstwy geometrii (kolor 7,
gięcia kolor 6) w bbox widoku z raportu (nie tylko spójny klaster) → transform jak
kontur → czyszczenie (okręgi współśrodkowe = najmniejszy; gięcia tylko P/L lub skos).
**Każda pozycja obejrzana WZROKIEM** (region-źródło vs stary vs nowy), zgodnie z
żelazną zasadą (nigdy nie odrzucać flagi po wielkości różnicy).

Pliki: `poprawki_region_warstwa/*.dxf|png`; wgrane do `_DXF_gotowe/`
(stare w `_DXF_gotowe/_przed_region_warstwa/`).

## Naprawione (potwierdzone realne braki)

| pozycja | kontury: stare→nowe | co odzyskano (wzrokowo) | tech |
|---------|:---:|---|:---:|
| **SL10585490_p1P** + p2L | 9→26 | lewy blok: duży owalny otwór + 4 sloty + fasola + 2 kolumny slotów (było 2 z 16) + dolny rząd | GS |
| **SL40051182_p1P** + p2L | 6→17 | cały pas slotów strefy środkowej + CAŁY dolny rząd 6 slotów | G |
| **SL10596954_p1** | 33→67 | lewy blok 6 wentów + drugi blok ~26 wentów + narożne sloty (logo SBM = grawer, OK) | G |
| **SL40071953_p1P** + p2L | 54→68 | ~10 małych kwadratowych otworów w pasie środkowym + 2 pionowe sloty | GS |
| **SL10599245_p1** | 20→21 | **wielki centralny owal Ø~225 mm** (spline niepołączony z konturem — klaster gubił) | GS |
| **SL41061329_p1** | 7→8 | poziomy slot (fasola) nad dolnym okręgiem | G |
| **SL10599171_p1** | 4→8 | po 2 poziome sloty z każdej strony (4 łącznie) — wykryte SWEEPEM, poza listą operatora | — |
| **SL40061302_p1** | 0→3 | 3 poziome sloty (fasole) w środku ośmiokąta — wskazane przez operatora; geometria KOLOR 2 (nie 7!) | G |

Wymiary zewnętrzne bez zmian (kontur ten sam) → kontrola wymiarów w wykazie zostaje.

## Do potwierdzenia operatorem (asymetria)

- **SL10599245_p1 vs p2** — to NIE para lustrzana, lecz DWIE różne części o tym samym
  obrysie: **p1 ma duży owalny otwór dostępowy Ø~225 mm, p2 go nie ma** (na warstwie
  geometrii p2 tego splajnu brak). Geometria wyekstrahowana wiernie ze źródła —
  ale asymetrię warto zweryfikować z rysunkiem (status: ŻÓŁTY).

## Sprawdzone — bez zmian (false positive flagi, NIE ruszane)

- **SL10596953_p1** — kontury 67 = 67 (już kompletny; „bez warstw, all" złapał całość).
- **SL10596953_p2 / SL10596954_p2** — proste płyty 382,5×180 z 4 otworami narożnymi, kompletne.
- SL10599245_p2 — poprawny (bez owalu, zgodnie ze źródłem).
- **SL41085224_p1, SL10585554_p1** — sweep flagował, ale po dedupie region=dostarczone (szum liczników), kompletne.
- **SL10602681_p1** — 6 otworów, sweep liczył 15 (przed dedupem Ø6), delivered 11 = poprawnie odduplikowane.
- **SL10596945_p3P_1** — duplikat świeży (4=4 z naprawionym p3P).

## Thorough sweep (domknięcie żelaznej zasady)

`/tmp/sweep.py` + `/tmp/sweep2.py`: dla KAŻDEJ pozycji trybu „(bez warstw)"
policzono kontury region+warstwa vs dostarczone. Flagi delta≥2 obejrzano WSZYSTKIE
wzrokiem. Wynik: **SL10599171_p1** (STAN błędnie miał za „kompletny").

**WSZYSTKIE tryby ekstrakcji pokryte** (bo geometria bywa na różnym kolorze!):
- `col7` (17×), `all` (32×) → sweep1/2.
- `col2` (4×) → **znaleziono SL40061302_p1** (sweep1 szukał tylko koloru 7 — pominął!).
- `col4` (1×) = SL10600635_p1 → naprawiony wcześniej (wachlarz, 9 otw.), raport przestarzały.
- `geometria` (3×) = SL10599245_p6/p7 (warstwa 107), SL10585552_p4L_1 (warstwa 53)
  → region=dostarczone=1, kompletne (p6/p7 i tak DO_SPRAWDZENIA jako tarcze okrągłe).

LEKCJA DLA SILNIKA V2: sweep kompletności NIE może zakładać koloru geometrii = 7;
klaster gubi cechy odseparowane w KAŻDYM trybie (col2/col4/all/col7).

## Wykaz — do uzupełnienia (nie nadpisałem, masz otwarte niezapisane edycje STATUS/UWAGI)

Dla wierszy: SL10585490 (p1P,p2L), SL40051182 (p1P,p2L), SL10596954_p1,
SL40071953 (p1P,p2L), SL10599245_p1, SL41061329_p1:
- `plik_dxf` = tak, wymiary bez zmian, `uwagi_rysowanie` = „cechy uzupełnione region+warstwa".
- SL10599245_p1: status ŻÓŁTY + uwaga o owalu vs p2.
- reszta: status jak był (ZIELONY), skoro geometria teraz kompletna.
