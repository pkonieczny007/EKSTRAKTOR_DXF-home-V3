# Kontrola wyniku: karta kontrolna z liczbami; jeden znaleziony blad NIE konczy ogledzin

**Skad:** test zlecenia (SL10596945 p3, 2026-07-04). AI znalazlo duble okregow
(Ø13+Ø14,7) i uznalo kontrole za skonczona, piszac o fasoli "prawdopodobnie brakuje"
BEZ sprawdzenia. Brak dolnej fasoli wskazal dopiero CZLOWIEK na miniaturach.
Bramka 6 flagowala w qc_powody zgubione giecie - nieprzeczytane.

**Why (dlaczego to grozne):** blad "satysfakcji ze znaleziska" - pierwszy wykryty
problem konczy szukanie, a najgrozniejsze braki (kontury wewnetrzne) nie psuja ani
wymiaru, ani pierwszego wrazenia. Duble okregow MASKUJA brak w surowym liczniku
(stary wynik: 5 "konturow" surowo, 3 po dedupie; zrodlo: 4) - bilans na surowych
encjach klamie w obie strony.

**How to apply (karta kontrolna - werdykt dopiero po wypelnieniu WSZYSTKICH pol):**
1. KONTURY WEWNETRZNE zrodlo-region vs wynik - liczby, PO DEDUPIE okregow wspolsrodkowych.
2. Okregi: ile grup wspolsrodkowych zdedupowano (raw -> po dedupie).
3. Giecie: liczba encji koloru 6 w zrodle vs encji na warstwie GIECIE w wyniku.
4. qc_powody z raportu PRZECZYTANE (kazda zolta pozycja ma powod - to nie dekoracja).
5. Ogledziny renderu wynik vs zrodlo (para PNG) - dopiero PO liczbach.
Zakaz slowa "prawdopodobnie" w werdykcie: albo liczby+render, albo status DO_SPRAWDZENIA.

**Metoda operatora (reczny wzorzec = silnik W-C):** zlokalizuj widok, zaznacz caly
region; geometria czesci jest na JEDNEJ warstwie (tu: 53) -> kopiuj WSZYSTKO z tej
warstwy (fasole nie znikaja). Wariant: kontur jest BIALY (kolor 7) -> zaznacz po
kolorze bialym, dodaj linie giecia (kolor 6), potem skaluj.

Powiazane: [[cechy-odseparowane-region-warstwa]], [[otwory-wspolsrodkowe-zdublowane]],
[[giecie-kiedy-nanosic-pl-skos]]. Golden: testy/golden/SL10596945_fasola_odseparowana/.
