# -*- coding: utf-8 -*-
"""Testy silnika W-D dwutorowy (produkcja/silniki/wd_dwutorowy.py).

W-D = root-fix na (a) cechy ODSEPAROWANE (point-in-polygon, nie gap) i (b) otwory
INNEGO koloru niz kontur (UWAGA-pass). Test dowodzi, ze na widokach golden odtwarza
kompletnosc konturow, domyka kontur (0 otwartych) i lapie otwory obcego koloru.
TOR 1 (box+skala) przychodzi Z ZEWNATRZ (jak w W-C). Wartosci = zmierzony prototyp v2.

  T1 import bez efektow ubocznych (0 nowych plikow z obcego cwd);
  T2 SL40034116 zgubione otwory (klaster gubil 13 Langlochow) -> interior 38, okregi 7,
     0 otwartych, giecia 2, wym 808.0x842.27;
  T3 SL40061302 sloty odseparowane -> interior 3, kolor bazowy 2 (nie 7!), giecia 4,
     wym 286.94x210;
  T4 SL40062903 otwory INNEGO koloru -> interior 6 == wzorzec gotowe, UWAGA-pass>0
     (otwory koloru 4 przy bazowym 2), wynik ZAWIERA encje koloru 4, wym 396.8x195;
  T5 SL10596945 fasola odseparowana -> zgodnosc z wzorcem p3 (interior 4, okregi 2),
     wym 282.4x260.24;
  T6 kazdy wynik: outer==1, brak flagi NIEDOMKNIETE, wysrodkowany (srodek bbox 0,0).

Uzycie:  python testy\\test_wd.py     (exit 0 = PASS)
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
KONTROLA = HERE.parent / "produkcja" / "kontrola"
sys.path.insert(0, str(SILNIKI))
sys.path.insert(0, str(KONTROLA))
from wd_dwutorowy import extract_wd            # noqa: E402
from bilans_konturow import count_interior_contours_shapely  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def approx(a, b, tol=0.05):
    return a is not None and abs(a - b) <= tol


def _wzorzec_interior(rel):
    """Kontury wewn. + okregi (po dedupie) pliku wzorca - target dla porownania."""
    ents = list(ezdxf.readfile(GOLDEN / rel).modelspace())
    n, det = count_interior_contours_shapely(ents)
    return n, det["circles_dedup"]


# (nazwa, zrodlo, box, scale, is_pl, oczekiwania)
# box+scale = TOR 1 (z zewnatrz). Dla SL40062903 box = klaster W-A widoku p1
# (cluster_entities gap=8), scale 2.0 (w=198.40 -> 396.8).
CASES = [
    ("SL40034116", "SL40034116_p1_zgubione_otwory/wejscie/SL40034116_1_conv.dxf",
     (43.85, 50.87, 205.45, 219.32), 5.0, False,
     dict(interior=38, circ=7, oe=0, n_bend=2, wx=808.0, wy=842.27, baza=7, uwaga=0)),
    ("SL40061302", "SL40061302_sloty_odseparowane/wejscie/SL40061302_1_conv.dxf",
     (50.83, 136.99, 194.3, 241.99), 2.0, False,
     dict(interior=3, circ=0, oe=0, n_bend=4, wx=286.94, wy=210.0, baza=2, uwaga=0)),
    ("SL10596945", "SL10596945_fasola_odseparowana/wejscie/SL10596945_1_conv.dxf",
     (434.17, 153.97, 490.68, 206.05), 5.0, False,
     dict(interior=4, circ=2, oe=0, n_bend=1, wx=282.40, wy=260.24, baza=7, uwaga=0,
          wzorzec="SL10596945_fasola_odseparowana/wzorzec/SL10596945_p3.dxf")),
    ("SL40062903", "SL40062903_p1_otwory_inny_kolor/wejscie/SL40062903_1.dxf",
     (79.16, 143.91, 277.56, 250.91), 2.0, False,
     dict(interior=6, circ=6, oe=0, n_bend=2, wx=396.80, wy=195.0, baza=2,
          uwaga_min=1, col_otworow=4,
          wzorzec="SL40062903_p1_otwory_inny_kolor/wzorzec/2_oc_SL40062903_p1_2st_G_2050_.dxf")),
]


def test_t1_import():
    """Import z OBCEGO cwd nie tworzy plikow (zero efektow ubocznych)."""
    code = (
        "import os,sys; sys.path.insert(0, r'%s'); sys.path.insert(0, r'%s'); "
        "b=set(os.listdir(r'%s')); import wd_dwutorowy; "
        "a=set(os.listdir(r'%s')); print('NEW='+repr(sorted(a-b)))"
        % (SILNIKI, KONTROLA, SILNIKI, SILNIKI)
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(Path.home()), encoding="utf-8", errors="replace")
    new = "NEW=[]" in r.stdout
    check("T1 import bez efektow ubocznych", new,
          f"stdout={r.stdout.strip()} err={r.stderr[-200:]}")
    print(f"  T1 import z obcego cwd: {'0 nowych plikow' if new else 'EFEKT UBOCZNY!'}")


def test_reprodukcja():
    print("\n  odtworzenie kompletnosci (W-D dwutorowy):")
    for nm, rel, box, scale, is_pl, oc in CASES:
        msp = ezdxf.readfile(GOLDEN / rel).modelspace()
        doc, info = extract_wd(msp, box, scale, is_pl=is_pl)
        det = info["interior_detale"]
        check(f"{nm} interior", info["interior"] == oc["interior"],
              f"interior={info['interior']} != {oc['interior']}")
        check(f"{nm} okregi_dedup", det["circles_dedup"] == oc["circ"],
              f"circ={det['circles_dedup']} != {oc['circ']}")
        check(f"{nm} otwarte_konce", info["otwarte_konce"] == oc["oe"],
              f"oe={info['otwarte_konce']} != {oc['oe']}")
        check(f"{nm} n_bend", info["n_bend"] == oc["n_bend"],
              f"n_bend={info['n_bend']} != {oc['n_bend']}")
        check(f"{nm} kolor_bazowy", info["kolor_bazowy"] == oc["baza"],
              f"baza={info['kolor_bazowy']} != {oc['baza']}")
        check(f"{nm} wymiar_x", approx(info["wymiar_x"], oc["wx"]),
              f"wx={info['wymiar_x']} != {oc['wx']}")
        check(f"{nm} wymiar_y", approx(info["wymiar_y"], oc["wy"]),
              f"wy={info['wymiar_y']} != {oc['wy']}")
        # UWAGA-pass: dokladny (0) albo minimalny (>0 dla otworow obcego koloru)
        if "uwaga" in oc:
            check(f"{nm} uwaga_pass", info["uwaga_pass"] == oc["uwaga"],
                  f"uwaga_pass={info['uwaga_pass']} != {oc['uwaga']}")
        if "uwaga_min" in oc:
            check(f"{nm} uwaga_pass>0", info["uwaga_pass"] >= oc["uwaga_min"],
                  f"uwaga_pass={info['uwaga_pass']} < {oc['uwaga_min']}")
        # otwory INNEGO koloru realnie w wyniku (UWAGA-pass dolaczyl kol.4)
        if "col_otworow" in oc:
            n_col = sum(1 for e in doc.modelspace()
                        if e.dxf.color == oc["col_otworow"])
            check(f"{nm} otwory koloru {oc['col_otworow']} w wyniku", n_col > 0,
                  f"encji koloru {oc['col_otworow']} = {n_col}")
        # zgodnosc z wzorcem (interior + okregi po dedupie)
        if "wzorzec" in oc:
            wi, wc = _wzorzec_interior(oc["wzorzec"])
            check(f"{nm} interior == wzorzec", info["interior"] == wi,
                  f"wynik={info['interior']} vs wzorzec={wi}")
        # T6: outer==1, brak NIEDOMKNIETE, wysrodkowanie (0,0)
        check(f"{nm} outer==1", det["outer"] == 1, f"outer={det['outer']}")
        niedom = any(fl.startswith("NIEDOMKNIETE") for fl in det["flags"])
        check(f"{nm} kontur domkniety", not niedom, f"flags={det['flags']}")
        ext = _bb.extents(list(doc.modelspace()))
        cx = (ext.extmin.x + ext.extmax.x) / 2
        cy = (ext.extmin.y + ext.extmax.y) / 2
        check(f"{nm} wysrodkowany", abs(cx) <= 0.01 and abs(cy) <= 0.01,
              f"srodek=({cx:.3f},{cy:.3f})")
        print(f"  {nm:12} interior={info['interior']:2} okr={det['circles_dedup']} "
              f"oe={info['otwarte_konce']} baza={info['kolor_bazowy']} "
              f"uwaga={info['uwaga_pass']} giecia={info['n_bend']} "
              f"wym={info['wymiar_x']}x{info['wymiar_y']} srodek=({cx:.3f},{cy:.3f})")


def main():
    print("=== TESTY W-D dwutorowy (opt-in) ===\n")
    test_t1_import()
    test_reprodukcja()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== W-D: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== W-D: PASS (dwutorowy odtwarza kompletnosc + UWAGA-pass otwory obcego koloru) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
