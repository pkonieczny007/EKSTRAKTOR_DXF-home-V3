# -*- coding: utf-8 -*-
"""Test ZACOMMITOWANEJ reguly LUSTRA par P/L (produkcja/warianty.py, PATCH 4).

Regula (CLAUDE.md + lantek1nn-poz-parzysta-lustro + golden SL40036103):
  pozycja-LUSTRO nie powstaje z wlasnego (slabego) widoku - jest ODBICIEM zwyciezcy
  blizniaka, zeby zachowac jego KOMPLETNOSC. Wykrycie pary:
    T1 (wykaz roboczy): DODATKOWA KOLUMNA = L / Nazwa konczy _L, blizniak _P.
    T2 (bez kolumn): 2 pozycje te same dims + DOKLADNIE 1 wspolny widok (nakladajace
       src-bbox). Asymetryczne blizniaki (2 OSOBNE widoki) NIE sa sklejane.
  Lustro = zawsze ZOLTY (nigdy auto-zielony - blizniaki bywaja asymetryczne).

Golden: testy/golden/SL40036103_lustro_skos_giecia/ (poz1 _P blacha, poz2 _L blacha
  te same dims 441x294; przed fixem V3 dawal p2 = dymek nr-pozycji 441x294 z 4 encji
  naciagniety skala ~29 zamiast odbicia p1).
Kontrprzypadek: SL10599245 p1/p2 (owal spline odseparowany) - te same dims 1150x1130,
  ale DWA OSOBNE widoki -> asymetryczne blizniaki, NIE lustro (T2 nie odpala).

Sprawdza:
  A) T1 z wykazu -> {2:1}, poz2 lustro/L, poz1 P.
  B) _odbij_lustro = mirror-X + wysrodkowanie: odbicie p1 == mirror_x(p1) (max_nn<0.01),
     zachowuje liczbe encji (25, nie 4-encjowy dymek).
  C) end-to-end warianty_zlecenia na golden: p2 = LUSTRO(p1), semafor ZOLTY,
     max_nn(p2, mirror_x(p1_zwyciezcy))<0.01, p2 ma 25 encji (nie dymek).
     (INFO/bonus: czy p1 ma linie giecia na warstwie GIECIE - kol6-przed-linetype).
  D) kontrprzypadek: wykryj_pary_pl na realnych boxach 245 (2 osobne widoki) -> {}
     (nie sklejone); kontrola dodatnia: nakladajace widoki -> sklejone {2:1}.

Uzycie:  python testy\\test_lustro_pary.py     (exit 0 = PASS)
"""
import io
import math
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb
from ezdxf.math import Matrix44

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
sys.path.insert(0, str(HERE.parent / "produkcja"))
sys.path.insert(0, str(HERE.parent / "produkcja" / "silniki"))
import warianty as W  # noqa: E402

FAILS = []
CHECKS = 0
POMIARY = {}

G_LUSTRO = GOLDEN / "SL40036103_lustro_skos_giecia" / "wejscie"
CONV = G_LUSTRO / "SL40036103_1.dxf"
WYKAZ = G_LUSTRO / "wykaz_41_2050.xlsx"
P1_WEJ = G_LUSTRO / "V3__3_S235_SL40036103_p1_1st_GS_2050_Ptest.dxf"  # realna czesc n=25


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")
    print(f"    [{'OK ' if warunek else 'BAD'}] {nazwa}" + (f"  ({info})" if info else ""))


