# 54_4867 — STAN I KONTYNUACJA (przed compact, 03.07.2026)

## ⛔ NAJWAŻNIEJSZY WNIOSEK (błąd weryfikacji — nie powtórzyć)
Licznik konturów wewnętrznych (region↔wynik) sflagował 13 pozycji. **Duże różnice
(brak 17/22/64/128) odrzuciłem BEZ OGLĘDZIN jako „szum bbox / 2 widoki" — to było
FAŁSZYWE.** To były REALNE duże braki (całe bloki otworów/perforacji).
**ŻELAZNA ZASADA: KAŻDA flaga = oględziny wzrokowe (render region vs wynik).
NIGDY nie odrzucać flagi po WIELKOŚCI różnicy — największe różnice = najgroźniejsze
braki.** Licznik tylko wskazuje GDZIE patrzeć; decyzja zawsze wzrokiem, 100% flag.

## STAN ZLECENIA
- 98 pozycji `nazwa_rysowanie`, 43 rysunki — wszystkie skonwertowane + wyekstrahowane.
- Wykaz `wykaz_rysowanie_54_4867.xlsx` wypełniony; backup `..._BACKUP.xlsx`.
  Kolumny: AR nazwa_rysowanie, AS uwagi_rysowanie, AT plik_dxf, AU technologia,
  AV uwagi_technologia, AW/AX wymiar_dxf_x/y, AY skala, AZ+ kontrola wymiarów
  (wg `tablica/pomysł/kontekst/3.2.2 - dxf_reader.py`: uwagi_wymiar="ok" gdy X i Y ±1).
- Gotowe DXF: `wyniki_rysowanie/_DXF_gotowe/` (96 plików + PNG). Nazwa = nazwa_rysowanie.
- ⚠️ Wpisany bilans 71 ziel/26 żółt/1 czerw jest ZA OPTYMISTYCZNY — część zielonych
  ma ZGUBIONE CECHY (patrz niżej). Trzeba przejść wszystkie 13 flag wzrokiem.

