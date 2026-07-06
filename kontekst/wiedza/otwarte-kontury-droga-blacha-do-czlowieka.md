# Otwarty kontur na drogiej blasze -> DO CZLOWIEKA (nie domykac automatem)

**Zrodlo:** operator, 2026-07-07 (38_1847 gr5, SL40034116 = 28x🔴). Decyzja procesowa.

## Regula

Pozycja z REALNIE otwartym konturem cięcia na DROGIEJ blasze (Hardox / gruba s>=10 mm)
NIE idzie na laser i NIE jest domykana automatem. Trafia do osobnego folderu
`wyniki/<zlecenie>/DO_CZLOWIEKA/` z PNG + powodem + liczbami; **czlowiek rysuje/potwierdza**.
Blad na drogiej blasze = duzy koszt materialu -> zasada 1 (nie zgadujemy) ma priorytet
nad automatyzacja. Odrzucony pomysl auto-domykania kolnierzy (audyt 2026-07-06 P2.10).

## Skad biora sie otwarte konce (rozroznic PRZED decyzja)

1. **Kolnierz "bend up 90"** (SL40034116: tekst "90 n.oben k./bend up 90") - odgieta sciana
   rysowana jako linie doklejone do obrysu = T-zlacza = otwarte konce. REALNY otwarty
   kontur -> do czlowieka.
2. **Gwint** ~270 luk ([[gwint-okrag-luk-dimension]]) - okrag wiercenia + wspolsrodkowy luk
   dużego Ø + DIMENSION "M..". Luk ~270 to NIE otwarty kontur, ale bramka 2 potrafi go
   FALSZYWIE oflagowac. Zbic deterministycznie (nie kierowac do czlowieka bez potrzeby).
3. **Fazowanie** - linia rownolegla do krawedzi ([[fazowanie-linia-przy-krawedzi]]) - juz
   rozwiazane ([[magenta-kolor6-semantyka]] osobno: magenta = giecie/dospawienie, nie faza).

Dwa ROZNE zjawiska, oba daja otwarte konce - nie mylic:
- **SL40034116 (38_1847) = KOLNIERZ**, nie Hardox. Zmierzone: brak HB400/HB450/Hardox w
  tekscie i wykazie ("400" tam = numery czesci / wymiary, nie gatunek); blacha s=5/s=12.
  Przyczyna otwartych koncow = odgiecie "bend up 90".
- **Hardox HB400 / HB450 Z GWINTAMI = osobny przypadek** (operator SPRAWDZIL, 2026-07-07):
  takie drogie blachy miewaja gwinty; luk gwintu ~270 -> bramka 2 falszywie "otwarty
  kontur". Marker gatunku: **HB400 / HB450** (twardosc Brinella Hardoxa) w nazwie/wykazie/
  rysunku. NA SL40034116 tego NIE ma - to inny detal.

Zawsze ZMIERZYC zrodlo (gatunek, grubosc, przyczyne otwartego konca), nie zakladac.

## Jak stosowac

- Flager (nie automat, zasada 5): otwarty kontur -> rozroznij gwint/faza/kolnierz -> jesli
  realny otwarty obrys na drogiej blasze -> routing do `DO_CZLOWIEKA/`, status 🔴.
- Rozpoznanie drogiej blachy: gatunek **HB400 / HB450 (Hardox)** lub Hardox z nazwy/wykazu,
  ewentualnie duza grubosc s (tekst "Blech s=.." / kolumna wykazu). Zmierzyc.
- Konwencja folderu i kryterium awansu: `zasady/propozycje/2026-07-07_otwarte_kontury_droga_blacha_do_czlowieka.md`.
