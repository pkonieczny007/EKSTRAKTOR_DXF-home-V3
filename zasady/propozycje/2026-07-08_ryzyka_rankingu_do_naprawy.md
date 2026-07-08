# Ryzyka zacommitowanego rankingu (detektor rozwiniecia + partition) - do naprawy przez golden

- **Data / autor:** 2026-07-08, adwersaryjny audyt (workflow, 3 agenty) + weryfikacja Opus
- **Status:** ZNALEZIONE po fakcie - kod rankingu wszedl commitem `1164059 home` BEZ review
  i BEZ testow; testy dopisane potem (test_detektor 24/0, test_lustro 16/0, regresja 43/43,
  benchmark_v3 0 regresji). Ryzyka LATENTNE (0 regresji na zbiorze testowym), realne dla
  typow rysunkow SPOZA zbioru. Naprawa: golden PRZED zmiana kodu (zasada 11).

## Kontekst
Commit `1164059` wpial: detektor_rozwiniecia.py + extract_positions.py (rank_value tuple,
sciezka awaryjna argmax geo, grupowanie per-warstwa, partition kolor6-przed-linetype) +
warianty.py (lustro T1/T2). Przechodzi wszystkie bramki, ale W-A wygrywa 0% pozycji, wiec
benchmark (porownuje ZWYCIEZCOW) NIE widzi zmian w W-A - stad 0 regresji mimo realnych ryzyk.

## RYZYKO 1 (srednia) — ✅ NAPRAWIONE 2026-07-08 (silnik-w-a v1.1)
**Rozwiazanie:** test GEOMETRYCZNY zamiast progu dlugosci (fable-advisor zmierzyl 84288
encji kolor-6: konwerter GstarCAD rozbija linie przerywane na kreski <3mm, wiec sam prog
dlugosci zabilby rozbite giecie; ZERO z 210 realnych giec przechodzi przez srodek okregu).
`partition()`: kolor-6 LINE -> `axis` (odrzucany z GIECIE) tylko gdy midpoint <= 0.5*r od
srodka CIRCLE i L in [0.8, 4.0]*srednica; cala reszta magenta -> `bend`. Przesuwa encje
wylacznie miedzy bend/axis (poza klastrowaniem geom+dashed) -> klastry/ranking/detektor
nietkniete. Golden `testy/golden/R1_kolor6_krzyz_osi_vs_giecie/` (geom=4/axis=6/bend=14,
w tym rozbite giecie 12 kresek NIE ginie + os symetrii L/D=5.6 zostaje bend). Test
`testy/test_r1_kolor6_giecie.py` (7 asercji). Walidacja: regresja 43/43, testy_v2 35/35,
detektor 24/24, lustro 16/16, warianty 17/17, benchmark_v3 0 regresji, benchmark_v2 bez
zmian (35 identycznych przed i po). Realnie SL40081914: 48 falszywych krzyzy z GIECIE
usunietych, 0 zgubionej geometrii. NIEPOKRYTE (zostaje jako znane): krzyz osi na
fasoli/slocie/elipsie bez CIRCLE -> zostaje bend jak dzis (lagodzi W-D + oko w galerii).

### (historyczny opis defektu)
**POTWIERDZONE w kodzie** (`extract_positions.py:234`): `if e.dxf.color == 6: bend.append(e)`
bez rozroznienia dlugoscia, choc komentarz (l.231-233) obiecuje "krzyz osi otworu rozni sie
od giecia dlugoscia". Stary kod: magenta+CENTER -> axis (odrzucany). Nowy: -> bend (GIECIE).
- Skutek typowy: KRZYZ OSI OTWORU rysowany magenta trafia na warstwe GIECIE = falszywa linia
  giecia (myli bramke 7/lustro). Metadata, nie geometria ciecia; W-A rzadko wygrywa; lapie
  czlowiek. Ale realne.
- Skutek skrajny (rzadki): fragment OBRYSU w magenta -> do bend, znika z geom -> otwarty
  kontur / brak krawedzi na laser (lapie bramka 2).
- **Naprawa:** prog dlugosci wzgledem szerokosci widoku (linia giecia ~ pelna szerokosc
  czesci; krzyz osi ~ srednica otworu). Golden: rysunek z magenta krzyzem osi + magenta
  linia giecia -> giecie na GIECIE, os odrzucona. Do zrobienia PRZED zmiana l.234.

## RYZYKO 2 (srednia) — ✅ NAPRAWIONE 2026-07-08 (silnik-w-a v1.3, detektor_rozwiniecia.py)
**Rozwiazanie:** `_bend_annot_nearest` — kazda adnotacja giecia liczy +2 tylko dla klastra,
ktory jest jej NAJBLIZSZY (srodkiem bbox, jak babelek kategorii 4), nie dla kazdego kandydata
ktorego bbox ja zawiera. Adnotacja sasiedniego widoku wpadajaca w (wiekszy) bbox innego
kandydata przestaje dawac falszywe +2. Izometryki 91010/652 (maja adnotacje giecia w
rozwinieciu) nietkniete - rozwiniecie jest najblizsze swojej adnotacji. Test
`testy/test_r2_bend_annot_najblizszy.py` (7 asercji: nowe przypisanie, dowod ze stare 'w bbox'
dawalo oba, integracja przez features). Bramka: regresja 43/43, detektor 24/24 (izometryki
bez zmian), benchmark_v3 0 regresji, testy_v2/lustro/warianty/gr4/sweep_54_4867 PASS.

