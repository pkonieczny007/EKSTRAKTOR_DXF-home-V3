# -*- coding: utf-8 -*-
"""Test UWAGA-pass w silniku W-C: otwory INNEGO koloru niz kontur.

Root-fix (werdykt operatora 41_2050, SL40062903_p1): W-C ekstrahuje po JEDNYM
trybie/kolorze -> gubi otwory narysowane innym kolorem niz kontur. UWAGA-pass
(port z W-D, patch_uwaga_pass.uwaga_pass) DOKLADA (ADDITIVE) zamkniete petle
innego koloru scisle wewnatrz obrysu.

  T-62903  golden 'otwory inny kolor' (box hardcode, scale 2.0):
           PRZED (sam tryb bazowy col2) = 2 kontury wewn. (dowod luki, FAIL bez passa);
           PO   (z UWAGA-pass)          = 6 konturow, 4 okregi col4 (r6.5) OBECNE,
                2 okregi col2 (r6.0), uwaga_pass==4, brak NIEDOMKNIETE, wym 396.8x195.
  T-34116  GUARD 0 regresji: brak obcych petli (col4=osie) -> uwaga_pass==0,
           interior 38 / okregi 7 BEZ ZMIAN.
  T-61302  GUARD 0 regresji: 3 sloty col2, col4=osie -> uwaga_pass==0,
           interior 3 BEZ ZMIAN.

Test dziala PRZED i PO wpieciu patcha do produkcji:
  - jesli produkcyjny extract_region_warstwa juz zwraca 'uwaga_pass' -> testuje produkcje;
  - jesli jeszcze nie -> sklada wiazke wg INSTRUKCJI WPIECIA z patch_uwaga_pass.py
    (zbierz_region + detect_geom_layer + wybierz_tryb + uwaga_pass) i testuje ja,
    z GLOSNYM ostrzezeniem "PATCH NIEWPIETY". Po wpieciu przez orkiestratora znika.

Uzycie:  python testy\\test_uwaga_pass.py     (exit 0 = PASS)
"""
import io
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb
from ezdxf.math import Matrix44

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
# Po przeniesieniu do testy/ : HERE=testy/, golden=testy/golden. Ze scratchpada:
# fallback na znane repo (zeby dalo sie uruchomic przed przeniesieniem).
_REPO = Path(r"c:/Python_CLaude/EKSTRAKTOR_DXF/EKSTRAKTOR_DXF-home-V3")
GOLDEN = HERE / "golden" if (HERE / "golden").exists() else _REPO / "testy" / "golden"
_ROOT = HERE.parent if (HERE / "golden").exists() else _REPO
SILNIKI = _ROOT / "produkcja" / "silniki"
KONTROLA = _ROOT / "produkcja" / "kontrola"
sys.path.insert(0, str(SILNIKI))
sys.path.insert(0, str(KONTROLA))

# patch_uwaga_pass.py: docelowo wkleic do region_warstwa.py; tu testujemy modul
# lezacy obok testu (po przeniesieniu do testy/ dolozyc kopie/symlink lub import
# z produkcja/silniki po wpieciu).
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import region_warstwa as WC                                    # noqa: E402
from bilans_konturow import count_interior_contours_shapely    # noqa: E402

FAILS = []
CHECKS = 0
PATCH_WPIETY = None


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def approx(a, b, tol=0.05):
    return a is not None and abs(a - b) <= tol


def _import_uwaga_pass():
    """uwaga_pass: z produkcji (po wpieciu) albo z modulu patcha (przed)."""
    try:
        from region_warstwa import uwaga_pass  # po wpieciu (D) instrukcji
        return uwaga_pass, True
    except Exception:
        from patch_uwaga_pass import uwaga_pass  # przed wpieciem (deliverable)
        return uwaga_pass, False


