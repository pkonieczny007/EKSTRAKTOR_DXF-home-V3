# WNIOSKI: zly wybor widoku — rozwiniecie vs izometria/rzut zgietej czesci

**Data / autor:** 2026-07-06, fable-advisor (pomiary) + operator (korekta i wzorce).
**Przypadki dowodowe (4):**
- `testy/golden/SL10582652_p1_widok_z_gieciem/` — system wzial IZOMETRIE, wykaz ma BLEDNA dlugosc (720 zamiast 560);
- `testy/golden/SL10582797_p1_rzut_boczny_zamiast_rozwiniecia/` — system wzial RZUT ZGIETEJ CZESCI, wykaz POPRAWNY (czysty blad wyboru widoku); czlowiek wskazal widok ZAZNACZENIEM na PNG (nie rysowal DXF);
- SL10583142 (zlecenia/38_1847_ZUBEHOR/dok_zub/) — system wzial WLASCIWY widok (rozwiniecie 895.36x273.58 == wykaz 894x274), czerwony wtornie przez otwarty kontur kolnierzy; dostarcza SYGNAL TEKSTOWY: adnotacja "alle Kantungen 90 st. n. oben k. / all bendings up 90" WEWNATRZ konturu rozwiniecia (wniosek D). NIE jest to przyklad zlego wyboru widoku;
- SL40685913_p1 (wyniki/38_1847_ZUBEHOR/_all/warianty/wA/) — detal POPRAWNY z NACIECIAMI, falszywy czerwony bramki 2 (wniosek E). Tez nie jest bledem wyboru widoku.

W przypadkach zlego wyboru widoku (652, 797) system slusznie skonczyl na czerwono
(otwarty kontur + brak zgodnosci proporcji) — nic nie poszlo na laser. Wnioski dotycza
NASTEPNEGO kroku: zamiast "czerwony -> czlowiek rysuje od zera" system ma umiec
(a) wskazac wlasciwy widok detektorem rozwiniecia, (b) gdy niejednoznaczne — poprosic
czlowieka o ZAZNACZENIE widoku (kategoria 6), co jest tansze niz rysowanie,
(c) nie strzelac falszywymi czerwonymi na nacieciach/kolnierzach czesci gietych.

---

## 1. Pomiary (deterministyczne, ezdxf+shapely na obu conv)

### SL10582652 (A3 420x297, SBM "HALTERUNG FUR MOTOR ABDECKUNG", tabelka: 1:2 i 1:5)

| klaster | warstwa | bbox zrodla | encje | CIRCLE | ELLIPSE | otwarte konce | linie kolor 6 | co to jest |
|---|---|---|---|---|---|---|---|---|
| rozwiniecie | **51** | 280.00 x 41.98 | 31 | 2 | 0 | **0** (kontur zamkniety, polygonize po snap 0.02) | **1x DASHDOT L=280.00**, pozioma, konce DOKLADNIE na krawedziach konturu (x=62.52 i 342.52) | **widok do palenia** |
| izometria | 101 | 79.50 x 45.07 | 65 | 0 | **29** | 18 | 3x Continuous (0.55; 0.47; 83.47 pod katem 25.7 st.) | rzut izometryczny, "(M / S 1:5)" |
| przekroj | 101 (x>360) | 23.2 x 23.2 | ~18 | 0 | 0 | brak zamknietych | 4x DASHED L=1.5 | przekroj profilu L 45x45 po gieciu |

- **Skala rozwiniecia = 2.0 (tabelka 1:2), zmierzona z DIMENSION:** dim tekst "560" ma
  meas=280.00; dim "84" ma meas=41.98. Rozwiniecie 1:1 = **560.00 x 83.96**.
- **Wzorzec czlowieka = DOKLADNIE warstwa 51 x2** (te same 31 encji: 16 LINE + 12 ARC
  + 2 CIRCLE kolor 7 + 1 LINE kolor 6; 560.00 x 83.96).
- Kontury wewnetrzne rozwiniecia: 5 (2 okregi D6->D12 po skali + 3 sloty).
- Na widoku rozwiniecia MTEXT kolor 3: **"90 st. n.oben k. | bend up 90"** — jawna
  adnotacja giecia.
- Katy linii rozwiniecia: tylko 0/45/90/135 st. (ortho); izometria: 25/95/140/160 st.,
  ortho_frac=0.25 — bramka 6 (rozklad katow) ODROZNIA je wprost.