### (historyczny opis defektu)
`detektor_rozwiniecia`: bend_annot = +2 za KAZDY tekst giecia (n.oben/gekantet/Kantung),
ktorego punkt wstawienia lezy w bbox kandydata - a teksty zbierane z CALEGO msp. Adnotacja
giecia SASIEDNIEGO widoku, geometrycznie w bbox innego kandydata o tych samych wymiarach
wykazu, daje falszywe +2. Bo prop_match=True dla wszystkich (skala 0/1), o rankingu decyduje
geo -> te +2 potrafi PRZEWROCIC wybor na zly klaster.
- Scenariusz: rysunek z 2-3 widokami blisko (Lantek/niemiecki blokowy), opis "gekantet"
  jednego rozwiniecia nakłada sie na bbox drugiego kandydata -> wybrany zly widok.
- **Naprawa:** przypisz adnotacje giecia do NAJBLIZSZEGO klastra (jak kategoria 4 babelek),
  nie do kazdego bbox go zawierajacego. Golden: 2 widoki blisko + 1 adnotacja giecia.

## RYZYKO 3 (niska/srednia) — ✅ NAPRAWIONE 2026-07-08 (silnik-w-a v1.2)
**Rozwiazanie:** `_pick_fallback_geo` — w sciezce awaryjnej (extract_position, brak
prop-matchu) sposrod kandydatow ktore NIE wygladaja na rzut (geo > PROG_ANTY) wybiera
NAJWIEKSZY powierzchnia; dopiero gdy wszyscy wygladaja na rzut - argmax geo (jak dawniej).
Zmierzone/potwierdzone: SL40047020 40x16(geo+1) -> 62x53(geo-1, rozwiniecie); SL10582652
22x22(geo+4) -> 281x44(geo+2, rozwiniecie). Bez zmiany: SL10582797, SL40091010 (stary tez
trafial). Test `testy/test_r3_fallback_rozmiar.py` (8 asercji, +dowod ze stary argmax-geo
bral zly dla 47020/652). Bramka: regresja 43/43, detektor 24/24, benchmark_v3 0 regresji,
testy_v2/lustro/warianty/gr4/sweep_54_4867 PASS.

### (historyczny opis defektu)
Zmierzone przez test-writera: SL40047020 sciezka awaryjna - maly klaster 40x16 (geo +1)
WYGRYWA nad rozwinieciem 62x53 (geo -1), bo kara open_ends (wchloniete linie wymiarowe)
spycha prawdziwa czesc ponizej szumu. Detektor moze wskazac zly, drobny klaster jako
rozwiniecie.
- **Naprawa:** w argmax uwzglednic ROZMIAR/zgodnosc z wykazem jako wage (nie sam geo);
  albo min. rozmiar klastra kandydata. Golden: SL40047020 (juz jest) - argmax ma wskazac
  62x53, nie 40x16.

## RYZYKO 4 (info) - rozjazd geo-margin prototyp vs kod
Prototyp zapowiadal geo(rozwiniecie)>=+2; realnie przy klastrowaniu calego msp (gap=8)
rozwiniecie WCHLANIA linie wymiarowe -> open_ends>4 -> kara -2 -> geo <+2 dla 797/47020/61302.
Separacja WZGLEDNA (rozwiniecie>izometryka) trzyma sie wszedzie (ranking dziala), ale prog
bezwzgledny +2 tylko dla czystych konturow (652 +2, 91010 +7). test_detektor asertuje
niezmienniki realne, nie prototypowe. Do rozwazenia: czyszczenie linii wymiarowych przed
liczeniem open_ends w score (spojnie z UWAGA-pass/W-D czyszczeniem).

## Kryterium naprawy (kolejnosc, kazde przez golden)
1. ✅ RYZYKO 1 (partition krzyz osi) - ZROBIONE 08.07 (silnik-w-a v1.1).
2. ✅ RYZYKO 3 (argmax rozmiar) - ZROBIONE 08.07 (silnik-w-a v1.2).
3. ✅ RYZYKO 2 (bend_annot najblizszy klaster) - ZROBIONE 08.07 (silnik-w-a v1.3). NASTEPNE:
4. RYZYKO 4 (czyszczenie linii wymiarowych przed geo - INFO, do rozwazenia).
Kazde: golden -> zmiana -> regresja 43/43 + benchmark_v3 + test_detektor/lustro -> potwierdzenie.

## PRZY OKAZJI ZNALEZIONE (osobne, NIE z R1)
- **benchmark_v2 PRE-EXISTING FAIL**: `SL10578806_p4` 14 roznic W-A vs W-B na czystym HEAD
  (przed patchem R1 - baseline potwierdzil). Maskowane przez `--szybko` (SKIP_SZYBKO zawiera
  benchmark_v2). Plik NIE ma ani jednej encji przenoszonej przez R1 (magenta-w-axis=0), wiec
  R1 go nie dotyka. Osobna diagnoza do zrobienia - do NOWEJ propozycji, nie mieszac z R1.
