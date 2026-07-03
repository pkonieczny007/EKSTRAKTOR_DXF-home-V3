# -*- coding: utf-8 -*-
"""
Test regresyjny ekstraktora - uruchamiac PO KAZDEJ zmianie w src/.

Przepuszcza 3 rysunki testowe i sprawdza:
  1. wymiary kazdej pozycji vs oczekiwane (z wykazu),
  2. statusy (OK / LUSTRO / BRAK W WYKAZIE),
  3. liczbe otworow (NIE WOLNO zgubic otworow!),
  4. pozycje 1 SL10478356 encja-po-encji vs referencja operatora.

Uzycie:  python testy\\regresja.py
Wynik:   PASS/FAIL per przypadek + podsumowanie. Kod wyjscia 0 = wszystko OK.
"""
import sys
import io
import csv
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
SRC = HERE.parent / "produkcja" / "silniki" / "extract_positions.py"
RYSUNKI = HERE / "rysunki"
WZORCE = HERE / "wzorce"
# Wykazy per zlecenie (jeden rysunek = jeden wykaz; klucz uzywany w OCZEKIWANE)
WYKAZY = {
    "35": RYSUNKI / "35.45671546_lista materiałowa + domówienie + rev akt.28.05.2026.xlsx",
    "43": RYSUNKI / "43.45672404_lista materiałowa akt.26.05.2026.xlsx",
    "46": RYSUNKI / "46.45672998_lista materiałowa + Rev + domówienie akt.10.06.2026.xlsx",
}

