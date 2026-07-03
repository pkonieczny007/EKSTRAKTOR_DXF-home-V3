# -*- coding: utf-8 -*-
"""
Zestaw ZNANYCH BLEDOW (XFAIL) - trudne przypadki ze zlecenia 54_4867 (SBM),
ktorych silnik JESZCZE nie robi dobrze. Cel: udokumentowac przypadek + poprawny
wynik i sledzic, kiedy silnik zostanie naprawiony (region+warstwa, skan okregow).

To NIE jest regresja PASS/FAIL - to lista celow. Semantyka jak pytest xfail:
  - blad OBECNY  (check nie przechodzi) + oczekiwany  -> XFAIL  (ok, nadal do zrobienia)
  - blad ZNIKNAL (check przechodzi)                   -> XPASS  (napraw! -> awansuj do regresja.py)
  - regresja: gdy case ma `naprawiony=True` a check pada -> FAIL (kod wyjscia 1)

Uzycie:  python testy\\regresja_znane_bledy.py
Rysunki: testy/rysunki/<zeinr>_1_conv.dxf + testy/rysunki/wykaz_54_4867.xlsx
Reguly:  kontekst/wiedza/cechy-odseparowane-region-warstwa.md,
         otwory-wspolsrodkowe-zdublowane.md, giecie-kiedy-nanosic-pl-skos.md
"""
import sys
import io
import csv
import math
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
SRC = HERE.parent / "produkcja" / "silniki" / "extract_positions.py"
RYSUNKI = HERE / "rysunki"
WYKAZ = RYSUNKI / "wykaz_54_4867.xlsx"


def _load(f):
    import ezdxf
    return ezdxf.readfile(f).modelspace()


def circles_by_center(msp):
    by = defaultdict(list)
    for e in msp:
        if e.dxftype() == "CIRCLE":
            c = e.dxf.center
            by[(round(c.x, 1), round(c.y, 1))].append(round(e.dxf.radius, 2))
    return by


def interior_contours(msp):
    """Zamkniete kontury wewnetrzne = cyklomatyka (E-V+C) + samozamkniete, minus kontur zewn."""
    edges = []
    isolated = 0
    def k(p): return (round(p[0], 1), round(p[1], 1))
    for e in msp:
        if e.dxf.layer == "GIECIE" or e.dxf.color == 6:
            continue
        t = e.dxftype()
        if t in ("CIRCLE", "ELLIPSE"):
            isolated += 1
        elif t in ("LWPOLYLINE", "POLYLINE"):
            closed = getattr(e, "closed", False) or (e.dxf.hasattr("flags") and e.dxf.flags & 1)
            try:
                pts = list(e.get_points("xy")) if t == "LWPOLYLINE" else [v.dxf.location for v in e.vertices]
            except Exception:
                pts = []
            if closed and len(pts) >= 3:
                isolated += 1
            else:
                for a, b in zip(pts, pts[1:]):
                    edges.append((k(a), k(b)))
        elif t == "SPLINE" and getattr(e, "closed", False):
            isolated += 1
        elif t == "LINE":
            edges.append((k(e.dxf.start), k(e.dxf.end)))
        elif t == "ARC":
            edges.append((k(e.start_point), k(e.end_point)))
    nodes = set()
    for a, b in edges:
        nodes.add(a); nodes.add(b)
    parent = {n: n for n in nodes}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    C = len({find(n) for n in nodes}) if nodes else 0
    cyclomatic = len(edges) - len(nodes) + C
    return max(cyclomatic + isolated - 1, 0)


# --- CHECKI: zwracaja (ok, opis) - ok=True gdy WYNIK POPRAWNY (blad naprawiony) ---
def chk_wachlarz(msp, row):
    """SL10600635 p1: rozwiniecie = wachlarz 481x170, status OK, >=9 otworow (nie tabelka/NIEPEWNE)."""
    try:
        w, h = float(row["out_w"]), float(row["out_h"])
    except Exception:
        return False, "brak wymiaru"
    dim_ok = abs(w - 481.0) <= 1.5 and abs(h - 170.0) <= 1.5
    st_ok = row["status"].startswith("OK")
    holes_ok = int(row["n_holes"]) >= 9
    ok = dim_ok and st_ok and holes_ok
    return ok, f"dim={w}x{h} status={row['status'][:16]} otw={row['n_holes']} (cel 481x170 OK >=9)"


