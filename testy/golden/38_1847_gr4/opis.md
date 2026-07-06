# 38_1847 gr4 — golden GRUPY: sweep kompletnosci na prawdziwej partii

Nietypowy przypadek golden: nie pojedyncza para wejscie→wzorzec, lecz **cala grupa**
(6 rysunkow, 10 pozycji) w ukladzie pod **sweep** (`produkcja/kontrola/sweep.py`),
bo sweep jest narzedziem GRUPOWYM (domkniecie zlecenia, zasada 7). Testuje go
`testy/test_gr4.py`.

- **Skad:** zlecenie 38_1847, ekstrakcja z 2026-07-05, folder `wyniki/38_1847/gr4/`.
  Statusy potwierdzone wzrokiem w `ANALIZA_gr4.md`.
- **Uklad:**
  - `wejscie/` — 6 rysunkow zrodlowych `<zeinr>_1_conv.dxf` (= folder_rysunkow sweepa).
  - `wynikow/<zeinr>/` — raport z bboxami (`src_x1..src_y2`) + dostarczone DXF-y
    (= folder_wynikow sweepa; skopiowane TYLKO pliki referowane przez raporty).

## Ground truth (zmierzone sweepem, exit 1 = sa flagi = poprawnie)

| pozycja | zrodlo | wynik | delta | semafor | co lapie |
|---|---|---|---|---|---|
| SL40846315_p1 | 4 | 4 | 0 | 🟢 | 2 sloty + 2 okregi, domkniete |
| SL40851203_p1 | 3 | 3 | 0 | 🟢 | 2 sloty + okrag |
| SL40851203_p2 | 0 | 0 | 0 | 🟢 | goly kontur (0 wewn.) |
| SL40851203_p3 | 2 | 2 | 0 | 🟢 | 2 sloty |
| SL40851344_p1 | 63 | 63 | 0 | 🟢 | logo SBM + perforacja 63=63 |
| SL40851344_p2 | 4 | 4 | 0 | 🟢 | 4 okregi narozne |
| SL40851345_p1 | 63 | 63 | 0 | 🟢 | blizniak 344 |
| SL40851345_p2 | 4 | 4 | 0 | 🟢 | blizniak 344 |
| **SL40852200_p1** | 5 | 3 | 2 | 🔴 | **OTWARTY KONTUR** (bramka 2) + strata slotow (5→3) |
| **SL40052110_p1** | 12 | 4 | 8 | 🟡 | **ZWODNICZA ZIELEN**: strata 8 cech mimo domknietego konturu i wymiaru co do mm |

## Znane bledy ktore lapie (rdzen tego golden)

1. **SL40052110_p1 — zwodnicza zielen (HEADLINE).** Wynik: kontur domkniety, wymiar
   1000×345 zgodny co do mm — sam plik przechodzi bramke 5 bez flagi (interior=4,
   spojny). Zrodlo bylo **zasmiecone 176 wymiarami** i zmylilo stary licznik
   cyklomatyczny (dostal 🟡→traktowany jako OK). Sweep liczy region zrodla przez
   polygonize = **12 konturow wewnetrznych**, wiec delta=8 → 🟡 flaga. Dowod, ze
   **samokontrola wyniku nie wystarcza** — sweep-vs-zrodlo jest obowiazkowy (zasada 7).
2. **SL40852200_p1 — otwarty kontur.** Seria SL4 gieta z kolnierzem, geometria rozbita
   na warstwy (kolor 7 + 3); tryb „bez warstw" zgubil sloty (5→3) i zostawil otwarty
   kontur. Bramka 5 flaguje NIEDOMKNIETE (cuts=1) → 🔴, nie na laser. Naprawa
   region+warstwa tez nie domyka → czlowiek (ANALIZA_gr4.md).
3. **Zero falszywych flag na 8 poprawnych** — w tym perforacja SBM 63=63 (duza siatka),
   sloty, okregi. Straznik przed regresja typu „sweep zaczyna flagowac poprawne".

Uwaga: 🟢 sweepa = KOMPLETNOSC (0 zgubionych konturow, domkniety). Status 🟡 z
`ANALIZA_gr4.md` dla 851203_p2 / 851344_p2 / 851345_p2 to INNA os (giecie / para P-L
do potwierdzenia), nie kompletnosc — dlatego brak sprzecznosci z 🟢 sweepa.