## ✅ NAPRAWIONE region+warstwa (04.07 — folder `poprawki_region_warstwa/`, wgrane do `_DXF_gotowe/`)
Narzędzie: `_region_warstwa.py` (auto-wykrycie warstwy geometrii = najczęstsza L
koloru 7 w bbox; okręgi=najmniejszy; gięcia P/L-lub-skos). KAŻDA obejrzana wzrokiem.
- **SL10585490_p1P + p2L** (9→26 kontur) — lewy blok, fasola, 2 kolumny slotów, dolny rząd.
- **SL40051182_p1P + p2L** (6→17) — pas środkowy + cały dolny rząd 6 slotów.
- **SL10596954_p1** (33→67) — 2 bloki wentów + narożne sloty (logo SBM = grawer, OK).
- **SL40071953_p1P + p2L** (54→68) — kwadratowe otwory + 2 pionowe sloty.
- **SL10599245_p1** (20→21) — wielki owal Ø~225 mm (spline). UWAGA: p1≠p2 (p2 bez owalu — asymetria do potw.).
- **SL41061329_p1** (7→8) — poziomy slot.
- **SL10599171_p1** (4→8) — +4 sloty poziome. WYKRYTE SWEEPEM (STAN błędnie miał za kompletny!).
- Bez zmian (false positive): SL10596953_p1/p2, SL10596954_p2, SL10599245_p2, SL10602681_p1, SL41085224_p1, SL10585554_p1, SL10596945_p3P_1.
- Thorough sweep `/tmp/sweep.py` (region vs delivered dla WSZYSTKICH „bez warstw") = domknięty; jedyny nowy brak to SL10599171_p1.
- ZOSTAŁO: wpisać poprawki do wykazu (patrz `poprawki_region_warstwa/RAPORT_POPRAWEK.md`) — nie nadpisano, bo wykaz był otwarty z niezapisanymi edycjami STATUS.

## JUŻ NAPRAWIONE (nie ruszać)
- SL10596945 p3P/p4L/p3P_1/p4L_1 — dorobiona fasola + usunięte podwójne okręgi Ø14.7 (zostało Ø13).
- SL400521106_p1 — dorobione 4 zgubione sloty (teraz 8).
- SL10602681_p1 — odduplikowane okręgi Ø6.

## POTWIERDZONE KOMPLETNE (false positive, nie ruszać)
- SL10599171_p1 (4 sloty narożne), SL10585490_p3, SL10585490_p6, SL10585490_p4P (off-by-one lustra).

## METODA NAPRAWY region+warstwa (sprawdzona)
1. Z raportu `<z>_raport.csv` weź src_x1..src_y2 + scale dla pozycji.
2. W `<z>_1_conv.dxf`: warstwa geometrii = najczęstsza (≠ '1', ≠ Defpoints) w bbox.
   Weź WSZYSTKIE encje tej warstwy w bbox (nie kolor 4=oś). Transform:
   `Matrix44.translate(-cx,-cy) @ Matrix44.scale(scale)`, cx,cy=środek bbox.
   Kolor 6 → warstwa GIECIE; reszta → warstwa 0.
3. Reguły czyszczenia:
   - linie gięcia: usuń jeśli **nie-P/L I proste** (zostaw gdy P/L `_p\d+[PL]` albo skos >5° od osi).
   - okręgi: per środek zostaw NAJMNIEJSZY (usuń współśrodkowe większe i duplikaty).
4. Lustra P/L = odbicie bazy `Matrix44.scale(-1,1,1)` + recenter; duplikaty = kopie.
5. Re-render `testy/pretesty/_render_png.py`; **obejrzyj wzrokiem region vs wynik**.
6. Zaktualizuj wykaz: wymiar_dxf_x/y (AW/AX) + kolumny kontroli (BB/BC X-DXF/Y-DXF,
   BD uwagi_wymiar, BH/BI checks) dla poprawionego wiersza.

## NARZĘDZIA (w tym folderze)
- `_licznik_konturow.py` — licznik konturów wewnętrznych (cyklomatyka E-V+C + samozamknięte, minus kontur zewn.). UWAGA: off-by-one na lustrach (sklejanie 0.1mm), region liczy sąsiadów → to FLAGER, nie bramka.
- `_postproc.py` — post-processing wszystkich pozycji (naming, gięcia, lustra, dup, wykaz).
- `_batch_driver.py` — konwersja+ekstrakcja wsadowa (dodać RETRY dla GstarCAD).
- `_conv_bak.py` — konwersja plików .bak (=DWG) z `dok54/konwersja reczna/`.
- `UWAGI/strategia_kompletnosc_otworow.md` — pełna strategia (7 warstw obrony).
- `UWAGI/uwagi do poprawki.md` — prompty operatora.

## LICZNIKI KOMPLETNOŚCI — ślepe plamy (dlaczego zgubiłem)
- Licznik CIRCLE (tylko okręgi): czysty, ale NIE widzi slotów/perforacji → dał „0" i uśpił czujność.
- Licznik ARC+CIRCLE w bbox: szum od sąsiednich widoków i naroży.
- Licznik konturów wewn.: widzi wszystko, ale ma szum (region liczy sąsiadów/balony, off-by-one na lustrach).
- **NAJPEWNIEJSZE = nakładka region-na-źródło + oczy.** Docelowo shapely.polygonize (bez off-by-one).

## REGUŁY DZIEDZINOWE (spisane w kontekst/wiedza/ + CLAUDE.md pułapki 5-9)
- Cechy odseparowane gubione przez klaster → region+warstwa (`cechy-odseparowane-region-warstwa`).
- Podwójne/zdublowane okręgi → najmniejszy (`otwory-wspolsrodkowe-zdublowane`).
- Linie gięcia tylko P/L lub skos (`giecie-kiedy-nanosic-pl-skos`).
- Technologia GS/G/S/brak z „Schweissgruppe" w DWG (`technologia-schweissgruppe-auto`).
- Konwersja retry; TIF-reconstruction = czerwono, ostateczność (`konwersja-gstarcad-retry-tif-czerwono`).
- Test XFAIL znanych błędów: `testy/regresja_znane_bledy.py` (4 cele silnika V2).
- Szkolenie: `szkolenia/projekty/2026-07-03_54_4867_ekstrakcja_SBM/`.

## NASTĘPNY KROK (po compact)
Przejść WZROKIEM wszystkie 13 flag (render region vs wynik, bez pomijania dużych),
naprawić potwierdzone region+warstwa (4 duże + lustra + 4 drobne do sprawdzenia),
re-render, zaktualizować wykaz i bilans. Potem ewentualnie wpiąć region+warstwa do
silnika V2 (żeby XFAIL-e przeszły w XPASS).
