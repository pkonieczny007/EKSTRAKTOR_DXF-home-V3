# Propozycja zasady: preferuj widok DO PALENIA nad ZLOZENIOWY (dospawywane elementy)

- **Data / autor:** 2026-07-07, operator (korekta na 38_1847 gr6) + AI (spisanie)
- **Status:** propozycja → golden `SL10585238_p1_widok_zlozeniowy/` PRZED naprawa (zasada 11)
  → testy → merge do rankingu widokow (`extract_positions.py` / `v2/kategorie`)

## Problem, ktory rozwiazuje

Rysunki spawanych zespolow (SBM) czesto maja na JEDNYM arkuszu DWA widoki tej samej pozycji:
1. **widok zlozeniowy** - czesc + **dospawywane elementy** (inne czesci stykajace sie,
   rysowane kolorem 6 magenta) - pokazuje jak wyglada po spawaniu;
2. **widok do palenia** - TA SAMA czesc CZYSTA (sam kontur ciecia + otwory + fazowanie),
   bez dospawien - to jest to, co idzie na laser.

Pipeline nie odroznia tych widokow (oba na tej samej warstwie pozycyjnej, te same wymiary
z wykazu) i moze zlapac ZLOZENIOWY. Wtedy dospawienia (kolor 6) trafiaja do wyniku jako
ciete elementy -> zly detal. Dowod: SL10585238 p1 (W-C=11 z 2 dospawieniami vs W-A/W-B=9
czyste; poszlo do 🟡 przez rozbieznosc - ale zwyciezca-plik byl bledny, W-C).

**Blad diagnozy AI (do zapamietania):** poczatkowo uznalem magenta linie za GIECIE do
przeniesienia na warstwe GIECIE. Operator: to dospawywane elementy, nie giecie; obok jest
czysty widok do palenia. Uczy to: **nie zakladac semantyki magenta bez ogledzin arkusza.**

## Tresc zasady (czytelna dla czlowieka)

Gdy dla jednej pozycji (zeinr+posn) istnieje >1 klaster-kandydat o zgodnym wymiarze:

1. **Preferuj widok CZYSTSZY** = mniej elementow koloru 6 (magenta) STYKAJACYCH sie z
   konturem (dospawienia) i mniej "obcej" geometrii wewnatrz bbox. Widok do palenia ma
   ich zero/minimum; zlozeniowy - kilka.
2. **Rozbieznosc wariantow jako sygnal zlego widoku:** jesli W-A/W-B/W-C daja rozny interior
   na TYM SAMYM klastrze, a inny klaster tej samej pozycji daje interior SPOJNY - wybierz
   ten spojny (to zwykle widok do palenia). Rozjazd = "chyba zlozeniowy".
3. **Dospawienia = kolor 6 stykajacy sie z konturem, NIE zamkniete otwory wewnetrzne.**
   Nie mylic z gieciem (tez kolor 6, ale linia w POPRZEK czesci na rozwinieciu) ani z
   fazowaniem (linia rownolegla do krawedzi, patrz osobna propozycja). Rozstrzyga
   ostatecznie czlowiek, gdy niejednoznaczne (🟡).

## Przyklad referencyjny (golden)

`testy/golden/SL10585238_p1_widok_zlozeniowy/` - wejscie + oba widoki (PNG) + bledny wynik.
Wzorzec = prawy widok (do palenia), 8 slotow + stopien + fazowanie, bez dospawien.

## Uwaga wdrozeniowa

To problem GEOMETRYCZNO-SEMANTYCZNY (rozroznianie widokow) - kandydat do delegacji
[[fable-advisor-trudne-problemy]]. Orkiestrator (Opus) weryfikuje na golden i wpina przez
testy. Do czasu awansu: rozbieznosc wariantow trzyma takie pozycje w 🟡 (czlowiek) -
nic nie ucieka na laser jako 🟢.
