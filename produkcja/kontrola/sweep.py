# -*- coding: utf-8 -*-
"""
SWEEP KOMPLETNOSCI - obowiazkowe domkniecie zlecenia (CLAUDE.md zasada 7).

Dla WSZYSTKICH pozycji zlecenia: policz kontury region+warstwa w zrodle vs
w dostarczonym DXF. Flagi delta>=2 -> OGLEDZINY WZROKIEM 100% (render region
vs wynik), od NAJWIEKSZYCH roznic. Nigdy nie odrzucac flagi po wielkosci
roznicy (zasada 6 - blad z 54_4867).

WSZYSTKIE tryby ekstrakcji musza byc pokryte, bo geometria bywa na roznym
kolorze/warstwie (54_4867: col7 17x, all 32x, col2 4x -> SL40061302 znaleziony
dopiero sweepem col2!, col4 1x, warstwa-geometria 3x).

Procedura wzorcowa (dziala recznie, patrz kontekst/lekcje_54_4867_raport_poprawek.md
oraz sweep.py/sweep2.py z tamtego zlecenia):
  1. Z raportu <zeinr>_raport.csv wez src_x1..src_y2 + scale pozycji.
  2. W <zeinr>_conv.dxf: warstwa geometrii = najczestsza (!= '1', != Defpoints,
     != kolor 4 osie) w bbox; policz kontury wewnetrzne (docelowo shapely.polygonize).
  3. Policz kontury w dostarczonym DXF (po dedupie okregow wspolsrodkowych).
  4. delta>=2 -> flaga -> render pary PNG (czarne tlo!) -> oczy.
  5. Kazda flaga zamknieta z DOWODEM (para PNG w raporcie sweepa).

ETAP 2 (PLAN.md): implementacja tego skryptu na bazie _region_warstwa.py
(silniki/region_warstwa.py) + licznik_konturow.py -> raport sweepa do
testy/raporty/ i pozycje-flagi do sprawdzanie/ai (ogledziny).

Uzycie (docelowe): python produkcja\\kontrola\\sweep.py <folder_wynikow> <folder_rysunkow>
"""
import sys

TRYBY = ["col7", "col2", "col4", "all", "warstwa-geometria"]


def main(argv):
    print(__doc__)
    print("STATUS: szkielet - implementacja = PLAN.md etap 2 "
          f"(tryby do pokrycia: {', '.join(TRYBY)})")
    return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
