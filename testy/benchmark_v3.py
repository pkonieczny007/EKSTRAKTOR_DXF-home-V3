# -*- coding: utf-8 -*-
"""Benchmark V3 vs V2 - warunek przelaczenia orkiestratora na --warianty (default).

V3 (produkcja/warianty.py: W-A/W-B/W-C + ocena wybiera zwyciezce) MUSI byc >= V2
(sam W-B) na WSZYSTKIM. Sedno "wygrywa": V3 wybiera NAJLEPSZY wariant, a W-B jest
jednym z nich -> strukturalnie V3 nie moze byc gorszy. Sprawdzamy realnie:
  1. KOMPLETNOSC: interior (bramka 5) zwyciezcy V3 >= interior W-B (V3 nie gubi
     cech, ktore W-B mial - to caly sens dolozenia W-C).
  2. KONTUR: V3 nie oddaje OTWARTEGO konturu tam, gdzie W-B mial domkniety
     (bramka 2 - otwarty = nie na laser).
  3. POKRYCIE: kazda pozycja obecna w V2 jest obecna w V3 (zwyciezca skopiowany).
Poprawa (V3 interior > W-B) = OK; tylko regres (mniej / otwarty / brak) = FAIL.

Te same rysunki co regresja/benchmark_v2. Kod wyjscia 0 = V3 >= V2.
Uzycie:  python testy\\benchmark_v3.py   (WOLNY: uruchamia W-A/W-B/W-C na kazdym rysunku)
"""
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
# regresja podmienia sys.stdout na wrapper UTF-8 - nie wrapowac drugi raz
from regresja import OCZEKIWANE, WYKAZY, RYSUNKI   # noqa: E402

sys.path.insert(0, str(HERE.parent / "produkcja"))
sys.path.insert(0, str(HERE.parent / "produkcja" / "kontrola"))
import warianty  # noqa: E402
from bilans_konturow import count_interior_contours_shapely  # noqa: E402

SRC_V2 = HERE.parent / "produkcja" / "silniki" / "v2" / "orkiestrator.py"
RAPORT_MD = HERE / "benchmark_v3_raport.md"


