# -*- coding: utf-8 -*-
"""Test R1 — partition() rozroznia krzyz osi (kolor 6, wycentrowany na okregu) od
linii giecia (kolor 6) TESTEM GEOMETRYCZNYM, nie sama dlugoscia.

Cel (RYZYKO 1, audyt rankingu): kolor 6 (magenta) NIE moze bezwarunkowo trafiac na
warstwe GIECIE. Krzyz osi otworu (magenta, midpoint na srodku CIRCLE, L~srednica) -> axis
(odrzucany). Reszta magenta (giecie DASHDOT, ROZBITE giecie <3mm, dluga os symetrii) -> bend.

Golden: testy/golden/R1_kolor6_krzyz_osi_vs_giecie/ (opis.md + generator.py; progi zmierzone
przez fable-advisor na 84 288 realnych encjach kolor-6, 0/210 giec przez srodek okregu).

STATUS: ZIELONY po fixie partition() (na kodzie sprzed fixu byl czerwony, zasada 11).

Uzycie:  python testy\\test_r1_kolor6_giecie.py     (exit 0 = PASS)
"""
import io
import math
import sys
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
GOLDEN = HERE / "golden" / "R1_kolor6_krzyz_osi_vs_giecie" / "wejscie" / "R1_kolor6_giecie.dxf"
sys.path.insert(0, str(ROOT / "produkcja" / "silniki"))
import extract_positions as ep          # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _len(e):
    s, en = e.dxf.start, e.dxf.end
    return math.hypot(en.x - s.x, en.y - s.y)


def main():
    doc = ezdxf.readfile(str(GOLDEN))
    ents = list(doc.modelspace())
    geom, axis, dashed, bend, annot = ep.partition(ents)

    # --- kontrakt liczbowy (zweryfikowany na patchu) ---
    check("geom_kontur_3okregi", len(geom) == 4,
          f"geom={len(geom)} (oczekiwano 4: kontur + 3 okregi)")
    check("axis_6_krzyzy", len(axis) == 6,
          f"axis={len(axis)} (oczekiwano 6: 3 krzyze osi po 2 linie; "
          f"0 => bug R1 - krzyze zlepione z gieciem)")
    check("bend_14", len(bend) == 14,
          f"bend={len(bend)} (oczekiwano 14: 1 DASHDOT + 12 rozbitych + 1 os symetrii; "
          f"20 => bug R1 - cala magenta na GIECIE)")

    # --- celowane: prawdziwe giecie i jego warianty ZOSTAJA w bend ---
    dashdot = [e for e in bend if (e.dxf.linetype or "").upper() == "DASHDOT"]
    check("giecie_dashdot_w_bend", len(dashdot) == 1,
          f"DASHDOT w bend={len(dashdot)} (dluga linia giecia musi zostac)")

    rozbite = [e for e in bend if e.dxftype() == "LINE" and abs(_len(e) - 2.0) < 0.1]
    check("rozbite_giecie_nie_ginie", len(rozbite) == 12,
          f"kreski L~2 w bend={len(rozbite)} (rozbite giecie <3mm NIE moze trafic do axis - "
          f"to sedno testu geometrycznego zamiast progu dlugosci)")

    os_sym = [e for e in bend if e.dxftype() == "LINE" and abs(_len(e) - 90.0) < 0.1]
    check("os_symetrii_w_bend", len(os_sym) == 1,
          f"os symetrii L=90 w bend={len(os_sym)} (L/D=5.6>4.0 -> NIE krzyz; "
          f"swiadomy kompromis R1)")

    # --- zaden magenta nie ginie: bend+axis pokrywa wszystkie kolor-6 ---
    magenta = [e for e in ents if e.dxf.color == 6]
    pokryte = len([e for e in bend if e.dxf.color == 6]) + \
              len([e for e in axis if e.dxf.color == 6])
    check("magenta_nie_ginie", pokryte == len(magenta),
          f"magenta w bend+axis={pokryte} vs wszystkich={len(magenta)} (skrajny R1)")

    print(f"CHECKS={CHECKS}  FAILS={len(FAILS)}")
    for f in FAILS:
        print("  FAIL:", f)
    if FAILS:
        print("\n[R1 CZERWONY] — sprawdz patch partition().")
        sys.exit(1)
    print("[R1 ZIELONY] — krzyz osi -> axis, giecie (tez rozbite) -> bend.")
    sys.exit(0)


if __name__ == "__main__":
    main()
