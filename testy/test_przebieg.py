# -*- coding: utf-8 -*-
"""Testy PRZEBIEGU ZLECENIA (P0.1): produkcja/przebieg.py.

Runner krokow wstrzykiwany STUBEM (rejestruje nazwa+cmd, zwraca sterowany kod) -
testujemy ORKIESTRACJE (kolejnosc, propagacja --parytet, GLOSNOSC przy padnietym
kroku, pomijanie --bez-*), NIE realne silniki (zasada: bez odpalania silnikow).

A) kolejnosc krokow a-f na komplecie danych (staging sweepa dziala).
B) propagacja --parytet do orkiestratora.
C) krok padl (raport rc=1) -> FAIL w rekordach + KONTYNUACJA pozostalych + exit=1.
D) --bez-galerii -> przeglad POMIN (nie wywolany), reszta leci.
E) --bez-metryki -> metryka POMIN (nie wywolany).
F) sweep-staging niemozliwy (brak raportu z bbox) -> sweep FAIL (GLOSNO) + exit=1.

Uzycie:  python testy\\test_przebieg.py     (exit 0 = PASS)
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
sys.path.insert(0, str(HERE.parent / "produkcja"))
import przebieg as pb  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _rect_dxf(path, w=100.0, h=50.0):
    doc = ezdxf.new()
    doc.modelspace().add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)
    doc.saveas(path)


def _stub_runner(rc_map=None):
    """Zwraca (run_fn, CALLS). run_fn rejestruje (nazwa, cmd) i zwraca rc_map[nazwa]|0."""
    rc_map = rc_map or {}
    calls = []

    def run(nazwa, cmd):
        calls.append((nazwa, [str(c) for c in cmd]))
        return rc_map.get(nazwa, 0)
    return run, calls


def _setup(tmp, zeinr, z_bbox=True):
    """Buduje FLAT folder wynikow jednego rysunku: conv + wykaz + ocena + (wA raport)
    + zwycieskie DXF. Zwraca sciezke conv."""
    # ocena wielowariantowa (plik_produkcyjny -> zwyciescy)
    with open(tmp / f"{zeinr}_ocena.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "zeinr", "posn", "zwyciezca", "semafor", "pewnosc", "zrodlo_prawda",
            "warianty", "interior", "plik_produkcyjny", "powod"])
        w.writeheader()
        for posn, sem in [(1, "zielony"), (2, "zolty"), (3, "czerwony")]:
            plik = f"{zeinr}_p{posn}.dxf" if posn != 3 else "-"
            w.writerow(dict(zeinr=zeinr, posn=posn, zwyciezca="W-C", semafor=sem,
                            pewnosc="-", zrodlo_prawda=4, warianty="", interior="",
                            plik_produkcyjny=plik, powod="test"))
    # raport silnika bazowego z BBOXEM (staging sweepa)
    if z_bbox:
        wA = tmp / "warianty" / "wA"
        wA.mkdir(parents=True, exist_ok=True)
        with open(wA / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=[
                "posn", "scale", "src_x1", "src_y1", "src_x2", "src_y2",
                "wykaz_w", "wykaz_h", "status", "file"])
            w.writeheader()
            for posn in (1, 2, 3):
                w.writerow(dict(posn=posn, scale=5.0, src_x1=10.0, src_y1=10.0,
                                src_x2=60.0, src_y2=40.0, wykaz_w=250.0, wykaz_h=150.0,
                                status="OK", file=f"{zeinr}_p{posn}.dxf"))
    for posn in (1, 2):
        _rect_dxf(tmp / f"{zeinr}_p{posn}.dxf")
    conv = tmp / f"{zeinr}_1_conv.dxf"
    _rect_dxf(conv)
    (tmp / f"{zeinr}_wykaz.xlsx").write_text("dummy")   # istnienie wystarcza (raport stub)
    return conv


ORDER = [pb.K_ORK, pb.K_RAP, pb.K_SPR, pb.K_SWEEP, pb.K_PRZ, pb.K_MET]


def test_kolejnosc():
    print("--- A) kolejnosc krokow a-f (staging sweepa OK) ---")
    zeinr = "SLPB0001"
    tmp = Path(tempfile.mkdtemp(prefix="pb_ord_"))
    try:
        conv = _setup(tmp, zeinr)
        run_fn, calls = _stub_runner()
        rekordy, kod = pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp, run_fn=run_fn)
        kolejnosc = [n for n, _ in calls]
        check("A0 exit 0", kod == 0, f"kod={kod}")
        check("A1 6 krokow wywolanych", len(calls) == 6, kolejnosc)
        check("A2 kolejnosc a-f", kolejnosc == ORDER, kolejnosc)
        check("A3 wszystkie OK", all(r["status"] == "OK" for r in rekordy),
              [(r["krok"], r["status"]) for r in rekordy])
        # sweep faktycznie stagowany i wywolany (nie FAIL)
        sweep_rec = [r for r in rekordy if r["krok"] == pb.K_SWEEP]
        check("A4 sweep OK (staging)", sweep_rec and sweep_rec[0]["status"] == "OK",
              sweep_rec)
        # sweep cmd wskazuje na sweep.py + staging pod out_dir
        sweep_cmd = next(c for n, c in calls if n == pb.K_SWEEP)
        check("A5 sweep cmd -> sweep.py", any("sweep.py" in x for x in sweep_cmd), sweep_cmd)
        check("A6 sweep cmd -> staging _sweep_", any("_sweep_" in x for x in sweep_cmd),
              sweep_cmd)
        print(f"  kolejnosc: {kolejnosc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_parytet():
    print("\n--- B) propagacja --parytet do orkiestratora ---")
    zeinr = "SLPB0002"
    tmp = Path(tempfile.mkdtemp(prefix="pb_par_"))
    try:
        conv = _setup(tmp, zeinr)
        run_fn, calls = _stub_runner()
        pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp, parytet=True, run_fn=run_fn)
        ork_cmd = next(c for n, c in calls if n == pb.K_ORK)
        check("B1 orkiestrator ma --parytet", "--parytet" in ork_cmd, ork_cmd)
        # bez parytetu -> brak flagi
        run_fn2, calls2 = _stub_runner()
        pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp, parytet=False, run_fn=run_fn2)
        ork_cmd2 = next(c for n, c in calls2 if n == pb.K_ORK)
        check("B2 default bez --parytet", "--parytet" not in ork_cmd2, ork_cmd2)
        print(f"  --parytet w cmd: {'--parytet' in ork_cmd}; default: {'--parytet' in ork_cmd2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_padniety_krok():
    print("\n--- C) krok padl (raport rc=1) -> FAIL + KONTYNUACJA + exit=1 ---")
    zeinr = "SLPB0003"
    tmp = Path(tempfile.mkdtemp(prefix="pb_fail_"))
    try:
        conv = _setup(tmp, zeinr)
        run_fn, calls = _stub_runner(rc_map={pb.K_RAP: 1})
        rekordy, kod = pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp, run_fn=run_fn)
        check("C1 exit != 0", kod == 1, f"kod={kod}")
        rap = [r for r in rekordy if r["krok"] == pb.K_RAP]
        check("C2 raport FAIL", rap and rap[0]["status"] == "FAIL", rap)
        # KONTYNUACJA: kroki PO raporcie wciaz wywolane (sprawdz_folder, sweep, przeglad, metryka)
        kolejnosc = [n for n, _ in calls]
        for krok in (pb.K_SPR, pb.K_SWEEP, pb.K_PRZ, pb.K_MET):
            check(f"C3 kontynuacja {krok}", krok in kolejnosc, kolejnosc)
        check("C4 tylko raport FAIL", sum(1 for r in rekordy if r["status"] == "FAIL") == 1,
              [(r["krok"], r["status"]) for r in rekordy])
        print(f"  FAIL: {[r['krok'] for r in rekordy if r['status']=='FAIL']}; "
              f"kontynuowano: {kolejnosc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_bez_galerii():
    print("\n--- D) --bez-galerii -> przeglad POMIN (nie wywolany) ---")
    zeinr = "SLPB0004"
    tmp = Path(tempfile.mkdtemp(prefix="pb_bg_"))
    try:
        conv = _setup(tmp, zeinr)
        run_fn, calls = _stub_runner()
        rekordy, kod = pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp,
                                   bez_galerii=True, run_fn=run_fn)
        kolejnosc = [n for n, _ in calls]
        check("D0 exit 0 (pomin nie jest bledem)", kod == 0, f"kod={kod}")
        check("D1 przeglad NIE wywolany", pb.K_PRZ not in kolejnosc, kolejnosc)
        prz = [r for r in rekordy if r["krok"] == pb.K_PRZ]
        check("D2 przeglad POMIN", prz and prz[0]["status"] == "POMIN", prz)
        check("D3 metryka wciaz wywolana", pb.K_MET in kolejnosc, kolejnosc)
        print(f"  kolejnosc: {kolejnosc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_bez_metryki():
    print("\n--- E) --bez-metryki -> metryka POMIN (nie wywolana) ---")
    zeinr = "SLPB0005"
    tmp = Path(tempfile.mkdtemp(prefix="pb_bm_"))
    try:
        conv = _setup(tmp, zeinr)
        run_fn, calls = _stub_runner()
        rekordy, kod = pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp,
                                   bez_metryki=True, run_fn=run_fn)
        kolejnosc = [n for n, _ in calls]
        check("E0 exit 0", kod == 0, f"kod={kod}")
        check("E1 metryka NIE wywolana", pb.K_MET not in kolejnosc, kolejnosc)
        met = [r for r in rekordy if r["krok"] == pb.K_MET]
        check("E2 metryka POMIN", met and met[0]["status"] == "POMIN", met)
        print(f"  kolejnosc: {kolejnosc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_sweep_staging_fail():
    print("\n--- F) sweep-staging niemozliwy (brak raportu z bbox) -> FAIL + exit=1 ---")
    zeinr = "SLPB0006"
    tmp = Path(tempfile.mkdtemp(prefix="pb_sw_"))
    try:
        conv = _setup(tmp, zeinr, z_bbox=False)   # brak wA raportu = brak bboxow
        run_fn, calls = _stub_runner()
        rekordy, kod = pb.przebieg(conv, tmp / f"{zeinr}_wykaz.xlsx", tmp, run_fn=run_fn)
        kolejnosc = [n for n, _ in calls]
        check("F1 exit != 0 (sweep obowiazkowy)", kod == 1, f"kod={kod}")
        sweep = [r for r in rekordy if r["krok"] == pb.K_SWEEP]
        check("F2 sweep FAIL", sweep and sweep[0]["status"] == "FAIL", sweep)
        check("F3 sweep NIE wywolany przez runner", pb.K_SWEEP not in kolejnosc, kolejnosc)
        # kroki po sweepie i tak leca (przeglad, metryka)
        check("F4 przeglad mimo to wywolany", pb.K_PRZ in kolejnosc, kolejnosc)
        print(f"  sweep status: {sweep and sweep[0]['status']}; powod: "
              f"{sweep and sweep[0]['powod']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_folder_wielorysunkowy():
    print("\n--- G) folder z *_conv.dxf -> per-rysunek podfoldery ---")
    tmp = Path(tempfile.mkdtemp(prefix="pb_folder_"))
    try:
        src = tmp / "rysunki"
        src.mkdir()
        # dwa rysunki jako conv w folderze zrodlowym (bez ocena/raport - orkiestrator stub
        # ich nie tworzy, wiec staging sweepa padnie GLOSNO, ale petla MA objac oba)
        for zeinr in ("SLPBA001", "SLPBB002"):
            _rect_dxf(src / f"{zeinr}_1_conv.dxf")
        (tmp / "wykaz.xlsx").write_text("dummy")
        out = tmp / "wyniki"
        run_fn, calls = _stub_runner()
        rekordy, kod = pb.przebieg(src, tmp / "wykaz.xlsx", out,
                                   bez_galerii=True, bez_metryki=True, run_fn=run_fn)
        rysunki = sorted(set(r["rysunek"] for r in rekordy))
        check("G1 oba rysunki objete", rysunki == ["SLPBA001", "SLPBB002"], rysunki)
        # kazdy rysunek dostal wlasny podfolder wynikow
        check("G2 podfolder rysunku A", (out / "SLPBA001").is_dir())
        check("G3 podfolder rysunku B", (out / "SLPBB002").is_dir())
        # orkiestrator wywolany dla obu (2x)
        n_ork = sum(1 for n, _ in calls if n == pb.K_ORK)
        check("G4 orkiestrator 2x", n_ork == 2, n_ork)
        print(f"  rysunki: {rysunki}; orkiestrator wywolan: {n_ork}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== TESTY PRZEBIEGU ZLECENIA (P0.1) ===\n")
    test_kolejnosc()
    test_parytet()
    test_padniety_krok()
    test_bez_galerii()
    test_bez_metryki()
    test_sweep_staging_fail()
    test_folder_wielorysunkowy()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== PRZEBIEG: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== PRZEBIEG: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
