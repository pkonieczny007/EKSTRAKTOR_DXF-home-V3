# -*- coding: utf-8 -*-
"""
Benchmark V2 vs V1 - warunek przelaczenia skilla na V2.

Oba silniki dostaja te same rysunki testowe (3 zlecenia, w tym realne
46_2998) i te same OCZEKIWANE z testy/regresja.py. Zasada z architektury:
V2 "wygrywa" dopiero, gdy jest >= V1 na WSZYSTKIM:
  1. kazde sprawdzenie (status/wymiar/otwory), ktore przechodzi V1,
     musi przejsc w V2,
  2. pliki DXF pozycji porownywane sygnatura geometryczna (idealnie:
     identyczne encja-po-encji - wtedy zero ryzyka regresu jakosci).

Uzycie:  python testy\\benchmark_v2.py
Wynik:   tabela per rysunek + raport testy/benchmark_v2_raport.md;
         kod wyjscia 0 = V2 >= V1 na wszystkim.
"""
import sys
import io
import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
# UWAGA: import regresji sam podmienia sys.stdout na wrapper UTF-8 -
# nie wolno wrapowac drugi raz (GC starego wrappera zamyka wspolny bufor)
from regresja import OCZEKIWANE, WYKAZY, RYSUNKI, sigset   # noqa: E402

SRC_V1 = HERE.parent / "produkcja" / "silniki" / "extract_positions.py"
SRC_V2 = HERE.parent / "produkcja" / "silniki" / "v2" / "orkiestrator.py"
RAPORT_MD = HERE / "benchmark_v2_raport.md"


