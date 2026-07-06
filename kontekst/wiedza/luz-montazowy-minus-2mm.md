# Luz montazowy - operator zmniejsza czesc o ~2 mm wzgledem wykazu

**Zrodlo:** operator, 24_0417 SL10217547 p5/p11/p12 (2026-07-07).

Dla czesci, ktore musza WEJSC w zlozenie (np. zebra wchodzace w wyciecia), operator
**RECZNIE zmniejsza wymiar o ~2 mm** wzgledem nominalu z wykazu - to **luz montazowy**,
zeby elementy latwiej weszly. Przyklad: wykaz 212x52, na laser (reczny wzorzec) 210x50.

## Implikacje

- **Wykaz nominalny != wymiar na laser** dla czesci z luzem. Reczny DXF operatora
  (mniejszy o ~2 mm) jest tu "prawda" na laser, nie nominal wykazu.
- Pipeline dopasowuje do NOMINALU wykazu (212x52) -> daje wymiar wiekszy o luz. To NIE
  blad ekstrakcji - to brakujacy reczny krok montazowy. Pipeline nie wie, ktore czesci
  wymagaja luzu (decyzja montazowa/czlowiek).
- **Nie mylic z rozjazdem realnym:** ~2 mm systematyczny, w OBU wymiarach, ksztalt+cechy
  identyczne = luz. Wieksza/asymetryczna roznica = realny problem do ogledzin.
- Docelowo: pipeline moze FLAGOWAC "sprawdz luz montazowy" (nie auto-odejmowac).

## Pulapka pomiarowa (przy porownaniu z recznym wzorcem)

Reczne DXF operatora bywaja z ODPIETYMI encjami (np. krotka linia koloru 15 ~100 mm pod
czescia w SL10217547 p4 -> bbox 164.6 zamiast realnych 65). Porownujac wymiary z recznym
wzorcem: liczyc bbox NAJWIEKSZEGO klastra / ignorowac odosobnione encje, inaczej falszywy
"rozjazd". [[cechy-odseparowane-region-warstwa]] (odwrotny problem - realne cechy odseparowane).
