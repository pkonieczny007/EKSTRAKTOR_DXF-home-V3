---
name: technologia-schweissgruppe-auto
description: "Technologie G/GS/S/brak da sie wyliczyc automatycznie z DWG: spaw = tekst 'Schweissgruppe' w rysunku, giecie = linie kolor6 w zrodle"
metadata:
  type: project
---

Zlecenie 54_4867. Kolumna technologia_rysowanie (G=giecie, GS=giecie+spaw,
GSO=+obrobka, S, SO, O). Da sie wyliczyc automatycznie z conv.dxf:

- **spaw?** = w tekstach (TEXT/MTEXT) rysunku wystepuje "Schweissgruppe" /
  "Welding group" (grupa spawalnicza). Sprawdzone 100% trafnie: SL10596945,
  SL40051412, SL40071953, SL10599245 = grupy (spaw); SL41263007 (skrecane),
  SL10596953 (nitowane) = bez.
- **giecie?** = obecnosc linii kolor6 w bbox widoku zrodla.
- regula: giecia+spaw -> **GS**; giecia bez spaw -> **G**; plaski+spaw -> **S**;
  inaczej -> **brak** (plaski, tylko wypalanie).

**Wyjatki (nie z tekstu):**
- pojedyncza czesc spawana **symbolem spoiny** bez grupy (np. SL10600635 = plyta
  + przyspawany pret, GS) - nie wykryje "Schweissgruppe", trzeba TIF.
- **GSO/SO/O (obrobka)** - niewykrywalne z DXF, wymaga TIF/technologa.
- "Schweissnahtvorbereitung / Welding seams" w tabelce to BOILERPLATE na KAZDYM
  rysunku (jest tez na plaskiej listwie) - NIE liczyc jako spaw.
- element plaski bez G/S/O -> wpisujemy "brak" (nie "-", nie puste).

**Why:** unika czytania TIF-a dla kazdej pozycji; GS vs G to inny gniot i wycena.
**How to apply:** funkcja has_weld(z) = "schweissgruppe" in tekst.lower(); tech z
(has_weld, ma_giecia). Weryfikacja spornych (pojedyncze spawy, obrobka) z TIF.
