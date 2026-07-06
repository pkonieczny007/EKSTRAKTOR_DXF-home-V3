# REGUŁA: Zgodny wymiar + domknięty kontur ≠ KOMPLETNOŚĆ

**Status:** wdrożona (etap 2–4; bramka 5 + sweep + nakładka).
**Klasa błędu, której zapobiega:** zgubione cechy wewnętrzne (fasole, sloty/Langlochy,
kwadraty, bloki perforacji, wyspy odseparowane) w pliku, który wygląda na dobry —
wymiar zgadza się co do mm, kontur jest zamknięty, wszystkie klasyczne bramki milczą.

## Zasada (ogólna, niezależna od numeru rysunku)

Plik wynikowy może być **wewnętrznie spójny** (domknięty kontur, poprawny bbox,
zielony z silnika) i mimo to mieć zgubione otwory. Wewnętrzna kontrola samego wyniku
tego NIE wykryje z zasady — brakującej cechy nie ma w pliku, więc nie ma czego liczyć.
Jedyny deterministyczny sposób: **bilans konturów wewnętrznych REGIONU-ŹRÓDŁA vs
WYNIKU**, obowiązkowy dla KAŻDEJ pozycji (także 🟢), zanim status może zostać 🟢.

Mechanizm geometryczny błędu: ekstrakcja gubi cechy, które nie łączą się z konturem
(wyspa odseparowana wypada z klastra po sąsiedztwie) albo leżą na innym kolorze/warstwie
niż tryb ekstrakcji (geometria bywa na kolorze 2/4/7 lub warstwie numerycznej — widok
per warstwa 51/103/…). Wymiar zewnętrzny przy tym NIE cierpi — dlatego bbox nie alarmuje.

## Mechanizm wykrywania (jak liczy)

1. Region źródłowy = widok, z którego wycięto pozycję (bbox z raportu), geometria
   z trybu CZYSTEGO (patrz reguła [region-tryb-czysty.md](region-tryb-czysty.md)),
   z wykluczeniem gięcia (kolor 6 / warstwa GIECIE) i osi.
2. Liczba konturów WEWNĘTRZNYCH: `shapely.polygonize` (nodowanie unary_union + snap
   końcówek realną odległością — odporne na lustro/float-jitter, bez off-by-one
   zaokrąglania węzłów do 0,1 mm) — to jest bramka 5.
3. Okręgi: środek zawsze OCS→WCS + **dedup współśrodkowych PRZED liczeniem**
   (duble MASKUJĄ braki: surowo 5 vs 4 wygląda dobrze, po dedupie 3 vs 4 = brak).
4. delta = kontury(region-źródło) − kontury(wynik).

## Bramka / skrypty, które to egzekwują

| Warstwa | Skrypt | Próg |
|---|---|---|
| Bramka 5 — bilans konturów (pojedynczy plik / para) | `produkcja/kontrola/bilans_konturow.py` | delta konturów ≥2 lub delta okręgów ≥1 = flaga (`DELTA_KONTURY=2`, `DELTA_OKREGI=1`) |
| Sweep kompletności — CAŁE zlecenie, wszystkie pozycje i tryby (domknięcie zlecenia, zasada 7) | `produkcja/kontrola/sweep.py` | `PROG_DELTA=1` (delta ≥1 = flaga; zmierzone 0 fałszywych na golden) |
| Nakładka wynik-na-źródło (niezależna od liczenia — łapie, co licznik przeoczy) | `sprawdzanie/ai/nakladka.py` + `sprawdzanie/ai/sprawdz_folder.py` | `pokrycie_zrodla < 97%` = MOŻLIWY BRAK + skupiska braków zakreślone na czerwono |

Charakter: **FLAGER** (zasada 6) — delta wskazuje GDZIE patrzeć, decyzję podejmują
OCZY (render region vs wynik), 100% flag, od NAJWIĘKSZYCH różnic, nigdy odrzucenie
flagi po wielkości. Twarda (blokująca) jest tylko flaga NIEDOMKNIĘTE (otwarty kontur).

## Golden-testy (dowód — przykłady TESTUJĄ regułę, nie definiują jej)

- `testy/golden/SL40034116_p1_zgubione_otwory/` — finalny plik: kontur zamknięty,
  wymiar 808×842 zgodny z wykazem, WSZYSTKIE bramki przechodzą — a zgubił 13 Langlochów
  (interior 26 vs 39; potwierdzone wzrokowo przez operatora 2026-07-07). Sweep/nakładka
  MUSZĄ go flagować.
- `testy/golden/38_1847_gr4/` — SL40052110_p1: „zwodnicza zieleń", delta 8 (12 vs 4)
  mimo domkniętego konturu i wymiaru co do mm. Test: `testy/test_gr4.py`.
- `testy/golden/SL10596945_fasola_odseparowana/`, `SL40061302_sloty_odseparowane/`,
  `SL10582608_owal_odseparowany_klaster/`, `SL10599245_owal_spline_odseparowany/` —
  cechy odseparowane (lekcja 54_4867).
- Testy: `testy/test_bramka5.py`, `testy/test_sweep.py`, `testy/test_nakladka.py`,
  `testy/test_sweep_54_4867.py`, `testy/test_gr4.py`.

## Powiązane

CLAUDE.md „KONTROLA DETALU GOTOWEGO" (trzy kontrole: liczbowa → wizualna → zamknięte
kontury); zasada żelazna 2 i 6; `kontekst/strategia_kompletnosc_otworow.md`.