def _extract(msp, box, scale, is_pl=False, dedup_tol=0.3, sag=0.1, snap=0.1):
    """Zwraca (info, doc). Preferuje produkcyjny extract_region_warstwa gdy juz
    ma UWAGA-pass; inaczej sklada wiazke wg INSTRUKCJI WPIECIA (dowod, ze wpiecie
    da ten sam wynik). Zwrotka ujednolicona: interior, circ_dedup, uwaga_pass,
    uwaga_kolory, wx, wy, niedomkniete, r65, r60."""
    global PATCH_WPIETY
    # 1) produkcja juz wpieta?
    doc0, info0 = WC.extract_region_warstwa(msp, box, scale, is_pl=is_pl)
    if "uwaga_pass" in info0:
        PATCH_WPIETY = True
        circ = [e for e in doc0.modelspace() if e.dxftype() == "CIRCLE"]
        info0["r65"] = sum(1 for e in circ if abs(e.dxf.radius - 6.5) < 0.05)
        info0["r60"] = sum(1 for e in circ if abs(e.dxf.radius - 6.0) < 0.05)
        info0["niedomkniete"] = any(str(f).startswith("NIEDOMKNIETE")
                                    for f in info0["interior_detale"]["flags"])
        info0["circ_dedup_out"] = info0["circ_dedup"]
        return info0, doc0
    # 2) przed wpieciem: skladamy wiazke jak w patchu (C)(D)
    PATCH_WPIETY = False
    uwaga_pass, _ = _import_uwaga_pass()
    picked, bends_all, lcs = WC.zbierz_region(msp, box)
    det_layer, _fb = WC.detect_geom_layer(picked)
    tryb, geom_ents, _diag = WC.wybierz_tryb(picked, det_layer, sag, snap)
    gids = {id(e) for e in geom_ents}
    other = [e for e, _ec in picked if id(e) not in gids]
    add_circles, add_others, up = uwaga_pass(geom_ents, other, lcs)
    wg = {e.dxf.layer for e in geom_ents}
    bends = [e for e in bends_all if e.dxf.layer in wg or e.dxf.layer.upper() == "GIECIE"]
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    m = Matrix44.translate(-cx, -cy, 0) @ Matrix44.scale(scale, scale, 1)
    new = ezdxf.new(dxfversion="AC1021")
    new.layers.add("GIECIE", color=6)
    nmsp = new.modelspace()
    circles = []
    for e in list(geom_ents) + list(add_circles):
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "0"
        ne.dxf.color = 7
        (circles.append(ne) if ne.dxftype() == "CIRCLE" else nmsp.add_entity(ne))
    for e in add_others:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "0"
        ne.dxf.color = 7
        nmsp.add_entity(ne)
    grupy = []
    for ne in circles:
        c = WC._wcs_center(ne)
        for gc, lst in grupy:
            if math.hypot(c.x - gc.x, c.y - gc.y) <= dedup_tol:
                lst.append(ne)
                break
        else:
            grupy.append((c, [ne]))
    for gc, lst in grupy:
        best = min(lst, key=lambda c: c.dxf.radius)
        best.dxf.center = (gc.x, gc.y, 0)
        best.dxf.extrusion = (0, 0, 1)
        nmsp.add_entity(best)
    for e in bends:
        if not (is_pl or WC.is_skos(e)):
            continue
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "GIECIE"
        ne.dxf.color = 6
        nmsp.add_entity(ne)
    ext = _bb.extents(nmsp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2.0,
                            -(ext.extmin.y + ext.extmax.y) / 2.0, 0)
    for e in nmsp:
        e.transform(mv)
    ext = _bb.extents(nmsp)
    interior, det = count_interior_contours_shapely(list(nmsp), sagitta=sag,
                                                    snap_tol=snap, dedup_center_tol=dedup_tol)
    info = dict(tryb=tryb, interior=interior, circ_dedup_out=det["circles_dedup"],
                uwaga_pass=up["uwaga_pass"], uwaga_kolory=sorted(up["obce_kolory"]),
                wymiar_x=round(ext.size.x, 2), wymiar_y=round(ext.size.y, 2),
                niedomkniete=any(str(f).startswith("NIEDOMKNIETE") for f in det["flags"]),
                r65=sum(1 for e in nmsp if e.dxftype() == "CIRCLE" and abs(e.dxf.radius - 6.5) < 0.05),
                r60=sum(1 for e in nmsp if e.dxftype() == "CIRCLE" and abs(e.dxf.radius - 6.0) < 0.05))
    return info, new


def _base_interior(msp, box, sag=0.1, snap=0.1):
    """Interior samego trybu bazowego (bez UWAGA-pass) = stan PRZED (dowod luki)."""
    picked, _b, _lc = WC.zbierz_region(msp, box)
    det_layer, _fb = WC.detect_geom_layer(picked)
    tryb, _ge, diag = WC.wybierz_tryb(picked, det_layer, sag, snap)
    return tryb, diag["metryki"][tryb]["interior"]


