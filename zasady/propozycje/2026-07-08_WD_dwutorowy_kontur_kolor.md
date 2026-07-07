# Propozycja: silnik W-D — metoda DWUTOROWA operatora (kontur zewnętrzny → kolor bazowy → skan reszty)

- **Data / autor:** 2026-07-08, operator (opis metody własnej) + AI (spisanie)
- **Status:** propozycja → prototyp (fable-advisor, scratchpad) → golden → testy → benchmark
  W-D vs W-C → opt-in czwarty wariant w `config/warianty.yaml` (bramka 10: 4. głos)
  → potwierdzenie operatora → merge. NIE dotyka istniejących silników (zasada 8/9).

## Problem, który rozwiązuje

- W-A/W-B (klaster po gap): przynależność otworu = ODLEGŁOŚĆ od sąsiadów → cechy
  odseparowane >gap wypadają (54_4867; SL40034116: −13 Langlochów), wymiar-bbox ślepy.
- W-C (bbox + jeden tryb): nie gubi w bbox, ALE (a) prostokąt ≠ kontur → brud z tabelek/
  sąsiadów; (b) JEDEN tryb koloru → pojedynczy otwór INNEGO koloru wypada (przypadek
  operatora: „część elementów biało/fioletowa, a pojedynczy element żółty");
  (c) spłaszcza gięcie (0 linii kol.6 w wyniku — reguła giecie-warstwa-GIECIE).

## Metoda dwutorowa (słowa operatora, 2026-07-08; korekta: bbox NA ETAPIE GEOMETRII)

> Korekta operatora: „na etapie GEOMETRII też chcę brać bbox — nie możemy brać konturu
> na tym etapie. Znajdujemy wymiary zewnętrzne, KOPIUJEMY CAŁOŚĆ, a dopiero potem przy
> czyszczeniu skupiamy się na kształcie. Nie możemy bbox za szybko odrzucić."
> Czyli: bbox = hojna siatka zbierania (zawsze działa), kontur = filtr CZYSZCZENIA.

**TOR 1 — GEOMETRIA (wymiary zewnętrzne; bbox):**
1. Szukamy geometrii i określamy ją przez BBOX (konturu jeszcze nie znamy — różne
   przypadki: otwarte obrysy, segmenty łukowe itd.; bbox działa zawsze).
2. Wymiary zewnętrzne bboxa porównujemy z wykazem PO przeskalowaniu (wykaz = BAZA,
   [[wykaz-to-baza-additive]]).
3. **KOPIUJEMY CAŁOŚĆ z bboxa** (hojnie, z marginesem) — nic nie odrzucamy na tym etapie.

**TOR 2 — CZYSZCZENIE I SZCZEGÓŁY (dopiero tu kontury/kształt):**
4. Na skopiowanym zbiorze budujemy kontur zewnętrzny (polygonize → pierścień).
5. Badamy KOLOR, z jakiego jest określona krawędź obrysu → kolor bazowy.
6. Zostaje: obrys + WSZYSTKIE wewnętrzne kontury koloru bazowego WEWNĄTRZ pierścienia
   (przynależność = point-in-polygon, NIE odległość/gap) + gdy trzeba linie gięcia
   (kol.6, wg reguł P/L / skos; na warstwę GIECIE — nie spłaszczać).
7. **UWAGA-pass:** czasami otwory są INNEGO koloru → zawsze sprawdzamy, czy nie ma
   innych ZAMKNIĘTYCH krawędzi wewnątrz obrysu. Znalezione → DOŁĄCZ + uwaga w raporcie
   + zaznaczenie na PNG (skrypt porównuje; nigdy cicho). Baza = obrys + wnętrze
   z koloru bazowego; reszta = dodatek flagowany.
8. Obce z bboxa (tekst/tabelka/sąsiad POZA pierścieniem) odpadają dopiero TERAZ,
   w czyszczeniu — nie na etapie zbierania.
9. **Warstwa jako wsparcie** (sygnał pomocniczy, nie twardy): bywa poz.1→warstwa 51,
   poz.2→warstwa 102 itd. (numery nie zawsze odpowiadają); typ „biały rzut + fioletowe
   gięcie". Stare rysunki: WSZYSTKO na warstwie 1 → zostaje sam kolor. Zależne od TYPU
   rysunku (typowanie dostraja, nie ogranicza — decyzja 06.07). Etap czyszczenia
   celowo NIE jest sztywno wyspecyfikowany — różne przypadki; niepewność = flaga.

## Różnice vs W-C (sedno)

| | W-C | W-D (propozycja) |
|---|---|---|
| zbieranie | bbox + jeden tryb | bbox HOJNIE, całość (jak W-C — bbox nie odrzucany za szybko) |
| czyszczenie | brak (co zebrał, to oddał) | osobny etap: kontur zewn. → kolor bazowy z krawędzi → point-in-polygon |
| kolory | jeden tryb (czysty) | kolor bazowy Z KRAWĘDZI OBRYSU + skan innych kolorów z UWAGĄ |
| gięcie | spłaszcza (luka) | przenosi na GIECIE wg reguł |
| obce w bbox (tekst/tabelka/sąsiad) | brud (dyskwalifikacja/flagi) | odpada w CZYSZCZENIU (poza pierścieniem) |

## Przykłady referencyjne (golden)

- `SL40034116_p1_zgubione_otwory` — 38 konturów wewn. na warstwie 51 (klaster zgubił 13).
- `SL40061302_sloty_odseparowane` — kolor bazowy 2 (nie 7), wszystko na warstwie '1'
  (stary typ: sam kolor, warstwa nie pomoże).
- ⬜ DO UZUPEŁNIENIA: rysunek z pojedynczym ŻÓŁTYM otworem wśród geometrii biało-
  fioletowej (operator wskaże) — test UWAGA-passu (pkt 6).

## Kryterium awansu (zasada 8/10/11)

Prototyp (scratchpad, fable) → pomiar na golden: W-D odtwarza komplet konturów
(38/38, 3/3 sloty) + UWAGA-pass łapie otwór obcego koloru + 0 obcych encji spoza ringu
→ testy (`test_wd.py`) → benchmark W-D≥W-C na rysunkach regresji (0 regresji) →
opt-in w `config/warianty.yaml` → potwierdzenie operatora. Ryzyka: (a) otwarte obrysy
(kołnierze/nacięcia) = polygonize nie da ringu → W-D uczciwie pasuje (fallback W-C),
nie zgaduje; (b) pętla obcego koloru wewnątrz ringu może być adnotacją (dymek) —
dlatego DOŁĄCZ+UWAGA+zaznaczenie, decyzja u człowieka (zasada 5/6).
