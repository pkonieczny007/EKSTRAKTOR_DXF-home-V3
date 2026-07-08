# -*- coding: utf-8 -*-
"""Test transformacji gwintow na materiale TRUDNOSCIERALNYM (gwint.zastosuj_do_pliku).

Golden: testy/golden/gwint_hb450/wzorzec/SL10582645_p5.dxf - realny wynik 1:1 z 8x gwint
M12 (Hardox HB450). Plan operatora (2026-07-08): material trudnoscieralny -> luk USUN, okrag
POWIEKSZ wg tablicy, CZERWONY; nieznana wartosc -> zostaw + status ZOLTY; material zwykly -> BEZ zmian.

Scenariusze (wszystkie na KOPII pliku - golden nietkniety):
  1. HB450 + tablica {M12: 10.6}  -> 8 lukow out, 8 okregow czerwonych r=5.3, status None
  2. material zwykly (S355)       -> NO-OP (8 arcs/8 circ nietkniete)
  3. HB450 + pusta tablica        -> gwint zostaje (8 arcs), status 'zolty' (M12 bez wartosci)

Uzycie:  python testy\\test_gwint_hardox_transformacja.py     (exit 0 = PASS)
"""
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
GOLDEN = HERE / "golden" / "gwint_hb450" / "wzorzec" / "SL10582645_p5.dxf"
sys.path.insert(0, str(ROOT / "produkcja" / "kontrola"))
import gwint as gw          # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _stan(path):
    m = ezdxf.readfile(str(path)).modelspace()
    arcs = sum(1 for e in m if e.dxftype() == "ARC")
    circ = [e for e in m if e.dxftype() == "CIRCLE"]
    czerw = [c for c in circ if c.dxf.color == 1]
    _, gwinty = gw.thread_arcs(m)
    return arcs, len(circ), len(gwinty), czerw


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        a0, c0, g0, cz0 = _stan(GOLDEN)
        check("wzorzec_8_gwintow", g0 == 8 and a0 == 8 and c0 == 8 and len(cz0) == 0,
              f"wzorzec: arcs={a0} circ={c0} gwinty={g0} czerwone={len(cz0)} (oczekiwano 8/8/8/0)")

        # --- 1) HB450 + tablica M12=10.6 -> transformacja 8 gwintow ---
        p1 = tmp / "hardox.dxf"
        shutil.copy(GOLDEN, p1)
        n, kom, stat = gw.zastosuj_do_pliku(p1, "Blech s=8 HB450", {"M12": 10.6})
        a1, c1, g1, cz1 = _stan(p1)
        check("hb450_8_zmienione", n == 8, f"n_zmienione={n} (oczekiwano 8)")
        check("hb450_luki_usuniete", a1 == 0, f"arcs po={a1} (oczekiwano 0 - luki gwintu out)")
        check("hb450_okregi_zostaja", c1 == 8, f"circ po={c1} (oczekiwano 8 - otwory swiete)")
        check("hb450_8_czerwonych", len(cz1) == 8, f"czerwone={len(cz1)} (oczekiwano 8)")
        promienie = sorted(set(round(c.dxf.radius, 2) for c in cz1))
        check("hb450_srednica_10_6", promienie == [5.3],
              f"promienie czerwonych={promienie} (oczekiwano [5.3] = o10.6)")
        check("hb450_status_none", stat is None, f"status={stat} (wszystko zmienione -> None)")
        check("hb450_komentarz", "M12" in kom and "10.6" in kom, f"komentarz='{kom[:60]}'")

        # --- 2) material zwykly -> NO-OP ---
        p2 = tmp / "zwykly.dxf"
        shutil.copy(GOLDEN, p2)
        n2, kom2, stat2 = gw.zastosuj_do_pliku(p2, "S355JR", {"M12": 10.6})
        a2, c2, g2, cz2 = _stan(p2)
        check("zwykly_no_op", n2 == 0 and stat2 is None and kom2 == "",
              f"zwykly: n={n2} status={stat2} kom='{kom2}' (oczekiwano 0/None/'')")
        check("zwykly_nietkniety", a2 == 8 and c2 == 8 and len(cz2) == 0,
              f"zwykly po: arcs={a2} circ={c2} czerwone={len(cz2)} (oczekiwano 8/8/0 - BEZ zmian)")

        # --- 3) HB450 + pusta tablica -> zostaw + zolty ---
        p3 = tmp / "brak.dxf"
        shutil.copy(GOLDEN, p3)
        n3, kom3, stat3 = gw.zastosuj_do_pliku(p3, "HB450", {})
        a3, c3, g3, cz3 = _stan(p3)
        check("brak_tablicy_zostaw", n3 == 0 and a3 == 8,
              f"pusta tablica: n={n3} arcs={a3} (oczekiwano 0/8 - gwint zostaje)")
        check("brak_tablicy_zolty", stat3 == "zolty",
              f"status={stat3} (oczekiwano 'zolty' - M12 bez wartosci = kotwica operatora)")

        # --- golden NIETKNIETY ---
        ag, cg, gg, czg = _stan(GOLDEN)
        check("golden_nietkniety", ag == 8 and cg == 8 and len(czg) == 0,
              f"golden po testach: arcs={ag} circ={cg} czerwone={len(czg)} (MUSI byc 8/8/0)")

        # --- INTEGRACJA: raport.scal(--wykaz) transformuje wyjsciowy DXF pozycji Hardox ---
        import csv
        import openpyxl
        sys.path.insert(0, str(ROOT / "produkcja"))
        import raport
        zeinr = "SL10582645"
        folder = tmp / "scal"
        folder.mkdir()
        with open(folder / f"{zeinr}_ocena.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";",
                               fieldnames=["posn", "semafor", "powod",
                                           "plik_produkcyjny", "zwyciezca"])
            w.writeheader()
            w.writerow(dict(posn="5", semafor="zielony", powod="",
                            plik_produkcyjny=f"{zeinr}_p5.dxf", zwyciezca="W-C"))
        shutil.copy(GOLDEN, folder / f"{zeinr}_p5.dxf")
        wb = openpyxl.Workbook()
        wsx = wb.active
        wsx.append(["Zeinr", "Posn", "Bezeichnung"])
        wsx.append([zeinr, 5, "Blech s=8 HB450"])
        wykaz = folder / "wykaz.xlsx"
        wb.save(wykaz)

        _, rek = raport.scal(str(folder), None, str(wykaz))
        a_int, c_int, _g, cz_int = _stan(folder / f"{zeinr}_p5.dxf")
        check("scal_transformuje_dxf", a_int == 0 and len(cz_int) == 8,
              f"scal(--wykaz) HB450: arcs={a_int} czerwone={len(cz_int)} (oczekiwano 0/8)")
        check("scal_zwraca_rekord", len(rek) == 1, f"rekordow={len(rek)} (oczekiwano 1)")
        if rek:
            check("scal_technologia_gwint", "gwint" in rek[0]["technologia"],
                  f"technologia='{rek[0]['technologia']}' (oczekiwano zawiera 'gwint')")
            check("scal_uwagi_m12", "M12" in rek[0]["uwagi"],
                  f"uwagi='{rek[0]['uwagi'][:50]}' (oczekiwano zawiera 'M12')")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"CHECKS={CHECKS}  FAILS={len(FAILS)}")
    for f in FAILS:
        print("  FAIL:", f)
    if FAILS:
        print("\n[GWINT-TRANSFORMACJA CZERWONY]")
        sys.exit(1)
    print("[GWINT-TRANSFORMACJA ZIELONY] — Hardox M12->o10.6 czerwony; zwykly nietkniety; brak->zolty.")
    sys.exit(0)


if __name__ == "__main__":
    main()