- **Co zrobil system:** wzial klaster izometrii (jedyny na warstwie pozycyjnej 101)
  i przeskalowal x9.053 (=719.73/79.50), zeby trafic wykazowe 720 -> wynik
  719.73 x 408.31, otwarty kontur (50 koncow), "brak zgodnosci proporcji" -> czerwony.

### Skad 720 vs 560 (blad wykazu — zweryfikowany geometria)

- **Liczba 720 NIE wystepuje NIGDZIE na rysunku** — zaden z 18 DIMENSION jej nie
  pokazuje. Wymiary calkowite na rysunku: dlugosc **560**, wysokosc **84**.
- 84 = 45 + 45 - 2*3 (przekroj L 45x45, blacha t=3, dedukcja giecia) — spojne
  z rozwinieciem; giecie dzieli 84 na 42+42 (dim "42" na rysunku).
- Przy skali 2 z tabelki wysokosc wykazu pasuje idealnie (83.96 vs 84), dlugosc nie
  (560 vs 720). Zadna skala nie godzi OBU wymiarow wykazu z zadnym klastrem —
  dlatego system dryfowal do izometrii z niestandardowa skala 9.05.
- Operator potwierdzil: **720 w wykazie jest bledne**, realne rozwiniecie = 560.

### SL10582797 (A4 210x297, SBM "QUERVERBINDUNG MOTORABDECKUNG", tabelka: 1:5 i 1:10)

| klaster | warstwa | bbox zrodla | encje | CIRCLE | ELLIPSE | otwarte konce | linie kolor 6 | co to jest |
|---|---|---|---|---|---|---|---|---|
| rozwiniecie | **51** | 14.88 x 104.93 | 17 | 2 (D2.4 -> D12) | 0 | **0** (polygonize: outer + 2 okregi) | **1x Continuous L=6.00 pod katem 59 st.** (giecie SKOSNE, "bend up 90") | **widok do palenia** |
| rzut zgietej czesci | 101 (srodek) | 8.00 x **101.81** | 36 | 0 | **13** (4 DASHED = ukryte otwory) | otwarty | 7x DASHED + 1x Continuous | czesc PO GIECIU; H=101.81 = dokladnie dim referencyjny "(509)" (dlugosc po zgieciu, 1:5) |
| poglad | 101 (prawo-dol) | 6.56 x 50.36 | 33 | 0 | 17 | otwarty | 3x Continuous | "(M / S 1:10)" |

- **Skala rozwiniecia = 5.0 (tabelka 1:5), zmierzona z DIMENSION:** dim "527"
  meas=105.31 (527/105.31=5.004), dim "76" meas=15.25 (76/15.25=4.984).
  **OBA wymiary wykazu (527 x 76) zgadzaja sie z rozwinieciem przy JEDNEJ skali —
  wykaz tu jest POPRAWNY.** Otwory: 2x D12 + wyciecie R10/D17 na haku.
- **Co zrobil system:** wzial SRODKOWY rzut zgietej czesci (zgodnosc encja-w-encje
  ze zlym plikiem: 36 encji, w tym 13 ELLIPSE) i przeskalowal x5.176 (=527/101.81),
  zeby trafic wykazowe 527 -> wynik 41.41 x 527.00; szerokosc 41.41 vs wykaz 76 ->
  "brak zgodnosci proporcji", otwarty kontur -> czerwony.
- Czlowiek NIE rysowal: zaznaczyl wlasciwy widok czerwonym kolkiem na PNG
  (`czlowiek_zaznaczenie/SL10582797-zaznaczenie.png`) — najczystszy przyklad
  brakujacej kategorii 6.

### SL10583142 (SBM "ZWISCHENBLECH", tabelka 1:5) — sygnal tekstowy + wzorzec warstw

System wzial tu WLASCIWY widok (895.36x273.58 vs wykaz 894x274 — bramka 1 OK);
czerwony byl WTORNY (otwarty kontur kolnierzy "bend up 90"). Pomiary istotne:
- **2x MTEXT "alle Kantungen 90 st. n. oben k. | all bendings up 90"** (kolor 3):
  wstawienia (338.6,339.0) i (335.9,168.0) leza **WEWNATRZ** bboxow klastrow
  rozwiniec: warstwa 51 = (303.6,306.0)-(482.4,360.8), warstwa 52 =
  (303.6,141.8)-(470.2,200.7). Adnotacja giecia siedzi W SRODKU konturu rozwiniecia.
