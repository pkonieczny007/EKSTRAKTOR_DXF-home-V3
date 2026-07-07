# -*- coding: utf-8 -*-
"""Test gwintow Hardox (detekcja + transformacja + bramka 2 swiadoma gwintu).

DOCELOWO: testy/test_gwint.py (import z produkcja.kontrola.gwint).
W scratchpadzie importuje gwint_hardox.py (prototyp fable).

Sprawdza (syntetyczny DXF + golden):
 1. detekcja: okrag+luk 270 st = 1 gwint (M10); zwykly okrag = nie-gwint
 2. transformacja z tablica: luk USUNIETY, okrag powiekszony, kolor 1 (czerwony)
 3. tablica pusta (null): 100% nietkniete + status min. zolty
 4. M nierozpoznane (luk poza nominalami): nietkniete + zolty
 5. bramka 2: konce luku gwintu wykluczone (2 -> 0), realny otwarty zostaje
 6. lustro (OCS, extrusion -Z): detekcja dziala
 7. materialy: regex trudnoscieralny (HB 450 tak, S355/wymiary nie)
 8. golden SL40852200_p1 (M10 z notatki gwint-okrag-luk-dimension): 1 gwint,
    bramka2 2->0; golden SL40061302 (material zwykly): 0 detekcji
"""
import io
import sys
from pathlib import Path

import ezdxf

BASE = Path(__file__).resolve().parents[1] if \
    (Path(__file__).resolve().parents[0].name == "testy") else None
if BASE:  # po przeniesieniu do testy/
    sys.path.insert(0, str(BASE))
    sys.path.insert(0, str(BASE / "produkcja" / "kontrola"))
    from produkcja.kontrola import gwint as gw
    try:  # bramka 5 z wpietym gwintem (PATCH 1) - dowod wpiecia u ZRODLA
        from bilans_konturow import count_interior_contours_shapely as _bramka5
    except Exception:
        _bramka5 = None
    GOLDEN = BASE / "testy/golden"
else:     # prototyp w scratchpadzie
    sys.path.insert(0, str(Path(__file__).parent))
    import gwint_hardox as gw
    _bramka5 = None
    GOLDEN = Path(r"C:\Python_CLaude\EKSTRAKTOR_DXF\EKSTRAKTOR_DXF-home-V3"
                  ) / "testy/golden"

WYNIKI = {"pass": 0, "fail": 0}


def check(nazwa, warunek, info=""):
    if warunek:
        WYNIKI["pass"] += 1
        print("  [OK]   %s" % nazwa)
    else:
        WYNIKI["fail"] += 1
        print("  [FAIL] %s %s" % (nazwa, info))


