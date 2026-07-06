---
name: gwint-okrag-luk-dimension
description: "Gwint = okrag (wiercenie) + wspolsrodkowy LUK wiekszego Ø (~270 st) + DIMENSION z tekstem 'M<n>'; zostaw OBA, opisz w wykazie M10, srednica wiercenia wg tabeli (M10->8.5); luk gwintu NIE jest wada konturu"
metadata:
  type: project
---

Zlecenie 38_1847, SL40852200_p1 (operator, 2026-07-05). Otwor gwintowany rysowany jako
para wspolsrodkowa **OKRAG + LUK** (NIE dwa okregi - to inne niz fertzing!):
- **OKRAG Ø8.5** (kolor 7, warstwa geometrii) = otwor wiercony pod gwint,
- **LUK Ø10, rozpietosc ~270 st** (75->345) = symbol gwintu (klasyczne 3/4 okregu).

**Sygnal tekstowy (kluczowy - "przy tego typu rysunkach jest opis gwintu"):** nominal
gwintu stoi jako **DIMENSION z nadpisanym tekstem `"M 10"`** (kolor 2, jak wymiary) -
NIE zwykly MTEXT (dlatego grep po TEXT/MTEXT go nie lapie; szukac w DIMENSION.dxf.text).
Obok bywa `"R 10"`. Sloty na tych rysunkach maja opis `LL<w>x<h>` (Langloch, np.
LL12x20 = otwor podluzny 12x20).

**Why:** gwint to jedna cecha technologiczna, nie dwa wyciecia. Do lasera zostaje otwor
przelotowy o srednicy WIERCENIA wg tabeli (M10 -> 8.5 mm), a nie nominal 10. Trzeba to
oznaczyc w wykazie, bo srednice zmienia sie recznie (pozniej auto) wg tabeli gwintow.
Dwie pulapki: (1) dedup wspolsrodkowych z [[otwory-wspolsrodkowe-zdublowane]] dotyczy
okrag+OKRAG (fertzing -> najmniejszy); gwint to okrag+LUK, wiec **NIE dedupowac, zostawic
oba**. (2) Luk gwintu ~270 st jest z definicji OTWARTY - bramka 2 / bilans_konturow
(count_interior_contours_shapely) bierze go za NIEDOMKNIETE i falszywie flaguje detal
jako "otwarty kontur, nie na laser". W SL40852200 te 2 "otwarte konce" to DOKLADNIE dwa
konce luku gwintu - detal jest KOMPLETNY.

**How to apply:**
1. Wykryj kandydata gwintu: CIRCLE + ARC wspolsrodkowe (tol srodka 0.5 mm), R_luku > R_okregu,
   luk niepelny (rozpietosc < 360, typowo ~270). Srodek CIRCLE zawsze OCS->WCS (lustro).
2. Odczytaj nominal z DIMENSION zawierajacego `M\s?\d+` (np. "M 10") - autorytatywny;
   geometria (okrag=wiercenie, luk=nominal) potwierdza.
3. Wykaz kolumna uwagi: `M10` + "gwint". Srednica wiercenia wg tabeli (M10->8.5, M8->6.8,
   M6->5.0, M12->10.2...); zmierz istniejaca srednice, zapisz, popraw jesli != tabela.
4. Ekstrakcja: zostaw OKRAG i LUK (W-C je zostawia - CIRCLE i ARC to rozne typy, nie dedup).
5. Kontrola: luk gwintu wykluczyc z testu NIEDOMKNIETE (inaczej kazdy detal z gwintem = 🔴).
   Do awansu: bramka 2 / bilans_konturow ma byc "swiadoma gwintu".

Propozycja poprawki bramki 2 + wykrywania = zadanie dla fable-advisor (geometria/topologia).