- Warstwa 51: 178.8 x 54.8; **x5 (tabelka 1:5) = 894 x 274 = wykaz co do mm.**
- To samo w 652: MTEXT "90 st. n.oben k. | bend up 90" w (201.2,187.2) lezy wewnatrz
  bboxu rozwiniecia warstwy 51 (62.5-342.5 x 168.5-210.5).
- **Ograniczenie zmierzone:** w 797 adnotacja "bend up 90" jest widoczna na renderze,
  ale NIE istnieje jako TEXT/MTEXT (rozbita na male linie kolor 6, jak logo SBM) —
  sygnal tekstowy bywa niedostepny, wiec NIE moze byc jedynym detektorem.

### Wspolny wzorzec strukturalny (3/3 przypadki)

**Rozwiniecie lezy na warstwie 5N (51, 51, 51+52), a widoki pogladowe/zgiete na
warstwie pozycyjnej 1NN (101).** Kategoria 1 (warstwa 1NN -> pozycja 1 -> warstwa
101) kieruje system prosto w ZLY widok. Hipoteza konwencji SBM: 1NN = widok pozycji
N (po gieciu / pogladowy), 5N = rozwiniecie pozycji N (w 3142 pozycje 1 i 2 maja
odpowiednio warstwy 51 i 52 — wspiera hipoteze). Do potwierdzenia na wiekszej
probie rysunkow SBM — obserwacja do reguly typu, nie twarda regula (na razie:
warstwy INNE niz 1NN tez sa kandydatami, nie wolno ich odrzucac).
**Skala rozwiniecia = skala z tabelki rysunku w 3/3 przypadkow (2.0, 5.0, 5.0).**

---

## 2. WNIOSEK A — wybor widoku po linii giecia + otworach (detektor rozwiniecia)

**Regula ogolna (kandydat do rankingu widokow, deterministyczna):**
sposrod klastrow-kandydatow pozycji **rozwiniecie do palenia** poznaje sie po
koniunkcji mierzalnych cech:

1. **kontur zamkniety** (polygonize po snap 0.02; 0 otwartych koncow) — warunek twardy;
2. **CIRCLE > 0 lub kontury wewnetrzne > 0** (otwory sa na rozwinieciu, nie na
   pogladzie) — 652: 2 okregi + 3 sloty; 797: 2 okregi;
3. **czysta linia giecia**: LINE kolor 6 LEZACA WEWNATRZ zamknietego konturu,
   konce na konturze/przy nim; linetype dowolny (652: DASHDOT przez cala dlugosc;
   797: Continuous 6 mm SKOSNA — nie zakladac "przez cala szerokosc" ani linetype);
4. **proporcje/skala**: bbox klastra zgadza sie z wykazem przy JEDNEJ skali
   i skala ta jest STANDARDOWA (z tabelki rysunku: 1:2/1:5/1:10, lub typowa
   {1, 2, 2.5, 5, 10, 20}).

**Anty-cechy widoku pogladowego / izometrii / rzutu zgietej czesci (odrzuc):**
- **ELLIPSE w klastrze** = okregi w rzucie nieprostopadlym — najsilniejszy pojedynczy
  sygnal (652 izometria: 29 elips; 797 zly rzut: 13 elips; oba rozwiniecia: 0);
- otwarty kontur (652: 18 koncow; 797: otwarty) — juz lapie bramka 2;
- rozklad katow nie-ortho (652 izometria: ortho_frac=0.25, katy 25/95/140/160 st.
  vs rozwiniecie 1.0) — istniejaca bramka 6 rozszerzona na WYBOR widoku, nie tylko
  odrzucenie wyniku;
- linie/elipsy DASHED w roli krawedzi (ukryte krawedzie rzutu zlozonego; 797: 11 szt);
- **skala dopasowana niestandardowa** (652: 9.053; 797: 5.176) — system "naciagnal"
  skale, zeby trafic wykaz; skala spoza {tabelka, typowe} = czerwona flaga kandydata;
- adnotacja "(M / S 1:N)" przy klastrze = widok pogladowy (sygnal pomocniczy);
  odwrotnie: MTEXT "bend up"/"n.oben k."/"gekantet" przy klastrze = rozwiniecie.

