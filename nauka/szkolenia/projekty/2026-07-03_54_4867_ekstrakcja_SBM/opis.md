# Opis szkolenia (wypełnia człowiek)

- **Zlecenie / źródło:** 54_4867, klient SBM (przenośniki DB1200 / FB-PBB, "as drawn / mirrored")
- **Tryb:** A (całe zlecenie — 98 pozycji z kolumną `nazwa_rysowanie`, 43 rysunki)
- **Pozycje, których dotyczy:** cała 10-tka pilotażowa + reszta; kluczowe: SL10596945 (p3P/p4L wsporniki), SL10600635 (wachlarz), SL400521106 (panel), SL41263007/SL40071953 (P/L), rodzina SL10596953/54 (osłony)

## Czego uczę (własnymi słowami)

Realne zlecenie „RYSOWANIE": z rysunków DWG + wykazu robimy gotowe DXF 1:1 na laser
i wypełniamy wykaz (status kolorem, uwagi, plik_dxf, technologia, wymiary DXF, skala,
kontrola wymiarów). W trakcie wyszło kilka rzeczy, których ekstraktor V2 nie robił
dobrze — i konkretne reguły, jak ma robić.

## Na co zwrócić uwagę / pułapki (wykryte na tym zleceniu)

1. **Zgubione cechy** — klaster po sąsiedztwie gubi fasole/otwory odseparowane od
   konturu (SL10596945_p3P: 1 z 2 fasol; SL400521106_p1: 4 z 8 slotów). Wymiar OK,
   więc nie wykrywa. Ratunek: ekstrakcja region+warstwa + liczniki kompletności.
2. **Tabelka zamiast rozwinięcia** — SL10600635_p1 (wachlarz): silnik złapał tabelkę
   rysunku (~480×170 = rozmiar części). Ratunek: region+warstwa (widok był na warstwie 51).
3. **Podwójne/zdublowane okręgi** — otwór jako Ø13+Ø14.7 (przelot+pogłębienie);
   zostaje najmniejszy.
4. **Linie gięcia** — nanosić tylko dla P/L albo skosów, nie dla nie-P/L prostych.
5. **Technologia** — GS vs G z tekstu „Schweissgruppe" w DWG (auto), nie z boilerplate.
6. **Konwersja GstarCAD** — przejściowe błędy, potrzebny retry.
7. **Odtwarzanie z TIF** — tylko w ostateczności, na czerwono, do sprawdzenia.

Pełne wnioski i strategia: `wnioski.md` + `zlecenia/54_4867_RYSOWANIE/UWAGI/`.