def test_62903():
    rel = "SL40062903_p1_otwory_inny_kolor/wejscie/SL40062903_1.dxf"
    box = (79.16, 149.91, 277.56, 247.41)      # bbox konturu col2 = wzorzec/2.0
    scale = 2.0
    msp = ezdxf.readfile(GOLDEN / rel).modelspace()
    # PRZED: sam tryb bazowy gubi otwory col4
    tryb, przed = _base_interior(msp, box)
    check("62903 PRZED luka", tryb == "col2" and przed == 2,
          f"tryb={tryb} interior_bazowy={przed} (oczekiwano col2/2)")
    # PO: UWAGA-pass odtwarza 6 konturow
    info, _doc = _extract(msp, box, scale, is_pl=False)
    check("62903 interior=6", info["interior"] == 6, f"interior={info['interior']}")
    check("62903 uwaga_pass=4", info["uwaga_pass"] == 4, f"uwaga_pass={info['uwaga_pass']}")
    check("62903 kolor obcy=4", info.get("uwaga_kolory") in ([4], None) or 4 in (info.get("uwaga_kolory") or [4]),
          f"kolory={info.get('uwaga_kolory')}")
    check("62903 okregi col4 obecne (4x r6.5)", info["r65"] == 4, f"r6.5={info['r65']}")
    check("62903 okregi col2 (2x r6.0)", info["r60"] == 2, f"r6.0={info['r60']}")
    check("62903 circ_dedup=6", info["circ_dedup_out"] == 6, f"circ={info['circ_dedup_out']}")
    check("62903 kontur domkniety", not info["niedomkniete"], "NIEDOMKNIETE w wyniku")
    check("62903 wymiar", approx(info["wymiar_x"], 396.8, 0.5) and approx(info["wymiar_y"], 195.0, 0.5),
          f"wym={info['wymiar_x']}x{info['wymiar_y']}")
    print(f"  T-62903  PRZED tryb={tryb} interior={przed}  ->  PO interior={info['interior']} "
          f"circ={info['circ_dedup_out']} (r6.5={info['r65']} r6.0={info['r60']}) "
          f"uwaga_pass={info['uwaga_pass']} wym={info['wymiar_x']}x{info['wymiar_y']}")


def test_guard_34116():
    rel = "SL40034116_p1_zgubione_otwory/wejscie/SL40034116_1_conv.dxf"
    box = (43.85, 50.87, 205.45, 219.32)
    msp = ezdxf.readfile(GOLDEN / rel).modelspace()
    info, _doc = _extract(msp, box, 5.0, is_pl=True)
    check("34116 GUARD uwaga_pass=0", info["uwaga_pass"] == 0, f"uwaga_pass={info['uwaga_pass']}")
    check("34116 GUARD interior=38", info["interior"] == 38, f"interior={info['interior']}")
    check("34116 GUARD circ=7", info["circ_dedup_out"] == 7, f"circ={info['circ_dedup_out']}")
    check("34116 GUARD kontur domkniety", not info["niedomkniete"], "NIEDOMKNIETE")
    print(f"  T-34116  GUARD interior={info['interior']} circ={info['circ_dedup_out']} "
          f"uwaga_pass={info['uwaga_pass']} (0 regresji)")


def test_guard_61302():
    rel = "SL40061302_sloty_odseparowane/wejscie/SL40061302_1_conv.dxf"
    box = (50.83, 136.99, 194.3, 241.99)
    msp = ezdxf.readfile(GOLDEN / rel).modelspace()
    info, _doc = _extract(msp, box, 2.0, is_pl=True)
    check("61302 GUARD uwaga_pass=0", info["uwaga_pass"] == 0, f"uwaga_pass={info['uwaga_pass']}")
    check("61302 GUARD interior=3", info["interior"] == 3, f"interior={info['interior']}")
    check("61302 GUARD kontur domkniety", not info["niedomkniete"], "NIEDOMKNIETE")
    print(f"  T-61302  GUARD interior={info['interior']} circ={info['circ_dedup_out']} "
          f"uwaga_pass={info['uwaga_pass']} (0 regresji)")


def main():
    print("=== TEST UWAGA-pass (otwory innego koloru niz kontur) ===\n")
    test_62903()
    test_guard_34116()
    test_guard_61302()
    print(f"\n  [tryb testu] PATCH_WPIETY_DO_PRODUKCJI = {PATCH_WPIETY}"
          + ("" if PATCH_WPIETY else "  <-- GLOSNO: patch jeszcze nie w region_warstwa.py; "
                                     "testowano przez patch_uwaga_pass (deliverable)"))
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== UWAGA-pass: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== UWAGA-pass: PASS (otwory innego koloru odzyskane; guardy 0 regresji) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