Status: **wniosek-do-wdrozenia** (ranking kandydatow w szukaniu pozycji; laczy sie
z propozycja `zasady/propozycje/2026-07-07_widok_zlozeniowy_vs_do_palenia.md` —
tam widok zlozeniowy z dospawieniami, tu izometria/rzut zgietej czesci; ten sam
mechanizm rankingu moze obsluzyc oba). UWAGA na semantyke koloru 6: dziala tez
w izometrii (652: krawedz giecia 83.47 mm w izo) — samo "ma kolor 6" NIE wystarcza,
rozstrzyga koniunkcja z zamknietym konturem i orto-katami.

## 3. WNIOSEK B — wykaz to BAZA, ale bywa bledny: nie gonic za blednym wymiarem

**Mechanizm bledu 652:** zaden klaster nie godzil OBU wymiarow wykazu (bo 720 bledne),
wiec dopasowanie zdegenerowalo sie do JEDNEGO wymiaru (720 ~ 719.75 po naciagnietej
skali 9.05) na zlym widoku. Zgodnosc jednego wymiaru przy zlamanych proporcjach
to NIE trafienie — to artefakt goniema za liczba.

**Regula ogolna:** gdy najlepszy kandydat wymaga skali niestandardowej ORAZ drugi
wymiar sie nie zgadza (brak zgodnosci proporcji), a istnieje INNY klaster, ktory
przy skali standardowej godzi JEDEN wymiar wykazu i ma cechy rozwiniecia (wniosek A:
zamkniety kontur + otwory + linia giecia) -> podejrzenie **BLEDU WYKAZU**, nie braku
widoku. Wynik: eskalacja do czlowieka z jawnym powodem "wykaz podejrzany: klaster
X pasuje do wymiaru B (84) przy skali 1:2, wymiar A (720) nie wystepuje na rysunku;
zmierz/zatwierdz" — **NIGDY automatyczne przyjecie geometrii sprzecznej z wykazem**
(wykaz to baza; wyjatki additive — `kontekst/wiedza/wykaz-to-baza-additive.md`,
`zasady/propozycje/2026-07-07_bramka1_giete_wyjatek_additive.md`).
Kontrprzyklad w parze: w 797 wykaz jest poprawny i oba wymiary pasuja do rozwiniecia
przy jednej skali — detektor z wniosku A rozwiazuje 797 W PELNI automatycznie,
a 652 zamienia z "czerwony, czlowiek rysuje od zera" na "czerwony, potwierdz
kandydata 560x84 i popraw wykaz".

Status: **wniosek-do-wdrozenia** (logika oceny kandydatow + tresc powodu semafora).

## 4. WNIOSEK C — kategoria 6: czlowiek WSKAZUJE widok (mechanizm nie istnieje)

Audyt 2026-07-06 (pkt 2.2/5) potwierdza: kategoria 6 ("pomoc czlowieka") jest
w `config/kategorie.yaml` tylko zadeklarowana — **nie ma implementacji**. Te dwa
przypadki definiuja jej minimalny, najtanszy wariant:

- **Wejscie:** pozycja czerwona z klasa "widok niejednoznaczny / wykaz podejrzany";
  system pokazuje PNG calego arkusza z PONUMEROWANYMI ramkami klastrow-kandydatow
  (z pomiarami: bbox, skala, otwory, giecie).
- **Czlowiek:** klika/zakresla wlasciwa ramke (jak w 797: czerwone kolko na PNG —
  dowod, ze operatorowi to wystarcza) LUB podaje nr kandydata. NIE rysuje DXF.
- **System:** tnie widok z tego bbox istniejacym silnikiem (W-C region+warstwa),
  skaluje wg zmierzonej skali standardowej, przechodzi PELNE bramki 1-9 (czlowiek
  wskazal WIDOK, nie zatwierdzil GEOMETRII — kontrola zostaje).
- **Nauka:** para (arkusz, zaznaczenie) -> `nauka/etykiety/` + golden; to przyszly
  trening automatycznego wyboru widoku.
- Koszt czlowieka: sekundy (kliecie) zamiast minut (rysowanie od zera w CAD) —
  wprost zasada 3 i metryka zaufania.

Status: **wniosek-do-wdrozenia** (nowy mechanizm; 797 dostarcza gotowy format
wejscia/wyjscia). 652 po poprawieniu wykazu tez laduje w tej sciezce, dopoki
detektor z wniosku A nie awansuje.

