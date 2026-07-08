# -*- coding: utf-8 -*-
"""Generator golden R1: kolor 6 — krzyz osi otworu vs linia giecia (test GEOMETRYCZNY).

Rozroznienie NIE po samej dlugosci (konwerter GstarCAD rozbija linie przerywane na
kreski <3mm — prog dlugosci zabilby rozbite giecie), lecz GEOMETRIA: krzyz osi jest
wycentrowany na srodku CIRCLE i ma dlugosc ~srednica. Progi zmierzone przez fable-advisor
na 84 288 realnych encjach kolor-6 (0/210 prawdziwych giec przechodzi przez srodek okregu).

Buduje deterministyczny rysunek z przypadkami brzegowymi (liczby zweryfikowane na patchu):
  KONTUR:  prostokat 200x100 (LWPOLYLINE, kolor 7)                         -> geom
  OKREGI:  H1(50,50)r8, H2(150,50)r8, H3(100,25)r7 (kolor 7)               -> geom (3)
  KRZYZE OSI (magenta, -> axis, ODRZUCane):
    H1: poziom+pion L=24 (L/D=1.5)
    H2: poziom+pion L=24 (L/D=1.5)
    H3: poziom+pion L=42 (L/D=3.0 — realna proporcja przeciagniecia osi)   -> axis (6)
  GIECIA (magenta, -> bend, ZOSTAJA na warstwie GIECIE):
    dluga linia giecia x=100 y=0..100 (DASHDOT, przez cala czesc)          -> bend (1)
    ROZBITE giecie: 12 wspolliniowych kreski L=2 wzdluz y=80 (CONTINUOUS)  -> bend (12)
    os symetrii przez H2: pion L=90 (L/D=5.6 > 4.0 -> NIE krzyz, zostaje)  -> bend (1)

Kontrakt (po fixie R1):  geom=4  axis=6  bend=14  (przed fixem: cala magenta -> bend).
"""
import io
import sys
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = Path(__file__).parent / "wejscie" / "R1_kolor6_giecie.dxf"

HOLES = [(50, 50, 8), (150, 50, 8), (100, 25, 7)]   # cx, cy, r


def _cross(msp, cx, cy, half):
    """Krzyz osi: 2 krotkie linie magenta wycentrowane na (cx,cy), dlugosc 2*half."""
    msp.add_line((cx - half, cy), (cx + half, cy), dxfattribs={"color": 6})   # poziom
    msp.add_line((cx, cy - half), (cx, cy + half), dxfattribs={"color": 6})   # pion


def build():
    doc = ezdxf.new("R2010", setup=True)   # setup=True -> linetypy CENTER/DASHDOT
    msp = doc.modelspace()

    # --- kontur (kolor 7, geom) ---
    msp.add_lwpolyline([(0, 0), (200, 0), (200, 100), (0, 100)],
                       close=True, dxfattribs={"color": 7})

    # --- 3 okregi (kolor 7, geom) ---
    for cx, cy, r in HOLES:
        msp.add_circle((cx, cy), r, dxfattribs={"color": 7})

    # --- KRZYZE OSI (magenta -> axis) ---
    _cross(msp, 50, 50, 12)    # L=24, L/D=1.5
    _cross(msp, 150, 50, 12)   # L=24, L/D=1.5
    _cross(msp, 100, 25, 21)   # L=42, L/D=3.0 (realna proporcja)

    # --- GIECIA (magenta -> bend) ---
    # dluga linia giecia przez cala czesc (DASHDOT)
    msp.add_line((100, 0), (100, 100), dxfattribs={"color": 6, "linetype": "DASHDOT"})
    # rozbite giecie: 12 wspolliniowych kreski L=2, pitch 4, wzdluz y=80 (jak po konwersji)
    for i in range(12):
        x0 = 10 + 4 * i
        msp.add_line((x0, 80), (x0 + 2, 80), dxfattribs={"color": 6})
    # os symetrii przez srodek H2: pion L=90, L/D=5.6 > 4.0 -> zostaje bend (kompromis R1)
    msp.add_line((150, 5), (150, 95), dxfattribs={"color": 6, "linetype": "CENTER"})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(OUT))
    return OUT


def verify(path):
    ROOT = Path(r"c:\Python_CLaude\EKSTRAKTOR_DXF\EKSTRAKTOR_DXF-home-V3")
    sys.path.insert(0, str(ROOT / "produkcja" / "silniki"))
    import extract_positions as ep

    doc = ezdxf.readfile(str(path))
    geom, axis, dashed, bend, annot = ep.partition(list(doc.modelspace()))
    print(f"  geom={len(geom)}  axis={len(axis)}  bend={len(bend)}  "
          f"(cel po fixie: geom=4 axis=6 bend=14)")
    return dict(geom=len(geom), axis=len(axis), bend=len(bend))


if __name__ == "__main__":
    p = build()
    print(f"[OK] zapisano {p}")
    verify(p)
