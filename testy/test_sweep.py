# -*- coding: utf-8 -*-
"""Testy SWEEP KOMPLETNOSCI (produkcja/kontrola/sweep.py).

Dwie warstwy:
  A) RDZEN kontury_regionu_zrodla na golden z bboxami z realnych raportow silnika
     (stabilne): SL40061302 sloty widzi TYLKO col2 (col7=0!), filtr n_outer==1
     odrzuca skazona warstwe adnotacji; SL10582608 owal=12; SL10596945 fasola=4.
  B) PLUMBING sweep_zlecenie na fixture z golden: zrodlo=wejscie, dostarczone=
     wzorzec (delta=0 -> zielony, ZERO falszywej flagi) oraz wzorzec-bez-otworow
     (delta>=1 -> zolty). Brzegowe: bbox pusty/zdegenerowany.

Uzycie:  python testy\\test_sweep.py     (exit 0 = PASS)
"""
import csv
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
sys.path.insert(0, str(HERE.parent / "produkcja" / "kontrola"))
from sweep import kontury_regionu_zrodla, sweep_zlecenie  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# (nazwa, zrodlo wejscie, bbox z realnego raportu, posn, oczekiwania)
RDZEN = [
    ("SL40061302", "SL40061302_sloty_odseparowane/wejscie/SL40061302_1_conv.dxf",
     (50.83, 136.99, 194.3, 241.99),
     dict(prawda=3, tryb="col2", col7=0, col2=3)),
    ("SL10582608", "SL10582608_owal_odseparowany_klaster/wejscie/SL10582608_1.dxf",
     (113.14, 78.46, 202.94, 151.51),
     dict(prawda=12, col7=12)),
    ("SL10596945", "SL10596945_fasola_odseparowana/wejscie/SL10596945_1_conv.dxf",
     (434.17, 153.97, 490.68, 206.05),
     dict(prawda=4, col7=4)),
]


def test_rdzen():
    print("--- A) RDZEN kontury_regionu_zrodla (bboxy z realnych raportow) ---")
    for zeinr, rel, box, oc in RDZEN:
        msp = ezdxf.readfile(GOLDEN / rel).modelspace()
        res = kontury_regionu_zrodla(msp, box)
        check(f"{zeinr} prawda", res["zrodlo_prawda"] == oc["prawda"],
              f"prawda={res['zrodlo_prawda']} != {oc['prawda']}")
        if "tryb" in oc:
            check(f"{zeinr} tryb", res["tryb_znaleziony"] == oc["tryb"],
                  f"tryb={res['tryb_znaleziony']} != {oc['tryb']}")
        for k in ("col7", "col2"):
            if k in oc:
                check(f"{zeinr} {k}", res["per_tryb"][k] == oc[k],
                      f"{k}={res['per_tryb'][k]} != {oc[k]}")
        # 'all' NIGDY nie jest prawda i zawsze >= prawda (zawyza)
        check(f"{zeinr} all>=prawda", res["per_tryb"]["all"] >= res["zrodlo_prawda"],
              f"all={res['per_tryb']['all']} < prawda={res['zrodlo_prawda']}")
        print(f"  {zeinr:12} col7={res['per_tryb']['col7']:>3} col2={res['per_tryb']['col2']:>3} "
              f"all={res['per_tryb']['all']:>3} prawda={res['zrodlo_prawda']} "
              f"tryb={res['tryb_znaleziony']}")


def test_brzegowe():
    print("\n--- brzegowe ---")
    msp = ezdxf.readfile(GOLDEN / RDZEN[2][1]).modelspace()
    # pustka -> tryb None + GLOSNA uwaga, nie zgadywanie
    res = kontury_regionu_zrodla(msp, (-5000, -5000, -4900, -4900))
    check("pustka tryb None", res["tryb_znaleziony"] is None, f"tryb={res['tryb_znaleziony']}")
    check("pustka uwaga glosna", any("BRAK GEOMETRII" in u for u in res["diag"]["uwagi"]),
          f"uwagi={res['diag']['uwagi']}")
    # zdegenerowany bbox -> ValueError (nie cichy 0)
    try:
        kontury_regionu_zrodla(msp, (10, 10, 10, 20))
        check("bbox zdegenerowany", False, "brak ValueError")
    except ValueError:
        check("bbox zdegenerowany", True)
    print("  pustka -> None + uwaga GLOSNA; bbox zdegenerowany -> ValueError")


