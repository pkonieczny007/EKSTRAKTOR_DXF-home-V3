# Propozycja: OTWARTY KONTUR na drogiej blasze -> osobny folder DO_CZLOWIEKA (nie domykac automatem)

- **Data / autor:** 2026-07-07, operator (decyzja na 38_1847 gr5 / SL40034116) + AI (spisanie)
- **Status:** propozycja -> golden (SL40034116_p*) -> flager+routing (fable-advisor) -> testy -> merge
- **Zastepuje kierunek:** wczesniejszy pomysl AUTO-DOMYKANIA konturow kolnierzy (audyt 2026-07-06,
  P2 pkt 10) - operator go ODRZUCIL: za drogo, nie zgadujemy.

## Decyzja operatora (wiazaca)

> "Otwarte kontury to pewnie gwinty w hardoxach. Stworzymy osobny folder, wrzucacie
> propozycje i sprawdza czlowiek, bo to drogie blachy."

NIE budujemy automatu domykajacego kontur cięcia. Blacha odporna na scieranie (Hardox) i
grube blachy (s=12) sa drogie - wypalony blednie detal = duzy koszt materialu. Zasada 1
(nie zgadujemy geometrii) ma tu absolutny priorytet nad automatyzacja. Pozycja z realnie
otwartym konturem trafia do CZLOWIEKA, nie na laser.

## Co pokazaly dane (uczciwie, zmierzone)

- SL40034116 (38_1847 gr5) = zrodlo 28x🔴. Tekst rysunku: **"90 n.oben k. / bend up 90"**
  (odginane KOLNIERZE) + "Blech s=5 / s=12" (blacha 5 i 12 mm) + "spiegelbildlich" (lustro).
  Otwarte konce pochodza tu z KOLNIERZY (linie odgiecia doklejone do obrysu = T-zlacza),
  nie potwierdzono gwintow na tym rysunku.
- Hipoteza operatora "gwinty w hardoxach" - do WERYFIKACJI (fable-advisor): gwint =
  okrag wiercenia + wspolsrodkowy luk ~270 + DIMENSION "M.." ([[gwint-okrag-luk-dimension]]);
  luk ~270 to NIE otwarty kontur, ale bramka 2 moze go FALSZYWIE flagowac. Trzeba rozbic
  28x🔴 na: (a) gwinty = falszywy alarm bramki 2 (zbic deterministycznie), (b) realne
  otwarte kontury kolnierzy = DO CZLOWIEKA.

## Tresc zasady (czytelna dla czlowieka)

1. **Rozroznienie zrodla otwartego konca** (deterministyczne, flager - fable):
   - luk gwintu ~270 (okrag wspolsrodkowy + DIMENSION "M..") -> NIE defekt, bramka 2 nie liczy;
   - realny otwarty obrys / kolnierz (bend up) -> defekt do czlowieka.
2. **Rozpoznanie DROGIEJ blachy:** gatunek **HB400 / HB450** (twardosc Brinella Hardoxa;
   operator SPRAWDZIL 2026-07-07 - takie Hardoxy miewaja gwinty) lub "Hardox" z nazwy/wykazu
   LUB duza grubosc (np. s>=10 mm) -> podnosi priorytet recznego sprawdzenia. UWAGA:
   SL40034116 to NIE Hardox (zmierzone: brak HB400/HB450, s=5/s=12, otwarty kontur z KOLNIERZA)
   - Hardox-z-gwintem to osobny rownolegly przypadek. Zmierzyc gatunek, nie zakladac.
3. **Routing zamiast domykania:** pozycja z realnie otwartym konturem NIE jest zapisywana
   jako gotowa (🔴), tylko kopiowana do OSOBNEGO FOLDERA `wyniki/<zlecenie>/DO_CZLOWIEKA/`
   z: PNG zrodla + PNG wyniku, powodem ("otwarty kontur - mozliwy gwint/kolnierz, blacha
   s=.. gatunek.., sprawdz recznie"), liczbami (ile otwartych koncow, wspolrzedne). Czlowiek
   rysuje/potwierdza; gotowy plik -> golden (zasada 11).
4. **Flager, nie automat podnoszacy status** (zasada 5): moze tylko skierowac do czlowieka,
   nigdy oznaczyc jako 🟢. Osobny folder = jawna kolejka drogich pozycji do decyzji.

## Folder DO_CZLOWIEKA - konwencja

`wyniki/<zlecenie>/DO_CZLOWIEKA/<zeinr>_p<N>/`:
- `zrodlo.png`, `wynik.png` (czarne tlo), `powod.txt` (liczby + gatunek + grubosc),
- kopia problematycznego DXF (do reki jako baza), miejsce na `reczny.dxf` operatora.
Poza gitem (jak wyniki/, zasada 14). Podsumowanie kolejki -> wejscie do galerii przegladu.

## Kryterium awansu (zasada 8/10/11)

Golden SL40034116_p* (rozbicie gwint/kolnierz z liczbami) -> flager+routing (nowy modul
`produkcja/kontrola/otwarty_kontur.py` lub rozszerzenie bramki 2) za testem -> regresja +
benchmark_v3 0 regresji (pozycje z zamknietym konturem BEZ zmian; gwinty przestaja falszywie
czerwienic) -> potwierdzenie operatora -> merge. Ryzyko: nie skierowac do czlowieka pozycji
poprawnych (falszywy routing = zjada zysk) ani nie przepuscic realnego otwartego konturu.
