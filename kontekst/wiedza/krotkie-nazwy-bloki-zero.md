---
name: krotkie-nazwy-bloki-zero
description: "Rysunki o krotkich nazwach (bez SL) - zero wiodace w pliku, geometria w blokach INSERT, niemieckie linetypy"
metadata: 
  node_type: memory
  type: project
  originSessionId: 968ce1f5-7363-4270-b157-e1aba3716d08
---

Pozycje o KROTKICH nazwach rysunku (bez prefiksu SL, np. Zeinr=55648) maja kilka pulapek:

1. **Zero wiodace w nazwie pliku**: wykaz ma Zeinr "55648", a plik to "055648.dxf".
   load_wykaz filtruje `zeinr in str(r[Zeinr])` -> "055648" NIE pasuje do "55648".
   Trzeba zmapowac recznie (strip zera / dopasowac po koncowce).
2. **Geometria w blokach INSERT**: caly rysunek bywa same INSERT-y (engine je ignoruje
   jako adnotacje -> "NIE ZNALEZIONO"). Rozbic: `ins.virtual_entities()` do nowego msp.
3. **Niemieckie linetypy**: AUSGEZOGEN=ciagla(kontur), MITTE=os, VERDECKT=ukryta.
   Engine AXIS_LINETYPES nie zna MITTE -> doda osie do konturu. Pomijac MITTE recznie.
4. Rysunek bywa w skali 1:1 (klaster od razu = wymiar z wykazu, skala 1.0).

Giecie tu = magenta (kolor 6), ale UWAGA: krzyz osi otworu tez bywa magenta+MITTE.
Odrozniac po dlugosci: linia giecia idzie przez cala czesc (L >= ~0.6*min wymiar),
krzyz osi jest krotki. Patrz [[giecie-phantom-kolor6]].

Przyklad: 59_6940, 055648.dxf, poz. 55648_p1 (190x40) -> wyciagniete recznie.