def syntetyczny():
    """Blacha 100x60 (zamknieta LWPOLYLINE) + gwint M10 (okrag o8.5 + luk o10
    270 st) + zwykly okrag o12 + luk 'M?' (o7.1, poza nominalami)
    + realnie otwarta linia."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)], close=True)
    # gwint M10: wiercenie o8.5 + luk nominalny o10, 75->345 (270 st)
    msp.add_circle((20, 30), 4.25)
    msp.add_arc((20, 30), 5.0, 75, 345)
    # zwykly otwor o12 (bez luku)
    msp.add_circle((50, 30), 6.0)
    # kandydat z lukiem poza nominalami: okrag o6.1 + luk o7.1 (ratio 1.164 OK,
    # ale o7.1 nie pasuje do M3..M24 w tol 0.3) -> M? -> zostaw
    msp.add_circle((80, 30), 3.05)
    msp.add_arc((80, 30), 3.55, 80, 350)
    return doc


def main():
    print("=== test_gwint: detekcja + transformacja + bramka 2 ===")

    # --- 1. detekcja na syntetyku ---
    doc = syntetyczny()
    msp = doc.modelspace()
    handles, gwinty = gw.thread_arcs(msp)
    check("detekcja: 2 kandydaty gwintu (M10 + M?)", len(gwinty) == 2,
          "znaleziono %d" % len(gwinty))
    ms = sorted(gw.m_z_luku(g["r_luk"]) or "M?" for g in gwinty)
    check("rozmiary: M10 + M? (z nominalu luku)", ms == ["M10", "M?"], ms)
    n_circ = sum(1 for e in msp if e.dxftype() == "CIRCLE")
    check("zwykly okrag o12 NIE jest gwintem", n_circ == 3 and
          all(abs(g["r_okr"] - 6.0) > 1e-9 for g in gwinty))

    # --- 2. bramka 2: luki gwintu wykluczone ---
    b2 = gw.wyklucz_z_bramki2(msp)
    check("bramka2 surowo: 4 otwarte konce (2 luki x 2)",
          b2["otwarte_surowe"] == 4, b2)
    check("bramka2 bez gwintow: 0 otwartych",
          b2["otwarte_bez_gwintow"] == 0, b2)

    # --- 2b. realnie otwarta linia NIE znika przez wykluczenie ---
    msp.add_line((10, -20), (40, -20))
    b2b = gw.wyklucz_z_bramki2(msp)
    check("realny otwarty koniec zostaje po wykluczeniu gwintow",
          b2b["otwarte_bez_gwintow"] == 2, b2b)

    # --- 3. transformacja z tablica (M10 -> 11.0 TESTOWO) ---
    doc = syntetyczny()
    msp = doc.modelspace()
    zmiany = gw.transformuj(msp, {"M10": 11.0})
    zm = [z for z in zmiany if z["akcja"] == "zmieniony"]
    zo = [z for z in zmiany if z["akcja"] == "zostaw"]
    check("transformacja: 1 zmieniony (M10), 1 zostawiony (M?)",
          len(zm) == 1 and len(zo) == 1 and zm[0]["m"] == "M10", zmiany)
    arcs = [e for e in msp if e.dxftype() == "ARC"]
    check("luk gwintu M10 USUNIETY (zostal tylko luk M?)",
          len(arcs) == 1 and abs(float(arcs[0].dxf.radius) - 3.55) < 1e-9)
    red = [e for e in msp if e.dxftype() == "CIRCLE" and e.dxf.color == 1]
    check("okrag powiekszony do o11 i CZERWONY (kolor 1)",
          len(red) == 1 and abs(2 * float(red[0].dxf.radius) - 11.0) < 1e-9)
    zwykly = [e for e in msp if e.dxftype() == "CIRCLE"
              and abs(float(e.dxf.radius) - 6.0) < 1e-9]
    check("zwykly okrag NIETKNIETY (o12, kolor bez zmian)",
          len(zwykly) == 1 and zwykly[0].dxf.color != 1)
    check("status po transformacji: zolty (M? zostal)",
          gw.status_po_transformacji(zmiany) == "zolty")

    # --- 4. tablica PUSTA / null -> nic nie ruszone ---
    doc = syntetyczny()
    msp = doc.modelspace()
    przed = sorted((e.dxftype(), round(float(getattr(e.dxf, "radius", 0)), 6),
                    e.dxf.color) for e in msp)
    for tab in ({}, {"M10": None}, None):
        zmiany = gw.transformuj(msp, tab)
        po = sorted((e.dxftype(), round(float(getattr(e.dxf, "radius", 0)), 6),
                     e.dxf.color) for e in msp)
        check("tablica %r: plik nietkniety, wszystko 'zostaw'" % (tab,),
              przed == po and all(z["akcja"] == "zostaw" for z in zmiany)
              and gw.status_po_transformacji(zmiany) == "zolty")

    # --- 5. lustro: OCS extrusion -Z ---
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    c = msp.add_circle((20, 30), 4.25)
    c.dxf.extrusion = (0, 0, -1)
    a = msp.add_arc((20, 30), 5.0, 75, 345)
    a.dxf.extrusion = (0, 0, -1)
    _, gwinty = gw.thread_arcs(msp)
    check("lustro OCS (extrusion -Z): gwint wykryty", len(gwinty) == 1)

    # --- 6. material ---
    check("material: 'Blech s=10 HB 450' trudnoscieralny",
          gw.czy_trudnoscieralny("Blech s=10 HB 450"))
    check("material: 'HARDOX 450' trudnoscieralny",
          gw.czy_trudnoscieralny("HARDOX 450"))
    check("material: 'S355JR' NIE",
          not gw.czy_trudnoscieralny("S355JR"))
    check("material: 'Blech 400 x 250 x 12' NIE (400 to wymiar)",
          not gw.czy_trudnoscieralny("Blech 400 x 250 x 12"))

    # --- 7. golden (realne dane w repo) ---
    f_gwint = GOLDEN / "38_1847_gr4/wynikow/SL40852200/SL40852200_p1.dxf"
    if f_gwint.exists():
        msp = ezdxf.readfile(f_gwint).modelspace()
        _, gwinty = gw.thread_arcs(msp)
        b2 = gw.wyklucz_z_bramki2(msp)
        check("golden SL40852200_p1: 1 gwint M10 (zrodlo notatki)",
              len(gwinty) == 1 and gw.m_z_luku(gwinty[0]["r_luk"]) == "M10",
              [(2 * g["r_okr"], 2 * g["r_luk"]) for g in gwinty])
        check("golden SL40852200_p1: bramka2 %d->0 (falszywa czerwien znika)"
              % b2["otwarte_surowe"], b2["otwarte_bez_gwintow"] == 0, b2)
    else:
        print("  [SKIP] brak %s" % f_gwint)
    f_zwykly = GOLDEN / "SL40061302_sloty_odseparowane/wzorzec/SL40061302_p1.dxf"
    if f_zwykly.exists():
        doc = ezdxf.readfile(f_zwykly)
        msp = doc.modelspace()
        _, gwinty = gw.thread_arcs(msp)
        zmiany = gw.transformuj(msp, {"M10": 11.0, "M12": 13.0})
        check("golden SL40061302 (zwykly material): 0 gwintow, 0 zmian",
              len(gwinty) == 0 and len(zmiany) == 0)
    else:
        print("  [SKIP] brak %s" % f_zwykly)

    # --- 8. golden gwint_hb450 (SL10582645_p5: 8x M12 na HB450) ---
    f_hb = GOLDEN / "gwint_hb450/wzorzec/SL10582645_p5.dxf"
    if f_hb.exists():
        msp = ezdxf.readfile(f_hb).modelspace()
        _, gwinty = gw.thread_arcs(msp)
        ms = sorted(gw.m_z_luku(g["r_luk"]) or "M?" for g in gwinty)
        check("golden gwint_hb450 SL10582645_p5: 8 gwintow M12",
              len(gwinty) == 8 and set(ms) == {"M12"}, ms)
        b2 = gw.wyklucz_z_bramki2(msp)
        check("golden gwint_hb450: bramka2 %d->0 (8 lukow gwintu wykluczone)"
              % b2["otwarte_surowe"], b2["otwarte_bez_gwintow"] == 0, b2)
    else:
        print("  [SKIP] brak %s" % f_hb)

    # --- 9. PATCH 1: gwint wpiety do BRAMKI 5 (bilans_konturow) u ZRODLA ---
    if _bramka5 is not None:
        # gwint_hb450: 8 lukow gwintu -> thread_skipped=8, ZERO NIEDOMKNIETE, interior=8
        if f_hb.exists():
            n, det = _bramka5(ezdxf.readfile(f_hb).modelspace())
            nd = any(str(fl).startswith("NIEDOMKNIETE") for fl in det["flags"])
            check("bramka5 gwint_hb450: thread_skipped=8, interior=8, bez NIEDOMKNIETE",
                  det.get("thread_skipped") == 8 and n == 8 and not nd,
                  f"thread_skipped={det.get('thread_skipped')} interior={n} flags={det['flags']}")
        # SL40852200_p1: 1 luk gwintu M10 -> falszywa czerwien (NIEDOMKNIETE) znika
        if f_gwint.exists():
            n, det = _bramka5(ezdxf.readfile(f_gwint).modelspace())
            nd = any(str(fl).startswith("NIEDOMKNIETE") for fl in det["flags"])
            check("bramka5 SL40852200_p1: thread_skipped=1, bez NIEDOMKNIETE (falszywa czerwien)",
                  det.get("thread_skipped") == 1 and not nd,
                  f"thread_skipped={det.get('thread_skipped')} flags={det['flags']}")
        # GUARD material zwykly: 0 gwintow -> thread_skipped=0, bilans bez zmian
        for rel in ("SL40061302_sloty_odseparowane/wzorzec/SL40061302_p1.dxf",
                    "SL40034116_p1_zgubione_otwory/wejscie/SL40034116_1_conv.dxf"):
            fz = GOLDEN / rel
            if fz.exists():
                _, det = _bramka5(ezdxf.readfile(fz).modelspace())
                check("bramka5 GUARD %s: thread_skipped=0 (material zwykly bez zmian)"
                      % rel.split("/")[0], det.get("thread_skipped") == 0,
                      f"thread_skipped={det.get('thread_skipped')}")
    else:
        print("  [SKIP] bramka5 (bilans_konturow) niedostepna - prototyp scratchpad")

    print("\nWYNIK: %d PASS, %d FAIL" % (WYNIKI["pass"], WYNIKI["fail"]))
    return 1 if WYNIKI["fail"] else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.exit(main())
