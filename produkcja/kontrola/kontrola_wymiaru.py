# -*- coding: utf-8 -*-
"""
KONTROLA WYMIARU (standard operatora, 2026-07-07) - porownanie wykaz vs DXF.

Metoda operatora (archiwum/tmp/3.2.2 - dxf_reader.py + pl.PLIK_DO_SPRAWDZENIA.xlsx):
  X-DXF, Y-DXF = wymiar z extents DXF (INT: int(maxX-minX), int(maxY-minY));
  'x =x,y' = OR(X==Abm1, X==Abm2, X==Abm1+-1, X==Abm2+-1)   (orientacja-agnostyczna, tol +-1)
  'y =x,y' = OR(Y==Abm1, Y==Abm2, Y==Abm1+-1, Y==Abm2+-1)
  I=PRAWDA i J=PRAWDA  -> UWAGI = "ok"  (wymiar zgodny);
  chocby jeden FALSZ    -> "sprawdz"     (rece operatora).

Wykaz = BAZA (nigdy nie rezygnujemy z porownania z wykazem, [[wykaz-to-baza-additive]]);
'wg technologii' = element identyfikowany po NAZWIE (koduje grubosc/gatunek/technologie
GS/G/S), wymiar per NAZWA. Formuly zapisujemy do Excela TAKZE jako tekst - operator
weryfikuje/dostraja recznie po skrypcie (jego workflow).

Po zmianie: python testy/test_kontrola_wymiaru.py + testy/test_raport.py.
"""
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb

UWAGA_OK = "ok"
UWAGA_SPR = "sprawdz"
# naglowki kolumn kontroli (styl operatora)
KOL = ["X-DXF", "Y-DXF", "x =x,y", "y =x,y"]


def zmierz_dxf_int(path):
    """(X, Y) w mm jako INT z extents (jak dxf_reader: int(max-min)). None gdy brak."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        msp = ezdxf.readfile(str(p)).modelspace()
        ext = _bb.extents(msp)
        if not ext.has_data:
            return None
        return (int(ext.extmax.x - ext.extmin.x), int(ext.extmax.y - ext.extmin.y))
    except Exception:
        return None


def _dopasuj(v, a, b):
    """v (int) zgodne z a lub b w tolerancji +-1 (jak OR operatora). a/b liczby."""
    if a is None and b is None:
        return False
    cele = set()
    for x in (a, b):
        if x is None:
            continue
        xr = round(float(x))
        cele.update((xr, xr + 1, xr - 1))
    return int(v) in cele


def sprawdz(dxf_xy, abm1, abm2):
    """Zwraca dict(x_dxf, y_dxf, ix, jy, uwaga). ix/jy = bool (PRAWDA/FALSZ operatora).
    uwaga = 'ok' gdy ix AND jy, inaczej 'sprawdz'. Brak DXF/wymiaru -> 'sprawdz'."""
    if not dxf_xy:
        return dict(x_dxf="", y_dxf="", ix=False, jy=False, uwaga=UWAGA_SPR)
    x, y = int(dxf_xy[0]), int(dxf_xy[1])
    ix = _dopasuj(x, abm1, abm2)
    jy = _dopasuj(y, abm1, abm2)
    return dict(x_dxf=x, y_dxf=y, ix=ix, jy=jy,
                uwaga=UWAGA_OK if (ix and jy) else UWAGA_SPR)


def formula_xy(col_v, col_abm1, col_abm2, row):
    """Formula Excela operatora: =OR(V=A1,V=A2,V=A1+1,V=A2+1,V=A1-1,V=A2-1)
    col_* = litery kolumn (np. 'C','F','G'); row = numer wiersza."""
    v, a, b = f"{col_v}{row}", f"{col_abm1}{row}", f"{col_abm2}{row}"
    return (f"=OR({v}={a},{v}={b},{v}={a}+1,{v}={b}+1,{v}={a}-1,{v}={b}-1)")


def skala(dxf_xy, abm1, abm2):
    """Skala jak dxf_reader: '1:1' gdy X,Y w {Abm1,Abm2}; inaczej max(Abm)/max(dxf)."""
    if not dxf_xy or (abm1 is None and abm2 is None):
        return "-"
    x, y = int(dxf_xy[0]), int(dxf_xy[1])
    abset = {round(float(a)) for a in (abm1, abm2) if a is not None}
    if x in abset and y in abset:
        return "1:1"
    try:
        return round(max(a for a in (abm1, abm2) if a is not None) / max(x, y), 2)
    except (ZeroDivisionError, ValueError):
        return "-"
