# Golden R1 — kolor 6: krzyż osi otworu vs linia gięcia (próg długości)

- **Data / źródło:** 2026-07-08, audyt rankingu (RYZYKO 1,
  `zasady/propozycje/2026-07-08_ryzyka_rankingu_do_naprawy.md`). Zasada 11: golden PRZED fixem.
- **Defekt (potwierdzony w kodzie):** `produkcja/silniki/extract_positions.py`, `partition()`
  ~l.234: `if e.dxf.color == 6: bend.append(e); continue` — kolor 6 (magenta) trafia
  BEZWARUNKOWO na warstwę GIECIE. Komentarz obiecuje rozróżnienie „długością względem
  widoku", ale kod tego nie robi.
- **Skutek:** krzyż osi otworu rysowany magentą (krótkie `+` w środku otworu) staje się
  FAŁSZYWĄ linią gięcia — myli bramkę 7 (gięcie) i detekcję luster.

## Przypadek (syntetyczny, deterministyczny)

`wejscie/R1_kolor6_giecie.dxf` (buduje `generator.py`, ezdxf):
- kontur prostokąt 200×100 (LWPOLYLINE, kolor 7) → **geom**
- 2 okręgi R=8 w (50,50) i (150,50) (kolor 7) → **geom**
- dla każdego okręgu KRZYŻ OSI: 2 krótkie linie magenta (dł. 24 ≈ 3·R, przez środek) →
  mają iść do **axis** (odrzucane), NIE do bend
- 1 DŁUGA linia gięcia magenta x=100, y=0..100 (pełna wysokość, linetype DASHDOT) →
  ma iść do **bend**

## Kontrakt (asercja testu `testy/test_r1_kolor6_giecie.py`)

| pole | OBECNIE (bug R1) | PO FIXIE (cel) |
|---|---|---|
| geom | 3 | 3 |
| axis | 0 | **4** (krzyże osi) |
| bend | **5** (wszystko magenta) | **1** (tylko linia gięcia) |

Test jest CZERWONY na obecnym kodzie (dokumentuje R1). Po naprawie `partition()` (próg
długości względny — reguła z fable-advisor, mierzona na realnych rysunkach) staje się
zielony → wtedy wpięcie do `testy/wszystkie.py` + potwierdzenie regresja 43/43 i benchmark.

## Twarde ograniczenia naprawy (nie regresować)
- 4 izometryki naprawione przez detektor (652/797/47020/91010) — ranking bez zmian.
- Goldeny z gięciem (SL10582652, SL40036103) nie tracą linii gięcia.
- Długi fragment obrysu w kolorze 6 (skrajny R1) nie może zniknąć z geometrii.
