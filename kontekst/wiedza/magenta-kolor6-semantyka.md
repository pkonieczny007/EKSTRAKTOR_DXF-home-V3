# Semantyka koloru 6 (magenta/fioletowy) - NIE zakladac jednego znaczenia

**Zrodlo:** operator, 38_1847 gr6 (2026-07-07). Konsoliduje rozproszona wiedze.

Kolor 6 (magenta) w rysunkach tego klienta ma KILKA roznych znaczen. **Nie zakladac
semantyki bez ogledzin calego arkusza i typu rysunku** - ta sama encja magenta moze byc:

1. **Linia giecia** (rozwiniecie/flat pattern) - linia w POPRZEK czesci, tam gdzie sie ja
   gnie. Nanosic tylko dla par P/L albo giecia pod skosem; na warstwe GIECIE, NIE ciac.
   Szczegoly: [[giecie-phantom-kolor6]], [[giecie-kiedy-nanosic-pl-skos]].
2. **Dospawywany element** (widok zlozeniowy) - inna czesc stykajaca sie z konturem,
   pokazana bo sie ja dospawuje. NIE ciac; wskazuje, ze zlapano widok zlozeniowy zamiast
   do palenia. Szczegoly: [[widok-zlozeniowy-vs-do-palenia]].
3. **Element POZA rysunkiem** (kontekst/otoczenie) - geometria narysowana zeby pokazac
   sasiedztwo/kontekst, NIE nalezaca do tej czesci. Wystepuje na widokach zlozeniowych i
   INNYCH typach rysunkow. NIE ciac, wykluczyc z ekstrakcji. (operator 07.07)

## Regula zbiorcza (na laser)

Magenta (kol.6) to zwykle **NIE kontur ciecia tej czesci**. Wyjatek: linia giecia na
rozwinieciu (rysowana, ale idzie na warstwe GIECIE, nie ciecie). Przy ekstrakcji: magenta
traktowac swiadomie wg TYPU RYSUNKU i widoku - giecie -> GIECIE/pomin; dospawienie /
element poza rysunkiem -> wyklucz. Rozstrzyga widok + ogledziny, nie sama encja.

## UWAGA: fazowanie to NIE magenta

Fazowanie (chamfer) rysowane jest kolorem GEOMETRII (kol.7), rownolegle do krawedzi -
osobny przypadek: [[fazowanie-linia-przy-krawedzi]]. Nie mylic z magenta.