def uruchom(silnik, conv, wykaz, out):
    r = subprocess.run([sys.executable, str(silnik), str(conv), str(wykaz), str(out)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode == 0, r.stderr[-800:]


def ocen(raport_csv, expected):
    """Te same sprawdzenia co regresja: status prefix, wymiar, otwory.
    Zwraca (zaliczone, wszystkie, lista_bledow)."""
    rows = {}
    if raport_csv.exists():
        with open(raport_csv, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                rows[int(row["posn"])] = row
    ok, blad = 0, []
    for posn, w, h, holes_min, status_prefix in expected:
        row = rows.get(posn)
        if row is None:
            blad.append(f"poz.{posn}: brak w raporcie")
            continue
        czesciowe = []
        if not row["status"].startswith(status_prefix):
            czesciowe.append(f"status '{row['status'][:50]}' != '{status_prefix}*'")
        if w is not None:
            got_w, got_h = float(row["out_w"]), float(row["out_h"])
            if abs(got_w - w) > 0.5 or abs(got_h - h) > 0.5:
                czesciowe.append(f"wymiar {got_w}x{got_h} != {w}x{h}")
            if int(row["n_holes"]) < holes_min:
                czesciowe.append(f"otwory {row['n_holes']} < {holes_min}")
        if czesciowe:
            blad.append(f"poz.{posn}: " + "; ".join(czesciowe))
        else:
            ok += 1
    return ok, len(expected), blad


def porownaj_pliki(out1, out2, expected, zeinr):
    """Sygnatura geometryczna plikow V1 vs V2 dla pozycji z plikiem."""
    ident, rozne, brak = 0, [], []
    for posn, w, h, _hm, _sp in expected:
        kandydaci = list(out1.glob(f"{zeinr}_p{posn}.dxf")) + \
                    list(out1.glob(f"{zeinr}_p{posn}_*.dxf"))
        for f1 in kandydaci:
            f2 = out2 / f1.name
            if not f2.exists():
                brak.append(f1.name)
                continue
            a, b = sigset(f1), sigset(f2)
            diff = list((a - b).elements()) + list((b - a).elements())
            if diff:
                rozne.append(f"{f1.name} ({len(diff)} roznic)")
            else:
                ident += 1
    return ident, rozne, brak


def main():
    tmp = Path(tempfile.mkdtemp(prefix="benchmark_"))
    wiersze_md = []
    suma = {"v1": 0, "v2": 0, "sprawdzen": 0, "ident": 0, "rozne": [], "brak": []}
    v2_gorszy = []   # sprawdzenia, ktore V1 zalicza a V2 nie

    print(f"{'rysunek':<14} {'V1':>7} {'V2':>7}  pliki V2 vs V1")
    for zeinr, (wykaz_key, expected) in OCZEKIWANE.items():
        conv = RYSUNKI / f"{zeinr}_1_conv.dxf"
        wykaz = WYKAZY[wykaz_key]
        out1, out2 = tmp / f"v1_{zeinr}", tmp / f"v2_{zeinr}"

        ok1, err1 = uruchom(SRC_V1, conv, wykaz, out1)
        ok2, err2 = uruchom(SRC_V2, conv, wykaz, out2)
        if not ok1 or not ok2:
            print(f"{zeinr:<14} {'PAD' if not ok1 else 'ok':>7} "
                  f"{'PAD' if not ok2 else 'ok':>7}")
            v2_gorszy.append(f"{zeinr}: silnik pad ({(err1 or err2)[:200]})")
            continue

        z1, n, b1 = ocen(out1 / f"{zeinr}_raport.csv", expected)
        z2, _, b2 = ocen(out2 / f"{zeinr}_raport.csv", expected)
        ident, rozne, brak = porownaj_pliki(out1, out2, expected, zeinr)

        suma["v1"] += z1
        suma["v2"] += z2
        suma["sprawdzen"] += n
        suma["ident"] += ident
        suma["rozne"] += rozne
        suma["brak"] += brak
        # V2 musi zaliczac WSZYSTKO co zalicza V1
        b2_tylko = [x for x in b2 if x not in b1]
        if b2_tylko:
            v2_gorszy += [f"{zeinr} {x}" for x in b2_tylko]

        opis_plikow = f"{ident} identycznych"
        if rozne:
            opis_plikow += f", ROZNE: {', '.join(rozne)}"
        if brak:
            opis_plikow += f", brak w V2: {', '.join(brak)}"
        print(f"{zeinr:<14} {z1:>4}/{n:<2} {z2:>4}/{n:<2}  {opis_plikow}")
        wiersze_md.append(
            f"| {zeinr} | {z1}/{n} | {z2}/{n} | {opis_plikow} |")
        if b2:
            for x in b2:
                wiersze_md.append(f"|  | | V2: {x} | |")

    wygrana = not v2_gorszy and not suma["rozne"] and not suma["brak"]
    print(f"\nSprawdzenia OCZEKIWANE: V1 {suma['v1']}/{suma['sprawdzen']}, "
          f"V2 {suma['v2']}/{suma['sprawdzen']}")
    print(f"Pliki identyczne geometrycznie: {suma['ident']}")
    if v2_gorszy:
        print("V2 GORSZY od V1 w:")
        for x in v2_gorszy:
            print("  -", x)
    print("\n=== BENCHMARK: " + ("V2 >= V1 (PASS) ===" if wygrana
                                 else "V2 PONIZEJ V1 (FAIL) ==="))

    RAPORT_MD.write_text("\n".join([
        "# Benchmark V2 vs V1",
        "",
        "Te same rysunki testowe (zlecenia 35, 43 i realne 46_2998) i te same",
        "oczekiwania co `testy/regresja.py`. V2 wygrywa dopiero gdy >= V1",
        "na kazdym sprawdzeniu, a pliki sa geometrycznie zgodne.",
        "",
        f"- sprawdzenia: V1 **{suma['v1']}/{suma['sprawdzen']}**, "
        f"V2 **{suma['v2']}/{suma['sprawdzen']}**",
        f"- pliki DXF identyczne encja-po-encji (V1 vs V2): **{suma['ident']}**",
        f"- pliki rozne: **{len(suma['rozne'])}**, brakujace w V2: **{len(suma['brak'])}**",
        f"- werdykt: **{'V2 >= V1 (PASS)' if wygrana else 'V2 PONIZEJ V1 (FAIL)'}**",
        "",
        "| rysunek | V1 | V2 | pliki |",
        "|---|---|---|---|",
        *wiersze_md,
        "",
        "Uruchomienie: `python testy\\benchmark_v2.py` (kod wyjscia 0 = PASS).",
        ""]), encoding="utf-8")
    print(f"Raport: {RAPORT_MD}")

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if wygrana else 1)


if __name__ == "__main__":
    main()
