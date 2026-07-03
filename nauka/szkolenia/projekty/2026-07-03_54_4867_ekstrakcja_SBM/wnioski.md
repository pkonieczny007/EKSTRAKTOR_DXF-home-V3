---
name: 54-4867-ekstrakcja-sbm-lekcje
description: "Zlecenie 54_4867 (SBM, 98 pozycji): zestaw regul dla V2 - zgubione cechy, tabelka, wspolsrodkowe okregi, giecia P/L/skos, auto-technologia, kontrola wymiarow, konwersja retry"
metadata:
  type: project
---

Zlecenie 54_4867 (SBM, przenosniki DB1200/FB-PBB). 98 pozycji `nazwa_rysowanie`,
43 rysunki. Wynik: 71 zielone / 26 zolte / 1 czerwony (33419 = rysunek blokowy
INSERT, inny CAD, do recznego), 96 gotowych DXF. Z tego zlecenia wyszlo 6 regul -
kazda ma osobna notatke w kontekst/wiedza/:

1. **Zgubione cechy odseparowane** (fasole, otwory-wyspy) i **tabelka zamiast
   rozwiniecia** - klaster po sasiedztwie zawodzi; root-fix = **region+warstwa** +
   liczniki kompletnosci (nakladka, licznik okregow, licznik konturow wewnetrznych
   `_licznik_konturow.py`). Realne trafienia na tym zleceniu: SL10596945_p3P (fasola),
   SL400521106_p1 (4 sloty), SL10600635_p1 (wachlarz vs tabelka).
   -> [[cechy-odseparowane-region-warstwa]]
2. **Podwojne/zdublowane okregi** - Ø13+Ø14.7 (przelot+poglebienie); zostaw najmniejszy.
   SL10596945 p3/p4, SL10602681. -> [[otwory-wspolsrodkowe-zdublowane]]
3. **Linie giecia - kiedy** - tylko P/L albo skos; nie-P/L proste bez linii.
   -> [[giecie-kiedy-nanosic-pl-skos]]
4. **Auto-technologia** - spaw z tekstu "Schweissgruppe" w DWG, giecie z kolor6;
   GS/G/S/brak. -> [[technologia-schweissgruppe-auto]]
5. **Konwersja GstarCAD retry** + **TIF tylko na czerwono w ostatecznosci**.
   -> [[konwersja-gstarcad-retry-tif-czerwono]]
6. **Kontrola wymiarow** w wykazie (kolumny wg 3.2.2 - dxf_reader.py): X-DXF/Y-DXF
   vs Abmess ±1, uwagi_wymiar = "ok" gdy obie PRAWDA. 95/98 ok; 3 nie-ok = brak DXF
   + 2 tarcze ~2% za male (do sprawdzenia srednicy).

**Why:** kazda z tych rzeczy przepuszcza na laser detal z brakujacym otworem/slotem,
zla srednica albo zla reka - czyli zlom. Kontrola samego wymiaru zewnetrznego tego
NIE lapi (kontur caly, cecha wewnetrzna znika).

**How to apply:** wdrozyc w V2: (a) tryb ekstrakcji region+warstwa jako auto-fallback
gdy licznik/nakladka wykryje brak; (b) skan wspolsrodkowych okregow jako bramka;
(c) regula giecia P/L-lub-skos w budowie DXF; (d) has_weld() z tekstu DWG do
technologii; (e) retry konwersji; (f) kolumny kontroli wymiarow. Pelna strategia
kompletnosci: zlecenia/54_4867_RYSOWANIE/UWAGI/strategia_kompletnosc_otworow.md.

Pokrewne: [[sbm-okragle-niewyciagalne]], [[sbm-legenda-lustro]], [[giecie-phantom-kolor6]].
