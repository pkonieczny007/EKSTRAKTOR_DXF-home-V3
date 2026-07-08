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

## RYZYKO 1 (srednia) - partition: kolor 6 BEZWARUNKOWO na GIECIE, brak progu dlugosci
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

## RYZYKO 2 (srednia) - bend_annot liczony z CALEGO modelspace, przestrzenny false-positive
`detektor_rozwiniecia`: bend_annot = +2 za KAZDY tekst giecia (n.oben/gekantet/Kantung),
ktorego punkt wstawienia lezy w bbox kandydata - a teksty zbierane z CALEGO msp. Adnotacja
giecia SASIEDNIEGO widoku, geometrycznie w bbox innego kandydata o tych samych wymiarach
wykazu, daje falszywe +2. Bo prop_match=True dla wszystkich (skala 0/1), o rankingu decyduje
geo -> te +2 potrafi PRZEWROCIC wybor na zly klaster.
- Scenariusz: rysunek z 2-3 widokami blisko (Lantek/niemiecki blokowy), opis "gekantet"
  jednego rozwiniecia nakłada sie na bbox drugiego kandydata -> wybrany zly widok.
- **Naprawa:** przypisz adnotacje giecia do NAJBLIZSZEGO klastra (jak kategoria 4 babelek),
  nie do kazdego bbox go zawierajacego. Golden: 2 widoki blisko + 1 adnotacja giecia.

## RYZYKO 3 (niska/srednia) - argmax-geo w sciezce awaryjnej wybiera DROBNY klaster
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
1. RYZYKO 1 (partition dlugosc) - safety-adjacent, pierwsze. 2. RYZYKO 3 (argmax rozmiar).
3. RYZYKO 2 (bend_annot najblizszy klaster). 4. RYZYKO 4 (czyszczenie przed geo).
Kazde: golden -> zmiana -> regresja 43/43 + benchmark_v3 + test_detektor/lustro -> potwierdzenie.