## 4a. WNIOSEK D — sygnal tekstowy kategorii 4: adnotacja giecia WEWNATRZ konturu

**Regula ogolna:** TEXT/MTEXT pasujacy do wzorcow giecia (DE/EN, case-insensitive):
`alle Kantungen ... oben`, `all bendings up`, `bend up 90`, `n.oben k.`, `Kantung`,
`Biegung`, `gekantet` — ktorego punkt wstawienia lezy **WEWNATRZ bbox klastra-kandydata**
— oznacza jednoczesnie:
- (a) **element JEST giety** -> spodziewaj sie linii giecia kolor 6; wymiar wykazu
  traktuj jako potencjalnie nominalny/zlozony (laczy sie z wnioskiem B i propozycja
  `2026-07-07_bramka1_giete_wyjatek_additive.md`);
- (b) **ten klaster to ROZWINIECIE do palenia** -> preferuj go nad izometria /
  rzutem bocznym / pogladem, ktore tej adnotacji w srodku nie maja.

Dowod pomiarowy: 3142 (2 adnotacje, kazda wewnatrz bbox "swojego" rozwiniecia
51/52), 652 (adnotacja wewnatrz bbox rozwiniecia 51). Przewaga nad geometria:
napis jest jednoznaczny tam, gdzie proporcje/kontur myla (3142: kontur otwarty
przez kolnierze, a adnotacja i tak potwierdza wlasciwy widok). **Ograniczenie:**
bywa rozbity na linie (797) — sygnal DODATKOWY (additive) do wniosku A, nie jedyny.

Status: **wniosek-do-wdrozenia** — naturalne miejsce: kategoria 4 (adnotacje
tekstowe, `produkcja/silniki/v2/kategorie`, opt-in wg rejestru), jako booster
rankingu kandydata + ustawienie flagi "gieta" dla oceny wymiaru.

## 4b. WNIOSEK E — falszywe czerwone bramki 2 na czesciach gietych (naciecia, kolnierze)

Przypadek pozytywny: **SL40685913_p1** ("ZWISCHENRAHMEN", rama gieta z zakladkami).
System: czerwony "OTWARTY KONTUR (brud=4)". Operator: *"wyglada dobrze zrobiony —
bo sa naciecia; i naciecia wypalamy"*. Pomiar (wariant wA):
- 894.10 x 214.10 (wykaz 894x214 OK), 16 ARC = 8x R6/180 st. (konce szczelin)
  + 8x R10/90 st. (narozniki), 0 CIRCLE, zadnego luku ~270 st. (to NIE gwint);
- **wierzcholki nieparzystego stopnia: 0 przy tol 0.01 mm i 0 przy tol 0.1 mm** —
  geometrycznie kontur jest DOMKNIETY; "brud=4" bramki liczyl inaczej (do
  wyjasnienia przy wdrozeniu), ale detal jest poprawny.

**Regula ogolna:** NACIECIE = intencjonalna szczelina/odciecie wchodzace w material
od krawedzi (typowo odciazenie przy narozniku giecia zakladki) — **laser je wypala,
to czesc detalu, nie defekt**. Dolacza do znanej listy falszywych czerwonych
bramki 2: luk gwintu ~270 st. (`kontekst/wiedza/gwint-okrag-luk-dimension.md`),
linia fazowania (`produkcja/kontrola/fazowanie.py`), kolnierz "bend up".
Sygnatura odrozniajaca od REALNEGO otwartego konturu:
- naciecie: dwa bliskie, ~rownolegle konce TUZ przy obrysie (krotka szczelina);
  przy tolerancji domkniecia realnej geometrii czesto znika (0 nieparzystych);
- realny brak: dziura w obrysie (duzy fragment bez geometrii) — NIE znika przy
  zadnej rozsadnej tolerancji.
Meta: na czesciach GIETYCH (rozpoznanych po adnotacji z wniosku D LUB linii giecia
kolor 6) czerwony Z SAMEGO otwartego konturu wymaga rozroznienia naciecie/kolnierz
(OK, ciete/giete) vs realny brak obrysu (defekt).

**Regula statusu (operator: "naciecia na przynajmniej zolto moga byc"):**
- otwarte konce z sygnatura naciecia/kolnierza -> **ZOLTY MINIMUM, nigdy zielony
  automatem** (nie mamy pewnosci naciecie vs realny brak — nie zgadujemy, zasada 1)
  i **nie twardy czerwony** (nie blokowac poprawnego detalu);
