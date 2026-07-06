# -*- coding: utf-8 -*-
"""Testy silnika W-C region+warstwa (produkcja/silniki/region_warstwa.py).

W-C to root-fix na cechy ODSEPAROWANE. Test dowodzi, ze na widokach golden
ODTWARZA PELNA KOMPLETNOSC (te cechy, ktore W-A/W-B gubi) i czyta okregi
OCS-poprawnie (fix zaakceptowany 2026-07-05).

  T1 import bez efektow ubocznych (0 nowych plikow z obcego cwd);
  T2 SL10596945 fasola  -> interior 4, okregi 4->2 (fertzing dedup), giecie 1, wym 282.40x260.24;
  T3 SL40061302 sloty   -> tryb col2 (kolor 2!), fallback warstwy, interior 3, giecie 4, wym 286.94x210;
  T4 SL10582608 owal     -> interior 12, okregi 5, giecie 3, wym 449.00x365.27;
  T5 golden OCS lustrzany okrag -> dedup po WCS = 1 grupa (nie 2), zostaje najmniejszy;
  T6 kazdy wynik wysrodkowany (srodek bbox 0,0) i bez flag NIEDOMKNIETE.

Uzycie:  python testy\\test_wc.py     (exit 0 = PASS)
"""
import io
import subprocess
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
SILNIKI = HERE.parent / "produkcja" / "silniki"
sys.path.insert(0, str(SILNIKI))
from region_warstwa import extract_region_warstwa, _wcs_center  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def approx(a, b, tol=0.02):
    return a is not None and abs(a - b) <= tol


# (nazwa, zrodlo, box, scale, oczekiwania)
CASES = [
    ("SL10596945", "SL10596945_fasola_odseparowana/wejscie/SL10596945_1_conv.dxf",
     (434.17, 153.97, 490.68, 206.05), 5.0,
     dict(interior=4, circ_raw=4, circ_dedup=2, bends_kept=1, wx=282.40, wy=260.24,
          geom_layer="53")),
    ("SL40061302", "SL40061302_sloty_odseparowane/wejscie/SL40061302_1_conv.dxf",
     (50.83, 136.99, 194.3, 241.99), 2.0,
     dict(interior=3, tryb="col2", warstwa_fallback=True, bends_kept=4, wx=286.94, wy=210.00)),
    ("SL10582608", "SL10582608_owal_odseparowany_klaster/wejscie/SL10582608_1.dxf",
     (113.14, 78.46, 202.94, 151.51), 5.0,
     dict(interior=12, circ_dedup=5, bends_kept=3, wx=449.00, wy=365.27)),
]


def test_t1_import():
    """Import z OBCEGO cwd nie tworzy plikow (zero efektow ubocznych)."""
    code = (
        "import os,sys; sys.path.insert(0, r'%s'); "
        "b=set(os.listdir(r'%s')); import region_warstwa; "
        "a=set(os.listdir(r'%s')); print('NEW='+repr(sorted(a-b)))"
        % (SILNIKI, SILNIKI, SILNIKI)
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(Path.home()), encoding="utf-8", errors="replace")
    new = "NEW=[]" in r.stdout
    check("T1 import bez efektow ubocznych", new, f"stdout={r.stdout.strip()} err={r.stderr[-200:]}")
    print(f"  T1 import z obcego cwd: {'0 nowych plikow' if new else 'EFEKT UBOCZNY!'}")


def test_reprodukcja():
    print("\n  odtworzenie kompletnosci (is_pl=True - pary P/L):")
    for nm, rel, box, scale, oc in CASES:
        msp = ezdxf.readfile(GOLDEN / rel).modelspace()
        doc, info = extract_region_warstwa(msp, box, scale, is_pl=True)
        check(f"{nm} interior", info["interior"] == oc["interior"],
              f"interior={info['interior']} != {oc['interior']}")
        for k in ("circ_raw", "circ_dedup", "bends_kept", "tryb", "warstwa_fallback",
                  "geom_layer"):
            if k in oc:
                check(f"{nm} {k}", info[k] == oc[k], f"{k}={info[k]} != {oc[k]}")
        check(f"{nm} wymiar_x", approx(info["wymiar_x"], oc["wx"]),
              f"wx={info['wymiar_x']} != {oc['wx']}")
        check(f"{nm} wymiar_y", approx(info["wymiar_y"], oc["wy"]),
              f"wy={info['wymiar_y']} != {oc['wy']}")
        # T6: wysrodkowanie (0,0) + brak NIEDOMKNIETE
        ext = _bb.extents(list(doc.modelspace()))
        cx = (ext.extmin.x + ext.extmax.x) / 2
        cy = (ext.extmin.y + ext.extmax.y) / 2
        check(f"{nm} wysrodkowany", abs(cx) <= 0.01 and abs(cy) <= 0.01,
              f"srodek=({cx:.3f},{cy:.3f})")
        niedom = any(fl.startswith("NIEDOMKNIETE") for fl in info["interior_detale"]["flags"])
        check(f"{nm} kontur domkniety", not niedom, f"flags={info['interior_detale']['flags']}")
        print(f"  {nm:12} tryb={info['tryb']:13} interior={info['interior']:2} "
              f"okr={info['circ_raw']}->{info['circ_dedup']} giecie={info['bends_kept']} "
              f"wym={info['wymiar_x']}x{info['wymiar_y']} srodek=({cx:.3f},{cy:.3f})")


def test_t5_ocs():
    """Golden OCS: dedup po WCS grupuje fertzing lustrzany (raw by nie sparowal)."""
    f = GOLDEN / "lustrzany_okrag_ocs/wejscie/lustrzany_okrag_ocs.dxf"
    msp = ezdxf.readfile(f).modelspace()
    circ = [e for e in msp if e.dxftype() == "CIRCLE"]
    check("T5 golden ma 2 okregi", len(circ) == 2, f"{len(circ)}")
    # surowe srodki roznia sie (mirror OCS), WCS sie pokrywaja
    raw = [(e.dxf.center.x, e.dxf.center.y) for e in circ]
    wcs = [(_wcs_center(e).x, _wcs_center(e).y) for e in circ]
    raw_grupy = len({(round(x, 1), round(y, 1)) for x, y in raw})
    wcs_grupy = len({(round(x, 1), round(y, 1)) for x, y in wcs})
    check("T5 raw = 2 grupy (blad)", raw_grupy == 2, f"raw_grupy={raw_grupy} raw={raw}")
    check("T5 WCS = 1 grupa (fix)", wcs_grupy == 1, f"wcs_grupy={wcs_grupy} wcs={wcs}")
    r_min = min(e.dxf.radius for e in circ)
    print(f"  T5 OCS: raw={raw_grupy} grupy (blad), WCS={wcs_grupy} grupa (fix); "
          f"zostaje r_min={r_min}")


def main():
    print("=== TESTY W-C region+warstwa ===\n")
    test_t1_import()
    test_reprodukcja()
    test_t5_ocs()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== W-C: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== W-C: PASS (region+warstwa odtwarza kompletnosc, OCS-poprawny) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
