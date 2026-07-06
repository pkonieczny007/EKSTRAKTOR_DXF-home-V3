# Wnioski (zaakceptowane przez człowieka 2026-07-04 — „sprawdź i wyciągnij lekcje")

## 1. Jeden znaleziony błąd NIE kończy kontroli  →  REGUŁA
Błąd „satysfakcji ze znaleziska": pierwszy wykryty problem (duble okręgów) zamknął
szukanie, a najgroźniejszy (zgubiona fasola) został. Werdykt wolno wydać dopiero po
WYPEŁNIONEJ karcie kontrolnej (liczby: kontury/okręgi/gięcia + qc_powody + render).
→ wdrożone: karta kontrolna w CLAUDE.md („Sprawdzanie przez AI") +
`kontekst/wiedza/kontrola-karta-kontrolna-jeden-blad.md`.

## 2. Bilans konturów wewnętrznych liczyć PO DEDUPIE okręgów  →  REGUŁA + BRAMKA 5
Duble maskują braki: stary wynik surowo 5 „konturów" (4 okręgi w tym 2 duble + 1 fasola),
źródło 4 — wygląda dobrze; po dedupie 3 vs 4 = brak widoczny. Bramka 5 (etap 2) musi
dedupować przed porównaniem.

## 3. qc_powody czytać ZAWSZE  →  REGUŁA
Bramka 6 pisała wprost „zgubione gięcie?" — flaga była w raporcie, nikt jej nie
przeczytał. Każda żółta pozycja ma powód i ten powód jest częścią karty kontrolnej.

## 4. Metoda operatora = spec silnika W-C  →  POTWIERDZENIE ARCHITEKTURY
„Zaznacz region → jedna warstwa (53) → kopiuj wszystko" / „zaznacz po kolorze białym
→ dodaj gięcia → skaluj" — dokładnie ekstrakcja region+warstwa. Auto-wykrycie warstwy
(najczęstsza koloru 7 w regionie) trafiło w 53. Integracja W-C = PLAN etap 2.

## 5. Trening na przyszłość (propozycje → PLAN)
- Golden `SL10596945_fasola_odseparowana` pilnuje wszystkich 3 błędów naraz (etap 2 odbiór).
- Kalibracja oczu przed sesją sprawdzania AI: 1–2 znane pary z golden, AI musi wskazać brak.
- Galeria: dopisać na kafelku bilans liczbowy „kontury: źródło N / wynik M" (etap 4).
- Zakaz „prawdopodobnie" w werdyktach — liczby albo DO_SPRAWDZENIA.
