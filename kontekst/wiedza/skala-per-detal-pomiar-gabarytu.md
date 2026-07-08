# Skala PER DETAL + pomiar gabarytu (nie do krawędzi otworu)

**Źródło:** feedback operatora 2026-07-08, zlecenie 60_7205, rysunek 51730649 (ekstrakcja Pos.3-6).

## Zasada skali — PRIORYTET
- **Nie zakładać jednej skali na cały rysunek.** Pojedyncze pozycje DOSYĆ CZĘSTO mają
  inną skalę niż reszta arkusza. Realny przypadek: 51730649 cały 1:5, ale **Pos6 = 1:2**
  (gdyby założyć 1:5 → detal 2,5× za mały na laser).
- Założenie jednej skali = **błąd niedoświadczonego technologa**.
- **Skalę KAŻDEGO detalu ustalać z jego własnych wymiarów**: `DIMENSION.get_measurement()`
  (długość geometryczna z defpoints) vs liczba w `dxf.text` przy tym widoku. Iloraz = skala.
- Metoda pracy operatora: jak wiadomo, że detal był 1:5 → następny sprawdzaj NAJPIERW 1:5;
  OK → jedź dalej; nie → ustal nową skalę. Sugerować się sąsiadem wolno, **potwierdzić
  zawsze** na danym detalu.

## Pomiar gotowego DXF = GABARYT (skrajne extents)
- **Mierzyć gabaryt, nie do krawędzi otworu.** Błąd: na Pos3 pomiar „do krawędzi otworu"
  dał 132 mm zamiast 145 mm (otwór Ø24 przy krawędzi zaniżył wynik).
- Kanoniczna metoda operatora (`archiwum\tmp\3.2.2 - dxf_reader.py`): czytać `$EXTMIN` /
  `$EXTMAX` z nagłówka DXF → `W = maxX−minX`, `H = maxY−minY`.
- Weryfikacja skryptowa (ezdxf): `ezdxf.bbox.extents(msp, fast=False)` daje ten sam gabaryt
  (uwzględnia wybrzuszenie łuków — pomiar tylko po końcach łuku ZANIŻA i przesuwa środek).
- Porównanie z wykazem: `W,H ∈ {Abmess_1, Abmes_2}` z tol. ±1 = OK; inaczej
  `skala = max(Abmess)/max(W,H)`.

## Walidacja bojowa (dowód, że metoda działa)
Ekstrakcja AI (skala per detal + ×5, Pos6 ×2) vs DXF narysowane ręcznie przez operatora
(`60_7205\PK\`): gabaryty zgodne <0,1 mm, identyczna liczba otworów:
Pos3 145,2×119,8 (o1) · Pos4 394,6×82,0 (o0) · Pos5 399,9×130,0 (o0, 2 gięcia) · Pos6 41×41 (o2).

Powiązane: [[karta-kontrolna-jeden-blad-nie-konczy]], [[kontrola-konturow-obowiazkowa-dwie-metody]].
Wpięte do CLAUDE.md → „KONTROLA DETALU GOTOWEGO" jako krok **0. SKALA + GABARYT**.