def _fixture(tmp, zeinr, src_rel, box, delivered_doc):
    """Buduje folder_wynikow/<zeinr>/ (raport + dostarczone) + folder_rysunkow."""
    wyn = tmp / "wynikow" / zeinr
    rys = tmp / "rysunkow"
    wyn.mkdir(parents=True, exist_ok=True)
    rys.mkdir(parents=True, exist_ok=True)
    shutil.copy(GOLDEN / src_rel, rys / f"{zeinr}_1_conv.dxf")
    delivered_doc.saveas(wyn / f"{zeinr}_p1.dxf")
    with open(wyn / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["posn", "src_x1", "src_y1", "src_x2", "src_y2", "file"])
        w.writerow([1, box[0], box[1], box[2], box[3], f"{zeinr}_p1.dxf"])
    return tmp / "wynikow", rys


def test_plumbing():
    print("\n--- B) PLUMBING sweep_zlecenie (fixture z golden) ---")
    zeinr, src_rel, box, _ = RDZEN[2]          # SL10596945, prawda=4
    wzor = GOLDEN / "SL10596945_fasola_odseparowana/wzorzec/SL10596945_p3.dxf"

    # (1) dostarczone = wzorzec (4 kontury) -> delta=0 -> ZIELONY (zero falszywej flagi)
    tmp1 = Path(tempfile.mkdtemp(prefix="sweep_ok_"))
    try:
        w, r = _fixture(tmp1, zeinr, src_rel, box, ezdxf.readfile(wzor))
        wiersze, braki = sweep_zlecenie(w, r)
        row = wiersze[0]
        check("plumbing zielony (brak falszywej flagi)", row["semafor"] == "zielony",
              f"semafor={row['semafor']} delta={row['delta']} powod={row['powod']}")
        check("plumbing delta0", row["delta"] == 0, f"delta={row['delta']}")
        print(f"  wzorzec pelny:  zrodlo={row['zrodlo']} wynik={row['wynik']} "
              f"delta={row['delta']} -> {row['semafor']}")
    finally:
        shutil.rmtree(tmp1, ignore_errors=True)

    # (2) dostarczone = wzorzec BEZ okregow (silnik "zgubil" 2 otwory) -> delta>=1 -> ZOLTY
    tmp2 = Path(tempfile.mkdtemp(prefix="sweep_flag_"))
    try:
        doc = ezdxf.readfile(wzor)
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxftype() == "CIRCLE":
                msp.delete_entity(e)
        w, r = _fixture(tmp2, zeinr, src_rel, box, doc)
        wiersze, braki = sweep_zlecenie(w, r)
        row = wiersze[0]
        check("plumbing zolty (wykryty brak)", row["semafor"] == "zolty",
              f"semafor={row['semafor']} delta={row['delta']}")
        check("plumbing delta>=1", (row["delta"] or 0) >= 1, f"delta={row['delta']}")
        print(f"  wzorzec-2 otwory: zrodlo={row['zrodlo']} wynik={row['wynik']} "
              f"delta={row['delta']} -> {row['semafor']} ({row['powod'][:50]})")
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

    # (3) brak zrodla -> log GLOSNO + wpis do braki (nie cichy pass)
    tmp3 = Path(tempfile.mkdtemp(prefix="sweep_brak_"))
    try:
        wyn = tmp3 / "wynikow" / zeinr
        wyn.mkdir(parents=True)
        with open(wyn / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
            w2 = csv.writer(f, delimiter=";")
            w2.writerow(["posn", "src_x1", "src_y1", "src_x2", "src_y2", "file"])
            w2.writerow([1, box[0], box[1], box[2], box[3], f"{zeinr}_p1.dxf"])
        (tmp3 / "rysunkow").mkdir()
        wiersze, braki = sweep_zlecenie(tmp3 / "wynikow", tmp3 / "rysunkow")
        check("brak zrodla zglaszany", zeinr in braki, f"braki={braki}")
        print(f"  brak zrodla -> braki={braki} (GLOSNO)")
    finally:
        shutil.rmtree(tmp3, ignore_errors=True)


def main():
    print("=== TESTY SWEEP KOMPLETNOSCI ===\n")
    test_rdzen()
    test_brzegowe()
    test_plumbing()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== SWEEP: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== SWEEP: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