# Oczekiwane wyniki: zeinr -> (wykaz_key, [(posn, out_w, out_h, n_otworow_min, status_prefix), ...])
# status_prefix - poczatek statusu (reszta to flagi informacyjne)
OCZEKIWANE = {
    # --- zlecenie 35 (3 konwencje: warstwy / lamana / SBM-kolory) ---
    "SL10478356": ("35", [
        (1, 2232.0, 484.0, 1, "OK"),
        (2, 616.29, 484.0, 0, "OK"),
        (3, 1675.03, 386.54, 0, "OK"),
        (4, 3040.0, 100.0, 0, "OK"),
        (5, 2112.79, 150.0, 0, "OK"),
        (6, 1245.0, 100.0, 0, "OK"),
        (7, 1461.02, 150.0, 0, "OK"),
        (8, 355.61, 150.0, 0, "OK"),
        (9, 658.0, 150.0, 0, "OK"),
        (10, 184.0, 150.0, 0, "OK"),
        (11, 150.0, 95.99, 0, "OK"),
        (12, 292.0, 73.0, 0, "OK"),
        (13, 209.0, 150.0, 4, "OK"),
        (14, 484.0, 300.0, 2, "OK"),
        (22, None, None, 0, "BRAK W WYKAZIE"),
    ]),
    "SL10524825": ("35", [
        (1, 180.0, 180.0, 4, "OK"),
        (2, 374.68, 175.63, 1, "OK"),
        (3, None, None, 0, "LUSTRO z poz. 2"),
        (4, 238.85, 150.0, 0, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL10582053": ("35", [
        (1, 200.0, 72.05, 4, "OK (TRYB BEZ WARSTW)"),
    ]),

    # --- zlecenie 43_2404 ---
    "SL40081914": ("43", [
        (1, 6000.0, 225.13, 10, "OK (TRYB BEZ WARSTW)"),
        (2, None, None, 0, "BRAK W WYKAZIE"),
        (3, None, None, 0, "BRAK W WYKAZIE"),
        (4, 1200.0, 110.13, 3, "OK (TRYB BEZ WARSTW)"),
        (5, 490.45, 60.0, 3, "OK (TRYB BEZ WARSTW)"),
    ]),

    # --- zlecenie 46_2998 (podzespoly 0123 + 0300, SBM) ---
    # Pary lustrzane SBM: poz "as drawn" + poz "spiegelbildlich" (legenda przy numerze).
    # Gdy poz.1 znajduje wlasny widok -> reka przypisana poprawnie (poz.2 = LUSTRO).
    "SL10578701": ("46", [
        (1, 2500.0, 313.75, 14, "OK (TRYB BEZ WARSTW)"),
        (2, None, None, 0, "LUSTRO z poz. 1"),
    ]),
    "SL10578699": ("46", [
        (1, None, None, 0, "BRAK W WYKAZIE"),
        (2, 100.0, 50.0, 2, "OK"),
        (3, 40.0, 40.0, 2, "OK"),
    ]),
    "SL40052144": ("46", [
        (1, 1750.0, 313.45, 7, "OK (TRYB BEZ WARSTW)"),
    ]),
    # sito: wyciecia KWADRATOWE (LINE, nie CIRCLE) -> n_holes=0, ale geometria w pliku
    "SL40852311": ("46", [
        (1, 1750.0, 304.38, 0, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL400521100": ("46", [
        (1, 2250.0, 313.75, 9, "OK (TRYB BEZ WARSTW)"),
        (2, None, None, 0, "LUSTRO z poz. 1"),
    ]),
    "SL40052423": ("46", [
        (1, 2240.0, 64.82, 0, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL40071940": ("46", [
        (1, 3490.0, 454.1, 81, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL10578806": ("46", [
        (4, 305.0, 305.0, 0, "OK (TRYB BEZ WARSTW)"),
        (51, None, None, 0, "BRAK W WYKAZIE"),
        (55, None, None, 0, "BRAK W WYKAZIE"),
    ]),
    "SL40885240": ("46", [
        (1, 1500.0, 1007.35, 7, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL10584235": ("46", [
        (1, 2119.16, 1278.86, 7, "OK (TRYB BEZ WARSTW)"),
    ]),
    "SL10584244": ("46", [
        (1, 1082.99, 198.0, 7, "OK (TRYB BEZ WARSTW)"),
    ]),
}


def sigset(path):
    """Sygnatura geometryczna niezalezna od przesuniecia (znormalizowana do bbox-min)."""
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    ext = bbox.extents(msp)
    ox, oy = ext.extmin.x, ext.extmin.y
    s = []
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            p = sorted([(round(e.dxf.start.x - ox, 1), round(e.dxf.start.y - oy, 1)),
                        (round(e.dxf.end.x - ox, 1), round(e.dxf.end.y - oy, 1))])
            s.append(("LINE", tuple(p[0]), tuple(p[1])))
        elif t in ("ARC", "CIRCLE"):
            s.append((t, round(e.dxf.center.x - ox, 1), round(e.dxf.center.y - oy, 1),
                      round(e.dxf.radius, 1)))
        else:
            s.append((t,))
    return Counter(s)


def main():
    out = Path(tempfile.mkdtemp(prefix="regresja_"))
    fails = []
    checks = 0

    for zeinr, (wykaz_key, expected) in OCZEKIWANE.items():
        conv = RYSUNKI / f"{zeinr}_1_conv.dxf"
        wykaz = WYKAZY[wykaz_key]
        r = subprocess.run([sys.executable, str(SRC), str(conv), str(wykaz), str(out)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            fails.append(f"{zeinr}: skrypt pad? kod {r.returncode}\n{r.stderr[-500:]}")
            continue
        raport = out / f"{zeinr}_raport.csv"
        rows = {}
        with open(raport, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                rows[int(row["posn"])] = row

        for posn, w, h, holes_min, status_prefix in expected:
            checks += 1
            row = rows.get(posn)
            tag = f"{zeinr} poz.{posn}"
            if row is None:
                fails.append(f"{tag}: brak w raporcie")
                continue
            if not row["status"].startswith(status_prefix):
                fails.append(f"{tag}: status '{row['status'][:60]}' != '{status_prefix}*'")
            if w is not None:
                got_w, got_h = float(row["out_w"]), float(row["out_h"])
                if abs(got_w - w) > 0.5 or abs(got_h - h) > 0.5:
                    fails.append(f"{tag}: wymiar {got_w}x{got_h} != {w}x{h}")
                if int(row["n_holes"]) < holes_min:
                    fails.append(f"{tag}: otwory {row['n_holes']} < {holes_min} - ZGUBIONE OTWORY!")

    # zloty test: p1 identyczna z referencja operatora
    checks += 1
    ref = sigset(WZORCE / "SL10478356_p1_REFERENCJA_OPERATORA.dxf")
    mine = sigset(out / "SL10478356_p1.dxf")
    diff = list((ref - mine).elements()) + list((mine - ref).elements())
    if diff:
        fails.append(f"SL10478356 p1: {len(diff)} roznic geometrycznych vs referencja operatora!")

    shutil.rmtree(out, ignore_errors=True)
    print(f"\nSprawdzen: {checks} | Bledow: {len(fails)}")
    for f in fails:
        print("  FAIL:", f)
    print("\n=== REGRESJA: " + ("PASS ===" if not fails else "FAIL ==="))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