def chk_sloty8(msp, row):
    """SL400521106 p1: 8 slotow = kontury wewn. >=8 (silnik gubi 4 odseparowane)."""
    ic = interior_contours(msp)
    return ic >= 8, f"kontury_wewn={ic} (cel >=8)"


def chk_fasola_i_okregi(msp, row):
    """SL10596945 p3: 2 fasole + 2 otwory = kontury_wewn>=4 ORAZ okregi bez podwojnych (2, nie 4)."""
    ic = interior_contours(msp)
    by = circles_by_center(msp)
    n_circ = sum(len(v) for v in by.values())
    concentric = any(len(v) > 1 for v in by.values())
    ok = ic >= 4 and n_circ == 2 and not concentric
    return ok, f"kontury_wewn={ic} okregi={n_circ} wspolsrodkowe={concentric} (cel >=4, 2 okregi, brak podw.)"


def chk_bez_duplikatow(msp, row):
    """SL10602681 p1: brak zdublowanych okregow (ten sam O, ten sam srodek)."""
    by = circles_by_center(msp)
    dup = sum(len(v) - 1 for v in by.values() if len(v) > 1)
    return dup == 0, f"zdublowane_okregi={dup} (cel 0)"


CASES = [
    # (zeinr, posn, opis, check, naprawiony?)
    ("SL10600635", 1, "wachlarz zamiast tabelki/NIEPEWNE (region+warstwa)", chk_wachlarz, False),
    ("SL400521106", 1, "4 z 8 slotow zgubione (cechy odseparowane)", chk_sloty8, False),
    ("SL10596945", 3, "zgubiona fasola + podwojne okregi O13/O14.7", chk_fasola_i_okregi, False),
    ("SL10602681", 1, "zdublowane okregi O6 (x4)", chk_bez_duplikatow, False),
]


def main():
    out = Path(tempfile.mkdtemp(prefix="znane_bledy_"))
    xfail = xpass = regres = 0
    print("=== ZNANE BLEDY (54_4867) - lista celow silnika ===\n")
    for zeinr, posn, opis, check, naprawiony in CASES:
        conv = RYSUNKI / f"{zeinr}_1_conv.dxf"
        subprocess.run([sys.executable, str(SRC), str(conv), str(WYKAZ), str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
        rows = {}
        rap = out / f"{zeinr}_raport.csv"
        if rap.exists():
            with open(rap, encoding="utf-8-sig") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    rows[int(r["posn"])] = r
        row = rows.get(posn, {})
        f = out / (row.get("file") or f"{zeinr}_p{posn}.dxf")
        try:
            ok, detail = check(_load(f), row) if f.exists() else (False, "brak pliku wyniku")
        except Exception as e:
            ok, detail = False, f"blad checku: {e}"
        tag = f"{zeinr} p{posn}"
        if ok and not naprawiony:
            xpass += 1
            print(f"  [XPASS] {tag}: NAPRAWIONE! -> awansuj do regresja.py  | {opis}\n          {detail}")
        elif ok and naprawiony:
            print(f"  [ OK  ] {tag}: {opis}\n          {detail}")
        elif not ok and naprawiony:
            regres += 1
            print(f"  [FAIL ] {tag}: REGRESJA - bylo naprawione!  | {opis}\n          {detail}")
        else:
            xfail += 1
            print(f"  [XFAIL] {tag}: nadal do zrobienia            | {opis}\n          {detail}")
    shutil.rmtree(out, ignore_errors=True)
    print(f"\nXFAIL(do zrobienia)={xfail}  XPASS(naprawione)={xpass}  REGRESJE={regres}")
    if xpass:
        print("-> Sa naprawione przypadki: przenies je do regresja.py (naprawiony=True lub twardy assert).")
    sys.exit(1 if regres else 0)


if __name__ == "__main__":
    main()