- mechanizm = FLAGER zgodny z zasada 5: **degraduje twardy czerwony (bramka 2)
  -> zolty** z jawnym powodem "wykryto naciecie (cieta cecha) — potwierdz";
  NIGDY nie podnosi do zielonego. Analogia 1:1 do propozycji giete-additive
  (degradacja czerwony->zolty, baza nienaruszona) i fazowania (zolty z powodem);
- to samo dla kolnierza "bend up" dajacego otwarte konce: zolty do potwierdzenia;
- **realny brak duzego fragmentu obrysu** (nie znika przy tolerancji, brak
  sygnatury naciecia/kolnierza) -> **zostaje czerwony** (twarda bramka);
  niepewnosc klasyfikacji -> zolty, nie zielony;
- petla nauki: czlowiek oglada zolte, potwierdza naciecia, jego OK -> etykieta
  (`nauka/etykiety/`).

Status: **wniosek-do-wdrozenia** (klasyfikator otwartych koncow w bramce 2 /
raporcie: naciecie-podejrzenie vs realny brak). SL40685913_p1 = pozytywny golden:
oczekiwany status ZOLTY (nie twardy czerwony, nie zielony automatem).

## 5. Co JUZ dziala (uczciwie)

- Bramka 2 (otwarty kontur) i kontrola proporcji ZATRZYMALY oba bledne warianty:
  652 i 797 wyszly czerwone z jawnym powodem, nic nie poszlo na laser. Wnioski
  NIE naprawiaja dziury bezpieczenstwa — podnosza AUTOMATYZACJE (mniej rysowania
  recznego, wieksza szansa na dobry wariant za pierwszym razem).
- Bramka 6 (rozklad dlugosci/katow) ma juz wlasciwy sygnal (ortho_frac 0.25 vs 1.0)
  — wniosek A to jej uzycie WCZESNIEJ (ranking kandydatow), nie nowa matematyka.

## 6. Kryteria akceptacji (golden)

1. **Regresyjne (dziala DZIS, chroni przed pogorszeniem):** pipeline na obu conv
   NIGDY nie oddaje tych pozycji jako zielone/zolte z obecnym zlym widokiem —
   status czerwony/do czlowieka. (652: zaden wariant z otwartym konturem nie
   przechodzi; 797: j.w.)
2. **Docelowe wniosku A (po wdrozeniu detektora):** detektor rozwiniecia wskazuje
   na SL10582652 klaster warstwy 51 (280.00x41.98, skala 2.0 -> 560.0x83.96;
   tolerancja 0.5 mm vs wzorzec czlowieka) i na SL10582797 klaster warstwy 51
   (14.88x104.93, skala 5.0 -> ~74.4x524.7; oba wymiary wykazu 76x527 w tolerancji
   bramki 1), a klastry z ELLIPSE>0 lub otwartym konturem NIE wygrywaja rankingu.
3. **Docelowe wniosku B:** dla 652 raport zawiera powod "wykaz podejrzany"
   z konkretem (84 OK przy 1:2, 720 nieobecne na rysunku); pozycja NIE jest zielona.
4. **Docelowe wniosku C:** po recznym wskazaniu bbox rozwiniecia (z zaznaczenia PNG)
   pipeline tnie i oddaje DXF zgodny geometrycznie ze wzorcem czlowieka
   (652: 560.00x83.96, 5 konturow wewn., 1 linia giecia na warstwie GIECIE,
   0 otwartych koncow) i przechodzi bramki.
5. **Docelowe wniosku D:** detektor tekstowy na SL10583142 znajduje 2 adnotacje
   "alle Kantungen..." i przypisuje je klastrom warstw 51 i 52 (punkt wstawienia
   wewnatrz bbox); na 652 znajduje 1 i przypisuje klastrowi warstwy 51; na 797
   zwraca 0 (adnotacja rozbita) — bez falszywego trafienia.
6. **Docelowe wniosku E:** SL40685913_p1 dostaje status ZOLTY z powodem
   "naciecia (cieta cecha) — potwierdz" zamiast twardego czerwonego; detal
   z realnie wycietym fragmentem obrysu (kontrprzyklad syntetyczny lub z golden
   SL40034116) ZOSTAJE czerwony. Zaden detal nie awansuje do zielonego automatem.
