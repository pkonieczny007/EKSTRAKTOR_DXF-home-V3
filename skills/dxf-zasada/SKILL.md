---
name: dxf-zasada
description: Tworzenie propozycji reguly/typu rysunku EKSTRAKTOR_DXF V3 z obserwacji lub trudnego przypadku. Zapisuje propozycje w formacie zasady/propozycje/ (opis problemu, przyklady, oczekiwany wynik) - NIE dziala w produkcji, dopoki nie przejdzie sciezki awansu (golden + regresja + benchmark + potwierdzenie czlowieka). Uzyj gdy uzytkownik prosi "zapisz zasade", "nowa regula", "to sie powtarza - dodaj regule", "propozycja typu rysunku", albo wywola /dxf-zasada.
---

# Skill: dxf-zasada

Obserwacja/przypadek -> propozycja reguly w poprawnym formacie. System tworzenia
zasad w `zasady/` (reguly/ propozycje/ przyklady/). Ten skill pilnuje FORMATU i
SCIEZKI AWANSU - nie wpuszcza pomyslu wprost do produkcji.

**Zasada 8:** nowa zasada wchodzi do produkcji WYLACZNIE przez system testowy (0
regresji) i za potwierdzeniem czlowieka. **Zasada 12:** reguly czytelne dla czlowieka.

## Wywolanie
`/dxf-zasada` - gdy pojawia sie powtarzalna obserwacja lub trudny przypadek wart reguly.

## Procedura
1. Ustal, czy to REGULA (jak traktowac cos w danym typie rysunku) czy nowy TYP
   rysunku (nowy wzorzec konwencji klienta).
2. Utworz propozycje `zasady/propozycje/<RRRR-MM-DD>_<nazwa>.md` z sekcjami:
   - **Problem**: co i dlaczego (z przykladem rysunku/pozycji),
   - **Przyklady**: sciezki do rysunkow/pozycji ilustrujacych (do `zasady/przyklady/`),
   - **Oczekiwany wynik**: co silnik/kontrola ma robic po zmianie,
   - **Jak sprawdzic**: proponowany przypadek golden + metryka sukcesu.
3. Dodaj przypadek do `testy/golden/` (para wejscie -> oczekiwany wynik) - bez tego
   propozycja nie ma jak byc zweryfikowana.
4. Sciezka awansu (NIE pomijac): propozycja -> golden + `testy/regresja.py` +
   `testy/benchmark_v3.py` (wynik >= obecny, 0 nowych bledow) -> POTWIERDZENIE
   czlowieka -> merge do `zasady/reguly/` lub `config/typy.yaml` + podbicie wersji.
5. Dopoki nie zmergowane: propozycja NIE dziala w produkcji (tylko dokument).

## Uwagi
- Reguly per typ: co jest konturem/wymiarem/linia giecia, jakie warstwy/kolory co
  znacza, ktore silniki wariantow uruchamiac, progi bramek.
- Trudny przypadek z produkcji NIE czeka na swoj etap: od razu golden + wpis w
  `kontekst/wiedza/` (zasady zelazne 6, 11), propozycja reguly moze isc rownolegle.
