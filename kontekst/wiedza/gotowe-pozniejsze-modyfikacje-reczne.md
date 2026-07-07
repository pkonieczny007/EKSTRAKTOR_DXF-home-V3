# "Gotowe" DXF zawieraja POZNIEJSZE modyfikacje reczne - nie sa czysta prawda ekstrakcji

**Zrodlo:** operator, werdykty 41_2050 (2026-07-08). Krytyczne dla benchmarkow.

## Fakt

Pliki "co poszlo na laser" (DXF_do_gotowe) = wynik generowania + RECZNE modyfikacje
operatora PO wygenerowaniu, wynikajace z technologii/uzgodnien, m.in.:
- **poszerzone otwory** ("poszerzone pozniej", SL10311085_p4, SL40061400_p1, SL41061412_p1),
- **rozszerzenia naciec pod rolki** ("robione pozniej po uzgodnieniach", SL10311085_p2),
- **dorobione otwory pod nakladki** na daszkach (SL40051195, SL400521105 - typ "daszek"),
- **dodana recznie linia giecia** (SL10311085_p1),
- **skrocone linie giecia** ("zeby bylo mniej palenia", [[linie-giecia-kierunek-lustro-skracanie]]),
- **naciecie dorobione pozniej** (SL40062237_p1).

## Konsekwencje

1. **Automatyczne porownanie wynik-vs-gotowe (KONTURY_ROZNE) NIE dowodzi bledu
   ekstrakcji** - duza czesc rozjazdow 41_2050 to wlasnie pozniejsze mody (werdykt
   czlowieka: "generowanie prawidlowe"). Rozstrzyga czlowiek albo porownanie ze
   ZRODLEM (rysunkiem), nie z gotowym.
2. Benchmark na gotowych = tylko FLAGER kandydatow do ogledzin; metryka sukcesu
   musi odsiewac kategorie "pozniejsza modyfikacja" (etykiety!).
3. Docelowo: werdykty czlowieka buduja liste wzorcow czystych (golden) - te sa
   prawda; gotowe pozostaje prawda tylko dla wymiaru i obecnosci glownych cech.
