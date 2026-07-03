---
name: sbm-okragle-niewyciagalne
description: "Rysunki SBM sit okraglych (rodzina, tabela a[mm]) - plaszcze zwiniete i kola osiowe nie sa auto-ekstrahowalne"
metadata: 
  node_type: memory
  type: project
  originSessionId: 968ce1f5-7363-4270-b157-e1aba3716d08
---

Na zleceniach SBM (np. 49_3776 przesiewacz) czesc pozycji ZAKUPY=blacha NIE jest
auto-ekstrahowalna mimo zgodnego bbox - test wymiaru sprawdza tylko bounding box,
nie jakosc konturu. Typy do recznej obrobki przez operatora:

1. **Plaszcz zwiniety (Mantel)**: pozycja o proporcjach paska (np. 1722x110, 732x460),
   gdzie dluzszy bok ~= obwod kola (1722 ~= pi*560). Narysowany TYLKO po zwinieciu
   (jako kolo / w przekroju), brak rozwiniecia plaskiego. = pulapka #5 z CLAUDE.md.
   Przyklady: SL10125910_p2, SL10125935_p2, SL10130021_p4.
2. **Rysunek wariantowy/tabelaryczny**: tabela "a [mm]" z wieloma nr czesci -> geometria
   schematyczna, wymiary nominalne bez konturu do skali. Przyklad: SL10125910 (czesci
   nie ma nawet w tabeli na rysunku).
3. **Kolo osiowe/podzialowe segmentowane**: "pierscien" zlozony z ~230 krotkich
   odcinkow (faceted), open_ends>0, renderuje sie prawie pusto -> NIE kontur ciecia.
   Przyklad: SL10125935_p3 (560x560) -> oznaczone _DO_SPRAWDZENIA.

QC po ekstrakcji: liczyc encje + srednia dlugosc LINE + open_ends. Duzo krotkich
odcinkow albo <3 encje = falszywy trafik. Patrz [[sbm-legenda-lustro]].