def _uruchom(silnik, conv, wykaz, out):
    r = subprocess.run([sys.executable, str(silnik), str(conv), str(wykaz), str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode == 0, r.stderr[-600:]


def _zmierz(f):
    """interior (bramka 5) + czy otwarty kontur, dla pliku DXF."""
    if f is None or not f.exists():
        return None
    import ezdxf
    ents = list(ezdxf.readfile(f).modelspace())
    interior, det = count_interior_contours_shapely(ents)
    otwarty = (det["dangles"] + det["cuts"] + det["invalid"]) > 0
    return dict(interior=interior, otwarty=otwarty)


def _plik_v2(out2, zeinr, posn):
    kand = list(out2.glob(f"{zeinr}_p{posn}.dxf")) + list(out2.glob(f"{zeinr}_p{posn}_*.dxf"))
    return kand[0] if kand else None


def main():
    tmp = Path(tempfile.mkdtemp(prefix="benchmark_v3_"))
    wiersze_md = []
    suma = dict(pozycji=0, lepsze=0, rowne=0, regresje=[])

    print(f"{'rysunek':<14} {'poz':>3}  {'W-B':>4} {'V3':>4}  werdykt")
    for zeinr, (wykaz_key, expected) in OCZEKIWANE.items():
        conv = RYSUNKI / f"{zeinr}_1_conv.dxf"
        wykaz = WYKAZY[wykaz_key]
        out2, out3 = tmp / f"v2_{zeinr}", tmp / f"v3_{zeinr}"

        ok2, err2 = _uruchom(SRC_V2, conv, wykaz, out2)
        try:
            wiersze_v3, _ = warianty.warianty_zlecenia(conv, wykaz, out3)
        except Exception as e:
            suma["regresje"].append(f"{zeinr}: V3 pad ({e})")
            wiersze_v3 = []
        if not ok2:
            suma["regresje"].append(f"{zeinr}: W-B(V2) pad ({err2[:150]})")

        v3_by_posn = {int(w["posn"]): w for w in wiersze_v3}
        for posn, w, h, holes_min, status_prefix in expected:
            f2 = _plik_v2(out2, zeinr, posn)
            f3 = out3 / f"{zeinr}_p{posn}.dxf"
            m2, m3 = _zmierz(f2), _zmierz(f3)
            suma["pozycji"] += 1

            if m2 is None:
                # V2 nie wyprodukowal pozycji - nie ma czego bronic (nie liczymy jako regres V3)
                werdykt = "V2 brak - pomijam"
            elif m3 is None:
                suma["regresje"].append(f"{zeinr} p{posn}: V3 BRAK pliku (V2 mial interior={m2['interior']})")
                werdykt = "V3 BRAK -> REGRES"
            elif m3["otwarty"] and not m2["otwarty"]:
                suma["regresje"].append(f"{zeinr} p{posn}: V3 OTWARTY kontur, W-B domkniety")
                werdykt = "V3 OTWARTY -> REGRES"
            elif m3["interior"] < m2["interior"]:
                suma["regresje"].append(f"{zeinr} p{posn}: V3 interior={m3['interior']} < W-B={m2['interior']}")
                werdykt = f"REGRES {m3['interior']}<{m2['interior']}"
            elif m3["interior"] > m2["interior"]:
                suma["lepsze"] += 1
                zw = v3_by_posn.get(posn, {}).get("zwyciezca", "?")
                werdykt = f"LEPSZE (+{m3['interior'] - m2['interior']}, zw={zw})"
            else:
                suma["rowne"] += 1
                werdykt = "rowne"

            i2 = m2["interior"] if m2 else "-"
            i3 = m3["interior"] if m3 else "-"
            print(f"{zeinr:<14} {posn:>3}  {str(i2):>4} {str(i3):>4}  {werdykt}")
            wiersze_md.append(f"| {zeinr} | {posn} | {i2} | {i3} | {werdykt} |")

    wygrana = not suma["regresje"]
    print(f"\nPozycje: {suma['pozycji']} | V3 lepsze: {suma['lepsze']} | "
          f"rowne: {suma['rowne']} | regresje: {len(suma['regresje'])}")
    if suma["regresje"]:
        print("V3 GORSZY od V2 w:")
        for x in suma["regresje"]:
            print("  -", x)
    print("\n=== BENCHMARK V3: " + ("V3 >= V2 (PASS) ===" if wygrana
                                    else "V3 PONIZEJ V2 (FAIL) ==="))

    RAPORT_MD.write_text("\n".join([
        "# Benchmark V3 vs V2",
        "",
        "V3 (warianty W-A/W-B/W-C + ocena) vs V2 (sam W-B), te same rysunki co regresja.",
        "V3 >= V2 gdy zwyciezca nie gubi konturow, nie oddaje otwartego konturu i",
        "produkuje kazda pozycje (bramki 2+5). Poprawa (wiecej konturow) = OK.",
        "",
        f"- pozycje: **{suma['pozycji']}**, V3 lepsze: **{suma['lepsze']}**, "
        f"rowne: **{suma['rowne']}**, regresje: **{len(suma['regresje'])}**",
        f"- werdykt: **{'V3 >= V2 (PASS)' if wygrana else 'V3 PONIZEJ V2 (FAIL)'}**",
        "",
        "| rysunek | poz | W-B interior | V3 interior | werdykt |",
        "|---|---|---|---|---|",
        *wiersze_md,
        "",
        "Uruchomienie: `python testy\\benchmark_v3.py` (kod wyjscia 0 = PASS).",
        ""]), encoding="utf-8")
    print(f"Raport: {RAPORT_MD}")

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if wygrana else 1)


if __name__ == "__main__":
    main()
