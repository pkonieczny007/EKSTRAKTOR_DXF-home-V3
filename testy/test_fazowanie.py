# -*- coding: utf-8 -*-
"""Testy FLAGERA FAZOWANIA: produkcja/kontrola/fazowanie.py.

Fazowanie = linia rownolegla do krawedzi (T-zlacza), oznaczana ZOLTYM + komentarzem
(operator 2026-07-07: zostawic linie, kolor zolty, komentarz). Rdzen: fable-advisor,
zweryfikowany niezaleznie (Opus). Golden: testy/golden/fazowanie_linia_przy_krawedzi/.

A) 3 POZYTYWY (SL10585238_p2, SL10585242_p2, SL10583062_p2) -> >=1 kandydat, d~5, ratio~1;
B) NEGATYWY (sloty/okregi/dospawienia) -> 0 kandydatow (0 falszywych);
C) oznacz_w_pliku: koloruje linie fazy na ZOLTY (2), idempotentne, geometria bez zmian;
D) komentarz niepusty dla pozytywu.

Uzycie:  python testy\\test_fazowanie.py     (exit 0 = PASS)
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "produkcja" / "kontrola"))
import fazowanie  # noqa: E402

GOLD = HERE / "golden" / "fazowanie_linia_przy_krawedzi" / "wynikow_biezacy"
POZYTYWY = ["SL10585238_p2.dxf", "SL10585242_p2.dxf", "SL10583062_p2.dxf"]
# negatywy: sloty (p2 4 sloty), okregi+sloty (p1), dospawienia (238 p1) - NIE fazowanie
NEGATYWY = ["SL10584847_p2.dxf", "SL10409233_p1.dxf", "SL10585238_p1.dxf"]
NEG_DIR = ROOT / "wyniki" / "38_1847" / "gr6"

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _kand(path):
    return fazowanie.wykryj_fazowanie(ezdxf.readfile(str(path)).modelspace())


def test_pozytywy():
    print("--- A) POZYTYWY (maja fazowanie) ---")
    for nz in POZYTYWY:
        p = GOLD / nz
        check(f"A istnieje {nz}", p.exists(), str(p))
        if not p.exists():
            continue
        k = _kand(p)
        check(f"A0 {nz} >=1 kandydat", len(k) >= 1, f"n={len(k)}")
        if k:
            d = k[0]["dystans_mm"]
            r = k[0]["ratio"]
            check(f"A1 {nz} d w [1,10]", 1.0 <= d <= 10.0, f"d={d}")
            check(f"A2 {nz} ratio ~1", 0.6 <= r <= 1.4, f"ratio={r}")
            print(f"  {nz}: kand={len(k)} d={d} ratio={r} pewnosc={k[0]['pewnosc']}")


def test_negatywy():
    print("\n--- B) NEGATYWY (bez fazowania -> 0) ---")
    for nz in NEGATYWY:
        p = NEG_DIR / nz
        if not p.exists():
            print(f"  (pominieto brak {nz})")
            continue
        k = _kand(p)
        check(f"B {nz} = 0 kandydatow", len(k) == 0, f"FP n={len(k)}")
        print(f"  {nz}: kand={len(k)} {'OK' if not k else '!!! FP'}")


def test_oznacz():
    print("\n--- C) oznacz_w_pliku: recolor ZOLTY + idempotencja + geometria ---")
    tmp = Path(tempfile.mkdtemp(prefix="faz_"))
    try:
        src = GOLD / POZYTYWY[0]
        c = tmp / "faz.dxf"
        shutil.copy(src, c)
        e0 = _bb.extents(ezdxf.readfile(str(src)).modelspace())
        n1, kom = fazowanie.oznacz_w_pliku(c)
        check("C0 wykryto", n1 >= 1, f"n={n1}")
        check("C1 komentarz niepusty", bool(kom), repr(kom))
        msp = ezdxf.readfile(str(c)).modelspace()
        zolte = sum(1 for e in msp if e.dxftype() == "LINE" and int(e.dxf.color) == 2)
        check("C2 linia zolta (2)", zolte >= 1, f"zoltych={zolte}")
        e1 = _bb.extents(msp)
        check("C3 geometria bez zmian",
              abs((e0.extmax.x - e0.extmin.x) - (e1.extmax.x - e1.extmin.x)) < 0.01
              and abs((e0.extmax.y - e0.extmin.y) - (e1.extmax.y - e1.extmin.y)) < 0.01,
              "extents zmienione")
        # idempotencja: 2. wywolanie nadal wykrywa, nie psuje
        n2, _ = fazowanie.oznacz_w_pliku(c)
        check("C4 idempotentne (nadal wykrywa)", n2 == n1, f"{n2} vs {n1}")
        print(f"  recolor OK: zoltych={zolte} kom='{kom}' idempotent n2={n2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== TESTY FLAGERA FAZOWANIA ===\n")
    test_pozytywy()
    test_negatywy()
    test_oznacz()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== FAZOWANIE: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== FAZOWANIE: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
