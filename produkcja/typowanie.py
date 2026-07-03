# -*- coding: utf-8 -*-
"""
TYPOWANIE rysunku - okreslenie typu (moze byc WIECEJ NIZ JEDEN) z bazy typow.

Baza typow: config/typy.yaml (rosnie przez system nauki - nowy typ wchodzi
przez zasady/propozycje/ -> testy -> merge). Tu sa HEURYSTYKI WSTEPNE wykrywania;
kalibracja na zasady/przyklady/<typ>/ = PLAN.md etap 4.

Typ jest na etapie 1 INFORMACYJNY (orkiestrator loguje, nie zmienia zachowania);
od etapu 3 typ wybiera silniki wariantow (config/typy.yaml pole `silniki`).

Uzycie: python produkcja\\typowanie.py <rysunek_conv.dxf>
"""
import re
import sys
from collections import Counter
from pathlib import Path

import ezdxf

WARSTWA_POZYCYJNA = re.compile(r"^1\d\d$")   # Lantek: 101 -> pozycja 1
KOLORY_SBM = {2, 3, 6}                        # kontur=2, wymiary=3, giecie=6


def okresl_typy(dxf_path, min_encji=10):
    """Zwraca liste typow [{typ, pewnosc, powod}] posortowana od najpewniejszego.
    Zawsze co najmniej [{'typ': 'domyslny', ...}] - fallback."""
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    n_insert = 0
    n_geo = 0
    warstwy_encji = Counter()
    kolory_encji = Counter()
    for e in msp:
        t = e.dxftype()
        if t == "INSERT":
            n_insert += 1
        elif t in ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE",
                   "SPLINE", "ELLIPSE"):
            n_geo += 1
            warstwy_encji[e.dxf.layer] += 1
            kolory_encji[getattr(e.dxf, "color", 256)] += 1

    typy = []

    # niemiecka blokowa: modelspace = (prawie) same INSERTy
    if n_insert >= 3 and n_geo < max(min_encji, n_insert // 4):
        typy.append({"typ": "niemiecka_blokowa", "pewnosc": "wysoka",
                     "powod": f"INSERT={n_insert}, geometria luzem={n_geo}"})

    # lantek_1nn: uzywane warstwy pozycyjne 1NN
    poz = sorted(w for w in warstwy_encji if WARSTWA_POZYCYJNA.match(w))
    if poz:
        typy.append({"typ": "lantek_1nn", "pewnosc": "wysoka",
                     "powod": f"warstwy pozycyjne: {', '.join(poz[:6])}"})

    # sbm_kolorowa: jedna warstwa dominuje, role koduje kolor (2/3/6 obecne)
    if warstwy_encji and not poz:
        dominujaca, n_dom = warstwy_encji.most_common(1)[0]
        obecne_sbm = KOLORY_SBM & {k for k, n in kolory_encji.items() if n >= 3}
        if n_dom >= 0.8 * max(n_geo, 1) and len(obecne_sbm) >= 2:
            typy.append({"typ": "sbm_kolorowa", "pewnosc": "srednia",
                         "powod": (f"warstwa '{dominujaca}' {n_dom}/{n_geo} encji, "
                                   f"kolory {sorted(obecne_sbm)}")})

    if not typy:
        typy.append({"typ": "domyslny", "pewnosc": "-",
                     "powod": "zadna heurystyka nie zapalila"})
    return typy


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    for t in okresl_typy(Path(argv[0])):
        print(f"{t['typ']:<22} pewnosc={t['pewnosc']:<8} {t['powod']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