def _verts(msp):
    """Punkty charakterystyczne encji (LINE konce, srodki ARC/CIRCLE) do porownania NN."""
    p = []
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            p += [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t in ("ARC", "CIRCLE"):
            p.append((e.dxf.center.x, e.dxf.center.y))
    return p


def _mirror_x_center_verts(path):
    """Niezalezna referencja: mirror-X (scale(-1,1,1)) + wysrodkowanie bbox do (0,0).
    Ta sama OS co _odbij_lustro; gdyby kod odbijal w Y/obracal - max_nn urosnie."""
    doc = ezdxf.readfile(str(path))
    m = doc.modelspace()
    for e in m:
        try:
            e.transform(Matrix44.scale(-1, 1, 1))
        except Exception:
            pass
    ex = _bb.extents(m)
    mv = Matrix44.translate(-(ex.extmin.x + ex.extmax.x) / 2.0,
                            -(ex.extmin.y + ex.extmax.y) / 2.0, 0)
    for e in m:
        e.transform(mv)
    return _verts(m)


def _max_nn(A, B):
    """Symetryczny max najblizszego sasiada (mm) miedzy dwoma zbiorami punktow."""
    def one(P, Q):
        return max(min(math.hypot(a[0] - b[0], a[1] - b[1]) for b in Q) for a in P)
    return max(one(A, B), one(B, A))


def _n_ents(path):
    return len(list(ezdxf.readfile(str(path)).modelspace()))


# ---------------------------------------------------------------------------
def test_t1_wykaz():
    print("--- A) T1: wykaz roboczy mowi lustro (_L/_P, DODATKOWA KOLUMNA) ---")
    pl = W.wczytaj_pl_wykaz(WYKAZ, "SL40036103")
    check("A poz2 lustro=True", pl.get(2, {}).get("lustro") is True, f"pl2={pl.get(2)}")
    check("A poz2 pl='L'", pl.get(2, {}).get("pl") == "L", f"pl2={pl.get(2)}")
    check("A poz1 pl='P' nie-lustro", pl.get(1, {}).get("pl") == "P"
          and pl.get(1, {}).get("lustro") is False, f"pl1={pl.get(1)}")
    pary = W.wykryj_pary_pl(pl, [])
    check("A para P/L {2:1}", pary == {2: 1}, f"pary={pary}")
    POMIARY["T1_pary"] = pary


def test_mirror_unit():
    print("\n--- B) _odbij_lustro = mirror-X + wysrodkowanie (jednostkowo na p1) ---")
    tmp = Path(tempfile.mkdtemp(prefix="lustro_u_"))
    try:
        dst = tmp / "odbicie_p1.dxf"
        W._odbij_lustro(str(P1_WEJ), str(dst))
        ref = _mirror_x_center_verts(P1_WEJ)
        out = _verts(ezdxf.readfile(str(dst)).modelspace())
        mnn = _max_nn(out, ref)
        POMIARY["mirror_unit_max_nn"] = round(mnn, 6)
        check("B odbicie == mirror_x(p1) (max_nn<0.01mm)", mnn < 0.01, f"max_nn={mnn:.6f}mm")
        n_odb, n_p1 = _n_ents(dst), _n_ents(P1_WEJ)
        check("B liczba encji zachowana (nie 4-encjowy dymek)",
              n_odb == n_p1 and n_odb != 4, f"n_odbicie={n_odb} n_p1={n_p1}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e2e():
    print("\n--- C) end-to-end warianty_zlecenia na golden SL40036103 ---")
    out = Path(tempfile.mkdtemp(prefix="lustro_e2e_"))
    try:
        wiersze, _csv = W.warianty_zlecenia(CONV, WYKAZ, out)
        by = {w["posn"]: w for w in wiersze}
        r2 = by.get(2)
        check("C poz2 istnieje w ocenie", r2 is not None, f"posn={list(by)}")
        if r2 is None:
            return
        check("C poz2 zwyciezca = LUSTRO(pN)", str(r2["zwyciezca"]).startswith("LUSTRO"),
              f"zwyciezca={r2['zwyciezca']}")
        check("C poz2 semafor ZOLTY (nigdy auto-zielony)", r2["semafor"] == "zolty",
              f"semafor={r2['semafor']}")
        POMIARY["e2e_p2_status"] = r2["semafor"]
        POMIARY["e2e_p2_zwyciezca"] = r2["zwyciezca"]

        p1o, p2o = out / "SL40036103_p1.dxf", out / "SL40036103_p2.dxf"
        check("C p2 zapisany", p2o.exists(), f"{p2o}")
        if p2o.exists():
            n2 = _n_ents(p2o)
            check("C p2 to czesc, nie dymek (n!=4)", n2 != 4, f"n_p2={n2}")
            POMIARY["e2e_p2_n_ents"] = n2
        if p1o.exists() and p2o.exists():
            mnn = _max_nn(_verts(ezdxf.readfile(str(p2o)).modelspace()),
                          _mirror_x_center_verts(p1o))
            POMIARY["e2e_max_nn"] = round(mnn, 6)
            check("C p2 == mirror_x(p1_zwyciezcy) (max_nn<0.01mm)", mnn < 0.01,
                  f"max_nn={mnn:.6f}mm")
        # BONUS (INFO, nie failuje): linie giecia p1 na warstwie GIECIE (kol6-przed-linetype)
        if p1o.exists():
            m1 = ezdxf.readfile(str(p1o)).modelspace()
            n_g = sum(1 for e in m1 if str(e.dxf.layer).upper() == "GIECIE")
            POMIARY["bonus_p1_GIECIE"] = n_g
            print(f"    [INFO] bonus: p1 linie na warstwie GIECIE = {n_g} "
                  f"(oczekiwane 2 wg opis; 0 = zacommitowany kod NIE naprawil kol6-przed-linetype)")
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_kontrprzypadek():
    print("\n--- D) kontrprzypadek: 245 p1/p2 = 2 OSOBNE widoki, NIE lustro ---")
    # realne src-boxy z W-A na golden SL10599245_1_conv.dxf (zmierzone 2026-07-08):
    #   poz1 x[257.44..372.44]  poz2 x[40.93..155.93] - te same dims 1150x1130, ROZLACZNE.
    r1 = {"posn": "1", "wykaz_w": "1150.0", "wykaz_h": "1130.0",
          "src_x1": "257.44", "src_y1": "73.91", "src_x2": "372.44", "src_y2": "186.96",
          "status": "OK (TRYB BEZ WARSTW)"}
    r2 = {"posn": "2", "wykaz_w": "1150.0", "wykaz_h": "1130.0",
          "src_x1": "40.93", "src_y1": "73.91", "src_x2": "155.93", "src_y2": "186.96",
          "status": "OK (TRYB BEZ WARSTW)"}
    pary = W.wykryj_pary_pl({}, [r1, r2])
    check("D 245 (2 osobne widoki) NIE sklejone", pary == {},
          f"pary={pary} (asymetryczne blizniaki - p1 z owalem, p2 bez)")
    check("D _ten_sam_widok rozlaczne=False", W._ten_sam_widok(r1, r2) is False)
    POMIARY["kontr_245_pary"] = pary

    # kontrola dodatnia: gdyby to byl JEDEN wspolny widok (nakladajace boxy) -> sklejone
    o1 = {"posn": "1", "wykaz_w": "300", "wykaz_h": "200",
          "src_x1": "0", "src_y1": "0", "src_x2": "100", "src_y2": "100", "status": ""}
    o2 = {"posn": "2", "wykaz_w": "300", "wykaz_h": "200",
          "src_x1": "5", "src_y1": "5", "src_x2": "105", "src_y2": "105", "status": ""}
    pary2 = W.wykryj_pary_pl({}, [o1, o2])
    check("D kontrola dodatnia (wspolny widok) -> {2:1}", pary2 == {2: 1},
          f"pary={pary2}")
    check("D _ten_sam_widok nakladka=True", W._ten_sam_widok(o1, o2) is True)


def main():
    print("=== TEST LUSTRA PAR P/L (PATCH 4, produkcja/warianty.py) ===\n")
    test_t1_wykaz()
    test_mirror_unit()
    test_e2e()
    test_kontrprzypadek()
    print("\n--- POMIARY ---")
    for k, v in POMIARY.items():
        print(f"    {k} = {v}")
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== LUSTRO: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== LUSTRO: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
