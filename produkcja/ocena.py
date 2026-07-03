# -*- coding: utf-8 -*-
"""
OCENA WARIANTOW - porownanie kilku wersji tej samej pozycji (bramka 10).

CLAUDE.md "Wielowariantowosc": kazda pozycja moze byc wygenerowana przez 2-3
niezalezne silniki (W-A/W-B/W-C); zgodnosc >=2 metod = wysoka pewnosc,
rozbieznosc = eskalacja do czlowieka (NIGDY cichy wybor).

DZIALA JUZ: sygnatura geometryczna DXF + porownanie pary/zbioru wariantow (CLI).
ETAP 3 (PLAN.md): wpiecie w orkiestrator (generowanie wariantow, wybor zwyciezcy,
scoring z bramkami, zapis ocena.csv, przegrane warianty -> material do nauki).

Uzycie:
  python produkcja\\ocena.py <plik_A.dxf> <plik_B.dxf> [plik_C.dxf ...]
  python produkcja\\ocena.py <folder_warianty>            # grupuje po {poz}__w?.dxf
"""
import re
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bbox

import yaml

HERE = Path(__file__).resolve().parent
CFG = HERE.parent / "config" / "warianty.yaml"
SUFFIX = re.compile(r"__w(\w+)$")   # {Zeinr}_p{N}__wA.dxf


def sygnatura_dxf(path):
    """Sygnatura geometryczna pliku: wymiary bbox + liczniki encji."""
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    typy = Counter(e.dxftype() for e in msp)
    ext = _bbox.extents(msp, fast=False)   # scisle (fast przeszacowuje SPLINE!)
    w = h = 0.0
    if ext.has_data:
        w = ext.size.x
        h = ext.size.y
    return {"plik": Path(path).name, "w": round(w, 2), "h": round(h, 2),
            "n_encji": sum(typy.values()), "n_circle": typy.get("CIRCLE", 0),
            "typy": dict(typy)}


def _tolerancja(cfg):
    z = (cfg or {}).get("zgodnosc", {})
    return float(z.get("tolerancja_wymiaru_mm", 1.0)), \
        float(z.get("tolerancja_wymiaru_proc", 0.2))


def porownaj(sig_a, sig_b, tol_mm=1.0, tol_proc=0.2):
    """Porownanie dwoch sygnatur -> (zgodne: bool, rozjazdy: [str])."""
    rozjazdy = []
    for os_ in ("w", "h"):
        a, b = sig_a[os_], sig_b[os_]
        tol = max(tol_mm, tol_proc / 100.0 * max(a, b))
        if abs(a - b) > tol:
            rozjazdy.append(f"wymiar {os_}: {a} vs {b} (tol {tol:.2f})")
    if sig_a["n_circle"] != sig_b["n_circle"]:
        rozjazdy.append(f"okregi: {sig_a['n_circle']} vs {sig_b['n_circle']}")
    # TODO etap 2: liczba konturow wewnetrznych (shapely.polygonize) zamiast n_encji
    if sig_a["n_encji"] != sig_b["n_encji"]:
        rozjazdy.append(f"encje: {sig_a['n_encji']} vs {sig_b['n_encji']} (info)")
    zgodne = not any(not r.endswith("(info)") for r in rozjazdy)
    return zgodne, rozjazdy


def ocen_zbior(pliki):
    """Porownuje kazdy wariant z kazdym; zwraca (sygnatury, pary, werdykt)."""
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    tol_mm, tol_proc = _tolerancja(cfg)
    sygnatury = [sygnatura_dxf(p) for p in pliki]
    pary = []
    n_zgodnych = 0
    for i in range(len(sygnatury)):
        for j in range(i + 1, len(sygnatury)):
            zgodne, rozjazdy = porownaj(sygnatury[i], sygnatury[j], tol_mm, tol_proc)
            n_zgodnych += zgodne
            pary.append((sygnatury[i]["plik"], sygnatury[j]["plik"], zgodne, rozjazdy))
    werdykt = "ZGODNE" if pary and all(z for _, _, z, _ in pary) else \
        ("ROZBIEZNE -> eskalacja do czlowieka" if pary else "za malo wariantow")
    return sygnatury, pary, werdykt


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if len(argv) == 1 and Path(argv[0]).is_dir():
        folder = Path(argv[0])
        grupy = {}
        for p in sorted(folder.glob("*.dxf")):
            m = SUFFIX.search(p.stem)
            grupy.setdefault(SUFFIX.sub("", p.stem) if m else p.stem, []).append(p)
        pliki_grup = [(poz, pliki) for poz, pliki in grupy.items() if len(pliki) > 1]
        if not pliki_grup:
            print("brak grup wariantow ({poz}__w?.dxf) w folderze")
            return 1
    else:
        pliki_grup = [("(argumenty)", [Path(a) for a in argv])]

    kod = 0
    for poz, pliki in pliki_grup:
        syg, pary, werdykt = ocen_zbior(pliki)
        print(f"\n=== {poz}: {werdykt} ===")
        for s in syg:
            print(f"  {s['plik']:<40} {s['w']}x{s['h']}  encje={s['n_encji']} okregi={s['n_circle']}")
        for a, b, zgodne, rozjazdy in pary:
            if rozjazdy:
                print(f"  {a} vs {b}: {'OK' if zgodne else 'ROZJAZD'} - {'; '.join(rozjazdy)}")
        if "ROZBIEZNE" in werdykt:
            kod = 1
    return kod


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
